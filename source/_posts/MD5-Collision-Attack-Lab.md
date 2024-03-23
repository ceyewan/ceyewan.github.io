---
title: MD5-Collision-Attack-Lab
categories:
  - SeedLabs/Cryptography
tags:
  - MD5 Collision
  - Cryptography
abbrlink: 7944d15b
date: 2024-03-24 00:57:05
---

## Introduction

一个安全的单向散列函数需要满足两个性质：单向性质和抗冲突性质。单向性质保证无法通过哈希值找到最开始的输入。抗冲突性确保了计算上不可能找到两个不同的输入，计算得到的哈希值是相同的。

但是，一些广泛使用的单向哈希函数在保持抗冲突性方面存在问题，在 2004 年 CRYPTO 会议的尾部会议 上，王晓云和合著者演示了一个针对 md5 的碰撞攻击。2017 年 2 月，阿姆斯特丹 CWI 和谷歌研究公司发 布了 SHAttered at-tack，它打破了 SHA-1 的抗碰撞特性。

本次实验我们需要用到 [Fast MD5 Collision Generation](https://www.win.tue.nl/hashclash/) 这个工具，它是由 Marc Stevens 编写的。

## Task 1: Generating Two Different Files with the Same MD5 Hash

在这个任务中，我们将生成两个具有相同 MD5 哈希值的不同文件，这两个文件具有相同的前缀。我们可以使用 md5collgen 这个程序来实现，这个程序的工作方式如下：

![image-20240321161620665](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240321161620665.png)

我们执行如下命令：

![image-20240321163613051](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240321163613051.png)

可以发现，尽管 out1.bin 和 out2.bin 的内容是不同的，但是它俩计算出来的哈希值确实相同的，也就是说，我们实现了哈希碰撞。

-   **Question 1**：如果你的前缀文件的长度不是 64 的倍数，会发生什么？

![image-20240321204321158](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240321204321158.png)

我们发现，如果长度不是 64 的倍数，那么会使用 00 来填充，一直填充到是 64 的倍数。

-    **Question 2**：创建一个 64 字节的前缀文件，然后再次运行碰撞工具，看看会发生什么？

![image-20240321204856235](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240321204856235.png)

就不会再有填充了。

-    **Question 3**：两个文件中 md5collgen 生成的数据（128 字节）是否完全不同？并不是，我们粗略观察，会发现大部分都是一样的，基本上没有什么区别，可以使用 cmp 命令来查看。（diff 用来比较文本文件，cmp 用来比较二进制文件）我们发现，只有七处不同。

![image-20240321222011111](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240321222011111.png)

## Task 2: Understanding MD5’s Property

![image-20240321222140713](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240321222140713.png)

MD5 的工作原理如上所示，它将文件分为 64 字节大小的若干块，在每个块中迭代进行哈希运算。最开始有一个初始 $IHV_0$，每次计算的结果就是下一个块的输入，最后的结果就是最终的哈希值。

基于这个原理，我们可以发现，如果 A 和 B 的哈希值相同，那么 $A || C$ 和 $B || C$ 的哈希值也会相同，$||$ 表示拼接两个字符串。这是因为前面的哈希值相同了，再来和后面相同的块进行相同的哈希运算，结果自然也是相同的。

![image-20240321223242061](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240321223242061.png)

## Task 3: Generating Two Executable Files with the Same MD5 Hash

基于前面两个任务，我们知道，任何一个二进制文件，将其分为 prefix + region + suffix 三个部分。由任务一我们知道 prefix + region1 和 prefix + region2 的哈希值是可以相同的，其中 region 长度为 128 字节。由任务二，添加了 suffix 后，哈希值还是相同的。也就是说，我们可以修改一个程序（把 region1 修改为 region2），而不改变其哈希值。

首先，给定一个 C 代码，作用就是以十六进制输出一个长度为 200 的数组。

```c
#include <stdio.h>
unsigned char xyz[200] = {0x41, 0x41, 0x41, 0x41, ..., 0x41, 0x41, 0x41, 0x41};
int main() {
  for (int i = 0; i < 200; i++) {
    printf("%x", xyz[i]);
  }
  printf("\n");
}
```

首先，我们将其编译成二进制文件，然后通过二进制查看工具，我们发现我们的字符串出现在 12352 附近。我们选这个数，是因为是 64 的倍数，我们把文件中前 12352 个字符作为前缀，通过攻击程序得到两个哈希值相同的文件。接下来，我们将 out.bin 文件写入 hash 文件中。因为 md5collgen 程序生成的哈希值相同的文件只会多 128 个字节，这 128 个字节只会覆盖掉我们最开始写入的全 A（0x41）。

![image-20240321232732049](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240321232732049.png)

这样，尽管 xyz 数组被 out1.bin 和 out2.bin 修改了，hash1 和 hash2 的哈希值还是一样的。如下：

![image-20240321232028582](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240321232028582.png)

我们的 python 程序如下：

```python
import os

with open("out1.bin", "rb") as src_file1:
    src_data1 = src_file1.read()
with open("out2.bin", "rb") as src_file2:
    src_data2 = src_file2.read()
    
with open("hash1", "r+b") as dst_file:
    dst_file.write(src_data1)
print("hash1 程序输出:")
os.system("./hash1")
print("hash1 程序哈希值:")
os.system("md5sum hash1")

with open("hash2", "r+b") as dst_file:
    dst_file.write(src_data2)
print("hash2 程序输出:")
os.system("./hash2")
print("hash2 程序哈希值:")
os.system("md5sum hash2")
```

## Task 4: Making the Two Programs Behave Differently

上面我们已经实现了两个打印不同数据的哈希值相同的程序，现在我们要实现两个行为不同的哈希值相同的程序。我们用一个好程序获得权威机构的证书，证书中使用哈希值来防止篡改。而然，如果我们构造一个坏程序和好程序的哈希值相同，那么证书的防篡改功能就失效了。

但是，我们看到，我们只能修改程序中间的 128 个字节，并且还不是随意的修改。尽管还有其他更复杂、更先进的工具可以解除一些限制，但它们需要更多的计算能力，因此不在本实验室的范围之内。

```c
Array X; Array Y;
main()
{
    if (X’s contents and Y’s contents are the same)
    	run benign code;
    else
    	run malicious code;
    return;
}
```

我们的实验可以这样进行，修改程序两处数组，然后如果相等就执行好命令，如果不等就执行坏命令。

![image-20240321234132864](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240321234132864.png)

1.   构造程序如下：

```c
#include <stdio.h>
unsigned char xyz[200] = {0x41, 0x41, 0x41, 0x41, ..., 0x41, 0x41, 0x41, 0x41};
unsigned char abc[200] = {0x41, 0x41, 0x41, 0x41, ..., 0x41, 0x41, 0x41, 0x41};
int main() {
  for (int i = 0; i < 128; i++) {
    if (xyz[32 + i] != abc[i]) { // 这里分别偏移 32 和 0 是实验出来的，因为替换要以 64 为块
      printf("I am bad!\n");
      return 0;
    }
  }
  printf("I am good!\n");
  return 0;
}
```

2.   编译程序，可以发现，第一个数组开始位置为 12320，因此替换需要在 12352 位置进行，保证是 64 的倍数。第二个数组开始位置为 12544，不用偏移，这也是为什么上面一个是 32 + i，一个是 i。
3.   执行如下命令，将 P 和 Q 分别求出来。

![image-20240322004316624](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240322004316624.png)

4.   改善 python 代码如下，四次替换，写入了三次 P 和一次 Q：

```python
import os

with open("out1.bin", "rb") as src_file1:
    src_file1.seek(-128, 2)
    src_data1 = src_file1.read()

with open("out2.bin", "rb") as src_file2:
    src_file2.seek(-128, 2)
    src_data2 = src_file2.read()

with open("hash1", "r+b") as dst_file1:
    dst_file1.seek(12352)
    dst_file1.write(src_data1)
    dst_file1.seek(12544)
    dst_file1.write(src_data1)
os.system("md5sum hash1")
with open("hash2", "r+b") as dst_file2:
    dst_file2.seek(12352)
    dst_file2.write(src_data2)
    dst_file2.seek(12544)
    dst_file2.write(src_data1)
os.system("md5sum hash2")
```

5.   运行结果如下：

![image-20240322004507207](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240322004507207.png)