---
categories:
- Golang
date: '2025-06-28T21:53:07+08:00'
draft: false
slug: ccbc66d4
summary: RPC与gRPC核心概念解析及实战示例
tags:
- gRPC
title: Go 远程过程调用标准库与 GRPC
---

## 1 RPC 核心概念与通信基础

**RPC（Remote Procedure Call）远程过程调用** 是一种使程序可以调用另一台机器上函数的通信协议，开发者可以像调用本地函数一样透明地调用远程服务。这种抽象极大简化了分布式系统中服务之间的交互逻辑，是微服务架构中最基础的通信手段。

>[!NOTE]
> **RPC（Remote Procedure Call）**：远程过程调用是一种封装通信细节的机制，允许开发者调用远程服务如同本地函数。常见实现包括 gRPC、Thrift、Dubbo 等。它屏蔽了底层网络传输、数据序列化等复杂性，是构建现代微服务系统的基础。
>
> **IPC（Inter-Process Communication）**：进程间通信用于同一主机内多个进程的数据交换与协同，方式包括管道、消息队列、共享内存、信号、Socket 等。IPC 更多用于单机多进程协作，RPC 更适合跨网络服务交互。

在软件系统从单体架构向微服务架构演化的过程中，不同服务部署在不同主机或容器中，模块之间无法通过函数调用直接通信。此时，就需要一种通信机制，**既能跨进程、跨主机调用远程服务，又不需要开发者处理底层细节**——这就是 RPC 诞生的背景。

### 1.1 RPC 核心组成与工作流程

- **客户端存根（Client Stub）**：负责将客户端的函数调用请求序列化成网络消息，并发送给服务端。
- **服务端骨架（Server Stub）**：负责接收客户端的请求，反序列化消息，调用相应的服务函数，并将结果序列化后返回给客户端。
- **序列化协议**：定义了数据如何序列化和反序列化，常见的序列化协议有 JSON、Protobuf 等。
- **传输协议**：定义了网络消息如何传输，常见的传输协议有 TCP、HTTP、gRPC（基于 HTTP/2）等。

## 2 最简 RPC 示例：HelloWorld

### 2.1 标准库实现

Go 语言标准库中提供了一个内置的 RPC 包 `net/rpc`，用于实现远程过程调用。它基于自定义的二进制协议，支持通过原始 TCP 或 HTTP 通信。不过，`net/rpc` 不支持 HTTP/2，因此无法享受到如多路复用、流量控制等高级特性，性能上也相对有限，适合学习和内部系统使用。

首先，我们定义一个 HelloService 类型，并在其中实现一个符合 RPC 规范的方法 SayHello：

```go
type HelloService struct {}

func (p *HelloService) SayHello(request string, reply *string) error {
    *reply = "Hello World:" + request
    return nil
}
```

Go 的 RPC 方法必须满足以下规范：方法必须是**导出方法**（首字母大写）。方法只能有**两个可序列化**的参数；第一个参数是请求参数，类型必须是导出或内建类型；第二个参数是响应参数的**指针类型**；并且必须返回一个 error 类型。

定义好服务方法后，我们需要将 HelloService 注册为 RPC 服务，并在服务端监听客户端的请求：

```go
func main() {
    // 注册 RPC 服务，将 HelloService 的所有方法注册进默认 RPC 服务中
    rpc.RegisterName("HelloService", new(HelloService))
    // 启动 TCP 监听
    listener, _ := net.Listen("tcp", ":1234")
    defer listener.Close()
    for {
        // 接受客户端连接
        conn, _ := listener.Accept()
        // 为每个连接启动独立 goroutine 提供服务，支持并发处理
        go rpc.ServeConn(conn)
    }
}
```

- `rpc.RegisterName`：将对象注册为一个 RPC 服务，并允许我们自定义服务名称（如 "HelloService"）。相比 `rpc.Register`（服务名由反射获取类型名），RegisterName 更灵活，适用于需要避免命名冲突或提升可读性的场景。
- `rpc.ServeConn`：在一个连接上处理所有来自客户端的 RPC 请求，直到该连接关闭。它是**阻塞式**的，因此我们需要为每个连接启动一个新的 goroutine，以支持并发请求处理。

接下来，服务器需要通过调用 `net.Listen` 方法来监听指定的网络端口，从而等待客户端的连接请求。一旦成功监听端口并建立连接，服务器会进入连接处理阶段。此时，可以启动一个独立的 Goroutine，调用 `rpc.ServeConn(conn)` 来处理每个客户端的 RPC 请求。

`rpc.ServeConn` 是一个专用于在单个网络连接上运行 `DefaultServer`（默认 RPC 服务器）的函数。它的核心职责是管理客户端与服务器之间的通信，直到客户端断开连接为止。需要注意的是，`ServeConn` 是一个阻塞式函数，这意味着它会持续运行以处理该连接上的所有请求，直到连接终止。由于它仅处理单一连接，因此在高并发场景中，通常需要为每个连接启动一个 Goroutine 来实现并发处理。

客户端通过 rpc.Dial 与服务端建立连接后，便可调用远程方法：

