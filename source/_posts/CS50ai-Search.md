---
title: CS50ai-Search
categories:
  - AI
tags:
  - CS50ai
abbrlink: 5d505f64
date: 2024-09-10 22:55:47
---

# Search

搜索问题，主要的算法有 DFS、BFS、GBFS（贪婪的 BFS）、A*、Minimax 和 Alpha-Beta 剪枝。这部分主要聚焦于寻找问题的解决方案，比如找出从起点到终点的最佳路线、玩游戏中下一步的最佳操作。

搜索问题通常设计一个主体（Agent），给定 Agent 的初始状态和目标状态，返回解决方案。有如下关键词：

-   Agent：一个能够感知其环境并对环境做出行动的实体。
-   State：一个 Agent 在其环境中的某种配置或状态。它描述了在特定时刻Agent与其环境的具体情况。
-   Action：在某一 State（状态）下可以做出的选择。
-   Transition Model：描述状态变化的模型，定义了在某个状态（state）下执行某个动作（action）后会得到什么新的状态。
-   State Space：状态空间，所有可到达状态的合集。
-   Goal Test：确定给定状态是否为目标状态。
-   Path Cost：路径成本。

## 解决Search问题

-   Solution：从初始状态到目标状态的一系列操作。
    -   Optimal Solution：最优解。

在Search过程中，数据通常存储在Node中，Node是包含以下数据的数据结构：

1.   当前的 State
2.   生成当前节点的 Parent Node
3.   从父节点到当前节点的 Action
4.   从初始节点到当前节点的 Path Cost

Node 只保存信息，而不进行搜索，实际搜索，我们需要使用 **frontier**，这是一种操作节点的机制，**frontier** 从包含初始状态和一个空的已探索项开始，重复以下操作：

1.   如果 **frontier** 是空的，
     -   Stop，问题没有解决办法。
2.   从 **frontier** 中删除一个 Node，即我们要考虑的节点。
3.   如果 Node 包含目标状态
     -   返回解决方案，Stop。
     -   拓展该 Node，即把该 Node 能到达的 Node 加入 **frontier**，并把该 Node 加入已探索 set。

## DFS

**frontier** 使用堆栈来存储 Node，这样每次删除时，删除的都是后进来的元素。

-   优点：如果幸运，那么该算法的速度很快。
-   缺点：找到的解决方案不是最佳的；最坏情况下，速度很慢。

## BFS

**frontier** 使用队列来存储 Node，这样每次删除时，删除的都是最新进来的元素。

-   优点：保证找到最优解。
-   缺点：运行时间肯定比最优方案长。

## GBFS

**frontier** 使用优先队列来存储 Node，使用启发式函数 h(n) 来确定最接近目标的节点，比如使用曼哈顿距离。

-   可能出错，找到的并不是最优解。

## A* Search

是 GBFS 的优化，不仅考虑启发式函数 h(n)，还考虑从起始状态到当前状态的成本 g(n)。通过这两个值相加，可以更准确的估计成本确定路线。为了能找到最优解，启发式函数需要：

1.   Admissible：可接受性。启发函数 h(n) 在任何情况下都不能高估从当前节点 n 到目标节点的实际最小代价。因此，A* 保证它在搜索过程中不会错过任何可能的最优路径。
2.   Consistent：一致性。一致性要求对于每一个节点 n 和它的相邻节点 $n{\prime}$，加上从 n 到 $n{\prime}$ 的实际代价 c 后，$n{\prime}$ 的启发估计 $h(n{\prime})$ 应该不会比 n 的启发估计 h(n) 更低，也就是：$h(n) \leq h(n{\prime}) + c$。这样可以保证不走回头路。

## Adversarial Search

在对抗性搜索中，算法面临着试图实现相反目标的对手，比如在井字游戏中的对手。

## Minimax

是一种用于决策和博弈论中的算法，尤其常用于两人零和博弈的人工智能中。它旨在模拟双方玩家的决策过程，以找到对抗最优策略。算法中最大化玩家(Maximizer)试图最大化收益，最小化玩家(Minimizer)试图最小化最大化玩家的收益。算法通过递归地模拟双方的最佳决策来选择最优的行动。

