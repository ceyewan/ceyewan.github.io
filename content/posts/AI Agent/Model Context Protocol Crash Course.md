---
categories:
- AI Agent
date: '2025-06-25T22:12:45+08:00'
draft: false
summary: 本文深入解析了模型上下文协议（MCP）如何解决大型语言模型（LLM）在知识时效性、上下文管理和工具集成方面的核心限制，通过标准化能力连接提升AI系统的智能性与扩展性。
tags:
- MCP
- Agent
title: MCP协议：打破LLM限制的模型上下文新标准
---

## 1 引言

大型语言模型（LLM）在自然语言理解和生成方面展现了惊人的能力，但它们面临着几个根本性的限制：

- **知识的时效性问题**：LLM 的知识基于训练时的静态数据集，存在明显的"知识截止日期"。当我们询问最新的股价、天气信息或突发新闻时，模型只能基于过时的训练数据进行推测，无法提供准确的实时信息。
- **上下文窗口的物理限制**：尽管现代 LLM 的上下文窗口不断扩大（从早期的 4K 到现在的数百万 tokens），但仍然存在物理上限。当需要处理的信息超出这个窗口时，模型必须在保留重要信息和接收新信息之间做出权衡。
- **被动信息处理的局限**：传统的 LLM 交互模式是单向的：用户提供输入，模型生成输出。模型无法主动获取信息、执行计算或与外部系统交互，这严重限制了其作为智能助手的实用性。

**模型上下文协议（Model Context Protocol, MCP）** 是由 Anthropic 开发的开放标准，旨在解决 AI 模型与外部工具和数据源之间的连接问题。它提供了一个统一的接口，让 AI 模型能够安全、高效地访问各种外部能力。是人工智能系统与能力（工具等）之间的通用连接器，类似于 USB-C 标准化电子设备之间的连接。

MCP 的设计灵感来源于软件开发领域的**语言服务器协议（LSP）**。正如 LSP 让代码编辑器能够与任何编程语言的分析引擎标准化通信，MCP 让 AI 应用能够与任何外部工具标准化交互。

![image.png](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/20250621105636.png)

---

## 2 LLMs 的上下文管理

LLM 的响应完全依赖于其上下文窗口内的输入信息，包括用户提示、对话历史和相关数据。然而，LLM 面临两个核心限制：**上下文长度限制**（超出窗口的信息无法被"看到"）和**知识时效性问题**（只能基于训练截止日期前的静态知识）。因此，有效的上下文管理需要主动向模型提供最新或专业化的信息来弥补这些局限，这正是 RAG（检索增强生成）等技术要解决的核心问题。

### 2.1 传统方法

- **截断/滑动窗口**：保留最近对话，丢弃旧信息，易丢失重要上下文。
- **摘要法**：对长内容做摘要，易丢失细节且需要额外计算。
- **模板化 prompt**：预留插槽（slots）手动填充信息，开发负担大。

### 2.2 RAG（检索增强生成）

**RAG（检索增强生成）技术**通过让外部系统检索相关文档或数据，并将结果注入到模型的上下文中，有效解决了 LLM 知识过时和领域专业性不足的问题。

然而，RAG 存在两个根本性局限：

1. **被动性问题**：模型仍然是信息的被动接收者，无法主动发起检索请求，所有检索逻辑都需要开发者预先设计和硬编码。
2. **功能单一性**：RAG 主要专注于知识查找和文本检索，无法让模型执行实际操作或使用多样化的外部工具。

这些限制使得 RAG 虽然在信息增强方面取得了重要进展，但距离真正的"智能代理"仍有差距——模型需要的不仅是更多信息，更需要主动获取信息和执行操作的能力。这正是 MCP 等新一代协议要解决的核心问题：从被动的信息消费者转变为主动的工具使用者。

### 2.3 Prompt 链与 Agent

**提示链和代理技术**代表了 LLM 从被动信息处理向主动工具使用的重要演进。通过 **ReAct（推理 + 行动）模式**，模型能够输出结构化的命令（如 `SEARCH: 'weather in SF'`），系统识别这些命令后调用相应的外部工具，并将结果反馈给模型进行后续处理。

这种方法的核心优势是让 LLM 具备了**主动性**——模型可以根据需要"决定"调用什么工具，而不是被动接收预设的信息。然而，这一阶段存在显著的**标准化缺失问题**：

1. **实现碎片化**：每个开发者都需要构建自定义的链式逻辑和解析系统
2. **模型差异性**：不同 LLM 表达工具调用的方式各不相同
3. **集成复杂性**：每添加一个新工具都需要编写专门的提示逻辑和输出解析代码

这种"各自为政"的状态虽然证明了 LLM 工具使用的可行性，但缺乏统一标准使得开发效率低下、维护成本高昂，难以形成生态规模效应。

### 2.4 函数调用 Function Calling

**函数调用机制**标志着 LLM 工具使用的重要标准化里程碑。2023 年 OpenAI 引入的 Function Calling 功能让开发者能够预定义结构化函数，模型可以通过返回标准 JSON 格式来精确指定要调用的函数和参数。

相比之前的文本解析方式（如 `SEARCH: 'weather in SF'`），函数调用机制实现了：

- **结构化输出**：统一的 JSON 格式替代了不可靠的文本解析
- **精确参数传递**：明确的函数名和参数结构，避免了歧义
- **标准化接口**：模型与外部工具之间有了规范的通信协议