```go
func main() {
	// 连接服务端，Dial 的含义是拨号/建立连接
	conn, _ := rpc.Dial("tcp", "localhost:1234")
	// 构建请求参数
	var reply string
	// 同步调用远程方法
	// 第一个参数是用点号连接的 RPC 服务名字和方法名字
	// 第二和第三个参数分别我们定义 RPC 方法的两个参数。
	_ = conn.Call("HelloService.SayHello", "hello", &reply)
	fmt.Println(reply)
}
```

- `rpc.Dial`：拨号连接远程 RPC 服务，返回一个 Client 实例。
- `Call` 方法：发起一个同步 RPC 调用，第一个参数是 " 服务名.方法名 " 的形式，其余两个参数对应服务端定义方法的两个参数。

虽然 `Client.Call` 是一个同步调用接口，其内部实现却是基于异步机制 `Client.Go` 封装的：

```go
func (client *Client) Call(serviceMethod string, args interface{}, reply interface{}) error {
    // 发起异步调用
    call := client.Go(serviceMethod, args, reply, make(chan *Call, 1))
    // 等待调用完成
    completedCall := <-call.Done
    // 返回调用结果中的错误
    return completedCall.Error
}
```

其流程为：

1. `Client.Go` 启动一个异步调用，并返回一个 Call 对象；
2. 该 Call 对象中包含一个 Done 通道，表示调用完成；
3. `Client.Call` 通过读取 Done 通道，实现同步阻塞等待；
4. 返回调用结果或错误。

这种设计既保证了同步调用的简洁性，也为底层的异步调用提供了扩展空间。如果需要完全异步的调用流程，用户可以直接使用 `Client.Go` 并自行监听 `Call.Done` 获取返回值。

### 2.2 JSON 编码实现

Go 语言标准库中的 `net/rpc` 默认采用 Gob 编码格式进行数据序列化与传输。Gob 是 Go 特有的二进制编码格式，虽然效率较高、适合 Go 内部使用，但由于缺乏跨语言支持，导致其他语言难以直接调用基于 Gob 编码实现的 RPC 服务。

Gob 是 Go 标准库中的一种高效二进制序列化格式，位于 `encoding/gob` 包中，适用于将 Go 中的结构体等数据编码为字节流，并在网络传输或本地存储后再解码还原。其优势在于**支持 Go 中复杂的数据类型**且**编码紧凑，性能高效**。但其局限也非常明显：**Gob 是 Go 独有的格式，其他语言无法解析 Gob 编码的数据**，这使得 Go 的默认 RPC 服务无法直接被其他语言调用。

为了实现跨语言调用，可以替换默认的 Gob 编码方式为通用的 JSON 编码格式。Go 的 RPC 框架天然支持插件式的编解码器，并且基于抽象的 `io.ReadWriteCloser` 接口构建通信，因此我们可以非常方便地将编码器替换为 JSON 版本。

Go 标准库提供了 `net/rpc/jsonrpc` 包，用于支持 JSON-RPC 协议。我们只需要将服务端的 `rpc.ServeConn` 替换为 `rpc.ServeCodec`，并使用 `jsonrpc.NewServerCodec` 即可完成替换；客户端亦可通过 `rpc.NewClientWithCodec` 进行配套调用。

```go
// 服务端：使用 JSON 编码器替代默认 Gob 编码器
go rpc.ServeCodec(jsonrpc.NewServerCodec(conn))

// 客户端：建立 TCP 连接并指定使用 JSON 编码器
conn, err := net.Dial("tcp", "localhost:1234")
client := rpc.NewClientWithCodec(jsonrpc.NewClientCodec(conn))
```

下面，我们使用 nc 创建一个普通的 TCP 服务器代替服务端，分别查看采用 JSON 编码和 Gob 编码的客户端发送过来的请求。对于 JSON 编码，其中 method 部分对应要调用的 rpc 服务和方法组合成的名字，params 部分的第一个元素为参数，id 是由调用端维护的一个唯一的调用编号。

![image.png](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/20250122211328.png)

知道了数据格式后，运行 RPC 服务端，就可以向服务器发送 JSON 数据包模拟 RPC 方法调用，可以获得响应数据的格式。

```shell
echo -e '{"method":"HelloService.Hello","params":["hello"],"id":1}' | nc localhost 1234
```

虽然 Go 的 `net/rpc` 也支持通过 `rpc.HandleHTTP` 在 HTTP 上提供服务，但其 HTTP 接口依然使用 Gob 编码，不支持 JSON 编码方式。因此，为了让服务能够通过浏览器、跨语言客户端（如 Python）访问，我们可以手动将 HTTP 请求适配为 RPC 通信。

我们使用一个 `http.HandleFunc` 将 HTTP 请求的 Body 和 ResponseWriter 组合为 `io.ReadWriteCloser`，并使用 `rpc.ServeRequest` 搭配 JSON 编解码器进行处理：

