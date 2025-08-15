---
title: Windows+Manjaro双系统的安装与配置
categories:
  - ForFun
tags:
  - Dev Tips
  - Dual System
draft: false
slug: 4a1a11d9
date: 2022-07-10 00:25:51
---

## 1 双系统安装

下载 `manjaro kde` 镜像文件，使用 `rufus` 将镜像写入到 U 盘中（搜索关键词即可）。在 `windows` 中打开磁盘管理，压缩出一个 `100G` 的卷（百度解决）。重启系统，狂按 `F12` （不同电脑不同），选择 U 盘启动。然后就是正常的安装一个系统（驱动建议选择 free），分区的话我没搞，直接默认了。但是要注意安装位置选择之前压缩出的分区，不要把 `windows` 给覆盖掉了！！！

## 2 双系统时间统一

因为 `windows` 和 `linux` 的时间算法不一样，那么就需要修改一下，这里我选择改 `linux`：

```shell
sudo timedatectl set-local-rtc true
```

## 3 分辨率

调整光标、分辨率、缩放等适配显示屏。

## 4 软件源

执行命令：

```shell
sudo pacman-mirrors -i -c China -m rank
```

选择最快（最顺眼）的一个软件源即可。如果之后安装东西有报什么不信任、密钥之类的错误，可以把 `/etc/pacman.conf` 文件里的 `SigLevel` 设置为 `Optional TrustAll` （不推荐，但管用）。

也可以配置一个 `arch` 源（不建议），在文件中添加内容如下：

```
[archlinuxcn]
SigLevel = Optional TrustAll
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinuxcn/$arch
```

## 5 更新系统

```shell
sudo pacman -Syyu
```

## 6 安装 yay

```shell
sudo pacman -Sy yay
```

## 7 安装输入法

```shell
# 安装 fcitx5 框架
yay -S fcitx5-im
# 配置环境变量
nano ~/.pam_environment
# 添加内容如下：
GTK_IM_MODULE DEFAULT=fcitx
QT_IM_MODULE  DEFAULT=fcitx
XMODIFIERS    DEFAULT=\@im=fcitx
SDL_IM_MODULE DEFAULT=fcitx
# 安装输入法引擎
yay -S fcitx5-rime
# 安装输入方案
yay -S rime-cloverpinyin
# 如果出错需要执行下面这步
yay -S base-devel
# 创建并写入ime-cloverpinyin的输入方案
nano ~/.local/share/fcitx5/rime/default.custom.yaml
# 添加内容如下：
patch:
  "menu/page_size": 7
  schema_list:
    - schema: clover
# 安装中文维基百科词库
yay -S fcitx5-pinyin-zhwiki-rime
# 配置主题
yay -S fcitx5-material-color
```

这个输入法会有很多 `emoji` 表情，还有我讨厌的半角全角切换，我们可以去配置文件中修改以下，配置文件在 `/home/ceyewan/.local/share/fcitx5/rime/build/clover.schema.yaml` 中，按照自己的喜好修改。我就注释了以下几行：

```yaml
emoji_suggestion:
  opencc_config: # emoji.json
  option_name: # emoji_suggestion
  tips: # all

# - {accept: "Shift+space", toggle: full_shape, when: always}
```


之前使用过一段时间的搜狗输入法，输入体验较好，使用体验较差。对中文输入支持较好，但是 bug 也多。不知道为什么，我好像装不上了，就用这个了。

## 8 安装 QQ 微信和腾讯会议

微信我比较推荐使用下面这个命令安装，这个看名字应该是统信版的。QQ 的话可以使用 `icalingua++` 。这两个虽然不是特别好用，但至少还是能用的咯。我不是很推荐 `wine` ，感觉太臃肿了。

```shell
yay -Sy wechat-uos
sudo pacman -Sy icalingua++
yay -Sy wemeet-bin      
```

其实有一个对 `linux` 支持比较好的平台，就是字节跳动的飞书。

## 9 安装 oh-my-zsh

首先，还是得先确保安装了 `zsh`，然后再安装 `oh-my-zsh` 。

搜索 `gitee oh-my-zsh` 查看如何安装。下面也提供一个一行配置方法：

```shell
REMOTE=https://gitee.com/mirrors/oh-my-zsh.git sh -c "$(curl -fsSL https://gitee.com/mirrors/oh-my-zsh/raw/master/tools/install.sh)"
```