尽管函数调用在**技术层面**实现了标准化，但在**开发体验**上仍然存在挑战：

- 每个应用仍需自建函数定义和调用逻辑
- 缺乏统一的工具生态和复用机制
- 开发者需要处理复杂的状态管理和错误处理

这为后续 MCP 等更高层次的标准化协议奠定了基础。

### 2.5 M×N 集成难题

在 MCP 出现之前，AI 工具集成面临的核心问题是**缺乏统一标准**，导致每个 AI 应用与每个工具之间都需要**独立的定制集成**。

M 个 AI 应用，N 个工具/服务，每个 AI 应用都需要为每个工具编写专门的连接代码，结果是 **M × N 个独立集成**，形成"意大利面条式"的混乱连接。

---

## 3 MCP：模型上下文协议

### 3.1 MCP 是什么？

MCP 是一种**标准化协议**，充当 AI 模型与外部工具之间的"通用翻译器"。就像 USB-C 统一了设备连接标准一样，MCP 统一了 AI 工具集成标准，使 AI 模型能够无缝地与外部工具、资源和环境进行交互。

解决了 M×N 集成复杂性问题：

- **传统方式**：每个 AI 应用需要为每个工具编写独立的集成代码
- **MCP 方式**：M 个 AI 应用 + N 个工具 = M+N 次实现（而非 M×N）

![image.png](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/20250621111133.png)

### 3.2 MCP 的优势

- **动态能力发现**：传统 AI 系统只能使用预先硬编码的工具集，添加新功能需要修改核心代码并重新部署。MCP 则允许 AI 在运行时主动查询服务器端可用的功能和工具，就像智能助手能够实时了解周围环境中的可用资源。这种能力实现了真正的即插即用：当新工具添加到 MCP 服务器时，所有连接的 AI 客户端都能立即发现并使用这些新能力，无需任何代码修改。
- **有状态交互与记忆**：传统 API 调用是无状态的，每次请求都独立处理，无法维护上下文。MCP 能够在整个会话期间维护丰富的上下文信息，就像人类对话中记住之前的讨论内容。这使得 AI 可以缓存查询结果避免重复计算，重用上下文信息优化后续操作，并在复杂任务执行过程中追踪中间状态。例如在多步骤数据分析中，AI 能记住每个步骤的结果并在后续步骤中引用。
- **多步编排与智能决策**：MCP 使 AI 能够像项目经理一样协调执行复杂工作流程，支持条件逻辑判断、循环控制和多工具精密协调。AI 可以根据中间结果动态调整执行路径，处理异常情况，甚至并行执行任务提高效率。例如处理客户服务请求时，AI 可以先查询用户信息，根据用户类型调用不同处理流程，同时记录日志并发送通知，整个过程可控且可追踪。
- **关注点分离**：MCP 采用客户端 - 服务器架构，实现清晰的职责分离。AI 客户端专注于理解用户意图、制定执行策略和智能决策，无需关心具体工具实现细节。MCP 服务器专注于工具的具体执行逻辑，包括参数验证、错误处理等技术细节。这种分离使得 AI 开发者和工具开发者可以独立专注各自领域，系统更易维护、测试和扩展。
- **安全与控制**：在 AI 系统日益强大的今天，安全控制变得至关重要，MCP 在这方面提供了多层次的保护机制。通过集中化的安全检查点，MCP 可以在工具执行前进行统一的安全审查，包括权限验证、参数校验、操作风险评估等。对于可能产生重大影响的敏感操作，如删除文件、发送邮件、执行系统命令等，MCP 可以要求用户进行明确确认，确保人类始终保持对关键决策的控制权。此外，MCP 还支持细粒度的权限管理，可以为不同的 AI 客户端或不同的使用场景配置不同的权限级别。这种多层次的安全机制不仅保护了用户数据和系统安全，还为 AI 系统在企业环境中的部署提供了必要的合规保障，使得组织能够放心地使用 AI 技术来处理敏感业务流程。

---

## 4 MCP 架构详解

### 4.1 三大核心角色

| 角色   | 定位         | 主要职责                   | 举例                      |
|------|------------|-------------------------|------------------------|
| Host | 用户侧应用      | 管理用户输入输出、会话状态、决定何时调用外部能力 | Claude Desktop、Cursor、定制 AI 助手等 |
| Client | Host 内部组件 | 具体负责与 MCP Server 按协议通信，转发请求与响应 | SDK、适配层              |
| Server | 能力提供方    | 暴露工具/资源/提示词，按协议响应调用请求      | 本地/远程工具服务器、API 封装等     |

Host 是用户直接交互的 AI 应用程序，如 Claude Desktop、Cursor 或自定义聊天应用。它承担着整个系统的决策和协调责任：

- **用户界面管理**：处理用户输入输出，维护会话状态
- **智能决策**：根据 AI 意图决定何时调用哪些外部能力
- **连接管理**：主动发起与 MCP 服务器的连接
- **工作流编排**：协调 AI 模型与外部工具间的复杂交互

Client 是 Host 内部的通信组件，负责与 MCP 服务器的底层协议交互。每个 Client 与一个服务器建立 1:1 连接：

- **协议驱动**：处理 MCP 请求发送和响应接收
- **连接维护**：管理网络连接、错误处理和超时控制
- **协议合规**：确保严格遵循 MCP 协议规范
- **多实例支持**：Host 可创建多个 Client 实例连接不同服务器

Server 是实际提供具体功能的外部程序，可本地或远程部署：

