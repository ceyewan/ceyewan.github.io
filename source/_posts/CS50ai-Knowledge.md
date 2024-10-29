---
title: CS50ai-Knowledge
categories:
  - AI
tags:
  - CS50ai
abbrlink: 84d7f84a
date: 2024-10-29 18:32:11
---

# CS50ai-Knowledge

## 总结

```markdown
# 知识表示与逻辑推理

## 一、基础概念

### 1. 知识型智能体
- **定义**：能够通过对知识的内部表示进行操作来实现推理的智能体
- **核心要素**：句子(用知识表示语言对世界的断言)

### 2. 命题逻辑系统
- **命题符号**：使用P、Q、R等字母表示可真可假的陈述
- **真值模型**：为命题分配真值的集合，n个命题有2^n个可能模型
- **知识库(KB)**：智能体掌握的命题集合

### 3. 逻辑连接词

1. 否定(¬): 反转真值
2. 合取(∧): 且，全真才真
3. 析取(∨): 或，有真则真
   - 包含或：允许同真
   - 排他或(⊕)：不允许同真
4. 蕴含(→): if P then Q
   - P为前件，Q为后件
   - P假时永真(trivially true)
5. 双条件(↔): 当且仅当，等价关系


## 二、推理系统

### 1. 基本概念
- **蕴含关系(⊨)**：若α⊨β，则α真时β必真
- **推理过程**：从已知句子推导出新句子

### 2. 推理方法

1. 模型检查法
   - 枚举所有可能模型
   - 验证KB为真时α是否为真
   
2. 推理规则法(更高效)
   - 假言推理：P→Q且P，则Q
   - 合取消去：P∧Q，则P
   - 双重否定：¬(¬P)，则P
   - 蕴含消去：P→Q，则¬P∨Q
   - 德摩根定律：¬(P∧Q)≡¬P∨¬Q

### 3. 归结原理(Resolution)

核心思想：通过补充文字(P和¬P)生成新知识

基本规则：
1. P∨Q, ¬P ⊨ Q
2. P∨Q, ¬P∨R ⊨ Q∨R

应用步骤：
1. 转换为合取范式(CNF)
2. 寻找互补文字
3. 生成新子句
4. 若得到空子句则证明成功

## 三、一阶逻辑(更强大的表达系统)

### 1. 基本元素
- **常量符号**：表示具体对象
- **谓词符号**：表示对象间的关系/属性

### 2. 量词系统
1. 全称量词(∀)：对所有x都成立
   例：∀x.Person(x)→Mortal(x)
   
2. 存在量词(∃)：存在某个x成立
   例：∃x.House(x)∧BelongsTo(Minerva,x)
   
3. 混合使用：
   ∀x.Person(x)→(∃y.House(y)∧BelongsTo(x,y))
   含义：每个人都属于某个房子
```

## Knowledge

本节探讨如何在人工智能中表现知识并对现有知识进行推理得出结论。

### Knowledge-Based Agents

### Sentence

句子是 AI 存储知识并用它来推断新信息的方式，是一种用知识表示语言对世界的断言。

## Propositional Logic

命题逻辑基于命题，即关于世界的陈述，可以是真或者假。

### Propositional Symbols

命题符号，一般使用 `(P、Q、R)`。

### Logical Connectives

逻辑连接词，用于连接命题符号的逻辑符号。

- **Not (¬)** ：用于反转命题的真值。
- **And (∧)**：连接两个不同的命题，仅当 P 和 Q 都为真时，命题 P∧Q 才为真，表示且。
- **Or (∨)**：连接两个不同的命题，只要其中一个参数为真就为真，表示或。

> 有两种类型的或，包含或（Inclusive Or）和排他或（Exclusive Or）。排他或也就是异或（XOR，用符号 ⊕ 表示），两者都为真，结果为假。

- **Implication(→)**：如果 P 则 Q，P 被称为前件（Antecedent），Q 被称为后件（consequent）。
    - 如果 P 为真，Q 为真，则结果为真；Q 为假，则结果为假。
    - 如果 P 为假，无论 Q 的真值如何，结果都为真（trivially true）。
- **Biconditional（↔）**：相当于当且仅当，P↔Q = P→Q∧Q→P。即当 P 和 Q 同时为真或者同时为假时，结果为真；P 和 Q 不同时，结果为假。

### Model

模型是为每个命题分配一个真值，即 {P = True， Q = False}。如果有 n 个命题，那么就会有 $n^2$ 个可能的模型。

