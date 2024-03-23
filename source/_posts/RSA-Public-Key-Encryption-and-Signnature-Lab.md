---
title: RSA-Public-Key-Encryption-and-Signnature-Lab
abbrlink: 63322fc3
date: 2024-03-24 01:00:50
categories:
  - SeedLabs/Cryptography
tags:
  - RSA
  - Cryptography
---

## Overview

RSA 是最早的公钥密码系统之一，广泛用于安全通信。RSA 算法首先生成两个大的随机素数，然后使用它们生成公钥和私钥对，可用于加密、解密、数字签名生成和数字签名验证。RSA 算法是建立在数论基础上的，在相关库的支持下可以很容易地实现。本次实验包括如下主题：

-   公开密钥加密
-   RSA 算法以及密钥的生成
-   大数计算
-   使用 RSA 的加密和解密

## Background

RSA 算法涉及对大数的计算。这些计算不能直接使用程序中的简单算术运算符进行，因为这些运算符只能对 32 位或 64 位整数类型进行操作，而 RSA 设计的数字通常超过 512 位。

有几个库可以对任意大小的整数执行算术运算。在这个实验中，我们将使用 openssl 提供的 Big Number 库。为了使用这个库，我们将把每个大数定义为 BIGNUM 类型，然后使用库提供的 api 执行各种操作，如加法、乘法、指数、模操作等。

### BIGNUM APIs

所有的 api 都可以从  https://linux.die.net/man/3/bn 中找到，我们介绍主要的几个。

-   一些库函数需要临时变量。由于在重复子程序调用中与动态内存分配一起使用会很昂贵，占用大量内存，所以创建了一个 BN_CTX 结构来保存库函数使用的 BIGNUM 临时变量。我们需要创建这样一个结构，并将其传递给需要它的函数。

```c
BN_CTX *ctx = BN_CTX_new()
```

-   初始化 BIGNUM 变量

```c
BIGNUM *a = BN_new()
```

-   有很多方法可以给 BIGNUM 变量赋值

```c
// 十进制数字字符串
BN_dec2bn(&a, "12345678901112231223");
// 十六进制数字字符串
BN_hex2bn(&a, "2A3B4C55FF77889AED3F");
// 随机的 128 位数字
BN_rand(a, 128, 0, 0);
// 随机的 128 位素数
BN_generate_prime_ex(a, 128, 1, NULL, NULL, NULL);
```

-   打印一个大数

```c
void printBN(char *msg, BIGNUM * a) {
    // 将大数转为字符串
    char * number_str = BN_bn2dec(a);
    printf("%s %s\n", msg, number_str);
    OPENSSL_free(number_str);
}
```

-   基本运算

```c
BN_sub(res, a, b); // res = a - b
BN_add(res, a, b); // res = a + b
BN_mul(res, a, b, ctx); // ctx 是 BN_CTX 类型, res = a * b
BN_mod_mul(res, a, b, n, ctx); // res = a * b mod n
BN_mod_exp(res, a, c, n, ctx) // res = a ^ c mod n
BN_mod_inverse(b, a, n, ctx); // 计算模逆，找到 b 使得 a * b mod n = 1
```

### A Complete Example

提供了相关文件，我们只需要执行看看即可。

## Task 1: Deriving the Private Key

设 $p$、$q$、$e$ 是三个质数，设 $n = p * q$。我们使用  $(e, n)$ 作为公钥，请计算私钥 $d$。

>   在 RSA 加密算法中，$p$ 和 $q$ 是两个足够大且不相等的素数；$n$ 是这两个素数的乘积；$e$ 是公钥中的加密指数，用于加密消息；$(e, n)$ 这一对数值一起构成了 RSA 中的公钥。
>
>   要生成私钥 $d$，我们需要先计算欧拉函数，$\varphi(n) = (p-1)(q-1)$，而 $d$ 就是 $e$ 关于 $\varphi(n)$ 的模逆，也就是说 $e\ *\ d\ \equiv\ 1(mod\ \varphi(n))$​​ 

## Task 2: Encrypting a Message

让 $(e, n)$​ 成为公钥。请加密消息 "A top secret!"。我们需要将这个 ASCII 字符串转换为十六进制字符串，然后将十六进制字符串转换为 BIGNUM。下面的 python 命令可以用来将普通的 ASCII 字符串转换成十六进制字符串。

```shell
python3 -c 'rint("A top secret!".encode("utf-8").hex())'
```

>   加密的公式为 $c \equiv m^e\ (mod\ n)$，其中 $m$ 是需要加密的消息，$c$​ 是加密后的密文。

## Task 3: Decrypting a Message

>   解密的公式为 $m \equiv c^d\ (mod\ n)$，其中 $c$ 是需要解密的消息，$m$​ 是解密后的明文。

下面的 python 命令可以用来将十六进制字符串转换成 ASCII 字符串。

```shell
python3 -c 'print(bytes.fromhex("4120746f702073656372657421").decode("utf-8"))'
```

完整代码如下，包括初始化、加密、解密三个部分。

```c
#include <openssl/bn.h>
#include <stdio.h>

char *p_str = "F7E75FDC469067FFDC4E847C51F452DF";
char *q_str = "E85CED54AF57E53E092113E62F436F4F";
char *e_str = "0D88C3";
char *m_str = "4120746F702073656372657421";

void printBN(char *msg, BIGNUM *a) {
  char *number_str = BN_bn2hex(a);
  printf("%s %s\n", msg, number_str);
  OPENSSL_free(number_str);
}

int main() {
  BN_CTX *ctx = BN_CTX_new();
  BIGNUM *p = BN_new();
  BIGNUM *p_1 = BN_new();
  BIGNUM *q = BN_new();
  BIGNUM *q_1 = BN_new();
  BIGNUM *e = BN_new();
  BIGNUM *d = BN_new();
  BIGNUM *n = BN_new();
  BIGNUM *n2 = BN_new();
  BIGNUM *m = BN_new();
  BIGNUM *c = BN_new();
  BN_hex2bn(&p, p_str);
  BN_hex2bn(&q, q_str);
  BN_hex2bn(&e, e_str);
  BN_hex2bn(&m, m_str);
  // RSA 算法初始化
  BN_mul(n, p, q, ctx);
  BN_sub_word(p, 1);
  printBN("p_1 is", p);
  BN_sub_word(q, 1);
  printBN("q_1 is", q);
  BN_mul(n2, p, q, ctx);
  BN_mod_inverse(d, e, n2, ctx);
  // 加密
  BN_mod_exp(c, m, e, n, ctx);
  printBN("c is", c);
  // 解密
  BN_mod_exp(m, c, d, n, ctx);
  printBN("m is", m);
  return 0;
}
```

## Task 4: Signing a Message

如下，明文失之毫厘，密文差以千里。

![image-20240319174600075](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240319174600075.png)

## Task 5: Verifying a Signature

使用公钥  $(e, n)$  将消息 $m$ 加密，与签名 $s$ 对比，如果符合，那么说明签名来自于 Alice。