- **能力封装**：将各种功能（工具、数据、API）标准化暴露
- **标准接口**：以统一格式描述可用工具和资源
- **请求执行**：接收并执行来自客户端的具体操作请求
- **结果返回**：将执行结果按协议格式返回给客户端

### 4.2 通信流程

1. **用户发起请求**
    用户通过 Host 应用界面提出需求，如"查询旧金山天气"。Host 使用 LLM 解析意图，识别需要外部工具支持。
2. **服务器连接与发现**
    - Host 确定需要的服务器类型（如天气服务器）
    - 指示对应的 Client 建立连接（本地启动进程或远程网络连接）
    - Client 发送标准查询请求（`tools/list`、`resources/list`）
    - Server 返回可用能力的详细描述（工具名称、参数、功能说明）
3. **工具调用执行**
    - Host 基于能力发现结果做出具体调用决策
    - Client 发送格式化的工具调用请求（如 `get_weather(location='San Francisco')`）
    - Server 执行底层逻辑（调用天气 API、查询数据库等）
    - Server 将执行结果封装为标准响应返回
4. **结果集成与展示**
    - Client 将服务器响应传递给 Host
    - Host 将结果整合到 AI 模型上下文中
    - AI 模型基于工具返回的数据生成用户友好的回答
    - Host 通过界面向用户展示最终结果
5. **会话管理与终止**
    - 支持多轮交互和多服务器并发调用
    - 维护会话状态和上下文连续性
    - 会话结束时优雅关闭连接，清理资源

> **优势**：这种三层分离的架构设计实现了：
> - **模块化扩展**：新工具无需修改 AI 应用，只需部署新服务器
> - **协议标准化**：统一的通信协议确保互操作性
> - **职责清晰**：每个角色专注自身核心功能，降低系统复杂度
> - **灵活部署**：支持本地和远程服务器的混合架构

---

## 5 MCP 能力体系（Capabilities）

MCP Server 可以向 Client 暴露多种能力，分为四大类：

### 5.1 Tools（工具/操作）

Tools 是 MCP 中最活跃的能力类型，代表具备执行能力的函数或动作。它们通常会产生副作用，能够改变外部系统状态或触发实际操作。智能调用机制如下：

- **自主触发**：LLM 通过 Host 根据对话上下文和用户意图自主决定调用时机
- **参数传递**：支持复杂的参数结构，包括必需参数和可选参数
- **链式调用**：支持多个工具的顺序或并行调用，形成复杂工作流

```python
@mcp.tool() 
def send_email(recipient: str, subject: str, body: str): """发送邮件 - 需要用户确认的高风险操作""" 
return email_service.send(recipient, subject, body)
```

### 5.2 Resources（资源）

Resources 提供只读的数据访问能力，专注于信息检索而非操作执行。这种设计确保了数据安全性，避免意外的数据修改。智能检索机制：

- **语义搜索**：基于内容理解的智能检索
- **上下文感知**：根据对话历史优化检索结果
- **增量更新**：支持资源内容的动态更新和版本管理
- **缓存优化**：智能缓存策略减少重复访问开销

```Python
@mcp.resource("database/users") 
def query_user_data(filters: dict): 
"""用户数据查询""" 
return sanitized_user_data
```

### 5.3 Prompts（提示词/模板）

Prompts 提供预定义的对话模板和**行为引导**，帮助 AI 在特定场景下表现出期望的行为模式。这种能力特别适合标准化的业务流程和专业领域应用。其智能适配机制如下：

- **上下文感知**：根据当前对话状态调整模板内容
- **个性化定制**：基于用户历史交互优化提示策略
- **多语言支持**：自动适配不同语言环境的提示模板
- **A/B 测试**：支持多版本模板的效果对比

```python
@mcp.prompt("code_review")
def code_review_prompt(language: str, complexity: str):
    """代码审查提示模板"""
    return {
        "role": "资深代码审查专家",
        "context": f"审查 {language} 代码，复杂度：{complexity}",
        "checklist": ["安全性", "性能", "可维护性", "最佳实践"],
        "output_format": "结构化反馈报告"
    }
```

### 5.4 Sampling（采样）

Sampling 是 MCP 的高级能力，允许服务端请求 AI 执行复杂的认知任务，实现多步推理和自我反思，实现认知能力扩展：

- **多步推理**：分解复杂问题，逐步求解
- **自我反思**：评估答案质量，自我纠错
- **创意生成**：头脑风暴、方案设计、创新思维
- **决策分析**：权衡利弊、风险评估、最优选择

### 5.5 能力协同体系

- **工具链集成**：多个 Tools 形成完整的业务流程
- **资源驱动决策**：基于 Resources 数据调用相应 Tools
- **模板引导执行**：使用 Prompts 优化 Tools 的执行效果
- **采样增强智能**：通过 Sampling 提升整体决策质量

---

## 6 MCP 通信协议详解

MCP（Model Context Protocol）采用基于 **JSON-RPC 2.0** 的通信架构，实现了客户端、主机和服务器之间的标准化交互。这种设计选择体现了以下核心理念：

- **简洁性**：JSON-RPC 2.0 提供了最小化但完整的远程调用机制
- **互操作性**：跨语言、跨平台的标准化接口
- **可扩展性**：支持多种传输方式和消息模式
- **可靠性**：成熟的协议基础，经过广泛验证

### 6.1 基础协议：JSON-RPC 2.0

