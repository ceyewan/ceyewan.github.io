---
title: MacOS下开发环境配置和软件推荐
categories:
  - ForFun
tags:
  - MacOS
  - DevTips
abbrlink: 63f70079
draft: false
slug: 2024-03-24 22:35:09
---

Mac 真香，虽然我只是用的丐版。拿到 Mac 的第一步，当然就是配置开发环境啦。

## Terminal

还是得先确保安装了 `zsh`，然后再安装 `oh-my-zsh` 。

搜索 `gitee oh-my-zsh` 查看如何安装。下面也提供一个一行配置方法：

```shell
REMOTE=https://gitee.com/mirrors/oh-my-zsh.git sh -c "$(curl -fsSL https://gitee.com/mirrors/oh-my-zsh/raw/master/tools/install.sh)"
```

跟着流程走完，可以修改一下主题（其实默认的就很简洁了）：

```shell
vim ~/.zshrc # 编辑配置文件
ZSH_THEME="random" # 找到 ZSH_THEME 修改为 random （随机），或者任何你喜欢的主题，如 apple 
```

然后小小的配置一下：

```shell
# 语法高亮
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git $ZSH_CUSTOM/plugins/zsh-syntax-highlighting
# 自动补全
git clone https://github.com/zsh-users/zsh-autosuggestions $ZSH_CUSTOM/plugins/zsh-autosuggestions
# 修改 ~/.zshrc 里的 plugins 如下：
plugins=(
  git
  zsh-syntax-highlighting
  zsh-autosuggestions
)
# 这样在输入命令时会有提示，并且还会有语法正确与否的提示
```

## HomeBrew

MacOS 下的 brew 就和 Ubuntu 下的 apt 差不多，安装软件就可以使用 `brew install xxx` 啦。以武汉为例，我亲测还是中科大的源比较快。官网有安装教程：