考虑井字棋人工智能：

-   $S_0$：初始状态
-   Player(s)：一个函数，给定状态*s* ，返回轮到哪个玩家。
-   Actions(s)：一个函数，给定一个状态*s* ，返回该状态下的所有合法动作。
-   Result(s, a)：一个函数，给定状态*s*和操作*a* ，返回一个新状态。
-   Terminal(s) ：一个函数，给定状态*s* ，检查这是否是游戏的最后一步。
-   Utility(s) ：给定最终状态*s*的函数，返回该状态的效用值：-1、0 或 1。

而 Minimax 算法的工作原理如下：

-   给定一个状态 s

    -   最大化玩家在 Actions(s) 中选择产生 Min-Value(Result(s, a)) 最大值的动作 a。
    -   最小化玩家在 Actions(s) 中选择产生 Max-Value(Result(s, a))最小值的动作 a。

-   函数 Max-Value(state)

    -   v = -∞

    -   如果 Terminal(state)，返回 Utility(state)。

    -   for action in Actions(state):

        v = max(v, Min-Value(Result(state, action)))

        return v

-   函数 Min-Value(state)

    -   v = ∞

    -   如果 Terminal(state)，返回 Utility(state)。

    -   for action in Actions(state):

        v = min(v, Max-Value(Result(state, action)))

        return v

## Alpha-Beta 剪枝

是一种优化 Minimax 的方法，它会跳过一些明显不利的递归计算。在确定一个 Action 的价值后，如果有初步证据表明接下来的行动可以使对手获得比已经建立的行动更好的分数，则可直接跳过。

## Depth-Limited Minimax

深度限制 Minimax 算法，如果状态空间太庞大，可以在停止之前仅考虑预定义的移动次数，而不到达最终状态。该优化方案依赖于**评估函数**。

## Project 0 - Degrees

注意给出的参考代码，Node 中的 action 就表示 movie，通过一部电影，parent 和当前 node 产生了联系。由于要找到最短路径，因此需要使用 BFS 来处理。

```python
class Node():
    def __init__(self, state, parent, action):
        self.state = state
        self.parent = parent
        self.action = action


class StackFrontier():
    def __init__(self):
        self.frontier = []
    def add(self, node):
        self.frontier.append(node)
    def contains_state(self, state):
        return any(node.state == state for node in self.frontier)
    def empty(self):
        return len(self.frontier) == 0
    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        else:
            node = self.frontier[-1]
            self.frontier = self.frontier[:-1]
            return node

class QueueFrontier(StackFrontier):
    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        else:
            node = self.frontier[0]
            self.frontier = self.frontier[1:]
            return node
```

具体算法如下：

```python
def shortest_path(source, target):
    frontier = QueueFrontier()
    # 初始状态
    frontier.add(Node(source, None, None))
    explored = set()
    while not frontier.empty():
        node = frontier.remove()
        # 出队时处理输出，也可以在入队时处理，效率好一些
        if node.state == target:
            path = []
            while node.parent is not None:
                path.append((node.action, node.state))
                node = node.parent
            return path[::-1]
        explored.add(node.state)
        for action, state in neighbors_for_person(node.state):
            if state not in explored and not frontier.contains_state(state):
                frontier.add(Node(state, node, action))
    return None
```

总之，这里是 AI 的搜索问题，而不是单纯的 BFS 算法，我们需要使用模板来解决复杂的问题。

## Project 0 - TicTacToe

```python
def minimax(board):
    def max_value(board):
        if terminal(board):
            return utility(board), None
        v = -math.inf
        action = None
        for a in actions(board):
            new_v, _ = min_value(result(board, a))
            if new_v > v:
                v = new_v
                action = a
        return v, action # 得分和对应动作
    def min_value(board):
        if terminal(board):
            return utility(board), None
        v = math.inf
        action = None
        for a in actions(board):
            new_v, _ = max_value(result(board, a))
            if new_v < v:
                v = new_v
                action = a
        return v, action
    if terminal(board):
        return None
    if player(board) == X:
        return max_value(board)[1]
    else:
        return min_value(board)[1]
```


