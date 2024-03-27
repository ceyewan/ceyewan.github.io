---
title: CMU15445-Project4-Concurrency-Control
categories:
  - CMU15445
tags:
  - CMU15445
abbrlink: '997e1890'
---

### Background

两阶段锁

>   GROWING：锁的增长阶段，即加锁阶段。
>
>   SHRINKING：锁的释放阶段，即解锁阶段。

五种锁类型

>   S 锁：共享锁。
>
>   IS 锁：意向共享锁，读取行时需要对表加 IS 锁。
>
>   X 锁：排他锁。
>
>   IX 锁：意向排他锁，写行时需要对表加 IX 锁。
>
>   SIX 锁：共享意向排他锁，读取全表，并且会对部分行加写锁。

隔离级别：

>   REPEATABLE_READ：可重复读，事务从开始到结束，读到的东西自始至终都是一样。
>
>   READ_COMMITTED：读提交，事务可以读到其他事务已经提交了的数据。
>
>   READ_UNCOMMITTED：读未提交，事务可以读到其他事务还没有提交的数据。

### Lock Manager

**LockTable**

1.   检查 `txn` 状态

     可重复读,在 `SHRINKING` 状态不允许使用锁,`GROWING` 状态可以加任何锁。

     读提交,在 `SHRINKING` 状态只能加 `S/IS` 锁,`GROWING` 状态可以加任何锁。

     读未提交,不允许 `S/IS/SIX` 锁,`SHRINKING` 状态不允许加锁。

2.   获取 `table` 对应的 `lock request queue`

     `table_lock_map_` 维护了一个 `table` 到 `lock request queue` 的映射关系。在获取时需要对 `map` 加锁，获取后立即释放该锁。不存在映射关系则创建。

3.   判断是否为锁升级

     对 `lock request queue` 加锁后，遍历在 `queue` 上的所有事务，找到 `txn_id` 相等的。判断是否为锁升级。如果有其他事务在升级，直接 `ABORTED`；如果事务锁模式不变，直接返回 `true`；升级只能从 `IS -> S/X/IX/SIX、S-> X/SIX、IX->X/SIX、SIX -> X`，其他升级全部 `ABORTED`。

     是锁升级的话，在 `request queue` 和 `txn->Get[Shared/...]TableLockSet()` 中删除原有锁。

4.   接下来 `new` 一个 `request`，将其加入 `request queue`。

5.   接下来，就是经典的条件变量 + 互斥锁模型了

     首先拿到 `lock_request_queue` 的锁，然后等待为事务赋予在 `table` 上想要的锁，如果没有成功，那么就 `wait`。被唤醒后，发现被 `ABORTED` 了（可能是死锁检测把它给 `ban` 了），直接退出，取消拿锁。调用 `notify_all()` 通知所以正在等待该资源的线程。

     ```cpp
     std::unique_lock<std::mutex> lock(lock_request_queue->latch_);
     ...
     while (!lock_request_queue->GrantLockForTable(txn, lock_mode)) {
       lock_request_queue->cv_.wait(lock);
       if (txn->GetState() == TransactionState::ABORTED) {
         RemoveRequest();
         lock_request_queue->cv_.notify_all();
         return false;
       }
     }
     ```

6.   `GrantLockForTable()` 函数，为事务赋予锁。

     遍历 `request queue` 拿到 `granted_set`，和当前事务的 `lock_request`。判断所有 `greated` 的锁和当前的 `lock_request` 是否兼容。`IS` 和 `X` 不兼容，`IX` 和 `S/SIX/X` 不兼容，`S` 和 `IX/SIX/X` 不兼容，`SIX` 和 `IX/SIX/X/S` 不兼容，`X` 和所有都不兼容。

     然后判断优先级。如果是锁升级，优先级最高，那么赋予锁并将 `upgrading` 设为 `INVALID_TXN_ID`；因为锁是 `FIFO` 顺序满足，查看当前事务前所有正在等待的事务记为 `wait list`，如果和前面的 `wait` 都兼容，那么可以认为优先级也是最高的。（文档说了，所有兼容的锁需要一起被赋予）。

7.   文档中的 `Bookkeeping` 操作，就是在 `txn->Get[Shared/...]TableLockSet()` 中记录拿到的或者删除的锁。

**LockRow**

和上面几乎完全相同，行锁只支持 `S` 和 `X` 锁。在加 `S` 锁时，需要保证对表有锁（任意锁都行）；在加 `X` 锁时，需要保证对表有 `X/IX/SIX` 锁。

**UnLockTable**

1.   如果事务行读锁或者行写锁不为空的话，不能释放表锁
2.   拿到 `lock_request_queue`
3.   遍历找到表锁，然后删除即可。注意需要在 `lock_request_queue` 和 `txn->Get[Shared/...]TableLockSet()` 中删除。
4.   在可重复读隔离级别下， `S/X` 锁的释放会导致事务进入 `SHRINKING` 状态；在读提交和读未提交状态，`X` 锁的释放会导致事务进入 `SHRINKING` 状态。

### Deadlock Detection

1.   `LockManger` 后台维护一个死锁检测线程

     ```cpp
       LockManager() {
         enable_cycle_detection_ = true;
         cycle_detection_thread_ = new std::thread(&LockManager::RunCycleDetection, this);
       }
     ```

2.   `RunCycleDetection()` 中维护一个循环，循环条件是 `enable_cycle_detection_` 每次循环开始前先等待一会 `std::this_thread::sleep_for(cycle_detection_interval)`

3.   遍历 `table lock map` 得到在 `table` 锁上的 `wait` 关系。具体来说，`txn_i` 没有 `granted` 锁，而 `txn_j` 却 `granted` 了锁，且 `txn_i` 和 `txn_j` 不兼容，那么 `txn_i wait for txn_j`。将这组边调用 `AddEdge` 加入 `wait for` 图中。

4.   接着遍历 `row lock map` 执行同样的操作。

5.   `while(HasCycle(&txn_id))` 得到 `wait for` 图中环 `txn_id` 最大的那个 `txn_id`，遍历该事务上的 `Get[Shared][Row]LockSet`，释放所有的锁，或者简单粗暴的将事务的状态设为 `ABORTED`。因为可能有多个环，我们都要打破，所以使用 `while` 循环。

6.   `HasCycle` 实际上调用的 `DFS` 来检测环的存在。记录已经访问过的节点，如果有搜到已经访问过的节点，说明成环了。

7.   调用 `RemoveEdge` 移除 `wait for` 图上和 `txn_id` 有关的所有边。

8.   `notify_all` 正在等待这个事务持有资源的其他事务。

### Concurrent Query Execution

在 `SeqScan、Insert、Delete` 三个算子中添加并发控制，因为只有这三个算子是直接操控数据的。

分别按照隔离级别，对表加 `IS/IX` 锁，并且还需要对行加 `S/X` 锁。

### 结果

有两个测试没过，留到后续有时间再补上吧。

![image-20230320155042928](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20230320155042928.png)