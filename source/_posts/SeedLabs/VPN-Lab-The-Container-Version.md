---
title: VPN-Lab-The-Container-Version
categories:
  - SeedLabs/NetworkSecurity
tags:
  - VPN
  - NetworkSecurity
abbrlink: 71113d12
date: 2024-03-24 01:05:08
---

## Overview

虚拟专用网（VPN）是建立在公共网络之上的专用网络。VPN 中的计算机可以安全地进行通信，就像它们在一个真正的私有网络上一样，即使它们的通信可以通过一个公共网络进行。

这个实验专注于建立在传输层之上的 VPN 类型。我们将从头开始构建一个非常简单的 VPN，并用这个过程来说明 VPN 技术的每一部分是如何工作的。一个真正的 VPN 程序有两个基本部分，隧道和加密。本实验关注隧道部分。

##  Task 1: Network Setup

我们将在计算机和网关之间创建一个 VPN 隧道，允许计算机通过网关安全的访问一个专用网络。实验设置如下：

![a](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318143828838.png)

实际上，VPN 客户端和 VPN 服务器是通过 Internet 连接的。为了简单起见，我们将这两台机器直接连接到实验室的同一个局域网，也就是说，这个局域网模拟了互联网。

进行如下测试，确保实验环境设置正确：

1.   Host U 可以和 VPN Server 通信
2.   VPN Server 可以和 Host V 通信
3.   Host U 不能和 Host v 通信
4.   在路由器上运行 tcpdump，并嗅探每个网络上的流量

## Task 2: Create and Configure TUN Interface

我们要建立基于 TUN/TAP 技术的 VPN 隧道。TUN 和 TAP 是虚拟网络内核驱动程序；它们实现了完全由软件支持的网络设备。TAP 模拟一个以太网设备，它与第二层包（如以太网帧）一起工作； TUN 模拟一个网络层设备，它与第三层包（如 IP 包）一起工作。有了 TUN/TAP，我们可以创建虚拟网络接口。

一个用户空间程序通常附加在 TUN/TAP 虚拟网络接口上。操作系统通过 TUN/TAP 网络接口发送的数据包被传送到用户空间程序。另一方面，程序通过 TUN/TAP 网络接口发送的数据包被注入到操作系统网络堆栈中。对于操作系统来说，这些数据包似乎来自于通过虚拟网络接口的外部来源。

当一个程序接入到 TUN/TAP 接口时，内核发送到该接口的 IP 数据包将通过管道传输到程序中。另一方面，程序写入接口的 IP 数据包将通过管道进入内核，就像它们是通过这个虚拟网络接口从外部进入的一样。该程序可以使用标准的 read() 和 write() 系统调用从虚拟接口接收数据包或向虚拟接口发送数据包。

### Task 2.a: Name of the Interface

在 Host U 上运行 tun.py 程序，修改程序权限为可执行，然后使用 root 权限来执行它。

打开一个新的 shell，输入 `ip address` 查看机器上所有的网络接口。

![image-20240318151134146](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318151134146.png)

### Task 2.b: Set up the TUN Interface

此时，TUN 接口还是不可用的，因为还没有配置它。我们首先需要为它分配一个 IP 地址，然后再开启接口。

```shell
 ip addr add 192.168.53.99/24 dev tun0
 ip link set dev tun0 up
```

为了避免重复执行，我们可以在程序中添加以下两行代码，这样就可以自动配置了。

```python
os.system("ip addr add 192.168.53.99/24 dev {}".format(ifname))
os.system("ip link set dev {} up".format(ifname))
```

重新执行，结果如下：

![image-20240318152158337](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318152158337.png)

### Task 2.c: Read from the TUN Interface

在这个任务中，我们将读取 TUN 接口。任何从 TUN 接口出来的东西都是一个 IP 数据包。我们可以把从接口接收到的数据转换成 Scapy IP 对象，这样我们就可以打印出 IP 包的每个字段。修改代码中的 while 循环如下：

```python
while True:
    packet = os.read(tun, 2048)
    if packet:
        ip = IP(packet)
        print(ip.summary())
```