跟着流程走完，可以修改一下主题（其实默认的就很简洁了）：

```shell
vim ~/.zshrc # 编辑配置文件
ZSH_THEME="random" # 找到 ZSH_THEME 修改为 random （随机），或者任何你喜欢的主题 
```

然后小小的配置一下：

```shell
# 下载 powerlevel10k 主题
git clone https://github.com/romkatv/powerlevel10k.git $ZSH_CUSTOM/themes/powerlevel10k
# 导入主题
echo 'source $ZSH_CUSTOM/themes/powerlevel10k/powerlevel10k.zsh-theme' >>! ~/.zshrc
# 修改 ~/.zshrc 里的 ZSH_THEME 为 "powerlevel10k/powerlevel10k"
# 然后重新打开终端，跟着提示配置好这个主题（后续需要重新配置，执行 p10k configure 即可）

# 语法高亮
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git $ZSH_CUSTOM/plugins/zsh-syntax-highlighting
# 自动补全
git clone https://github.com/zsh-users/zsh-autosuggestions $ZSH_CUSTOM/plugins/zsh-autosuggestions
# 修改 ~/.zshrc 里的 plugins 如下：
plugins=(
  zsh-syntax-highlighting
  zsh-autosuggestions
)
# 这样在输入命令时会有提示，并且还会有语法正确与否的提示
```

## 10 配置 konsole

依次点击设置 -> 编辑当前方案 -> 外观 -> 编辑，这里就可以添加一个背景壁纸（实测壁纸分辨率需要在 `1280 × 720` 左右。可能是我电脑的问题，分辨率太大了显示有问题。

其他的配置在设置里慢慢折腾，看个人喜好咯。总体效果如下（全局的配置稍后会写）：

![image-20220720190135100](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20220720190135100.png)

## 11 安装 vscode

```shell
yay -Sy visual-studio-code-bin
```

`vscode` 的配置就是仁者见仁智者见智了。我还是会先下载一个 `consolas` 字体，然后把代码默认字体改成这个，之前用 windows 看习惯了，不愿意再改。然后我也会关闭掉右边的 `minimap` ，因为我屏幕确实太小了。

## 12 科学上网

安装 `v2raya` 好像需要一个 `arch` 源，可以把上面提到的那个源加入，安装完之后也可以再把源删了。

```shell
sudo pacman -Sy v2ray
sudo pacman -Sy v2raya
sudo systemctl start v2raya.service
# 开机自启，可选
sudo systenctl enable v2raya.service
```

然后浏览器访问网站 `localhost:2017` 你就能开心的上网了。

## 13 安装 docker

```shell
# 安装 docker 
sudo pacman -Sy docker
# 开启 docker 服务
sudo systemctl start docker.service
# 开机自启，可选
sudo systemctl enble docker.service
# 建立 docker 组
sudo groupadd docker
# 将当前用户加入 docker 组
sudo usermod -aG docker $USER
# 添加访问和执行权限
sudo chmod a+rw /var/run/docker.sock
# 重启一下 docker 服务
sudo systemctl restart docker.service
# 查看是否配置过镜像加速器（显然是没有的，有的话也不会需要看这个了）
systemctl cat docker | grep '\-\-registry\-mirror'
# 添加如下镜像到指定文件
sudo vim /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://docker.mirrors.ustc.edu.cn"
  ]
}AppImage
# 重启一下服务
sudo systemctl daemon-reload
sudo systemctl restart docker
# 查看镜像是否生效(如果能看到刚刚添加的镜像)
docker info
```

同样，可以使用 `vscode + remote-container`（插件） + `docker`（插件）来使用 `docker` 。

## 14 配置浏览器

我还是喜欢用谷歌，必备的拓展：

```
yay -Sy google-chrome
xxx 新标签页（自定义新标签页）
Adblock Plus（屏蔽广告）
Tampermonkey(安装 csdn 插件，对抗毒瘤)
```

## 15 FlameShot

截图软件，安装后需要配置一下截图快捷键。

```shell
sudo pacman -Sy flameshot
```

设置->快捷键->自定义快捷键->编辑->新建->全局快捷键->命令/URL。操作为：`/usr/bin/flameshot gui`，触发器我使用的是 `F1` ，这个看个人习惯。

![image-20220711165255047](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20220711165255047.png)

