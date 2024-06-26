---
title: Introduction-to-Parallel-Computing
categories:
  - HPC
tags:
  - HPC
abbrlink: 5042922f
date: 2024-06-13 17:05:46
---

## 并行计算概述

### 什么是并行计算

传统上，软件是为串行计算编写的。问题被分解为一系列离散的指令，指令按顺序依次在单个处理器上执行，任何时刻只能执行一条指令。

而并行计算是同时使用多个计算资源来解决一个计算问题。问题被分解为可以同时解决的离散部分，每个部分进一步细分为一系列指令，每个部分的指令在不同的处理器上同时执行，采用总体控制/协调机制。

其中，计算问题应该能够：

-   分解为可以同时解决的离散工作。
-   随时执行多条指令。
-   使用多个计算资源比使用单个计算资源可以用更短的时间解决问题。

计算资源通常是：

-   具有多个处理器/核心的一台计算机。
-   通过网络连接任意数量的此类计算机。

#### 并行计算机

从硬件角度来看，当今几乎所有独立计算机都是并行的：

-   多个功能单元（L1缓存、L2缓存、分支、预取、解码、浮点、GPU、整数等）
-   多个执行单元/核心。
-   多个硬件线程。
-   网络连接多个独立计算机（节点）以形成更大的并行计算机集群。

### 为什么使用并行计算

### 谁在使用并行计算

## 概念和术语

### 冯诺依曼计算机体系架构

Memory + 控制器 + ALU 运算器 + I/O = Computer。

### 弗林经典分类法

SISD 单核处理器、SIMD 图形处理器、MISD 基本没有、MIMD 多核处理器。

>   许多 MIMD 架构还包括 SIMD 执行子组件。

### 通用并行计算术语

1.   **CPU**：当代的CPU由一个或多个内核组成——每个内核都有自己的指令流。一个CPU内的内核可能被组织到一个或多个插槽中——每个插槽都有各自独立的内存。当一个CPU由两个或多个插槽组成时，通常硬件基础设施支持跨插槽的内存共享。

2.   **Node：**独立的“盒子里的电脑”。通常由多个 CPU/处理器/核心、内存、网络接口等组成。节点通过网络连接在一起组成超级计算机。

3.   **Task：**任务通常是处理器执行的程序或类似程序的指令集。并行程序由在多个处理器上运行的多个任务组成。

4.   **Pipelining：**流水线。

5.   **SMP：**对称多处理器，共享内存硬件架构，其中多个处理器共享单个地址空间并可以平等地访问所有资源。

6.   **Distributed Memory：**在硬件中，指的是对不常见的物理内存的基于网络的内存访问。作为一种编程模型，任务只能在逻辑上“查看”本地机器内存，并且必须使用通信来访问正在执行其他任务的其他机器上的内存。

7.   **Communications：**通过共享内存总线或通过网络实现并行任务之间交换数据。

8.   **Synchronization**：同步通常涉及至少一个任务的等待，来协调并行任务，通常与通信相关。

9.   **Computational Granularity**：计算粒度，粗粒度指的是通信事件之间完成相对大量的计算工作。

10.   **Speedup：**加速比，串行程序执行时间/并行程序执行时间。

11.   **Parallel Overhead：**并行开销，包括任务启动时间、同步、数据通信、并行语言库或操作系统等造成的软件开销、任务终止时间。

12.   **Massively Parallel**：大规模并行。

13.   **Embarrassingly (IDEALY) Parallel**：最理想的并行。同时解决许多相似但独立的任务；任务之间几乎不需要协调。

14.   **Scalability：**可扩展性。指并行系统通过添加更多资源来证明并行加速按比例增加的能力。

### 并行编程潜在好处、限制和成本

#### Amdahl's Law 阿姆达尔定律

潜在的程序加速由可并行化的代码比例 (P) 定义：$Speedup = \frac{1}{1 - p}$。

-   如果没有代码可以被并行化，则 P = 0 且加速比 = 1，表示无加速。
-   如果所有代码都是并行化的，则 P = 1 并且加速比是无限的（理论上）。

