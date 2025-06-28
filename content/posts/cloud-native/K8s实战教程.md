+++
date = '2025-06-28T22:03:32+08:00'
draft = false
title = 'K8s 实战教程'
slug = '295cf1c4'
tags = ["k8s"]
categories = ["Cloud Native"]
+++

Kubernetes（简称 K8s）已成为云原生时代的标准，是构建、部署和管理可扩展应用的事实上的操作系统。掌握它对于现代软件工程师和运维专家而言至关重要。

本教程将采用一种循序渐进的实战方法。我们将从最基础的 **Container（容器）** 概念出发，通过逐步迭代和完善配置文件，引导你掌握 Pod、Deployment、Service、Ingress 等核心资源。最终，你将学会如何使用 Helm 将所有组件打包，实现一套完整服务的自动化部署。

## 准备工作

在开始之前，请确保你的开发环境满足以下要求。本教程主要参考自这篇优秀的 [教程](https://guangzhengli.com/courses/kubernetes)，并结合了个人实践。

1. **容器运行时与 Kubernetes 集群**：你需要一个容器运行时（如 Docker）和一个本地 Kubernetes 集群。
  - **推荐方案 (macOS)**：使用 [OrbStack](https://orbstack.dev/)。它集成了 Docker 和 Kubernetes，一键启动即可获得完整的开发环境，无需额外安装 Minikube 或 Docker Desktop。
2. **Kubernetes 命令行工具**：安装 `kubectl`，它是与 Kubernetes 集群交互的核心工具。
3. **容器镜像仓库**：注册一个容器镜像仓库账号，如 Docker Hub、阿里云 ACR 或其他公有/私有仓库，并使用 `docker login` 命令登录。我们后续构建的镜像将推送到这里。

## Container

我们的云原生之旅始于最核心的构建块：**容器 (Container)**。容器将应用程序及其所有依赖项打包在一起，确保其在任何环境中都能以一致的方式运行。主要氛围三个部分：

1. **编写一个简单的 Go Web 应用**。
2. **使用多阶段构建 (Multi-stage Build) 的 `Dockerfile` 将其打包成一个轻量、安全的镜像**。
3. **编写一个脚本来自动化构建和推送镜像的流程**。

选择 Go 语言是因为它在云原生领域广受欢迎，其主要优势在于：

- **静态编译**：生成无外部依赖的单个二进制文件，非常适合容器化。
- **跨平台**：轻松编译适用于不同操作系统和架构（如 `linux/amd64`）的程序。
- **高性能**：天生支持并发，内存占用低，非常适合构建高效的微服务。

为了构建一个最优的容器镜像，我们将采用**多阶段构建（Multi-stage Build）** 策略。这是一种最佳实践，能有效减小镜像体积并提高安全性。

- **构建阶段 (Builder Stage)**：使用一个包含完整 Go 工具链的基础镜像来编译我们的源代码，生成一个静态链接的可执行文件。
- **最终阶段 (Final Stage)**：使用一个极简的基础镜像（如 `distroless`），它仅包含运行程序所必需的库。我们只将上一步生成的可执行文件拷贝进来，完全抛弃了 Go 编译环境和源代码。

通过这种方式，最终镜像的体积可以从数百 MB 锐减到约 10MB，极大地提升了分发效率和安全性。

```dockerfile
# 使用 Go 官方镜像作为构建环境
FROM golang:1.20-buster AS builder
# 设置工作目录
WORKDIR /src
# 复制项目文件到工作目录
COPY . .
# 设置 Go 模块自动模式
RUN go env -w GO111MODULE=auto
# 下载依赖并编译二进制文件
RUN go build -o main .

# 使用轻量级的基础镜像
FROM gcr.io/distroless/base-debian10
# 设置工作目录
WORKDIR /
# 从构建阶段复制二进制文件
COPY --from=builder /src/main /main
# 暴露服务端口
EXPOSE 3000
# 设置容器启动命令
ENTRYPOINT ["/main"]
```

为了简化镜像的构建、标记和推送流程，我们编写一个 shell 脚本来自动化这些重复性任务。

- **跨平台构建**：`docker build` 命令中的 `--platform` 标志允许我们在 ARM 架构的 Mac（如 M1/M2/M3）上构建出能在标准 x86-64 服务器（`linux/amd64`）上运行的镜像。你也可以使用 `docker buildx` 来同时构建多种架构的镜像。

```shell
#!/bin/zsh

# 设置严格模式，确保脚本在遇到错误时立即退出
set -e

IMAGE_NAME="hellok8s"
VERSION="v1"
REGISTRY="registry.cn-hangzhou.aliyuncs.com/ceyewan"

echo "构建镜像…"
docker build --platform linux/amd64 -t "${IMAGE_NAME}:${VERSION}" ./container

echo "打 tag…"
docker tag "${IMAGE_NAME}:${VERSION}" "${REGISTRY}/${IMAGE_NAME}:${VERSION}"

echo "登录阿里云镜像仓库…"
docker login "${REGISTRY}"

echo "推送镜像…"
docker push "${REGISTRY}/${IMAGE_NAME}:${VERSION}"
```

镜像成功推送到仓库后，我们可以先用 Docker 在本地运行它，以验证其功能是否正常。

```shell
docker run -p 3000:3000 --name hellok8s -d ${REGISTRY}/${IMAGE_NAME}:${VERSION}
```

## Pod

在 Kubernetes 的世界里，**Pod** 是最小、最基本的可部署单元。它不是直接运行容器，而是对容器的一层抽象，代表了集群中一个正在运行的**进程实例**。一个 Pod 封装了一个或多个紧密协作的容器，为它们提供了一个共享的执行环境。这意味着：

- **共享网络**：Pod 内的所有容器共享同一个网络命名空间，包括 IP 地址和端口。它们可以通过 `localhost` 互相通信。
- **共享存储**：可以为 Pod 指定一组共享的存储卷（Volumes），Pod 内的所有容器都可以挂载和访问这些卷。

让我们通过一个 YAML 清单（Manifest）来定义并创建一个 Pod。YAML 文件是 Kubernetes 中定义资源的标准方式。

```yaml
# pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: hellok8s-pod # Pod 的名称，在同一个命名空间内必须唯一
spec:
  containers:
    - name: hellok8s-container # 容器的名称
      image: registry.cn-hangzhou.aliyuncs.com/ceyewan/hellok8s:v1
```

- `apiVersion`: 定义了创建此对象的 Kubernetes API 版本。
- `kind`: 指定了要创建的资源类型，这里是 `Pod`。
- `metadata`: 包含了资源的元数据，如 `name`（名称）。
- `spec`: 描述了 Pod 的期望状态（Desired State），包括它应该运行哪些 `containers`。

常用 **kubectl** 命令：

```shell
kubectl apply -f hellok8s.yaml # 基于 YAML 文件创建资源
kubectl get pods # 查看当前命名空间下所有 Pod 的状态
kubectl port-forward hellok8s-pod 3000:3000 # 端口转发
kubectl logs --follow hellok8s-pod # 查看日志，即 stdio
# 进入 Pod 内的容器执行命令 
# (注：我们使用的 distroless 镜像不包含 shell，此命令会失败)
kubectl delete pod hellok8s-pod  # 删除 pod
kubectl delete -f hellok8s.yaml # 删除资源，效果一样
```

虽然 Pod 是运行容器的基础，但我们通常不会在生产环境中直接创建和管理单个 Pod（这种 Pod 被称为**裸 Pod**）。这是因为裸 Pod 非常脆弱：

- **无自愈能力**：如果 Pod 所在节点发生故障，或者 Pod 进程崩溃退出，这个 Pod 将会永远消失，Kubernetes 不会自动重建它。
- **无扩展能力**：无法轻松地水平扩展（增加或减少）应用实例。
- **升级困难**：更新应用版本需要手动删除旧 Pod 并创建新 Pod，这会导致服务中断。

为了解决这些问题，Kubernetes 提供了更高层次的抽象，也就是 **Deployment**。

## Deployment

**Deployment** 是一种更高阶的控制器（Controller），它为 Pod 和 ReplicaSet（Deployment 的另一个底层组件）提供了声明式的管理能力。你只需在 Deployment 中声明应用的 " 期望状态 "，Deployment Controller 就会持续工作，确保集群的 " 实际状态 " 与你的期望保持一致。

Deployment 的核心职责包括：

1. **管理 Pod 生命周期**：确保指定数量的 Pod 副本（Replicas）持续运行，实现应用的**自愈**和**高可用**。
2. **应用扩缩容**：轻松调整运行的 Pod 副本数量。
3. **自动化发布与回滚**：支持滚动更新（Rolling Update）等多种发布策略，实现应用平滑升级，且无需停机。

### 实现高可用与自愈

让我们创建一个 `deployment.yaml` 文件，用它来管理我们的 `hellok8s` 应用。

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hellok8s-deployment
spec:
  replicas: 3 # 期望状态：保持 3 个 Pod 副本运行
  selector:
    matchLabels:
      app: hellok8s # 选择器：找到带有 'app=hellok8s' 标签的 Pod
  template:
    metadata:
      labels:
        app: hellok8s # Pod 标签：必须与上面的 selector 匹配
    spec:
      containers:
        - image: registry.cn-hangzhou.aliyuncs.com/ceyewan/hellok8s:v1
          name: hellok8s-container
```

- `replicas`: 定义了期望的 Pod 副本数量。Deployment 会始终维持这个数量。
- `template`: 定义了创建 Pod 的模板。它的内容（除了 `apiVersion` 和 `kind`）就是一个完整的 Pod `spec`。注意，这里我们**不**需要为 Pod 指定 `name`，因为 Deployment 会自动为每个 Pod 生成唯一的名称。
- `selector`: 定义了 Deployment 如何找到它所管理的 Pod。`spec.selector.matchLabels` 必须与 `spec.template.metadata.labels` 匹配。这个标签是 Deployment 和 Pod 之间的 " 契约 "。

```shell
# 创建 Deployment
kubectl apply -f deployment.yaml
# 查看 Deployment 状态和它创建的 Pods
kubectl get deployments
kubectl get pods
# 输出：会看到 3 个由 Deployment 创建的 Pod
# NAME                                   READY   STATUS    RESTARTS   AGE
# hellok8s-deployment-ff77b48f7-7lhtv    1/1     Running   0          …
# hellok8s-deployment-ff77b48f7-mmjws    1/1     Running   0          …
# hellok8s-deployment-ff77b48f7-xpfbh    1/1     Running   0          …
# 随机删除一个 Pod
kubectl delete pod hellok8s-deployment-ff77b48f7-7lhtv
# 立即再次查看 Pods
kubectl get pods                                       
# NAME                                   READY   STATUS    RESTARTS  AGE
# hellok8s-deployment-6bb45fd886-hs4cs  1/1     Running   0           …
# hellok8s-deployment-ff77b48f7-mmjws   1/1     Running   0           …
# hellok8s-deployment-ff77b48f7-xpfbh   1/1     Running   0           …
```

你会发现，被删除的 Pod 几乎瞬间就被一个新的 Pod 替代了。这就是 Deployment 的自愈能力：它持续监控匹配 `selector` 的 Pod 数量，一旦发现数量少于 `replicas`，就会立即使用 `template` 创建一个新的 Pod 来补足。

**应用扩缩容**也非常简单，只需修改 `replicas` 的值（例如改为 5），然后重新 `kubectl apply -f deployment.yaml`，Kubernetes 就会自动创建或删除 Pod 以达到新的期望数量。

### 滚动发布

在生产环境中，更新应用版本时，我们最不希望看到的就是服务中断。如果同时停止所有旧版本 Pod 再启动新版本，必然会导致服务不可用。Deployment 的**滚动更新（Rolling Update）** 策略完美地解决了这个问题。

滚动更新会逐步地用新版本的 Pod 替换旧版本的 Pod，保证在整个更新过程中，始终有可用的 Pod 在线提供服务。

我们可以通过 `spec.strategy` 字段来精细控制更新过程：

```yaml
# deployment-rolling-update.yaml
spec:
  replicas: 3
  strategy:
    type: RollingUpdate # 默认为滚动更新
    rollingUpdate:
      maxSurge: 1       # 更新期间，允许超出期望副本数的最大 Pod 数量
      maxUnavailable: 1 # 更新期间，允许处于不可用状态的最大 Pod 数量
```

- `maxSurge`: 决定了可以 " 额外 " 创建多少个新 Pod。如果 `replicas` 为 3，`maxSurge` 为 1，那么在更新过程中，Pod 总数最多可以达到 4 个。这能加速更新过程。
- `maxUnavailable`: 决定了可以有多少个 Pod 处于 " 不可用 " 状态。如果 `replicas` 为 3，`maxUnavailable` 为 1，那么在更新过程中，必须保证至少有 2 (`3-1`) 个 Pod 是可用的。这能保证服务的稳定性。

将 `deployment.yaml` 文件中的镜像版本从 `v1` 改为 `v2`，然后 `apply`。Kubernetes 就会开始滚动更新。你可以使用以下命令来观察和控制发布过程：

```shell
# 建议在 deployment 文件中写清楚版本信息，方便回滚调试等
kubectl rollout history deployment/<name> # 查看历史版本
kubectl rollout history deployment/<name> --revision=<number> # 查看特定版本详情
kubectl rollout undo deployment/<name> # 回滚到上一个版本
kubectl rollout undo deployment/<name> --to-revision=<number> # 回滚到指定版本
kubectl rollout status deployment/<name> # 监控部署/回滚状态
kubectl rollout pause deployment/<name> # 暂停部署
kubectl rollout resume deployment/<name> # 恢复部署
```

### 存活探针

Deployment 确保了 Pod 的数量，但它如何知道 Pod 内部的应用是否真的健康呢？答案是**探针（Probes）**。

存活探针用于判断容器是否仍在正常运行。如果探测失败，kubelet 会认为容器已经 " 死亡 "（例如陷入死锁），并会根据其重启策略（`restartPolicy`）**重启该容器**。

**场景**：当你的应用虽然进程存在但已无响应时，存活探针能触发自动重启，使其恢复服务。

修改代码，打包新的镜像，标签为 `liveness`。

```go
started := time.Now() 
http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) { 
    duration := time.Since(started) 
    if duration.Seconds() > 15 { 
        w.WriteHeader(500) 
        w.Write([]byte(fmt.Sprintf("error: %v", duration.Seconds()))) 
    } else { 
        w.WriteHeader(200) w.Write([]byte("ok")) 
    } 
})
```

然后我们编写 deployment 的定义，这里使用存活探测方式是使用 HTTP GET 请求，请求的是刚才定义的 `/healthz` 接口，`periodSeconds` 字段指定了 kubelet 每隔 3 秒执行一次存活探测。 `initialDelaySeconds` 字段告诉 kubelet 在执行第一次探测前应该等待 3 秒。

```yaml
containers:
  - image: registry.cn-hangzhou.aliyuncs.com/ceyewan/hellok8s:liveness
    name: hellok8s-container
    livenessProbe:
      httpGet:
        path: /healthz
        port: 3000
      initialDelaySeconds: 3 # 执行第一次探测前等待时间
      periodSeconds: 3 # 存活探测周期
