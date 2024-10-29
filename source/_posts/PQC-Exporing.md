---
title: 'PQC:Exploring Kyber in Python'
categories:
  - PQC
tags:
  - Kyber
abbrlink: 63fe6d08
date: 2024-10-29 18:33:09
---
# PQC: Exploring Kyber in Python

## Preface

CRYSTALS-Kyber 是 NIST 选定的首个抗量子攻击的密钥封装机制（KEM）。Kyber 是一种基于格的公钥（非对称）密码系统，其安全性依赖于解决模块格中的带误差学习问题（Learning With Errors, LWE）。其主要设计目的是在两个通信方之间安全地建立共享密钥，以便后续使用对称加密，确保攻击者无法解密该密钥，从而保护双方的后续通信安全。 

> **LWE(Learning With Errors)**: 给定随机矩阵 A 和带有小随机误差  e 的向量 $b = As + e$，其中 s 是秘密向量；该问题的困难性在于从这些带噪声的线性方程中恢复出原始秘密向量 s。
>
> **MLWE(Module Learning With Errors)**: 将 LWE 中的整数系数提升到多项式环 $Rq = Zq[X]/(X^n + 1)$ 上，使用多项式向量作为秘密值和误差项；这种模块化结构在保持安全性的同时提供了更紧凑的密钥和更高效的运算。

Kyber 提供了两种主要的加密方案：

1. CPA 安全的公钥加密（PKE）方案;
2. IND-CCA2 安全的密钥交换机制（KEM），通过结合 PKE 方案与 Fujisaki-Okamoto（FO）变换提供 。

>**CPA**（Chosen Plaintext Attack），选择明文攻击，即攻击者可以选择任意明文并获得其对应的密文。
>
>**IND-CCA2**（Indistinguishability under Chosen Ciphertext Attack），选择密文攻击下的不可区分性。攻击者可以选择任意密文并获得其对应的明文，但无法确定目标密文的明文。即使攻击者可以访问其他密文的解密结果，他们仍然无法区分出两个候选明文对应的密文。

Kyber 提供三组参数，分别为 Kyber512、Kyber768 和 Kyber1024，旨在实现 128、192 和 256 位的安全级别。Kyber 设计的一大优点是其参数的可扩展性，不改变格的维度（n）、模数（q）和噪声分布的方差，而是仅通过增加一个缩放参数 k 来提高安全性，从而实现更高的格维度。这意味着在 Kyber 中，所有操作都可以使用相同的基本操作和参数，只是为了达到更高的安全级别，需要更多次重复这些操作。

## Polynomial

### 表示

通常，一个多项式可以表示为：

$$
P(X) = 5X^3 + 2X^2 + 1
$$
更一般地，可以表示为：

$$
P(X) = \sum_{i = 0}^{n} p_i X^i
$$

其中，$ p_i $ 是系数，$ n $ 是多项式的最大次数。因此，可以用其 $ n + 1 $ 个系数来表示一个多项式，形式为：

$$
[p_0, p_1, \ldots, p_n]
$$

例如，上述的多项式 $ P(X) $ 可以表示为：

$$
[1, 0, 2, 5]
$$

### 域和环

Kyber 中的数字定义在有限域 $ GF(q) = \mathbb{Z}/q\mathbb{Z} $ 中，$ \mathbb{Z} $ 是所有整数的集合，$ q $ 是一个素数，而 $ GF $ 代表伽罗瓦域。简单来说，该域只包含整数，并定义了一个简单的模 $ q $，在 Kyber 中对数字或多项式系数的每次操作都将取模 $ q $。 其次，Kyber 中的多项式定义在另一个特殊结构中，称为多项式环 $ R = GF[q](X)/(X^n + 1) $，意思是每个多项式操作最终都将取模 $ X^n + 1 $。由于模是 $ X^n + 1 $，这意味着 $ X^n = -1 $，因为环是循环的。因此，我们可以简单地将目标多项式中的每个 $ X^n $ 替换为 -1，直到所有项的次数都小于 $ n $。

### 多项式运算

1. 加法：将两个多项式的对应系数相加，然后对 $ q $ 取模。
2. 减法：可视为对一个多项式的系数取反后再进行加法。
3. 乘法：将一个多项式的每个系数与另一个多项式的所有系数相乘，并将结果相加。不仅需要模 q，还需要对多项式 $ F(X) = X^n + 1 $ 进行模运算。

### 向量化多项式

在有了多项式运算后，就可以创建由多项式组成的向量和矩阵，并定义它们的运算。由多项式组成的向量就是向量中的每个元素都是一个多项式。

- 向量加法：只是逐分量的多项式加法。
- 向量乘法（内积）：只是一个分量多项式乘法，并使用多项式加法对结果求和。
- 矩阵-向量乘法：和普通的矩阵向量乘法一样，只是具体的元素不是一个数了，而是一个多项式。