### Knowledge Base

知识库是知识型智能体(agent)所掌握的一组句子集合。这是以命题逻辑句子形式提供给人工智能系统的关于世界的知识。这些知识可以用来对世界做出额外的推理。

### Entailment（⊨）

如果 α ⊨ β （α 蕴含 β），那么在任何 α 为真的世界中，β 也为真。

> **Implication**：是两个命题之间的逻辑连接词。
>
> **Entailment**：是一种关系，表示如果 α 中信息为真，β 中所有信息都是真的。

## Inference

推理是从旧句子中推导出新句子的过程。首先，考虑模型检查（Model Checking）算法：

1. 确定 KB ⊨ α 是否成立（即我们能否通过知识库 KB 得出 α 为真的结论）
2. 枚举所有可能的模型。
3. 如果在每个 KB 为真的模型中，α 都为真，则结论成立。

例如：P：今天是星期二；Q：下雨；R：Herry 要去跑步；KB：(P ∧ ¬Q) → R。现在我们想知道 KB ⊨ R，即 R 到底是不是真的。

```python
from logic import *

# 创建表示命题的符号
P = Symbol("P")  # 今天是星期二
Q = Symbol("Q")  # 下雨
R = Symbol("R")  # Harry 要去跑步

# 构建知识库 KB: (P ∧ ¬Q) → R
knowledge = Implication(And(P, Not(Q)), R)

def check_all(knowledge, query, symbols, model):
    # 如果 model 已经为每个符号都分配了真值
    if not symbols:
        # 如果知识库在此模型下为真, 那么查询也必须为真
        if knowledge.evaluate(model):
            return query.evaluate(model)
        return True
    else:
        # 选择一个剩余的未使用符号
        remaining = symbols.copy()
        p = remaining.pop()
        # 创建一个符号为真的模型
        model_true = model.copy()
        model_true[p] = True
        # 创建一个符号为假的模型
        model_false = model.copy()
        model_false[p] = False
        # 确保在两个模型中都成立
        return (check_all(knowledge, query, remaining, model_true) and 
                check_all(knowledge, query, remaining, model_false))

# 检查 KB ⊨ R
symbols = [P, Q, R]
query = R
result = check_all(knowledge, query, symbols, {})

print(f"KB ⊨ R 是 {result}")
```

check_all 递归为每一个 Symbols 分配真值并将其添加到 Model 中，所有的 Symbols 都分配完真值之后，如果 KB 为真，R 也为真就输出真；R 为假，说明不成立，输出假，即表示不能得到这样的结论。如果 KB 为假，不是我们要考虑的，直接返回 True，不影响最后的结果。

## Knowledge Engineering

知识工程是弄清楚如何在人工智能中表示命题和逻辑的过程。

## Inference Rules

模型检查算法效率较低，而推理规则让我们能够根据现有知识生成新信息。

- **假言推理（Modus Ponens）**: 如果 $$\alpha \rightarrow \beta$$ 且 $$\alpha$$，则 $$\beta$$。

- **合取消去（And Elimination）**: 如果 $$\alpha \land \beta$$，则 $$\alpha$$。

- **双重否定消去（Double Negation Elimination）**: 如果 $$\neg(\neg \alpha)$$，则 $$\alpha$$。

- **蕴涵消去（Implication Elimination）**: 如果 $$\alpha \rightarrow \beta$$，则 $$\neg \alpha \lor \beta$$。

- **双条件消去（Biconditional Elimination）**: 如果 $$\alpha \leftrightarrow \beta$$，则 $$\alpha \rightarrow \beta \land \beta \rightarrow \alpha$$。

- **德摩根定律（De Morgan’s Law）**: $$\neg (\alpha \land \beta) \equiv \neg \alpha \lor \neg \beta$$；$$\neg (\alpha \lor \beta) \equiv \neg \alpha \land \neg \beta$$

- **分配律（Distributive Property）**: $$\alpha \land (\beta \lor \gamma) \equiv (\alpha \land \beta) \lor (\alpha \land \gamma)$$；$$\alpha \lor (\beta \land \gamma) \equiv (\alpha \lor \beta) \land (\alpha \lor \gamma)$$

### 知识和搜索问题

推理被视为具有以下属性的搜索问题：

- 初始状态（Initial State）：启动知识库；
- 动作（Action）：推理规则；
- 转换模型（Transition Model）：推理后的新知识库；
- 目标测试（Goal Test）：检查要证明的语句是否在知识库中；
- 路径成本函数（Path Cost Function）：证明中的步骤数。

