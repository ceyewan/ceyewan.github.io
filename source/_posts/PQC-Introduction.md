---
title: PQC:Introduction
categories:
  - PQC
tags:
  - PQC
abbrlink: 859aac7b
date: 2024-10-29 18:33:32
---

# PQC：Introduction

## Introduction

在 2024 年，美国国家标准与技术研究所（NIST）发布了一套量子安全密钥封装机制（KEM）和签名方案的标准。这些方案旨在取代 RSA 和 ECC，因为它们不可抵抗量子攻击。预计 Kyber（KEM）和 Dilithium（DSA）将在未来几年得到广泛应用。

### 量子计算机

- **概念**：量子计算机利用量子力学现象（如叠加、干涉和纠缠）来进行数据操作。
- **量子比特（qubit）**：量子比特可以同时处于两种状态，每种状态具有一定的概率。
- **n-量子比特寄存器**：可以处于 $2^n$ 种状态，每种状态具有一定的概率。

当函数 $f: \{0, 1\}^n \rightarrow \{0, 1\}^n$ 应用到 n-量子比特寄存器时，它会在所有 $2^n$ 状态上同时进行评估。然而，当 n-量子比特寄存器被测量时，它会根据其底层概率分布回归为 $2^n$ 中的一个状态。因此，量子计算机并不是“高度并行的机器”。

### Shor 算法

在实际应用中使用的公钥系统包括：

- **RSA**：安全性基于整数分解的难度。
- **DL（离散对数）**：安全性基于离散对数问题的难度。
- **ECC（椭圆曲线密码学）**：安全性基于 ECDLP（椭圆曲线离散对数问题）的难度。

**Shor 算法**：在 1994 年，Peter Shor 发现了一种非常高效的（多项式时间）量子算法来解决这些问题。因此，所有的 RSA、DL 和 ECC 实现都可以被量子计算机完全破解。

### Grover 算法

设 $F:\{0,1\}^n→\{0,1\}$ 是一个函数，满足以下条件：

1. F 是可以高效计算的；
2. $F(x)=1$ 对于恰好一个输入 $x∈\{0,1\}^n$ 成立。

Lov Grover 在 1996 年发现了一种量子算法，可以在 $\sqrt{2^n}$ 次 F 的评估中找到 x。

考虑使用 $ \ell $-位密钥的 AES。假设我们有 $ t $ 对已知的明文-密文对 $ (m_i, c_i) $，其中 $ t $ 的期望值接近于 0。   定义 $ F : \{0, 1\}^\ell \rightarrow \{0, 1\} $ 为：  
$$
F(k) =   \begin{cases}   1 & \text{如果 } AES_k(m_i) = c_i \text{ 对于所有 } 1 \leq i \leq t \\   0 & \text{否则}   \end{cases}
$$

然后，Grover 的算法可以在 $ 2^{\ell/2} $ 次量子操作中找到秘密密钥。因此，为了实现 128 位的安全性水平，应该使用 256 位的 AES 密钥以抵御量子攻击。

> **Harvest Now Decrypt Later（HNDL）attacks**：这种攻击策略指的是在当前阶段收集数据，即使这些数据现在是加密的，未来可能会有技术手段将其解密。

## Mathematical prerequisites

### Modular arithmetic

- **模数**：$ q \geq 2 $，一般选择素数。
- $ a \equiv b \ (\text{mod } q) $ 表示 $ a - b $ 是 $ q $ 的整数倍。
- $ r = a \ \text{mod} \ q $ 表示 $ r $ 是将整数 $ a $ 除以 $ q $ 后的余数（所以 $ 0 \leq r < q $）。
- **模 $ q $ 的整数**：$ \mathbb{Z}_q = {0, 1, 2, \ldots, q - 1} $，在这里，加法、减法和乘法都是模 $ q $ 进行的。

### Polynomial rings

- 设 $ q $ 为一个素数模数。
- $ \mathbb{Z}_q[x] $ 是所有以 $ x $ 为变量且系数在 $ \mathbb{Z}_q $ 中的多项式的集合。
- 在 $ \mathbb{Z}_q[x] $ 中进行加法、减法、乘法和除法时，所有系数的算术运算都在 $ \mathbb{Z}_q $ 中进行。
- 多项式环 $ R_q = \mathbb{Z}_q[x]/(x^n + 1) $ 由所有在 $ \mathbb{Z}_q[x] $ 中的多项式组成，其次数小于 $ n $，并且多项式的乘法是在约简多项式 $ x^n + 1 $ 下进行的。

多项式相乘的步骤：

1. 在 $ \mathbb{Z}_q[x] $ 中相乘多项式 $ f(x) $ 和 $ g(x) $，得到一个多项式 $ h(x) $，其次数最多为 $ 2n - 2 $。
2. 将 $ h(x) $ 除以 $ x^n + 1 $，得到一个余数多项式 $ r(x) $，其次数最多为 $ n - 1 $。
3. 则 $ f(x) \times g(x) = r(x) $ 在 $ R_q $ 中。