引入执行并行工作部分的处理器数量，可以通过以下方式对关系进行建模：
$$
Speedup = \frac{1}{\frac{P}{N} + S}
$$
其中 P 为并行部分，N 是处理器数量，S 为串行部分。

可以知道，当 P 占 75%，S 占 25% 时，无论 N 多大，加速比都不会超过理想中的最大值 4。

#### 复杂度

一般来说，并行应用程序比相应的串行应用程序更复杂。不仅有多个指令流同时执行，而且它们之间还有数据流动。

#### 可移植性

-   由于 MPI、OpenMP 和 POSIX 线程等多个 API 的标准化，并行程序的可移植性问题并不像过去几年那么严重。
-   与串行程序相关的所有常见的可移植性问题都适用于并行程序。
-   尽管多个 API 存在标准，但实现在许多细节上会有所不同，有时甚至需要修改代码才能实现可移植性。
-   操作系统可以在代码可移植性问题中发挥关键作用
-   硬件架构具有高度可变性，并且会影响可移植性。

#### 资源要求

-   并行编程的主要目的是减少执行时间，但是为了实现这一点，需要更多的 CPU 时间。例如，在 8 个处理器上运行 1 小时的并行代码实际上使用了 8 小时的 CPU 时间。

-   需要复制数据以及与并行支持库和子系统相关的开销，并行代码所需的内存量可能比串行代码更大。
-   对于短时间运行的并行程序，与类似的串行实现相比，性能实际上可能会下降。

#### 可扩展性

**强可扩展性**（Strong scaling (Amdahl)）

-   随着更多处理器的添加，总问题大小保持不变。
-   目标是更快地运行相同大小的问题。
-   理想情况下意味着问题在 1/P 时间内得到解决（与串行相比）。

**弱可拓展性**（Weak scaling (Gustafson)）

-   随着更多处理器的添加，每个处理器的问题大小保持不变。总问题大小与所使用的处理器数量成正比。
-   目标是在相同的时间内运行更大的问题。
-   理想情况意味着问题 Px 与单处理器运行同时运行。

强可拓展性很难达到理想情况，因为规模变小，额外开销占比会增大；而弱可拓展性规模增大，处理器也增加了，额外开销和之前相比比例不变，更容易达到理想情况。


## 并行计算机内存架构

### 共享内存

基本特征：

-   共享内存并行计算机差异很大，但通常都具有**所有处理器通过全局地址空间访问所有内存**的能力。
-   多个处理器可以独立运行但共享相同的内存资源。
-   一个处理器影响的内存位置的变化对于所有其他处理器都是可见的。
-   历史上，共享内存机器根据**内存访问时间**分为 UMA 和 NUMA。

统一内存访问（Uniform Memory Access，UMA）

-   常见于对称多处理器 (SMP) 机器。
-   处理器相同。
-   所有处理器对内存的访问机会和时间是相同的。
-   有时称为 CC-UMA - Cache Coherent UMA。缓存一致性是硬件实现，意味着如果一个处理器更新共享内存中的某个位置，所有其他处理器都会知道该更新。

非统一内存访问（Non-Uniform Memory Access，NUMA）

-   通常通过物理连接两个或多个 SMP 来实现。
-   一个SMP可以直接访问另一个SMP的内存。
-   并非所有处理器对所有存储器都有相同的访问时间。
-   跨链接的内存访问速度较慢。
-   如果保持缓存一致性，则也可以称为 CC-NUMA - Cache Coherent NUMA。

优点

-   全局地址空间为内存提供了用户友好的编程视角。
-   由于内存靠近 CPU，任务之间的数据共享既快速又统一。

缺点

-   程序员要负责保证同步，以确保全局内存的“正确”访问。
-   内存和 CPU 之间缺乏可扩展性。处理器共享一个统一的内存总线。当增加更多的 CPU 时，这些 CPU 都需要通过同一个路径访问共享的内存；每增加一个 CPU，可能会引起所有 CPU 之间的更多交互和竞争，导致内存访问请求数量指数级增加。