```go
func main() {
    rpc.RegisterName("HelloService", new(HelloService))
    // 在 /jsonrpc 路径上配置一个 HTTP 处理函数
    http.HandleFunc("/jsonrpc", func(w http.ResponseWriter, r *http.Request) {
        // io.ReadWriteCloser 是一个接口，表示既可以读取又可以写入的对象
        // 将 HTTP 请求体（r.Body）作为读取端，将 HTTP 响应写入端（w）作为写入端
        // 使用匿名结构体封装 ReadCloser 和 Writer，组合成一个 ReadWriteCloser
        var conn io.ReadWriteCloser = struct {
            io.Writer
            io.ReadCloser
        }{
            ReadCloser: r.Body,
            Writer:     w,
        }
        // 基于 conn 创建一个 JSON 编解码器，并处理 RPC 请求
        rpc.ServeRequest(jsonrpc.NewServerCodec(conn))
    })
    http.ListenAndServe(":1234", nil)
}
```

此时，我们即可通过 HTTP 请求调用 JSON-RPC 服务：

```go
curl localhost:1234/jsonrpc -X POST \  
    --data '{"method":"HelloService.SayHello","params":["hello"],"id":0}'

{"id":0,"result":"Hello World:hello","error":null}
```

由于我们已将 RPC 服务暴露为标准的 HTTP + JSON-RPC 接口，因此可以非常容易地使用其他语言进行调用。以下是使用 Python 模拟客户端请求的示例代码：

```python
import requests
import json

url = "http://localhost:1234/jsonrpc"

payload = {
    "method": "HelloService.SayHello",
    "params": [{"Name": "Python HTTP Client"}],
    "id": 0
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, data=json.dumps(payload), headers=headers)
result = response.json()
message = result.get("result", {}).get("Message")
print("Message:", message)

```

## 3 RPC 编解码协议对比

在 Go 语言的标准库中，默认使用的是 gob 编码格式。这是一种专为 Go 应用设计的高效二进制序列化方案，位于 `encoding/gob` 包中。Gob 能将 Go 的数据结构高效地编码为字节流，并支持快速反序列化还原，非常适合在 Go 内部组件之间进行通信。

然而，Gob 也有明显的局限性：它是 Go 语言特有的编码格式，不具备跨语言兼容性。这意味着，若需使用其他语言（如 Python、Java）与 Go 的 RPC 服务进行交互，就无法直接使用 Gob 编码。这在多语言分布式系统中显然是不现实的。

为了解决跨语言通信问题，我们需要使用支持多语言的数据交换格式。常见的替代方案包括：

- **JSON**：人类可读性好、广泛支持、无需额外工具即可在多语言间使用，适合调试和轻量通信场景。但因其基于字符串表示，体积大、编码解析性能较低。
- **Protobuf**（Protocol Buffers）：由 Google 提出的一种高性能、紧凑的二进制序列化协议。它具备语言中立、平台中立和良好的向后兼容性，适用于构建高性能服务间通信系统，也是 gRPC 默认采用的序列化协议。

Protocol Buffers（简称 Protobuf）是一种结构化数据的序列化机制，适用于网络通信、配置、存储等场景。它以 .proto 文件定义数据结构和 RPC 服务接口，通过编译生成对应语言的类型和方法。

一个典型的 .proto 文件结构如下：

```proto
syntax = "proto3";

package helloworld;

// 指定生成的 Go 包路径
option go_package = "./proto/helloworld";

service Greeter {
  rpc SayHello (HelloRequest) returns (HelloReply);
}

message HelloRequest {
  string name = 1;
}

message HelloReply {
  string message = 1;
}
```

1. **syntax**：声明使用 Protobuf 版本（推荐 proto3）。
2. **message**：用于定义结构化数据类型，每个字段需分配唯一编号（1~536870911），编号用于高效序列化标识。
3. **service + rpc**：定义 RPC 接口，是 gRPC 支持远程调用的基础。
4. **option go_package**：指定生成代码的 Go 包路径，便于模块化管理。

Protobuf 核心的工具集是 C++ 语言开发的，在官方的 protoc 编译器中并不支持 Go 语言。要想从上面的文件生成对应的 Go 代码，需要安装相应的插件。

```shell
brew install protobuf               # 安装 protoc
go install google.golang.org/protobuf/cmd/protoc-gen-go@lates
# 添加 Go 插件路径到环境变量
export PATH="$PATH:$(go env GOPATH)/bin"
# 编译 proto 文件，生成 Go 代码
protoc --go_out=. --go-grpc_out=. hello.proto
```

执行后会生成两个文件：

- `helloworld.pb.go`（包含消息结构和字段序列化逻辑）
- `helloworld_grpc.pb.go`（包含 gRPC 客户端和服务端接口定义）