> $ R_q $ 的大小为 $ q^n $。

### Module $ R_q^k $

- 设 $ k $ 为正整数。
- 模 $ R_q^k $ 的元素是长度为 $ k $ 的多项式向量，且这些多项式在 $ R_q $ 中。
- 在 $ R_q^k $ 中，元素的加法和减法是逐分量进行的（因此结果也是 $ R_q^k $ 中的元素）。
- 两个向量的内积（乘法）在 $ R_q^k $ 中的结果是一个多项式，且该多项式在 $ R_q $ 中。
- 所有的向量将在 $ R_q^k $ 中以列向量的形式书写。

### Size

- 我们引入了“大小”的概念，用于：
    - $ \mathbb{Z}_q $ 中的整数
    - $ R_q = \mathbb{Z}_q[x]/(x^n + 1) $ 中的多项式
    - $ R_q^k $ 中的多项式向量
- 这个大小被称为“无穷范数”，用符号 $ \| \cdot \|_\infty $ 表示。

为此，我们需要引入“对称模”的概念。

### Symmetric mod

设 $ q $ 为奇数，$ r \in \mathbb{Z}_q $：
$$
r \mod q = 
\begin{cases} 
r, & \text{if } r \leq \frac{q - 1}{2} \\ 
r - q, & \text{if } r > \frac{q - 1}{2} 
\end{cases}
$$
因此，$ -\frac{q - 1}{2} \leq r \mod q \leq \frac{q - 1}{2} $。

设 $ q $ 为偶数，$ r \in \mathbb{Z}_q $：
$$
r \mod q = 
\begin{cases} 
r, & \text{if } r \leq \frac{q}{2} \\ 
r - q, & \text{if } r > \frac{q}{2} 
\end{cases}
$$
因此，$ -\frac{q}{2} < r \mod q \leq \frac{q}{2} $。

> $ \mod q $ 也可以写作 $ \mod^+ q $。

### Size of Polynomial

- **模 $ q $ 的整数**：设 $ r \in \mathbb{Z}_q $。则 $ \| r \|_\infty = | r \mod q | $。
    - **例子**：设 $ q = 19 $。则 $ \| 7 \|_\infty = 7 $ 和 $ \| 18 \|_\infty = 1 $。
    - 注意：如果 $ q $ 为奇数，则 $ 0 \leq \| r \|_\infty \leq \frac{(q - 1)}{2} $；如果 $ q $ 为偶数，则 $ 0 \leq \| r \|_\infty \leq \frac{q}{2} $。

- **环元素**：设 $ f(x) = f_0 + f_1 x + \cdots + f_{n-1} x^{n-1} \in R_q $。则 $ \| f \|_\infty = \max \| f_i \|_\infty $。
    - **例子**：设 $ f(x) = 1 + 12x + 3x^3 + 18x^5 \in R_{19} $。则 $ \| f \|_\infty = 7 $，因为 $ f $ 的模 $ q $ 表示为 $ 1 - 7x + 3x^3 - x^5 $。

- **模元素**：设 $ a = [a_1, a_2, \ldots, a_k]^T \in R_q^k $。则 $ \| a \|_\infty = \max \| a_i \|_\infty $。

### Small Polynominal

- 如果 $ \| f \|_\infty $ 是“小”的，那么一个多项式 $ f \in R_q $ 是小的。
- 设 $ \eta $ 为一个与 $ q/2 $ 相比小的正整数。
- 定义 $ S_\eta = \{ f \in R_q \mid \| f \|_\infty \leq \eta \} $ 为在 $ R_q $ 中所有系数大小最多为 $ \eta $ 的多项式的集合。
- $ S_\eta $ 是“小”多项式的集合。

> **例子**：设 $ q = 31 $。那么 $ 1 + 30x + 29x^2 + x^4 + 2x^5 \in S_2 $。

**声明**：如果 $ f \in S_{\eta_1} $ 且 $ g \in S_{\eta_2} $，则 $ fg \in S_{n\eta_1\eta_2} $，也是一个相对小的多项式。

证明：

设 $ f(x) = f_0 + f_1 x + \cdots + f_{n-1} x^{n-1} \in S_{\eta_1} $ 和 $ g(x) = g_0 + g_1 x + \cdots + g_{n-1} x^{n-1} \in S_{\eta_2} $，令 $ h(x) = f(x)g(x) = h_0 + h_1 x + \cdots + h_{n-1} x^{n-1} $。容易知道 $ \| h_i \|_\infty \leq n \eta_1 \eta_2 $，因此，$ h \in S_{n \eta_1 \eta_2} $。

同样地，如果 $ a \in S^{k}_{\eta_1} $ 且 $ b \in S^{k}_{\eta_2} $，则 $ ab^T \in S_{k n \eta_1 \eta_2} $。

## Lattice problems

- **Kyber 的安全性**：基于决策模块学习带错误 (D-MLWE) 问题的困难性，而该问题又与 MLWE 问题的困难性相关。
- **Dilithium 的安全性**：基于 D-MLWE 和模块短整数解 (MSIS) 问题的困难性。

