---
title: CMU15445-Project3-Query-Execution
categories:
  - CMU15445
tags:
  - CMU15445
abbrlink: d38b2590
---

### 概述

下面是 Bustub 架构的概述：

![img](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/project-structure.svg)

我们可以使用 `EXPLAIN` 来打印查询执行计划的命令：

```
bustub> EXPLAIN SELECT * FROM __mock_table_1;
=== BINDER ===
BoundSelect {
  table=BoundBaseTableRef { table=__mock_table_1, oid=0 },
  columns=[__mock_table_1.colA, __mock_table_1.colB],
  groupBy=[],
  having=,
  where=,
  limit=,
  offset=,
  order_by=[],
  is_distinct=false,
}
=== PLANNER ===
Projection { exprs=[#0.0, #0.1] } | (__mock_table_1.colA:INTEGER, __mock_table_1.colB:INTEGER)
MockScan { table=__mock_table_1 } | (__mock_table_1.colA:INTEGER, __mock_table_1.colB:INTEGER)
=== OPTIMIZER ===
MockScan { table=__mock_table_1 } | (__mock_table_1.colA:INTEGER, __mock_table_1.colB:INTEGER)
```

以上结果概述了查询处理层内的转换过程，该语句首先进入解析器和绑定器，从而生成抽象语法树 AST，Bustub 到此理解了查询语句想要做什么。

接下来，AST 进入 `planner`，`planner` 将生成与查询对应的查询计划。查询计划包含两个节点的树，数据从树的叶子流向根部。

![img](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/mock_scan.svg)

之后，`optimizer` 优化器会优化查询计划。在这个例子中，它会移除 `projection plan node` 投影计划结点，因为这是冗余的。

我们看一个更复杂的例子：

```
bustub> EXPLAIN (o) SELECT colA, MAX(colB) FROM
  (SELECT * FROM __mock_table_1, __mock_table_3 WHERE colA = colE) GROUP BY colA;
=== OPTIMIZER ===
Agg { types=[max], aggregates=[#0.1], group_by=[#0.0] }
  NestedLoopJoin { type=Inner, predicate=(#0.0=#1.0) }
    MockScan { table=__mock_table_1 }
    MockScan { table=__mock_table_3 }
```

在 Bustub 中，优化器的输出总是一棵树，对于这个查询，树的结构如下：

![img](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/more_complex_example.svg)

我们可以看到这个命令的查询计划是 `scan` 两个表后执行 `Join` 操作，最后将结果执行 `Aggregation` 聚合操作。

`Executor` 在拿到 `Optimizer` 生成的具体查询计划之后，就可以生成真正执行查询计划的一系列算子了。在火山模型中，每个算子都有 `Init()` 和 `Next()` 两个方法。`Init()` 对算子进行初始化工作，`Next()` 则是向下层算子请求下一条数据。当 `Next()` 返回 `false` 时，则代表下层算子已经没有剩余数据，迭代结束。

Bustub 中 `table` 的结构如下：

![img](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/15-445-3-4-20230316120354580.png)

首先，Bustub 有一个 `Catalog`。`Catalog` 提供了一系列 API，例如  `CreateTable()`、`GetTable()` 等等。

`table heap` 是管理 `table` 数据的结构，包含 `InsertTuple()`、`MarkDelete()` 一系列 `table` 相关操作。`table heap` 本身并不直接存储 `tuple` 数据，`tuple` 数据都存放在 `table page` 中。

`table page` 是实际存储 `table` 数据的结构，父类是 `page`。相较于 `page`，`table page` 多了一些新的方法。`table page` 在 `data` 的开头存放了 `next page id`、`prev page id` 等信息，将多个 `table page` 连成一个双向链表，便于整张 `table` 的遍历操作。

`tuple` 对应数据表中的一行数据。每个 `tuple` 都由 `RID` 唯一标识。

`executor` 本身并不保存查询计划的信息，应该通过 `executor` 的成员 `plan` 来得知该如何进行本次计算，例如 `SeqScanExecutor` 需要向 `SeqScanPlanNode` 询问自己该扫描哪张表。