| **维度**    | **Gob**               | **JSON**      | **Protobuf**     |
| --------- | --------------------- | ------------- | ---------------- |
| **语言支持**  | Go 专用                 | 跨语言，天然支持      | 跨语言（官方多语言支持）     |
| **可读性**   | 二进制格式，不可读             | 文本格式，易读易调试    | 二进制格式，不可读        |
| **编码效率**  | 中等                    | 低（字符串处理开销大）   | 高                |
| **数据体积**  | 中（比 JSON 小）           | 最大            | 最小               |
| **开发成本**  | 零配置，Go 内置支持           | 零配置，Go 内置支持   | 需定义 .proto 并安装插件 |
| **兼容性支持** | 差（结构变动易出错）            | 一般            | 强（字段编号支持扩展）      |
| **依赖情况**  | 无需额外依赖                | 无需额外依赖        | 依赖 protoc 和插件    |
| **适用场景**  | Go 内部组件通信             | 对外开放接口、调试工具等  | 高性能服务间通信、微服务     |

通过对比可以发现，如果你的 RPC 服务只在 Go 语言内部使用，那么 Gob 是一种快速、简洁的选择。但在需要与其他语言协同的微服务架构中，JSON 是最易接入的方案，而 Protobuf 则在性能和灵活性上更具优势，是构建高性能服务的首选，gRPC 默认使用的就是 Protobuf。

## 4 gRPC 通信模式实战

在前文我们介绍了 Protobuf 的定义方式和序列化机制，它为跨语言的数据交换提供了高性能的基础。但如果我们要构建一套真正可扩展的服务间通信框架，仅有 Protobuf 并不足够。**我们还需要一套支持远程调用、连接管理、负载均衡、双向流等高级能力的通信系统**。

这正是 gRPC 所要解决的问题。

gRPC 是由 Google 开发的一种高性能、开源的通用 RPC 框架，基于 HTTP/2 和 Protobuf 实现。它不仅支持传统的一问一答式远程调用，还支持流式通信模式，非常适合构建微服务、移动端与后端通信等场景。

gRPC 提供了四种通信方式，分别覆盖了从简单调用到双向流的多种场景需求：

| **模式**                          | **客户端**   | **服务器**   |
| ------------------------------- | --------- | --------- |
| **Unary RPC（普通 RPC）**           | 发送单个请求    | 返回单个响应    |
| **Server Streaming RPC**        | 发送单个请求    | 返回多个响应（流） |
| **Client Streaming RPC**        | 发送多个请求（流） | 返回单个响应    |
| **Bidirectional Streaming RPC** | 发送多个请求（流） | 返回多个响应（流） |

**普通 RPC（Unary RPC）**

最常见的调用方式，客户端发送一个请求，服务器返回一个响应，语义类似于传统 HTTP 的请求 - 响应模型。

```go
// rpc GetUserInfo(GetUserRequest) returns (GetUserResponse);
func (s *server) GetUserInfo(ctx context.Context, req *GetUserRequest) (*GetUserResponse, error) {
    // 处理请求逻辑
    return &GetUserResponse{Username: "Tom"}, nil
}
```

**服务器流式 RPC（Server Streaming）**

客户端发送一个请求，服务端通过流的方式连续返回多个响应，常用于需要推送多条数据的场景，如日志输出、实时监控、分页加载等。

```go
// rpc ListUsers(ListUsersRequest) returns (stream ListUsersResponse);
func (s *server) ListUsers(req *ListUsersRequest, stream YourService_ListUsersServer) error {
    for _, user := range users {
        stream.Send(&ListUsersResponse{User: user})

    }
    return nil
}
```

**客户端流式 RPC（Client Streaming）**

客户端通过流方式发送多个请求，服务端在接收完所有请求后，统一返回一个响应。常见于上传日志、批量导入数据等应用。

```go
// rpc UploadLogs(stream UploadLogsRequest) returns (UploadLogsResponse);
func (s *server) UploadLogs(stream YourService_UploadLogsServer) error {
    for {
        req, err := stream.Recv()
        if err == io.EOF {
            return stream.SendAndClose(&UploadLogsResponse{Message: "Upload complete"})
        }
    }
}
```

**双向流式 RPC（Bidirectional Streaming）**

```go
// rpc Chat(stream ChatMessage) returns (stream ChatMessage);
func (s *server) Chat(stream YourService_ChatServer) error {
    for {
        msg, err := stream.Recv()
        if err == io.EOF {
            return nil
        }
        stream.Send(&ChatMessage{Content: "Echo: " + msg.Content})
    }
}
```

与普通 RPC 不同，流式 RPC 方法的关键点在于：

- 不再通过返回值传递响应对象，而是通过函数参数传入的 stream 进行读写；
- 服务端可通过 `stream.Send()` 持续发送响应，或通过 `stream.Recv()` 持续接收请求；
- 方法最终返回一个 error，标识连接是否正常结束。

流式通信中，客户端和服务端均可发起关闭：

```go
// 客户端调用 CloseSend() 关闭发送流，服务器 Recv() 方法返回 io.EOF
stream.CloseSend()
// 服务器返回 nil 或 error，gRPC 运行时会关闭连接
return nil  // 正常关闭
return status.Errorf(codes.Internal, "Server error")  // 服务器错误
```

### 4.1 Unary RPC：HelloWorld

gRPC 使用 Protobuf 作为数据编解码格式，具备跨语言、高性能等优势。更重要的是，它通过 **proto 文件定义接口**，将客户端与服务端的**开发解耦**：两端只需依据统一的 proto 文件生成对应的代码，并各自实现（或调用）接口即可，无需手动对齐方法名、参数类型等细节。proto 文件天然就是一份良好的 **API 契约文档**。