```

在示例中，应用在 15 秒后 `/healthz` 接口开始返回失败状态码。部署后，你会观察到 Pod 在运行一段时间后会进入 `CrashLoopBackOff` 状态，因为存活探针失败导致容器被反复重启。

```shell
$ kubectl get pods
NAME                                  READY   STATUS    RESTARTS   AGE
hellok8s-deployment-ff77b48f7-64b2t   1/1     Running   0          3m55s
hellok8s-deployment-ff77b48f7-j6l8h   1/1     Running   0          3m55s
hellok8s-deployment-ff77b48f7-mb2tm   1/1     Running   0          3m55s
$ kubectl apply -f hellok8s-liveness.yaml
deployment.apps/hellok8s-deployment configured
$ kubectl get pods -w
NAME                                  READY   STATUS              RESTARTS
hellok8s-deployment-55fd7b768-pjn5c   0/1     ContainerCreating   0        
hellok8s-deployment-55fd7b768-zgn6l   0/1     ContainerCreating   0        
hellok8s-deployment-ff77b48f7-64b2t   1/1     Running             0        
hellok8s-deployment-ff77b48f7-j6l8h   1/1     Running             0        
hellok8s-deployment-55fd7b768-zgn6l   1/1     Running             0        
...
hellok8s-deployment-55fd7b768-zgn6l   1/1     Running             2 (1s ago)
hellok8s-deployment-55fd7b768-pjn5c   1/1     Running             2 (1s ago)
hellok8s-deployment-55fd7b768-v8qms   1/1     Running             2 (1s ago)
```

### 就绪探针

就绪探针用于判断容器是否已经准备好接收并处理外部流量。如果就绪探针失败，会发生两件事：

1. **端点移除**：该 Pod 的 IP 地址会从所有关联的 Service 的端点列表（Endpoints）中被移除。流量将不再被转发到这个 Pod。
2. **发布暂停**：在滚动更新期间，Deployment 会等待新 Pod 的就绪探针成功后，才继续更新下一个 Pod。

**场景**：

- 应用启动时需要较长时间加载数据或预热缓存，在完成前不应接收流量。
- 防止有问题的版本（例如，无法连接数据库）被发布到生产环境。

修改代码，将应用的 `/healthz` 接口直接设置成返回 500 状态码，代表该版本是一个有问题的版本。修改 deployment 文件如下：

```yaml
containers:
  - image: registry.cn-hangzhou.aliyuncs.com/ceyewan/hellok8s:bad
    name: hellok8s-container
    readinessProbe: # 就绪探针
      httpGet:
        path: /healthz
        port: 3000
      initialDelaySeconds: 1 # 执行第一次探测前等待时间
      successThreshold: 5 # 最少成功次数，即探测成功5次才认为就绪
