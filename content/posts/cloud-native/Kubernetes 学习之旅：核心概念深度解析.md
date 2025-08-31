---
categories:
- Cloud Native
date: 2025-08-31 11:43:55+08:00
draft: true
slug: 20250831-ucoyfjaa
summary: 本文系统解析Kubernetes 30个核心概念，涵盖Pod、Deployment、Service、Ingress、HPA及CRD等关键技术，提供从入门到精通的云原生学习路径，助力开发者构建生产级容器化应用。
tags:
- k8s
title: Kubernetes 学习之旅：核心概念深度解析
---

## 1 **引言**

在当今的技术浪潮中，向云原生架构的转型已成为不可逆转的趋势。容器化与微服务彻底重塑了应用的开发、部署与运维模式，而 Kubernetes（常简称为 K8s）则凭借其强大的自动化、伸缩性和可移植性，成为了容器编排领域无可争议的行业标准。它不仅仅是一个工具，更是一个构建弹性、可扩展分布式系统的平台和生态系统。

本报告旨在为有志于成为云原生工程师的学习者提供一条清晰、循序渐进的路径。它并非一份简单的术语表，而是一次精心设计的学习之旅，分为五个连贯的阶段。从部署第一个应用的基础操作，到驾驭复杂工作负载，再到深潜架构内部原理，直至掌握安全与扩展等高级主题，本报告将系统性地解析 30 个 Kubernetes 的核心概念。

通过这次旅程，学习者将建立起一个坚实且全面的知识框架，目标是达到对 Kubernetes 架构、核心对象和设计哲学的中级精通水平。这将为应对真实世界的生产环境挑战、构建稳健的云原生应用打下至关重要的基础。

---

## 2 第一阶段：入门 - 部署你的第一个应用

本阶段的目标是建立对 Kubernetes 最基本、最核心概念的理解。通过掌握这些原子构建块，学习者将能够成功地在集群中运行一个简单的无状态应用，并实现对其的访问。这是后续所有学习的基石。

### 2.1 Pod

**电梯演讲**：Kubernetes Pod 是最小、最基础的可部署单元。它代表了集群中一个正在运行的进程实例，封装了一个或多个紧密耦合的容器、它们共享的存储资源以及一个唯一的内部网络 IP。可以将其视为构建应用的 " 原子 "。

#### 2.1.1 **深度解析**

**原子单元**  

在 Kubernetes 的对象模型中，Pod 是能够创建和部署的最小、最简单的单元。它并非直接管理单个容器，而是将一个或多个容器组合成一个逻辑主机。所有调度、部署和伸缩的基本单位都是 Pod，而非容器。这种设计是 Kubernetes 的核心区别之一。  

**Pod 的生命周期**  

Pod 被设计为相对短暂的实体，而非持久的服务。每个 Pod 在创建时都会被分配一个唯一的 ID (UID)，并被调度到一个节点上运行，直至其终止或被删除。其生命周期包含几个明确的阶段（phase）：

- Pending：Pod 已被 Kubernetes 系统接受，但其容器尚未全部创建完成。这通常包括等待调度和从镜像仓库拉取镜像的时间。
- Running：Pod 已经绑定到了一个节点，并且其所有容器都已被创建。至少有一个容器正在运行，或者正处于启动或重启状态。
- Succeeded：Pod 中的所有容器都已成功终止，并且不会再重启。这通常用于 Job 或一次性任务。
- Failed：Pod 中的所有容器都已终止，并且至少有一个容器是因失败而终止的。
- Unknown：由于某种原因，无法获取 Pod 的状态，这通常是由于与该 Pod 所在节点的通信问题导致的。

重要的是，Pod 本身不具备自愈能力。当一个 Pod 或其所在的节点发生故障时，该 Pod 不会自动在别处重建。这种自愈能力是由更高级别的控制器（如 Deployment）提供的。

**共享上下文**  

Pod 的真正威力在于它为内部的容器提供了一个共享的执行环境。所有位于同一个 Pod 内的容器共享以下资源：

- **网络命名空间**：它们共享同一个网络 IP 地址和端口空间。这意味着 Pod 内的容器可以通过 localhost 互相通信，就像它们运行在同一台物理机上一样。
- **存储卷**：可以在 Pod 级别定义一组存储卷，Pod 内的所有容器都可以挂载和访问这些卷，从而实现数据共享。一个常见的例子是**使用 emptyDir 卷作为临时共享空间**。
- **IPC 命名空间**：可以选择性地共享进程间通信命名空间。

这种设计模式允许将紧密协作的辅助进程（如日志收集器、服务网格代理，通常称为 " 边车 " 或 sidecar 容器）与主应用容器部署在一起，同时保持每个进程在各自容器中的隔离性。

从架构层面看，Pod 是对容器的进一步抽象。早期的容器编排系统直接管理容器，但现实世界的应用往往需要多个进程协同工作。例如，一个 Web 服务器可能需要一个日志代理来收集其日志。将这两个进程打包进一个容器会破坏 " 每个容器一个进程 " 的最佳实践，而将它们分开部署又会使通信和资源共享变得复杂。Pod 正是为解决这一问题而生，它提供了多容器协同工作所需的共享环境，同时维持了容器的独立性。这一抽象是 Kubernetes 能够优雅地管理复杂应用的关键所在。

#### 2.1.2 **YAML 示例**

以下是一个简单的 Pod 定义，它运行一个 NGINX 容器：

```YAML
apiVersion: v1  
kind: Pod  
metadata:  
  name: my-nginx-pod  
  labels:  
    app: nginx  
spec:  
  containers:  
  - name: nginx-container  
    image: nginx:latest  
    ports:  
    - containerPort: 80
```

- `apiVersion: v1`：指定了创建此对象所使用的 Kubernetes API 版本。v1 是 Pod 等核心对象的稳定版本。
- `kind: Pod`：声明此对象的类型是 Pod。
- `metadata`：包含了关于 Pod 的元数据，如唯一的 name 和用于识别与组织的 labels。
- `spec`：定义了 Pod 的期望状态，其中 containers 字段是一个列表，描述了要在此 Pod 中运行的所有容器。

### 2.2 Container Runtime (容器运行时)

**电梯演讲**：容器运行时是每个节点上真正负责运行容器的底层引擎。它是 Kubernetes（通过 kubelet）指挥的 " 手和脚 "，负责从镜像仓库拉取镜像、启动和停止 Pod 内的容器。

#### 2.2.1 **深度解析**

**底层引擎**  

集群中的每个节点都必须安装一个容器运行时，这样 Pod 才能在其上运行。容器运行时是执行和管理容器生命周期的核心软件。  

**CRI 标准**  

Kubernetes 通过一个名为容器运行时接口（Container Runtime Interface, CRI）的插件接口与容器运行时进行通信。CRI 定义了一套标准的 gRPC API，kubelet 通过这套 API 来命令容器运行时执行各种操作，如创建 Pod 沙箱、拉取镜像、创建和启动容器等。  

CRI 的出现是 Kubernetes 演进过程中的一个重要里程碑。早期，Kubernetes 与 Docker Engine 紧密耦合。为了支持更多种类的容器运行时并促进生态系统的发展，社区创建了 CRI 标准。这使得 Kubernetes 核心代码可以与任何实现了 CRI 接口的容器运行时解耦。这一举措最终导致了在 Kubernetes 1.24 版本中移除了内置的 dockershim（一个用于适配 Docker Engine 的组件），使得所有运行时都必须通过 CRI 标准进行集成。这种模块化设计让 Kubernetes 平台本身更加灵活和面向未来，能够轻松接纳新的运行时技术，如轻量级运行时或提供更强隔离性的沙箱运行时（如 Kata Containers）。

**主流容器运行时**  

目前，社区中最主流的 CRI 兼容运行时包括：

- **containerd**：最初由 Docker 公司开发并捐赠给 CNCF，containerd 是一个业界标准的容器运行时，专注于提供稳定、高性能的核心容器管理功能。它是目前许多 Kubernetes 发行版的默认选择。
- **CRI-O**：这是一个专为 Kubernetes 设计的轻量级容器运行时。它的唯一目标就是成为一个优秀的 CRI 实现，因此不包含任何 Kubernetes 不需要的多余功能，力求简洁、稳定和安全。

**Cgroup 驱动**  

在 Linux 系统上，控制组（cgroups）是实现容器资源限制（如 CPU 和内存限制）的关键内核特性。kubelet 和容器运行时都必须与 cgroups 交互来强制执行这些资源策略。为了保证系统稳定，kubelet 和容器运行时必须配置使用相同的 cgroup 驱动。主要有两种驱动：

- `cgroupfs`：直接与 cgroup 文件系统交互。
- `systemd`：通过 systemd 的接口来管理 cgroup。当操作系统使用 systemd 作为初始化系统时，推荐使用 systemd 驱动，以确保资源管理的统一和稳定。

配置不匹配的 cgroup 驱动是集群中一个常见且难以排查的问题来源，尤其是在资源压力较大时，可能导致 Pod 行为异常。

### 2.3 Node (节点)

**电梯演讲**：Kubernetes 节点是一台工作机器，可以是物理机或虚拟机，是您应用（以 Pod 形式）实际运行和执行的地方。每个节点都由控制平面管理，并包含运行 Pod 所必需的核心服务。

#### 2.3.1 **深度解析**

**工作单元**

一个 Kubernetes 集群由一个控制平面（Control Plane）和一组工作节点（Node）组成。节点是承载工作负载的主机，Pod 最终会被调度到某个节点上运行。一个生产集群通常包含多个节点以实现高可用性和负载均衡，但在学习或资源受限的环境中，也可能只有一个节点。  

**节点上的核心组件**  

每个节点上都必须运行三个关键组件，使其能够被控制平面管理并运行工作负载：

1. **kubelet**：这是运行在每个节点上的主要 " 节点代理 "。它负责与控制平面的 API Server 通信，接收在该节点上运行 Pod 的指令，并确保这些 Pod 中的容器处于健康运行状态。
2. **Container Runtime**：如前所述，这是负责实际运行容器的软件。
3. **kube-proxy**：这是一个网络代理，运行在每个节点上。它负责维护节点上的网络规则，这些规则实现了 Kubernetes Service 的概念，允许对 Pod 进行网络通信。

**节点的管理与状态** 

节点通过向 API Server 注册来加入集群。注册后，控制平面中的 Node Controller 组件会开始管理该节点。它会持续监控节点的健康状况。节点通过两种方式向控制平面报告心跳，以表明其可用性：更新节点对象的  
.status 字段，以及在 kube-node-lease 命名空间中更新 Lease 对象。

如果一个节点长时间没有发送心跳，Node Controller 会将其状态标记为 Unknown。经过一段超时（默认为 5 分钟）后，控制器会认为该节点已宕机，并触发驱逐机制，将运行在该节点上的所有 Pod 标记为删除，以便它们可以在其他健康节点上被重建。

从架构上看，Kubernetes 集群是一个典型的状态机。API Server 中存储的 Node 对象是物理或虚拟机的**表示**，而非机器本身。控制平面通过操作这个表示来管理集群。当一台物理服务器启动并运行 kubelet 时，kubelet 会向 API Server 注册，从而创建一个 Node 对象。调度器和节点控制器看到的是这个对象及其报告的容量和状态，而非直接与物理机交互。这种将期望状态（API 对象）与物理世界的实际状态解耦的设计，是 Kubernetes 能够以声明方式管理集群并自动应对故障的核心机制。

### 2.4 **4. Labels & Selectors (标签与选择器)**

**电梯演讲**：标签和选择器是 Kubernetes 的 " 粘合剂 "。标签是附加到 Pod 等对象上的简单键值对，而选择器则是用于查询和筛选带有特定标签对象的工具。这种松耦合的机制是 Service 找到其后端 Pod 的核心方式。

#### 2.4.1 **深度解析**

**键值对元数据**

标签（Labels）是可以附加到任何 Kubernetes 对象（如 Pod、Service、Deployment）上的键值对。它们旨在用于指定对用户有意义和相关的对象识别属性。例如，可以为一个 Pod 添加标签 app: my-backend，environment: production，tier: database。标签的键和值是字符串，可以灵活定义。

**查询语言**  

选择器（Selectors）是 Kubernetes 的核心分组机制，它允许用户根据标签来识别和选择一组对象。这是实现许多高级功能的基石。  

**核心应用场景**  

标签和选择器最重要的应用是将不同的 Kubernetes 资源动态地关联起来。最经典和关键的例子是 Service 和 Deployment 之间的协作：

