---
title: Public-Key-Infrastructure-(PKI)-Lab
categories:
  - SeedLabs/Cryptography
tags:
  - PKI
  - Cryptography
abbrlink: ccc415c2
date: 2024-03-24 00:51:18
---

## Overview

公钥密码学是当今安全通信的基础，但当通信的一方向另一方发送其公钥时，就会受到中间人攻击。根本的问在于没有简单的方法来核实公钥的所有权。公钥基础设施（PKI）是解决这个问题的一 个实用方案。

在这个实验中，学生能够理解 PKI 是如何工作的、是如何保护网络的以及中间人攻击是如何被 PKI 击败的。此外，学生能够理解信任根在 PKI 中的意义以及信任根被破坏会出现的问题。本次实验包括以下主题：

- 公钥加密、公钥基础建设 PKI
- 证书颁发机构 CA、X.509 证书和根 CA
- Apache、HTTP 和 HTTPS
- 中间人攻击

## Lab Environment

在这个实验中，我们将生成公钥证书，用它来保护 Web 服务器。

**DNS 设置**：我们在主机的 /etc/hosts 文件中写入如下条目，这样，当我们访问这两个域名时，去往的都是 Web 服务器的地址。

```
10.9.0.80 www.bank32.com
10.9.0.80 www.ceyewan2024.com
```

## Task 1: Becoming a Certificate Authority (CA)

证书颁发机构（CA）是一个发布数字证书的可信实体。数字证书通过证书的命名主体证明公钥的所有权。在这个实验中，我们需要创建数字证书。首先我们自己成为一个根 CA，然后使用这个 CA 为其他人（例如服务器）颁发证书。在这个任务中，我们将使自己成为一 个根 CA，并为这个 CA 生成一个证书，根 CA 的证书是自签名的。

**配置文件 openssl.conf**：为了使用 OpenSSL 来创建证书，我们需要一个配置文件，这个文件由三个 OpenSSL 命令使用：ca、req 和 x509。该文件的手册可以在网上找到，默认情况下，OpenSSL 使用  /usr/lib/ssl/openssl.cnf 配置文件。因为我们要修改配置文件，需要将其复制到当前目录，并配置 OpenSSL 使用这个副本。

配置文件的  [CA default] 部分显示了我们需要准备的默认设置。其中，我们需要将 unique_subject = no 的注释去掉，允许生成具有相同主题（Subject）的证书。

```
[ CA_default ]

dir		= ./ceyewanCA		# Where everything is kept
certs		= $dir/certs		# Where the issued certs are kept
crl_dir		= $dir/crl		# Where the issued crl are kept
database	= $dir/index.txt	# database index file.
unique_subject	= no			# Set to 'no' to allow creation of
								# several certs with same subject.
new_certs_dir	= $dir/newcerts		# default place for new certs.

certificate	= $dir/cacert.pem 	# The CA certificate
serial		= $dir/serial 		# The current serial number
crlnumber	= $dir/crlnumber	# the current crl number
					# must be commented out to leave a V1 CRL
crl		= $dir/crl.pem 		# The current CRL
private_key	= $dir/private/cakey.pem# The private key
```

对于 index.txt 文件，只需要创建空文件；对于 serial 文件，在文件中输入一个字符串格式的数字即可（长度需要是偶数）。一旦建立了配置文件，就可以创建并发布证书了。

运行如下命令为我们的 CA 生成一个自签名的证书：

![image-20240313135756887](.\image-20240313135756887.png)

- `openssl`：表示要使用 OpenSSL 工具执行操作。
- `req`：表示执行证书请求和生成操作。
- `-x509`：指示 OpenSSL 生成自签名的 X.509 证书，而不是证书请求。
- `-newkey rsa:4096`：表示生成一个新的 RSA 密钥对，其中 RSA 算法的密钥长度为 4096 位。
- `-sha256`：指定使用 SHA-256 算法进行证书签名，以确保证书的安全性。
- `-days 3650`：指定生成的证书有效期为 3650 天（大约10年）。
- `-keyout ca.key`：指定生成的私钥文件名为 `ca.key`，该私钥将用于签署证书。
- `-out ca.crt`：指定生成的证书文件名为 `ca.crt`，这就是最终生成的自签名根证书。

综合起来，这条命令的目的是使用 RSA 算法生成一个新的 4096 位密钥对，然后使用该密钥对生成一个自签名的根证书（CA 证书），并将私钥保存在 `ca.key` 文件中，将证书保存在 `ca.crt` 文件中。这样就生成了一个自定义的 CA 证书，可以用于签署其他证书。

> OpenSSL 在执行时，会先从当前目录查找配置文件，再从默认配置文件读取，因此只要在我们改的配置文件目录下执行就行。