然后我们在 Host U 上 ping 192.168.53.0/24 网络中的一个主机，输出如下；ping 192.168.60.0/24 网络中的一个主机，没有输出。这是因为我们的虚拟网卡绑定的 IP 是 192.168.53.99/24，对于 192.168.53.0/24 网络的数据，都会交给这个虚拟网卡。并且程序并不会只能拿到 Raw，而是拿到了 IP 包及以上的东西。

![image-20240318152756155](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318152756155.png)

### Task 2.d: Write to the TUN Interface

从 TUN 接口获取一个 ICMP 请求包，那么久构造一个相应的应答包并将其写入 TUN 接口。

```python
while True:
    packet = os.read(tun, 2048)
    if packet:
        packet = IP(packet)
        print(packet.summary())
        new_ip = IP(src=packet[IP].dst, dst=packet[IP].src)
        new_icmp = ICMP(type=0, id=packet[ICMP].id, seq=packet[ICMP].seq)
        new_raw = Raw(load=packet[Raw].load)
        new_packet = new_ip/new_icmp/new_raw
        print(new_packet.summary())
        os.write(tun, bytes(new_packet))
```

![image-20240318161321636](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318161321636.png)

如果不向接口写入 IP 包，而是乱七八糟的东西，那么结果如下：

![image-20240318161635234](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318161635234.png)

## Task 3: Send the IP Packet to VPN Server Through a Tunnel

在这个任务中，我们将接收到的 IP 数据包当做 Raw，放入一个新的 IP 数据包的 UDP Payload 中，并将其发送给另一计算机，这种方式叫做 IP 隧道。隧道实现就是一个标准的 C/S 程序而已，可以建立在 TCP 或者 UDP 之上。

**tun_server.py**，在 VPN 服务器上运行，监听 9090 端口，将接收到的 UDP Payload 数据转化为 Scapy IP 对象。

```python
#!/usr/bin/env python3
from scapy.all import *

IP_A = "0.0.0.0"
PORT = 9090
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((IP_A, PORT))
while True:
    data, (ip, port) = sock.recvfrom(2048)
    print("{}:{} --> {}:{}".format(ip, port, IP_A, PORT))
    pkt = IP(data)
    print(" Inside: {} --> {}".format(pkt.src, pkt.dst))
```

**tun_client.py**，修改 tun.py 的 while 循环如下：

```python
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVER_IP = "10.9.0.11"
SERVER_PORT = 9090
while True:
    packet = os.read(tun, 2048)
    if packet:
        sock.sendto(packet, (SERVER_IP, SERVER_PORT))
```

**Test**，测试隧道是否工作，首先 ping 192.168.53.0/24 网络的任何 IP 地址，查看 VPN Server 的输出；然后测试 ping 192.168.60.0/24 网络的任何 IP 地址，查看 VPN Server 的输出。结果如下，前者有输出，后者无输出。

![image-20240318163402818](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318163402818.png)

添加路由如下，这样去往 192.168.60.0/24 网络的数据包也会通过 VPN Client 经过隧道传输了。

![image-20240318163830724](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318163830724.png)

## Task 4: Set Up the VPN Server

tun_server.py 程序从隧道获取数据包之后，需要将数据包提供给内核，这样内核就可以将数据包路由到最终目的地，这同样需要 TUN 接口来完成。我们需要：

-   创建 TUN 接口并进行配置
-   从套接字接口获取数据，将接收到的数据作为 IP 包处理
-   将数据包写入 TUN 接口

```python
# Create the tun interface
tun = os.open("/dev/net/tun", os.O_RDWR)
ifr = struct.pack('16sH', b'ceyewan%d', IFF_TUN | IFF_NO_PI)
ifname_bytes = fcntl.ioctl(tun, TUNSETIFF, ifr)

# Get the interface name
ifname = ifname_bytes.decode('UTF-8')[:16].strip("\x00")
print("Interface Name: {}".format(ifname))
# 这里需要分配 192.168.60.0/24 网段的 IP 地址
os.system("ip addr add 192.168.60.99/24 dev {}".format(ifname)) 
os.system("ip link set dev {} up".format(ifname))

# listen UDP packet
IP_A = "0.0.0.0"
PORT = 9090
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((IP_A, PORT))
while True:
    data, (ip, port) = sock.recvfrom(2048)
    print("{}:{} --> {}:{}".format(ip, port, IP_A, PORT))
    pkt = IP(data)
    print(" Inside: {} --> {}".format(pkt.src, pkt.dst))
    os.write(tun, bytes(pkt)) # 发送到虚拟网卡
```

