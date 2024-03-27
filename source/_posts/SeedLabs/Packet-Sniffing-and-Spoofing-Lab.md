---
title: Packet-Sniffing-and-Spoofing-Lab
categories:
  - SeedLabs/NetworkSecurity
tags:
  - Scapy
  - NetworkSecurity
abbrlink: e62f13aa
date: 2024-03-23 23:56:16
---

## Interview

**包嗅探和欺骗**是网络安全中的两个重要概念，我们需要学习使用相关工具并理解其原理，以下是这个实验的主题：

-   嗅探和欺骗是如何工作的
-   使用 pcap 库和 Scapy 进行数据包嗅探
-   使用原始套接字和 Scapy 的数据包欺骗
-   使用 Scapy 操纵数据包

在这个实验中，我们主要就是熟悉 Scapy，能够使用它来嗅探包，构造数据包并发送出去。

## Environment Setup using Container

我们将使用 docker 构造如下的一个虚拟局域网。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/FrMHbe503o6Alrx4m0vcPtEynib.png)

- 开启虚拟环境

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/X91nbnEgRoj74axbKgEcfG2Qnoe.png)

- 主机模式

我们可以发现，在 docker-conpose 文件中，attacker 容器和其他两个容器不一样，其中 network_mode 为 host 表示主机模式。当一个容器处于主机模式时，它可以看到所有主机的网络接口，它甚至拥有与主机相同的 IP 地址。这样，攻击容器和主机一样，能看到所有的流量。

- 共享文件夹

如下设置，在主机和容器之间创建了一个共享文件夹，这样我们将代码放在主机的 /volumes 文件夹中，就可以在攻击容器中找到它。

```dockerfile
volumes:
    - ./volumes:/volumes
```

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/YX2qbfbRFoaeuMxB7KQcoYIVnXc.png)

- 在创建容器时，会创建一个新的网络来连接主机和容器，这个网络的 IP 为 10.9.0.0/24。为主机分配的 IP 地址是 10.9.0.1，我们可以通过 ifconfig 命令查找其相应的网络接口名称。（在攻击容器或者主机中执行均可，因为主机模式）

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/KqDQb0RiAoirXjxOsenci1dInzc.png)

## Task 1.1: Sniffing Packets

如下代码，嗅探目标网卡上的 ICMP 数据包，我们执行 ping 10.9.0.5 命令时，就可以捕获该数据包并将其显示出来。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/Gi8Bb9rO8oB3plxkirwcFpFgnDh.png)

如果是在普通用户下执行，就会报错。因为监听网卡需要管理员权限。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/RPMnbsURvo2GJUxtDj3c8N2ynBd.png)

BPF 语法：

- 只捕获 ICMP 数据包 --> icmp
- 特定 IP 及端口号 23 的 TCP 数据包 --> tcp and src host 192.168.0.1 and dst port 23
- 特定子网 --> net 128.230.0.0 mask 255.255.0.0

## Task 1.2: Spoofing ICMP Packets

如下，我们在攻击容器中伪装成 10.9.0.5 给 10.9.0.6 发送了一个 ICMP 包，右边的嗅探程序发现 10.9.0.6 给 10.9.0.5 回复了一个 echo-reply 包。这说明我们的欺骗是成功的。这里的 / 符号被 IP() 重载了，最后得到的 p 就是封装在 IP 协议中的 ICMP 数据包。

当然了，也可以不用嗅探，而是直接使用 wireshark 查看。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/O7zIbqicKovEHxxb3uGc4HPHnYg.png)

## Task 1.3: Traceroute

我们设置不同的 TTL 值，并查看返回的数据包的 IP，就能够得到这一系列的中间路由。

- 在 Scapy 中，`sr1()` 函数用于发送一个数据包并等待第一个响应数据包的到达，然后返回这个响应数据包。
- verbose=0 时，表示关闭输出，即不显示任何提示信息或调试信息。
- 超时、目标不可达、ICMP 错误消息被过滤都会导致 reply 变量为 None。

```python
from scapy.all import *

def traceroute(destination):
    ttl = 1
    max_hops = 30

    while True:
        pkt = IP(dst=destination, ttl=ttl) / ICMP()
        reply = sr1(pkt, verbose=0, timeout=1)

        if reply is None:
            print(f'{ttl}: *')
        else:
            print(f'{ttl}: {reply.src}')

        if reply and reply.src == destination:
            break

        ttl += 1
        if ttl > max_hops:
            break

traceroute('120.26.56.2')
```

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/OrDcbYgjXouWQjxrLSCcSX0UnGc.png)

## Task 1.4: Sniffing and-then Spoofing

```python
#!/usr/bin/python3
from scapy.all import *

def print_pkt(pkt):
    print(pkt[IP].dst, pkt[IP].src)
    reply = IP(src=pkt[IP].dst, dst=pkt[IP].src)/ICMP(type='echo-reply',
                                                      id=pkt[ICMP].id, seq=pkt[ICMP].seq)/Raw(load=pkt[Raw].load)
    send(reply)

pkt = sniff(iface='br-e1c97aa198c1',
            filter="icmp[icmptype]==icmp-echo", prn=print_pkt)
```

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/DWaLbWAr8oGbXIxg6NIcu5Znn0e.png)

如下结果我们发现，对于不存在或者存在的外部地址，均能得到响应，但是对于同一子网地址，不会得到响应。这和 ARP 协议有关，当给内网 IP 地址发送数据时，无法通过 ARP 协议得到对应的 MAC 地址，这样，数据包根本就不能发送出去，因此我们也就嗅探不到了。