```

在示例中，当使用一个 `/healthz` 总是失败的 "bad" 镜像进行滚动更新时，你会发现新的 Pod 永远无法达到 `READY 1/1` 的状态。更重要的是，滚动更新会卡住，旧版本的 Pod 会继续提供服务，从而防止了故障版本的上线，保证了服务的整体可用性。

```shell
kubectl get pods
NAME                                   READY   STATUS    RESTARTS   AGE
hellok8s-deployment-6bb45fd886-8s6px   0/1     Running   0          62s
hellok8s-deployment-6bb45fd886-hksgf   0/1     Running   0          62s
hellok8s-deployment-ff77b48f7-86vkr    1/1     Running   0          112s
hellok8s-deployment-ff77b48f7-hshnv    1/1     Running   0          2m1s
```

## Service

我们已经通过 Deployment 实现了应用的自愈和扩缩容，但一个新的问题出现了：**Pod 是短暂的，它们的 IP 地址会随着重建、扩缩容而动态改变。** 那么，集群内部的其他服务，或者外部用户，如何才能可靠地访问到一个由多个动态 Pod 组成的应用程序呢？

答案就是 **Service**。Service 是 Kubernetes 中的一个核心网络抽象，它为一组功能相同的 Pod 提供了一个**稳定、统一的访问入口**和**自动的负载均衡**。

你可以将 Service 想象成一个应用的 " 虚拟 IP" 或 " 内部域名 "。它会持续跟踪符合其 `selector` 条件的健康 Pod，并将网络请求智能地分发给它们。

Service 主要通过 `type` 字段定义其暴露方式，常见的有以下三种：

### ClusterIP

这是 Service 的**默认类型**。它会为 Service 分配一个只能在**集群内部**访问的虚拟 IP 地址。

- **核心用途**：实现集群内部服务之间的相互发现和通信。例如，Web 前端服务需要调用后端的账户服务。
- **工作原理**：Service 通过 `selector` 找到所有带有 `app: hellok8s` 标签的 Pod，并把它们的 IP 和端口注册为自己的端点（Endpoints）。集群内的任何其他 Pod 只需要访问 Service 的 ClusterIP 和端口，请求就会被自动负载均衡到后端的某个健康 Pod 上。

```yaml
# service-clusterip.yaml
apiVersion: v1
kind: Service
metadata:
  name: service-hellok8s-clusterip