- **优点**：轻量、跨语言、易读，广泛支持。
- **消息类型**：
    - **Request**：客户端发起调用（如 `tools/call`、`tools/list`），带唯一 `id`、`method`、`params` 这些参数。
    - **Response**：服务端响应（带同一 `id`），返回 `result` 或 `error`。
    - **Notification**：服务器单向通知客户端，无需响应（如进度更新、异步事件）。

### 6.2 传输方式

1. **Stdio（标准输入输出）**
    - **进程间通信**：利用操作系统的标准输入输出流
    - **同步通信**：基于行缓冲的 JSON 消息交换
    - **进程隔离**：天然的安全边界和资源控制
2. **HTTP + SSE（Server-Sent Events）**
    - **HTTP 请求**：客户端发送 POST 请求携带 JSON-RPC 消息
    - **SSE 响应**：服务器通过 Server-Sent Events 流式返回数据
    - **连接复用**：支持长连接和连接池管理

---

## 7 MCP 交互生命周期

1. **Initialization（初始化阶段）**
    - 客户端发送 `initialize request` ，协商协议版本、身份、偏好等。
    - 服务器响应 `initialize response`，确认连接并说明其支持的协议版本和可能的服务器信息。
    - 服务端确认后，客户端发送 `initialized` 通知，双方准备就绪。
2. **Discovery（能力发现阶段）**
    - 客户端依次请求 `tools/list`、`resources/list`、`prompts/list` 等，获取所有可用能力及参数描述，供 LLM 决策调用。
3. **Execution（执行阶段）**
    - 客户端根据用户意图和能力清单，发起具体调用（如 `tools/call`、`resources/read`）。
    - 服务端执行并返回结果，同时可通过 `notification` 推送进度、事件等异步信息。
4. **Termination（终止阶段）**
    - 会话结束时，客户端发送 `shutdown` 请求，服务端确认后可发送 `exit` 通知，安全关闭连接和资源。

## 8 MCP vs. FC vs. API

>[!NOTE]
> **"没有什么是加一个中间层不能解决的"**

|   维度    |    MCP    | Function Calling |    API     |
| :-----: | :-------: | :--------------: | :--------: |
| **定位**  |  统一能力协议   |     AI 模型特性      |    服务接口    |
| **层级**  |   协议标准层   |      模型能力层       |   应用服务层    |
| **作用域** |   生态系统    |       单一模型       |    单一服务    |
| **本质**  | **抽象层** ✨ |    **适配层** 🔄    | **实现层** ⚙️ |

MCP 是协议标准，Function Calling 是 AI 能力，API 是服务接口。三者处于不同层次，各有优势，可以协同使用。

## 9 Hands-on 实践

本节将通过 Python 的 `fastmcp` 库，演示如何快速构建一个遵循模型上下文协议（MCP）的服务。以下示例代码将创建一个简单的天气服务，该服务包含两个工具（Tools）：一个用于获取城市经纬度，另一个用于查询该地点的天气。

```Python
from fastmcp import FastMCP

# 初始化 FastMCP 应用，并命名为 "Simple Weather Server"
mcp = FastMCP("Simple Weather Server")

@mcp.tool
def get_coordinates(city: str) -> dict:
    """
    根据城市名称获取其地理坐标（经纬度）。
    
    :param city: 城市名称，例如 "北京"。
    :return: 包含城市名称、纬度和经度的字典。
    """
    # 注意：此处为演示目的，返回硬编码的坐标。
    # 实际应用中应调用地理编码 API。
    return {"city": city, "latitude": 39.9042, "longitude": 116.4074}

@mcp.tool
def get_weather(latitude: float, longitude: float) -> dict:
    """
    根据经纬度坐标获取天气信息。
    
    :param latitude: 纬度。
    :param longitude: 经度。
    :return: 包含天气详情的字典。
    """
    # 注意：此处为演示目的，返回硬编码的天气数据。
    # 实际应用中应调用天气服务 API。
    return {
        "latitude": latitude,
        "longitude": longitude,
        "temperature": 20.0,
        "condition": "Sunny"
    }

if __name__ == "__main__":
    # 启动 FastMCP 服务器。
    # 传输方式 (transport) 决定了客户端与服务器的通信机制。
    
    # 方式一：Stdio (标准输入/输出)
    # mcp.run() 
    
    # 方式二：SSE (Server-Sent Events)，监听于 8080 端口
    mcp.run(transport="sse", port=8080)
```

服务启动后，可以通过兼容 MCP 的客户端（如 CherryStudio, Cursor）或官方调试工具与其交互。官方调试器（MCP Inspector）可通过以下命令启动：

```shell
npx -y @modelcontextprotocol/inspector
```

启动后，在浏览器中访问 `http://localhost:6274/`，并附上认证令牌。

> **重要提示** 访问调试器时，必须携带 `MCP_PROXY_AUTH_TOKEN` 参数，其值可在 MCP 服务器启动时的终端输出中找到。 示例 URL: `http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=your_token_here`

![MCP Inspector](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/Pasted%20image%2020250630152955.png)

为了深入理解 MCP 的工作机制，我基于代理捕获所有的通信日志并分析了基于 SSE 的通信全过程。其核心在于一个两阶段的连接建立过程：首先通过初始 SSE 端点获取一个动态的、带会话 ID 的通信端点，然后所有后续业务交互都在这个新端点上进行。

详细流程分解如下：

