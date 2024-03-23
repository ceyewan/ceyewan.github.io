---
title: Transport-Layer-Security-(TLS)-Lab
categories:
  - SeedLabs/Cryptography
tags:
  - TLS
  - Cryptography
abbrlink: 862ec7e4
date: 2024-03-24 00:55:27
---

##  Overview

现在，越来越多的数据是通过互联网传输的，然而，当数据通过这样一个不受保护的公共网络时，可能会被读取甚至修改。因此，考虑通信安全的应用程序需要加密数据并且检测篡改。密码算法可以用来解决该问题，有许多加密算法，即使是同一个算法，也有许多参数可以使用。为了实现互操作性，即允许不同的应用程序相互通信，这些应用程序需要遵循一个共同的标准 TLS，传输层安全，就是这样一个标准。现在大多数网络服务器都使用 HTTPS，它是建立在 TLS 之上的。

## Lab Environment

这个实验中，我们使用三台机器，一台是客户端、一台是服务端，还有一台用于代理。

```bash
➜ dockps   
1572ed82cb5b  client-10.9.0.5
88e86e068b11  mitm-proxy-10.9.0.143
9e6cdc38823b  server-10.9.0.43
```

## Task 1: TLS Client

### Task 1.a: TLS handshake

在客户端和服务器进行安全通信之前，首先需要设置几个问题，包括使用什么加密算法和密钥、使用什么 MAC 算法、使用什么算法进行密钥交换等。这些加密参数需要客户端和服务器达成一致。这就是 TLS 握手协议的主要目的。

```python
#!/usr/bin/env python3

import socket
import ssl
import sys
import pprint

hostname = sys.argv[1]
port = 443
cadir = '/etc/ssl/certs'

# Set up the TLS context
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)  # 创建 TLS 上下文
context.load_verify_locations(capath=cadir)  # 加载 CA 证书
context.verify_mode = ssl.CERT_REQUIRED  # 设置验证模式为必须
context.check_hostname = True  # 检查主机名是否匹配

# Create TCP connection
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((hostname, port))	# TCP 握手
input("After making TCP connection. Press any key to continue ...")

# Add the TLS
ssock = context.wrap_socket(sock, server_hostname=hostname,
                            do_handshake_on_connect=False)  # 包装套接字为 TLS 连接
ssock.do_handshake()   # 开始 TLS 握手
print("=== Cipher used: {}".format(ssock.cipher()))  # 打印所使用的加密算法
print("=== Server hostname: {}".format(ssock.server_hostname))  # 打印服务器主机名
print("=== Server certificate:")
pprint.pprint(ssock.getpeercert())  # 打印服务器证书
pprint.pprint(context.get_ca_certs())  # 打印已加载的 CA 证书
input("After TLS handshake. Press any key to continue ...")

# 发送HTTP GET请求
http_request = http_request = b"GET / HTTP/1.1\r\nHost: "+hostname.encode('utf-8')+b"\r\n\r\n"
ssock.sendall(http_request)

# 接收并打印响应
response = ssock.recv(4096)
pprint.pprint(response.decode('utf-8'))

# Close the TLS Connection
ssock.shutdown(socket.SHUT_RDWR)  # 关闭TLS连接的读写
ssock.close()  # 关闭套接字
```

-   客户端和服务端使用的密码如下，具体来说，它使用了 TLSv1.3 协议，并且采用了 TLS_AES_256_GCM_SHA384 算法，密钥长度为 256 位。
-   输出的第一个证书就是服务器的证书。
-   `'/etc/ssl/certs'` 用于指示本地可信的 CA 证书路径。

![image-20240314154222358](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240314154222358.png)

### Task 1.b: CA’s Certificate

首先，将相应的证书复制到 ./client-certs 文件夹中，我们从上面的输出中可以看到，subject 部分的 CN 值为 DigiCert Global Root CA，接下来我们去证书路径查找该证书并将其拷贝过来。

```bash
➜ ls | grep DigiCert_Global_Root_CA
DigiCert_Global_Root_CA.pem
➜ cp DigiCert_Global_Root_CA.pem ~/SeedLab/Cryptography/Labsetup/volumes/client-certs
```