### MLWE（Module Learning With Errors）

**MLWE** 是 LWE（Learning With Errors）问题的一个推广。LWE 问题是密码学中的一个基础问题，其安全性基于计算困难的假设。LWE 问题的基本形式是给定一个秘密向量和一个带有噪声的线性方程组，求解秘密向量。

MLWE 扩展了 LWE 的概念，引入了模块结构（即引入了模运算）。具体来说，MLWE 问题在一个模块上定义，其中模块是一个环上的自由模。这样做的好处是可以在保持安全性的同时提高效率和灵活性。

- **参数**：
    - 素数 $ q $
    - 整数 $ n, k, \ell $ 使得 $ k \geq \ell $
    - 整数 $ \eta_1, \eta_2 $ 使得 $ \eta_1, \eta_2 \ll \frac{q}{2} $

- **模块带错误学习 (MLWE) 实例**：
    - $ A \in R_q^{k \times \ell} $（其中 $ R_q = \mathbb{Z}_q[x]/(x^n + 1) $）
    - $ t = As + e $，其中 $ s \in_R S_{\eta_1}^{\ell} $ 和 $ e \in_R S_{\eta_2}^{k} $（因此 $ t \in R_q^k $）

- **要求**：求解 $ s $

### D-MLWE（Decisional Module Learning With Errors）

**D-MLWE** 是 MLWE 问题的一个变体，侧重于决策问题而非搜索问题。D-MLWE 的目标是区分两种情况：一种是给定的向量是根据 MLWE 问题生成的（即带有噪声的线性方程组），另一种是给定的向量是随机生成的。

换句话说，D-MLWE 问题是关于判断特定样本是否符合某种结构（即是否是带噪声的线性组合）的问题。这种决策问题在密码学中非常重要，因为许多加密协议的安全性依赖于无法有效区分这两种情况。

D-MLWE（Decisional-Module Learning With Errors）问题是一个基于格的密码学问题，具体描述如下：

- **参数：**

    - 素数 $ q $：用于定义模数。

    - 整数 $ n, k, \ell $：满足 $ k \geq \ell $。

    - 整数 $ \eta_1, \eta_2 \ll q/2 $：用于定义噪声的界限。


- **决策-模块带错误学习(D-MLWE)实例：**

    - 矩阵 $ A $：属于 $ R_q^{k \times \ell} $，其中 $ R_q = \mathbb{Z}_q[x]/(x^n + 1) $。

    - 向量 $ z $：属于 $ R_q^k $，有两种可能的生成方式：
        - $ z = t $ 以概率 $ \frac{1}{2} $ 生成，其中 $ t = As + e $，$ s \in R_{S_{\eta_1}^\ell} $，$ e \in R_{S_{\eta_2}^k} $。
        - $ z $ 是随机生成的，属于 $ R_q^k $，以概率 $ \frac{1}{2} $。


- **要求**：判断给定的 $ (A, z) $ 是否是一个 MLWE 实例，即判断 $ z $ 是否等于 $ t $。

### MSIS（Module Short Integer Solution）

**MSIS** 是 SIS（Short Integer Solution）问题的模块化版本。SIS 问题要求找到一个短向量，使其在给定的整数矩阵下映射为零。这个问题在密码学中用于构造基于格的密码系统。

MSIS 将 SIS 问题扩展到模块上，类似于 MLWE 对 LWE 的扩展。MSIS 问题的目标是找到一个短的模块向量，使其在给定的模块矩阵下映射为零。MSIS 的安全性也基于格问题的计算困难性。

### Why Lattices

在现代密码学中，格（lattices）在评估 MLWE、D-MLWE 和 MSIS 问题的难度时扮演了两个重要角色。

1. **理论上的难度保证**：

    在 2012 年，Langlois 和 Stehlé 证明了 MLWE、D-MLWE 和 MSIS 的平均情况难度至少与某些结构化格中的自然格问题的最坏情况量子难度一样难。这一结果提供了理论上的安全性保证，表明在平均情况下解决这些问题至少和解决某些特定的最坏情况格问题一样困难。

    - **高度渐近性**：这种保证是高度渐近性的，意味着它更多地适用于非常大的参数集。在实际应用中，参数集可能并不总是足够大以使这些渐近结果直接适用。因此，这种理论保证在实际中能提供的安全性保证可能有限。

2. **作为格问题的重述**：

    MLWE、D-MLWE 和 MSIS 问题可以被重述为格问题。这些格问题是密码学领域中被广泛研究的对象，研究人员通过分析这些问题的最优攻击策略来评估其难度。

    - **具体参数的选择**：通过研究这些格问题，可以找到已知最快的攻击方法，从而帮助确定具体的参数选择。例如，Kyber 和 Dilithium（两种基于格的加密方案和签名方案）的参数选择就是基于这种分析。这种方法确保在给定的参数下，这些问题足够难以抵御已知的攻击。

