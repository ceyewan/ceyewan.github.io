---
date: '2025-06-28T21:53:07+08:00'
draft: false
title: 'Go 库函数和内置方法'
slug: '21b8541d'
tags:
  - ""
categories:
  - "Golang"
---

## 1 List

`container/list` 包提供了一个双向链表的实现。双向链表是一种常见的数据结构，支持高效的插入、删除和遍历操作。

- `l:= list.New()`：创建一个新的双向链表。
- `l.PushFront(value)`：在链表头部插入一个元素。
- `l.PushBack(value)`：在链表尾部插入一个元素。
- `l.InsertBefore(value, mark)`：在 `mark` 元素之前插入一个元素。
- `l.InsertAfter(value, mark)`：在 `mark` 元素之后插入一个元素。
- `l.Remove(elem)`：删除链表中的指定元素。
- `l.MoveToFront(elem)`：将元素移动到链表头部。
- `l.MoveToBack(elem)`：将元素移动到链表尾部。
- `l.MoveBefore(elem, mark)`：将元素移动到 `mark` 元素之前。
- `l.MoveAfter(elem, mark)`：将元素移动到 `mark` 元素之后。
- `l.Front()`：获取链表头部的元素。
- `l.Back()`：获取链表尾部的元素。
- `l.Len()`：返回链表中元素的数量。

```go
import "container/heap"

for e := l.Front(); e != nil; e = e.Next() {
    fmt.Println(e.Value)
}
```

上面的 `e` 的类型是 `*list.Element`，即指向 `list.Element` 结构体的指针。其中包括 `next` 和 `prev` 两个指针，`list` 指向该元素所属的链表，最后是 `Value`，表示该元素存储的值，类型是 `interface{}` 可以存储任何类型的值。

因此，假设我们向链表中写入的是一个结构体，那么需要进行一次**类型断言**，然后再来获取结构体里面的值，如 `e.Value.(*CacheItem).key` 和 `e.Value.(*CacheItem).value`。

## 2 Heap

`container/heap` 包提供了一个堆的实现。堆是一种特殊的树形数据结构，通常用于实现优先队列。堆分为最小堆和最大堆，`container/heap` 包默认实现的是最小堆。

- `h:= &Heap{}`：创建一个堆对象。
- `heap.Init(h)`：初始化堆，使其满足堆的性质。
- `heap.Push(h, value)`：向堆中插入一个元素，并保持堆的性质。
- `heap.Pop(h)`：从堆中删除并返回最小（或最大）的元素，并保持堆的性质。
- `h[0]`：获取堆顶元素（最小或最大元素），但不删除它。
- `len(h)`：返回堆中元素的数量。

```go
type hp []*ListNode
func (h hp) Len() int { return len(h) }
func (h hp) Less(i, j int) bool { return h[i].Val < h[j].Val } // 最小堆
func (h hp) Swap(i, j int) { h[i], h[j] = h[j], h[i] }
func (h *hp) Push(v any) { *h = append(*h, v.(*ListNode)) }
func (h *hp) Pop() any { a := *h; v := a[len(a)-1]; *h = a[:len(a)-1]; return v }
```

要使用 `container/heap` 包，需要实现 `heap.Interface` 接口，该接口包含 `sort.Interface` 接口和 `Push`、`Pop` 方法，而 `sort.Interface` 接口又要求实现 `Len`、`Less`、`Swap` 这三种方法。因此，最后就是要实现上面这五种方法，不过还好，都挺容易的。注意，`Push` 和 `Pop` 都是操作的最后一个元素。

## 3 Unicode

`unicode` 包是 Go 语言中用于处理 Unicode 字符的标准库包。它提供了许多函数来检查和操作 Unicode 字符。

- `unicode.IsLetter(r rune) bool`：检查字符 `r` 是否是字母；
- `unicode.IsDigit(r rune) bool`：检查字符 `r` 是否是数字（0-9）；
- `unicode.IsSpace(r rune) bool`：检查字符 `r` 是否是空格、制表符、换行符等；
- `unicode.IsUpper(r rune) bool`：检查字符 `r` 是否是大写字母；
- `unicode.IsLower(r rune) bool`：检查字符 `r` 是否是小写字母。
- `unicode.ToUpper(r rune) rune`：将字符 `r` 转换为大写形式；
- `unicode.ToLower(r rune) rune`：将字符 `r` 转换为小写形式；
- `unicode.In(r rune, ranges…*unicode.RangeTable) bool`：检查字符 `r` 是否在指定的 Unicode 范围内。

## 4 Strings

- `strings.Contains(s, substr string) bool`：检查字符串 `s` 是否包含子串 `substr`；
- `strings.Index(s, substr string) int`：返回子串 `substr` 在字符串 `s` 中第一次出现的索引，如果未找到则返回 `-1`；
- `strings.LastIndex(s, substr string) int`：返回子串 `substr` 在字符串 `s` 中最后一次出现的索引，如果未找到则返回 `-1`;
- `strings.Count(s, substr string) int`：返回子串 `substr` 在字符串 `s` 中出现的次数。
- `strings.EqualFold(s1, s2 string) bool`：比较字符串 `s1` 和 `s2` 是否相等（不区分大小写）；
- `strings.Split(s, sep string) []string`：使用分隔符 `sep` 将字符串 `s` 分割为子串切片；
- `strings.SplitAfter(s, sep string) []string`：使用分隔符 `sep` 将字符串 `s` 分割为子串切片，保留分隔符；
- `strings.Fields(s string) []string`：将字符串 `s` 按空白字符（空格、制表符、换行符等）分割为子串切片；
- `strings.FieldsFunc(s string, f func(rune) bool) []string`：使用自定义函数 `f` 将字符串 `s` 分割为子串切片。
- `strings.Join(elems []string, sep string) string`：使用分隔符 `sep` 将字符串切片 `elems` 连接为一个字符串。
- `strings.Replace(s, old, new string, n int) string`：将字符串 `s` 中的前 `n` 个 `old` 子串替换为 `new`。如果 `n` 为 `-1`，则替换所有。
- `strings.Trim(s, cutset string) string`：去除字符串 `s` 开头和结尾的 `cutset` 字符。`TrimSpace`、`TrimLeft`、`TrimRight`。
- `strings.ToUpper(s string) string`：将字符串 `s` 转换为大写。
- `strings.ToLower(s string) string`：将字符串 `s` 转换为小写。
- `strings.ToTitle(s string) string`：将字符串 `s` 转换为标题格式。
- `strings.Builder` 使用方法，适合用于大量字符串拼接：