## Resolution

归结（Resolution）是一个强大的推理规则，它基于补充文字，即一个命题符号和它的否定形式，例如 P 和 ¬P。归结规则允许我们通过推理生成新句子，从而获得新的知识。

> 如果我们知道 $P \lor Q$ 并且还知道 $\neg P$，那么就能推理出 $Q$。

归结可以进一步推广：

> 如果我们知道 $P \lor Q$ 并且还知道 $\neg P \lor R$，那么就能推理出 $Q \lor R$。

### 从句和合取范式（CNF）

- **从句（Clause）**：是文字的析取（例如 $$P \lor Q \lor R$$）。
- **合取范式（CNF）**：是从句的合取，例如 $$(A \lor B \lor C) \land (D \lor \neg E) \land (F \lor G)$$。

### 转换为合取范式的步骤

1. **消去双条件**：将 $$(\alpha \leftrightarrow \beta)$$ 转换为 $$(\alpha \rightarrow \beta) \land (\beta \rightarrow \alpha)$$。
2. **消去蕴涵**：将 $$(\alpha \rightarrow \beta)$$ 转换为 $$(\neg \alpha \lor \beta)$$。
3. **移动否定**：使用德摩根定律，将否定移到文字上。$$\neg (\alpha \land \beta) \equiv \neg \alpha \lor \neg \beta$$
4. **分配律**：应用分配律以达到合取范式。

**例子**：将 $$(P \lor Q) \rightarrow R$$ 转换为 CNF。

- 消去蕴涵：$$\neg (P \lor Q) \lor R$$
- 德摩根定律：$$(\neg P \land \neg Q) \lor R$$
- 分配律：$$(\neg P \lor R) \land (\neg Q \lor R)$$

### 推理算法

推理算法通过分解生成新子句，直到生成空子句（即矛盾），从而证明知识库的蕴涵关系。

**证明过程**：

1. 将 $$(KB \land \neg \alpha)$$ 转换为 CNF。
2. 检查是否可以通过分解生成新子句。
3. 如果生成空子句，则证明 $$(KB \models \alpha)$$。
4. 如果无法生成矛盾，则无蕴涵。

**例子**：验证 $$(A \lor B) \land (\neg B \lor C) \land (\neg C)$$ 是否蕴涵 $$A$$。

- 假设 $$A$$ 为假，得到 $$(A \lor B) \land (\neg B \lor C) \land (\neg C) \land (\neg A)$$。
- 由于 $$\neg C$$，可知 $$B$$ 为假，添加 $$(\neg B)$$。
- 由于 $$\neg B$$，可知 $$A$$ 为真，添加 $$(A)$$。
- 现在有互补文字 $$(A)$$ 和 $$(\neg A)$$，生成空子句，证明矛盾。

通过以上步骤，我们可以利用分解和合取范式的转换来进行有效的逻辑推理和证明。

## First Order Logic

一阶逻辑使用两种符号：常量符号和谓词符号，可以表达更复杂的思想。

> - **常量符号**：表示对象。例如 Minerva 等。
> - **谓词符号**：类似于关系或函数，接受一个或多个参数并返回真或假。例如，谓词 Person(Minerva) 表示 Minerva 是一个人。

### 通用量化（Universal Quantification）

通用量化使用符号 ∀ 来表示“对于所有”。例如，表达式 $$\forall x. \text{BelongsTo}(x, \text{Gryffindor}) \rightarrow \neg \text{BelongsTo}(x, \text{Hufflepuff})$$ 表示对于每一个符号 x，如果 x 属于 Gryffindor，则 x 不属于 Hufflepuff。

### 存在量化（Existential Quantification）

存在量化与通用量化相对，表示“至少存在一个”。使用符号 ∃ 表示。例如，表达式 $$\exists x. \text{House}(x) \land \text{BelongsTo}(\text{Minerva}, x)$$ 表示至少存在一个符号 x，它既是一个房子且 Minerva 属于它。这表达了 Minerva 属于某个房子的思想。

### 混合量化

存在量化和通用量化可以在同一个句子中使用。例如，表达式 $$\forall x. \text{Person}(x) \rightarrow (\exists y. \text{House}(y) \land \text{BelongsTo}(x, y))$$ 表示如果 x 是一个人，那么至少存在一个房子 y，使得这个人属于该房子。换句话说，每个人都属于一个房子。