spec:
  type: ClusterIP # 可省略，因为是默认值
  selector:
    app: hellok8s # 关键：这个标签选择器必须与 Pod 模板中的标签一致
  ports:
  - protocol: TCP
    port: 3000       # Service 自身暴露的端口
    targetPort: 3000 # 流量要转发到的目标 Pod 容器的端口
```

可以通过以下命令查看相关信息：

```shell
kubectl get endpointslice
# 获取endpoint信息，因为可能 Pod 非常多，将一个 Service 的所有端点分割成多个更小的slice
kubectl get service
# 查看 service 信息，会有一个统一的内部地址，我们可以进入集群内的一个容器来访问这个地址
```

多次访问，可以发现我们程序返回的 hostname 各不相同，说明进行了负载均衡策略。

### NodePort

`NodePort` 在 `ClusterIP` 的基础上，额外在**集群中每个 Node（物理或虚拟节点）** 上都开放一个相同的静态端口（范围通常在 30000-32767）。

- **核心用途**：在开发或测试环境中，快速地将服务暴露给外部网络，以便进行临时访问和调试。
- **工作原理**：外部流量可以通过访问 `http://<任意一个Node的IP>:<NodePort>` 来触达服务。请求到达 Node 后，会被转发到 Service 的 ClusterIP，再由 Service 负载均衡到后端的 Pod。

