---
categories:
  - AI Agent
date: 2025-07-04T18:57:45+08:00
draft: false
summary: AI 智能体凭借动态推理与自主决策能力，超越传统 RAG 系统与固定逻辑软件，展现更强适应性与扩展性。通过角色定义、任务分工、工具集成及多智能体协作机制，结合安全控制与记忆管理，实现高效精准的任务执行，推动自动化系统迈向真正智能化。
tags:
  - Agent
title: Agentic Systems 101
slug: 20250705-va9tp119
---

## 1 CrewAI 基础

在构建现代人工智能系统的过程中，AI 智能体（AI Agents）展现出相较于传统方法更强大的灵活性与自主性。

### 1.1 AI 智能体的动机

1. **RAG 系统的视角**：虽然检索增强生成（RAG）技术在信息扩展方面表现优异，但其程序化的流程限制了系统的自主决策能力。相比之下，AI 智能体具备动态推理和规划能力，能够根据任务需求自主选择信息源，实现更高程度的任务自动化。
2. **软件开发视角**：传统软件依赖于固定输入、预设逻辑和标准化输出，而 AI 智能体则支持多样化的输入格式（如文本、PDF、JSON 等），并基于大语言模型（LLM）进行灵活转换，输出形式也更加丰富，包括代码、结构化数据等，极大提升了系统的适应性和扩展性。
3. **自主系统视角**：AI 智能体突破了传统 LLM 需要频繁人工干预的交互模式，能够将复杂目标分解为子任务，逐步执行并自我优化，从而显著减少人为参与，提升整体效率。

### 1.2 AI Agents 的构建模块

- **角色扮演（Role-playing）**：赋予智能体明确的专业身份，有助于提升响应的专业性和一致性。例如，"企业法律事务律师"比"通用助手"更具针对性。
- **任务聚焦（Focus/Tasks）**：专业化分工优于多功能集成。每个智能体应专注于单一任务，通过多智能体协作完成复杂工作流，避免功能重叠和冲突。
- **工具集成（Tools）**：外部工具的使用极大增强了智能体的能力。工具选择应遵循"精简有效"的原则，优先配置完成任务所需的核心工具。
- **协同机制（Cooperation）**：多智能体系统通过任务划分与上下文共享，实现相互反馈与结果优化，从而提升整体系统的决策质量与执行效率。
- **安全护栏（Guardrails）**：为防止幻觉、无限循环或错误决策，需设置使用限制、验证检查点及回退机制，确保智能体行为可控可靠。
- **记忆管理（Memory）**：智能体的记忆可分为短期记忆（如对话历史）、长期记忆（如用户偏好）和实体记忆（如客户信息），合理设计记忆机制有助于提升个性化服务能力和系统连续性。

AI 智能体代表了从传统自动化向真正自主智能系统演进的重要方向。通过科学的角色定义、任务分配、工具整合与协作机制，结合有效的安全控制与记忆系统，AI 智能体能够在复杂环境中实现高效、精准的任务执行，成为未来智能系统构建的关键支柱。

### 1.3 使用 CrewAI 构建 Agent

构建一个功能性的 AI Agent 系统在 CrewAI 中被清晰地划分为三个核心步骤：**定义智能体 (Agents)**、**分配任务 (Tasks)** 和 **组建团队 (Crew)**。

智能体是您团队中的"执行者"。它不仅仅是一个简单的语言模型调用，而是一个被赋予了特定 **角色 (Role)**、**目标 (Goal)** 和 **背景故事 (Backstory)** 的虚拟专家。这种设定为其行为和决策提供了丰富的上下文，使其输出更具针对性和专业性。

有了智能体，我们还需要为其分配具体的工作，这就是 **任务 (Task)** 的作用。一个好的任务定义应该清晰、具体，并包含对最终成果的预期。

当智能体和任务都准备就绪后，最后一步就是将它们组织起来，形成一个 **团队 (Crew)**。Crew 负责管理整个工作流程的执行。