我们使用 Wireshark 监听 192.168.60.0/24 这个局域网，发现存在 ICMP 请求和应答数据包。这也就说明 Host U 到 Host V 这条单向通路已经配置完成了。

![image-20240318165119817](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318165119817.png)

## Task 5: Handling Traffic in Both Directions

**tun_server.py** 

```python
#!/usr/bin/env python3
import fcntl
import struct 
import os
import time
from scapy.all import *

TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_TAP = 0x0002
IFF_NO_PI = 0x1000

# Create the tun interface
tun = os.open("/dev/net/tun", os.O_RDWR)
ifr = struct.pack('16sH', b'ceyewan%d', IFF_TUN | IFF_NO_PI)
ifname_bytes = fcntl.ioctl(tun, TUNSETIFF, ifr)

# Get the interface name
ifname = ifname_bytes.decode('UTF-8')[:16].strip("\x00")
print("Interface Name: {}".format(ifname))
os.system("ip addr add 192.168.60.99/24 dev {}".format(ifname))
os.system("ip link set dev {} up".format(ifname))
os.system("ip route add 192.168.53.0/24 dev ceyewan0 via 192.168.60.99")

# listen UDP packet
IP_A = "0.0.0.0"
PORT = 9090
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((IP_A, PORT))
while True:
    ready, _, _ = select.select([sock, tun], [], [])
    for fd in ready:
        if fd is sock:
            data, (ip, port) = sock.recvfrom(2048)
            pkt = IP(data)
            print("From socket <==: {} --> {}".format(pkt.src, pkt.dst))
            os.write(tun, data)
        if fd is tun:
            packet = os.read(tun, 2048)
            pkt = IP(packet)
            print("From tun ==>: {} --> {}".format(pkt.src, pkt.dst))
            sock.sendto(packet, (ip, port))
```

**tun_client.py** 

```python
#!/usr/bin/env python3

import fcntl
import struct
import os
import time
from scapy.all import *

TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_TAP = 0x0002
IFF_NO_PI = 0x1000

# Create the tun interface
tun = os.open("/dev/net/tun", os.O_RDWR)
ifr = struct.pack('16sH', b'ceyewan%d', IFF_TUN | IFF_NO_PI)
ifname_bytes = fcntl.ioctl(tun, TUNSETIFF, ifr)

# Get the interface name
ifname = ifname_bytes.decode('UTF-8')[:16].strip("\x00")
print("Interface Name: {}".format(ifname))
os.system("ip addr add 192.168.53.99/24 dev {}".format(ifname))
os.system("ip link set dev {} up".format(ifname))
os.system("ip route add 192.168.60.0/24 dev ceyewan0 via 192.168.53.99")

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
while True:
    ready, _, _ = select.select([sock, tun], [], [])
    for fd in ready:
        if fd is sock:
            data, (ip, port) = sock.recvfrom(2048)
            pkt = IP(data)
            print("From socket <==: {} --> {}".format(pkt.src, pkt.dst))
            os.write(tun, data)
        if fd is tun:
            packet = os.read(tun, 2048)
            pkt = IP(packet)
            print("From tun ==>: {} --> {}".format(pkt.src, pkt.dst))
            sock.sendto(packet, ("10.9.0.11", 9090))
```

每次重启程序都需要配一遍默认路由，因为程序执行结束后，虚拟网卡就没了，默认路由也就失效了。然后 Host U to Host V 没问题，Host V to Host U 利用之前建立的连接也能通信，但不稳定。因为 Client 端没有监听端口。

![image-20240318172612805](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318172612805.png)

## Task 6: Tunnel-Breaking Experiment

我们把默认路由配置写到代码里，上面我已经写了。在连接时，我们发现输入的字符可以正确的回显，说明是通路，断开 VPN Server 后，输入字符不能回显。重新启动 VPN Server，发现刚刚的输入都显示出来了，判断是网络一直在重试，然后通了就一下全显示了。后续能正常工作，没有问题。