1. **建立 SSE 连接**: 客户端向初始端点（例如 `http://localhost:8080/sse/`）发起一个 HTTP GET 请求。请求头中必须包含 `Accept: text/event-stream`，以表明其期望建立 SSE 连接。服务器以 `HTTP 200 OK` 响应，保持连接开放。注意是 `/sse/` 否则会有一次重定向。
2. **端点发现 (Endpoint Discovery)**: 连接建立后，服务器立即通过 SSE 推送一条 `endpoint` 事件，其 `data` 字段包含了用于后续通信的、唯一的会话端点 URL。

    ```txt
    event: endpoint 
    data: /messages/?session_id=xxx
    ```

    此步骤将通信引导至一个专用的、具有会话隔离能力的路径。

3. **初始化请求 (Initialize)**: 客户端向步骤 2 中获取到的新端点（`/messages/?session_id=...`）发送一个 HTTP POST 请求，请求体为 JSON-RPC 格式，`method` 为 `initialize`。
4. **初始化响应**: 服务器接收到初始化请求后，会立即以 `HTTP 202 Accepted` 状态码关闭该 POST 请求。随后，通过之前建立的 SSE 连接推送初始化结果。这通常包含两条消息：一条 `message` 事件通知，紧接着一条 `data` 事件，其中包含具体的初始化数据（如服务器能力、可用工具列表等）。
5. **初始化确认 (Initialized Notification)**: 客户端在成功处理初始化信息后，会再次向会话端点发送一个 POST 请求，请求体为 `{"method":"notifications/initialized","jsonrpc":"2.0"}`，以此通知服务器客户端已准备就绪。
6. **后续通信**: 此后的所有交互，例如列出客调用工具（Tool Calls），都将遵循类似的 `POST 请求 -> SSE 响应` 模式，在同一个会话端点上进行。

> **核心问题**：在将 MCP 服务部署于反向代理（如 NGINX Ingress）之后，一个常见的挑战源于上述的"端点发现"机制。服务器在响应体中动态下发的会话端点 URL（如 `/messages/?…`）是一个相对路径，反向代理默认不会重写响应体中的内容。这导致客户端收到的地址是服务的内部地址，如果代理配置了路径前缀（Path Prefix），客户端将无法正确访问该端点，导致通信失败。
> **解决方案**：
> 1. **响应体内容重写 (Response Body Rewriting)** 利用反向代理的高级功能，在响应返回给客户端前，动态替换响应体中的 URL。例如，`NGINX Ingress Controller` 的 `sub_filter` 指令可以实现此功能，将内部路径替换为可公开访问的完整路径。
> 2. **使用高级 API 网关插件 (Advanced API Gateway Plugins)** 许多现代 API 网关（如 Kong, APISIX）提供插件或脚本能力，可以编写逻辑来拦截和修改响应体，实现更灵活的地址转换。
> 3. **依赖请求头进行动态路径构建 (Recommended)** 这是一种更优雅的后端解决方案。让后端应用感知其代理环境。在反向代理中配置 `X-Forwarded-Prefix` 或类似的标准请求头，将公开访问的路径前缀传递给后端。后端 MCP 服务在生成会话端点 URL 时，读取此请求头并将其拼接到 URL 的最前端。这种方式无需修改代理的响应，耦合度更低。

## 10 MCP 客户端和服务端实现

我们可以动手编程实现一个 MCP 客户端和服务器。客户端的核心职责是连接 MCP 服务器、处理用户查询并协调 LLM 与工具的交互。

![image.png](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/20250621150033.png)

**实现流程：**

1. **工具发现** - 从 MCP 服务器获取可用工具列表
2. **查询处理** - 将用户查询和工具信息一起发送给 LLM
3. **工具调用** - 检测并解析 LLM 输出中的工具调用指令
4. **结果整合** - 执行工具后将结果反馈给 LLM
5. **循环迭代** - LLM 根据工具结果决定继续调用工具或输出最终答案

这种设计让 LLM 能够智能地进行多轮工具调用，直到完成复杂任务并给出最终响应。

## 11 MCP Resources & Prompts

### 11.1 Resources

在 MCP（Model Context Protocol）框架中，**Resources** 是三大核心能力之一，专门用于为 AI 模型提供**只读的上下文信息**。与工具（Tools）不同，Resources 不执行任何操作，而是作为**智能知识库**，让模型能够访问和推理各种结构化信息。

>⚠️ Resources 是纯粹的信息接口，不会产生任何副作用，为 AI 工作流提供安全、可预测的上下文供给方式。资源的内容如果发生变更，需重新加载，模型上下文才会感知到变化。

- **直接资源**：通过 `/resources/list` 接口暴露，适合静态、已知资源。
- **资源模板**：使用 URI 模板 `file://{path}` 暴露从而实现动态资源发现，适合大规模、动态内容。

### 11.2 Prompts

在 MCP（Model Context Protocol）框架中，**Prompts** 是第三个核心原语，用于封装可重用的 LLM 指令模板。如果说工具让模型"行动"，资源让模型"获取信息"，那么提示就是指导模型如何"思考"——塑造其角色、推理策略和输出方式。

Prompts 将 MCP 从简单的任务执行层提升为**上下文感知的智能接口协议**：

1. **认知塑造**：不仅让 LLM 基于工具和数据行动，还能以一致、结构化的方式调整语调、目的和目标
2. **可重用性**：参数化指令让交互变得可组合、可解释、可共享
3. **表达力扩展**：提示不仅是模板，更是提供给 LLM 的可重新配置的心智模型