```Python
from crewai import Agent, Task, Crew

# 创建智能体
senior_technical_writer = Agent(
    role="高级技术写作专家",
    goal="创作发布级别的技术文章",
    backstory="您是一位经验丰富的研究员，擅长发现AI领域的最新发展。xxx",
    tools=[file_write_tool],
    verbose=True,
    llm=llm  # 指定使用的语言模型
)

# 创建任务 
writing_task = Task( 
    description="基于主题 {topic} 撰写一篇全面的技术文章", 
    agent=senior_technical_writer, 
    tools=[file_write_tool],
    expected_output="一篇结构化的技术文章，包含引言、主要内容和结论" 
)

# 组建团队
crew = Crew(
    agents=[senior_technical_writer],
    tasks=[writing_task],
    verbose=True
)

# 执行任务
result = crew.kickoff(inputs={"topic": "AI智能体的未来发展"})
```

- `role` (str): 智能体的"职位头衔"。它明确了智能体在团队中的身份和职责，例如"市场分析师"、"资深软件工程师"或"代码审查员"。这直接影响其沟通风格和专注点。
- `goal` (str): 智能体的核心任务目标。这是它所有行动的最终导向，是衡量其工作是否成功的标准。一个清晰的 `goal` 能让智能体更有效地规划步骤。
- `backstory` (str): 这是塑造智能体"性格"和"经验"的关键。一段丰富的背景故事能为 LLM 提供强大的上下文，使其在生成内容时，无论是语气、措辞还是思考深度，都更贴近所扮演的角色。
- `description` (str): 任务的核心描述。这是给智能体的"任务简报"。注意，这里使用了 `{topic}` 占位符，这使得任务可以动态接收输入，极大地提高了复用性。
- `agent` (Agent): 指定执行此任务的智能体实例。通过这个参数，我们将 `writing_task` 与 `senior_technical_writer` 绑定在一起。
- `expected_output` (str): 定义任务的"完成标准 (Definition of Done)"。这部分至关重要，它为智能体提供了明确的交付物形态和质量要求，有效避免了结果的模糊和不可控。描述越具体，产出质量越高。

---

CrewAI 的真正威力体现在多智能体协作上。你可以定义一个由研究员、写作者、审查员等组成的流水线，让它们接力完成复杂任务。

```python
# 创建多智能体工作组 
multi_agent_crew = Crew( 
    agents=[research_agent, summarization_agent, fact_checking_agent],
    tasks=[research_task, summarization_task, fact_checking_task],
    process=Process.sequential,  # 按顺序执行任务
    verbose=True 
) 

# 执行工作流 
result = multi_agent_crew.kickoff(inputs={"topic": "量子计算的最新突破"})
```

- `agents` (list): 包含此团队中所有智能体实例的列表。
- `tasks` (list): 包含需要被执行的所有任务实例的列表。
- `process` (Process): 定义任务的执行流程。这是多智能体协作的核心。
    - `Process.sequential`（顺序流程）: 任务将按照它们在 `tasks` 列表中的顺序依次执行。前一个任务的输出会自动作为后一个任务的上下文，形成一个完美的工作流管道。
    - `Process.hierarchical`（层级流程）: 更复杂的模式，通常会有一个"经理"智能体来协调和委派任务给其他"员工"智能体。
- `kickoff(inputs: dict)`: 这是启动整个团队工作的入口方法。`inputs` 字典用于填充任务描述中定义的占位符（如 `{topic}`），从而启动整个流程。

### 1.4 模块化

随着智能体系统复杂度的增加，将所有配置（角色、任务、背景故事等）硬编码在主脚本中会变得混乱且难以维护。为了解决这个问题，我们可以采用一种更优雅、更具扩展性的模块化架构。将智能体和任务的定义从执行逻辑中分离出来，通过**独立的 YAML 配置文件**进行管理，并使用一个专门的 **Python 类来组织和加载整个工作流**（Crew）。

我们将通过三个核心步骤实现模块化：

1. **分离配置文件**：创建独立的 YAML 文件来定义智能体 (`agents.yaml`) 和任务 (`tasks.yaml`)。
2. **创建模块化 Crew 类**：使用 `crewai` 提供的装饰器 (`@CrewBase`, `@agent`, `@task`, `@crew`) 在一个 Python 类中"声明式"地组装工作流。
3. **简洁的执行入口**：在主程序中，只需实例化该类并调用其 `crew()` 方法即可启动任务。