[Homebrew 源使用帮助 — USTC Mirror Help 文档](https://mirrors.ustc.edu.cn/help/brew.git.html)

## Xcode

首先，在 App Store 中安装 Xcode，然后在命令行中输入 `xcode-select --install`，大概需要安装挺久的，很大一个开发包，包括很多东西，比如 git 之类的。接下来，输入 clang -v 看看是否安装成功。

Mac 还是比较友好的，输入 gcc g++ 也是 ok 的，会被链接到 clang。

## VScode

试过一段时间 CLoin，还是笨重了点，我平等的不喜欢任何一个占大量内存的软件。而且 jb 家的软件用不惯，快捷键操作啥的都不熟。虽然感觉写大型程序时，迟早得用到，但是目前还是达咩吧。

以前，我用的是 C/C++ 插件，后来发现 clangd 很好用，更加优雅！下载这个插件后，打开 vscode 的 setting.json，输入以下配置：

```json
// "clangd.path": "/Users/ceyewan/Important/clangd-15/bin/clangd",
"clangd.checkUpdates": true,
"clangd.fallbackFlags": [
    "-std=c++14"
],
"clangd.arguments": [
    "--clang-tidy", // 开启clang-tidy
    "--completion-style=detailed", // 详细补全
    "--header-insertion=never",
    "--pch-storage=disk", // 如果内存够大可以关闭这个选项
    "--log=error",
    "--j=5", // 后台线程数，可根据机器配置自行调整
    "--background-index",
    "--query-driver=/usr/bin/clang,/usr/bin/clang++",
],
"[cpp]": {
    "editor.defaultFormatter": "llvm-vs-code-extensions.vscode-clangd"
},
```

~~"clangd.path" 这行我没有用默认的，Xcode 安装的 clangd 版本是 14.0，没有 auto 类型推导这种功能，所以我从 github 上下载了最新版，就不加入环境变量了，直接指定就好了。~~MacOS 上 clangd 目前更新到 15 了，有我需要的类型推导了，所以直接用系统自带的就好了。

上面我们指定使用 `-std=c++14`，这样有一个小问题，就是在写纯 C 语言代码时会被当做 C++ 代码来处理。另一种方法就是在项目下写一个配置文件，但是我又不想每个目录下都配置一下，很麻烦。第三个办法就是通过一个全局的配置文件来处理，编辑文件 `~/Library/Preferences/clangd/config.yaml` 如下：

```yaml
# Fragment specific to C++ source files
If:
    PathMatch: [.*\.cpp, .*\.cxx, .*\.cc, .*\.h, .*\.hpp, .*\.hxx]
CompileFlags:
    Add:
        - "-std=c++14"
---
# Fragment specific to C source files
If:
    PathMatch: [.*\.c]
CompileFlags:
    Add:
        - "-std=c99"
```

C++ 开发我用的是 GitHub Theme + Error Lens + clangd 这三个插件，效果如下：

![image-20230321221258813](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20230321221258813.png)

还有一个我需要经常用的是 Remote-SSH，这点 vscode 也比 jb 家强。

## 图标替换

现在 Mac 的系统基本都是使用扁平图标了，但是总有个别软件就不一样，还是圆形或者奇奇怪怪的形状，我们可以自定义图标修改它。

1.   从 [macOSicons](https://macosicons.com/#/) 下载需要的图标。
2.   显示需要更改图标的软件的简介，依次点击访达、应用程序，右键需要更改图标的程序，选择实现简介。
3.   将下载的 icns 文件拖入到简介左上角的图标位置，即可完成替换。

![image-20240324215514835](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240324215514835.png)

好了，来一张全家福吧，一家人就是要整整齐齐！

![image-20240324221529643](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240324221529643.png)

## 系统设置

把设置玩明白了，电脑才会好用。

1.   控制中心，最下面自动隐藏和显示菜单栏，修改为仅在全屏幕视图下。这样全屏看视频就没那一条亮带影响观感了。
2.   隐私与安全性，当打开一个网上下载的软件被系统拦截了之后，可以在这里允许打开。
3.   桌面与程序坞，修改程序坞大小，将放大效果设置到最大，买 Mac 不就是为了鼠标滑过时放大效果。最小化窗口使用神奇效果。**连按窗口标题栏以缩放。**打开弹跳打开应用程序，打开台前调度。
4.   桌面与程序坞，最下面，触发角。比如可以将左上角设置为锁定屏幕，这样临时有事可以将鼠标移动到左上角，直接锁定屏幕，保护隐私。
5.   通用，共享，互联网共享。我连接的是以太网，可以使用 WIFI 共享（需要开启 WIFI 先）。Mac 能 24 小时开机，用来在寝室开个热点还是可以的。

## 软件推荐

一些我从 win 来带来的习惯，总得想办法满足哈

### Snipaste

截图软件。我知道 Mac 自带的截图很好，使用 Ctrl+Shift+3 全屏截图，Ctrl+Shift+4 选择区域截图，然后按下空格键之后还可以定位应用窗口，能够保留 R 角，这点很细节。

不过截图默认是保持到桌面的，应该是吧？忘记了。可以打开截图应用程序，然后选择截图方式并在选项中将默认保存位置修改为剪切板。

![image-20240324220200108](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240324220200108.png)

但是习惯了没办法，按 F1 一个键比按下三个键要简单一点吧。snipaste 还支持贴图，最重要的是，它还支持截图回溯。比如你想找三天前截的一张图，就可以随便截一张图之后，按下 `,` 键向前回溯！我居然最近才知道。

然后截图之后，一般都会有一些需要编辑的地方，这点默认的截图软件也做不到。不过它也有缺点，就是不支持 OCR，目前我 OCR 的需求比较低，微信和 QQ 的 OCR 就够用了，就没去尝试那些有 OCR 功能的。

另外还有长截屏也是不支持的，不过对我而言任然是优点大于劣势。

>   目前已经在用 Longshot 了。

### NeatDownloadManager

多线程下载器，在 Win 上一直用的 IDM，结果没有 Mac 版，找了个替代品，很好用，基本上可以当成 IDM 用，配置一下代理加上 ClashX 基本上可以把代理速度跑满。

![image-20240324220639975](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240324220639975.png)

浏览器插件我没有使用，只有需要这个下载器的时候，我会手动将 URL 复制过来，浏览器挂太多插件，乱七八糟的，丑死了。

### Rectangle

分屏软件，自带的分屏真心不好操作，win 键 + 上下左右箭头已经把我养刁了。这个软件我们使用 Ctrl+Option+方向键就好了，还有好多快捷键，好用！

>   目前由 Raycast 代替。

### 腾讯柠檬清理

企鹅家居然有这么良心的产品，我哭死。强迫症希望能时时刻刻看到系统占用。磁盘深度分析功能好评，使用一年多了，希望它能保持初心吧，不要变质。

### Typora

钱都花了，用着呗，还能咋滴。写 MarkDown 真的很省事，搭配 PicGo 很方便的上传图片，调整格式什么的还有快捷键之类的，大大提高了我的效率，导致我写了三年 MarkDown，很多格式都还是不熟悉。

### BatterDisplay

放假回家的时候，我需要外接一台 2K 显示器，由于 Mac 的显示策略，在 2K 显示器上的显示效果很差，这个软件可以一键开启 HiDPI。并且，我的显示器亮度不支持调到很低，晚上很暗的时候屏幕就显得太亮了，而这个软件可以打破硬件的亮度最低值。

### PlayCover

支持在 m 芯片上跑 iOS 应用，[Decrypt IPA Store](https://decrypt.day/) 可以下载 ipa 文件。不过我现在就下了一个酷狗概念版，免费听歌，界面清爽，移动端都适用。

>   目前用的 apple music，所以它也没用了。

### VidHub

一款本地播放软件，搭配 Alist 挂载夸克、阿里等云盘，可以创建自己的影视资源库。如果再用上小雅的话，那就更加爽歪歪了，第一次知道阿里云盘不限速有多香。

其他软件：

- 小红书：现在 MAC 原生支持小红书了，在 MAC 上刷小红书好爽。
- 坚果云：使用坚果云在 Windows 和 Mac 之间同步文件，Onedrive 也可以吧，但总是要我登录登录登录。
- Pa.per：壁纸软件，一个壁纸看久了总会腻的，这个软件只有一个功能，可以帮你自动换壁纸。
- ~~UPDF：一款颜值很高的 PDF 阅读器，编辑啥的功能我用不着。~~每次打开都要我登录，我就知道该淘汰它了。没有找到好用的，~~目前用的系统自带的预览，其实够用了。~~现在使用 skim 和 Adobe acrobat，前者轻量化，看看 PDF，后者用来做一些 PDF 编辑工作。
- ~~搜狗输入法：我一般不想安装第三方输入法的，但是自带的输入法不能按 shift 切换中英文，这比杀了我还难受。无奈只能选择第三方。搜狗是为数不多支持 linux 的输入法了，所以在选择第三方的时候我选他家。~~  换成了鼠须管。
- ChatGPT：Mac 客户端程序，常驻后台，比用浏览器方便些。