### 分布式内存

基本特征

-   分布式内存系统差异很大，但具有共同的特征。分布式内存系统需要通信网络来连接处理器间内存。
-   处理器有自己的本地内存。一个处理器中的内存地址不会映射到另一处理器，因此不存在跨所有处理器的全局地址空间的概念。
-   由于每个处理器都有自己的本地内存，因此它独立运行。它对其本地内存所做的更改不会影响其他处理器的内存。因此，缓存一致性的概念不适用。
-   当一个处理器需要访问另一个处理器中的数据时，程序员的任务通常是明确定义如何以及何时传输数据。任务之间的同步同样是程序员的责任。
-   用于数据传输的网络“结构”差异很大，但它可以像以太网一样简单。

优点

-   内存可随着处理器的数量而扩展。增加处理器数量，内存大小也会成比例增加。
-   每个处理器都可以快速访问自己的内存，而不会受到干扰，也不会产生试图维持全局高速缓存一致性所产生的开销。
-   成本效益：可以使用商品、现成的处理器和网络。

缺点

-   程序员负责与处理器之间的数据通信相关的许多细节。
-   将基于全局内存的现有数据结构映射到该内存组织可能很困难。
-   内存访问时间不一致：访问驻留在远程节点上的数据比访问节点本地数据需要更长的时间。

### 混合分布式共享内存

-   当今世界上最大、最快的计算机同时采用共享和分布式内存架构。
-   共享存储器组件可以是共享存储器机器和/或图形处理单元(GPU)。
-   分布式内存组件是多个共享内存/GPU 机器的网络，这些机器只知道自己的内存，而不知道另一台机器上的内存。

优缺点

-   共享内存架构和分布式内存架构的共同点。
-   **提高可扩展性**是一个重要优势。
-   增加编程复杂性是一个重要劣势。

## 并行编程模型

常见的并行编程模型有以下几种：

-   共享内存模型（无线程）：多个处理器共享同一个全局内存空间。
-   线程模型：一种共享内存的并行编程模型，但每个处理单元是一个线程，而不是进程。
-   分布式内存/消息传递模型：每个处理单元都有独立的内存空间，处理单元之间通过消息传递进行通信。
-   数据并行模型：侧重于并行处理大量数据。每个处理单元执行相同的操作，但处理的数据不同，如 CUDA 和 OpenMP。
-   混合模型：通常是共享内存和分布式内存模型的结合。
-   单程序多数据 (SPMD)模型：多个处理单元运行同一个程序，但处理不同的数据。
-   多程序多数据 (MPMD)模型：多个处理单元运行不同的程序，处理不同的数据。

**并行编程模型作为硬件和内存架构之上的抽象而存在。**这些模型并不特定于特定类型的机器或内存架构，可以在任何底层硬件上实现。如下面两个例子。

#### 分布式内存机器上的共享内存模型

机器内存在物理上分布在联网的机器上，但对用户来说表现为单个共享内存全局地址空间。一般来说，这种方法被称为“虚拟共享内存”。

#### 共享内存机器上的分布式内存模型

在共享内存机器上实现分布式内存模型，通常通过在共享内存上运行分布式内存的通信库来模拟这种环境。优势有：分布式内存模型本身具有很好的扩展性，可以轻松扩展到更大规模的集群或分布式系统；每个进程独立运行，内存空间互不干扰，有助于提高程序的稳定性和可靠性。

### 共享内存模型

-   进程/任务共享一个公共地址空间，它们异步读取和写入该地址空间。
-   诸如锁/信号量之类的各种机制用于控制对共享内存的访问、解决争用并防止竞争条件和死锁。
-   不需要明确指定任务之间的数据通信。所有进程都可以平等地访问共享内存。
-   理解和管理**数据局部性**变得更加困难。
    -   内存访问：如果处理单元能够访问到本地存储的数据，内存访问速度会更快。
    -   缓存刷新：每个处理单元通常有自己的缓存。如果不同的处理单元频繁访问同一数据，这个数据在缓存中会不断被刷新和替换，从而降低缓存效率。
    -   总线流量：总线是连接处理单元和内存的通信通道。如果多个处理单元频繁访问同一数据，会增加总线流量，导致总线拥塞，进而降低整体系统性能。