```Python
@CrewBase  
class ResearchCrew:  
    """一个负责开展研究、归纳成果并进行事实核查的Crew"""  
    agents_config = 'config/agents.yaml'  
    tasks_config = 'config/tasks.yaml'  
    def __init__(self):  
        self.search_tool = SerperDevTool()  
        self.llm = llm  
    @agent  
    def research_agent(self) -> Agent:  
        return Agent(  
            config=self.agents_config['research_agent'],  
            tools=[self.search_tool],  
            llm=self.llm  
        )   
    @task  
    def research_task(self) -> Task:  
        return Task(  
            config=self.tasks_config['research_task'],  
            tools=[self.search_tool],  
        )  
    @crew  
    def crew(self) -> Crew:  
        return Crew(  
            agents=self.agents,  
            tasks=self.tasks,  
            process=Process.sequential,  
        )
```

`@CrewBase` 装饰器提供的便利使得指定路径 (`agents_config`) 就能当字典 (`self.agents_config[…]`) 使用。其内部工作流如下：

1. **识别配置路径**：当 `@CrewBase` 装饰器处理 `ResearchCrew` 类时，它会扫描类属性，找到了 `agents_config = 'config/agents.yaml'` 和 `tasks_config = 'config/tasks.yaml'`。
2. **自动加载和解析**：在类的 `__init__` 方法被调用之前或期间，`@CrewBase` 的底层逻辑会**自动**读取这些路径指向的 YAML 文件。
3. **数据转换**：它使用一个 YAML 解析库（如 PyYAML）将文件内容转换成 Python 的字典对象。
4. **属性覆盖**：最后，它将解析后的字典**覆盖**回同名的实例属性上。

`self.agents` 和 `self.tasks` 没有在 `__init__` 中被显式定义。它们是由 `@agent` 和 `@task` 装饰器**动态注入**到类实例中的。工作流程如下：

1. 当你创建实例 `crew_instance = ResearchCrew()` 时，`@CrewBase` 的逻辑开始运行。
2. 框架会查找所有被 `@agent` 装饰的方法（这里是 `research_agent`），并执行它。
3. `research_agent()` 方法返回一个 `Agent` 对象。
4. `@agent` 装饰器捕获这个返回的对象，并将它添加到一个名为 `agents` 的列表中。这个列表被附加到 `crew_instance` 实例上，成为 `self.agents`。
5. 对所有 `@task` 装饰的方法执行完全相同的过程，最终生成 `self.tasks` 列表。

### 1.5 结构化输出

默认情况下，大语言模型（LLM）就像一位才华横溢但天马行空的艺术家，其输出是自由流动的文本。这在日常对话中表现出色，但在需要程序化处理的自动化工作流中，却是一个巨大的挑战。程序如何才能可靠地使用一个时而是段落、时而是列表的输出呢？

解决方案是建立一份"契约"。我们需要强制 LLM 的输出遵循一个可预测的、结构化的格式，比如 JSON。这就是**结构化输出**的用武之地，而 Pydantic 正是我们用来定义这份"数据契约"的首选工具。

**核心原理：** 我们不再仅仅要求 LLM 描述一个答案，而是给它一个数据模板，并要求它填写这份模板。

首先，我们使用 Pydantic 的 `BaseModel` 来精确定义我们期望的数据结构。这个类就像一个蓝图。至关重要的是，我们为每个字段提供的 `description`（描述）会成为给 LLM 的直接指令。

假设我们需要提取货币转换所需的详细信息，我们的契约可以这样定义：

```Python
class CurrencyConverterInput(BaseModel):  
    """货币转换工具的输入模式"""  
    amount: float = Field(…, description="要转换的金额")  
    from_currency: str = Field(…, description="源货币代码（例如：'USD'）")  
    to_currency: str = Field(…, description="目标货币代码（例如：'EUR'）")
```

契约定义好后，我们便可以在任务（Task）中指示智能体（Agent）必须遵循它。这通过 `Task` 对象的 `output_pydantic` 参数来实现。

```Python
# 这个任务的唯一目标就是将用户的自然语言请求结构化 
query_task = Task(  
    description="理解用户的自然语言查询，提取总金额、源货币和目标货币。用户查询为：'{query}'",  
    expected_output="对用户查询的结构化响应",  
    agent=query_analyst,  
    output_pydantic=CurrencyConverterInput, 
)
```

当这个任务运行时，CrewAI 会指示 LLM 的最终回复**不能是**一个句子，而**必须是**一个严格遵循 `CurrencyConverterInput` 模型的 JSON 对象。一个像"100 美元等于多少人民币？"这样的模糊查询，就被从凌乱的文本转换为了干净、可供机器读取的数据：`{'amount': 100.0, 'from_currency': 'USD', 'to_currency': 'CNY'}`。

