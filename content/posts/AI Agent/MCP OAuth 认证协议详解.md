---
categories:
- AI Agent
date: 2025-07-11 15:07:32+08:00
draft: true
slug: 20250711-y4fj893d
summary: 本文详解 MCP 生态中 OAuth 2.0 认证授权流程，涵盖服务发现、客户端注册、PKCE 动态验证及令牌交换等关键步骤，助力开发者构建安全、合规的
  Agent 工具。
tags:
- MCP
- OAuth
title: 掌握 MCP Server 的 OAuth 2.0 认证：从零到一的实现指南
---

随着 MCP (Model Context Protocol) 生态的日渐成熟，统一且安全的认证授权标准变得至关重要。OAuth 2.0 作为业界公认的授权框架，凭借其安全性、灵活性和广泛的应用，成为了 MCP 协议认证的官方选择。

对于开发者而言，仅仅使用现成的客户端（如 Inspector 工具）可能无法满足定制化、自动化的需求。我们需要构建自己的 Agent 或工具来与 MCP 服务器交互，这就要求我们必须深入理解并能以代码实现 OAuth 2.0 的认证流程。

在开始实战之前，我们必须先理清 OAuth 2.0 场景中的关键角色，尤其是 MCP 服务器扮演的独特角色。

- **资源所有者 (Resource Owner)**：你，即最终用户。你拥有需要被访问的数据。这些数据可能在 MCP 服务器上（如工具使用权限），也可能在第三方服务上（如你的阿里云 OSS 存储桶或 GitHub 仓库）。
- **客户端 (Client)**：你正在开发的 Agent 程序。它希望代表你（资源所有者）去访问 MCP 服务器提供的工具和资源。
- **MCP 服务器 (The MCP Server)**：这是核心，它扮演着**三重角色**：
    1. **资源服务器 (Resource Server)**：它托管着受保护的 MCP 工具 (`https://mcp.example.com/mcp`)，客户端需要凭令牌才能调用这些工具。
    2. **授权服务器 (Authorization Server)**：**从客户端的视角来看**，MCP 服务器就是授权服务器。它负责处理客户端的注册、颁发和刷新自己的 **MCP 访问令牌**。它提供了 `/register` 等端点。
    3. **第三方服务的客户端 (Client for Third-Party Services)**：当 MCP 工具需要访问你在第三方（如 GitHub、阿里云）的资源时，MCP 服务器会扮演客户端的角色，去请求这些第三方服务的授权。

这种设计被称为**委托授权（Delegated Authorization）**。你授权**客户端**访问 **MCP 服务器**，然后你再授权 **MCP 服务器**访问**第三方服务**。这样做的好处是：

- **安全**：你的客户端 Agent 只需持有 MCP 的令牌，无需接触和管理多个第三方服务的敏感令牌。
- **解耦**：MCP 服务器封装了与第三方服务交互的复杂逻辑，客户端只需与统一的 MCP 接口交互。

我们即将实践的流程是 OAuth 2.0 中最推荐、最安全的 **授权码流程 (Authorization Code Flow)，并结合了 PKCE (Proof Key for Code Exchange) 扩展**。

## 1 初次试探与 401 "Unauthorized"

一切始于一次普通的 API 调用。我们尝试像访问一个开放 API 一样，向 MCP Server 发送一个 `initialize` 请求。

```bash
curl --location --request POST 'https://mcp.example.com/mcp' \
--header 'Content-Type: application/json' \
--data-raw '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "id": 0
}'
```

服务器返回了 `401 Unauthorized` 状态码和如下响应体，这在我们的预料之中：

```json
{
    "error": "Authorization header is missing"
}
```

- `401 Unauthorized` 是一个明确的信号：**" 你需要先证明你是谁，并获得许可 "**。
- 响应体中的 `Authorization header is missing` 直接告诉我们，资源服务器期望在请求头中看到一个 `Authorization` 字段，这通常用于承载访问令牌 (Access Token)。
- 根据 HTTP 规范，一个标准的 401 响应还会包含一个 `WWW-Authenticate` 头，它会指明认证方案（例如 `Bearer`），有时还会提供授权服务器的地址，引导客户端开始认证流程。