1. 一个 Deployment 的 Pod 模板（`.spec.template.metadata.labels`）中定义了一组标签，例如 app: my-app。
2. 当 Deployment 创建 Pod 时，这些 Pod 都会带上 app: my-app 这个标签。
3. 一个 Service 在其规约（.spec.selector）中定义了一个选择器，内容也是 app: my-app。
4. Kubernetes 的 EndpointSlice 控制器会持续监控集群，查找所有带有 app: my-app 标签且状态健康的 Pod，并将其 IP 地址和端口更新到与该 Service 关联的 EndpointSlice 对象中。
5. 当有流量发送到这个 Service 的虚拟 IP 时，kube-proxy 会根据 EndpointSlice 中的信息，将流量负载均衡到后端的某个 Pod 上。

这种机制的精妙之处在于其**动态性和松耦合**。Service 不需要知道后端 Pod 的具体 IP 地址，也不关心它们是由哪个 Deployment 创建的，它只关心标签是否匹配。这使得应用的滚动更新、扩缩容和故障恢复变得无缝。当 Deployment 进行滚动更新时，它会创建带有相同标签的新版本 Pod，Service 的选择器会自动将它们纳入负载均衡池；同时，旧版本的 Pod 被终止后，它们会自动从 EndpointSlice 中移除。整个过程无需人工干预，系统实现了动态的自我管理。

#### 2.4.2 **YAML 示例**

以下示例展示了一个 Deployment 和一个 Service 如何通过标签和选择器协同工作：

**Deployment (deployment.yaml)**

```YAML
apiVersion: apps/v1  
kind: Deployment  
metadata:  
  name: my-app-deployment  
spec:  
  replicas: 3  
  selector:  
    matchLabels:  
      app: my-app \# 这个选择器告诉 Deployment 要管理哪些 Pod  
  template:  
    metadata:  
      labels:  
        app: my-app \# Pod 模板带有的标签  
    spec:  
      containers:  
      - name: my-app-container  
        image: nginx
```

**Service (service.yaml)**

```YAML
apiVersion: v1  
kind: Service  
metadata:  
  name: my-app-service  
spec:  
  selector:  
    app: my-app # 这个选择器告诉 Service 要将流量转发到哪些 Pod  
  ports:  
  - protocol: TCP  
    port: 80  
    targetPort: 80
```

在这个例子中，my-app-service 会自动发现并负载均衡所有由 my-app-deployment 创建的、带有 app: my-app 标签的 Pod。

### 2.5 **5. Deployment (部署)**

**电梯演讲**：Deployment 是在 Kubernetes 中管理无状态应用的标准方式。您以声明式的方式告诉它要运行哪个容器镜像以及需要多少个副本，Deployment 控制器就会处理剩下的一切——创建 Pod、执行滚动更新以及维护期望的状态。

#### 2.5.1 **深度解析**

1. 声明式应用管理  
Deployment 是一个更高级别的 API 对象，它为 Pod 和 ReplicaSet 提供声明式的更新管理。核心思想是，用户只需定义应用的 " 期望状态 "（desired state），例如：" 我需要运行 3 个副本的  
nginx:1.14.2 镜像 "。Deployment 控制器会持续工作，确保集群的 " 当前状态 "（current state）与这个期望状态相匹配。

2. 层级关系：Deployment -> ReplicaSet -> Pod  
为了实现版本控制和回滚，Deployment 引入了 ReplicaSet 这一中间层。它们之间的关系如下：

- **Deployment**：管理应用的整个生命周期，包括版本更新和回滚。
- **ReplicaSet**：确保在任何时候都有指定数量的 Pod 副本在运行。它是一个版本化的实体。
- **Pod**：应用的实际运行实例。

当创建一个 Deployment 时，它会自动创建一个 ReplicaSet，该 ReplicaSet 再去创建指定数量的 Pod。当更新 Deployment（例如，更改容器镜像版本）时，Deployment 控制器会创建一个新的 ReplicaSet，并采用一种策略（默认为滚动更新）逐步地将流量从旧的 ReplicaSet 迁移到新的 ReplicaSet，从而实现零停机更新。直接操作 ReplicaSet 是不被推荐的，用户应始终通过 Deployment 来管理应用。

3. 滚动更新（Rolling Updates）  
这是 Deployment 的标志性功能。在滚动更新期间，Deployment 会确保总是有一定数量的 Pod 可用。它会逐个创建新版本的 Pod，并在新 Pod 准备就绪后，再逐个删除旧版本的 Pod。这个过程的速度和可用性可以通过 maxUnavailable 和 maxSurge 参数进行微调。如果更新过程中出现问题，可以轻松地回滚到上一个稳定的 ReplicaSet 版本。  
这种由 Deployment、ReplicaSet 和 Pod 组成的层级控制器模型，是 Kubernetes 控制循环哲学的完美体现。用户的意图（更新镜像）触发了 Deployment 控制器的调谐循环，该循环通过创建和伸缩不同的 ReplicaSet 来逐步实现状态迁移。这个过程是自动、安全且健壮的。

4. 适用场景：无状态应用  
Deployment 专为无状态应用设计。无状态意味着任何一个 Pod 副本都可以被另一个副本替换，而不会丢失任何关键状态。所有 Pod 都是相同的、可互换的 " 牛 "（cattle），而不是独一无二的 " 宠物 "（pets）9。对于需要稳定身份和持久化数据的应用，应使用 StatefulSet。

#### 2.5.2 **YAML 示例**

一个典型的 Deployment YAML 如下所示：

```YAML
apiVersion: apps/v1  
kind: Deployment  
metadata:  
  name: nginx-deployment  
  labels:  
    app: nginx  
spec:  
  replicas: 3  
  selector:  
    matchLabels:  
      app: nginx  
  template:  
    metadata:  
      labels:  
        app: nginx  
    spec:  
      containers:  
      \- name: nginx  
        image: nginx:1.14.2  
        ports:  
        \- containerPort: 80
```

- replicas: 3：定义了期望的副本数量。
- selector.matchLabels：定义了此 Deployment 如何识别它所管理的 Pod。
- template：定义了要创建的 Pod 的模板，包括其标签、容器镜像等。

### 2.6 **6. Service (服务)**

**电梯演讲**：Kubernetes Service 为一组功能相同的 Pod 提供了一个稳定的网络入口。由于 Pod 的 IP 地址会随着它们的创建和销毁而改变，Service 提供了一个固定的虚拟 IP 地址或 DNS 名称，让其他应用可以稳定地访问它们，并自动处理负载均衡。

#### 2.6.1 **深度解析**

解决 Pod 的短暂性问题  
在 Kubernetes 中，Pod 是短暂的。每当 Pod 被重新创建（例如在滚动更新或节点故障后），它都会获得一个新的 IP 地址。如果应用的其他部分直接依赖于某个 Pod 的 IP 地址，那么这种依赖关系会非常脆弱。Service 抽象正是为了解决这个问题而设计的。  
服务发现与负载均衡  
Service 的两大核心功能是：

1. **服务发现**：Service 提供一个稳定的访问端点。在集群内部，每个 Service 都会被分配一个虚拟 IP 地址（ClusterIP），并且会有一个对应的 DNS 条目（例如 my-service.my-namespace.svc.cluster.local）。应用可以通过这个固定的 IP 或 DNS 名称来访问服务，而无需关心后端 Pod 的具体位置。
2. **负载均衡**：当一个 Service 背后有多个 Pod 副本时，发送到 Service IP 的流量会被自动分发到其中一个健康的后端 Pod 上。

这个机制的底层实现者是运行在每个节点上的 kube-proxy。kube-proxy 会监视 API Server 中 Service 和 EndpointSlice 的变化，并相应地修改节点上的 iptables 或 IPVS 规则，从而实现流量的拦截、NAT 转换和分发。这种分布式的实现方式避免了单点瓶颈，使得服务间通信高效且可靠。

Service 的类型  
根据不同的暴露需求，Service 有几种不同的类型 10：

|类型 (Type)|范围/可访问性|使用场景|工作原理|
|---|---|---|---|
|ClusterIP|仅集群内部|集群内部服务间通信，如前端调用后端 API。|(默认类型) 分配一个仅在集群内部可达的虚拟 IP。|
|NodePort|集群内外|需要从外部快速访问服务进行测试或演示。|在每个节点的同一静态端口上暴露服务。外部流量通过 NodeIP:NodePort 访问。|
|LoadBalancer|集群外部|在公有云上将服务正式暴露给互联网用户。|(基于 NodePort) 请求云提供商创建一个外部负载均衡器，并将其指向所有节点的 NodePort。|
|ExternalName|DNS 级别重定向|需要在集群内部通过一个固定名称访问集群外部的服务。|不进行代理，而是返回一个外部域名的 CNAME 记录。|

#### 2.6.2 **YAML 示例**

这是一个 ClusterIP 类型的 Service，它将流量转发到带有 app: my-app 标签的 Pod 的 9376 端口：

YAML

apiVersion: v1  
kind: Service  
metadata:  
name: my-service  
spec:  
selector:  
app.kubernetes.io/name: MyApp  
ports:  

- protocol: TCP  
port: 80  
targetPort: 9376

- selector：定义了该 Service 应该将流量路由到哪些 Pod。
- port：Service 自身暴露的端口。
- targetPort：流量将被转发到后端 Pod 上的目标端口。

### 2.7 **7. Namespace (命名空间)**

**电梯演讲**：Namespace 就像在您的物理 Kubernetes 集群内部创建的 " 虚拟集群 "。它为资源名称提供了一个作用域，允许您按项目、团队或环境对资源进行逻辑分组和隔离，从而避免名称冲突并实现资源配额管理。

#### 2.7.1 **深度解析**

逻辑隔离  
当一个 Kubernetes 集群被多个团队或项目共享时，可能会出现资源名称冲突的问题（例如，两个团队都想创建一个名为 database 的 Service）。Namespace 通过为资源名称提供一个作用域来解决这个问题。在一个 Namespace 内，资源名称必须是唯一的，但在不同的 Namespace 之间则可以重名。  
多租户的基础  
Namespace 是在 Kubernetes 中实现多租户的基础。虽然它本身不提供强安全隔离，但它是一个组织和管理资源的逻辑边界。通过将以下机制与 Namespace 结合，可以构建出安全的多租户环境：

- **RBAC (基于角色的访问控制)**：可以限制用户或团队只能访问其指定 Namespace 内的资源。
- **ResourceQuotas**：可以为每个 Namespace 设置资源配额，限制其可以使用的 CPU、内存总量，以及可以创建的对象数量（如 Pod、Service 的数量）。
- **NetworkPolicies**：可以定义网络策略，限制不同 Namespace 之间的 Pod 通信。

因此，Namespace 是一个核心的组织原则，它使得其他所有多租户功能得以实施。它为构建一个安全的、共享的平台提供了起点。

默认的 Namespaces  
Kubernetes 启动时会创建几个默认的 Namespace：

- default：如果您在创建资源时没有指定 Namespace，它们会被创建在这个 Namespace 中。
- kube-system：用于 Kubernetes 系统自身组件，如控制平面组件、核心插件等。普通用户不应在此 Namespace 中创建资源。
- kube-public：此 Namespace 中的资源对所有用户（包括未认证用户）都是可读的。通常用于存放一些需要被整个集群公开访问的数据。
- kube-node-lease：用于存放与节点心跳相关的 Lease 对象。

### 2.8 **8. Kubectl (命令行工具)**

**电梯演讲**：kubectl 是您与任何 Kubernetes 集群交互的命令行 " 遥控器 "。它是您用来部署应用、检查资源、查看日志和管理集群日常运维的主要工具，其所有操作都是通过与 Kubernetes API 通信完成的。

#### 2.8.1 **深度解析**

与集群交互的入口  
kubectl 是 Kubernetes 官方提供的命令行接口（CLI）工具，用于与集群的 API Server 进行通信。几乎所有对集群的管理和操作都可以通过  
kubectl 完成。它通过读取 kubeconfig 文件（通常位于 ~/.kube/config）来获取集群的地址和认证信息。

命令式与声明式操作  
kubectl 支持两种主要的操作模式：