#### 实现

-   在独立的共享内存机器上，本机操作系统、编译器和硬件提供对共享内存编程的支持。例如，POSIX 标准提供了使用共享内存的 API，UNIX 提供了共享内存段（shmget、shmat、shmctl等）。
-   在分布式内存机器上，内存在物理上分布在机器网络上，但可通过专门的硬件和软件实现全局化。

### 线程模型

在并行编程的线程模型中，单个“重量级”进程可以具有多个“轻量级”并发执行路径，称为线程。

-   例如，主程序a.out被安排由本机操作系统运行。 a.out 加载并获取运行所需的所有系统和用户资源。这就是“重量级”的过程。
-   a.out 执行一些串行工作，然后创建许多可以由操作系统同时调度和运行的任务（线程）。
-   每个线程都有本地数据，但也共享 a.out 的整个资源。这节省了与为每个线程复制程序资源相关的开销（“轻量级”）。
-   线程的工作最好被描述为主程序中的子例程。任何线程都可以与其他线程同时执行任何子例程。
-   线程通过全局内存（更新地址位置）相互通信。这需要同步构造来确保多个线程在任何时候都不会更新同一全局地址。
-   线程可以创建销毁，但 a.out 仍然存在以提供必要的共享资源，直到应用程序完成。

#### 实现

从历史上看，硬件供应商已经实现了自己专有的线程版本。这些实现彼此之间存在很大差异，使得程序员很难开发可移植的线程应用程序。不相关的标准化工作导致了两种截然不同的线程实现：POSIX 线程和 OpenMP。

### 分布式内存/消息传递模型

-   一组任务在计算过程中使用它们各自的本地内存。多个任务可以驻留在同一台物理机器上，或者分布在任意数量的机器上。
-   任务通过发送和接收消息来进行通信来交换数据。
-   数据传输通常需要各个进程协同操作。例如，发送操作必须有匹配的接收操作。

#### 实现

从编程的角度来看，消息传递实现通常包含子例程库。对这些子例程的调用嵌入在源代码中。程序员负责确定所有并行性。MPI 是消息传递的“事实上的”行业标准，几乎取代了用于生产工作的所有其他消息传递实现。几乎所有流行的并行计算平台都存在 MPI 实现。

### 数据并行模型

也可称为分区全局地址空间 (PGAS) 模型。

-   地址空间被全局对待。
-   大多数并行工作都集中在对数据集执行操作。数据集通常被组织成通用结构，例如数组或立方体。
-   一组任务共同作用于同一数据结构，但是每个任务作用于同一数据结构的不同分区。
-   任务对其工作分区执行相同的操作，例如“向每个数组元素添加 4”。
-   在共享内存架构上，所有任务都可以通过全局内存访问数据结构。
-   在分布式内存架构上，全局数据结构可以在逻辑上和/或物理上跨任务分割。

### 混合模型

混合模型的常见示例是消息传递模型（MPI）与线程模型（OpenMP）的组合。线程使用本地节点数据执行计算密集型内核，不同节点上的进程之间的通信使用 MPI 通过网络进行。适合集群多核/众核机器硬件环境。

另一个类似且越来越流行的混合模型示例是使用 MPI 与 CPU-GPU 编程。MPI 任务使用本地内存在 CPU 上运行，并通过网络相互通信；计算密集型内核被卸载到节点上的 GPU；节点本地内存和 GPU 之间的数据交换使用 CUDA。

### SPMD and MPMD

SPMD 实际上是一种“高级”编程模型，可以构建在前面提到的并行编程模型的任意组合之上。

-   单个程序：所有任务同时执行同一程序的副本。该程序可以是线程、消息传递、数据并行或混合的。
-   多个程序：任务可以同时执行不同的程序。这些程序可以是线程、消息传递、数据并行或混合的。

## 设计并行程序

