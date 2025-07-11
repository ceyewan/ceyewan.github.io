## LLM

### Qwen

QWenLLM 是一个基于阿里云 通义千问（Qwen） 大语言模型的封装类，用于在项目中调用 Qwen 的生成能力。它继承自 langchain 的 LLM 基类，并实现了 `_call` 和 `_acall` 方法，以支持同步和异步调用。这个类不仅封装了模型的基本调用逻辑，还加入了**流式输出**、**系统提示模板**、**历史对话管理**等功能。

主要包括初始化，选择的模型、是否流式输出、上下文限制、top_k、 Temperature、Prompt 等。实现同步调用方法、异步调用方法、流式输出（在同步/异步调用时使用）、

构建消息（messages），该方法负责将以下三部分拼接成最终传给 Qwen 的 messages 列表：

- 系统提示（System Prompt）：定义角色和行为。
- 历史对话（History）：如果存在，则将其转换为 Message 对象加入。
- 用户输入（User Message）：作为最后一项加入。

你可以在 LangChain 中像使用其他 LLM 一样使用 QWenLLM：

```python
from llms.qwen import QWenLLM

llm = QWenLLM(model='qwen-plus', streaming=False)

response = llm("请介绍一下 Kubernetes 的架构组成。")
print(response)
```

或者在链式调用中使用：

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

prompt = PromptTemplate.from_template("解释一下 {topic} 的工作原理。")
chain = LLMChain(llm=llm, prompt=prompt)

result = chain.run(topic="Kubernetes")
print(result)
```

### CNPilot

CNPilot 是阿里巴巴集团内部研发的大语言模型系统，专注于支持中文场景下的自然语言理解和生成任务。它被广泛应用于企业内部的各种 AI 助手、智能客服、文档处理等场景。

与 Qwen 不同，CNPilot 更多面向内部服务集成，通常通过 POP（Platform of Platforms）网关进行认证和调用，并依赖于阿里云的访问密钥体系。

除了初始化配置不太一样，其他都大差不差。它对比 Qwen 的区别在于，它的训练数据来自于阿里巴巴内部的语料库，适用于需要在阿里云环境中调用 CNPilot 模型的应用场景，如 ACK 智能助手、运维自动化、YAML 自动生成等。

### Textembedding

## Prompts

这个模块主要实现了一个统一的提示词（Prompt）管理服务接口与工厂模式调用机制。支持 Prompt 不同的存储方式，目前只实现了 LOCAL 版本，定义了抽象类统一了 Prompt 操作接口，包括 pull 和 push，工具类根据配置创建具体的 PromptService 实例，目前只支持本地。

这样，就可以使用全局函数 pull 和 push 方便的调用接口了，不用管 Prompt 是本地存储还是远端存储。使用方式如下（PROMPT_SERVICE_TYPE=LOCAL 写在环境变量里面）：

```python
push("config/new_prompt.yaml", new_content)  # 存储一个 Prompt
content = pull("config/default_prompt.yaml") # 获取一个 Prompt
```

使用了单例模式，确保 LocalPromptService 只被初始化一次。

## Middleware

中间件模块有三个部分，键值对存储、日志、异常。

### tair_service

阿里自研的键值存储，类似 Redis，使用方法差不多其实。这里就是单例模式，操作 TairServiceSingleton 句柄即可。支持以下方法：

```python
def set_tair_kv_with_ttl(self, cache_bucket_key: str, field: str, value: str, ttl_sec: int) -> bool:
```

设置一个带有过期时间（TTL）的键值对。

```python
def get_tair_value_by_key_field(self, cache_bucket_key: str, field: str) -> str:
```

获取指定 key 和 field 的值。

假设你有一个 Key 为 user_profile，其中存储了用户的多个信息字段（Field），比如 name、email 和 age。每个字段可以有不同的过期时间：

```python
tair_service.set_tair_kv_with_ttl("user_profile", "name", "Alice", 3600)  # name 字段有效期为 1 小时
tair_service.set_tair_kv_with_ttl("user_profile", "email", "alice@example.com", 86400)  # email 字段有效期为 1 天
```

在这个例子中：

- user_profile 是 Key。
- name 和 email 是 Field。
- "Alice" 和 "alice@example.com" 是对应的 Value。

>[!NOTE]
>这两个方法使用了 Tair 的 exhset 和 exhget 方法。这些方法属于 Tair 的 Extended Hash（ExHash） 数据结构，它扩展了 Redis 原生 Hash 的功能，支持为每个 field 设置单独的过期时间（TTL）。Key 用于唯一标识一个 ExHash 结构的数据集合。Field 用于在一个 Key 下进一步细分数据。每个 Field 可以有独立的值（Value）和过期时间（TTL），这使得 ExHash 非常适合需要精细化管理数据生命周期的场景。

### Logging

实现了一个用于 FastAPI 应用的 **日志中间件** 和一个 **LangChain 回调处理器**，其主要作用是记录请求、响应以及模型调用链（LLM / Chain）中的详细信息。

只要在 FastAPI 启动时，导入并注册中间件，就可以在所有 HTTP 请求经过时自动记录请求和响应的日志。

```python
from middleware.logging import api_middleware_logging

app = FastAPI()
api_middleware_logging(app)
```

如果使用了 LangChain 的 Runnable 或 Chain，可以将 LoggerCallbackHandler 添加到回调中：

```python
from middleware.logging import LoggerCallbackHandler

chain.invoke(
    {"input": "hello"},
    config={"callbacks": [LoggerCallbackHandler()]}
)
```

这样就能看到每个 LLM 调用、Chain 进入/退出、错误等详细信息。

日志会在有请求到达时，输出包含请求方法、请求路径及参数、客户端 IP 的日志。此外，通过 logger.contextualize(…) 注入了以下上下文字段：

- request_id: 每个请求唯一 ID（可用于追踪日志）
- session_id: 用户会话 ID
- uid: 用户 ID（默认为 0）

LangChain 链式调用日志，使用了 LoggerCallbackHandler 后，就会支持将 LLM、Chain 的开始、结束、错误事件进行结构化打印。

### Exception

实现了一个 全局异常处理中间件，用于统一捕获和处理 FastAPI 应用中的各类异常（如 HTTPException、自定义异常 CommonException、验证错误等），并返回结构化的 JSON 错误响应。

注册异常中间件：

```python
from middleware.exception import api_middleware_exception

app = FastAPI()
api_middleware_exception(app)
```

当在业务逻辑中抛出任何异常（无论是 FastAPI 原生的 HTTPException、自定义的 CommonException，还是其它运行时异常），这个中间件都会自动拦截并返回结构化的 JSON 错误响应给调用方，而你无需在每个接口中手动 try-except 处理异常。
