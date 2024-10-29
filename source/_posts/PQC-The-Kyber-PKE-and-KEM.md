---
title: 'PQC:The-Kyber-PKE-and-KEM'
categories:
  - PQC
tags:
  - Kyber
abbrlink: 9731e9cf
date: 2024-10-29 18:33:53
---

# PQC：The Kyber PKE and KEM

Kyber 作为一种量子安全的密钥封装机制（Key Encapsulation Mechanism, KEM）的基本信息如下：

1. **量子安全的密钥封装机制（KEM）**：Kyber 是一种专门设计用于抵抗量子计算攻击的加密技术。传统的加密方法在量子计算机面前可能会变得不再安全，而 Kyber 通过其设计可以抵御这种威胁。

2. **NIST 标准化**：Kyber 已经被美国国家标准与技术研究院（NIST）标准化，并在 FIPS 203 中被称为 ML-KEM（基于模块格的 KEM）。这意味着 Kyber 的安全性和有效性已经得到了广泛的认可和验证。

3. **Fujisaki-Okamoto 变换**：Kyber-KEM 是通过对一个公钥加密方案（Kyber-PKE）应用 Fujisaki-Okamoto 变换而设计的。Fujisaki-Okamoto 变换是一种将公钥加密方案从仅对选择明文攻击安全（CPA 安全）提升为对选择密文攻击安全（CCA 安全）的通用方法。这使得 Kyber-KEM 在更广泛的攻击模型下保持安全。

## Kyber-PKE (simplified)

### Rounding

设定 $ q $ 为一个奇素数，$ x $ 为区间 $[0, q - 1]$ 内的一个数。计算 $x' = x \mod q $，其中 $x' $ 的范围是 $ [-(q-1)/2, (q-1)/2] $。

- 如果 $-q/4 < x' < q/4 $，则 $\text{Round}_q(x) = 0 $。
- 否则，$\text{Round}_q(x) = 1 $。

> 设 $q = 3329 $，则如果 $-832 \leq x' \leq 832 $，那么 $\text{Round}_q(x) = 0 $，否则为 1。

- 舍入操作可以扩展到多项式，通过对多项式的每个系数应用舍入操作。
- 示例：对于 $q = 3329 $，多项式 $3000 + 1500x + 2010x^2 + 37x^3 $ 的舍入结果为 $x + x^2 $。

### Domain parameters and key genaration

对于 ML-KEM-768 来说，参数设置如下：

- **$ q = 3329 $**：一个奇素数。
- **$ n = 256 $**：多项式的维度。
- **$ k = 3 $**：参数设置。
- **$ \eta_1 = 2, \eta_2 = 2 $**：用于生成随机多项式的参数。

密钥生成过程如下：

1. **选择参数**：
    - 选择矩阵 $ A \in_R R_q^{k \times k} $。
    - 选择随机多项式 $ s \in_R S_{\eta_1}^k $ 和 $ e \in_R S_{\eta_2}^k $。

2. **计算**：
    - 计算 $ t = As + e $。

3. **密钥对**：
    - Alice 的加密（公钥）是 $ (A, t) $。
    - Alice 的解密（私钥）是 $ s $。

### Encryption and decryption

加密过程（Kyber-PKE(s) encryption）：

1. **获取公钥**：
    - Bob 获取 Alice 的加密公钥 $(A, t)$。

2. **选择随机多项式**：
    - 选择 $ r \in_R S_{\eta_1}^k $、$ e_1 \in_R S_{\eta_2}^k $、$ e_2 \in_R S_{\eta_2} $。

3. **计算密文**：
    - 计算 $ u = A^T r + e_1 $。
    - 计算 $ v = t^T r + e_2 + \left\lfloor \frac{q}{2} \right\rfloor m $。

4. **输出密文**：
    - 输出密文 $ c = (u, v) $。

解密过程（Kyber-PKE(s) decryption）：

1. **计算明文**：
    - Alice 使用她的解密密钥 $ s $ 计算 $ m = \text{Round}_q(v - s^T u) $。

这个过程确保了通过公钥加密和私钥解密来安全地传输信息。

### Security

**声明**：简化的 Kyber-PKE 在选择明文攻击下是不可区分的，前提是 D-MLWE（模块学习误差问题）是不可解的。