### 自动 vs. 手动并行化

-   设计和开发并行程序通常是一个手动的过程，程序员通常负责识别和实际实现并行性。
-   手动开发并行代码是一个耗时、复杂、容易出错且迭代的过程。
-   已经有各种工具可以帮助程序员将串行程序转换为并行程序。用于自动并行化串行程序的最常见工具类型是并行化编译器或预处理器。
-   并行编译器通常以全自动、程序员指导两种不同的方式工作。

#### 全自动

-   编译器分析源代码并识别并行性的机会。
-   该分析包括确定并行性的抑制因素，以及可能对并行性是否真正提高性能进行成本权重。
-   循环（do、for）是自动并行化最常见的目标。

#### 程序员指导

-   使用“编译器指令”或可能的编译器标志，程序员明确告诉编译器如何并行化代码。
-   也可以与某种程度的自动并行化结合使用。
-   最常见的编译器生成的并行化是使用节点共享内存和线程（例如 OpenMP）完成的。

有几个适用于自动并行化的重要注意事项：

1.   可能会产生错误的结果
2.   性能实际上可能会下降
3.   比手动并行化灵活性差得多
4.   仅限于代码的子集（主要是循环）
5.   如果编译器分析表明存在抑制因素或代码过于复杂，实际上可能不会并行化代码

### 了解问题和计划

程序 = 算法 + 数据 +（硬件）

-   确定问题是否可以并行化。比如使用 `F(n)=F(n-1)+F(n-2)` 计算斐波那契数列，则基本没有并行性，若使用比萘公式，则可以并行计算。
-   确定程序的热点（hotspots），分析器和性能分析工具确定大部分实际工作是在哪里完成的。
-   识别程序中的瓶颈（bottlenecks），例如 I/O 通常会减慢程序速度。可以重组程序或使用不同的算法来减少或消除不必要的慢速区域。

### 分区 Partitioning

设计并行程序的第一步是将问题分解为可以分配给多个任务的离散工作“块”，这称为分区。

在并行任务之间划分计算工作有两种基本方法：领域分解和功能分解。

#### Domain Decomposition 领域分解

在这种类型的分区中，与问题相关的数据被分解。然后，每个并行任务都处理一部分数据。

#### Functional Decomposition 功能分解

问题根据必须完成的工作进行分解。然后，每个任务执行整体工作的一部分。功能分解非常适合解决可以分解为不同任务的问题，如信号处理。

音频信号数据集通过四个不同的计算滤波器。每个过滤器都是一个单独的过程。第一段数据必须先通过第一个过滤器，然后才能进入第二个过滤器。此时，第二段数据将通过第一个过滤器。当第四段数据进入第一个过滤器时，所有四个任务都已繁忙。

### 通信 Communications

某些类型的问题可以分解并并行执行，几乎不需要任务共享数据。通常称为 embarrassingly parallel。

大多数并行应用程序并不是那么简单，并且确实需要任务彼此共享数据。

#### 需要考虑的因素

-   通信开销：打包和传输数据、等待同步、通信流量竞争。
-   延迟与带宽：通常，将小消息打包成较大消息会可以减少延迟，从而增加有效通信带宽。
-   通信可见性：使用消息传递模型通信是可见的，使用数据并行模型通信通常是透明的。
-   同步与异步通信：是否阻塞。
-   通信范围：点对点通信和一对多通信等。
    -   Broadcast（广播）：将一个进程中的数据发送到所有其他进程。
    -   Scatter（散播）：将一个进程中的整体数据分割成若干部分，然后将这些部分分别发送给不同的其他进程。
    -   Gather（收集）：从各个进程收集数据，并将这些数据传回到一个进程。
    -   Reduction（归约）：将多个进程中的数据通过某种操作（如求和、求最大值）进行组合，最后得到一个结果并传回到一个进程。
-   通信效率：网络结构、同步或异步通信、消息传递模型等。
-   开销和复杂度。

### 同步 Synchronization