```yaml
# service-nodeport.yaml
apiVersion: v1
kind: Service
metadata:
  name: service-hellok8s-nodeport
spec:
  type: NodePort
  selector:
    app: hellok8s
  ports:
  - port: 3000
    targetPort: 3000
    nodePort: 30000 # 在所有 Node 上开放 30000 端口
```

这种方式，就是通过物理节点的 IP 及 Port，来访问内部虚拟 Pod。如果你是用本地的 minikube 来搭的，可以通过 `minikube ip` 看到节点 IP，如果是用的虚拟机来搭的，那么就是虚拟机 IP，我这里使用的是阿里云的 ACK 容器服务，节点只有内部 IP，也需要进入集群内部才能访问。

### LoadBalancer

这是在**云环境（如 AWS, GCP, Azure, 阿里云）** 中最标准的暴露服务的方式。

- **核心用途**：为应用提供一个具备公网 IP 地址的、高可用的外部负载均衡器。
- **工作原理**：当你创建一个 `type: LoadBalancer` 的 Service 时，Kubernetes 会与云平台的 API 交互，自动为你**申请并配置一个外部负载均衡器**（如 AWS ELB, 阿里云 SLB）。这个负载均衡器会将流量导向所有节点的 `NodePort`。它本质上是 `NodePort` 和 `ClusterIP` 的一种自动化和生产级封装。

## Ingress

`Service` 的 `LoadBalancer` 类型虽然强大，但它通常是 L4（传输层）的，并且每暴露一个服务就需要一个独立的负载均衡器和公网 IP，成本高昂。如果我们想通过同一个 IP 地址，根据不同的域名（`Host`）或 URL 路径（`Path`）来访问不同的服务，就需要一个更智能的 L7（应用层）路由工具。

**Ingress** 就是这个解决方案。它不是一种 Service，而是一个独立的资源，作为集群所有入站流量的**智能网关**。

> [!NOTE] **Ingress 与 Ingress Controller**
> 
> - **Ingress 资源**：一个 YAML 文件，定义了一套**路由规则**。例如，" 将 `foo.example.com` 的流量转发到 `foo-service`"，" 将 `/bar` 路径的流量转发到 `bar-service`"。它本身**不执行任何操作**，只是一个配置声明。
> - **Ingress Controller**：一个实际运行在集群中的 Pod，通常是 NGINX、Traefik 或云厂商提供的特定控制器（如 ALB Ingress Controller）。它的职责是**读取**集群中所有的 Ingress 资源，并根据这些规则**动态配置**自己，从而实现真正的流量转发。
> 
> **结论：没有 Ingress Controller，Ingress 资源将毫无作用。**

我这里使用的是阿里云自研的 ALB Ingress，在创建集群时，需要创建好 Ingress 控制器，然后配置如下：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hellok8s-ingress
spec:
  ingressClassName: alb # 指定由哪个 Ingress Controller 来处理这个 Ingress
  rules:
    - host:  # 基于域名的路由
      http:
        paths:
          - path: / # 路径匹配
            pathType: Prefix # 路径匹配类型
            backend:
              service:
                name: service-hellok8s-clusterip # 将流量转发到这个 Service
                port:
                  number: 3000