通过 Tools（行动）、Resources（认知）、Prompts（思考）的三位一体，MCP 成为设计智能系统的完整语言。

当前主流的 MCP 客户端对资源支持普遍较弱。理论上，Claude Desktop 应该同时支持提示词和资源，但我在试用时未能正常使用资源；Cline 虽支持资源，但不支持提示词；CherryStudio 则似乎都不支持使用。不过，在 Agent 中，这一切都由我们自主掌控，资源与提示词的使用方式完全可定制！

### 11.3 总结

|      原语       | 控制方式 | 主要用途 |       使用场景       |
| :-----------: | :--: | :--: | :--------------: |
|   **Tools**   | 模型控制 | 执行操作 | 动态数据获取、计算、API 调用 |
| **Resources** | 应用控制 | 提供知识 |   静态文档、配置、背景信息   |
|  **Prompts**  | 用户控制 | 指导思考 |   标准化工作流、专业指导    |

## 12 Sampling 采样

### 12.1 核心概念

MCP（Model Context Protocol）采样是一个革命性的功能，它实现了**双向架构**的核心理念。传统的 MCP 架构中，客户端调用服务器的工具、资源和提示，但采样机制彻底改变了这种单向流动模式。通过采样，**服务器可以反向请求客户端的 LLM 执行文本生成任务**，这种"反转"创造了一个真正的双向智能协作环境。

采样的本质是**智能任务的分布式委托**。当服务器在执行过程中需要进行自然语言理解、生成或推理时，它不再需要自己集成 LLM 或调用外部 API，而是可以将这些计算密集型任务委托给客户端的模型。这种设计带来了显著的架构优势：首先是**可扩展性**，服务器避免了计算密集型的推理工作，能够处理更多并发请求；其次是**成本效率**，所有 LLM 相关的 API 成本和计算负载都由客户端承担；第三是**模型选择的灵活性**，不同客户端可以使用不同的模型，服务器无需修改；最后是**避免瓶颈**，每个用户的环境处理自己的请求，防止服务器端队列堆积。

### 12.2 架构流程详解

采样的完整执行流程体现了 MCP 协议的精妙设计。当服务器的工具函数运行时，通过调用 `ctx.sample()` 方法触发采样请求。这个调用并不在本地执行，而是将请求打包成标准化的 MCP 消息发送给客户端。客户端接收到请求后，触发用户定义的 `sampling_handler()` 函数，该函数负责处理请求的具体逻辑，包括格式化提示、处理重试等。

客户端随后使用外部 LLM API（如 OpenAI）或本地模型（如 LLaMA、Mistral）来完成请求，生成的文本作为完成结果返回给服务器。服务器接收到结果后，恢复在 `ctx.sample(…)` 处等待的协程执行，使用 LLM 生成的输出继续工具函数的执行。整个过程是异步的，服务器的工具协程会暂停直到结果返回，避免阻塞其他任务。