-   管理工作顺序和执行工作的任务是大多数并行程序的关键设计考虑因素。
-   可能是程序性能（或缺乏性能）的重要因素。
-   通常需要对程序的各个部分进行“序列化”。

#### 同步类型

##### Barrier 障碍

通常意味着涉及所有任务，每个任务都执行其工作，直到到达障碍。然后它停止，或“阻塞”。当最后一个任务到达障碍时，所有任务都会同步。

##### Lock / semaphore 锁/信号量

通常用于序列化（保护）对全局数据或一段代码的访问。一次只有一个任务可以使用（拥有）锁/信号量/标志。获取锁的第一个任务“设置”它。然后，该任务可以安全（串行）访问受保护的数据或代码。

##### Synchronous communication operations 同步通讯操作

当任务执行通信操作时，需要与参与通信的其他任务进行某种形式的协调。例如，在任务执行发送操作之前，它必须首先从接收任务接收到可以发送的确认。

### 数据依赖性 Data Dependencies

-   当语句执行顺序影响程序结果时，程序语句之间就存在依赖性。
-   数据依赖性是由不同任务多次使用存储中的相同位置造成的。

#### 如何处理数据依赖性

-   分布式内存架构 - 在同步点传送所需的数据。
-   共享内存架构 - 同步任务之间的读/写操作。

### 负载均衡 Load Balancing 

负载平衡是指在任务之间分配大致相等的工作量，以便所有任务始终保持忙碌的做法。可以认为是任务空闲时间的最小化。出于性能原因，负载平衡对于并行程序很重要。例如，如果所有任务都受到障碍同步点的影响，则最慢的任务将决定整体性能。

#### 如何实现负载均衡

##### 平均分配每个任务接收的工作

-   对于每个任务执行类似工作的数组/矩阵运算，请在任务之间均匀分配数据集。
-   对于每次迭代中完成的工作相似的循环迭代，将迭代均匀地分布在任务之间。
-   如果使用具有不同性能特征的异构机器组合，使用某种类型的性能分析工具来检测任何负载不平衡，相应地调整工作。

##### 使用动态工作分配

即使数据在任务之间均匀分布，某些类别的问题也会导致负载不平衡。当每个任务将执行的工作量故意变化或无法预测时，使用调度程序任务池方法可能会有所帮助。当每个任务完成其工作时，它会从工作队列接收一个新的部分。

### 粒度 Granularity

在并行计算中，粒度是计算与通信比率的定性度量。计算周期通常通过同步事件与通信周期分开。

#### 细粒度并行性

-   通信事件之间完成相对少量的计算工作。
-   计算与通信比率低。
-   有利于负载平衡。
-   意味着较高的通信开销和较少的性能增强机会。

#### 粗粒度并行性

和细粒度相反。

### I/O

-   可以使用并行文件系统，如 GPFS、HDFS 等。
-   MPI 并行 I/O 编程接口规范可用。
-   尽可能减少总体 I/O。
-   写入大数据块而不是小数据块通常效率更高。

### 性能分析调优 Performance Analysis and Tuning

## 并行示例

### 数组处理

本例演示了二维数组元素的计算；对每个数组元素执行一个函数。计算相互独立，为计算密集型问题，串行程序按顺序一次计算一个元素。

#### 并行方案 1

-   元素的计算是相互独立的——导致了一种 embarrassingly parallel 的解决方案。
-   数组元素均匀分布，因此每个进程都拥有数组的一部分（子数组）。
-   数组元素的独立计算确保任务之间不需要通信或同步。
-   由于工作量均匀分布在进程之间，因此不应该存在负载平衡问题。
-   分配数组后，每个任务都会执行与其拥有的数据相对应的循环部分。

#### 并行解决方案 2：任务池

##### 主进程

维护进程池给工作进程来处理，给工作进程分配工作，收集工作进程的结果。

##### 工作进程

从主进程获取任务，执行计算后，将结果发送给主进程。

-   工作进程在运行时之前不知道它们将处理数组的哪一部分或它们将执行多少任务。
-   动态负载平衡发生在运行时：任务越快，就会有更多的工作要做。