```

通过 Ingress，我们可以用一个公网 IP 和负载均衡器，管理和暴露集群内成百上千个服务，实现基于名称的虚拟主机和精细的路径路由，并集中处理 SSL/TLS 证书。

可以通过 `kubectl get ingress` 看到阿里云给我们分配了一个外部地址，到现在，我们终于可以使用这个地址来从外部请求我们的服务了。

```shell
curl alb-3houpovgvb8ljg6aov.cn-beijing.alb.aliyuncsslb.com
[v2] Hello, Kubernetes! 
From host: hellok8s-deployment-ff77b48f7-86vkr
CPU sum: 662921401752298880
Alloc: 10.12 MB
TotalAlloc: 10.19 MB
Sys: 23.44 MB
NumGC: 1
```

## Namespace

随着项目变多、团队扩大，直接在默认的（`default`）命名空间中管理所有资源会变得混乱不堪。**Namespace** 提供了一种在同一个物理集群内划分出多个**虚拟集群**的机制。

- **核心用途**：
  - **环境隔离**：创建 `dev`、`staging`、`production` 等命名空间来隔离不同环境的资源。
  - **多租户与团队隔离**：为不同团队或项目分配独立的命名空间，避免命名冲突和资源误操作。
  - **资源配额管理**：可以为每个命名空间设置资源配额（ResourceQuota），限制其可用的 CPU、内存等。

大部分资源（如 Deployment, Service, Pod）都属于某个命名空间，其名称在命名空间内必须唯一，但在不同命名空间之间可以重复。

前面的教程中，默认使用的 namespace 是 `default`。下面就是一个创建命名空间的配置。

```yaml
apiVersion: v1 
kind: Namespace 
metadata: 
  name: dev
```

通过 `kubectl get namespaces` 可以查看所有的命名空间，通过 `kubectl apply -f xxx.yaml -n dev` 可以指定在特定 namespace 下创建资源。

## ConfigMap

将配置信息（如数据库地址、API Key）硬编码在容器镜像中是一种糟糕的实践，因为它使得应用与特定环境紧密耦合，难以移植和维护。Kubernetes 提供了两种资源来解耦配置。其中 `ConfigMap` 用于存储**非敏感**的键值对配置数据。你可以将这些数据以**环境变量**或**文件挂载**的形式注入到 Pod 中。

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hellok8s-config
data:
  URL: "http://localhost-test:3306"

---

apiVersion: v1
kind: Pod
metadata:
  name: hellok8s-configmap-pod
spec:
  containers:
    - name: hellok8s-container
      image: registry.cn-hangzhou.aliyuncs.com/ceyewan/hellok8s:v3
      env:
        - name: URL
          valueFrom:
            configMapKeyRef:
              name: hellok8s-config
              key: URL
```

最终效果如下，不同的环境变量，读取到的值是不一样的：

![[Pasted image 20250627113634.png]]

## Secret

`Secret` 的结构和用法与 `ConfigMap` 非常相似，但它专门用于存储**敏感信息**，如密码、TLS 证书、API 令牌等。

- **重要提醒**：默认情况下，Secret 中的数据仅经过 Base64 **编码**，而非**加密**。Base64 只是为了防止数据在传输中出现问题，任何人都可以轻松解码。为了安全，必须在集群层面**启用 etcd 的静态加密 (Encryption at Rest)** 并配合 RBAC 严格控制对 Secret 的访问权限。

## Job

并非所有应用都是需要 7x24 小时运行的常驻服务。对于那些执行一次就结束的任务，Kubernetes 提供了 `Job` 和 `CronJob`。

一个 `Job` 会创建一个或多个 Pod，并确保指定数量的 Pod **成功运行到完成**。如果 Pod 失败，Job 会根据配置进行重试。

- **使用场景**：数据迁移、批量计算、执行一次性的初始化脚本。

`CronJob` 在 `Job` 的基础上增加了一个 `cron` 格式的调度表达式，用于周期性地创建和运行 Job。

- **使用场景**：每日生成报表、定时执行数据库备份、定期清理临时文件。

## Helm

随着云原生应用的规模和复杂度不断增长，我们通常需要管理数量庞大的 Kubernetes 资源文件（如 Deployment, Service, StatefulSet, ConfigMap, Secret, Ingress 等）。为不同的环境（开发、测试、生产）维护多套配置，并手动通过 `kubectl apply -f <file>` 逐一应用，这一过程不仅极其繁琐，而且极易因人为疏忽导致配置漂移和部署失败。

如何标准化地打包、分发、部署和管理这些复杂的 Kubernetes 应用？这正是 **Helm** 所要解决的核心问题。

**Helm** 是 Kubernetes 生态系统中的**事实标准包管理器**。它扮演着类似于 Linux 系统中 `apt`、`yum` 或 macOS 中 `brew` 的角色。Helm 允许开发者和运维人员将一个完整应用所需的所有 Kubernetes 资源打包、配置、共享和部署，极大地简化了复杂应用的生命周期管理。

通过 Helm，您可以：

- **一键部署**：用一条命令安装、升级或卸载一个完整的应用（如 Prometheus 监控栈、Redis 集群）。
- **标准化与复用**：将应用打包成可复用的模块，在不同项目和团队间共享。
- **版本控制与回滚**：对应用部署进行版本化管理，轻松实现一键回滚到历史版本。
- **管理复杂依赖**：一个应用可以声明对其他应用（如图表）的依赖，Helm 会自动处理。