**证明**：加密操作可以表示为矩阵乘积和随机元素的组合：
$$
\begin{bmatrix}
u \\
v
\end{bmatrix}
=
\begin{bmatrix}
A^T \\
t^T
\end{bmatrix}
r +
\begin{bmatrix}
e_1 \\
e_2
\end{bmatrix}
+
\begin{bmatrix}
0 \\
\left\lfloor \frac{q}{2} \right\rfloor m
\end{bmatrix}
$$

- **D-MLWE 假设**：
    - $\begin{bmatrix} A^T \\ t^T \end{bmatrix}$ 被假设为与随机不可区分。
    - $\begin{bmatrix} A^T \\ t^T \end{bmatrix} r + \begin{bmatrix} e_1 \\ e_2 \end{bmatrix}$ 也被假设为与随机不可区分。

- **对攻击者的影响**：
    - 从攻击者的角度来看，$ v $ 看起来是随机元素 $(t^T r + e_2)$ 和消息多项式 $\left\lfloor \frac{q}{2} \right\rfloor m$ 的和，因此攻击者无法从中学习到关于 $ m $ 的信息。

这个证明展示了在 D-MLWE 假设下，简化的 Kyber-PKE 能够有效防御选择明文攻击。

### Decryption doesn't always work

- 解密计算为：$ v - s^T u = (t^T r + e_2 + \left\lfloor \frac{q}{2} \right\rfloor m) - s^T u $
- 经过推导，得到：$ e^T r + e_2 - s^T e_1 + \left\lfloor \frac{q}{2} \right\rfloor m $（将 $ t = As + e $ 和 $ u = A^T r + e_1 $ 代入）。

- 解密成功的条件是误差多项式 $ E(x) = e^T r + e_2 - s^T e_1 $ 的每个系数 $ E_i $ 满足 $-q/4 < E_i \mod q < q/4$，即 $\|E\|_\infty < q/4$。

- 对于 ML-KEM-768 参数（$ q = 3329, n = 256, k = 3, \eta_1 = \eta_2 = 2 $），有 $|E_i| \leq 6146 \not< q/4$。因此，解密不一定总是成功。

- 尽管如此，可以证明 $\|E\|_\infty < q/4$ 的概率非常接近 1。因此，解密几乎总是会成功。

## Optimizations

这张图片介绍了 Kyber 加密中的密钥和密文的大小：

### 参数设置

- 使用 ML-KEM-768 参数：$ q = 3329, n = 256, k = 3, \eta_1 = 2, \eta_2 = 2 $。

- 在 $\mathbb{Z}_q$ 中，一个整数的位长为 $\lceil \log_2 3329 \rceil = 12$ 位。

- 加密密钥 $(A, t)$ 的大小为：
    $$
    (9 \times 256 \times 12) + (3 \times 256 \times 12) \text{ bits} = 4608 \text{ bytes}
    $$

- 密文 $ c = (u, v) $ 的大小为：
    $$
    (3 \times 256 \times 12) + (256 \times 12) \text{ bits} = 1536 \text{ bytes}
    $$

这些尺寸说明了在 Kyber 加密中所需的存储空间。

### Smaller public keys

- **生成 $ A $**：从一个随机且公开的 256 位种子 $\rho$ 生成。
- **多项式生成**：通过选择 $\rho \in_R \{0,1\}^{256}$，然后使用计数器对 $\rho$ 进行哈希来生成多项式的系数。

- 加密密钥现在是 $(\rho, t)$ 而不是 $(A, t)$。
- 任何知道 $\rho$ 的人都可以生成 $ A $。

- 新的加密密钥大小为 $256 + (3 \times 256 \times 12)$ 位，即 1184 字节。

### Ciphertext compression

- **压缩**：丢弃密文 $(u, v)$ 中所有多项式系数的“低位”。

- 设 $1 \leq d \leq \lfloor \log_2 q \rfloor$，定义如下：
    - 对于 $x \in [0, q - 1]$，压缩为：$ \text{Compress}_q(x, d) = \left\lfloor \frac{2^d}{q} \cdot x \right\rfloor \mod 2^d $
    - 对于 $y \in [0, 2^d - 1]$，解压缩为：$ \text{Decompress}_q(y, d) = \left\lfloor \frac{q}{2^d} \cdot y \right\rfloor \mod q $