TLS 在验证服务器证书时会检查证书的颁发者（issuer）信息。证书的颁发者信息通常包含了颁发者的身份信息，比如颁发者的名称、证书有效期等。TLS 会根据颁发者的身份信息生成一个哈希值（hash value）。然后，TLS 会将这个哈希值作为一部分文件名，并在指定的文件夹中寻找相应的颁发者证书。为了让 TLS 能够正确地找到颁发者证书，我们需要将每个颁发者证书的文件名改为与其主题字段（subject field）生成的哈希值相匹配的名称，或者创建一个哈希值的符号链接。

![image-20240314160854141](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240314160854141.png)

如上，我们生成了哈希值并且创建了符号链接，修改代码中的路径后执行，发现执行成功。

### Task 1.c: Experiment with the hostname check

**Step 1**：使用 dig 命令获取 www.example.com 的 IP 地址，结果为 93.184.216.34。

**Step 2**：修改 /etc/hosts 文件，添加 `93.184.216.34 www.example2024.com` 条目。

**Step 3**：观察程序中 `context.check_hostname = False/True` 这两种情况的结果。

可以看到，如果检查主机名，那么就连接不上；如果不检查主机名，那么可以直接连接。设置为 True 可以抵抗中间人攻击，Step 2 我们模拟了 DNS 攻击，所有去往 www.example2024.com 的流量都会被误导去往 93.184.216.34 即 www.example.com。如果不检查主机名，TLS 会正常的建立连接，我们还以为访问的是 2024，其实访问的是 example。

![image-20240314162222977](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240314162222977.png)

### Task 1.d: Sending and getting Data

已经实现了。接收图片只需要更改一下发送和接收部分代码。

```python
# 发送HTTP GET请求
http_request = b"GET /head.jpg HTTP/1.1\r\nHost: " + \
    hostname.encode('utf-8')+b"\r\n\r\n"
ssock.sendall(http_request)

ssock.settimeout(3) # 超时时间
# 接收并打印响应
response = b''
while True:
    try:
        data = ssock.recv(4096) # 阻塞，使用超时机制退出
        response += data
    except socket.timeout:
        break
# Extract image data from response
image_data = response.split(b'\r\n\r\n')[-1]
# Save image to file
with open('image.jpg', 'wb') as f:
    f.write(image_data)
```

## Task 2: TLS Server

在进行此任务之前，学生需要创建证书颁发机构(CA) ，并使用此 CA 的私钥为此任务创建服务器证书。如何做到这一点已经在 PKI 实验中完成了。在这个任务中，我 们假设已经创建了所有必需的证书，包括 CA 的公钥证书和私钥(CA.crt 和 CA.key) ，以及服务器的公钥证书和私钥(server.crt 和 server.key)。

### Task 2.a. Implement a simple TLS server

服务端代码如下：

```python
#!/usr/bin/env python3

import socket
import ssl
import pprint

html = """
HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html><html><body><h1>This is ceyewan2024.com!</h1></body></html>
"""

SERVER_CERT = './server-certs/mycert.crt'
SERVER_PRIVATE = './server-certs/mycert.key'


context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)  # For Ubuntu 20.04 VM
context.load_cert_chain(SERVER_CERT, SERVER_PRIVATE)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
sock.bind(('0.0.0.0', 4433))
sock.listen(5)

while True:
    newsock, fromaddr = sock.accept()
    try:
        ssock = context.wrap_socket(newsock, server_side=True)
        print("TLS connection established")
        data = ssock.recv(1024)              # Read data over TLS
        pprint.pprint("Request: {}".format(data))
        ssock.sendall(html.encode('utf-8'))  # Send data over TLS
        ssock.shutdown(socket.SHUT_RDWR)     # Close the TLS connection
        ssock.close()

    except Exception:
        print("TLS connection fails")
        continue
```

同样，我们需要配置 DNS 映射将服务器名称映射到 IP 地址，然后将服务器的公钥私钥复制到上述代码所指位置，将 CA 公钥文件复制到 Task 1 位置并且要做 Task 1 相同的操作。