## Kyber InnerPKE

这部分我们将实现 Kyber 底层的 PKE 原语。

### Key Generation

- 随机采样矩阵 A，维度为 k × k。A 由多项式组成，这些多项式使用之前定义的算术运算。
- 额外采样两个向量 s 和 e，各包含 k 个多项式。s 和 e 中的多项式具有 "小系数"。
- 计算 t：$t = As + e$ 。内部公钥加密
- 定义公钥：$(A, t)$；私钥：$s$ 。

### Quantum-Resistant Security

在讨论如何使用密钥之前，可以简要了解公钥的结构 $$(A, t)$$。由于 $$t$$ 不仅是矩阵向量乘积，还包含随机“噪声”向量，因此仅通过观察 $$(A, t)$$ 来确定秘密密钥 $$s$$ 并不简单。如果没有噪声偏移，可以使用行简化和高斯消元技巧来求解 $$s$$。

更具体地说，从 $$(A, t)$$ 求解 $$s$$ 可以简化为解决一个模块学习带错误（M-LWE）问题的实例，这被认为即使对于量子计算机也很难。因此，Kyber 通过将其核心公钥方案与一个数学上困难的问题（M-LWE）联系起来，获得了量子抗性。

### Encryption

在生成密钥对后，可以进行加密，其中一方使用公钥 $$(A, t)$$ 来加密消息 $$m$$。

加密过程中，加密方首先会随机生成一个掩蔽向量（blinding vector） $$r \in R^k$$、一个新的错误向量 $$e_1 \in R^k$$ 和一个单一的错误多项式 $$e_2 \in R$$。所有采样的多项式都将具有与密钥生成中 $$s$$ 和 $$e$$ 相同的“小系数”。

接下来，加密方会使用要加密消息的二进制表示，并将每个比特编码为二进制多项式的系数。例如，如果 $$m = 11$$（即 $$(1011)_2$$），则 $$m_b = X^3 + X + 1$$。

最终，Kyber 内部公钥加密（PKE）方案定义为以下两个计算：

$$
\text{Enc}((A, t), m_b) \rightarrow (u, v) \newline

u = A^T r + e_1 \newline

v = t^T r + e_2 + \left\lfloor \frac{q}{2} \right\rfloor m_b
$$

最终，我们得到一个向量 $$u$$ 和一个多项式 $$v$$，作为 Kyber 内部 PKE 的密文。注意 $$v$$ 中的 $$\left\lfloor \frac{q}{2} \right\rfloor m_b$$ 部分是为了将二进制多项式 $$m_b$$ 的幅度缩放到接近于有限域大小 $$q$$ 的一半。

缩放部分是确保成功解密的关键步骤，因为消息是二进制消息（0,1），而底层域 $$q$$ 通常较大（例如 17）。在这种情况下，1 被编码为 9，这比 0（仍然编码为 0）更远。因此，即使最终值受到小噪声的影响，我们仍然可以判断它更接近于 0 还是 9，从而解码出最初是 0 还是 1。二进制值的缩放为我们提供了更多的容错空间，同时仍然允许解密成功。

### Decryption

在接收到密文后，我们可以查看如何解密密文并恢复原始消息。

Kyber 定义内部公钥加密（PKE）解密为以下过程：

$$
\text{Dec}(s, (u, v)) \rightarrow m_n \newline

m_n = v - s^T u \newline

m_n = t^T r + e_2 + \left\lfloor \frac{q}{2} \right\rfloor m_b - s^T (A^T r + e_1) \newline

m_n = e^T r + e_2 + \left\lfloor \frac{q}{2} \right\rfloor m_b - s^T e_1
$$

我们可以看到，剩余的噪声项 $$e^T r$$、$$e_2$$ 和 $$s^T e_1$$ 都相对较小，因为它们是以“小系数”进行采样的。另一方面，$$\left\lfloor \frac{q}{2} \right\rfloor m_b$$ 相对较大，因为它的幅度被缩放到接近于有限域大小 $$q$$ 的一半。

因此，为了从 $$m_n$$ 恢复 $$m_b$$，我们只需执行一个“取整”操作，查看 $$m_n$$ 中的每个系数是更接近于 $$\left\lfloor \frac{q}{2} \right\rfloor m_b$$ 还是 0。最后，比较结果将产生一个布尔向量，应该与初始的 $$m_b$$ 匹配。

### Observations

实际消息（缩放后的 $$m_b$$）被 $$t^T r + e_2$$ 混淆，这类似于一次性密钥（one-time pad），并带有一些额外的噪声。由于 $$t = As + e$$ 的特殊结构，拥有秘密密钥 $$s$$ 的一方可以大致“重构”一次性密钥中 $$t^T r$$ 部分。这使得该方能够有效地从 $$v$$ 中去除大部分一次性密钥，同时加上或减去噪声向量引入的额外噪声。随后，消息的缩放和取整操作可以处理噪声并恢复消息。

