---
date: '2025-06-28T21:53:07+08:00'
draft: false
title: 'Go 中的优雅关闭 Graceful Shutdown'
slug: 'abf1fab9'
tags:
  - ""
categories:
  - "Golang"
---

 对于现代的 HTTP 服务器和容器化应用，优雅关闭不仅仅是一个好习惯，更是确保服务不中断的关键措施。一个优雅的关闭过程通常需要满足以下三个核心条件：

 1. **停止接受新请求或消息**：在关闭应用时，首先要确保系统不再接收新的 HTTP 请求或消息。此时，仍然保持与数据库、缓存等外部系统的连接，避免中断外部服务的通信。
 2. **等待正在处理的请求完成**：关闭过程中，应该等待所有正在处理的请求完成，防止已有的请求因为服务突然关闭而未被正确响应。对于请求超时的情况，提供优雅的错误响应或通知用户，确保用户获得清晰的服务状态。
 3. **释放关键资源并执行清理**：在关闭过程中，及时释放关键资源至关重要。这包括数据库连接、文件锁、网络监听器等。所有资源都应当在退出前清理，确保不会留下任何潜在的资源泄漏或死锁问题。

>[!NOTE] 优雅退出
> **优雅退出**指程序或系统在终止时主动释放资源、保存状态并妥善处理未完成任务，确保数据完整性和服务连续性，避免强制中断导致的错误或损坏。常见于后台服务、多线程应用或分布式系统，通过捕获退出信号、清理临时文件、关闭数据库连接等步骤实现平稳关闭，提升可靠性与用户体验。

## 1 捕获信号

优雅关闭的第一步是捕获终止信号，这些信号通知应用程序该退出并开始关闭过程。信号是一种**软件中断**，通知进程发生了特定事件。操作系统会中断进程的正常流程并传递信号。

- **Signal handler**：应用程序可以为特定信号注册处理函数，接收到信号时自动执行。
- **Default action**：如果未注册处理函数，进程会按信号的默认行为处理，如终止或忽略。
- **Unblockable signals**：某些信号（如 SIGKILL）无法被捕获或忽略，它们直接终止进程。

在 Go 应用启动时，**Go 运行时**自动处理常见的终止信号，如 SIGINT、SIGTERM 和 SIGHUP。其中，最常用于优雅关闭的信号是：

- **SIGTERM**：请求优雅退出，Kubernetes 通常是发送该信号终止该程序；
- **SIGINT**：中断，用户通过 Ctrl+C 中断进程时触发；
- **SIGHUP**：挂断，用于通知应用程序重新加载配置。

>[!NOTE] Go 如何终止程序
>当 Go 应用程序收到 SIGTERM 时，Go 运行时会通过内置的信号处理器捕获它，首先检查是否注册了自定义处理器。如果没有，运行时会暂时禁用自定义处理器，并再次向应用程序发送相同的信号 (SIGTERM)。此时，操作系统会使用默认行为终止进程。

在 Go 中，你可以通过 os/signal 包注册自定义信号处理器来覆盖默认的信号处理行为。以下是一个处理 SIGINT 和 SIGTERM 信号的示例：

```go
func main() {
  signalChan := make(chan os.Signal, 1)
  signal.Notify(signalChan, syscall.SIGINT, syscall.SIGTERM)

  // 其他初始化工作

  <-signalChan

  fmt.Println("收到终止信号，正在关闭…")
}
```

signal.Notify 告诉 Go 运行时将指定的信号发送到自定义的信号通道，而不是使用默认的终止行为。这样，你可以手动处理信号并避免程序自动终止。

使用容量为 1 的缓冲通道是一种可靠的信号处理方式。Go 内部通过 select 语句将信号发送到通道。如果缓冲通道有空间，信号会被发送；如果满了，则会丢弃信号。如果使用无缓冲通道，由于信号必须被接收后才能继续执行，在应用初始化期间如果还没有准备好接收信号，可能会错过信号。若将缓冲区设置为大于 1，则可以捕获多个信号，但这通常不必要，因为一个信号就应该触发优雅退出。更大的缓冲区还可能导致在按下多个 Ctrl+C 后，程序无法立即强制退出，从而影响用户的操作体验。

当你多次按下 `Ctrl+C` 时，它不会自动终止应用。第一次按下 `Ctrl+C` 会向前台进程发送一个 `SIGINT` 。再次按下通常发送另一个 `SIGINT` ，而非 `SIGKILL` 。大多数终端（如 bash 或其他 Linux shell）不会自动升级信号。如果想强制停止，必须手动使用 `kill -9` 发送 `SIGKILL` 。