然后我们进入容器执行如下：

![image-20240314171514116](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240314171514116.png)

### Task 2.b. Testing the server program using browsers

在做 PKI 实验时，已经把证书加入了，所以可以直接访问。

![image-20240314172852014](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240314172852014.png)

### Task 2.c. Certificate with multiple names

1.   复制 PKI 实验的 myopenssl.cnf 文件过来。
2.   配置 server_openssl.cnf 内容如下：

```
[ req ]
prompt = no
distinguished_name = req_distinguished_name
req_extensions = req_ext

[ req_distinguished_name ]
C = CN
ST = Hubei
L = Wuhan
O = whu
CN = www.ceyewan2024.com
[ req_ext ]
subjectAltName = @alt_names
[alt_names]
DNS.1 = www.ceyewan.com
DNS.2 = www.example.com
DNS.3 = *.ceyewan2024.com
```

3.   执行下面两条指令生成新的服务器公私钥对。

![image-20240314180029921](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240314180029921.png)

4.   使用新的服务器公私钥对运行服务端程序，并且配置上面几个域名的 DNS 解析。
5.   去浏览器访问这几个域名，结果如下，达到了实验的目的，允许证书拥有多个主机名。

![image-20240314175609457](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240314175609457.png)

## Task 3: A Simple HTTPS Proxy

代理实际上是 TLS 客户端和服务器程序的组合，对浏览器提供服务，对服务器充当客户。

![image-20240314180311616](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240314180311616.png)

我们编写 proxy 程序如下，这个程序充当 client 和 example.com 的中间人，它可以直接访问 example.com，又由于它使用了 client 可信的证书，只要 client 关闭了主机名匹配检查，那么它就可以做到两端欺骗。

```python
#!/usr/bin/env python3
import socket
import ssl

cadir = "/etc/ssl/certs"
SERVER_CERT = './server-certs/server.crt'
SERVER_PRIVATE = './server-certs/server.key'
# 等待浏览器的连接
context_srv = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)  # For Ubuntu 20.04 VM
context_srv.load_cert_chain(SERVER_CERT, SERVER_PRIVATE)
sock_listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
sock_listen.bind(('0.0.0.0', 443))
sock_listen.listen(5)
sock_for_browser, fromaddr = sock_listen.accept()
ssock_for_browser = context_srv.wrap_socket(sock_for_browser, server_side=True)
# 连接服务器
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)  # 创建 TLS 上下文
context.load_verify_locations(capath=cadir)  # 加载 CA 证书
context.verify_mode = ssl.CERT_REQUIRED  # 设置验证模式为必须
context.check_hostname = True  # 检查主机名是否匹配
sock_for_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_for_server.connect(('www.example.com', 443))
ssock_for_server = context.wrap_socket(sock_for_server, server_hostname='www.example.com',
                                       do_handshake_on_connect=False)  # 包装套接字为 TLS 连接
ssock_for_server.do_handshake()   # 开始 TLS 握手
# 四次接收发送数据
request = ssock_for_browser.recv(9192)
ssock_for_server.sendall(request)
response = ssock_for_server.recv(9192)
ssock_for_browser.sendall(response)
print(response.decode("utf-8"))
ssock_for_browser.shutdown(socket.SHUT_RDWR)
ssock_for_browser.close()
```

我们看到，proxy 可以正常访问网站，这是因为我们配置了该容器的默认 DNS 服务器为 8.8.8.8，而 client 不能访问该网站，是因为我们配置了 DNS 映射，模拟攻击。建立 SSL 连接和 proxy 捕获数据都成功了，这是很危险的，我们的所有数据都可以被 proxy 服务器看见。

![image-20240314220922909](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240314220922909.png)

使用浏览器结果也是一样的，可以转发。难道浏览器也不验证证书的主机名？不是的，是因为我们配置证书的时候，就已经把 www.example.com 加入到证书了。这也说明了如果 CA 私钥没有保密会造成多么严重的后果！