## 2 服务发现

既然需要认证，我们首先要找到授权服务器在哪，以及它支持哪些功能。OAuth 2.0 授权服务器元数据规范 (RFC 8414) 定义了一个标准的 " 发现 " 端点。

我们访问这个 `/.well-known/oauth-authorization-server` 路径：

```bash
curl --location --request GET 'https://mcp.example.com/.well-known/oauth-authorization-server'
```

服务器返回了一个包含其所有能力和端点信息的 JSON 对象：

```json
{
    "response_types_supported": ["code"],
    "code_challenge_methods_supported": ["S256"],
    "grant_types_supported": ["authorization_code", "refresh_token"],
    "revocation_endpoint": "https://mcp.example.com/revoke",
    "registration_endpoint": "https://mcp.example.com/register",
    "token_endpoint_auth_methods_supported": ["none"],
    "response_modes_supported": ["query"],
    "issuer": "https://mcp.example.com",
    "authorization_endpoint": "https://auth.example.com/oauth2/v1/auth",
    "token_endpoint": "https://auth.example.com/v1/token"
}
```

这个 JSON 就是授权服务器的 " 说明书 "。对我们而言，最重要的几个字段是：

- `authorization_endpoint`: 我们将引导用户到这个地址进行登录和授权。**请注意，这个地址指向了第三方授权服务！** 这正是委托授权模式的体现。
- `token_endpoint`: 我们的 Agent 将用授权码在这个地址换取访问令牌。
- `registration_endpoint`: 我们的 Agent 需要先到这个地址 " 注册 "，以获取一个客户端身份（`client_id`）。
- `code_challenge_methods_supported`: `["S256"]` 告诉我们，服务器支持并期望我们使用 PKCE 的 SHA-256 方式。
- `grant_types_supported`: `["authorization_code", "refresh_token"]` 表明服务器支持标准的授权码流程，并允许我们后续使用刷新令牌。
- `token_endpoint_auth_methods_supported`: `["none"]` 这是一个关键信息，意味着它支持 " 公共客户端 "，这类客户端在交换令牌时无需提供 `client_secret`。这完全符合我们 Agent 的情况。

## 3 动态客户端注册

``` bash
curl --location --request POST 'https://mcp.example.com/register' \
--header 'Content-Type: application/json' \
--data-raw '{
    "redirect_uris": [ "http://127.0.0.1:6274/oauth/callback" ],
    "token_endpoint_auth_method": "none",
    "grant_types": [ "authorization_code", "refresh_token" ],
    "response_types": [ "code" ],
    "client_name": "My Agent",
}'
```

注册成功后，授权服务器会返回客户端的凭证信息：

```json
{
    "client_id": "xxx",
    "client_name": "My Agent",
    "client_secret": "",
    "created_at": 1752218883279,
    "expires_at": 1783754883279,
    "grant_types": [ "authorization_code", "refresh_token" ],
    "redirect_uris": [ "http://127.0.0.1:6274/oauth/callback" ],
    "response_types": [ "code" ],
    "token_endpoint_auth_method": "none"
}
```

- `redirect_uris`: **这是 OAuth 流程中至关重要的安全参数**。授权服务器在完成用户授权后，只会将授权码发送到这个列表中的地址。这可以防止授权码被劫持并发送到恶意攻击者的服务器。在我们的 Agent 中，我们需要启动一个本地 Web 服务来监听这个地址。
- `token_endpoint_auth_method: "none"`: 我们明确声明自己是公共客户端。因此，返回的 `client_secret` 是空的。
- `grant_types`: 我们声明希望使用授权码和刷新令牌。
- `client_id`: **这是我们客户端的唯一公共标识符**。我们需要保存它，后续每一步都会用到。

## 4 动态生成 PKCE 代码对

为了防止 " 授权码劫持攻击 "，我们必须使用 PKCE。即使攻击者在不安全的网络环境中（例如，在操作系统的应用间通信中）截获了我们的授权码，但没有 `code_verifier`，他也无法用它来交换令牌。

PKCE 的核心是创建一对密钥：一个私有的 `code_verifier` 和一个公开的 `code_challenge`。