这对于本地开发来说并不理想，用户可能希望第二个 `Ctrl+C` 强制终止应用。因此，可以在接收到第一个信号后立即使用 `signal.Stop` 来阻止应用继续监听后续信号。

```go
func main() {
  signalChan := make(chan os.Signal, 1)
  signal.Notify(signalChan, syscall.SIGINT)

  <-signalChan
  signal.Stop(signalChan) // 停止监听后续信号，没有这行，该程序无法被Ctrl+C终止
  select {}               // 一直等待，出现新信号就终止
}
```

从 Go 1.16 开始，可以通过使用 `signal.NotifyContext` 来简化信号处理，它将信号处理与上下文取消绑定在一起：

```go
ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
defer stop() // 无论怎么退出，都停止监听后续信号（用户没发信号，程序崩溃的情况）

// Setup tasks here

<-ctx.Done()
stop()   // 停止对监听后续信号（主动执行）
```

在调用 `ctx.Done()` 之后，您仍应调用 `stop()` 以允许第二个 `Ctrl+C` 强制终止应用程序。

## 2 超时感知

了解应用程序在收到终止信号后的**关闭宽限期**至关重要，必须确保所有清理逻辑（包括处理剩余请求和释放资源）在此期间完成；最佳实践是预留约 20% 的时间作为安全边际（例如在 30 秒宽限期内目标在 25 秒完成），以可靠地防止程序在清理结束前被强制终止，避免数据丢失或不一致。

>[!NOTE] 关闭宽限期
>当应用程序被要求停止时，例如在 Kubernetes 环境中，K8s 会发送像 `SIGTERM` 这样的终止信号，程序会获得一个**关闭宽限期**（默认为 30 秒，可通过配置更改），应用程序必须在此时间内完成所有关闭操作并自行退出；如果超过这个设定的宽限期仍未退出，操作系统或容器编排平台（如 Kubernetes）将发送**无法被程序捕获或处理的强制信号 `SIGKILL`** 来立刻终止进程，这可能导致未完成的工作丢失或状态不一致。

## 3 停止接受新请求

当使用 `net/http` 时，可以通过调用 `http.Server.Shutdown` 方法来处理优雅关闭。该方法会停止服务器接受新连接，并等待所有活跃请求完成后再关闭空闲连接。

然而，在在 Kubernetes 这样的环境中，即使你的 Pod 被标记为终止 (terminating)，负载均衡器或 Service Controller 将流量从这个 Pod 移除是需要时间的。这段时间内，可能仍然有少量新的请求被路由到这个 Pod。如果你的程序仅仅在收到终止信号后立即调用 `Shutdown`，那么这些晚到的请求就会因为监听器已关闭而收到 "connection refused" 错误，这不是一个友好的用户体验，可能导致客户端错误。

```go
var isShuttingDown atomic.Bool // 使用原子操作保证并发安全

func readinessHandler(w http.ResponseWriter, r *http.Request) {
    // 检查关闭标志
    if isShuttingDown.Load() {
        // 如果正在关闭，返回服务不可用 (503)
        w.WriteHeader(http.StatusServiceUnavailable)
        w.Write([]byte("shutting down"))
        return
    }

    // 否则，返回正常 (200)，表示就绪
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("ok"))
}
```

因此，为了避免这种情况，优雅关闭的推荐策略：先失效就绪探针，再关闭服务：

1. **收到终止信号时 (SIGTERM 等):** 不要立即调用 `http.Server.Shutdown`；
2. **设置一个内部标志:** 在程序内部标记自己 " 正在关闭 "；
3. **修改 Readiness Probe 逻辑:** 让你的就绪探针处理器检查这个内部标志；
4. **Kubernetes 做出响应:** 检测到探针失败后，Kubernetes 会将 Pod 从 Endpoints 中移除；
5. **等待流量排空:** 在就绪探针开始失败后，程序需要**暂停**一小段时间等待流量排空；
6. 调用 `http.Server.Shutdown`；
7. **最终退出:** 关闭宽限期到了之后，k8s 发送 `SIGKILL` 确保终止。

>[!NOTE] 就绪探针
>就绪探针（Readiness Probe）是 Kubernetes 用来判断一个容器实例（Pod）**是否已经准备好接收流量**的一种机制。它通过定期执行你配置的检查（HTTP 请求、TCP 连接、命令执行等）来判断健康状态。
> - 探针成功 (Pass): Kubernetes 认为 Pod 是 " 就绪 " 的，会将这个 Pod 的 IP 地址添加到对应的 Service 的 Endpoints 列表中，负载均衡器就会将流量路由到它。
> - 探针失败 (Fail): Kubernetes 认为 Pod " 未就绪 "，会把这个 Pod 的 IP 地址从 Service 的 Endpoints 列表中移除，负载均衡器就不会再将流量路由到它。