我们可以使用以下命令查看 x509 证书的解码内容和 RSA 密码。

```
openssl x509 -in ca.crt -text -noout
openssl rsa -in ca.key -text -noout
```

- `-text` ：意味着将内容解码为纯文本
- `-noout`： 意味着不打印编码版本

**证书的哪一部分表明这是 CA 的证书？**

![image-20240313142431319](./image-20240313142431319.png)

**CA:TRUE** 表示该证书是一个 CA（Certificate Authority）证书，即证书拥有签发其他证书的权限。

**证书的哪一部分表明这是一个自签名的证书？**

![image-20240313142632441](./image-20240313142632441.png)

- Issuer：表示证书的颁发者信息，即签发该证书的实体。
- Subject：表示证书的主题信息，即该证书所属的实体。

在这里，Subject 的信息与 Issuer 的信息相同，颁发者和所属者相同，因此是一个自签名证书。

**在 RSA 算法中，我们有一个公共指数 e，一个私有指数 d，一个模 n，和两个秘密数 p 和 q， 使得 n = pq。请在你的证书和密钥文件中确定这些元素的值。**

在一个 `ca.key` 文件中，通常包括 RSA 算法中的私钥值，这些值包括：

1. **Modulus (n)**：模数，即 RSA 公钥和私钥共享的大整数。
2. **Public Exponent (e)**：公共指数，用于加密数据。
3. **Private Exponent (d)**：私有指数，用于解密数据。
4. **First Prime Factor (p)**：第一个素数因子，用于生成私钥。
5. **Second Prime Factor (q)**：第二个素数因子，用于生成私钥。
6. **First Factor CRT Exponent (dP)**：第一个因子的 CRT（Chinese Remainder Theorem）指数。
7. **Second Factor CRT Exponent (dQ)**：第二个因子的 CRT 指数。
8. **Coefficient (qInv)**：模数 `q` 对 `p` 的乘法逆元素。

这些值组合在一起构成了 RSA 密钥对，其中公钥由模数 `n` 和公共指数 `e` 组成，私钥由模数 `n`、私有指数 `d`、素数因子 `p` 和 `q`、CRT 指数以及乘法逆元素组成。这些值在 `ca.key` 文件中以特定的格式存储，通常是 PEM 格式或其他密钥文件格式。

## Task 2: Generating a Certificate Request for Your Web Server

一个叫 ceyewan2024.com 的公司希望从我们的 CA 获得公钥证书。首先，它需要生成一个证书签名请求(CSR) ，其中基本上包括公司的公钥和身份信息。CSR 将被发送到 CA，CA 将验证请求中的身份信息，然后生成一个证书。

我们只需要去掉 `-x509`，就是生成 CSR 的命令了。

![image-20240313144152971](./image-20240313144152971.png)

该命令将生成一对公钥/私钥，然后从公钥创建一个证书签名请求。我们可以使用以下命令来查看 CSR 和私钥文件的解码内容：

```
openssl req -in server.csr -text -noout
openssl rsa -in server.key -text -noout
```

添加替代名称。许多网站都有不同的 URL，如 www.ceyewan.top 和 ceyewan.top 等。由于主机名匹配策略由浏览器强制执行，证书中的公共名称必须与服务器的主机名匹配，否则浏览器将拒绝通信。

为了允许证书有多个名称，x.509 规范定义了附加到证书的扩展名。这个扩展名称为 Subject Alternative Name (SAN)。使用 SAN 扩展名，可以在证书的 subjectAltName 字段中指定几个主机名。

![image-20240313150323752](./image-20240313150323752.png)

## Task 3: Generating a Certificate for your server

CSR 文件需要 CA 的签名才能形成证书。在现实世界中，CSR 文件通常被发送到一个受信任的 CA 来签名。在这个实验里，我们将使用我们自己的可信 CA 来生成证书。如下命令使用 CA 的 CA.crt 和 CA.key 将证书签名请求 server.csr 转换为 x509 证书 server.crt。

**复制扩展字段**：出于安全原因，配置文件中默认不允许 openssl ca 命令将拓展字段从请求复制到最终证书。我们将配置文件副本中的相关字段的注释关闭

![image-20240313151338409](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240313151338409.png)

执行命令如下：

![image-20240313151804508](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240313151804508.png)

其中，myCA_openssl.cnf 是我们刚刚修改过的配置文件。使用 policy_anything 策略，默认策略要求请求中的一些主题信息与 CA 证书中的主题信息相匹配，这个策略并不强制执行任何匹配规则。在签署证书之后，可以使用 `openssl x509 -in server.crt -text -noout` 查看证书内容。