1. **命令式命令 (Imperative Commands)**：例如 kubectl run my-pod --image=nginx 或 kubectl create deployment...。这种方式直接、易于上手，适合快速执行一次性任务或在学习阶段使用。
2. **声明式对象配置 (Declarative Object Configuration)**：这是生产环境中推荐的最佳实践。用户将资源的期望状态定义在 YAML 或 JSON 文件中，然后使用 kubectl apply -f <filename.yaml> 命令来应用这些配置。这种方式的优势在于：
    - **版本控制**：配置文件可以存放在 Git 等版本控制系统中，便于追踪变更、协作和审计。
    - **可重复性**：可以轻松地在不同环境（开发、测试、生产）中重复部署相同的应用。
    - **幂等性**：反复执行 kubectl apply 会达到相同的最终状态，而不会产生错误。

核心命令  
以下是一些最常用和最重要的 kubectl 命令：

- kubectl get <resource>：列出资源。例如 kubectl get pods。
- kubectl describe <resource> <name>：显示资源的详细信息，包括事件，非常适合排错。例如 kubectl describe pod my-pod。
- kubectl apply -f <file>：通过文件名或标准输入创建或更新资源。
- kubectl delete -f <file> 或 kubectl delete <resource> <name>：删除资源。
- kubectl logs <pod-name>：查看 Pod 中容器的日志。
- kubectl exec -it <pod-name> -- <command>：在 Pod 的容器内执行命令，例如 kubectl exec -it my-pod -- /bin/bash 可以进入容器的交互式 Shell。

kubectl 的强大功能和灵活性直接源于 Kubernetes API 的设计。Kubernetes 的所有功能都通过一个一致的、基于资源的 REST API 暴露出来。

kubectl 本质上是这个 API 的一个精心设计的客户端，它将用户友好的命令翻译成底层的 HTTP 请求。因此，任何可以通过 API 完成的操作，也都可以通过 kubectl 完成。

---

## 3 **第二阶段：进阶 - 让应用生产就绪**

在掌握了部署和访问应用的基础之后，本阶段将关注让应用达到生产环境标准所需的关键要素：如何管理配置和敏感信息、如何实现数据持久化、如何将服务安全地暴露给外部世界，以及如何简化复杂应用的部署流程。

### 3.1 **9. ConfigMap & Secret (配置映射与保密字典)**

**电梯演讲**：ConfigMap 和 Secret 允许您将配置与应用代码解耦。ConfigMap 用于存储非敏感数据，如功能开关或 URL；而 Secret 则专为密码、API 密钥等敏感数据设计，通过 Base64 编码和独立的管理方式提供额外的安全层。

#### 3.1.1 **深度解析**

配置与代码分离  
在云原生应用开发中，一个核心原则是将配置（所有在不同环境间会发生变化的东西）与代码分离。硬编码配置会使应用难以移植和维护。ConfigMap 和 Secret 是 Kubernetes 提供的原生解决方案，用于将配置数据注入到 Pod 中，而无需修改容器镜像。  
ConfigMap  
ConfigMap 是一个用于存储非机密性配置数据的 API 对象，它以键值对的形式组织数据。这些数据可以是单个属性，也可以是完整的配置文件内容。

- **数据格式**：data 字段用于存储 UTF-8 编码的字符串。
- **大小限制**：ConfigMap 不适合存储大量数据，其大小不能超过 1 MiB。对于更大的数据，应考虑使用挂载卷或外部数据库。

Secret  
Secret 的设计目的与 ConfigMap 类似，但它专门用于存储和管理敏感信息，如密码、OAuth 令牌、SSH 密钥等。

- **数据编码**：Secret 中的数据以 Base64 格式进行编码存储。需要强调的是，**Base64 是编码，而非加密**。它只能防止无意的窥视，但无法阻止有意的解码。为了真正保护 Secret 中的数据，必须在  
    etcd 层面启用静态加密（Encryption at Rest）19。
- **内置类型**：Kubernetes 为常见场景提供了一些内置的 Secret 类型，如 kubernetes.io/tls 用于存储 TLS 证书和私钥，kubernetes.io/dockerconfigjson 用于存储访问私有镜像仓库的凭据。

在 Pod 中使用 ConfigMap 和 Secret  
Pod 可以通过多种方式使用 ConfigMap 和 Secret 中的数据，最常见的三种方式是：

1. **作为环境变量**：可以将 ConfigMap 或 Secret 中的特定键值注入为容器的环境变量。这是 " 十二因子应用 " 推荐的模式。
2. **作为卷挂载的文件**：可以将整个 ConfigMap 或 Secret 作为一个卷挂载到容器的文件系统中的某个目录下。每个键值对会成为该目录下的一个文件，文件名是键，文件内容是值。这种方式对于需要读取配置文件的传统应用非常友好。
3. **作为命令行参数**：可以通过环境变量的方式将值注入，然后在容器启动命令中引用这些环境变量。

一个重要的特性是，当以卷的形式挂载 ConfigMap 或 Secret 时，如果其内容在集群中被更新，挂载到 Pod 中的文件也会**最终**被同步更新，这为动态重新加载配置提供了可能。然而，如果数据被用作环境变量，或者通过 subPath 方式挂载，它们**不会**自动更新。这种灵活性使得 Kubernetes 能够同时兼容传统应用和现代云原生应用的配置管理模式，极大地降低了应用迁移的门槛。

#### 3.1.2 **YAML 示例**

**创建 ConfigMap 和 Secret**

YAML

## 4 configmap.yaml

