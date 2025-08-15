---
title: Windows/WSL/Linux/Docker+VSCode开发环境配置
categories:
  - ForFun
tags:
  - Dev Tips
draft: false
slug: b638e272
date: 2022-06-26 22:28:24
---

前几天重装了一下系统，于是从头开始配置了一下开发环境，在这里记录一下。主要就是使用虚拟机、`wsl`、`vscode` 以及 `docker` 这几个工具。

## windows 环境 C/C++ 开发环境配置

### git 安装

访问官网，`https://git-scm.com/` ，然后直接下载安装即可。

### windows terminal 安装

使用微软商店搜素下载即可。

### 使用 windows terminal 打开 git bash

打开 `windows terminal` ，点击上方下箭头，然后设置，然后点击添加新的配置文件，内容如下：

![image-20220626162925437](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20220626162925437.png)

命令行和图标我是使用的默认安装路径，这个根据安装目录更改就行，外观就仁者见仁智者见智了。这时，就可以在 `windows terminal` 中使用 `git bash` 了。但是显示中文会有一点点问题（如果没有问题的话不需要执行下面的操作）。在文件 `"C:\Program Files\Git\etc\bash.bashrc"` 末尾添加一行 `export LC_ALL=en_US.UTF-8  ` 即可。文件具体位置由安装目录决定。

最终效果如下：

![image-20220626163648872](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20220626163648872.png)

### 安装 gcc 套件

之前我都是从网上下载 `mingw` 文件，解压到指定目录，然后添加环境变量，感觉有点麻烦。可以从 `http://www.equation.com/servlet/equation.cmd?fa=fortran` 直接下载 `exe` 文件，傻瓜式安装即可。安装完成后打开终端，输入 `gcc --version` 、`g++ --version` 、`gdb --version` 和 `make --version` 查看是否安装成功。

![image-20220626164835575](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20220626164835575.png)

### 安装 vscode

访问官网，`https://code.visualstudio.com/` ，下载安装即可。安装后打开，打开后会提示是否安装中文插件，自行选择即可。我建议在某个盘下面创建一个文件夹，比如叫做 `CodeField` 用来存放所有的代码，然后在里面创建 `CodeCpp`、`CodePy` 等存放不同语言的代码。下面有一点点错误，第七点是 `g++ hello.cpp` 和 `./a.exe` 。

![image-20220626170528881](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20220626170528881.png)

使用 `vscode` 而不是 `vs` 或者 `cLion` 等 `IDE` 是因为，我经常要写一个一个文件的小程序，搞 `project` 太麻烦了。更重要的是，`vscode` 是宇宙第一编辑器！！！

### github ssh 认证

写代码总要用到 `git` 吧，现在都是用 `ssh` 认证了，来配置一下吧。

```bash
# 这两行初次使用需要
git config --global user.name "xxx"
git config --global user.email "xxx@xxx.com"
# 我乐意使用 ed25519 ，网上都是用 rsa ，一直回车到结束（之前生成过就没必要再生成了
ssh-keygen -t ed25519 -C "xxx@xxx.com"
# 生成的文件在 C:\Users\xxx\.ssh
# 将文件夹里面的 .pub(公钥) 复制添加到 github 等的 ssh key 中
# 测试连接是否完成
ssh -T git@github.com
```

到此，环境配置基本完成，你可以开心的 `code` 了，细节问题在使用中逐渐完善即可。

## Linux 环境 C/C++ 开发环境配置

直接虚拟机或者双系统，这两个我都折腾过，还是不太方便。因此，这里主要讲在 `windows` 下使用 `vscode` 进行远程 `Linux` 环境开发。

### 安装 WSL

打开终端，推荐使用 `windows terminal`，需要管理员模式打开。输入命令 `wsl --install`，等待安装完成即可。

### 安装 Ubuntu

打开微软应用商店，搜索 `ubuntu` 自行选择版本安装即可。安装完成后，在终端中一个就有 `ubuntu` 选项了，打开，完成一些基本设置，然后就有一个全新的 `ubuntu` 系统了。首先还是推荐换源，清华源是一个很好的选择，`https://mirrors.tuna.tsinghua.edu.cn/help/ubuntu/`。执行 `sudo nano /etc/apt/sources.list`，将原本内容注释掉，将清华源加入，然后退出。执行 `sudo apt update` 和 `sudo apt upgrade` 。安装 `gcc` 的命令为 `sudo apt install gcc`，其他的以此类推。

### vscode 安装 remote development 插件组件

左侧栏第五个是插件商店，搜索安装即可。完成后，左下角会出现一个类型闪电的标，点击，然后选择 `new WSL windows` ，不出意外的话就会进入到 `wsl` 了，左下角会显示。此时在这个窗口操作就是纯正的 `Linux` 环境。`vscode` 提供了代码编辑器和终端的功能，足矣。

