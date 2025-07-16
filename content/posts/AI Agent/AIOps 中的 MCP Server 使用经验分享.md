---

date: 2025-07-16T14:30:47+08:00
draft: true
title: 'AIOps 中的 MCP Server 使用经验分享'
slug: '20250716-8lbvp5b2'
tags:
  - 标签
categories:
  - 分类
---

当前我们的 ACK AI 助手 2.0 版本主要基于的是 RAG 技术，这只能让我们的 LLM 拥有预训练时没有的知识，基于阿里云内部文档，成为一个 ACK 领域的专家。但是这样的专家像是一个书呆子，拥有丰富的知识，但是还是是**被动信息处理的局限**：传统的 LLM 交互模式是单向的：用户提供输入，模型生成输出。模型无法主动获取信息、执行计算或与外部系统交互，这严重限制了其作为智能助手的实用性为了解决这个问题，openai 提出了 functioncalling，去年十一月，Anthropic 开发的开放标准，旨在解决 AI 模型与外部工具和数据源之间的连接问题。它提供了一个统一的接口，让 AI 模型能够安全、高效地访问各种外部能力。是人工智能系统与能力（工具等）之间的通用连接器，类似于 USB-C 标准化电子设备之间的连接。

![](https://intranetproxy.alipay.com/skylark/lark/0/2025/png/185856366/1752647144286-75755774-8bc8-4306-bec5-1713708a551f.png)

## 1 一个简单的场景引入

我也是刚接触我们的 ACK 集群，我最常遇到过的问题就是，集群拉不下来 Dockerhub 中的镜像，然后呢，我就在本地拉下来镜像，将其提送到我们阿里云的容器镜像服务中，在 Deployment 中指定使用我自己打包的镜像。但是我是一个很粗心的人，因为本地是 arm64 的机构，集群是 x64 的架构，我在拉镜像的时候常常忘记 `--platform=linux/amd64`，tag 我还总是打 latest，这就导致报错 xxx，而且默认镜像仓库是私有的，我还得把他设成开放，很难一眼发现问题。

对于一个超超超级新手来说，我首先要执行 kubectl get pod，就会看到有一个 xxx 的错误，然后把一整个内容粘贴下来发送给 AI，AI 再告诉我这个错误是什么，可能的原因是什么，然后再提醒我可以继续执行 `kubectl describe <pod-name>` 命令和 kubectl log 命令看看，我再去执行，再把结果粘贴到 AI 让它分析原因是什么，AI 再告诉我可以怎么做。总之这个过程很繁琐。

而 MCP（Model Context Protocol）模型上下文协议就是用来解决这个问题的，简单来说，MCP 让 LLM 拥有了调用函数的能力。MCP Server 是一个类似 HTTP 的协议，统一了交互的格式，这样任意一个支持结构化输出的大模型，可以调用任意的函数。

下面是一个简单的创建 MCP Server 的例子，考虑到我们组大部分人都是 Go 选手，Python 封装的太厉害了，也很难通过代码了解去内部的细节。

```go
func main() {
	// 创建一个新的 MCP 服务器
	s := server.NewMCPServer(
		"Kubectl Get MCP Server",
		"1.0.0",
		server.WithResourceCapabilities(true, true),
		server.WithToolCapabilities(true),
		server.WithPromptCapabilities(true),
	)
	// 增加一个 kubectl get 工具
	get_tool := mcp.NewTool(
		"kubectl_get",
		mcp.WithDescription("Get Kubernetes resources using kubectl get functionality"),
		mcp.WithString("resource",
			mcp.Required(),
			mcp.Description("Resource type to get (e.g., pods, services, deployments, nodes)"),
		),
		mcp.WithString("namespace",
			mcp.DefaultString("default"),
			mcp.Description("Namespace to query (default: default)"),
		),
		mcp.WithString("name",
			mcp.Description("Specific resource name to get"),
		),
	)
	// 增加工具处理程序
	s.AddTool(get_tool, kubectlGetHandler)
	// 增加一个提示词，该提示词用于获取集群 Overview
	clusterOverviewPrompt := mcp.NewPrompt("cluster_overview",
		mcp.WithPromptDescription("Get an overview of the Kubernetes cluster"),
		mcp.WithArgument("resource",
			mcp.RequiredArgument(),
			mcp.ArgumentDescription("The resource type to get (e.g., nodes, pods, services)"),
		),
	)
	// 增加提示词处理程序
	s.AddPrompt(clusterOverviewPrompt, clusterOverviewHandler)
	
	// 启动 MCP Server 服务
	httpServer := server.NewStreamableHTTPServer(s)
    if err := httpServer.Start(":8080"); err != nil {
        log.Fatal(err)
    }
}
```

首先，用这个例子结合官方提供的 inspector 工具，可以查看 MCP 基本协议大概是：

1. **Initialization（初始化阶段）**
    - 客户端发送 `initialize request` ，协商协议版本、身份、偏好等。
    - 服务器响应 `initialize response`，确认连接并说明其支持的协议版本和可能的服务器信息。
    - 服务端确认后，客户端发送 `initialized` 通知，双方准备就绪。
2. **Discovery（能力发现阶段）**
    - 客户端依次请求 `tools/list`、`resources/list`、`prompts/list` 等，获取所有可用能力及参数描述，供 LLM 决策调用。**获取的信息直接附在 System Prompt 中**，例如 Cline 的系统提示词有上万行，其中绝大多数是 Tools 的描述。
3. **Execution（执行阶段）**
    - LLM 根据用户意图和能力清单，发起具体调用（如 `tools/call`、`resources/read`），客户端解析 LLM 的输出，向 MCP Server 发起调用。
    - 服务端执行并返回结果，同时可通过 `notification` 推送进度、事件等异步信息。
4. **Termination（终止阶段）**
    - 会话结束时，客户端发送 `shutdown` 请求，服务端确认后可发送 `exit` 通知，安全关闭连接和资源。

MCP Server 提供三种能力，分别是 Tool、Resource、Prompt，当前大多数的客户端其实只支持 Tool，写一个 MCP Server 本质上来说和 Web 开发差不多，将服务通过一个 endpoint 暴露出去，但是在传统的 Web 开发中，客户端是没办法知道后端服务需要哪些参数的，要依赖 API 文档才能知道 endpoint 路径、请求类型和参数格式。MCP 这个协议提供了动态发现的一个机制，这样 LLM 就能主动知道 Tool 的作用、需要的参数、参数的格式等信息。

第二个能力是 Prompt，现在大模型开发还是很依赖提示词工程的。比如说我们给大模型提供了一组工具，每个工具都有自己的描述，但是大模型可能并不知道这些工具组合起来怎么使用。也有一个场景，用户需要格式化的输出结果，如果每次都去手写提示词的话，就很麻烦，因此可以预制一个提示词模板，用于方便用户使用。当前支持 Prompt 的客户端不多，我知道的有 Claude Desktop 和 Vscode Github Copilot。

## 2 ACK AIOps MCP 依赖

在大致了解了 MCP 的基本知识后，我们来看一下要实现 ACK AI 助手 3.0 需要依赖的几个 MCP Server，分别是可观测团队提供的 obs-mcp-server，opanapi 封装的 openapi-mcp-server 和网上开源的 k8s-mcp-server。**k8s-mcp-server** 负责集群资源管理，集成 kubectl 和 helm 工具链功能；**obs-mcp-server** 提供全栈可观测性服务，聚合日志数据和 ARMS Prometheus 监控指标；**openapi-mcp-server** 封装阿里云 ACK OpenAPI，支持集群生命周期管理操作如重启、弹性伸缩等。

### 2.1 通信协议

由于 MCP 还是一个比较新的一个概念，它采用的通信协议还一直在变化，就在上个月，MCP 淘汰了 SSE 协议，改成了只采用 streamable-http 协议来作为远程传输协议。

但是目前很多 MCP Server 的实现都还是 stdio 和 sse 居多，安全认证协议基本上还都是没有，因此，如果我们要为用户提供统一的接入点、接入方式和认证协议，就需要在上层再抽象出来一层代理层，我使用的是 [Unla](https://github.com/AmoyLab/Unla)，当我写这篇稿子的时候，发现微软刚开源一个适用于 Kubernetes 环境的 [MCP-Gateway](https://github.com/microsoft/mcp-gateway)，描述如下：

>MCP Gateway is a reverse proxy and management layer for MCP servers, enabling scalable, session-aware routing and lifecycle management of MCP servers in Kubernetes environments.

我最开始想的是使用 Ingress 来做一个路由，没必要再加一个代理层，将

```go
http://alb-4iaqr7ucrms6i6ewee.cn-beijing.alb.aliyuncsslb.com/obs-mcp-server/sse
http://alb-4iaqr7ucrms6i6ewee.cn-beijing.alb.aliyuncsslb.com/k8s-mcp-server/sse
```

分别路由到：

```go
http://<obs-mcp-server.service>/sse
http://<k8s-mcp-server.service>/sse
```

但是由于 sse 的协议特点，详细流程分解如下：

1. **建立 SSE 连接**: 客户端向初始端点（例如 `http://localhost:8080/sse/`）发起一个 HTTP GET 请求。请求头中必须包含 `Accept: text/event-stream`，以表明其期望建立 SSE 连接。服务器以 `HTTP 200 OK` 响应，保持连接开放。注意是 `/sse/` 否则会有一次重定向。
2. **端点发现 (Endpoint Discovery)**: 连接建立后，服务器立即通过 SSE 推送一条 `endpoint` 事件，其 `data` 字段包含了用于后续通信的、唯一的会话端点 URL。

    ```txt
    event: endpoint 
    data: /messages/?session_id=xxx
    ```

    此步骤将通信引导至一个专用的、具有会话隔离能力的路径。

3. 接下来客户端会向 `/messages/?session_id=xxx` 发送 POST 请求，但是结果是一直通过最开始建立的 sse 连接返回的。

在将 MCP 服务部署于反向代理（如 ALB Ingress）之后，一个常见的挑战源于上述的**端点发现**机制。服务器在响应体中动态下发的会话端点 URL（如 `/messages/?…`）是一个相对路径，反向代理默认不会重写响应体中的内容。这导致客户端收到的地址是服务的内部地址，如果代理配置了路径前缀（Path Prefix），客户端将无法正确访问该端点，导致通信失败。

这也是为什么上个月协议更新，使用 streamable-http 删除了 sse，在收到 POST 请求之后，必须要找到对应的 SSE 长连接进行推送，如果是多机部署的后端，收到 POST 请求的机器和维持长连接的机器不是同一个，就必须进行两个机器之间的通信。（sse 没有 ack 机制，要求服务器一直维护高可用性的连接）

![image.png](https://ceyewan.oss-cn-beijing.aliyuncs.com/obsidian/20250716152809894.png)

## 3 OpenAPI MCP Server

`OpenAPI MCP Server` 不需要本地部署，而是直接在服务器上创建。通过 https://api.aliyun.com/mcp 可以方便的创建一个 OpenAPI MCP Server，客户端需通过 OAuth 认证连接后即可使用。当前 ACK 共提供有 128 个 OpenAPI，但是创建的一个 MCP Server 最多包含 30 个 Tools，这主要是响应时间与能力大小的一个权衡。当前的 MCP 客户端，连接 MCP Server 时，会获取所有的 Tools 的名称、描述、参数信息等内容，然后将这些信息打包到系统提示词中，每一次交互，会将所有的信息都打包交给 LLM 来决策，过长的 input Token 不仅会拖慢 LLM 的响应速度，同时成本也会巨大。例如 CreateCluster 这个 API 具有上百个参数，这是输入 Token 的数据巨大，过多的参数也会打乱 LLM 的注意力机制，更容易产生幻觉。

第二点，是 OpenAPI MCP Server 调用输出的内容同样很长，比如 DescribeKubernetesVersionMetadata 这个 OpenAPI，返回结果包括了不同 Kubernetes 版本的详细信息，如 Etcd 版本、可用的运行时、兼容的操作系统镜像、版本的发布时间和过期时间。

考虑到 qwen 模型的上下文长度为 128k，因此必然需要进行调整，调整方向包括 OpenAPI 选用、描述和参数的调优，并不是所有的 OpenAPI 都会需要用到我们的 AI 助手场景中，另外，API 的描述是写给人看的，现在变更为写给机器看，需要做出一些调整；最后就是参数及参数描述，对于已经弃用、可选参数，可以尽量精简。

第二是 AI 助手设计上，采用层级划分，多个领域场景、领域场景内有多个专家 Agent，每个专家 Agent 仅装配必须要的 Tools。

**异步操作影响后续调用问题**，每次 MCP Tool 调用，只是提交了一个任务，如创建集群、迁移到 Pro 版、升级 Kubernetes 版本等操作，实际在后台执行时间较长。这就会导致 LLM 的后续工具调用会失败，影响用户体验。这个问题不太能避免，建议在响应中提醒用户操作耗时较长，并避免 LLM 多次尝试失败调用。

## 4 Obs-mcp-server

该工具可用性较高，适用于日志分析和监控数据获取场景。对于 ACK 场景，需要提供下面这几个必要参数：

```go
sls_Project：k8s-log-c8d8d4be7163748d4876faf34c564150f
sls_logStore：k8s-event
regionId：cn-beijing
arms_Project：workspace-default-cms-1953507478506681-cn-beijing
arms_MetricStore：aliyun-prom-c8d8d4be7163748d4876faf34c564150f
namespace：default
```

工具中提供了 `sls_translate_text_to_sql_query` 和 `MCP_cms_translate_text_to_promql` 这两个方法，用于将 Prompt 中的自然语言转换为 SLS 支持的 SQL 查询语句和 PromQL 语句。因此，合适的 Prompt 就显得很重要了：

```go
我希望查询集群【集群 ID】在【时间范围】内的【指标类型】，对象是【具体资源（如 Deployment、Pod 名称等）】，数据应该来自【具体的日志库或监控源】，并且希望得到【展示形式（表格、图表等）】。
```

LLM 对于日志或监控中能够拿到什么数据并不清楚，因此很难写出质量高的提示词，预先写好 Few-Shot Prompting（少样本提示）很有帮助。这样的话，上面的这两个工具才能生成很精确的查询语句，查询得到信息密度高的结果。

## 5 效果展示

## 6 安全认证

OpenAPI 团队提供的 MCP Server 就采用了 MCP 协议规范指定的 OAuth 2.0 作为认证机制，目前的 MCP Client 很多都不支持该协议，支持的有 CherryStudio，我们的百炼平台对该协议的支持还在开发过程中，我自己

这部分其实 openapi 团队给内部的 AI 助手等功能的接入提供了绕过 OAuth 认证的端口，但是我之前没看到文档，就自己对这部分也研究了一下。

### 6.1 初次调用

我们尝试像访问一个开放 API 一样，向 MCP Server 发送一个 `initialize` 请求。

```bash
curl --location --request POST 'https://mcp.example.com/mcp' \
--header 'Content-Type: application/json' \
--data-raw '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "id": 0
}'
```

服务器返回了 `401 Unauthorized` 状态码和如下响应体：

```json
{
    "error": "Authorization header is missing"
}
```

根据 HTTP 规范，一个标准的 401 响应还会包含一个 `WWW-Authenticate` 头，它会指明认证方案（例如 `Bearer`），有时还会提供授权服务器的地址，引导客户端开始认证流程。

### 6.2 服务发现

既然需要认证，我们首先要找到授权服务器在哪，以及它支持哪些功能。OAuth 2.0 授权服务器元数据规范 (RFC 8414) 定义了一个标准的发现端点。

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

- `authorization_endpoint`：引导用户到这个地址进行登录和授权。
- `token_endpoint`：授权码在这个地址换取访问令牌。
- `registration_endpoint`：先到这里注册以获取一个客户端身份（`client_id`）。
- `code_challenge_methods_supported`：`["S256"]` 表示使用 PKCE 的 SHA-256 方式。
- `grant_types_supported`：`["authorization_code", "refresh_token"]` 表明服务器支持授权码和刷新令牌。
- `token_endpoint_auth_methods_supported`：`["none"]` 表明支持公共客户端。

### 6.3 动态客户端注册

```bash
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

注册成功后，授权服务器会返回凭证信息：

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

- `redirect_uris`：回调地址，用户认证后，授权服务器会将授权码发送到这个地址。
- `client_id`：这是我们客户端的唯一公共标识符。

### 6.4 动态生成 PKCE 代码对

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

### 6.5 发起授权请求

现在，万事俱备。我们将构造一个特殊的 URL，并引导用户（资源所有者）在浏览器中打开它并授权，授权后会被重定向到回调地址，通过监听回调地址就可以拿到授权码。

```url
http://【Authorization Endpoint】?response_type=code&client_id=【Client ID】&code_challenge=【Code Challenge】&code_challenge_method=S256&redirect_uri=【Redirect URI】
```

### 6.6 交换令牌

向 `token_endpoint` 发起一个 POST 请求，用刚刚获取的 `code` 和之前秘密保存的 `code_verifier` 来交换最终的访问令牌。

```bash
curl --location --request POST 'https://mcp.example.com/v1/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'grant_type=authorization_code' \
--data-urlencode 'code=【Code】' \
--data-urlencode 'redirect_uri=【Redirect URI】' \
--data-urlencode 'client_id=【Client ID】' \
--data-urlencode 'code_verifier=【Code Verifier】'
```

授权服务器接收到请求，校验一致后，将返回包含令牌的 JSON 响应。

### 6.7 使用 Token 访问

现在，我们可以带着 `access_token` 重新访问 MCP Server 了。我们将令牌放在 `Authorization` 请求头中，并使用 `Bearer` 方案。

```Python
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

### 6.8 刷新令牌

当 `access_token` 过期后，我们的请求会再次收到 `401 Unauthorized`。此时，我们不必让用户重新走一遍授权流程，而是可以使用 `refresh_token` 来静默地获取新的访问令牌。

```bash
curl --location --request POST 'https://mcp.example.com/v1/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'grant_type=refresh_token' \
--data-urlencode 'refresh_token=【Refresh Token】' \
--data-urlencode 'client_id=【Client ID】'
```