## 4 处理待处理请求

既然我们正在优雅地关闭服务器，就需要根据你的停机预算选择一个超时时间：

```go
ctx, cancelFn := context.WithTimeout(context.Background(), timeout)
err := server.Shutdown(ctx)
```

`server.Shutdown(ctx)` 函数只有在以下两种情况下才会返回（停止阻塞）：

1. **所有待处理请求都已完成**。服务器成功等待了所有活动连接上的请求处理完毕，并且关闭了空闲连接。这是理想的优雅关闭；
2. **传递给 `Shutdown(ctx)` 的 Context 超时了**。如果在超时时间内，仍然有请求没有处理完成，那么服务器会放弃继续等待，并**强制关闭**所有剩余的活动连接。

无论哪种情况，Shutdown 只有在服务器完全停止处理请求后才会返回，这也要求处理程序必须快速且具备上下文感知的能力。否则，在第二种情况下，处理过程中被中断，从而导致部分写入、数据丢失、状态不一致、未关闭的事务或数据损坏等问题。

因此，当你在优雅关闭 HTTP 服务器时，为 `server.Shutdown` 提供一个带有合理超时的 Context 是必要的。更重要的是，你的所有请求处理器都必须是 " 快速且**Context-aware**" 的。这意味着它们不仅要高效执行，还应该能够感知并响应来自 Context 的取消信号（例如通过检查 `ctx.Done()`），以便在超时发生前能够尽力完成或回滚当前操作，避免被强制中断带来的风险。有以下两种方案：

### 4.1 使用 Context 中间件注入取消逻辑

这是一种为每个独立的请求创建一个带有取消功能的 Context 的方法。通过编写一个中间件，对于每个到来的 HTTP 请求，这个中间件都会基于原始请求的 Context 创建一个新的、带有取消功能的子 Context，这个子 Context 会关联到表示服务器正在关闭的全局信号通道上，当这个通道接收到信号，所有由这个中间件创建的、关联到此通道的 Context 都会被关闭。

```go
func WithGracefulShutdown(next http.Handler, cancelCh <-chan struct{}) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        ctx, cancel := WithCancellation(r.Context(), cancelCh)
        defer cancel()

        r = r.WithContext(ctx)
        next.ServeHTTP(w, r)
    })
}
```

### 4.2 使用 BaseContext 为提供全局 Context

这是 `net/http` 包提供的另一种机制，允许你为服务器的所有连接设置一个**基础的、全局共享**的 Context。

```go
ongoingCtx, cancelFn := context.WithCancel(context.Background())
server := &http.Server{
    Addr: ":8080",
    Handler: yourHandler,
    BaseContext: func(l net.Listener) context.Context {
        return ongoingCtx
    },
}

// 服务器收到关闭信号并开始执行关闭流程
cancelFn()
time.Sleep(5 * time.Second) // 等待一段时间，保证 cancel 完
```

无论是 `server.Shutdown` 的 Context 还是通过中间件或 `BaseContext` 传播的关闭 Context，只有当你的业务逻辑函数和所使用的第三方库真正**检查并响应 Context 的取消信号时，才会有意义！**

如果你在 Handler 或其调用的函数中使用了会阻塞且不接受 Context 参数的操作（例如简单的 `time.Sleep(duration)`、不带 Context 的文件读写、不带 Context 的网络 I/O 或数据库查询），那么即使 Context 被取消了，这些操作也会继续阻塞执行，直到它们自己完成，从而可能导致 Handler 无法在 `server.Shutdown` 的 Context 超时前返回，最终被强制中断。

因此，可以自己实现或者选用 Context 感知的方法，如我们可以封装如下版本的 Sleep 函数，

```go
func Sleep(ctx context.Context, duration time.Duration) error {
    select {
    case <-time.After(duration): // 等待指定时长
        return nil // 时长到了，正常返回
    case <-ctx.Done(): // Context 被取消了
        return ctx.Err() // 返回 Context 的错误（通常是 context.Canceled 或 context.DeadlineExceeded）
    }
}
```

**普遍适用的优雅关闭原则**

不仅仅是 HTTP 服务器，几乎所有需要处理外部请求、连接或任务的应用程序都适用相同的优雅关闭核心原则：