## Task 4: Deploying Certificate in an Apache-Based HTTPS Website

在这个任务中，我们将看到网站如何使用公钥证书来保证网页浏览的安全。我们将建立一个基于 Apache 的 HTTPS 网站。Apache 服务器已经安装在我们的容器中，支持 HTTPS 协议。要创建一个 HTTPS 网站，我们只需要配置 Apache 服务器，这样它就知道从哪里获得私钥和证书。

修改服务器容器的配置如下：

![image-20240313155344817](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240313155344817.png)

我们可以知道，证书的配置文件夹地址，然后如果是 HTTPS 访问和 HTTP 访问的文件是不一样的。

![image-20240313155717398](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240313155717398.png)

完成上述配置后，执行 dcbuild & dcup 开启容器，进入 web 服务器容器执行  `service apache2 start` 开启网站程序。分别访问 HTTPS 和 HTTP 结果如下：

![image-20240313161503451](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240313161503451.png)

因为我们还没有配置证书可信，接下来，我们在浏览器中添加证书 ca.crt，然后再访问链接，发现建立了可信连接。

![image-20240314003323385](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240314003323385.png)

## Task 5: Launching a Man-In-The-Middle Attack

>   中间人攻击通常发生在安全通信的建立阶段，例如使用SSL/TLS加密的HTTPS连接。攻击者会冒充服务器与客户端建立连接，同时与服务器和客户端分别建立独立的连接。攻击者可以生成自己的伪造证书，与客户端建立安全连接并将自己的伪造证书发送给客户端，同时与服务器建立另一个安全连接并将客户端的请求发送给服务器。这样，攻击者就能够在客户端和服务器之间的通信中拦截、查看和修改数据。
>
>   为了防止中间人攻击，通常使用证书颁发机构（CA）签发的可信证书来验证服务器的身份。客户端会对服务器的证书进行验证，包括验证证书的有效性、合法性和所属的颁发机构等。

几种方法可以让用户的 HTTPS 请求到达我们的 Web 服务器。

-   一种方法是攻击路由，这样用户的 HTTPS 请求就被路由到我们的 Web 服务器。
-   另一种方法是攻击 DNS，所以当受害者的机器试图找出目标网络服务器的 IP 地址，它得到我们的网络服务器的 IP 地址。

在这个任务中，我们模拟了攻击 DNS 的方法。我们只需修改受害者机器的 /etc/hosts 文件，通过将主机名 [www.example.com](http://www.example.com/) 映射到我们的恶意网络服务器，来模拟 DNS 缓存定位攻击的结果，而不是启动一个实际的 DNS 域名服务器缓存污染。

因为域名和证书并不匹配，故浏览器会提示不安全。

![image-20240314103445152](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240314103445152.png)

## Task 6: Launching a Man-In-The-Middle Attack with a Compromised CA

>   在这个任务中，我们假设在 Task 1 中创建的根 CA 受到攻击者的攻击，并且它的私钥被盗取了。因此，攻击者可以使用此 CA 的私钥生成任意证书。在这项任务中，我们将看到这种妥协的后果。请设计一个实验来证明攻击者可以成功地在任何 HTTPS 网站上启动 MITM 攻击。您可以使用在 Task 5 中创建的相同设置，但是这一次，您需要证明 MITM 攻击是成功的，也就是说，当受害者试图访问一个网站但是登录到 MITM 攻击者的假网站时，浏览器不会引起任何怀疑。

在 task5 中的叙述描述了我们使用自己的**自签名CA导入到浏览器**的情况，但是如果**根CA私钥**被盗取了会有更严重的后果：

1.  伪造证书：攻击者可以使用根证书的私钥签发伪造的证书，模拟合法的网站或服务，使其看起来具有合法的身份和可信的安全性。这将导致用户误认为与真实网站或服务进行通信，从而暴露他们的敏感信息。
2.  中间人攻击：通过拦截通信并使用伪造的证书，攻击者可以进行中间人攻击，监视和修改通信内容，窃取敏感信息或注入恶意内容。这对用户、网站和系统的安全性构成了严重威胁。
3.  篡改和劫持：攻击者可以篡改通过伪造证书进行加密的通信内容，例如修改下载文件、注入恶意代码或劫持用户的会话。
4.  信任破裂：如果根证书的私钥被盗取，信任链中的所有证书都将受到威胁，导致整个系统的信任破裂。这将对证书基础设施的安全性和可信度产生长期的负面影响。

实际上，攻击已经完成了，www.ceyewan2024.com 如果去中间人攻击另一个由我们自签名的 CA 颁发的证书的网站，攻击是会成功的。因为我们有 CA 就能伪造一个证书，欺骗浏览器。