在上文中我们已经给出了 HelloWorld 示例的 proto 文件，gRPC 插件生成了两部分代码：

- 服务端接口定义（如 GreeterServer）
- 客户端调用封装（如 GreeterClient）

```go
// 定义 server 结构体，实现 GreeterServer 接口
type server struct {
    // 内嵌 UnimplementedGreeterServer 可确保未来接口新增方法时不报编译错误
    pb.UnimplementedGreeterServer
}

// 实现 SayHello 方法 —— 这是一个 Unary RPC
func (s *server) SayHello(ctx context.Context, req *pb.HelloRequest) (*pb.HelloReply, error) {
    return &pb.HelloReply{Message: "Hello, " + req.Name}, nil
}

// 编译期接口检查，确保 server 实现了 GreeterServer 接口
// 原理：将 server 类型转为接口接受的指针类型，但值是 nil，不实际分配内存
var _ pb.GreeterServer = (*server)(nil)

func main() {
	listener, err := net.Listen("tcp", ":1234")
	if err != nil {
		log.Fatalf("监听失败: %v", err)
	}
	// 创建新的gRPC服务器实例
	s := grpc.NewServer()
	// 注册Greeter服务实现
	pb.RegisterGreeterServer(s, &server{})
	log.Println("gRPC 服务器启动…")
	// 启动服务器，开始处理请求
	if err := s.Serve(listener); err != nil {
		log.Fatalf("启动失败: %v", err)
	}
}
```

客户端的实现也很简单：

```go
func main() {
    // 建立到服务器的连接，使用不安全凭证（仅用于开发环境）
	conn, err := grpc.NewClient("localhost:1234", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("连接失败: %v", err)
	}
	defer conn.Close()
    // 创建Greeter客户端
	client := pb.NewGreeterClient(conn)
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
    // 调用SayHello RPC方法
	resp, err := client.SayHello(ctx, &pb.HelloRequest{Name: "gRPC Client"})
	if err != nil {
		log.Fatalf("调用失败: %v", err)
	}
	fmt.Println("服务端返回:", resp.Message)
}
```

 虽然 gRPC 的接口调用是同步的（即每次调用会阻塞直到响应返回），但它是基于 HTTP/2 协议实现的，支持连接复用与多路复用。再结合 Go 的 Goroutine 并发机制，我们可以在多个协程中**并发发起多个同步调用**，实现高并发的请求处理。

### 4.2 Server-side & Client-side Streaming：PubSub

在本节中，我们以经典的 **发布 - 订阅（Pub/Sub）模型** 为例，演示如何使用服务端流式 gRPC 构建一个简单的消息分发系统。

Pub/Sub 是一种消息解耦模型，发布者向某个主题（Topic）发布消息，订阅者只需要订阅该主题即可接收对应消息。发布者和订阅者不直接通信，消息通过中间层（如消息队列或 Redis）转发。

在 proto 文件中，我们设计了两个 gRPC 方法：

```proto
service PubSub {
  // 客户端流式 RPC，允许客户端持续发送多个发布请求（发布消息）。
  rpc Publish (stream PublishRequest) returns (PublishResponse); 
  // 服务端流式 RPC，允许客户端发送一次订阅请求后，持续接收服务端推送的消息。
  rpc Subscribe (SubscribeRequest) returns (stream SubscribeResponse);
}
```

在服务端，我们使用 **Redis Pub/Sub** 机制作为消息的中转通道：

- Publish 方法通过 Redis PUBLISH 命令将消息推送到指定 topic；
- Subscribe 方法使用 Redis SUBSCRIBE 命令监听指定 topic，当有新消息发布时，实时转发给 gRPC 客户端。

服务端的核心逻辑如下：

```go
func (s *PubSubService) Subscribe(req *pb.SubscribeRequest, stream pb.PubSub_SubscribeServer) error {
	pubsub := s.redisClient.Subscribe(stream.Context(), req.Topic)
	defer pubsub.Close()

	ch := pubsub.Channel()
	for {
		select {
		case msg := <-ch:
			stream.Send(&pb.SubscribeResponse{Message: msg.Payload})
		case <-stream.Context().Done():
			return nil // 客户端断开连接
		}
	}
}
```

订阅者只需发起一次订阅请求，即可持续接收来自服务端的推送消息：

```go
stream, err := client.Subscribe(ctx, &pb.SubscribeRequest{Topic: "news"})
for {
    resp, err := stream.Recv()
    fmt.Println("接收到消息:", resp.Message)
}
```

发布者通过客户端流式 RPC 不断向服务端发送消息，服务端会将其发布到 Redis，从而触发分发：

```go
stream, _ := client.Publish(ctx)
for _, msg := range messages {
    stream.Send(&pb.PublishRequest{Topic: "news", Message: msg})
}
stream.CloseAndRecv() // 关闭发送端并等待响应
```

![image.png](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/20250516210341.png)

### 4.3 Bidirectional Streaming：goChat