- 对于 $x \in [0, q - 1]$ 和 $x' = \text{Decompress}_q(\text{Compress}_q(x, d), d)$，有：$ \|x' - x\|_\infty \leq \left\lceil \frac{q}{2^{d+1}} \right\rceil $

- 压缩和解压缩函数可以自然地扩展到 $R_q$ 中的多项式和 $R_q^k$ 中的多项式向量。

> - $ q = 3329 $，$ d = 10 $，$ x \in [0, q - 1] $。
>
> - 压缩：$\text{Compress}_q(223 + 1438x + 3280x^2 + 798x^3, 10) = 69 + 442x + 1009x^2 + 245x^3$。
> - 解压缩：$\text{Decompress}(69 + 442x + 1009x^2 + 245x^3) = 224 + 1437x + 3280x^2 + 796x^3$。
>
> - 误差多项式为 $-1 + x + 2x^3$。$|(x - x') \mod q| \leq 2$。
>
> - $ q = 3329 $，$ d = 4 $，$ x \in [0, q - 1] $。
>
> - 压缩：$\text{Compress}_q(223 + 1438x + 3280x^2 + 798x^3, 4) = 1 + 7x + 4x^3$。
> - 解压缩：$\text{Decompress}_q(1 + 7x + 4x^3, 4) = 208 + 1456x + 832x^3$。
>
> - 误差多项式为 $15 - 18x - 59x^2 - 34x^3$。$|(x - x') \mod q| \leq 104$。

密文压缩的过程如下：

- 将密文组件 $ u $ 和 $ v $ 分别替换为 $ c_1 = \text{Compress}_q(u, d_u) $ 和 $ c_2 = \text{Compress}_q(v, d_v) $。

1. **参数设置**：
    - 使用 ML-KEM-768 参数：$ q = 3329, n = 256, k = 3, \eta_1 = 2, \eta_2 = 2 $。
    - 压缩参数为 $ d_u = 10 $ 和 $ d_v = 4 $。

2. **结果**：
    - 压缩后的密文大小为 $ 3 \times 256 \times 10 + 256 \times 4 $ 位，即 1088 字节。
    - 相比原始的 1536 字节，显著减少了密文的大小。

这种压缩技术有效地减少了存储和传输需求，同时保持解密的准确性。

### Central binomial distribution

中心二项分布（Central Binomial Distribution, CBD）在 Kyber 中可以用来生成随机“小”多项式：

**目的**：从集合 $S_\eta$ 中随机选择多项式，通过从 $[-η, η]$ 范围内均匀选择系数来实现。

- 随机选择 $η$ 对位 $(a_i, b_i)$，其中 $1 \leq i \leq η$。
- 输出 $c = \sum_{i=1}^{η} (a_i - b_i)$，因此 $c \in [-η, η]$。

- 对于每个 $j \in [-η, η]$，有 $ \Pr(c = j) = \frac{\binom{2η}{η+j}}{2^{2η}} $

> 当 $η = 2$ 时分布为：$-2$ 和 $2$ 的概率是 $1/16$，$-1$ 和 $1$ 的概率是 $4/16$，$0$ 的概率是 $6/16$。

### Fast polynomial multiplication

- 加密和解密的计算时间主要受限于在环 $ R_q = \mathbb{Z}_{3329}[x]/(x^{256} + 1) $ 中多项式乘法的时间。

- 使用数论变换（Number-Theoretic Transform, NTT）可以显著加快多项式乘法的速度。
- NTT 是一种类似快速傅里叶变换（FFT）的算法，专门用于有限域上的多项式运算。

通过使用 NTT，Kyber 能够在不牺牲安全性的情况下提高加密和解密的效率。

## Kyber-PKE (full)

### Domain parameters and key generation

#### 域参数（ML-KEM-768）

- $ q = 3329 $
- $ n = 256 $
- $ k = 3 $
- $ \eta_1 = 2 $ 和 $ \eta_2 = 2 $
- $ d_u = 10 $ 和 $ d_v = 4 $

#### Kyber-PKE 密钥生成步骤

1. 选择 $ \rho \in_R \{0, 1\}^{256} $，并计算 $ A = \text{Expand}(\rho) $，其中 $ A \in R_q^{k \times k} $。
2. 选择 $ s \in_\text{CBD} S^{k}_{\eta_1} $ 和 $ e \in_\text{CBD} S^{k}_{\eta_2} $。
3. 计算 $ t = As + e $。
4. Alice 的加密（公钥）是 $ (\rho, t) $；她的解密（私钥）是 $ s $。

### Encryption and decryption

#### Kyber-PKE 加密

要加密消息 $ m \in \{0, 1\}^n $，Bob 执行以下步骤：

1. 获取 Alice 的加密密钥 $ (\rho, t) $ 的真实副本，并计算 $ A = \text{Expand}(\rho) $。
2. 选择 $ r \in_\text{CBD} S^{k}_{\eta_1} $，$ e_1 \in_\text{CBD} S^{k}_{\eta_2} $。
3. 计算 $ u = A^T r + e_1 $ 和 $ v = t^T r + e_2 + \left\lfloor \frac{q}{2} \right\rfloor m $。
4. 计算 $ c_1 = \text{Compress}(u, d_u) $ 和 $ c_2 = \text{Compress}(v, d_v) $。
5. 输出 $ c = (c_1, c_2) $。

#### Kyber-PKE 解密

要解密 $ c = (c_1, c_2) $，Alice 执行以下步骤：

1. 计算 $ u' = \text{Decompress}(c_1, d_u) $ 和 $ v' = \text{Decompress}(c_2, d_v) $。
2. 计算 $ m = \text{Round}_q(v' - s^T u') $。

### Decryption doesn’t always work

- 设 $ u' = u + e_u $ 和 $ v' = v + e_v $。
- 有：$ v' - s^T u' = (v + e_v) - s^T (u + e_u) = v - s^T u + e_v - s^T e_u + \left\lfloor \frac{q}{2} \right\rfloor m$.

- 因此，如果误差多项式的每个系数 $ E_i $ 满足：$ -\frac{q}{4} < E_i \mod q < \frac{q}{4} \quad \text{or} \quad \|E\|_\infty < \frac{q}{4}$
    则 $ \text{Round}_q(v' - s^T u') = m $。

- 对于 ML-KEM-768 参数，$|E_i| \not< \frac{q}{4}$，因此解密不一定成功。但可以证明，$\|E\|_\infty < \frac{q}{4}$ 的概率极接近于 1。因此，解密几乎肯定会成功。

> 这里可以看出 $e_u$ 被 $s^T$ 放大了，因此压缩等级更小一点。

### Security

- **密文压缩**：密文压缩不会影响 Kyber-PKE 的安全性。因此，声明仍然成立。

- **声明**：Kyber-PKE 在假设 D-MLWE 问题是不可解的情况下，对选择明文攻击是不可区分的。

- **注意**：Kyber-PKE 并不打算用于独立使用。

## Kyber-KEM

### Key encapsulation mechanisms

**密钥封装机制（KEM）** 允许两方建立共享的秘密密钥。

1. **密钥生成**：每个用户（例如 Alice）使用此算法生成一个封装密钥 $ ek $（公钥）和一个解封装密钥 $ dk $（私钥）。

2. **封装**：Bob 使用 Alice 的封装密钥 $ ek $ 来生成一个秘密密钥 $ K $ 和密文 $ c $，并将 $ c $ 发送给 Alice。

3. **解封装**：Alice 使用她的解封装密钥 $ dk $ 从密文 $ c $ 中恢复出 $ K $。

### Kyber-KEM

Kyber-KEM 是通过对 Kyber-PKE 应用“Fujisaki-Okamoto”（FO）变换而得出的。

> **FO 变换**：FO 变换是一种通用方法，用于将一个对选择明文攻击安全的公钥加密方案转换为一个对选择密文攻击安全的方案。

该变换使用了三个哈希函数：

- $ G : \{0,1\}^* \rightarrow \{0,1\}^{512} $
- $ H : \{0,1\}^* \rightarrow \{0,1\}^{256} $
- $ J : \{0,1\}^* \rightarrow \{0,1\}^{256} $

### FO Transform

1. **封装**：
    - 使用 Kyber-PKE 对随机选择的 $ m \in \{0, 1\}^{256} $ 进行加密。
    - **去随机化**：将消息 $ m $ 和封装密钥 $ ek $ 哈希以生成随机种子 $ R $ 和秘密密钥 $ K $。随机多项式 $ r, e_1 $ 和 $ e_2 $ 由 $ R $ 导出。

2. **解封装**：
    - 预期接收者解密 Kyber-PKE 密文 $ c $ 以恢复 $ m' $，然后将 $ m' $ 和 $ ek $ 哈希以获得 $ R' $ 和 $ K' $。
    - 接收者使用 $ R' $ 重新加密 $ m' $，并将生成的密文 $ c' $ 与 $ c $ 进行比较。
    - 如果 $ c = c' $，接收者接受 $ K' $；否则，输出一个随机密钥 $ \bar{K} $（与 $ K $ 独立），该密钥通过哈希 $ c $ 和一个秘密值 $ z $ 获得。

3. **明文意识**：
    - Kyber-KEM 具有明文意识，即解封装只会生成 $ K $（而不是 $ \bar{K} $），当且仅当执行封装的实体已经知道 $ K $。

4. **安全性**：
    - 这种机制提供了对选择密文攻击的抵抗。

### 域参数（ML-KEM-768）

- $ q = 3329 $
- $ n = 256 $
- $ k = 3 $
- $ \eta_1 = 2 $ 和 $ \eta_2 = 2 $
- $ d_u = 10 $ 和 $ d_v = 4 $

### Kyber-KEM 密钥生成

Alice 执行以下步骤：

1. 使用 Kyber-PKE 密钥生成算法选择 Kyber-PKE 加密密钥 $ (\rho, t) $ 和解密密钥 $ s $。
2. 选择 $ z \in_R \{0, 1\}^{256} $。
3. Alice 的封装密钥是 $ ek = (\rho, t) $；她的解封装密钥是 $ dk = (s, ek, H(ek), z) $。

### Kyber-KEM 密钥封装

1. 获取 Alice 的封装密钥 $ek$
2. 随机选择 $m \in_R \{0,1\}^{256}$
3. 计算：$h = H(ek)$，$(K, R) = G(m, h)$，其中 $K, R \in \{0,1\}^{256}$
4. 使用 Kyber-PKE 加密算法用封装密钥 $ek$ 加密 $m$，使用 $R$ 生成需要的随机变量并得到密文 $ c $ 。
5. 输出 $(K, c)$

### Kyber-KEM 解封装

1. 使用 Kyber-PKE 解密算法用解密密钥 $s$ 解密 $c$ ，得到明文 $m'$ ；
2. 计算 $(K', R') = G(m', H(ek))$
3. 计算 $\bar{K} = J(z, c)$
4. 使用 Kyber-PKE 加密算法，使用 $ek$ 和 $R'$ 加密 $m'$，得到新密文 $c'$。
5. 如果 $c \neq c'$，返回 $\bar{K}$，否则返回 $K'$。

### Security

1. **经典安全性**

    Kyber-KEM 在选择密文攻击(CCA)下是不可区分的，因为：

    - D-MLWE 问题是难解的；
    - $ G $、$ H $、$J$ 是随机函数。

2. **量子安全性**

    Kyber-KEM 对量子对手也具有不可区分性。

### Parameter sets

|  安全等级   | $q$  | $n$  | $k$  | $\eta_1$ | $\eta_2$ | $d_u$ | $d_v$ | encaps. key size | ciphertext size | decapsulation failure rate |
| :---------: | ---- | ---- | ---- | -------- | -------- | ----- | ----- | ---------------- | --------------- | -------------------------- |
| ML-KEM-512  | 3329 | 256  | 2    | 3        | 2        | 10    | 4     | 800              | 768             | $2^{-139}$                 |
| ML-KEM-768  | 3329 | 256  | 3    | 2        | 2        | 10    | 4     | 1184             | 1088            | $2^{-164}$                 |
| ML-KEM-1024 | 3329 | 256  | 4    | 2        | 2        | 11    | 5     | 1568             | 1568            | $2^{-174}$                 |

### Omitted details

1. 哈希函数：

    - $G$: 使用 SHA3-512

    - $H$: 使用 SHA3-256

    - $J$: 使用 SHAKE256

2. 可扩展输出函数(XOF)：

    - 用于生成矩阵 $A$

    - 使用 SHAKE128 算法

    - XOF 的特点是可以产生任意长度的输出

3. 伪随机函数(PRF)：

    - 用于生成多个参数：$s$、$e$、$r$、$e_1$、$e_2$

    - 使用的是 SHAKE256 算法

4. 数论变换(NTT)：
    - 用于在环 $R_q = \mathbb{Z}_{3329}[x]/(x^{256} + 1)$ 中进行快速多项式乘法