![image-20240318175525520](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318175525520.png)

## Task 7: Routing Experiment on Host V

在一个真正的 VPN 系统中，流量将被加密。这意味着返回的流量必须从同一个隧道返回（使用同一个 TLS/SSL 连接）。因此，Host V 的流量要经过 VPN Server 是非常重要的。在实验的设置中，Host V 的路由表有一个默认设置：到任何目的地的数据包，除 了 192.168.60.0/24 网络，将自动路由到 VPN 服务器。在现实世界中，Host V 可能离 VPN 服务器有几个跳，并且默认的路由条目可能不能保证将返回数据包路由回 VPN 服务器。必须正确设置私有网络中的路由表，以确保到隧道另一端的数据包将被路由到 VPN 服务器。

```shell
 ip route del default
 ip route add 192.168.53.0/24 via 192.168.60.11
```

当删除默认路由后，只要我们配置了 Host V 的数据都经过 VPN Server，还是可以正常的进行通信。

![image-20240318230507689](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318230507689.png)

## Task 8: VPN Between Private Networks

在这个任务中，我们要在两个私有网络之间建立一个 VPN。上述过程，一段只能做客户端，而现在，两端都是客户端，也都是服务端。

这个设置模拟了一个组织有两个站点的情况，每个站点都有一个专用网络。连接这两个网络的唯一方法是通过互联网。你的任务是在这两个网站之间建立一个 VPN，所以这两个网络之间的通信将通过一个 VPN 隧道。您可以使用前面开发的代码，但是需要考虑如何设置正确的路由，以便这两个专用网络之间的数据包可以路由到 VPN 隧道。

![image-20240318230907607](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318230907607.png)

我们查看配置文件，可以发现默认路由都已经设置好了，我们只需要在客户端和服务端各设置一个虚拟网卡，其中所有流向对面私有网络的数据包都被路由到虚拟网卡上然后通过 UDP 数据包发送过去。

**tun_client.py** 

```python
#!/usr/bin/env python3

import fcntl
import struct
import os
import time
from scapy.all import *

TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_TAP = 0x0002
IFF_NO_PI = 0x1000

# Create the tun interface
tun = os.open("/dev/net/tun", os.O_RDWR)
ifr = struct.pack('16sH', b'ceyewan%d', IFF_TUN | IFF_NO_PI)
ifname_bytes = fcntl.ioctl(tun, TUNSETIFF, ifr)

# Get the interface name
ifname = ifname_bytes.decode('UTF-8')[:16].strip("\x00")
print("Interface Name: {}".format(ifname))
os.system("ip addr add 192.168.50.99/24 dev {}".format(ifname))
os.system("ip link set dev {} up".format(ifname))
os.system("ip route add 192.168.60.0/24 dev ceyewan0 via 192.168.50.99")
# 对于 tun_server.py 我们只需要把上面的 50 和 60 相互对换即可
# listen UDP packet
IP_A = "0.0.0.0"
PORT = 9090
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((IP_A, PORT))
while True:
    ready, _, _ = select.select([sock, tun], [], [])
    for fd in ready:
        if fd is sock:
            data, (ip, port) = sock.recvfrom(2048)
            pkt = IP(data)
            print("From socket <==: {} --> {}".format(pkt.src, pkt.dst))
            os.write(tun, data)
        if fd is tun:
            packet = os.read(tun, 2048)
            pkt = IP(packet)
            print("From tun ==>: {} --> {}".format(pkt.src, pkt.dst))
            sock.sendto(packet, ("10.9.0.11", 9090)) # 对于 tun_server.py，将 IP 修改为 12
```

因为是 UDP 数据包，没有连接，我们不用管 Client 和 Server 的连接状态，直接发送给对方就行，服务端和客户端的程序一模一样。如果使用的是 TCP，那么通信之前 Client 和 Server 先建立连接，这样双方从 TUN 接口拿到的数据包都只需要发送到这个连接。

![image-20240319000011600](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240319000011600.png)

## Task 9: Experiment with the TAP Interface

使用 TAP 接口，拿到的是 MAC 层的包，这样，ARP 帧也可以处理。基本上操作是没有什么区别的，就不做了。