在本节中，我们实现了一个基于 **gRPC 双向流（Bidirectional Streaming）** 的简易聊天室系统 —— goChat。该系统支持多个客户端同时在线，每个客户端既可以流式地发送消息，也可以实时接收服务端推送的消息，实现了一个简洁但功能完整的聊天体验。

gRPC 的双向流式 RPC 模式允许客户端和服务端之间建立一个持续存在的连接，双方都可以在连接存续期间任意时刻读写消息。这种模式非常适用于实时通讯场景，如聊天室、在线游戏、音视频通信等。与单向流不同，双向流强调「对等通信」：无论客户端还是服务端，谁都可以主动发送消息。

服务端主要职责包括：

- 接收客户端的连接请求并识别身份；
- 管理客户端连接的流；
- 转发消息到指定客户端或广播到其他客户端；
- 在用户断开连接后清理资源。

```go
// rpc Chat(stream ChatMessage) returns (stream ChatMessage) {}
func (s *server) Chat(stream pb.ChatService_ChatServer) error {
	firstMsg, _ := stream.Recv()
	... // 注册用户
	
	// 如果有初始消息（如“加入聊天室”），立即处理
	if firstMsg.Content != "" {
		s.handleMessage(firstMsg, username)
	}
	// 持续接收消息
	for {
		msg, err := stream.Recv()
		if err == io.EOF {
			break
		}
		s.handleMessage(msg, username)
	}
    ... // 用户断开连接
	return nil
}

func (s *server) handleMessage(msg *pb.ChatMessage, senderUsername string) {
    if msg.Targetname == "" {
        for uname, clientStream := range s.clients {
            _ = clientStream.Send(msg)
        } else {
            targetStream, ok := s.clients[msg.Targetname]
            _ = targetStream.Send(msg)
        }
    }
}
```

客户端使用双向流与服务端通信，整个逻辑分为两个并发 goroutine：

1. **接收消息（stream.Recv）**：从服务端读取消息并输出到终端；
2. **发送消息（stream.Send）**：从用户输入读取内容并发送给服务端。

客户端连接服务器并发起双向流后，首先发送标识身份的初始消息，然后开启两个协程读写消息：

```go
// 接收消息线程
go func() {
	for {
		msg, _ := stream.Recv()
		if msg.Targetname == "" {
			fmt.Printf("[Broadcast] %s: %s\n", msg.Username, msg.Content)
		} else {
			fmt.Printf("[Private from %s]: %s\n", msg.Username, msg.Content)
		}
	}
}()
// 发送消息线程
go func() {
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		input := scanner.Text()
		// 处理私聊 @user msg 或普通广播
		stream.Send(&pb.ChatMessage{…})
	}
}()
```

![image.png](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/20250516233359.png)

### 4.4 服务发现与负载均衡

在微服务架构中，服务实例的动态变化是一个常见的挑战。如何让客户端找到可用的服务实例，并在多个实例之间分配请求，是实现高可用和可伸缩的关键。gRPC 提供了 `resolver` 机制来解决服务发现的问题，而结合像 etcd 这样的分布式键值存储，我们可以构建一个健壮的服务注册与发现中心，并轻松实现负载均衡。

服务注册是服务发现的第一步，服务实例启动后需要向注册中心注册自己的地址信息。在我们的示例中，服务启动时会调用 `etcd.NewServiceRegistry` 创建一个注册器，并通过 `registry.Register` 方法将自己的服务名称、实例 ID 和监听地址注册到 etcd 中。

```go
// 注册到 etcd
registry, err := etcd.NewServiceRegistry(nil)
if err != nil {
    log.Fatalf("Failed to create registry: %v", err)
}
// 注册服务
ctx, cancel := context.WithCancel(context.Background())
defer cancel()
err = registry.Register(ctx, "greater-service", "instance-"+*port, "localhost:"+*port)
if err != nil {
    log.Fatalf("Failed to register service: %v", err)
}
```

`etcd.Register` 方法会在 etcd 中以 `/services/服务名称/实例ID` 为键，服务地址为值，创建一个带有租约（Lease）的条目。租约的作用是当服务实例下线或出现异常时，etcd 会自动删除对应的服务地址，从而实现服务实例的自动注销。`keepAlive` 机制则会定期续签租约，保持服务注册信息的有效性。

gRPC 客户端在发起请求前，需要知道目标服务的具体地址。这就是服务发现的任务。gRPC 提供了 `resolver` 接口，允许我们自定义服务地址的解析逻辑。

在我们的实现中，客户端通过 `etcd.NewServiceDiscovery` 创建一个服务发现实例，并在创建 gRPC 连接时指定使用自定义的 etcd resolver。

```go
// 创建服务发现实例
discovery, err := etcd.NewServiceDiscovery(nil)
if err != nil {
    log.Fatalf("Failed to create discovery: %v", err)
}

// 获取服务连接
conn, err := discovery.GetConnection(context.Background(), "greater-service")
if err != nil {
    log.Fatalf("Failed to connect to service: %v", err)
}
```