要掌握 Helm，必须理解其三大核心概念：

- **Chart (图表)**
  - **定义**：Chart 是 Helm 的打包格式，它是一个包含了描述相关 Kubernetes 资源集合的所有文件的目录。你可以把一个 Chart 想象成一个软件的安装包，里面有程序本身、配置文件和安装说明。
  - **作用**：将一个应用（例如一个 Web 服务及其数据库）所需的所有 Kubernetes 资源定义文件（YAML）打包在一起，形成一个可重用、可分发的单元。
- **Release (发布)**
  - **定义**：一个 Chart 在 Kubernetes 集群中的一个具体**部署实例**。
  - **作用**：同一个 Chart 可以在同一个集群中被安装多次，每次安装都会创建一个新的 Release。每个 Release 都有一个唯一的名称，并且 Helm 会跟踪其部署历史。例如，你可以用同一个 `redis` Chart 在集群中部署两个独立的 Redis 实例，一个叫 `redis-for-cache`，另一个叫 `redis-for-queue`。
- **Repository (仓库)**
  - **定义**：用于存放和共享 Chart 的 HTTP 服务器。它类似于 Docker Hub。
  - **作用**：开发者可以从公共仓库（如 Bitnami、Artifact Hub）中搜索和拉取成熟的 Chart，也可以搭建私有仓库来管理团队内部的 Chart。

Helm 的强大之处在于其**模板引擎 (Templating Engine)**。它允许我们将配置值从 Kubernetes 资源定义中分离出来，实现高度的参数化。

一个典型的 Chart 目录结构如下：

```txt
my-chart/
├── Chart.yaml          # Chart 的元数据：名称、版本、描述、API 版本等。
├── values.yaml         # Chart 的默认配置值，是用户最常修改的文件。
├── templates/          # 存放所有 Kubernetes 资源模板文件。
│   ├── deployment.yaml   # 部署模板
│   ├── service.yaml      # 服务模板
│   ├── ingress.yaml      # Ingress 模板
│   ├── configmap.yaml    # 配置映射模板
│   └── _helpers.tpl      # 可选：存放通用的模板辅助函数和代码片段。
├── charts/             # 可选：存放此 Chart 依赖的其他 Chart (子 Chart)。
└── crds/               # 可选：存放自定义资源定义 (CRD)。
```

在 `templates/` 目录下的 YAML 文件中，使用 Go 模板语法将可变部分替换为占位符。例如，在 `deployment.yaml` 中，副本数量可以这样定义：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-deployment
spec:
  replicas: {{ .Values.replicaCount }}
  # …
```

在 `values.yaml` 文件中为这些占位符提供默认值。

```yaml
# values.yaml
replicaCount: 1
image:
  repository: nginx
  tag: stable