1. **`code_verifier`**: 一个高熵的随机字符串，由我们的 Agent 生成并**秘密保存**。
2. **`code_challenge`**: 对 `code_verifier` 进行 `SHA256` 哈希运算，然后进行 `Base64Url` 编码。

```Python
# 生成一个足够安全的随机字符串作为 code_verifier
code_verifier = secrets.token_urlsafe(64)  
# 对 code_verifier 进行 SHA256 哈希
hashed = hashlib.sha256(code_verifier.encode('utf-8')).digest()
# 对哈希结果进行 Base64Url 编码，生成 code_challenge
code_challenge = base64.urlsafe_b64encode(hashed).decode('utf-8').rstrip('=')
# 保存这两个变量
print(f"Code Verifier: {code_verifier}") 
print(f"Code Challenge: {code_challenge}")
```

**重要提示**：`code_verifier` 是整个流程中的一个关键秘密，必须妥善保管，直到令牌交换步骤完成。

## 5 发起授权请求

现在，万事俱备。我们将构造一个特殊的 URL，并引导用户（资源所有者）在浏览器中打开它并授权，授权了 Agent 能够访问 MCP Server，MCP Server 又能拿着这个 Token 去访问阿里云、Github 等第三方服务。

```go
【Authorization Endpoint】?response_type=code&client_id=【Client ID】&code_challenge=【Code Challenge】&code_challenge_method=S256&redirect_uri=【Redirect URI】
```

**流程拆解：**

1. **启动本地服务器**: 你的 Agent 程序需要启动一个临时的 Web 服务器，监听注册时提供的 `redirect_uri`。
2. **打开构造的请求地址**: 浏览器打开真正的第三方授权页面（如 `auth.example.com`）。
3. **用户授权**: 用户在熟悉的第三方页面（如阿里云）登录，并同意授权 **"MCP Server"** (而不是你的 "My Agent") 访问其云资源。
4. **重定向回调地址**: 授权成功后，第三方服务将浏览器重定向到预设的回调地址，并附上一个临时授权码。**只要这个地址能被用户浏览器访问即可！！！**
5. **MCP 服务器处理并重定向回客户端**: MCP 服务器用这个码在后台换取了**第三方令牌**并安全存储。然后，它会生成一个属于 MCP 自己的新 `code`，并将浏览器重定向到我们客户端指定的 `redirect_uri`。  
    `http://127.0.0.1:6274/oauth/callback?code=【MCP生成的Code】`
6. **捕获授权码**: 我们的本地服务器收到这个请求，成功捕获 **MCP 的授权码**。

## 6 交换令牌

这是最后也是最关键的一步。我们的 Agent 在后台（无需用户参与）向 `token_endpoint` 发起一个 POST 请求，用刚刚获取的 `code` 和之前秘密保存的 `code_verifier` 来交换最终的访问令牌。

```bash
curl --location --request POST 'https://mcp.example.com/v1/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'grant_type=authorization_code' \
--data-urlencode 'code=【Code】' \
--data-urlencode 'redirect_uri=【Redirect URI】' \
--data-urlencode 'client_id=【Client ID】' \
--data-urlencode 'code_verifier=【Code Verifier】'
```

当授权服务器收到此请求时，它会：

1. 找到 `code` 对应的 `code_challenge`。
2. 用 `S256` 算法处理请求中提供的 `code_verifier`。
3. 比较计算结果和存储的 `code_challenge` 是否一致。
4. **只有在一致的情况下**，才认为请求是合法的，并颁发令牌。

如果一切顺利，服务器将返回包含令牌的 JSON 响应：

```json
{
    "scope": "/internal/acs/openapi openid aliuid",
    "request_id": "ffa5bfba-8bd1-415a-b338-82928f67f314",
    "access_token": "xxx",
    "token_type": "Bearer",
    "refresh_token": "xxx",
    "id_token": "xxx",
    "additional_information": {
        "refresh_token_id": 16857050
    },
    "expires_in": 259199
}
```