- **停止接受新的工作:** 不再监听新的连接、不再从队列读取新消息、不再接受新的请求。
- **等待现有工作完成:** 给正在处理中的连接、请求或任务一段设定的时间（宽限期）来完成。
- **在宽限期后强制终止:** 如果在设定的时间内未能完成，则进行强制清理或终止，以避免无限期阻塞。

>[!NOTE] server.Close()
>`server.Close()` 会**立即**关闭服务器的监听器并强制关闭所有**活跃**的网络连接，不等待请求完成。`Close` 只处理网络连接。如果你的 Handler 启动了长时间运行的、**不涉及网络**的后台任务，`Close` 不会等待它们，它们可能会在后台继续运行，直到进程被操作系统终止。

## 5 释放关键资源

在应用程序启动优雅关闭流程（通常在收到终止信号后）时，一个常见的错误是立即释放其持有的关键资源。这种做法是不可取的，因为此时可能仍有待处理的请求或正在执行的处理程序依赖于这些资源。正确的策略是延迟这些资源的清理，直到 HTTP 服务器的 `Shutdown` 方法返回（表示所有待处理请求已处理完毕或设定的关闭超时已到）之后再进行。尽管操作系统会在进程终止时自动回收大多数资源，例如 Go 分配的内存、打开的文件描述符以及操作系统级别的进程句柄等，然而，对于以下类型的关键资源，为了确保数据完整性、下游系统状态一致性以及资源的及时有效释放，进行**显式清理**是必不可少的：

- **数据库连接：** 在关闭连接池之前，必须妥善处理所有未提交的事务（执行提交或回滚），确保数据库状态的一致性，并避免数据库端因连接异常终止而产生的资源积压或恢复问题。
- **消息队列/代理客户端：** 通常需要执行特定的关闭操作，例如刷新内部缓冲的消息、提交消费者的偏移量或向代理发送客户端正常下线的信号。这有助于防止消息丢失、重复处理或在分布式系统中引起不必要的重新平衡问题。
- **外部服务连接：** 主动关闭与外部服务的客户端连接（如 gRPC 客户端、Redis 客户端等），有助于这些外部系统更快地检测到断开并清理其关联资源，这比依赖于 TCP 连接超时检测更为及时和高效。

一个普遍遵循的原则是，按照组件在应用程序启动时初始化的**逆序**来执行关闭操作，以正确处理组件间的依赖关系。Go 语言的 `defer` 语句非常适合管理这类逆序清理任务。此外，对于某些需要特殊处理的组件，例如需要将内存中的缓存数据持久化到磁盘，则需要设计**定制的关闭例程**来确保数据在程序最终退出前被妥善保存。

## 6 总结

这是一个优雅关闭机制的完整示例。它采用扁平、直白的结构编写，以便于理解。您可以根据需要自定义以适应自己的应用程序。

```go
const (
	_shutdownPeriod      = 15 * time.Second
	_shutdownHardPeriod = 3 * time.Second
	_readinessDrainDelay = 5 * time.Second
)

var isShuttingDown atomic.Bool

func main() {
	// Setup signal context
	rootCtx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	// Readiness endpoint
	http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		if isShuttingDown.Load() {
			http.Error(w, "Shutting down", http.StatusServiceUnavailable)
			return
		}
		fmt.Fprintln(w, "OK")
	})

	// Sample business logic
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		select {
		case <-time.After(2 * time.Second):
			fmt.Fprintln(w, "Hello, world!")
		case <-r.Context().Done():
			http.Error(w, "Request cancelled.", http.StatusRequestTimeout)
		}
	})

	// Ensure in-flight requests aren't cancelled immediately on SIGTERM
	ongoingCtx, stopOngoingGracefully := context.WithCancel(context.Background())
	server := &http.Server{
		Addr: ":8080",
		BaseContext: func(_ net.Listener) context.Context {
			return ongoingCtx
		},
	}

	go func() {
		log.Println("Server starting on :8080.")
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("ListenAndServe: %v", err)
		}
	}()

	// Wait for signal
	<-rootCtx.Done()
	stop()
	isShuttingDown.Store(true)
	log.Println("Received shutdown signal, shutting down.")

	// Give time for readiness check to propagate
	time.Sleep(_readinessDrainDelay)
	log.Println("Readiness check propagated, now waiting for ongoing requests to finish.")

	shutdownCtx, cancel := context.WithTimeout(context.Background(), _shutdownPeriod)
	defer cancel()
	err := server.Shutdown(shutdownCtx)
	stopOngoingGracefully()
	if err != nil {
		log.Println("Failed to wait for ongoing requests to finish, waiting for forced cancellation.")
		time.Sleep(_shutdownHardPeriod)
	}

	log.Println("Server shut down gracefully.")
}
```