`etcd.GetConnection` 方法会注册一个实现了 `resolver.Builder` 接口的 `EtcdResolverBuilder`。当 gRPC 客户端需要解析服务地址时，会调用 `Build` 方法创建一个 `EtcdResolver` 实例。`EtcdResolver` 会监听 etcd 中对应服务名称前缀的键值变化，并将获取到的服务地址列表通过 `cc.UpdateState` 更新给 gRPC 客户端连接。

更具体的，还是去看代码吧！

## 5 深入理解 gRPC 底层原理

gRPC 是由 Google 开源的一款高性能、通用的远程过程调用（RPC）框架。它构建在 HTTP/2 之上，使用 Protocol Buffers（protobuf）作为默认的数据序列化协议，具备高效、强类型、多语言支持等优势，广泛应用于现代微服务系统中。为了更好地理解 gRPC 的强大能力，有必要从底层架构、通信机制、负载均衡策略、安全机制等方面进行深入剖析。

### 5.1 gRPC 架构分层

![image.png](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/20250124164401.png)

gRPC 的设计哲学在于清晰的分层，这使得框架既能提供强大的抽象能力，让开发者专注于业务逻辑，又能深入底层进行性能优化。其主要分层如下：

1. **应用层（Application Layer）**：这一层是开发者直接交互的层面。你在这里实现具体的业务服务（Server）或调用服务（Client）。开发者通过调用 gRPC 根据 `.proto` 文件自动生成的代码，以编程的方式进行远程服务调用，无需关心底层的网络通信细节。
2. **API 层（API Layer）**：这是 gRPC 框架提供给开发者的接口层。通过 protobuf 定义服务和消息格式后，gRPC 工具会生成客户端和服务端的接口代码。这些代码是连接应用层和底层实现的桥梁，极大地简化了 RPC 调用流程。
3. **Stub 层（Stub Layer）**：Stub（存根）层负责处理数据在客户端和服务端之间的具体传输细节。它包括了请求消息的序列化（使用 Protobuf 等）、压缩、以及响应消息的反序列化、解压缩和错误处理等。这一层将底层的数据处理逻辑封装起来，对上层应用层透明。
4. **传输层（Transport Layer）**：gRPC 的高性能很大程度上归功于其基于 HTTP/2 的传输层。HTTP/2 提供了多路复用、流控制、头部压缩等关键特性。传输层负责将 Stub 层处理过的数据封装成 HTTP/2 的帧进行传输，并管理连接的生命周期。
5. **网络层（Network Layer）**：作为最底层，网络层基于标准的 TCP/IP 协议进行数据传输。同时，gRPC 支持 TLS/SSL，可以在这一层提供端到端的加密通信，确保数据在传输过程中的安全性。
这种分层设计让 gRPC 既具备强大的抽象能力，也能深入系统底层实现优化。

### 5.2 多路复用

传统的基于 HTTP/1.1 的 RPC 框架常常受限于 " 队头阻塞 "（Head-of-Line Blocking）问题，即在同一个 TCP 连接上，请求必须串行处理，前一个请求未完成，后续请求即使已准备好也无法发送。这在并发请求多的场景下会严重影响性能。

gRPC 构建于 HTTP/2 之上，天生继承了 HTTP/2 的核心优势——**多路复用（Multiplexing）**。多路复用允许在同一个 TCP 连接上同时发送和接收多个独立的请求和响应，彻底解决了应用层的队头阻塞问题。

在 HTTP/2 中，每一个逻辑上的请求/响应对都被抽象为一个 "Stream"（流），每个 Stream 都有一个唯一的 Stream ID。客户端和服务端可以在同一时间通过同一个 TCP 连接并行地发送属于不同 Stream 的数据帧。

```go
go func() {
    resp, _ := client.SayHello(ctx, &pb.HelloRequest{Name: "Alice"})
    log.Println("SayHello Response:", resp.Message)
}()

go func() {
    resp, _ := client.GetUserProfile(ctx, &pb.UserRequest{Id: 1})
    log.Println("GetUserProfile Response:", resp.Profile)
}()
```

这两个 `SayHello` 和 `GetUserProfile` 调用会在同一个 gRPC 连接（底层即一个 TCP 连接）上，通过不同的 HTTP/2 Stream 并行传输。服务端也能同时接收和处理这两个请求，并将响应通过各自的 Stream 返回。这种机制极大地提高了连接的利用率和系统的吞吐量。

### 5.3 负载均衡

gRPC 提供了多种负载均衡方案，以适配不同部署环境和使用场景：

**客户端负载均衡（Client-side Load Balancing）**

- 客户端自行维护服务实例列表，进行请求分发（如轮询、最小连接数等策略）。
- 适用于客户端可感知所有可用实例的场景，如使用 Kubernetes 服务发现（DNS 轮询）。

```go
// 创建 gRPC 连接，使用 round_robin 负载均衡
conn, err := grpc.Dial(
    "dns:///service-name", // 或逗号分隔的多个地址
    grpc.WithTransportCredentials(insecure.NewCredentials()),
    grpc.WithDefaultServiceConfig(`{"loadBalancingPolicy": "round_robin"}`),
)
```