![image.png](https://ceyewan.oss-cn-beijing.aliyuncs.com/obsidian/20250701075403.png)

FastMCP 通过**Context 对象**为服务器函数提供强大的能力句柄。Context 不仅支持 LLM 采样请求，还能访问日志记录、发送更新等功能。FastMCP 会在工具函数包含 Context 参数时自动注入这个上下文对象。需要注意的是，Context 对象仅在请求期间有效，不能作为全局变量存储和在工具调用外使用。

`ctx.sample()` 方法是采样功能的核心接口，它接受多个参数来控制生成行为。`messages` 参数可以是单个字符串（被视为用户消息）或消息列表；`system_prompt` 参数设置系统指令，为 LLM 的行为提供高级指导；`temperature` 参数控制输出的随机性，较低值产生更确定性的输出；`max_tokens` 参数限制生成的最大令牌数。

### 12.3 服务端和客户端实现

服务器端的采样实现相对直观。在工具函数中，通过 `await ctx.sample(…)` 调用来请求客户端 LLM 的完成。例如，一个文档摘要工具可能会这样实现：

```python
@mcp.tool()
async def summarize_document(text: str, ctx: Context) -> str:
    response = await ctx.sample(
        messages=f"Please summarize the following document: {text}",
        system_prompt="You are an expert summarizer. Provide concise, accurate summaries.",
        temperature=0.7,
        max_tokens=300
    )
    return response.text
```

这种实现方式展现了采样的优雅性：服务器只需要专注于业务逻辑，而将复杂的文本生成任务委托给客户端的智能模型。

客户端需要定义一个采样处理函数来响应服务器的采样请求。这个处理函数接收 `SamplingMessage` 对象列表、`SamplingParams` 参数对象和 `RequestContext` 上下文信息。处理函数的职责是将服务器的请求转换为适合 LLM 的格式，调用相应的模型 API，并返回生成的文本。

一个典型的采样处理函数会构建符合 LiteLLM 格式的消息列表，处理系统提示，迭代处理消息内容，并在 try/except 块中调用 LLM 以处理潜在的网络或 API 错误。处理函数返回的字符串会被封装在 TextContent 对象中发送回服务器。

### 12.4 模型偏好设置

FastMCP 的采样 API 包含 `model_preferences` 参数，允许服务器提示或请求客户端使用特定模型。这个可选功能在某些场景下非常有价值，比如服务器知道某个任务最适合特定模型，或用户指定了模型选择。模型偏好可以是单个字符串、字符串列表（按优先级排序）或结构化的 ModelPreferences 对象。

客户端的采样处理函数可以检查 `params.modelPreferences` 并决定如何路由请求。不过，客户端没有义务遵循偏好设置，这更多是一种提示或请求。良好行为的客户端会尝试使用指定模型，但如果无法访问，会使用默认模型或检查其他支持的偏好模型。

### 12.5 应用场景与高级模式

采样开启了众多应用可能性。**文本摘要**场景中，服务器可以获取数据并调用 `ctx.sample` 进行摘要，用户无需服务器自带摘要模型。**复杂问答或分析**场景结合了逻辑处理和 LLM 推理，比如销售数据分析工具先从数据库提取数字，然后需要 LLM 解释这些数据的洞察。**数据分类**场景中，虽然简单分类可以用代码完成，但使用 LLM 可以提高细致案例的准确性。

更高级的应用包括**链式推理调用**，工具可以多次顺序调用 `ctx.sample` 来分解问题。例如，数学求解工具可能先调用 `ctx.sample` 获取逐步推理，然后解析验证推理过程，再次调用获取最终答案。**代理行为**模式结合工具使用和采样创建类似代理的行为，比如研究工具内部使用采样头脑风暴问题列表，为每个问题调用 API 获取信息，然后再次采样让 LLM 编译报告。

### 12.6 完整代码示例

以下是一个集成采样功能的完整 MCP 服务器和客户端实现：

```python
# server.py - MCP服务器端
from fastmcp import FastMCP, Context

mcp = FastMCP("SamplingDemo")

@mcp.tool()
async def analyze_sentiment_with_summary(text: str, ctx: Context) -> str:
    """分析文本情感并提供详细摘要"""
    try:
        # 第一次采样：分析情感
        sentiment_response = await ctx.sample(
            messages=f"Analyze the sentiment of this text: {text}",
            system_prompt="You are a sentiment analysis expert. Classify as positive, negative, or neutral with confidence score.",
            temperature=0.3,
            max_tokens=1000,
            model_preferences=["openai/qwen-turbo-latest"]
        )

        # 第二次采样：生成详细摘要
        summary_response = await ctx.sample(
            messages=f"Provide a detailed summary of this text: {text}",
            system_prompt="You are a professional summarizer. Create comprehensive yet concise summaries.",
            temperature=0.7,
            max_tokens=1000
        )

        return f"Sentiment Analysis: {getattr(sentiment_response, 'text', str(sentiment_response))}\n\nSummary: {getattr(summary_response, 'text', str(summary_response))}"

    except Exception as e:
        await ctx.error(f"Sampling failed: {str(e)}")
        return f"Analysis failed, but here's basic info: Text length is {len(text)} characters."

if __name__ == "__main__":
    mcp.run("sse", port=8080)

# client.py - MCP客户端端
import asyncio
from fastmcp import Client
from fastmcp.client.sampling import SamplingMessage, SamplingParams
from mcp.shared.context import RequestContext
import litellm
import os


# Qwen 配置
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = "openai/qwen-plus-latest"  # 可根据需要更换


async def sampling_handler(
    messages: list[SamplingMessage],
    params: SamplingParams,
    ctx: RequestContext
) -> str:
    """处理服务器的采样请求"""
    try:
        if not QWEN_API_KEY:
            return "Error: QWEN_API_KEY 环境变量未设置"
        # 构建消息格式
        chat_messages = []

        # 添加系统提示（如果有）
        if params.systemPrompt:
            chat_messages.append({
                "role": "system",
                "content": params.systemPrompt
            })

        # 添加对话消息
        for msg in messages:
            # 安全获取 text 属性，兼容 ImageContent/AudioContent 等
            content = getattr(msg.content, 'text', str(msg.content))
            chat_messages.append({
                "role": msg.role,
                "content": content
            })

        # 处理模型偏好
        model_to_use = QWEN_MODEL  # 默认用 Qwen
        if params.modelPreferences and params.modelPreferences.hints and params.modelPreferences.hints[0].name:
            model_to_use = params.modelPreferences.hints[0].name or QWEN_MODEL

        # 确保 model_to_use 是字符串且不为 None
        if not isinstance(model_to_use, str) or not model_to_use:
            model_to_use = QWEN_MODEL

        # 调用LLM，传递 Qwen 的 base_url 和 api_key
        response = await litellm.acompletion(
            model=model_to_use,
            messages=chat_messages,
            temperature=params.temperature or 0.7,
            max_tokens=params.maxTokens or 500,
            base_url=QWEN_BASE_URL,
            api_key=QWEN_API_KEY
        )

        # 只用 dict 方式安全提取内容
        if isinstance(response, dict):
            try:
                content = response['choices'][0]['message']['content']
                if content is not None:
                    return str(content)
            except Exception:
                pass
            try:
                text = response['choices'][0]['text']
                if text is not None:
                    return str(text)
            except Exception:
                pass
            return str(response)
        # 兜底：直接转字符串
        return str(response)
    except Exception as e:
        return f"Error generating response: {str(e)}"


async def main():
    # 连接到MCP服务器
    async with Client("http://localhost:8080/sse/", sampling_handler=sampling_handler) as client:
        # 调用工具
        result = await client.call_tool(
            "analyze_sentiment_with_summary",
            {"text": "I absolutely love this new technology! It's revolutionary and will change everything for the better."}
        )
        print("Analysis Result:")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

这个示例展示了采样的完整生命周期：服务器端工具进行双重采样（情感分析和摘要生成），客户端处理函数智能路由请求到合适的模型，并且包含了错误处理和模型偏好设置。通过这种方式，我们实现了一个既强大又灵活的分布式 AI 系统，服务器专注于业务逻辑，而将智能生成任务委托给客户端的模型资源。

![image.png](https://ceyewan.oss-cn-beijing.aliyuncs.com/obsidian/20250701105700498.png)

在这个架构中，Context 对象扮演着双重角色。服务器端的 Context 是业务编排器，提供 `ctx.sample()` 发起采样请求和 `ctx.info/error/debug()` 记录日志的能力，不是客户端向服务器传递 `ctx` 参数，而是由 FastMCP 框架自动创建并注入到每个工具调用中。客户端的 RequestContext 则是执行上下文，为每次采样提供请求元数据（如 request_id、session_id）和执行环境信息，支持智能路由和资源管理。

系统的核心特性体现在采样的完全独立性上。服务器端的两次 `ctx.sample()` 调用（情感分析和摘要生成）是完全独立的，客户端的 `sampling_handler` 接收到两个独立的请求，每次都有唯一的 request_id 和独立的参数配置，不存在状态共享。同时，系统支持智能模型路由，服务器端可以通过 `model_preferences` 指定模型偏好，客户端根据这些偏好智能选择最适合的 LLM 进行推理。

## 13 测试、安全性和沙箱

在 MCP 环境的测试与验证中，官方提供的 **MCP Inspector** 工具扮演着核心角色。它提供了一套全面的功能，允许用户深入查看和管理相关的工具、资源、提示词配置以及采样功能，同时也能有效测试系统间的连接性，确保整个 MCP 生态系统的健壮性与协同工作能力。

为了保障 MCP Server 的安全与稳定运行，采用沙箱化部署是关键实践。通过利用 Docker 等容器化技术，我们可以为 MCP Server 建立一个受严格限制的运行环境。这种沙箱机制能够有效地定义并约束服务器的能力边界，从而显著降低潜在的安全风险，并确保其操作的隔离性与可控性。

MCP 系统面临的主要安全挑战源于其设计特点：AI 模型可以轻松访问文档、数据、API 等各种资源，但这种便利性如果处理不当，就可能成为系统的薄弱环节。在企业和消费级环境中，我们需要确保只有经过批准的工具被使用，只有预期的数据被共享，并且没有恶意行为能够悄悄渗透。

### 13.1 主要攻击方法

1. **提示注入攻击**：提示注入是一类将恶意指令隐藏在用户内容或外部数据中的攻击方式。AI 系统无法区分哪些指令是真实的，哪些是攻击的一部分，因为它们在 LLM 眼中都只是文本。攻击者可以通过在正常请求中嵌入恶意指令来覆盖原始任务，从而控制模型的行为。
2. **工具污染攻击**：工具污染是提示注入的一种变体，攻击者将恶意指令隐藏在 MCP 工具的描述中。这种攻击特别危险，因为工具描述对用户来说通常是不可见的，但对 AI 模型完全可见。攻击者可以在看似无害的计算器工具描述中嵌入恶意指令，让 AI 在执行正常计算的同时，秘密读取用户的私钥或配置文件，并将这些敏感信息发送到攻击者控制的服务器。
3. **跑路攻击**：在跑路攻击中，恶意服务器在获得用户信任后，悄悄更改其工具描述或行为。由于大多数 MCP 客户端不会通知用户工具描述的变更，用户可能在不知情的情况下继续使用已被篡改的工具。
4. **过度能力暴露**：MCP 系统中客户端和服务器双向暴露能力，恶意服务器可能滥用客户端的 LLM 资源，通过采样工作流控制 LLM 行为，可能导致费用增加或资源滥用。
5. **服务器名称冲突和工具名称冲突**：攻击者可以注册与热门服务器几乎相同名称的恶意服务器，或者创建与合法工具同名的恶意工具。由于客户端通常依赖名称和简短描述来识别工具，用户可能误装恶意服务器或工具，导致敏感数据泄露。

### 13.2 MCP Roots

MCP Roots 是一种类似沙箱的边界机制，它为 MCP 服务器定义了明确的操作范围。通过设置 Roots，客户端可以告诉服务器："你只能在这个特定的文件夹、数据库或 API 路径中操作。"Roots 以 URI 形式表示，如文件路径、API 端点或数据库模式，它们限制了服务器的访问范围。

MCP Roots 通过限制服务器的访问范围来提供多层安全保护。首先，它们限制了数据泄露的可能性，因为 AI 无法泄露它看不到的内容。其次，它们减少了隐私风险，因为根目录之外的个人或机密数据保持隐藏状态。最后，它们提升了用户信任度，因为用户明确知道哪些数据在访问范围内。

在连接握手过程中，支持 Roots 的客户端会声明其支持并提供根 URI 列表。服务器确认这些根目录并相应地限制其操作范围。如果根目录发生变化，客户端会发送更新，服务器会调整其可访问的数据范围。所有搜索、文件操作或资源列表都被严格限制在指定的根目录内。

通过正确配置 Roots，即使面对巧妙的提示注入攻击，系统也能保持安全。例如，在前面提到的文件系统攻击案例中，如果设置了适当的根目录限制，服务器就无法访问 `.bashrc` 文件或其他敏感系统文件，从而阻止了后门的植入。