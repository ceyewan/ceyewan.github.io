---
categories:
- Golang
date: '2025-06-28T21:53:07+08:00'
draft: false
slug: a793fe12
summary: Go项目热重载工具air提升开发效率
tags:
- air
title: Go 热重载工具 Air
---

air 是一款专为 Go 项目设计的**热重载工具**，它能够在开发者保存代码文件时自动触发重新编译并重启程序。相比直接使用 `go run` 命令，air 提供了更多实用功能：

- 支持自定义构建和运行命令
- 避免路径错误和日志丢失问题
- 配置灵活且使用简单
- 显著提升本地开发效率

## 1 安装

安装 air 非常简单，只需执行以下命令：

```shell
go install github.com/air-verse/air@latest
```

- `go get` 主要作用是**将某个模块加入 go.mod**，并下载源码到本地缓存（GOPATH/pkg/mod）；
- `go install` 主要用于**安装 CLI 工具或构建你自己的可执行程序**。

## 2 使用

### 2.1 基础使用

最简单的使用方式是直接在项目目录下运行：

```shell
air
```

这会使用默认配置启动热重载功能。但更推荐的方式是通过配置文件进行详细配置。

### 2.2 配置文件

执行以下命令生成默认配置文件：

```shell
air init
```

这会生成一个 `.air.toml` 文件，内容类似：

```toml
# .air.toml
[build]
cmd = "go build -o ./tmp/main ./main.go"  # 指定构建命令，产出你要执行的 ./main
bin = "./tmp/main"                        # air 会运行这个二进制文件
full_bin = true                           # 使用完整路径（不加的话在某些环境变量下会找不到）

[run]
cmd = ""                                  # 不加的话 air 会自动运行上面 build 出来的 bin

[log]
time = true
```

### 2.3 配置详解

1. **构建配置**：
    - `cmd`：指定构建命令
    - `bin`：指定构建输出的可执行文件路径
    - `full_bin`：是否使用完整路径（避免环境变量问题）
2. **运行配置**：
    - `cmd`：可指定运行命令（留空则自动运行构建出的二进制文件）
3. **日志配置**：
    - `time`：是否显示时间戳

## 3 高级用法

### 3.1 自定义构建命令

```shell
air --build.cmd "go build -o bin/api cmd/run.go" --build.bin "./bin/api"
```

### 3.2 排除特定目录

```shell
air --build.exclude_dir "templates,build"
```

### 3.3 传递运行参数

```shell
# Will run ./tmp/main server --port 8080
air server --port 8080
```

## 4 注意事项

1. **不要使用 `go run`**：
    - air 的底层机制是编译后执行
    - `go run` 会在临时目录构建，可能导致路径问题
2. **临时文件位置**：
    - air 默认将编译好的程序放在 `tmp` 文件夹
    - 确保你的项目有适当的 `.gitignore` 配置
3. **与热部署的区别**：
    - **热重载**：开发环境使用，修改代码后自动编译 + 运行
    - **热部署**：生产环境使用，实现不中断服务的版本更新

>[!NOTE] 热重载&热部署
> **热重载**：改代码后自动编译 + 运行，常用于开发环境（如 air）；
> **热部署**：上线新版本时不中断服务，常用于生产环境，涉及滚动发布、负载均衡等；
> **守护进程**：程序崩溃或退出后自动重启，保持服务持续运行，如 systemd 和 docker；