## Next Steps

1. 放大参数（k，q，f 等），从而实现后量子安全；
2. 使用数论变换（NTT）来有效的计算多项式乘法，以应对大参数；
3. 使用随机种子并对种子进行伪随机扩展来填充大矩阵 A，以节省大小；
4. 使用压缩技术，删除不重要的信息并无损“解压缩”来缩短密文。

Kyber 的 `InnerPKE` 只提供 CPA 安全的公钥加密方案，还需要将其转换为 CCA 安全方案。

## 代码文件

```python
import numpy as np


# 多项式运算
def add_poly(a, b, q):
    result = [0] * max(len(a), len(b))
    for i in range(max(len(a), len(b))):
        if i < len(a):
            result[i] += a[i]
        if i < len(b):
            result[i] += b[i]
        result[i] %= q
    return result


def inv_poly(a, q):
    return list(map(lambda x: -x % q, a))


def sub_poly(a, b, q):
    return add_poly(a, inv_poly(b, q), q)


def mul_poly_simple(a, b, f, q):
    tmp = [0] * (len(a) * 2 - 1)

    for i in range(len(a)):
        for j in range(len(b)):
            tmp[i + j] += a[i] * b[j]

    degree_f = len(f) - 1
    for i in range(degree_f, len(tmp)):
        tmp[i - degree_f] -= tmp[i]
        tmp[i] = 0

    tmp = list(map(lambda x: x % q, tmp))
    return tmp[:degree_f]


# 矩阵向量运算
def add_vec(v0, v1, q):
    assert (len(v0) == len(v1))
    result = []
    for i in range(len(v0)):
        result.append(add_poly(v0[i], v1[i], q))
    return result


def mul_vec_simple(v0, v1, f, q):
    assert (len(v0) == len(v1))
    degree_f = len(f) - 1
    result = [0 for i in range(degree_f - 1)]
    for i in range(len(v0)):
        result = add_poly(result, mul_poly_simple(v0[i], v1[i], f, q), q)
    return result


def mul_mat_vec_simple(m, a, f, q):
    result = []
    for i in range(len(m)):
        result.append(mul_vec_simple(m[i], a, f, q))
    return result


def transpose(m):
    result = [[None for i in range(len(m))] for j in range(len(m[0]))]
    for i in range(len(m)):
        for j in range(len(m[0])):
            result[j][i] = m[i][j]
    return result


# 生成公私钥
def generate_keys(k, f, q):
    degree_f = len(f) - 1
    A = (np.random.random([k, k, degree_f]) * q).astype(int)
    s = (np.random.random([k, degree_f]) * 3).astype(int) - 1
    e = (np.random.random([k, degree_f]) * 3).astype(int) - 1
    t = add_vec(mul_mat_vec_simple(A, s, f, q), e, q)
    return A, t, s


# 加密
def encrypt(A, t, m_b, f, q, r, e_1, e_2):
    half_q = int(q / 2 + 0.5)
    m = list(map(lambda x: x * half_q, m_b))
    u = add_vec(mul_mat_vec_simple(transpose(A), r, f, q), e_1, q)
    v = sub_poly(add_poly(mul_vec_simple(t, r, f, q), e_2, q), m, q)
    return u, v


# 解密
def decrypt(s, u, v, f, q):
    m_n = sub_poly(v, mul_vec_simple(s, u, f, q), q)
    half_q = int(q / 2 + 0.5)

    def round(val, center, bound):
        dist_center = np.abs(center - val)
        dist_bound = min(val, bound - val)
        return center if dist_center < dist_bound else 0

    m_n = list(map(lambda x: round(x, half_q, q), m_n))
    m_b = list(map(lambda x: x // half_q, m_n))
    return m_b


# 测试
def test_enc_dec(N, k, f, q):
    degree_f = len(f) - 1
    failed = 0

    for i in range(N):
        A, t, s = generate_keys(k, f, q)
        m_b = (np.random.random(degree_f) * 2).astype(int)
        r = (np.random.random([k, degree_f]) * 3).astype(int) - 1
        e_1 = (np.random.random([k, degree_f]) * 3).astype(int) - 1
        e_2 = (np.random.random([degree_f]) * 3).astype(int) - 1
        u, v = encrypt(A, t, m_b, f, q, r, e_1, e_2)
        m_b2 = decrypt(s, u, v, f, q)
        if m_b.tolist() != m_b2:
            failed += 1

    print(f"[k={k}, f={f}, q={q}] Test result: {
          failed}/{N} failed decryption!")


# 运行测试
# np.random.seed(0xdeadbeef)
test_enc_dec(100, 2, [1, 0, 0, 0, 1], 17)
test_enc_dec(100, 2, [1, 0, 0, 0, 1], 37)
test_enc_dec(100, 2, [1, 0, 0, 0, 1], 67)

```