**服务端负载均衡（Server-side Load Balancing）**

- 请求通过负载均衡代理（如 Envoy、NGINX）转发到实际服务实例。
- 适用于服务实例动态扩缩容、统一网关接入等场景。

这种代理模式下，gRPC 客户端只需连接入口地址，代理负责请求转发和健康检查。

### 5.4 身份认证

在分布式系统中，确保服务间通信的安全性至关重要。gRPC 内置并支持多种身份认证和安全机制：

- **TLS/SSL 加密**：gRPC 可以轻松配置使用 TLS/SSL 来加密客户端和服务端之间的通信。这提供了传输层的数据机密性和完整性保护，并支持双向认证，确保通信双方的身份。
- **Token 认证**：对于应用层面的身份验证，可以通过在 gRPC 请求的 Metadata 中携带认证 Token（如 JWT, OAuth2 Token）。服务端通过验证 Token 的有效性来判断请求的合法性。
- **Interceptor（拦截器）**：gRPC 的 Interceptor 机制是实现统一认证逻辑的强大工具。无论是客户端还是服务端，都可以在请求发送前或接收后插入拦截器，执行认证、日志记录、监控等横切关注点逻辑。这避免了在每个 RPC 方法中重复编写认证代码。例如，可以在一个服务器端拦截器中统一校验客户端请求带来的 Token。

### 5.5 HTTP/2

gRPC 所依赖的 HTTP/2 协议在性能和功能上较 HTTP/1.1 有明显优势，主要体现在以下几个方面：

| **HTTP/2 特性**      | **在 gRPC 中的应用价值**                                                                                        |
| ------------------ | -------------------------------------------------------------------------------------------------------- |
| 多路复用（Multiplexing） | 同一 TCP 连接中支持多个并发 Stream，有效解决 HoL（队头阻塞）问题，提升并发性能。                                                         |
| 流（Stream）机制        | 每个 gRPC 方法调用都对应一个独立的 Stream。这使得 gRPC 能够原生支持**全双工流式通信**（包括客户端流、服务端流和双向流），适用于需要持续数据传输的场景。                  |
| 头部压缩（HPACK）        | 使用二进制编码和基于字典的压缩算法（HPACK）来高效压缩 HTTP 头部信息（包括 gRPC 的 Metadata）。这显著减少了头部数据的大小，尤其是在请求/响应头部信息重复较多的场景下，提高了传输效率。 |
| 流量控制（Flow Control） | HTTP/2 提供了 Stream 级别的流量控制机制，允许发送方和接收方独立地管理每个 Stream 的数据发送速率，防止发送速度过快导致接收方缓冲区溢出，提高了传输的稳定性和可靠性。            |
| 服务端推送（Server Push） | HTTP/2 支持服务端在客户端请求之前主动向客户端推送资源。虽然在标准的 gRPC RPC 调用中不常用，但在某些特定的自定义场景或与 Web 集成时，服务端推送可能发挥作用。                |

>[!NOTE]
>理解队头阻塞（Head-of-Line Blocking - HoL）对于理解网络协议的演进非常重要。在 **HTTP/1.1** 中，由于一个 TCP 连接一次只能处理一个请求 - 响应，多个请求必须排队等待。如果队列中的第一个请求处理缓慢，后面的请求都会被阻塞，这就是应用层的队头阻塞。为了缓解这个问题，浏览器通常会为同一个域名建立多个 TCP 连接，但这会增加连接建立和管理的开销。 
>
> **HTTP/2** 通过引入多路复用和 Stream 机制，在一个 TCP 连接上并发处理多个 Stream，成功解决了**应用层的队头阻塞**。然而，HTTP/2 仍然使用 TCP 作为传输层协议。TCP 的可靠传输机制是基于字节流和序号的。如果某个 TCP 数据包在中途丢失，TCP 会等待该数据包重传并确认。在这个等待过程中，即使是属于其他 Stream 的、已经到达的数据包，也必须在 TCP 缓冲区中等待，直到丢失的数据包被填补。这就是**传输层的队头阻塞**，它会影响到同一个 TCP 连接上的所有 HTTP/2 Stream。 
>
> **HTTP/3** 彻底摆脱了 TCP 的限制，转而使用基于 UDP 的 **QUIC 协议**。QUIC 原生支持多路复用，并且最关键的是，QUIC 的 Stream 是在 UDP 层之上实现的，每个 Stream 是独立的数据传输单元。这意味着即使某个 Stream 的数据包丢失，只会影响这一个 Stream 的数据传输，而**不会阻塞同一个连接上的其他 Stream**。QUIC 还集成了 TLS 加密、连接迁移（在网络切换时保持连接）等特性，并优化了握手过程（通常是 0-RTT 或 1-RTT 建立连接），进一步提升了性能和可靠性。因此，HTTP/3 在网络不稳定、丢包率高或延迟较高的环境下，能够比 HTTP/2 更有效地避免队头阻塞，提供更流畅的并发性能。

## 6 代码地址

- [grpc-learning](https://github.com/ceyewan/grpc-learning)