### 1.6 构建自定义工具

智能体是强大的思考者，但它们被禁锢在自己的数字世界里。要执行有意义的行动——比如查询数据库、调用 API 或保存文件——它们需要**工具**。虽然 CrewAI 提供了许多内置工具，但真正的威力在于创建属于你自己的工具。

一个自定义工具，本质上是一个被精心包装的 Python 函数。它拥有明确的 `name`（名称）、`description`（描述）和输入参数模式（`args_schema`），这使得智能体能够理解这个工具能做什么以及如何使用它。

延续上面的例子，让我们构建一个工具，它能接收上一步生成的结构化数据，并调用外部 API 来执行真实的货币转换。

```Python
class CurrencyConverterTool(BaseTool):  
    """货币转换工具类 - 使用实时汇率进行货币转换"""  
    name: str = "货币转换工具"  
    description: str = "使用实时汇率将一种货币的金额转换为另一种货币"  
    args_schema: Type[BaseModel] = CurrencyConverterInput # 参数格式
    api_key: str = os.getenv("EXCHANGE_RATE_API_KEY")
    
    # 工具被调用时执行的函数
    def _run(self, amount: float, from_currency: str, to_currency: str) -> str:  
        """执行货币转换的核心方法"""  
        pass
```

1. **`args_schema`**：我们将工具直接与 `CurrencyConverterInput` 这个 Pydantic 模型关联。这确保了工具只会接收到它期望格式的数据。
2. **`name` & `description`**：这不仅仅是注释。智能体背后的 LLM 会阅读它们，来判断这个工具是否适合用来完成当前的任务。
3. **`_run`**：这是包含你自定义业务逻辑的核心工作方法。

通过结合**结构化输出**和**自定义工具**，我们创造了一个强大而可靠的多智能体工作流，其能力远超单个 LLM 提示所能达到的高度。当用户提出查询："**100 美元等于多少人民币？**"

1. **智能体 1 (查询分析师):** 它的任务是**理解和结构化**。它接收到查询后，由于其任务指定了 `output_pydantic=CurrencyConverterInput`，它不会尝试直接回答问题。相反，它输出一个干净的结构化 Pydantic 对象：`{'amount': 100.0, 'from_currency': 'USD', 'to_currency': 'CNY'}`。这个输出会作为上下文传递给下一个任务。
2. **智能体 2 (货币分析师):** 它的任务是**行动和执行**。它接收到来自智能体 1 的结构化数据。它审视自己的目标和可用的工具，发现了"实时货币转换器"，通过阅读描述，它明白这正是完成任务所需的工具。由于传入的数据与工具的 `args_schema` 完美匹配，它便能可靠地调用 `_run` 方法来获取实时转换结果。

## 2 CrewAI Flows

在构建 AI 智能体系统时，简单的顺序执行已无法满足复杂应用的需求。本文将深入探讨 CrewAI 的强大功能——**Flows**，它为**构建事件驱动**、**状态管理**和**条件分支**的复杂 AI 工作流提供了优雅的解决方案。Flows 的核心理念在于，将传统软件开发的确定性逻辑与大语言模型（LLM）的自主推理能力巧妙融合，从而创造出既可靠又智能的全新系统。

### 2.1 基础构建

Flows 的构建基于两个核心的装饰器，它们像乐高积木一样，是我们搭建工作流的基础：

- **`@start()`**: 标记一个方法的"启动"状态。它告诉 Flow："这是我们旅程的起点。" 当整个流程启动时，所有被 `@start` 标记的方法会最先被执行。
- **`@listen(task_name)`**: 建立方法之间的依赖关系。它让一个方法"聆听"另一个方法的完成信号。一旦被监听的方法执行完毕，这个"聆听者"就会被自动触发，并能直接接收前者的输出作为自己的输入。

```Python
class MovieRecommendationFlow(Flow):
    @start
    def generate_movie_genre(self):
        ...
        return genre # 返回电影类型
        
    @listen(generate_movie_genre)
    def recommend_specific_movie(self, genre):
        # 'genre' 参数自动接收了上一步的返回值 "科幻"
        # … 执行电影推荐的逻辑 …
```

通过这种方式，我们建立了一个清晰的、事件驱动的依赖链：`generate_movie_genre` 完成 -> `recommend_specific_movie` 自动开始。