## 16 typora + picgo

`markdown` 编辑器 + 图床配置。这两个都可以去 `github` 上下载 `AppImage` 文件。`typora` 图片上传服务选择 `PicGo(App)` ，路径如下，`/home/ceyewan/Applications/PicGo.AppImage`，这个路径只能自己去复制过来。当然也能使用 `yay` 来安装。

## 17 系统美化

配置一下 `dock` 栏，虽然美化的终点是默认，但是我还是想折腾一下。。。

```shell
yay -S latte-dock # 安装
# 运行 latte 后右键 dock 栏，进行一些简单的配置，将常用软件固定到 dock 栏中
# 添加一个面板，我选择放在最上面，用来显示必要的 wifi 功能之类的
```

打开系统设置，将我圈出来的这些东西都取下载同一个主题，这里我选择的是 `sweet` 。大家自行选择喜欢的，或者混搭风格。如果自带的主题商店打不开的话，就需要自己去网上下载主题然后解压到指定目录了。

![image-20220720191346008](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20220720191346008.png)

## 18 配置鼠标滚动速度

`manjaro` 的滚动速度简直不能忍，网上搜了一番之后，结论如下：

```shell
sudo pacman -Sy imwheel
vim ~/.imwheelrc
  ".*"
  None,      Up,   Button4, 4
  None,      Down, Button5, 4
  Control_L, Up,   Control_L|Button4
  Control_L, Down, Control_L|Button5
  Shift_L,   Up,   Shift_L|Button4
  Shift_L,   Down, Shift_L|Button5
imwheel # 启动
```

开机启动我一直没搞定，手动操作也是 ok 的，问题不大。

## 19 文件同步

我们可以使用坚果云来进行文件同步，这样在 `manjaro`、`windows` 和手机上同步数据都比较方便

```
yay -Sy nutstore
```

## 20 clion 的安装

首先，我们去官网下载安装包，然后执行以下命令解压并执行程序。

```bash
tar -zxvf CLion-xxx.tar.gz
cd Clion-xxx/bin
./clion.sh # 启动程序
```

总是这样执行也不方便，在打开程序后，`tools -> create desktop entry` 可以创建桌面快捷方式。下次启动就很方便了。

## 21 安装 VMware-Workstation

找不到当时参考的博客了，那篇写的真的是很简练，可惜找不到了。于是我通过查看 `zsh` 的 `history` 找到了当时执行的一些命令。这也是我这篇博客存在的意义吧，把屎里淘金的金记录下来，方便下一次的我。

```bash
# 查看当前的内核版本
uname -a
Linux ceyewan 5.15.74-3-MANJARO #1 SMP PREEMPT Sat Oct 15 13:39:11 UTC 2022 x86_64 GNU/Linux
# 安装依赖，因为我是 5.15 大版本，所以我安装的是 linux-headers515
sudo pacman -Sy linux-headers515 
sudo pacman -Sy base-devel # 在 ubuntu中这个包叫 build-essential
# 创建 init.d 文件夹
sudo mkdir /etc/init.d
# 从官网下载安装包 
VMware-Workstation-Full-16.2.4-20089737.x86_64.bundle
# 安装 vmware
sudo sh ./VMware-Workstation-Full-16.2.4-20089737.x86_64.bundle
# 在使用之前需要启动 vmware 相关服务
sudo /etc/init.d/vmware start
```

## 22 安装 todesk 远程控制

官网有明确的安装教程，并且支持 `Arch linux`，我愿称之为良心软件。在官网下载好安装包后，执行下面这个命令就可以安装了。

```bash
sudo pacman -U todesk_4.1.0_x86_64.pkg.tar.zst
```

## 23 copytranslator 翻译软件

看英文文献时，还是需要一个方便的翻译工具的。[官网](https://copytranslator.github.io/)，我们可以在官网下载 `AppImage` 也可以使用 `yay -Sy copytranslator` 安装。

## 24 音乐软件

目前国内的 QQ 音乐和网易云音乐都有 `linux` 版本，可以直接使用 `pacman` 或者 `yay` 进行安装。腾讯是这样的，看到网易云提供了 `deb` 包，才会开始做 `linux`。QQ 和微信没有竞品就开始摆烂。所以我选择使用 `spotify`。

## 25 小结

![desktop](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/2022-11-05_16-15.png)