- `grant_type=authorization_code`: 表明我们正在用授权码交换令牌。
- `code_verifier`: **这就是我们用来开锁的 " 钥匙 "**。它证明了发起授权请求和发起令牌交换请求的是同一个客户端。
- `access_token`: **访问令牌**。这就是我们梦寐以求的凭证！它通常是短暂的（`expires_in` 表示其有效期，单位为秒）。
- `refresh_token`: **刷新令牌**。它通常有更长的有效期（例如几天或几个月）。当 `access_token` 过期后，我们可以用它来获取新的 `access_token`，而无需再次打扰用户。**必须像密码一样安全地存储它**。
- `token_type`: "Bearer" 意味着任何持有此令牌的人（"bearer"）都可以用它来访问资源。

## 7 使用令牌访问 MCP Server

现在，我们可以带着 `access_token` 重新访问 MCP Server 了。我们将令牌放在 `Authorization` 请求头中，并使用 `Bearer` 方案。

```python
from fastmcp import Client  
from fastmcp.client.auth import BearerAuth

auth_handler = BearerAuth(access_token)  
async with Client(MCP_SERVER_BASE_URL, auth=auth_handler) as client:  
    print("\n✅ 认证成功，已连接到服务器！")  
    tools = await client.list_tools()  
    print("\n🛠️  服务器可用工具列表:")  
    if not tools:  
        print("  - 未发现任何工具。")  
    else:  
        for tool in tools:  
            print(f"  - {tool.name}: {tool.description}")
```

当然，我们也可以构造符合 MCP 规范的 JSONRPC 2.0 格式的 POST 请求，这次会返回 200 OK 响应。

## 8 刷新访问令牌

当 `access_token` 过期后，我们的请求会再次收到 `401 Unauthorized`。此时，我们不必让用户重新走一遍授权流程，而是可以使用 `refresh_token` 来静默地获取新的访问令牌。

```bash
curl --location --request POST 'https://mcp.example.com/v1/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'grant_type=refresh_token' \
--data-urlencode 'refresh_token=【Refresh Token】' \
--data-urlencode 'client_id=【Client ID】'
```

服务器验证 `refresh_token` 和 `client_id` 后，会返回一组新的 `access_token` 和 `refresh_token`（可选）。

这个流程体现了 OAuth 2.0 的核心思想——**委托授权**。用户（资源所有者）从未将自己的密码暴露给我们的 Agent（客户端），而是通过一个受信任的中间方（授权服务器）授予了有限的、可撤销的访问权限。这正是 OAuth 2.0 强大而安全的原因。希望这篇详尽的指南能为你构建强大的 MCP 工具扫清障碍，并让你对现代网络认证体系有更深刻的认识。

## 9 保密客户端 vs. 公共客户端

1. **传统 Web 应用模式（保密客户端 - Confidential Client）**
    - **核心假设**: 客户端是一个可以**安全保管机密**的后端服务器。
    - **认证关键**: 在第 6 步 " 交换令牌 " 时，客户端必须同时提供 `code` 和它在注册时获得的 `client_secret`。`client_secret` 就像是客户端的密码，用于向授权服务器证明 " 我就是那个注册过的应用 "。
    - **安全性**: `client_secret` 的存在，使得即使 `code` 被截获，攻击者没有 `client_secret` 也无法换取令牌。
    - **适用于任何有安全后端服务器的应用**。例如传统网站（如电商网站、社交媒体的后端）。
2. **现代公共客户端模式（PKCE - Public Client）**
    - **核心假设**: 客户端是**无法安全保管机密**的环境，如桌面应用、浏览器单页应用（SPA）、移动 App 或我们的 Agent 程序。将 `client_secret` 硬编码在这些环境中，极易被反编译或窃取。
    - **认证关键**: 为了解决无法使用 `client_secret` 的问题，引入了 PKCE（Proof Key for Code Exchange）机制。
        - 在第 5 步 " 发起授权请求 " 时，客户端发送一个公开的 `code_challenge`（锁）。
        - 在第 6 步 " 交换令牌 " 时，客户端发送一个保密的 `code_verifier`（钥匙）。
    - **安全性**: `code_verifier` 扮演了**一次性的、动态生成的**`client_secret` 的角色。即使 `code` 被截获，攻击者没有在客户端本地秘密保存的 `code_verifier`，同样无法换取令牌。