>   对于这个项目，您将需要在 BusTub 中实现额外的 `operator executors` 操作执行器。我们将使用 [iterator](https://15445.courses.cs.cmu.edu/fall2022/slides/12-queryexecution1.pdf) query processing model 迭代器查询处理模型(即 Volcano 模型)。在这个模型中，每个查询计划执行器都实现一个 `Next` 函数。当 DBMS 调用执行器的 `Next` 函数时，执行器返回一个 `tuple` 元组或一个 `indicator` 指示器，表示没有更多的元组。使用这种方法，每个执行器实现一个循环，该循环继续在其子级上调用 `Next`，以检索元组并逐个处理它们。
>
>   简而言之，在这个实验中，我们将实现火山模型的一些算子。

### Access Method Executors

**SeqScan**

`SeqScanPlanNode` 在 `SELECT * from table` 语句中使用。

`SeqScanExecutor` 遍历一张表，并返回表上的 `tuples`，一次一个。

-   在使用 `TableIterator` 时需要注意 `++iter` 和 `iter++` 的区别。
-   顺序扫描的输出是每个匹配 `tuple` 和原始记录标识符 `RID` 的副本。

```cpp
// 调用 AbstractExecutor(exec_ctx) 来通过 exec_ctx 构造 exec_ctx_
// ExecutorContext 是执行上下文，包含了代码运行时的一些东西，比如 Catalog
SeqScanExecutor::SeqScanExecutor(ExecutorContext *exec_ctx, const SeqScanPlanNode *plan) 
    : AbstractExecutor(exec_ctx), plan_(plan) {}

void SeqScanExecutor::Init() { 
    auto table_info = exec_ctx_->GetCatalog()->GetTable(plan_->GetTableOid());
    table_heap_ = table_info->table_.get();
    // 迭代器，这里我们不使用普通指针的原因是 TableIterator 没有默认构造方法
    iterator_ = std::make_unique<TableIterator>(table_heap_->Begin(exec_ctx_->GetTransaction()));
}

auto SeqScanExecutor::Next(Tuple *tuple, RID *rid) -> bool { 
    if (*iterator_ != table_heap_->End()) {
        // *iterator 是 TableIterator 类型，**iterator 是 tuple 类型
        *tuple = *((*iterator_)++);
        *rid = tuple->GetRid();
        return true;
    }
    return false;
 }
```

**Insert**

`InsertPlanNode` 在 `INSERT` 语句中使用。

`InsertExecator` 将元组插入表中并更新索引。它只有一个子级生成要插入到表中的值。`planner` 将确保值具有与表相同的模式。执行器将生成一个整数数字的 `tuple` 作为输出，指示在插入所有行之后，有多少行已经插入到表中。如果表中有索引关联，请记住在插入表时更新索引。

-   在执行器初始化期间，需要查找插入目标的表信息。有关访问目录的更多信息，请参见 `System Catalog` 部分。
-   您需要更新将元组插入表的所有索引。有关详细信息，请参阅下面的 `Index Updates` 部分。
-   您将需要使用 `TableHeap` 类来执行表修改。

```cpp
auto InsertExecutor::Next([[maybe_unused]] Tuple *tuple, RID *rid) -> bool { 
    if (successful_) {
        return false;
    }
    int count = 0;
    while (child_executor_->Next(tuple, rid)) {
        // 向 table_heap_ 中插入，然后需要向 index 中插入
        //  indexs 中插入的 tuple 和原本的 tuple 不同，需要调用 KeyFromTuple 构造
        if (table_heap_->InsertTuple(*tuple, rid, exec_ctx_->GetTransaction())) {
            auto indexs = exec_ctx_->GetCatalog()->GetTableIndexes(table_name_);
            for (auto index : indexs) {
                auto key = (*tuple).KeyFromTuple(table_info_->schema_, index->key_schema_, index->index_->GetKeyAttrs());
                index->index_->InsertEntry(key, *rid, exec_ctx_->GetTransaction());
            }
        }
        count++;
    }
    // 返回值 tuple 需要 std::vector<Value> 和 Schema 来构造
    // Value 是数据，需要 typeID 和数据来构造，这里分别是 INTEGER （整数）和删除的行数 count
    // Schema 是表的结构，通过 std::vector<Column> 构造
    // Column 是每一行的属性，通过属性名（随便命名）和 typeID 来构造
    std::vector<Value> value;
    value.emplace_back(INTEGER, count);
    std::vector<Column> column;
    column.emplace_back("DeleteCount", INTEGER);
    Schema schema(column);
    // Schema schema(plan_->OutputSchema());
    *tuple = Tuple(value, &schema);
    successful_ = true;
    return true;
 }
```

**Delete**

`DeletePlanNode` 在 `DELETE` 语句时使用。它只有一个 `child`，该 `child` 包含要从表中删除的记录。删除执行器应该生成一个整数输出，表示从表中删除的行数。它还需要更新索引。

您可以假定 `DeleteExecator` 始终位于查询计划的根目录。`DeleteExecator` 不应修改其结果集。

-   您只需要从 `child exector` 中获取 `RID` 并调用 `TableHeap::MarkDelete()` 来有效地删除元组。所有删除将在事务提交时应用。
-   您需要更新删除元组的表的所有索引。有关详细信息，请参阅下面的 `Index Updates` 部分。

实现细节和 `Insert` 基本相同。

**IndexScan**

`IndexScanExecator` 在索引上迭代以检索元组的 `RID`。然后，`operator` 使用这些 `RID` 在相应的表中检索它们的元组。然后它一次一个地返回这些元组。可以通过 `SELECT FROM < table > ORDER BY < index column >` 测试索引扫描执行器。

`plan` 中的索引对象的类型始终是此项目中的 `BPlusTreeIndexForOneIntegerColumn`。您可以安全地将其强制转换并将其存储在 `Execator` 对象中:

```
tree_ = dynamic_cast<BPlusTreeIndexForOneIntegerColumn *>(index_info_->index_.get())
```

然后，您可以从索引对象构造索引迭代器，扫描所有键和元组 `RID`，从表堆中查找元组，并按索引键的顺序提交所有元组作为执行器的输出。BusTub 只支持具有单个、唯一整数列的索引。在测试用例中不会有重复的键。

和 `SeqScan` 的实现基本相同，在索引中拿到 `rid`，然后调用 `TableHeap::GetTuple()` 通过 `rid` 拿到 `tuple`。索引迭代器的自增需要调用 `iterator_->operator++()` 。

#### System Catalog

数据库维护一个内部目录 `catalog` 以跟踪数据库的元数据。在此项目中，您将与系统目录交互以查询有关表、索引及其架构的信息。

目录实现的全部内容在 `src/include/alog/catalog.h` 中。应该特别注意成员函数 `Catalog::GetTable() ` 和 `Catalog::GetIndex()`。您将在执行器的实现中使用这些函数来查询表和索引的目录。

#### Index Updates

对于表修改执行器( `InsertExecator` 和 `DeleteExecator`) ，必须修改操作所针对的表的所有索引。您可能会发现 `Catalog::GetTableIndexs() ` 函数对于查询特定表定义的所有索引非常有用。

### Aggregation & Join Executors

**Aggregation**

`AggregationPlanNode` 被用来为下面这样的查询提供支持：

```sql
SELECT colA, MIN(colB) FROM __mock_table_1 GROUP BY colA;
SELECT DISTINCT colA, colB FROM __mock_table_1;
```

实现聚合的一个常见策略是使用哈希表。我们做了一个简化的假设，即聚合哈希表完全适合于内存，这意味着我们不需要为散列聚合实现两阶段 (Partition，Rehash) 策略。我们还可以假设所有聚合结果都可以驻留在内存中的哈希表中(即哈希表不需要由缓冲池页面支持)。

聚合的 `Schema` 是 `group-by` 列，然后跟聚合列（如 `min(x)` 列、`count(*)` 列等）。

`SimpleAgregationHashTable` 数据结构，它有一个内存哈希表(`std::unordered_map`) 和一个为计算聚合而设计的接口，还有一个可用于迭代哈希表的 `SimpleAggreationHashTable::Iterator` 类型。你需要实现 `CombinAgregateValues` 函数。其中 `AggregateValue` 是一个 `Value` 数组，即 `input.aggregates_[i]` 是 `Value` 类型。需要注意的是 `count(column)` 和 `count(*)` 的区别，以及对空值的处理。

```cpp
case AggregationType::SumAggregate:
  // input 非空且 result 是空		
  if (!input.aggregates_[i].IsNull() && result->aggregates_[i].IsNull()) {
    result->aggregates_[i] = Value(INTEGER, 0);
  }
  // input 非空且 result 是整型
  if (!input.aggregates_[i].IsNull() && result->aggregates_[i].CheckInteger()) {
    result->aggregates_[i] = result->aggregates_[i].Add(input.aggregates_[i]);
  }
  break;
```

`Aggregation` 是 `pipeline breaker`，也就是说它会打破 `iteration model` 的规则，在 `Init()` 函数中将所有结果全部计算出来。

```cpp
while (child_->Next(&tuple, &rid)) {
  auto aggregate_key = MakeAggregateKey(&tuple);
  auto aggregate_value = MakeAggregateValue(&tuple);
  aht_.InsertCombine(aggregate_key, aggregate_value);
}
aht_iterator_ = aht_.Begin();  // 插入后需要重新指定 aht_iterator_
```

再在 `Next()` 函数中一条一条的返回：

```cpp
Schema schema(plan_->OutputSchema());
if (aht_iterator_ != aht_.End()) {
  std::vector<Value> value(aht_iterator_.Key().group_bys_);
  for (const auto &aggregate : aht_iterator_.Val().aggregates_) {
    value.push_back(aggregate);
  }
  *tuple = {value, &schema};
  ++aht_iterator_;
  return true;
}
// 应对某些没有 group_bys_ 的情况
if (plan_->group_bys_.empty()) {
  std::vector<Value> value;
  for (auto aggregate : plan_->agg_types_) {
    switch (aggregate) {
      case AggregationType::CountStarAggregate:
        value.push_back(ValueFactory::GetIntegerValue(0));
        break;
      case AggregationType::CountAggregate:
      case AggregationType::SumAggregate:
      case AggregationType::MinAggregate:
      case AggregationType::MaxAggregate:
        value.push_back(ValueFactory::GetNullValueByType(TypeId::INTEGER));
        break;
    }
  }
  *tuple = {value, &schema};
  return true;
}
```

**NestedLoopJoin**

`Join` 这里我们实现两种，分别是 `inner join` 和 `leaf join`。

对于 `inner join` 需要满足 `left` 表的 `tuple` 和 `right` 表的 `tuple` 匹配。这里我们通过 `next` 函数调用 `left` 表，对于 `left` 表的每个 `tuple`，都需要和 `right` 表的所有 `tuple` 尝试是否匹配。所以，我们需要将 `right` 表中的 `tuple` 存储到一个 `vector` 中，以供多次循环。

调用 `next` 函数时，如果 `right tuples` 的 `index` 不为 0，那么在上次调用时 `right tuples` 还未遍历完，所以需要遍历剩下的 `right tuples` 来和上次的 `leaf tuple` 测试是否匹配。这里，`leaf tuple` 是上次调用 `left executor` 的 `next` 函数得到的。如果 `index = 0`，说明 `right tuples` 已经遍历完了，调用 `left executor->next()` 函数，开始一轮新的匹配。难点在于这次匹配需要记录上次匹配的状态，接着上次的来。也可以暴力点，将两个表的 `tuple` 全都存起来。然后两次循环，记录循环变量 i 和 j。

对于 `left join` 需要满足 `left` 表的 `tuple` 和 `right` 表的 `tuple` 匹配，如果 `right` 表中没有任何 `tuple` 和 `left` 表中的 `tuple` 匹配，需要生成一个 `null tuple` 来 `join`。所以，我们需要一个变量 `is_match_` 来和记录是否有过 `right tuple` 和 `left tuple` 匹配过。如果 `index` 已经为 0 了，表示 `right tuples` 中的所有 `tuple` 都和 `left tuple` 测试匹配过了，此时如果 `is_match_` 仍然为 `false`，说明没有匹配的，需要生成 `null tuple`。

对于这种需要记录上次调用的状态，其他语言有 `yield` 等语法，十分方便。

**NestedIndexJoin**

在发现 `right` 表上有索引时，不使用循环，而是通过索引查找。我们知道， bustub 中的索引不支持重复值，所以通过索引最多查找到一个匹配的 `tuple`，因此不需要记录上次的状态。因此，在调用 `next` 时，`left child` 调用 `next` 函数，同时在 `right index` 中搜索相匹配的 `tuple`，如果搜索到了，就返回。没有搜到，需要考虑是否为 `left join`，如果是，需要构造一个 `null tuple` 和 `left tuple` 来 `join`。

### Sort + Limit Executors and Top-N Optimization

**Sort**

同样，在 `Init()` 中需要读取 `child` 算子返回的所有 `tuple`，将其存储下来，按照 `order by` 的顺序排序。这里，我们调用 `std::sort()` 自定义排序即可。

```cpp
std::sort(sorted_tuples_.begin(), sorted_tuples_.end(), [this](const Tuple &a, const Tuple &b) {
    for (auto [order_by_type, expr] : plan_->GetOrderBy()) {
      bool default_order_by = (order_by_type == OrderByType::DEFAULT || order_by_type == OrderByType::ASC);
      if (expr->Evaluate(&a, child_executor_->GetOutputSchema())
              .CompareLessThan(expr->Evaluate(&b, child_executor_->GetOutputSchema())) == CmpBool::CmpTrue) {
        return default_order_by;
      }
      if (expr->Evaluate(&a, child_executor_->GetOutputSchema())
              .CompareGreaterThan(expr->Evaluate(&b, child_executor_->GetOutputSchema())) == CmpBool::CmpTrue) {
        return !default_order_by;
      // equal 的情况不返回， for 循环到下一个需要排序的值
      }
    }
    return true;
  });
```

**limit**

维护一个计数变量，记录调用 `Next()` 函数的次数，超过 `limit` 直接返回 `false`。

**topN**

估计本意是想让我们写一个优先队列。不过我直接使用 `sort + limit` 解决了。时间复杂度没有区别的其实。

**Sort + Limit As TopN**

难点在于学习其他优化的写法，并需要去阅读大量的代码，理解执行过程。

```cpp
auto Optimizer::OptimizeSortLimitAsTopN(const AbstractPlanNodeRef &plan) -> AbstractPlanNodeRef {
  std::vector<AbstractPlanNodeRef> children;
  // 递归的优化执行树
  for (const auto &child : plan->GetChildren()) {
    children.emplace_back(OptimizeSortLimitAsTopN(child));
  }
  auto optimized_plan = plan->CloneWithChildren(std::move(children));
  // 对于执行树当前节点是 Limit，且 child 节点是 Sort
  // 利用 child 节点构造一个 TopNPlanNode 并返回。当前节点自然就是不要了
  if (optimized_plan->GetType() == PlanType::Limit) {
    const auto &limit_plan = dynamic_cast<const LimitPlanNode &>(*optimized_plan);
    BUSTUB_ENSURE(limit_plan.children_.size() == 1, "SLAT should have exactly 1 children.");
    if (limit_plan.GetChildAt(0)->GetType() == PlanType::Sort) {
      const auto &child = dynamic_cast<const SortPlanNode &>(*limit_plan.GetChildAt(0));
      return std::make_shared<TopNPlanNode>(limit_plan.output_schema_, 
             child.GetChildPlan(), child.GetOrderBy(), limit_plan.GetLimit());
    }
  }
  return optimized_plan;
}
```

### 结果

![image-20230319235012711](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20230319235012711.png)
