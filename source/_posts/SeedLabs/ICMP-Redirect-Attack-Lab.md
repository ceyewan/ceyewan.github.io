---
title: ICMP-Redirect-Attack-Lab
categories:
  - SeedLabs/NetworkSecurity
tags:
  - ICMP Redirect Attack
  - NetworkSecurity
abbrlink: 711b39f2
date: 2024-03-24 00:09:54
---

## Overview

ICMP 重定向是路由器发送给 IP 数据包发送者的错误消息。当路由器认为一个数据包被错误地路由，并且它想通知发送者它应该为发送到同一目的地的后续数据包使用不同的路由器时，就会使用重定向。比如路由 A、B 和主机 C 在同一网络中，如果 C 要访问互联网的数据包发送给了路由 A，A 判断需要转发给路由 B，那么 A 就会通知主机 C，接下来的数据包直接发送给路由 B 即可。

ICMP 重定向可以被攻击者用来改变受害者的路由。 本次实验包括以下主题：

-   IP、ICMP 协议
-   ICMP 重定向攻击
-   路由

## Environment Setup using Container

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/Jq3sbTnpWoG6nbxTnbZcEweinzf.png)

本次实验的拓扑图如上，正确的路由是 10.9.0.11。而 Attacker 需要伪造 ICMP 重定向数据包，欺骗 Victim 发送给 192.168.60.5 的数据包应该交给 Malicious Router。

## Task 1: Launching ICMP Redirect Attack

在 Ubuntu 中，有对 ICMP 重定向攻击的应对方法，我们在容器的配置中关闭了这种防御措施。

```dockerfile
sysctls:
    - net.ipv4.conf.all.accept_redirects=1
```

我们在 Victim 上执行 ip route，可以看到默认的路由是 Router：

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/ICT3bPtfmoZ73KxFNdkcz3iHnih.png)

编写如下代码：

```python
# !/usr/bin/python3
from scapy.all import *

ip = IP(src='10.9.0.11', dst='10.9.0.5') # 冒充 Router 发送给 Host
icmp = ICMP(type=5, code=1) # type=5,code=1 表示 Redirect for host，对主机重定向
icmp.gw = '10.9.0.111'        # 网关地址

# The enclosed IP packet should be the one that
# triggers the redirect message.
ip2 = IP(src='10.9.0.5', dst='192.168.60.5') # 表示构造的数据包是由 Src-to-Dst 触发的  
while True:
    send(ip/icmp/ip2/ICMP())    # 不停发送重定向包
    time.sleep(1)
```

实验要成功需要两个条件，第一：在攻击时 Victim 同时也在发出 ICMP 包；第二，对于 Ubuntu 20.04，验证重定向包中的 ip2 是否与触发 ICMP 重定向的原始包的类型和目标 ip 地址相匹配。

因此，我们让 Victim 一直执行 ping 命令发出 ICMP 包并且 Attacker 不停的发出重定向包。可以看到，重定向成功。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/JlUlbMcqBoknJLxarkCcrM3cnUe.png)

在 VIctim 上做一个跟踪路由（traceroute），命令为 `mtr -n 192.168.60.5`，mtr 命令是一种网络诊断工具，结合了 traceroute 和 ping 的功能，mtr 会显示从您的主机到目标主机之间经过的路由路径，并在每个路由器上执行一系列 ICMP 数据包的传输，以测量每个节点的延迟情况。

如下，被欺骗的先发送给了 Malicious Router，然后才是 Router，最后是目的地。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/Xy1Zb84KdoMUALxsajSc1V8Knye.png)

**Question 1: Can you use ICMP redirect attacks to redirect to a remote machine?**

不可以，修改了 `icmp.gw = '外部地址'` 后，发现重定向没有效果，抓包也只有 ping 和重定向的包。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/PUNybaSasoHBXEx9zA2cFckBnjR.png)

正确重定向的包是这样的，因为第一次 ping request 会走错地方，所以会 request 两次。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/RKnwbuolKoqEizxAYDpcdmecnjR.png)

**Question 2: Can you use ICMP redirect attacks to redirect to a non-existing machine on the same network? **

当收到重连后，受害者会通过 ARP 寻找目标网址的 MAC 地址，并同时先维持原先的连接。但由于并没有找到目标网址的 MAC 地址，所以维持原来的发送。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/Kt0absD82oQ5d0xYXXQcAYvkncf.png)

**Question 3**

- net.ipv4.conf.all.send_redirects=0：禁止向所有接口发送 ICMP 重定向消息。
- net.ipv4.conf.default.send_redirects=0：禁止向默认接口发送 ICMP 重定向消息。
- net.ipv4.conf.eth0.send_redirects=0：禁止向名为 eth0 的接口发送 ICMP 重定向消息。

修改为 1 之后开启了重定向，数据包不再被重定向到 111 了，也就是说，重定向失败。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/XBBKbGVjNoNLRXxi51XcTE2jnhe.png)

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/I14Cbe1R2oTQoWxzNnocz9zmngg.png)

数据包抓包结果如下！

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/TYwbbsCpuoALJjxUCMhco52PnPd.png)

## Task 2: Launching the MITM Attack

首先，修改 Docker 配置文件，然后重启容器。

```dockerfile
sysctls:
    - net.ipv4.ip_forward=0
    - net.ipv4.conf.all.send_redirects=0
    - net.ipv4.conf.default.send_redirects=0
    - net.ipv4.conf.eth0.send_redirects=0
```

第一步，让 Victim 一直执行 ping 命令发出 ICMP 包并且 Attacker 不停的发出重定向包。这一步同 Task1 一样。

第二步，让 Malicious Router 执行 python3 mitm_sample.py，代码只需要做如下修改。当然了，把 seedlabs 改了也没关系。

```python
f = 'tcp and ether src 02:42:0a:09:00:05'
pkt = sniff(iface='eth0', filter=f, prn=spoof_pkt)
```

第三步，在 Host 上开启 nc 服务器，在 Victim 上连接 nc 服务器。通信交互如下，发现嗅探并修改数据成功。

![](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/UePmbq0j1oOcTuxj4yScgjRinZg.png)

**Question 4: In your MITM program, you only need to capture the traffics in one direction. Please indicate which direction, and explain why.**

因为，我们欺骗也只欺骗了 Victim，只有 Victim 流向 Host 的数据会经过 Malicious Router，故只需要捕获这一个方向的即可。

**Question 5，**使用 MAC 地址是可以的，使用 IP 地址是不可以的。因为 Malicious Router 转发出的数据包的 IP 地址并没有修改，还是 Victim 的 IP 地址。这样，Malicious Router 发送的数据包又会被自己捕获，导致 IP 风暴。