apiVersion: v1  
kind: ConfigMap  
metadata:  
name: app-config  
data:  
api.url: "[http://my-service.default"](http://my-service.default")  
feature.enabled: "true"  
---  

## 5 secret.yaml

apiVersion: v1  
kind: Secret  
metadata:  
name: db-credentials  
type: Opaque  
stringData: # 使用 stringData 可以避免手动进行 base64 编码  
username: "admin"  
password: "SuperSecretPassword"

**在 Pod 中使用**

YAML

## 6 pod.yaml

apiVersion: v1  
kind: Pod  
metadata:  
name: my-app-pod  
spec:  
containers:  

- name: my-app-container  
image: busybox  
command:  
env:  
- name: API_URL # 作为环境变量注入  
valueFrom:  
configMapKeyRef:  
name: app-config  
key: api.url  
volumeMounts:  
- name: db-creds-volume # 作为文件挂载  
mountPath: /etc/db-creds  
readOnly: true  
volumes:  
- name: db-creds-volume  
secret:  
secretName: db-credentials

### 6.1 **10. PersistentVolume (PV) & PersistentVolumeClaim (PVC) (持久卷与持久卷声明)**

**电梯演讲**：PersistentVolume (PV) 和 PersistentVolumeClaim (PVC) 将存储的管理与使用解耦。集群管理员负责提供存储资源（PV），而应用开发者则通过 PVC 来申请使用这些存储，无需关心底层的具体实现。这使得 Kubernetes 中的数据持久化变得抽象、可移植且易于管理。

#### 6.1.1 **深度解析**

存储抽象层  
在 Kubernetes 中，计算资源（Pod）的生命周期是短暂的，但许多应用（如数据库）需要持久化的数据存储，其生命周期必须独立于 Pod。PV 和 PVC 子系统正是为此设计的 API，它将存储的提供与消费分离开来。

- **PersistentVolume (PV)**：是集群中的一块存储，由管理员手动配置（静态供应），或由 StorageClass 动态创建（动态供应）。PV 是集群级别的资源，就像 Node 一样，它包含了存储实现的细节，如 NFS 服务器地址、云存储的卷 ID 等。
- **PersistentVolumeClaim (PVC)**：是用户（或应用）对存储的请求。它类似于 Pod，Pod 消耗 Node 的 CPU 和内存资源，而 PVC 消耗 PV 的存储资源。PVC 中定义了所需的存储容量、访问模式（如 ReadWriteOnce、ReadOnlyMany）等。

存储生命周期  
PV 和 PVC 的交互遵循一个清晰的生命周期：

1. **供应 (Provisioning)**：
    - **静态供应**：管理员预先创建好一批 PV。
    - **动态供应**：当用户创建的 PVC 无法匹配到任何现有的 PV 时，如果该 PVC 指定了一个 StorageClass，Kubernetes 可以自动调用该 StorageClass 对应的存储插件来创建一个新的 PV，并与该 PVC 绑定。这是目前最常用和推荐的方式。
2. **绑定 (Binding)**：控制平面中的控制器会持续寻找未绑定的 PVC，并尝试为其匹配一个合适的 PV。一旦匹配成功，PV 和 PVC 就被一对一地绑定在一起。
3. **使用 (Using)**：Pod 在其 volumes 定义中引用 PVC 的名称，从而将该 PVC 绑定的 PV 挂载到容器中。
4. **回收 (Reclaiming)**：当用户删除 PVC 后，绑定的 PV 会被释放。此时，PV 的**回收策略 (persistentVolumeReclaimPolicy)** 决定了其后续行为：
    - Retain：保留 PV 和其上的数据。管理员需要手动清理数据和删除 PV。这是数据安全性的默认保障。
    - Delete：删除 PV 以及底层外部存储中的数据（如云硬盘）。动态供应的 PV 通常默认为此策略。
    - Recycle (已废弃)：清空卷上的数据，使其可以被新的 PVC 重新使用。

StorageClass  
StorageClass 为管理员提供了一种描述他们所提供的存储 " 类别 " 的方法。不同的类别可以映射到不同的服务质量等级、备份策略或由管理员定义的任意策略。用户只需在 PVC 中指定 storageClassName，即可申请特定类别的存储，而无需了解其背后的复杂实现。  
这种 PV/PVC/StorageClass 的三层模型是 " 关注点分离 " 原则在基础设施领域的绝佳实践。它为集群管理员和应用开发者划分了清晰的职责边界：管理员负责定义和管理存储基础设施（通过 StorageClass 和静态 PV），而开发者只负责声明其应用所需的存储规格（通过 PVC）。这种解耦使得应用清单（YAML 文件）具有极高的可移植性，可以无缝迁移到任何提供了相同 StorageClass 的 Kubernetes 集群中。

#### 6.1.2 **YAML 示例**

**StorageClass, PVC 和使用它的 Pod**

YAML

## 7 StorageClass (由管理员定义)

apiVersion: storage.k8s.io/v1  
kind: StorageClass  
metadata:  
name: standard-ssd  
provisioner: kubernetes.io/aws-ebs # 示例：使用 AWS EBS 存储插件  
parameters:  
type: gp2  
reclaimPolicy: Delete  
---  

## 8 PersistentVolumeClaim (由开发者创建)

apiVersion: v1  
kind: PersistentVolumeClaim  
metadata:  
name: my-app-pvc  
spec:  
storageClassName: standard-ssd  
accessModes:  

- ReadWriteOnce # 该卷只能被单个节点读写挂载  
resources:  
requests:  
storage: 10Gi  

---  

## 9 Pod (使用 PVC)

apiVersion: v1  
kind: Pod  
metadata:  
name: my-database-pod  
spec:  
containers:  

- name: postgres  
image: postgres  
ports:  
- containerPort: 5432  
volumeMounts:  
- name: postgres-storage  
mountPath: /var/lib/postgresql/data  
volumes:  
- name: postgres-storage  
persistentVolumeClaim:  
claimName: my-app-pvc

### 9.1 **11. Ingress (入口)**

**电梯演讲**：Ingress 是一个管理集群外部 HTTP 和 HTTPS 流量访问内部服务的 API 对象。它扮演着智能路由器的角色，允许您根据请求的主机名或 URL 路径，将流量从单一入口点分发到不同的服务。

#### 9.1.1 **深度解析**

七层路由  
虽然 Service 的 NodePort 和 LoadBalancer 类型可以在网络模型的第四层（TCP/UDP）暴露服务，但它们的功能相对简单。Ingress 则工作在第七层（HTTP/HTTPS），提供了更丰富、更灵活的路由能力。  
Ingress Controller  
与 Kubernetes 中的许多其他概念一样，Ingress 资源本身只是一份声明路由规则的配置清单。要让这些规则生效，集群中必须运行一个 Ingress Controller。Ingress Controller 是一个独立的程序，它会持续监视 Kubernetes API 中 Ingress 资源的变化，并根据这些规则来配置一个负载均衡器或反向代理（如 NGINX、Traefik、HAProxy 等）。  
这种设计再次体现了 Kubernetes 的可插拔架构。Kubernetes 定义了标准的 Ingress API，但将具体的实现细节委托给了社区和厂商。这催生了一个丰富的 Ingress Controller 生态系统，用户可以根据性能、功能或云平台集成等需求选择最适合自己的实现。这也推动了更具表现力和标准化的下一代入口 API——Gateway API 的发展。

核心功能  
Ingress 的主要功能包括：

- **基于主机名的虚拟托管 (Host-based Routing)**：可以将不同域名（例如 foo.example.com 和 bar.example.com）的流量路由到不同的后端 Service。
- **基于路径的路由 (Path-based Routing)**：可以根据请求的 URL 路径（例如 /api 和 /ui）将流量路由到不同的 Service。
- **TLS/SSL 终止**：Ingress 可以在入口点处理 HTTPS 流量的解密，然后将未加密的流量转发给内部 Service。TLS 证书和私钥通常存储在 Kubernetes Secret 中，并在 Ingress 规则中引用。

#### 9.1.2 **YAML 示例**

以下 Ingress 规则将 myapp.example.com 的流量根据路径分发到两个不同的 Service，并为该域名配置了 TLS：

YAML

apiVersion: networking.k8s.io/v1  
kind: Ingress  
metadata:  
name: my-app-ingress  
annotations:  
nginx.ingress.kubernetes.io/rewrite-target: / # NGINX Ingress Controller 的特定注解  
spec:  
ingressClassName: nginx-example # 指定使用哪个 Ingress Controller  
tls:  

- hosts:  
- myapp.example.com  
secretName: myapp-tls-secret # 引用包含 TLS 证书的 Secret  
rules:  
- host: myapp.example.com  
http:  
paths:  
- path: /api  
pathType: Prefix  
backend:  
service:  
name: api-service  
port:  
number: 8080  
- path: /  
pathType: Prefix  
backend:  
service:  
name: frontend-service  
port:  
number: 80

### 9.2 **12. Helm (包管理器)**

**电梯演讲**：Helm 是 Kubernetes 的包管理器。它允许您查找、分享和使用被称为 "Chart" 的预打包应用。通过一个简单的命令，Helm 就可以安装一个复杂的应用（如数据库），包括其所有的 Deployment、Service 和 ConfigMap，使得应用管理变得可重复且简单。

#### 9.2.1 **深度解析**

Kubernetes 的 "apt/yum"  
对于一个复杂的应用（例如 GitLab 或 WordPress），可能需要管理数十个相互关联的 YAML 文件。手动管理这些文件的依赖关系、配置和版本，尤其是在多个环境中，是一项极其繁琐且容易出错的任务。Helm 正是为了解决这一 "Day 2" 运维难题而生。它将管理的单元从单个的 Kubernetes 资源提升到了整个  
**应用**的层面。

核心概念  
Helm 的生态系统围绕几个核心概念构建：

- **Chart**：一个 Helm Chart 是一个描述 Kubernetes 应用的打包格式。它是一个包含了模板化的 YAML 文件、默认配置文件（values.yaml）和 Chart 元数据（Chart.yaml）的目录结构。
- **Repository**：一个用于存储和分享 Chart 的 HTTP 服务器。公共的 Chart 仓库（如 Artifact Hub）汇集了大量由社区维护的流行应用的 Chart。
- **Release**：一个 Chart 在 Kubernetes 集群中部署的实例。同一个 Chart 可以用不同的配置在同一个集群中安装多次，每次安装都会创建一个新的 Release。
- **Values**：Helm 的强大之处在于其模板化能力。Chart 中的 Kubernetes manifest 文件使用 Go 模板语言编写。用户可以通过提供一个自定义的 values.yaml 文件或在命令行中通过 --set 参数来覆盖 Chart 中的默认值，从而在不修改 Chart 源码的情况下，为不同环境定制化部署（例如，更改镜像标签、副本数、资源限制等）24。

常用命令  
Helm 的命令行工具提供了一整套管理应用生命周期的命令 24：

- helm repo add <name> <url>：添加一个新的 Chart 仓库。
- helm search repo <keyword>：在已添加的仓库中搜索 Chart。
- helm install <release-name> <chart-name>：安装一个 Chart。
- helm upgrade <release-name> <chart-name>：升级一个已部署的 Release。
- helm rollback <release-name> <revision>：回滚到一个历史版本。
- helm uninstall <release-name>：卸载一个 Release。
- helm list：列出所有已部署的 Release。

Helm 通过将应用的部署和生命周期管理标准化，极大地加速了 Kubernetes 的采用。它不仅解决了复杂应用的配置管理问题，还催生了一个庞大的可共享应用生态系统，让用户可以轻松地部署和复用经过验证的最佳实践。

---

## 10 **第三阶段：精通 - 驾驭复杂工作负载与自动化**

本阶段将深入探讨用于处理特殊类型工作负载的控制器，包括有状态应用、节点级守护进程和批处理任务。同时，将揭示 Kubernetes 强大的自动化能力和核心设计哲学，这是从 " 使用者 " 转变为 " 精通者 " 的关键一步。

### 10.1 **13. StatefulSet (有状态副本集)**

**电梯演讲**：StatefulSet 是 Kubernetes 为数据库等有状态应用设计的控制器。与 Deployment 不同，它为每个 Pod 提供了稳定且唯一的网络标识和持久化存储，确保即使 Pod 被重启或重新调度，其身份和数据也能保持不变。

#### 10.1.1 **深度解析**

有状态与无状态的对比  
理解 StatefulSet 的关键在于首先理解它与 Deployment 的根本区别。Deployment 管理的 Pod 是可互换的、匿名的 " 牛 "（cattle），而 StatefulSet 管理的 Pod 是独一无二的、有身份的 " 宠物 "（pets）9。对于数据库集群、消息队列等应用，每个实例的身份和数据都是至关重要的，不能随意替换。  
StatefulSet 的核心保证  
StatefulSet 为其管理的 Pod 提供了三大核心保证，这三大保证是 Deployment 所没有的 26：

1. **稳定、唯一的网络标识 (Stable, Unique Network Identifiers)**：StatefulSet 中的每个 Pod 都会获得一个基于其序号的、可预测的名称（例如 web-0, web-1, web-2）。当与一个 " 无头服务 "（Headless Service）配合使用时，每个 Pod 还会获得一个稳定且唯一的 DNS 主机名（例如 web-0.nginx.my-namespace.svc.cluster.local）。这个网络身份会伴随 Pod 的整个生命周期，即使它被重新调度到其他节点，其主机名也不会改变。
2. **稳定、持久的存储 (Stable, Persistent Storage)**：通过在 StatefulSet 定义中的 volumeClaimTemplates 字段，可以为每个 Pod 自动创建一个对应的 PersistentVolumeClaim。这个 PVC 的名称也与 Pod 的序号绑定（例如 data-web-0）。当 Pod 发生故障并被重建时，新的 Pod 会自动重新挂载回属于它自己的那个 PVC，从而保证了数据的持久性和连续性。
3. **有序、优雅的部署与伸缩 (Ordered, Graceful Deployment and Scaling)**：StatefulSet 对 Pod 的操作是严格有序的。
    - **部署/扩容**：Pod 会按照序号从小到大（0, 1, 2,...）的顺序逐个创建。只有当第 N 个 Pod 达到 Running 和 Ready 状态后，第 N+1 个 Pod 才会被创建。
    - **删除/缩容**：Pod 会按照序号从大到小（..., 2, 1, 0）的顺序逐个删除。
    - 更新：更新操作也是从大到小的顺序进行。  
        这种有序性对于需要按顺序启动和关闭以建立集群仲裁（quorum）的分布式应用至关重要。

|特性|Deployment|StatefulSet|适用场景|
|---|---|---|---|
|**Pod 身份**|匿名，可互换|稳定，唯一 (e.g., web-0)|**StatefulSet**: 数据库 (MySQL, PostgreSQL), 消息队列 (Kafka, RabbitMQ), 分布式协调服务 (ZooKeeper, etcd)|
|**网络**|共享一个 Service IP|每个 Pod 有独立的、稳定的 DNS 主机名|**Deployment**: Web 服务器, 无状态 API, 缓存服务|
|**存储**|共享同一个 PVC|每个 Pod 有自己独立的 PVC||
|**伸缩/更新**|并行，快速，无序|串行，有序，逐个进行||

#### 10.1.2 **YAML 示例**

以下示例展示了一个 StatefulSet，它部署了一个 3 节点的 NGINX 应用，并为其配置了 Headless Service 和持久化存储：

YAML

## 11 Headless Service for Network Identity

apiVersion: v1  
kind: Service  
metadata:  
name: nginx  
labels:  
app: nginx  
spec:  
ports:  

- port: 80  
name: web  
clusterIP: None # 关键：设置为 None 使其成为 Headless Service  
selector:  
app: nginx  

---  

## 12 StatefulSet

apiVersion: apps/v1  
kind: StatefulSet  
metadata:  
name: web  
spec:  
serviceName: "nginx" # 必须与 Headless Service 的名称匹配  
replicas: 3  
selector:  
matchLabels:  
app: nginx  
template:  
metadata:  
labels:  
app: nginx  
spec:  
containers:  

- name: nginx  
image: registry.k8s.io/nginx-slim:0.24  
ports:  
- containerPort: 80  
name: web  
volumeMounts:  
- name: www  
mountPath: /usr/share/nginx/html  
volumeClaimTemplates: # 为每个 Pod 创建 PVC 的模板  
- metadata:  
name: www  
spec:  
accessModes:  
storageClassName: "my-storage-class"  
resources:  
requests:  
storage: 1Gi

### 12.1 **14. DaemonSet (守护进程集)**

**电梯演讲**：DaemonSet 确保在集群中的所有（或部分）节点上都运行一个指定的 Pod 副本。它是部署节点级代理（如日志收集、监控或存储守护进程）的理想选择。

#### 12.1.1 **深度解析**

每节点一个 Pod  
DaemonSet 的核心功能是保证在满足条件的每个节点上都运行且只运行一个 Pod 的副本。当有新节点加入集群时，如果该节点符合 DaemonSet 的调度要求，DaemonSet 控制器会自动在该节点上创建一个 Pod。相反，当节点从集群中移除时，对应的 Pod 会被自动回收。  
典型用例  
DaemonSet 非常适合部署那些需要在每个节点上运行以提供底层基础设施或辅助功能的服务 29：

- **日志收集**：在每个节点上运行一个如 Fluentd 或 Logstash 的代理，以收集该节点上所有容器的日志。
- **节点监控**：在每个节点上运行一个如 Prometheus Node Exporter 或 Datadog Agent 的代理，以采集节点的性能指标。
- **集群存储**：在每个节点上运行一个存储守护进程，如 GlusterFS 或 Ceph，以提供分布式存储能力。
- **网络插件**：许多 CNI 网络插件（如 Calico、Flannel）本身就是通过 DaemonSet 部署到每个节点上的。

调度机制  
DaemonSet 的 Pod 调度是由 DaemonSet 控制器负责的，而不是默认的 Kubernetes 调度器（kube-scheduler）。控制器会为每个目标节点创建一个 Pod，并直接在该 Pod 的规约中设置 .spec.nodeName，将其绑定到特定节点。为了确保这些关键的守护进程能够在各种节点条件下运行（例如，在节点被标记为 unschedulable 时），DaemonSet 控制器会自动为其 Pod 添加必要的容忍（Tolerations）29。  
DaemonSet 将 Kubernetes 的声明式模型扩展到了节点级别，将节点本身视为一个需要被管理的资源集合。过去需要通过配置管理工具（如 Ansible、Puppet）在每台机器上手动安装和维护的系统级代理，现在可以通过一个简单的 YAML 文件，以云原生的方式进行全自动化的生命周期管理。这极大地简化了集群附加组件（如网络、存储、可观测性）的部署和运维。

#### 12.1.2 **YAML 示例**

以下是一个部署 Fluentd 日志收集代理的 DaemonSet 示例：

YAML

apiVersion: apps/v1  
kind: DaemonSet  
metadata:  
name: fluentd-elasticsearch  
namespace: kube-system  
labels:  
k8s-app: fluentd-logging  
spec:  
selector:  
matchLabels:  
name: fluentd-elasticsearch  
template:  
metadata:  
labels:  
name: fluentd-elasticsearch  
spec:  
tolerations:  

- key: node-role.kubernetes.io/control-plane  
operator: Exists  
effect: NoSchedule  
containers:  
- name: fluentd-elasticsearch  
image: quay.io/fluentd_elasticsearch/fluentd:v5.0.1  
resources:  
limits:  
memory: 200Mi  
requests:  
cpu: 100m  
memory: 200Mi  
volumeMounts:  
- name: varlog  
mountPath: /var/log  
volumes:  
- name: varlog  
hostPath: # 使用 hostPath 访问节点的文件系统  
path: /var/log

注意，DaemonSet 的 spec 中没有 replicas 字段，因为副本数是由符合条件的节点数决定的。

### 12.2 **15. Job & CronJob (任务与定时任务)**

**电梯演讲**：Job 和 CronJob 用于管理那些会运行至完成的任务。Job 负责运行一个一次性的 Pod 直到其成功结束，非常适合数据迁移等单次操作。CronJob 则是一个 Job 的调度器，它按照预定的周期（如每日备份或每周报告）重复运行 Job。

#### 12.2.1 **深度解析**

运行至完成的工作负载  
与 Deployment 或 StatefulSet 这类旨在永久运行服务的控制器不同，Job 的目标是创建一个或多个 Pod，并确保其中指定数量的 Pod 成功执行并终止。一旦达到预期的成功完成次数，Job 就宣告完成。  
Job  
Job 适用于一次性的、并行的批处理任务。其 spec 中的关键字段包括：

- completions：Job 成功完成所需的 Pod 数量。
- parallelism：允许并行运行的 Pod 数量。
- backoffLimit：在将 Job 标记为失败之前，允许的 Pod 失败重试次数。

CronJob  
CronJob 是在 Job 之上构建的更高级别控制器，它根据一个 cron 格式的时间表来周期性地创建 Job。每个 CronJob 对象就像 Unix crontab 文件中的一行。

其 spec 中的关键字段包括：

- schedule：定义任务执行周期的 Cron 表达式，例如 "0 5 * * *" 表示每天早上 5 点。
- jobTemplate：定义了每次调度时要创建的 Job 的模板。
- concurrencyPolicy：定义如何处理并发的 Job。可以是 Allow（允许，默认）、Forbid（禁止，如果上一个 Job 未完成则跳过本次执行）或 Replace（替换，用新的 Job 替换正在运行的旧 Job）30。
- successfulJobsHistoryLimit 和 failedJobsHistoryLimit：定义了要保留的已完成和已失败的 Job 历史记录数量，便于审计和调试。

Job 和 CronJob 将批处理和定时任务作为一等公民整合到了 Kubernetes 平台中。这使得企业可以在同一个集群上统一管理和调度其在线服务与离线计算任务，打破了传统架构中不同类型工作负载的资源孤岛，从而提高了资源利用率并简化了运维模型。

#### 12.2.2 **YAML 示例**

**一个简单的 Job**

YAML

apiVersion: batch/v1  
kind: Job  
metadata:  
name: pi-calculation  
spec:  
template:  
spec:  
containers:  

- name: pi  
image: perl:5.34.0  
command: ["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]  
restartPolicy: Never # Job 的 Pod 通常设置为 Never 或 OnFailure  
backoffLimit: 4

**一个 CronJob，每分钟执行一次**

YAML

apiVersion: batch/v1  
kind: CronJob  
metadata:  
name: hello  
spec:  
schedule: "*/1 * * * *"  
jobTemplate:  
spec:  
template:  
spec:  
containers:  

- name: hello  
image: busybox:1.28  
imagePullPolicy: IfNotPresent  
command:  
- /bin/sh  
- -c  
- date; echo "Hello from the Kubernetes cluster"  
restartPolicy: OnFailure

### 12.3 **16. Horizontal Pod Autoscaler (HPA) (水平 Pod 自动伸缩器)**

**电梯演讲**：Horizontal Pod Autoscaler (HPA) 根据负载自动增加或减少应用的 Pod 数量。您只需设定一个目标，比如 " 保持平均 CPU 使用率在 50%"，HPA 就会动态调整 Deployment 的副本数以达到该目标，从而确保应用的性能和成本效益。

#### 12.3.1 **深度解析**

弹性伸缩  
HPA 是 Kubernetes 实现应用弹性能力的核心组件。它通过水平伸缩（即改变 Pod 副本的数量）来应对变化的负载，这与垂直伸缩（改变单个 Pod 的资源分配）相对应。  
工作原理  
HPA 的工作机制是一个经典的控制循环：

1. **数据采集**：HPA 控制器通过 Metrics API 定期（默认为 15 秒）从一个名为 Metrics Server 的组件获取 Pod 的资源使用情况度量。因此，要使用 HPA，集群中必须首先安装 Metrics Server。
2. **计算**：控制器将当前度量值与 HPA 中定义的目标值进行比较。
3. **执行**：根据比较结果，控制器计算出所需的理想副本数，然后更新其目标资源（如 Deployment 或 StatefulSet）的 .spec.replicas 字段。之后，Deployment 或 StatefulSet 的控制器会负责实际创建或删除 Pod，以达到新的副本数。

伸缩指标  
HPA 的能力远不止于 CPU 和内存。它可以基于多种类型的指标进行伸缩 32：

- **资源指标 (Resource Metrics)**：最常见的，如 Pod 的平均 CPU 使用率或平均内存使用量。
- **自定义指标 (Custom Metrics)**：与 Kubernetes 对象相关的任意指标，例如 " 每秒请求数 "（通常由 Ingress Controller 提供）或 " 队列中的任务数 "。
- **外部指标 (External Metrics)**：来自集群外部系统的指标，例如云服务提供商的消息队列（如 AWS SQS）的队列长度。这使得应用可以根据业务指标（而不仅仅是资源指标）进行伸缩。

HPA 是 Kubernetes 自愈和自动化特性的体现。它使应用能够自动适应波动的用户需求，无需人工干预。在没有自动伸缩的情况下，运维团队必须为峰值负载预留资源，这在大部分时间里造成了巨大的成本浪费。HPA 则实现了真正的云原生弹性，让应用可以随需求 " 呼吸 "，在保证服务质量的同时，最大限度地提高资源利用率和成本效益。

#### 12.3.2 **YAML 示例**

以下 HPA 会监控名为 php-apache 的 Deployment，并调整其副本数（在 1 到 10 之间），以将所有 Pod 的平均 CPU 使用率维持在 50%：

YAML

apiVersion: autoscaling/v2  
kind: HorizontalPodAutoscaler  
metadata:  
name: php-apache  
spec:  
scaleTargetRef:  
apiVersion: apps/v1  
kind: Deployment  
name: php-apache  
minReplicas: 1  
maxReplicas: 10  
metrics:  

- type: Resource  
resource:  
name: cpu  
target:  
type: Utilization  
averageUtilization: 50

### 12.4 **17. Control Loop (Reconciliation Loop) (控制循环/调谐循环)**

**电梯演讲**：控制循环是 Kubernetes 的核心设计模式。这是一个简单而强大的理念：控制器持续地观察集群的 " 当前状态 "，将其与您定义的 " 期望状态 " 进行比较，并采取行动使两者匹配。这是 Kubernetes 所有自愈和自动化功能的底层引擎。

#### 12.4.1 **深度解析**

核心设计哲学  
在机器人学和自动化领域，控制循环是一个永不终止的、用于调节系统状态的循环。Kubernetes 将这一概念作为其架构的基石。整个系统可以被看作是由许多个独立的控制循环共同协作，来驱动集群状态向用户定义的期望状态收敛。  
**期望状态 vs. 当前状态**

- **期望状态 (Desired State)**：由用户通过 YAML 文件中的 .spec 字段来定义。例如，replicas: 3 就是一个期望状态。
- **当前状态 (Current State)**：集群中资源的实际情况，例如当前实际运行的 Pod 数量。这个状态通常反映在资源的 .status 字段中。

观察 - 比较 - 行动 (Observe-Diff-Act)  
每个控制器都执行一个调谐循环，这个循环可以分解为三个步骤 35：

1. **观察 (Observe)**：控制器通过 API Server 监视（watch）它所关心的资源。
2. **比较 (Diff)**：控制器比较资源的期望状态（.spec）和当前状态（.status）。
3. **行动 (Act)**：如果两者之间存在差异，控制器会采取行动来消除这个差异。行动的方式通常是向 API Server 发出请求，以创建、更新或删除其他资源。

以 ReplicaSet 控制器为例：其期望状态是 replicas: 3，它观察到当前只有 2 个正在运行的 Pod。比较后发现差异为 -1，于是它会向 API Server 发出一个创建新 Pod 的请求。

组合的力量  
Kubernetes 的强大之处在于，它不是一个单一的、庞大的控制循环，而是由许多个小型的、专注的、独立的控制循环组合而成。例如，Deployment 控制器并不直接创建 Pod，它只负责创建和管理 ReplicaSet。而 ReplicaSet 控制器则负责观察 ReplicaSet 并管理 Pod。这些控制器之间通过 API Server 中对象的改变进行间接通信和协作。  
这种去中心化、事件驱动的架构具有极高的弹性和可扩展性。如果某个控制器出现故障，系统的其他部分仍然可以正常工作。更重要的是，它使得扩展 Kubernetes 变得异常简单：要为 Kubernetes 添加新功能，只需编写一个新的控制器来管理一种新的资源类型。这正是下一阶段将要讨论的 Operator 模式的基石。控制循环是理解 Kubernetes 一切行为的 " 第一性原理 "。

---

## 13 **第四阶段：架构深潜 - 理解集群的 " 大脑 " 和 " 神经 "**

在掌握了如何使用 Kubernetes 的各种资源对象之后，本阶段将深入其内部，揭示支撑整个集群运行的核心组件。理解控制平面（大脑）和节点代理（神经）的工作原理，是进行高级故障排查、性能优化和架构设计的前提。

### 13.1 **18. Control Plane (控制平面)**

**电梯演讲**：控制平面是 Kubernetes 集群的大脑。它是一组核心服务的集合，负责做出全局性的决策，如调度应用、检测和响应故障，并持续维护整个集群达到您所期望的状态。

#### 13.1.1 **深度解析**

集群的大脑  
控制平面是 Kubernetes 的中央神经系统，负责管理和协调集群的所有活动。它不直接运行用户应用容器（这些容器运行在工作节点上），而是运行着使集群能够正常工作的核心进程。控制平面的主要任务就是运行一系列的控制循环，持续地将集群的当前状态调整为用户定义的期望状态。  
核心组件  
一个典型的 Kubernetes 控制平面由以下几个关键组件构成 7：

- **API Server (kube-apiserver)**：控制平面的统一入口，处理所有内部和外部的 API 请求。
- **etcd**：存储整个集群所有状态的分布式键值数据库，是集群的 " 真理之源 "。
- **Scheduler (kube-scheduler)**：负责决定新创建的 Pod 应该被调度到哪个 Node 上运行。
- **Controller Manager (kube-controller-manager)**：运行所有核心的控制器，如 Deployment 控制器、Node 控制器等。
- **Cloud Controller Manager (cloud-controller-manager)** (可选)：在云环境中运行时，此组件负责与云提供商的 API 交互，管理云相关的资源，如负载均衡器、存储卷等。

在生产环境中，为了实现高可用性，这些控制平面组件通常会冗余部署在多个主节点（master node）上。

大脑与肌肉的分离  
Kubernetes 的架构清晰地体现了 " 大脑 "（控制平面）与 " 肌肉 "（工作节点）的分离。用户通过 kubectl 向控制平面的 API Server 提交一个 Deployment 的 YAML 文件。控制平面的组件协同处理这个请求：Controller Manager 创建 ReplicaSet，Scheduler 为 Pod 选择最佳节点，所有这些决策和状态变更都被记录在 etcd 中。而分配到任务的工作节点上的 kubelet 则是 " 肌肉 "，它从 API Server 接收指令，然后调用容器运行时来实际执行创建容器的任务。kubelet 只执行，不决策。这种架构分离使得集群可以大规模扩展：一个相对小规模的控制平面可以管理成千上万个工作节点。

### 13.2 **19. API Server (kube-apiserver)**

**电梯演讲**：API Server 是 Kubernetes 控制平面的前门和中央枢纽。它以 REST API 的形式暴露了 Kubernetes 的所有功能。无论是 kubectl、控制器还是其他工具，所有对集群的操作都必须通过 API Server，使其成为所有通信和状态管理的中心。

#### 13.2.1 **深度解析**

中央枢纽  
kube-apiserver 是控制平面中最重要的组件，也是唯一直接与 etcd 交互的组件。所有其他组件，包括用户、控制器和节点上的  
kubelet，都通过 API Server 来读取和修改集群的状态。

主要职责  
API Server 的核心功能包括：

1. **提供 API**：通过 HTTP 提供了一套完整的、版本化的 RESTful API，用于对 Kubernetes 中的所有资源对象（Pod, Service, Deployment 等）进行增删改查（CRUD）操作。
2. **请求处理**：它负责接收所有 API 请求，并经过一个标准化的处理流程，包括：
    - **认证 (Authentication)**：验证请求者的身份。
    - **授权 (Authorization)**：检查请求者是否有权限执行该操作。
    - **准入控制 (Admission Control)**：在对象被持久化到 etcd 之前，执行一系列的校验和（可选的）修改。
3. **持久化状态**：将经过验证和准入控制的对象状态写入 etcd 进行持久化存储。
4. **提供 Watch 机制**：API Server 提供了一个高效的 watch 接口。客户端（如控制器）可以建立一个长连接来 " 订阅 " 某个或某类资源的变更事件。一旦资源发生变化，API Server 会立即将事件推送给客户端。这个机制是 Kubernetes 事件驱动架构的基石，它避免了所有组件都去轮询 API Server，极大地提高了系统的效率和响应速度。

API Server 的设计是 Kubernetes 声明式、控制器模式能够成功的关键。它作为一个无状态、可水平扩展的 RESTful 前端，为后端的 etcd 提供了一个一致、安全、可观察的访问层。所有组件都围绕这个中心 API 进行解耦和协作，这使得整个系统具有极高的可扩展性和灵活性。要为 Kubernetes 添加新功能，通常就是通过聚合 API 或 CRD 的方式在 API Server 中注册新的 API 端点，然后编写一个与这些新端点交互的控制器即可。

### 13.3 **20. etcd**

**电梯演讲**：etcd 是整个 Kubernetes 集群的记忆和单一事实来源。它是一个一致性、高可用的分布式键值存储系统，负责可靠地保存集群的所有数据，包括每一个资源的配置、当前状态和期望状态。

#### 13.3.1 **深度解析**

真理之源  
etcd 是 Kubernetes 控制平面的核心数据存储。集群中所有对象——Pod 的定义、Service 的配置、Secret 的内容、节点的健康状态等等——都被序列化后存储在 etcd 中。它是集群状态的唯一权威来源。除了  
etcd，控制平面的其他所有组件都是无状态的，它们的状态信息都从 etcd 读取，并将更新写回 etcd。

分布式与一致性  
etcd 本身就是一个复杂的分布式系统。为了保证高可用和数据一致性，它通常以一个由 3 个或 5 个节点组成的集群模式运行。etcd 使用 Raft 一致性算法来确保：

- **强一致性**：一旦一个写操作被确认，集群中的任何一个节点都能读到这个最新的值。这对于依赖准确状态信息来做决策的控制器至关重要。
- **容错性**：在一个 N 个节点的 etcd 集群中，只要有超过一半（(N/2)+1）的节点存活，集群就可以正常读写。例如，一个 3 节点的集群可以容忍 1 个节点失败。

对 Kubernetes 的重要性  
Kubernetes 对其后端存储有非常苛刻的要求：需要强一致性、高可用性以及高效的 watch 机制。etcd 正是为满足这些需求而设计的。

- **备份与恢复**：由于 etcd 存储了整个集群的状态，因此定期备份 etcd 是保障集群免于灾难性故障的最关键的运维任务。丢失了 etcd 的数据，就等于丢失了整个集群的状态。
- **性能瓶颈**：整个 Kubernetes 集群的性能，特别是 API Server 的响应能力，很大程度上受限于底层 etcd 集群的性能。etcd 的磁盘 I/O 延迟是影响集群规模和性能的关键因素。

### 13.4 **21. Scheduler (kube-scheduler)**

**电梯演讲**：Kubernetes Scheduler 是负责为新创建的 Pod 寻找最合适运行节点的组件。它就像一个精密的 " 婚介师 "，首先过滤掉不满足 Pod 运行条件的节点，然后对剩下的候选节点进行打分，最终选择得分最高的节点进行绑定。

#### 13.4.1 **深度解析**

决策者  
Scheduler 的唯一职责就是监视 API Server 中那些 .spec.nodeName 字段为空的新 Pod，并为它们选择一个合适的节点来运行。它只负责决策，不负责实际运行 Pod（那是  
kubelet 的工作）。

两阶段调度过程  
Scheduler 的决策过程主要分为两个阶段 38：

1. **过滤 (Filtering)**：在这个阶段，Scheduler 会遍历集群中的所有节点，并运行一系列 " 断言函数 "（Predicates）来过滤掉不能运行该 Pod 的节点。过滤的条件包括：
    - **资源充足性**：节点的 CPU、内存等资源是否满足 Pod 的 requests。
    - **节点选择器与亲和性**：节点是否匹配 Pod 的 nodeSelector、nodeAffinity 等要求。
    - **污点与容忍**：Pod 是否能容忍节点上的 " 污点 "（Taints）。
    - 卷冲突：节点是否能挂载 Pod 所需的存储卷。  
        经过过滤后，会得到一个可行的节点列表。如果列表为空，Pod 将保持 Pending 状态。
2. **打分 (Scoring)**：在这个阶段，Scheduler 会对所有可行的节点运行一系列 " 优选函数 "（Priorities），为每个节点打分。打分的策略旨在找到 " 最佳 " 节点，而不仅仅是 " 可行 " 的节点。常见的打分策略包括：
    - **最小负载优先**：优先选择资源使用率较低的节点，以实现负载均衡。
    - **镜像本地性优先**：优先选择已经缓存了 Pod 所需容器镜像的节点，以加快启动速度。
    - Pod 亲和性/反亲和性：根据 Pod 之间定义的亲和或互斥关系进行加分或减分。  
        最终，Scheduler 会将 Pod 绑定到得分最高的节点上。

调度框架 (Scheduling Framework)  
现代的 Kubernetes Scheduler 是基于一个可插拔的调度框架构建的。这个框架在调度过程的各个关键点（如 PreFilter, Filter, Score, Bind 等）定义了扩展点，允许开发者编写自定义插件来扩展或替换默认的调度逻辑，以满足特定的业务需求。这种设计的复杂性源于其需要平衡多个有时相互冲突的目标：资源利用率、高可用性、策略合规性等。

### 13.5 **22. kubelet**

**电梯演讲**：kubelet 是运行在每个工作节点上的核心代理。它是控制平面与节点之间的桥梁，负责监视分配到其所在节点的 Pod，并确保这些 Pod 中的容器处于健康运行状态。

#### 13.5.1 **深度解析**

节点代理  
kubelet 是将一台机器转变为 Kubernetes Node 的关键进程。没有  
kubelet，节点就无法加入集群或运行工作负载。

核心职责  
kubelet 的工作可以概括为以下几点 39：

1. **节点注册**：启动时，kubelet 会向 API Server 注册自己，创建一个 Node 对象。
2. **Pod 生命周期管理**：kubelet 持续监视 API Server。当它发现有 Pod 被调度到自己所在的节点时，它会读取该 Pod 的规约（PodSpec）。
3. **与容器运行时交互**：根据 PodSpec 中的容器定义，kubelet 通过 CRI 接口命令容器运行时执行具体操作：拉取镜像、创建并启动容器。
4. **状态报告**：kubelet 会持续地将节点和其上运行的 Pod 的状态报告回 API Server，更新 Node 和 Pod 对象的 .status 字段。
5. **健康检查**：kubelet 负责执行在 PodSpec 中定义的存活探针（Liveness Probes）、就绪探针（Readiness Probes）和启动探针（Startup Probes），以检查容器的健康状况，并根据结果采取行动（如重启容器）。

kubelet 是闭合控制循环的关键环节。控制平面的所有决策，最终都由目标节点上的 kubelet 来执行和落地。它将 API Server 中抽象的、期望的 Pod 对象，转化为节点上实实在在运行的容器进程，从而将 " 期望状态 " 变为 " 当前状态 "。

### 13.6 **23. kube-proxy**

**电梯演讲**：kube-proxy 是运行在每个节点上的网络代理，它是实现 Kubernetes Service 概念的幕后功臣。它监视 Service 和其后端端点的变化，并将这些信息转化为节点上的网络规则，确保发送到 Service 虚拟 IP 的流量能够被正确地路由和负载均衡到后端的 Pod。

#### 13.6.1 **深度解析**

Service 的实现者  
kube-proxy 的核心职责是在网络层面实现 Service 这一抽象。当用户创建一个 Service 时，他们只是在 API Server 中创建了一个对象。  
kube-proxy 负责将这个抽象的对象转化为节点上实际的、可工作的网络转发规则。

工作模式  
kube-proxy 支持多种后端模式来实现这些规则 11：

- **iptables** (默认)：这是最常用且性能良好的模式。kube-proxy 会监视 Service 和 EndpointSlice 对象，然后生成一系列 iptables 规则。这些规则利用 Linux 内核的 netfilter 功能，在内核空间直接对发往 Service ClusterIP 的数据包进行目的地址转换（DNAT），并随机选择一个后端 Pod 的 IP 作为新的目的地。整个过程高效且不经过用户空间。
- **IPVS (IP Virtual Server)**：对于拥有大量 Service 的超大规模集群，IPVS 模式通常能提供比 iptables 更好的性能和更复杂的负载均衡算法。IPVS 也是基于 netfilter 的，但在数据结构上使用哈希表，查找效率更高。
- **userspace** (已废弃)：这是最早的模式，kube-proxy 作为一个用户空间进程实际地代理流量，性能较差，已不推荐使用。

分布式负载均衡  
kube-proxy 的一个重要架构特点是它实现了分布式的服务负载均衡。每个节点上的 kube-proxy 都维护着一套完整的、针对集群中所有 Service 的转发规则。当一个在 Node A 上的 Pod 访问一个 Service 时，流量会被 Node A 上的 iptables/IPVS 规则直接转发到位于 Node B 或 Node C 的后端 Pod，而无需经过任何中央负载均衡器。这种去中心化的模型具有极高的可伸缩性和容错性，避免了集群内部服务间通信的单点瓶颈。

### 13.7 **24. CNI (Container Network Interface)**

**电梯演讲**：CNI，即容器网络接口，是 Kubernetes 用来通过插件模式集成不同网络方案的一套标准。它定义了如何为容器创建网络接口和分配 IP 地址，让您可以根据需求选择 Calico、Flannel 等各种网络插件，以实现特定的网络策略、性能或功能。

#### 13.7.1 **深度解析**

网络标准  
CNI 是由云原生计算基金会（CNCF）托管的一个项目，它为 Linux 容器的网络配置定义了一套简洁的规范和库。Kubernetes 本身并不负责实现 Pod 间的网络通信（特别是跨节点通信），而是将这个复杂的任务委托给了实现了 CNI 接口的网络插件。  
工作流程  
当一个 Pod 被调度到一个节点上后，kubelet 的工作流程大致如下：

1. 调用容器运行时（通过 CRI）为 Pod 创建网络命名空间。
2. 调用已配置的 CNI 插件（一个可执行文件）。
3. CNI 插件负责在 Pod 的网络命名空间内：
    - 创建一个网络接口（通常是 veth pair 的一端）。
    - 调用另一个 IPAM（IP 地址管理）插件为该接口分配一个 IP 地址。
    - 设置必要的路由规则，确保 Pod 可以与集群中的其他 Pod 通信。
4. 插件将分配的 IP 地址等信息返回给 kubelet。

插件生态系统  
CNI 标准的成功在于其极简的接口设计，它只关心 " 连接 " 和 " 断开 " 两个动作。这种简单性催生了一个极其丰富的 CNI 插件生态系统，提供了各种不同的网络实现方案，以满足不同场景的需求：

- **覆盖网络 (Overlay Networks)**：如 Flannel (VXLAN 模式)、Calico (IPIP 模式)，它们通过在节点间创建隧道来封装 Pod 流量，简化了跨主机通信，对底层网络要求低。
- **直接路由 (Direct Routing)**：如 Calico (BGP 模式)，它不使用覆盖网络，而是通过 BGP 协议将 Pod 的路由信息宣告给底层物理网络，性能更高，但对网络基础设施有要求。
- **云厂商集成**：如 AWS VPC CNI，它直接从云平台的 VPC 中为 Pod 分配 IP 地址，使 Pod 成为 VPC 网络中的一等公民，便于与云上其他服务集成。
- **基于 eBPF 的高级网络**：如 Cilium，它利用 eBPF 技术在内核中实现高效的网络、可观测性和安全策略，性能优异且功能强大。

CNI 的可插拔架构是 Kubernetes 能够适应从本地数据中心到公有云等各种异构环境的关键。用户可以根据对性能、安全、功能和运维复杂度的考量，自由选择最适合其业务场景的网络解决方案。

### 13.8 **25. CSI (Container Storage Interface)**

**电梯演讲**：CSI，即容器存储接口，是一套行业标准，它允许 Kubernetes 通过通用的插件模型与任何存储系统集成。存储厂商只需开发一个 "CSI 驱动程序 "，就能让他们的块存储或文件存储系统在任何容器编排平台上使用，为您提供极大的存储选择自由。

#### 13.8.1 **深度解析**

存储标准  
与 CNI 在网络领域的地位类似，CSI 是为容器编排系统（如 Kubernetes）提供统一存储接口的标准。在 CSI 出现之前，对新存储系统的支持需要将驱动代码直接合并到 Kubernetes 的核心代码库中（称为 "in-tree" 驱动）。这种模式开发周期长、维护困难，并且会使 Kubernetes 核心代码变得臃肿。  
CSI 通过定义一套标准的 gRPC API，将存储驱动的实现从 Kubernetes 核心中解耦出来（称为 "out-of-tree" 驱动）。这使得存储厂商可以独立于 Kubernetes 的发布周期来开发、部署和更新他们的驱动。

CSI 驱动的架构  
一个典型的 CSI 驱动由两部分组成 42：

1. **控制器插件 (Controller Plugin)**：通常以 Deployment 或 StatefulSet 的形式部署，在集群中只运行少数几个实例。它负责处理与存储系统控制平面交互的、非节点特定的操作，如：
    - CreateVolume / DeleteVolume (动态供应/删除卷)
    - ControllerPublishVolume / ControllerUnpublishVolume (将卷附加/分离到特定节点)
2. **节点插件 (Node Plugin)**：通过 DaemonSet 部署，在每个工作节点上都运行一个实例。它负责处理节点本地的操作，如：
    - NodeStageVolume (格式化卷并挂载到节点的暂存目录)
    - NodePublishVolume (将卷从暂存目录绑定挂载到 Pod 的目标目录)

Sidecar 容器  
为了进一步简化 CSI 驱动的开发，Kubernetes 社区提供了一系列标准的 " 边车 "（Sidecar）容器，如 external-provisioner、external-attacher、external-resizer 等。这些 Sidecar 容器负责监视 Kubernetes 的 API 对象（如 PVC），并将这些事件翻译成对 CSI 驱动的相应 gRPC 调用。驱动开发者只需专注于实现 CSI 接口中与自己存储系统相关的逻辑，而无需编写与 Kubernetes API 交互的复杂代码。  
CSI 和 CNI 是 Kubernetes 可扩展哲学的双生子。它们都通过定义一个最小化的、稳定的接口，将复杂的、快速变化的外部领域（网络和存储）的实现细节 " 移出 " 核心，从而赋予了 Kubernetes 强大的生命力和适应性。这使得 Kubernetes 能够与几乎所有现存和未来的存储技术无缝集成，真正成为一个通用的计算平台。

---

## 14 **第五阶段：高级主题 - 安全、扩展与生态**

这是学习之旅的最后阶段，重点关注如何保护集群、如何根据业务需求扩展 Kubernetes 的能力，以及如何将其融入更广泛的云原生生态系统以实现全面的可观测性。掌握这些主题，意味着您已准备好在生产环境中构建和维护复杂、安全且可靠的系统。

### 14.1 **26. ServiceAccount (服务账户)**

**电梯演讲**：ServiceAccount 为在 Pod 内部运行的进程提供了一个身份标识。当您的应用需要与 Kubernetes API 交互时（例如，列出其他 Pod），它会使用其 ServiceAccount 的令牌来进行身份验证，从而确保集群内部通信的安全性。

#### 14.1.1 **深度解析**

Pod 的身份  
在 Kubernetes 的世界里，身份分为两类：一类是供人类使用的用户账户 (User Account)，另一类是供 Pod 内进程使用的服务账户 (ServiceAccount)。ServiceAccount 是一个由 Kubernetes API 管理的、特定于命名空间的资源。  
自动挂载与使用  
当创建一个 Pod 时，如果没有明确指定，它会自动关联其所在命名空间中名为 default 的 ServiceAccount。更重要的是，Kubernetes 会自动为该 ServiceAccount 生成一个认证令牌（Token），并将这个令牌连同 CA 证书一起，以 Secret 的形式挂载到 Pod 内部的固定路径 /var/run/secrets/kubernetes.io/serviceaccount/ 下。  
当 Pod 内的应用程序需要与 API Server 通信时，官方的 Kubernetes 客户端库（client-go, client-python 等）会自动查找并使用这个挂载的令牌来构造认证请求头。这样，应用程序就能够以其 ServiceAccount 的身份向 API Server 进行认证。

最小权限原则  
在生产环境中，使用默认的 default ServiceAccount 通常是一个坏习惯，因为它可能被授予了过多的权限。最佳实践是为每个需要访问 API 的应用创建一个专用的 ServiceAccount，然后通过 RBAC（下一节将讨论）为其精确地授予完成其任务所需的最小权限。  
ServiceAccount 是实现集群内自动化和扩展的基础。所有运行在集群内部的控制器和 Operator（它们本身也是运行在 Pod 中）都是通过 ServiceAccount 来获得与 API Server 交互的权限的。例如，一个 Prometheus Operator 需要权限来创建 ServiceMonitor 对象和 Prometheus 实例，这些权限就是通过将其 ServiceAccount 与一个定义了相应权限的 Role/ClusterRole 绑定来实现的。因此，ServiceAccount 和 RBAC 的结合是实现 "Kubernetes on Kubernetes" 扩展模型的基石。

### 14.2 **27. RBAC (Role, ClusterRole, RoleBinding, ClusterRoleBinding)**

**电梯演讲**：RBAC，即基于角色的访问控制，是 Kubernetes 中定义 " 谁能对什么做什么 " 的核心安全机制。您通过 "Role" 来定义一组权限，然后通过 "RoleBinding" 将这个 Role 授予给用户或应用，从而实现最小权限原则。

#### 14.2.1 **深度解析**

授权模型  
RBAC 是 Kubernetes 中标准的授权机制。它的核心思想是将权限（Permissions）与角色（Roles）关联，再将角色赋予主体（Subjects，即用户、用户组或 ServiceAccount）。RBAC 的规则是纯粹累加的，没有 " 拒绝 " 规则。  
四大核心对象  
RBAC 模型由四个核心 API 对象构成 43：

1. **Role**：定义了一组在**特定命名空间内**的权限。一个 Role 包含了一系列规则，每个规则定义了可以对哪些资源（如 pods, services）执行哪些操作（动词，如 get, list, create, delete）。
2. **ClusterRole**：与 Role 类似，也定义了一组权限，但其作用域是**整个集群**。ClusterRole 可以用于：
    - 授权对非命名空间资源（如 nodes, persistentvolumes）的访问。
    - 授权对所有命名空间中同类资源的访问（例如，允许管理员 get pods --all-namespaces）。
    - 授权对非资源性端点（如 /healthz）的访问。
3. **RoleBinding**：将一个 Role 或 ClusterRole 的权限授予一个或多个主体，但其作用范围**仅限于该 RoleBinding 所在的命名空间**。
4. **ClusterRoleBinding**：将一个 ClusterRole 的权限授予一个或多个主体，其作用范围是**整个集群**。

|绑定对象|权限对象|授权范围|示例|
|---|---|---|---|
|RoleBinding|Role|在 RoleBinding 所在的**单一命名空间**内|授予用户 Jane 在 dev 命名空间中读取 Pod 的权限。|
|RoleBinding|ClusterRole|在 RoleBinding 所在的**单一命名空间**内|授予 ServiceAccount monitor 在 prod 命名空间中执行 view ClusterRole 定义的所有权限。|
|ClusterRoleBinding|ClusterRole|**整个集群**（所有命名空间）|授予 cluster-admins 组 cluster-admin ClusterRole 的权限，使其成为集群的超级管理员。|

理解这四种对象及其作用域的组合是正确配置 RBAC 的关键。最常见的混淆点是使用 RoleBinding 来绑定一个 ClusterRole，其结果是该 ClusterRole 中定义的权限仅在该 RoleBinding 的命名空间内生效，这是一种在多个命名空间中复用通用权限定义的有效方式。

#### 14.2.2 **YAML 示例**

**定义一个 Role 并将其绑定给一个用户**

YAML

## 15 创建一个 Role，允许在 "default" 命名空间中读取 Pod

apiVersion: rbac.authorization.k8s.io/v1  
kind: Role  
metadata:  
namespace: default  
name: pod-reader  
rules:  

- apiGroups: [""] # "" 表示核心 API 组  
resources: ["pods"]  
verbs: ["get", "watch", "list"]  

---  

## 16 创建一个 RoleBinding，将 Pod-reader Role 授予用户 "jane"

apiVersion: rbac.authorization.k8s.io/v1  
kind: RoleBinding  
metadata:  
name: read-pods  
namespace: default  
subjects:  

- kind: User  
name: jane  
apiGroup: rbac.authorization.k8s.io  
roleRef:  
kind: Role  
name: pod-reader  
apiGroup: rbac.authorization.k8s.io

### 16.1 **28. NetworkPolicy (网络策略)**

**电梯演讲**：NetworkPolicy 扮演着 Pod 防火墙的角色。默认情况下，集群中所有的 Pod 都可以相互通信，而 NetworkPolicy 允许您创建规则来限制这种流量，例如，确保只有前端 Pod 才能连接到数据库 Pod 的特定端口。

#### 16.1.1 **深度解析**

Pod 间的防火墙  
NetworkPolicy 是 Kubernetes 提供的一种用于实现网络隔离和微服务间访问控制的资源。它允许用户以声明式的方式定义 Pod 之间以及 Pod 与外部网络之间的流量规则。  
CNI 依赖  
与 Ingress 类似，创建 NetworkPolicy 资源本身并不会产生任何效果。集群的网络插件（CNI）必须支持并实现了 NetworkPolicy 的执行。主流的 CNI 插件如 Calico、Cilium、Weave Net 等都支持 NetworkPolicy。  
工作原理  
NetworkPolicy 的核心是 " 默认拒绝 " 和 " 白名单 " 模型。

- **默认行为**：在没有应用任何 NetworkPolicy 的情况下，一个命名空间中的所有 Pod 都是 " 非隔离 " 的，它们可以自由地接收和发送任何流量。
- **隔离行为**：一旦有一个 NetworkPolicy 通过其 podSelector 选中了某个 Pod，该 Pod 在相应的方向（入站 ingress 或出站 egress）上就变成了 " 隔离 " 状态。
- **白名单规则**：对于一个被隔离的 Pod，所有流量默认都是被拒绝的，**除了**那些被 NetworkPolicy 规则明确允许的流量。规则可以基于以下条件来定义允许的流量来源（from）或目的地（to）：
    - podSelector：来自或去往带有特定标签的其他 Pod。
    - namespaceSelector：来自或去往带有特定标签的命名空间中的所有 Pod。
    - ipBlock：来自或去往一个特定的 IP 地址范围（CIDR）44。

NetworkPolicy 将 Kubernetes 的声明式、标签驱动的哲学应用到了网络安全领域。管理员不再需要基于脆弱的、静态的 IP 地址来配置防火墙规则，而是可以根据应用的逻辑组件（通过标签来识别）来声明期望的通信模式。例如，"role=db 的 Pod 只允许接收来自 role=api 的 Pod 的流量 "。这种安全策略与应用定义一起存放在 YAML 文件中，可以随应用在任何支持 NetworkPolicy 的集群中迁移和部署，实现了真正的 " 安全即代码 "。

#### 16.1.2 **YAML 示例**

以下 NetworkPolicy 隔离了所有 role: db 的 Pod，只允许来自 role: frontend 的 Pod 访问其 6379 端口：

YAML

apiVersion: networking.k8s.io/v1  
kind: NetworkPolicy  
metadata:  
name: db-allow-frontend  
spec:  
podSelector:  
matchLabels:  
role: db  
policyTypes:  

- Ingress  
ingress:  
- from:  
- podSelector:  
matchLabels:  
role: frontend  
ports:  
- protocol: TCP  
port: 6379

### 16.2 **29. CRD (Custom Resource Definition) & Operator (自定义资源定义与操作器)**

**电梯演讲**：CRD 允许您通过自定义资源来扩展 Kubernetes API，让 Kubernetes 能够理解您的特定应用。而 Operator 模式则通过一个自定义控制器将这些资源 " 激活 "，这个控制器封装了运维专家的知识，能够自动化管理这些自定义资源，使您的应用在集群上实现自我管理。

#### 16.2.1 **深度解析**

扩展 Kubernetes API  
Custom Resource Definition (CRD) 是一种强大的机制，它允许用户在不修改 Kubernetes 源代码的情况下，向集群中添加新的、自定义的 API 资源类型。当您创建一个 CRD 对象时，API Server 会自动为这种新资源生成一个 RESTful 的 API 端点。之后，您就可以像操作内置资源（如 Pod）一样，使用  
kubectl 来创建、读取、更新和删除这种自定义资源（Custom Resource, CR）的实例了。

Operator 模式  
仅仅创建一个 CRD 只能让 Kubernetes 存储和检索您的自定义数据。要让这些数据变得 " 智能 "，就需要引入 Operator 模式。Operator 是一个封装了特定应用领域运维知识的自定义控制器。它由两部分组成：

1. **CRD**：定义了应用的声明式 API。例如，一个 EtcdCluster CRD 可能包含 spec.version 和 spec.size 字段。
2. **自定义控制器**：一个运行在集群中的 Pod，它会持续监视其管理的 CR。

这个自定义控制器会执行一个调谐循环，将 CR 中定义的期望状态（如 size: 3）与实际状态进行比较。如果发现不一致（例如，实际只运行了 2 个 etcd Pod），控制器就会采取行动（创建第 3 个 etcd Pod）来修复这种差异。Operator 可以处理比简单伸缩复杂得多的任务，如应用的安装、升级、故障恢复、备份等。

CRD 和 Operator 模式是 Kubernetes 可扩展性的终极体现。它将 Kubernetes 从一个单纯的容器编排器，转变为一个通用的、用于构建任何声明式 API 驱动控制平面的框架。通过编写 Operator，您可以将复杂应用的运维逻辑代码化，并将其作为 Kubernetes 的一部分来运行。这催生了一个庞大的 Operator 生态系统，涵盖了数据库、消息队列、监控系统等几乎所有类型的软件，使得在 Kubernetes 上管理这些复杂应用变得像管理内置资源一样简单。

### 16.3 **30. Prometheus (普罗米修斯)**

**电梯演讲**：Prometheus 是 Kubernetes 生态中事实上的监控标准。它是一个开源的监控和告警工具包，通过从您的应用和集群组件中 " 拉取 " 指标，将其存储为时序数据，并提供强大的查询语言和告警系统，帮助您深入了解系统的健康状况和性能。

#### 16.3.1 **深度解析**

拉取模型 (Pull-based Model)  
Prometheus 的核心架构是基于拉取模型的。它会定期地通过 HTTP 协议访问被监控目标（称为 target）暴露的 metrics 端点，并抓取（scrape）上面的指标数据。这种模型相比于推送模型（由被监控端主动上报数据）有几个优势，尤其是在动态环境中：集中控制、易于发现目标、对被监控端侵入性小。  
多维数据模型  
Prometheus 存储的是时序数据，但其强大的地方在于它的多维数据模型。每一条时间序列都由一个指标名称（metric name）和一组键值对标签（labels）唯一确定。例如 http_requests_total{method="POST", handler="/api/users"}。这种基于标签的数据模型与 Kubernetes 自身通过标签来组织资源的哲学完美契合。  
与 Kubernetes 的集成  
Prometheus 和 Kubernetes 堪称 " 天作之合 "，因为它们共享相似的设计理念。Prometheus 通过与 Kubernetes API Server 集成，实现了强大的服务发现 (Service Discovery) 功能。它可以配置为自动发现集群中的 Service、Pod、Endpoint、Ingress 等资源，并根据这些资源上的元数据（特别是标签和注解）来动态地生成监控目标。这意味着当您在 Kubernetes 中部署一个新应用或对其进行扩缩容时，Prometheus 能够自动地将其纳入或移出监控范围，无需任何手动配置。  
生态系统组件  
Prometheus 不仅仅是一个数据库，它是一个完整的生态系统 46：

- **Prometheus Server**：负责服务发现、指标抓取、存储和查询。
- **Exporters**：对于那些本身不暴露 Prometheus 格式指标的系统（如数据库、硬件设备），可以使用 Exporter 作为中间代理来转换其指标。
- **Alertmanager**：独立处理由 Prometheus Server 触发的告警，负责去重、分组、静默，并通过邮件、Slack 等多种方式发送通知。
- **PromQL**：一种功能强大的查询语言，用于查询和聚合时序数据，也是定义告警规则的基础。

Prometheus 与 Kubernetes 在 CNCF 中共同成长和演进，其设计哲学上的高度一致性使其成为监控云原生环境的不二之选。理解如何有效监控 Kubernetes，在很大程度上就等同于理解如何使用 Prometheus。

---

## 17 **结论：您的 Kubernetes 中级专家之路**

本次学习之旅系统性地穿越了 Kubernetes 的三十个核心概念，构建了一条从基础到高级的认知路径。

回顾整个旅程，可以发现几个贯穿始终的核心设计哲学：

- **声明式 API**：用户只需定义 " 期望状态 "，系统便会自动地、持续地工作以达到该状态。
- **控制循环**：无数个小型的、专注的控制器是实现声明式模型的引擎，赋予了系统自愈和自动化的能力。
- **抽象与解耦**：通过 Pod、Service、PV/PVC 等抽象，将应用与底层基础设施解耦；通过 CRI、CNI、CSI 等标准接口，将核心平台与外部生态解耦。
- **API 中心化**：API Server 是所有交互的中心，这种设计保证了系统的一致性、安全性和极高的可扩展性。

通过这五个阶段的学习，您不仅掌握了运行和管理应用所需的具体技能，更重要的是，理解了这些功能背后的架构决策和设计思想。您现在已经具备了中级 Kubernetes 专家的知识框架。

然而，真正的精通源于实践。下一步，建议您将理论付诸行动：

- **动手实践**：搭建自己的集群（使用 Minikube、Kind 或云服务），亲手部署和管理各类应用。
- **考取认证**：备考 CKA (认证 Kubernetes 管理员) 或 CKAD (认证 Kubernetes 应用开发者) 是检验和巩固知识的绝佳方式。
- **探索生态**：深入研究服务网格（如 Istio、Linkerd）、更高级的 CNI/CSI 插件，以及 GitOps 工具（如 ArgoCD、Flux）。
- **参与社区**：关注 Kubernetes 的特别兴趣小组（SIGs），了解其发展方向，甚至尝试为社区做出贡献。

Kubernetes 的世界广阔而充满活力。希望本报告能成为您在这条道路上坚实的垫脚石，助您在云原生的浪潮中行稳致远。

### 17.1 **Works cited**

1. Kubernetes, accessed August 30, 2025, [https://kubernetes.io/](https://kubernetes.io/)
2. Overview - Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/overview/](https://kubernetes.io/docs/concepts/overview/)
3. Pod Lifecycle | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
4. Container Runtimes | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/setup/production-environment/container-runtimes/](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)
5. cri-o, accessed August 30, 2025, [https://cri-o.io/](https://cri-o.io/)
6. Nodes | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/architecture/nodes/](https://kubernetes.io/docs/concepts/architecture/nodes/)
7. Kubernetes Control Plane: Ultimate Guide (2024) - Plural.sh, accessed August 30, 2025, [https://www.plural.sh/blog/kubernetes-control-plane-architecture/](https://www.plural.sh/blog/kubernetes-control-plane-architecture/)
8. Labels and Selectors — Kubernetes on AWS 0.1 documentation, accessed August 30, 2025, [https://kubernetes-on-aws.readthedocs.io/en/latest/user-guide/labels.html](https://kubernetes-on-aws.readthedocs.io/en/latest/user-guide/labels.html)
9. Kubernetes Deployment Strategies: The Definitive Guide - Codefresh, accessed August 30, 2025, [https://codefresh.io/learn/kubernetes-deployment/](https://codefresh.io/learn/kubernetes-deployment/)
10. Service | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/services-networking/service/](https://kubernetes.io/docs/concepts/services-networking/service/)
11. kube-proxy | Kubernetes, accessed August 30, 2025, [http://pwittrock.github.io/docs/admin/kube-proxy/](http://pwittrock.github.io/docs/admin/kube-proxy/)
12. User Namespaces - Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/workloads/pods/user-namespaces/](https://kubernetes.io/docs/concepts/workloads/pods/user-namespaces/)
13. Kubectl Reference Docs - Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)
14. Command line tool (kubectl) | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/reference/kubectl/overview/](https://kubernetes.io/docs/reference/kubectl/overview/)
15. Kubernetes API Concepts | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/reference/using-api/api-concepts/](https://kubernetes.io/docs/reference/using-api/api-concepts/)
16. API Overview | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/reference/using-api/](https://kubernetes.io/docs/reference/using-api/)
17. ConfigMaps | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/configuration/configmap/](https://kubernetes.io/docs/concepts/configuration/configmap/)
18. In-Depth Guide to Kubernetes ConfigMap & Secret Management Strategies - Ambassador Labs, accessed August 30, 2025, [https://www.getambassador.io/blog/kubernetes-configurations-secrets-configmaps](https://www.getambassador.io/blog/kubernetes-configurations-secrets-configmaps)
19. Secrets | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/configuration/secret/](https://kubernetes.io/docs/concepts/configuration/secret/)
20. Volumes and Storage - K3s, accessed August 30, 2025, [https://docs.k3s.io/storage](https://docs.k3s.io/storage)
21. Persistent Volumes | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/storage/persistent-volumes/](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
22. Basic configuration | NGINX Documentation, accessed August 30, 2025, [https://docs.nginx.com/nginx-ingress-controller/configuration/ingress-resources/basic-configuration/](https://docs.nginx.com/nginx-ingress-controller/configuration/ingress-resources/basic-configuration/)
23. Ingress | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/services-networking/ingress/](https://kubernetes.io/docs/concepts/services-networking/ingress/)
24. What is Helm in Kubernetes? - Sysdig, accessed August 30, 2025, [https://www.sysdig.com/learn-cloud-native/what-is-helm-in-kubernetes](https://www.sysdig.com/learn-cloud-native/what-is-helm-in-kubernetes)
25. Docs - Helm, accessed August 30, 2025, [https://helm.sh/docs/](https://helm.sh/docs/)
26. StatefulSets | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
27. StatefulSet Basics - Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/tutorials/stateful-application/basic-stateful-set/](https://kubernetes.io/docs/tutorials/stateful-application/basic-stateful-set/)
28. kubernetes_daemonset | Resources | hashicorp/kubernetes - Terraform Registry, accessed August 30, 2025, [https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs/resources/daemonset](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs/resources/daemonset)
29. DaemonSet | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
30. CronJob | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
31. Kubernetes HPA [Horizontal Pod Autoscaler] Guide - Spacelift, accessed August 30, 2025, [https://spacelift.io/blog/kubernetes-hpa-horizontal-pod-autoscaler](https://spacelift.io/blog/kubernetes-hpa-horizontal-pod-autoscaler)
32. Horizontal Pod Autoscaling | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
33. kube-controller-manager - Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager/](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager/)
34. Kubernetes Control Plane | dockerlabs - Collabnix, accessed August 30, 2025, [https://dockerlabs.collabnix.com/kubernetes/beginners/Kubernetes_Control_Plane.html](https://dockerlabs.collabnix.com/kubernetes/beginners/Kubernetes_Control_Plane.html)
35. Controllers | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/architecture/controller/](https://kubernetes.io/docs/concepts/architecture/controller/)
36. Creating Highly Available Clusters with kubeadm | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)
37. etcd, accessed August 30, 2025, [https://etcd.io/](https://etcd.io/)
38. Scheduling Framework | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/)
39. kubelet | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/)
40. CNI, accessed August 30, 2025, [https://www.cni.dev/](https://www.cni.dev/)
41. Amazon VPC CNI - Amazon EKS - AWS Documentation, accessed August 30, 2025, [https://docs.aws.amazon.com/eks/latest/best-practices/vpc-cni.html](https://docs.aws.amazon.com/eks/latest/best-practices/vpc-cni.html)
42. Introduction - Kubernetes CSI Developer Documentation, accessed August 30, 2025, [https://kubernetes-csi.github.io/docs/](https://kubernetes-csi.github.io/docs/)
43. Using RBAC Authorization | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/reference/access-authn-authz/rbac/](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
44. Network Policies | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/services-networking/network-policies/](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
45. Custom Resources | Kubernetes, accessed August 30, 2025, [https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
46. Overview | Prometheus, accessed August 30, 2025, [https://prometheus.io/docs/introduction/overview/](https://prometheus.io/docs/introduction/overview/)