```

`.Values` 对象会读取 `values.yaml` 的内容。`{{ .Values.replicaCount }}` 就会被渲染成 `1`。

当执行 `helm install` 时，Helm 模板引擎会将 `templates/` 目录下的所有模板文件与 `values.yaml`（以及用户通过命令行传入的值）结合起来，渲染成最终的、合法的 Kubernetes YAML 文件，然后将其发送给 Kubernetes API Server 执行。

这种机制使得同一套 Chart 可以通过提供不同的 `values` 文件或参数，轻松部署到开发、测试和生产等不同环境中。

```shell
# 创建一个名为 hellok8s 的 Chart 模板
helm create hellok8s
# 将当前目录的 Chart 打包成一个 .tgz 归档文件
helm package .
# 从本地目录安装 Chart，并创建一个名为 "hellok8s-release" 的 Release
helm install hellok8s-release .
# 安装时指定命名空间和自定义值
helm install hellok8s-release . --namespace my-app --set replicaCount=3
# 列出所有已部署的 Release
helm list -A
# 升级一个 Release（例如，更新镜像版本或副本数）
helm upgrade hellok8s-release .
# 查看一个 Release 的历史版本
helm history hellok8s-release
# 回滚到指定的历史版本（例如，版本 1）
helm rollback hellok8s-release 1
# 卸载一个 Release，并删除其所有关联的 Kubernetes 资源
helm uninstall hellok8s-release
# 添加一个社区仓库
helm repo add bitnami https://charts.bitnami.com/bitnami
# 更新本地仓库索引
helm repo update
# 从仓库中搜索 Chart
helm search repo redis
```

Helm 不仅仅是一个工具，它更是 Kubernetes 应用交付和管理的**最佳实践**。通过将应用定义、配置和生命周期管理进行标准化，Helm 解决了原生 YAML 管理的痛点，带来了以下核心价值：

- **复杂性管理**：将数十个 YAML 文件聚合为单一的、可管理的 Chart。
- **可重用性**：构建一次，即可在任何环境、任何集群中重复部署。
- **可分享性**：通过仓库轻松地在团队和社区之间共享和分发应用。
- **可靠的生命周期管理**：提供了一致且可靠的安装、升级、回滚和卸载工作流。

## Hpa

- **HPA (水平伸缩)**：调整 Pod 的 **数量**。当负载增加时，增加更多 Pod 实例来分担压力；当负载降低时，减少 Pod 实例以节省资源。就像超市人多时，多开几个收银台。
- **VPA (垂直伸缩)**：调整单个 Pod 的 **资源** (CPU/Memory)。当 Pod 需要更多资源时，为其分配更多的 CPU 或内存；反之则减少。就像给一台电脑升级 CPU 或内存条，让它变得更强大。

HPA 的目标是根据观察到的 **运行时指标** (如 CPU 使用率、内存使用量或自定义指标) 自动调整一个工作负载（如 Deployment、StatefulSet）的 Pod 副本数量。

**工作流程 (控制循环):**

1. **监控**：HPA Controller (通常在 `kube-controller-manager` 组件中) 会周期性地（默认为 15 秒）通过 Metrics Server 或自定义指标适配器（如 Prometheus Adapter）获取目标 Pod 的指标。
2. **比较**：将获取到的 **当前指标值** 与 HPA 对象中定义的 **目标指标值** 进行比较。
3. **计算**：根据以下公式计算出期望的 Pod 副本数：

```txt
期望副本数 = ceil[ 当前副本数 * ( 当前指标值 / 期望指标值 ) ]
ceil 是向上取整函数，确保在需要扩容时能及时响应。
```

4. **执行**：HPA Controller 更新目标工作负载（例如 Deployment）的 `.spec.replicas` 字段。Deployment Controller 监测到这个变化后，会创建或删除 Pod，使实际副本数与期望副本数一致。
5. **冷却**：为了防止因指标抖动而频繁扩缩容（称为"抖动"或"颠簸"），HPA 设有扩容和缩容的冷却时间（默认为扩容 3 分钟，缩容 5 分钟）。在此期间，不会执行同向的伸缩操作。

**支持的指标类型主要是资源指标 (Resource Metrics)**：最常见的即 CPU 和内存。

- **CPU 使用率 (targetCPUUtilizationPercentage)**：所有 Pod 的 CPU 使用量之和，除以它们的 CPU 请求 (Request) 总和，得出的百分比。**这是最常用的 HPA 指标**。
- **内存使用量 (targetMemoryValue)**：Pod 的平均内存使用量。

下面是一个典型的 **"快速扩容，谨慎缩容"（Fast Up, Slow Down）** 的高可用性策略。它会同时监控 CPU 和内存使用率，一旦任一指标超过阈值（CPU 60% 或内存 75%），就会非常 **迅速和激进** 地增加 Pod 数量（每次最多可翻倍或增加 5 个 Pod）来应对突发流量；而在负载降低时，它会经过 **更长的观察期**（3 分钟），并以非常 **平缓和保守** 的步调减少 Pod（每次最多减少 3 个或 25%），以防止因流量抖动造成服务不稳定。其核心目标是 **优先保证服务的响应能力和稳定性**，然后在确认负载确实降低后，再逐步回收资源以节约成本。

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vpa-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vpa-hpa-deployment
  minReplicas: 2
  maxReplicas: 60  # 3节点*4核*5Pod/core = 60 Pod，充分利用自动扩容的节点
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60  # CPU使用率60%时开始扩容，给计算留充足CPU
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 75  # 内存使用率75%时开始扩容
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30   # 扩容更积极，30秒稳定期
      policies:
      - type: Percent
        value: 100  # 每次可以扩容100%，更快响应
        periodSeconds: 30
      - type: Pods
        value: 5    # 每次最多增加5个Pod
        periodSeconds: 30
      selectPolicy: Max  # 选择更积极的扩容策略
    scaleDown:
      stabilizationWindowSeconds: 180  # 缩容稳定期3分钟
      policies:
      - type: Percent
        value: 25   # 每次最多缩容25%
        periodSeconds: 60
      - type: Pods
        value: 3    # 每次最多减少3个Pod
        periodSeconds: 60
      selectPolicy: Min   # 选择更保守的缩容策略
```

| 特性  | HPA (Horizontal Pod Autoscaler) | VPA (Vertical Pod Autoscaler) |
| --- | --- | --- |
| **伸缩维度** | **水平 (Horizontal)** | **垂直 (Vertical)** |
| **调整对象** | Pod 的 **数量** (`replicas`) | Pod 的 **资源** (`requests/limits`) |
| **主要目标** | 应对负载变化，保证服务吞吐量 | 优化资源利用率，保证单个 Pod 的稳定性 |
| **对服务的影响** | **无中断** (平滑增删 Pod) | **可能中断** (在 `Auto` 模式下会重启 Pod) |
| **成熟度** | Kubernetes **内置核心功能** | **需要单独安装** |
| **典型用例** | 无状态 Web 服务、API | 有状态应用 (数据库)、任务型作业、资源分析 |
| **与另一方的关系** | **不能** 与 VPA 同时基于 CPU/内存伸缩 | **不能** 与 HPA 同时基于 CPU/内存伸缩 |