### 2.2 状态管理

在复杂的流程中，信息需要在不同步骤间传递和更新。比如，用户的 ID、偏好设置、或者中间计算结果。Flows 通过 `self.state` 属性提供了强大的状态管理机制，它就像是整个流程共享的"记事本"。

**1. 非结构化状态 (Unstructured State)**

最简单直接的方式，就是把 `self.state` 当作一个普通的 Python 字典来用。它灵活、便捷，非常适合快速原型设计。

```python
@start def initialize_flow(self): 
    self.state['user_id'] = 12345 # 存入用户ID
    user = self.state['user_id'] # 在另一个步骤中轻松读取
    # 可以做到任意读写
```

**2. 结构化状态 (Structured State)**

当流程变得复杂，随意读写字典容易出错。为了保证数据的类型安全和一致性，我们可以为"记事本"规定一个格式。Flows 通过与 Pydantic 模型集成，完美实现了这一点。

我们首先定义一个 Pydantic 模型作为状态的"模板"，然后在定义 Flow 类时声明它。就像给我们的记事本加上了固定的栏目（如"用户 ID"、"电影类型"、"推荐列表"），并规定了每一栏只能填写特定类型的数据（数字、文本等），从而从根本上杜绝了运行时因数据格式错误引发的问题。

```python
class TaskState(BaseModel):  
    task: str  
    status: str  
  
class MovieRecommendationFlow(Flow[TaskState]):
    # self.state 里面只有两个变量，且类型为 str
```

### 2.3 条件流控制

现实世界的流程充满了选择。Flows 提供了强大的条件逻辑工具，让我们的 AI 工作流能够像经验丰富的决策者一样，根据实时结果动态调整执行路径。

1. `or_` 和 `and_`: 处理多个依赖
    - `or_`: 当一个任务需要等待**多个前置任务中的任意一个**完成时，使用 `or_`。  
        **场景**: 无论是用户通过**在线聊天**提出推荐请求，还是通过**邮件系统**，我们都需要记录这次请求。`@listen(or_(live_chat_request, email_ticket_request))` 就能完美实现这一点。
    - `and_`: 当一个任务**必须等待多个前置任务全部完成**时，使用 `and_`。  
        **场景**: 只有当 AI "**分析完用户历史偏好**"并且"**获取了最新的电影库**"后，才能开始最终的"个性化推荐"任务。
2. `@router`: 智能路由 `@router` 装饰器是实现复杂分支逻辑的利器。它可以将一个方法的返回值作为"路标"，动态地决定接下来应该走向哪条路径（执行哪个任务）。

```Python
class TicketRoutingFlow(Flow[TicketState]):
    @start
    def classify_ticket(self):
        self.state.priority = random.choice(["high", "low"])
        return self.state.priority

    @router(classify_ticket)
    def route_ticket(self, priority):
        if priority == "high":
            return "urgent_support"  # 返回路由值
        else:
            return "email_support"   # 返回路由值

    @listen("urgent_support")
    def assign_to_agent(self):
        print("Ticket assigned to a live agent.")

    @listen("email_support")
    def send_to_email_queue(self):
        print("Ticket sent to the email support queue.")
```

### 2.4 在 Flows 中集成 Crews

Flows 的真正威力在于它能够编排由多个智能体组成的、功能强大的 Crews。你可以将一个复杂的 Crew（比如一个专门负责撰写影评的团队）看作是 Flow 中的一个独立、可调用的"超级任务"。

通过 `crewai new flow <flow_name>` 命令，我们可以快速生成一个标准化的项目结构。在这个结构中，每个 Crew 都有自己独立的配置文件和脚本，而主流程文件 `main.py` 则负责扮演"总指挥"的角色。

在 `main.py` 的 Flow 中，你可以像调用普通函数一样，实例化并启动在其他文件中定义的任何 Crew，将其作为一个步骤无缝地集成到更宏大的工作流中。这使得我们可以构建出层次分明、高度模块化且极其强大的 AI 系统。

### 2.5 社交媒体内容撰写 FLow

随着 AI Agentic 系统的不断发展，单一智能体或单一 Crew 已无法满足复杂实际业务需求。CrewAI Flows 通过支持多 Crew 协作，极大提升了 AI 工作流的灵活性、可扩展性与模块化。