## 虚拟机 Linux + remote ssh 连接

### 安装 vmware workstation

这是一个让你运行虚拟机的软件，进入官网，`https://www.vmware.com/cn/products/workstation-pro.html` ，下载安装即可，这个是付费软件，但是网上激活码一搜一大堆。

### 下载一个 Linux 发行版的 iso 镜像

我选择的是 `manjaro`，因为已经有一个 `ubuntu` 的 `wsl` 发行版了。官网  `https://manjaro.org/download/`，推荐 `kde` 版本，下载即可。

### vmware 安装 manjaro

依次大概是新建虚拟机，典型，安装程序映射文件（`iso`）（选择刚刚下载的 `iso` 镜像即可），`Linux` 和其他 `Linux 5.x 64位`，然后就是自行选择了，名称啥的随意。注意内存大小和存储大小，尽量大点，推荐 `8G + 40G` 。然后就可以打开这个虚拟机了，剩下的内容和初次安装 `windows` 大差不差。

### vscode 远程连接 manjaro

`manjaro` 安装 `ssh` 服务，`sudo pacman -Sy openssh` ，然后开启服务 `systemctl start sshd.service && systemctl enable sshd.service ` 。执行 `sudo pacman -Sy net-tools` ，然后执行 `ifconfig` ，将 `ip` 地址记住。

打开本机的 `vscode`，点击左侧的 `remote explorer` 然后将选项修改为 `ssh targets`，再点击齿轮，然后选择第一个，输入内容：

![image-20220626175145422](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20220626175145422.png)

第一个随便填，第二个填 `ip` 地址，第三个填用户名。然后就能远程连接了。最后，如果需要配置无密码连接需要使用 `ssh` 认证，这个东西如果用过 `github` 的话很容易搞。复制上面连接 `github` 时的 `.pub` (公钥)，在 `manjaro` 中的 `~/.ssh` 文件夹中(没有这个文件夹就创建)创建一个文件 `authorized_keys` ，将复制的 `key` 写入，即可免密连接。

这样，我们只用打开虚拟机，然后就不用操作了，使用 `vscode` 远程连接即可。连接云服务器也是这样的操作。

## docker + remote containers 连接

### 安装 docker 

访问官网，安装即可。最好能配置换源。在设置里查找 `docker engine` ，修改内容如下：

```json
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "features": {
    "buildkit": true
  },
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn"
  ]
}
```

### docker 使用

这里用配置一个 `mysql` 环境为例：

```bash
# 查找 mysql 镜像
docker search mysql
# 拉取/下载镜像
docker pull [xxx] # xxx 是你刚刚 search 排行第一的 NAME 
# 列出镜像(应该可以看到刚刚下载的 mysql)
docker image ls
# 此时你也能选择删除它
docker image rm [选项] <镜像1> [<镜像2> ...]
# 简单启动镜像，创建一个叫做 mysql-demo 的容器(宿主机的 3306 被本地的 mysql 用了)
docker run --name mysql-demo -p 3307:3306 -e MYSQL_ROOT_PASSWORD=password -d mysql
# 查看容器，应该就能看到
docker container ls
# 进入容器（然后就会发现终端变了，因为我们进入了容器里面的终端）
docker exec -it mysql-demo /bin/bash
# 然后就能愉快的使用 mysql 了
mysql -u root -p password
# 当你容器运行起来了之后，也可以不进入容器，在本地远程连接容器中的数据库，注意端口
mysql 127.0.0.1 -P 3307 -u root -p
# 退出容器
exit
# 停止容器 
docker stop mysql-demo
# 删除容器
docker container rm mysql-demo
```

### vscode 远程连接 container

终端还是用不习惯，毕竟有些容器里面甚至连 `vim` 都没有，这个时候就要祭出我们的宇宙最强编辑器 `vscode` 了。安装 `docker` 和 `remote-container` 这两个插件。然后就会发现侧边栏出现了一个小鲸鱼，点开，就可以看到镜像和容器了。

我们就可以使用插件来管理容器和镜像了，如果要进入镜像，`ctrl + shift + p` 打开 `vscode` 的命令行，输入 `Remote-container：attach to running container` 回车，然后就会看到当前正在运行的容器，选择需要的进入即可。本地文件传入容器，可以在创建容器时使用 `-v /home/xxx/xxx/:/share` 就会把本地的文件挂载到容器中的 `share` 文件夹下。

![image-20220626214647085](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20220626214647085.png)

## 小结

配环境真的就是一个熟练工，配过两次就会了，没配过就是一头雾水。说实话，我这一篇够别人水十多篇了，一个方面是写的很多，几乎包括了这两年折腾过的所有环境配置；另一方面，是因为我确实写的很简略，有很多都是回忆的大致操作。不明白的地方可以根据关键词搜索一下，或者联系我。