```go
var b strings.Builder
b.WriteString("hello")
b.WriteRune(' ')
b.WriteByte('G')
result := b.String()
b.Reset()  // 重置
Builder.Grow(n) // 预分配
```

## 5 Strconv

- `strconv.Atoi(s string) (int, error)`：将字符串 `s` 转换为 `int` 类型。如果转换失败，返回错误。
- `strconv.ParseInt(s string, base int, bitSize int) (int64, error)`：将字符串 `s` 转换为指定进制（`base`）和位宽（`bitSize`）的整数类型（如 `int64`）。`base` 可以是 2 到 36 之间的值，`bitSize` 可以是 0、8、16、32、64。
- `strconv.Itoa(i int) string`：将整数 `i` 转换为字符串。
- `strconv.FormatInt(i int64, base int) string`：将整数 `i` 转换为指定进制（`base`）的字符串。

## 6 Sort

`sort` 包是 Go 语言中用于排序的标准库包，提供了对切片和用户自定义集合进行排序的功能。它支持对整数、浮点数、字符串等基本类型的切片进行排序，同时也允许用户通过实现 `sort.Interface` 接口来自定义排序规则。

- `sort.Ints(s []int)`：对整数切片 `s` 进行升序排序。
- `sort.Float64s(s []float64)`：对浮点数切片 `s` 进行升序排序。
- `sort.Strings(s []string)`：对字符串切片 `s` 进行升序排序。
- `sort.Search(n int, f func(int) bool) int`：在已排序的集合中查找满足条件的最小索引。`f` 是一个判断函数，返回 `true` 表示满足条件。

通过实现 `sort.Interface` 接口，可以对任意类型的切片进行排序。`sort.Interface` 接口包含三个方法：

```go
type Interface interface {
    Len() int           // 返回集合的长度
    Less(i, j int) bool // 比较索引 i 和 j 的元素
    Swap(i, j int)      // 交换索引 i 和 j 的元素
}
```

实现该接口后，可以使用 `sort.Sort` 函数进行排序。

**反转排序**

使用 `sort.Sort(sort.Reverse(sort.IntSlice(ints)))`，首先将 ints 转换为 `sort.IntSlice` 类型，`sort.IntSlice` 实现了 `sort.Interface` 接口，然后 `sort.Reverse` 会反转 `Less` 方法的逻辑，最后 `sort.Sort` 使用快速排序（QuickSort）算法对集合进行排序。

也可使用 `sort.Slice` 接受一个切片和一个自定义比较函数，使用快速排序算法对切片进行排序。

```go
ints := []int{5, 2, 9, 1, 5, 6} 
sort.Sort(sort.Reverse(sort.IntSlice(ints)))
sort.Slice(ints, func(i, j int) bool { return ints[i] > ints[j] // 反向排序 })
```

`sort` 包提供了 `sort.Stable` 函数，可以对集合进行稳定排序。

## 7 Maths

由于 Go 前期并不支持泛型，因此，只提供了一些简单的数学函数方法：

- `math.Abs(x float64) float64`：返回 `x` 的绝对值。
- `math.Max(x, y float64) float64`：返回 `x` 和 `y` 中的最大值。
- `math.Min(x, y float64) float64`：返回 `x` 和 `y` 中的最小值。
- `math.Mod(x, y float64) float64`：返回 `x` 除以 `y` 的余数。
- `math.Ceil(x float64) float64`：返回大于或等于 `x` 的最小整数。
- `math.Floor(x float64) float64`：返回小于或等于 `x` 的最大整数。
- `math.Round(x float64) float64`：返回 `x` 的四舍五入值。
- `math.Trunc(x float64) float64`：返回 `x` 的整数部分，去掉小数部分。
- `math.Inf(sign int) float64`：返回正无穷大（`sign >= 0`）或负无穷大（`sign < 0`）。

## 8 Bytes

bytes 包实现了操作 `[]byte` 的常用函数。本包的函数和 strings 包的函数相当类似。

### 8.1 内置方法和类型转换

|**类别**|**方法**|**描述**|
|---|---|---|
|**内置函数**|`append`|向切片追加元素|
||`delete`|从映射中删除键值对|
||`len`|返回长度|
||`cap`|返回容量|
||`make`|创建切片、映射或通道|
||`new`|分配内存并返回指针|
||`copy`|复制切片内容|
||`close`|关闭通道|
||`panic` 和 `recover`|处理运行时错误|
|**类型转换**|`[]byte(s)`|字符串转字节切片|
||`string(b)`|字节切片转字符串|
||`int(x)`|转换为 `int`|
||`float64(x)`|转换为 `float64`|
||`rune(x)`|转换为 `rune`|
||`string(r)`|`rune` 转字符串|
||`[]rune(s)`|字符串转 `rune` 切片|
||`bool(x)`|转换为 `bool`|
