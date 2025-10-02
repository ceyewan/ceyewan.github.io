---
categories:
  - Golang
date: 2025-06-28T21:53:07+08:00
draft: false
slug: 21b8541d
summary: 本文详细解析了Go语言中常用标准库的使用方法与技巧，涵盖list、heap、unicode、strings等核心包的关键函数。适合开发者快速掌握数据结构操作、字符串处理及排序算法，提升编程效率与代码质量。
tags:
title: Go语言标准库常用包详解：List、Heap、Sort、Unicode 等
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

// CacheItem 存储在链表 Value 中的结构体
type CacheItem struct {
    key string
    value interface{}
}
// LRUCache 定义
type LRUCache struct {
    capacity int
    list *list.List
    cache map[string]*list.Element
}
// NewLRUCache 创建一个新的 LRUCache
func NewLRUCache(capacity int) *LRUCache {
	return &LRUCache{
		capacity: capacity,
		list:     list.New(),
		cache:    make(map[string]*list.Element),
	}
}
// Get 获取一个值
func (c *LRUCache) Get(key string) (interface{}, bool) {
	if elem, ok := c.cache[key]; ok {
		// 如果找到，将该元素移动到链表头部（表示最近使用）
		c.list.MoveToFront(elem)
		// 类型断言，获取存储的值
		return elem.Value.(*CacheItem).value, true
	}
	return nil, false
}
// Put 插入或更新一个值
func (c *LRUCache) Put(key string, value interface{}) {
	// 如果 key 已存在，更新值并将其移动到头部
	if elem, ok := c.cache[key]; ok {
		c.list.MoveToFront(elem)
		elem.Value.(*CacheItem).value = value // elem 是指针类型才行
		return
	}
	// 如果 key 不存在，这是一个新元素
	// 检查容量是否已满
	if c.list.Len() >= c.capacity {
		// 获取链表尾部元素（最久未使用的）
		tail := c.list.Back()
		if tail != nil {
			// 从链表中删除
			c.list.Remove(tail)
			// 从 map 中删除
			delete(c.cache, tail.Value.(*CacheItem).key)
		}
	}
	// 创建新元素并插入到头部
	newItem := &CacheItem{key: key, value: value}
	elem := c.list.PushFront(newItem)
	c.cache[key] = elem
}
```

上面的 `elem` 的类型是 `*list.Element`，即指向 `list.Element` 结构体的指针。其中包括 `next` 和 `prev` 两个指针，`list` 指向该元素所属的链表，最后是 `Value`，表示该元素存储的值，类型是 `interface{}` 可以存储任何类型的值。

因此，假设我们向链表中写入的是一个结构体，那么需要进行一次**类型断言**，然后再来获取结构体里面的值，如 `elem.Value.(*CacheItem).key` 和 `elem.Value.(*CacheItem).value`。

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

要使用 `container/heap` 包，需要实现 `heap.Interface` 接口，该接口包含 `sort.Interface` 接口和 `Push`、`Pop` 方法，而 `sort.Interface` 接口又要求实现 `Len`、`Less`、`Swap` 这三种方法。因此，最后就是要实现上面这五种方法，不过还好，都挺容易的。注意，`Push` 和 `Pop` 都是操作的最后一个元素。可以 **借用标准库已经实现了 `sort.Interface` 的类型**（`sort.IntSlice`、`sort.StringSlice`、`sort.Float64Slice`），这样就只需要写 `Push/Pop`。

```go
// 嵌入 sort.IntSlice 来复用 Len/Swap/Less（默认是最小堆的 Less）
type IntMinHeap struct{ sort.IntSlice } // 嵌入字段，实现组合+自动转发方法
func (h *IntMinHeap) Push(v any) { h.IntSlice = append(h.IntSlice, v.(int)) }
func (h *IntMinHeap) Pop() any { old := h.IntSlice; n := len(old); x := old[n-1]; h.IntSlice = old[:n-1]; return x }

// 最大堆，重写 Less 方法
type IntMaxHeap struct{ sort.IntSlice }
func (h IntMaxHeap) Less(i, j int) bool { return h.IntSlice[i] > h.IntSlice[j] }

// TopK 返回 nums 中最大的 k 个元素，按降序排列。
func TopK(nums []int, k int) []int {
	h := &IntMinHeap{}
	// 先把前 k 个元素放进堆
	h.IntSlice = append(h.IntSlice, nums[:k]…)
	heap.Init(h)
	// 对剩下的元素：如果比堆顶（当前 k 个最大中的最小）大，替换堆顶
	for _, v := range nums[k:] {
		if v > h.IntSlice[0] {
			heap.Pop(h)
			heap.Push(h, v)
		}
	}
	// 依次 push 得到 res
	return res
}
```

## 3 Sort

### 3.1 `sort` 包

`sort` 包提供了对基本类型切片的直接排序方法，以及通过实现 `sort.Interface` 接口来对自定义类型进行排序的通用机制。

对于 `int`、`float64` 和 `string` 类型的切片，`sort` 包提供了便捷的直接排序函数，默认均为 **升序**：

- `sort.Ints([]int)`
- `sort.Float64s([]float64)`
- `sort.Strings([]string)`

要对自定义类型或复杂结构体切片进行排序，需要让该类型实现 `sort.Interface` 接口。此接口定义了三个方法：

```go
type Interface interface {
    Len() int
    Less(i, j int) bool
    Swap(i, j int)
}
```

实现 `sort.Interface` 后，即可使用 `sort.Sort` 或 `sort.Stable` 进行排序：

- `sort.Sort(data Interface)`：使用 **快速排序** 算法，不保证相等元素的相对次序。
- `sort.Stable(data Interface)`：使用 **归并排序** 算法，保证相等元素的相对次序不变（稳定排序）。

`sort` 包还提供了一些无需完整实现 `sort.Interface` 即可进行自定义排序的便捷方法：

- `sort.Slice(x any, less func(i, j int) bool)`：直接在切片 `x` 上提供一个比较函数 `less`。这是对任意切片进行自定义排序最常用的方式。
- `sort.Reverse(data Interface)`：包装一个 `sort.Interface` 对象，使其排序逻辑反转（例如，将升序变为降序）。

`sort.Search(n int, f func(int) bool) int`：在已排序的 `[0, n)` 范围内进行二分查找。它返回满足 `f(i) == true` 的最小索引 `i`。如果不存在这样的 `i`，则返回 `n`。

### 3.2 `slices` 包（Go 1.21+）

Go 1.21 引入的 `slices` 包利用泛型，极大地简化了排序 API，提供了类型安全且更简洁的写法，避免了 `sort.Interface` 的繁琐实现。

`slices` 包提供了与 `sort` 包功能类似的泛型排序函数：

- `slices.Sort[E Ordered](s []E)`：对实现了 `Ordered` 约束（如整数、浮点数、字符串）的切片进行升序排序。
- `slices.SortFunc[E any](s []E, cmp func(a, b E) int)`：通过自定义比较函数 `cmp` 对切片进行排序。`cmp` 函数应返回负数（`a < b`）、零（`a == b`）或正数（`a > b`）。
- `slices.SortStableFunc[E any](s []E, cmp func(a, b E) int)`：与 `SortFunc`类似，但保证排序的稳定性。

`slices` 包也提供了泛型版本的二分查找：

- `slices.BinarySearch[E Ordered](s []E, x E)`：在已排序的切片 `s` 中查找元素 `x`。
- `slices.BinarySearchFunc[E any, F any](s []E, x F, cmp func(E, F) int)`：通过自定义比较函数进行二分查找。

以下示例展示了 `slices` 包的简洁性，并使用了 `cmp` 包提供的 `Compare` 函数进行比较：

```go
import (
	"cmp"    // Go 1.21+ 提供的比较函数
	"slices" // Go 1.21+ 提供的泛型切片操作
	"fmt"
)

func main() {
	ints := []int{5, 2, 9, 1, 5, 6}
	fmt.Println("原始切片:", ints) // 原始切片: [5 2 9 1 5 6]

	// 1. 升序排序 (使用 slices.Sort)
	slices.Sort(ints)
	fmt.Println("升序排序:", ints) // 升序排序: [1 2 5 5 6 9]

	// 2. 降序排序 (使用 slices.SortFunc 和 cmp.Compare)
	// 注意：slices.SortFunc 会修改原切片，这里为了演示，重新初始化
	ints = []int{5, 2, 9, 1, 5, 6}
	slices.SortFunc(ints, func(a, b int) int {
		return cmp.Compare(b, a) // 比较 b 和 a，实现降序
	})
	fmt.Println("降序排序:", ints) // 降序排序: [9 6 5 5 2 1]

	// 3. 二分查找
	sortedInts := []int{1, 2, 5, 5, 6, 9}
	target := 5
	idx, found := slices.BinarySearch(sortedInts, target)
	fmt.Printf("查找 %d: 索引 %d, 找到 %t\n", target, idx, found) // 查找 5: 索引 2, 找到 true

	target = 4
	idx, found = slices.BinarySearch(sortedInts, target)
	fmt.Printf("查找 %d: 索引 %d, 找到 %t\n", target, idx, found) // 查找 4: 索引 2, 找到 false (插入点)
}
```

## 4 IO 优化

在 Go 语言中，`fmt.Scanf` 的行为与 C 语言的 `scanf` 类似，每次读取操作（例如读取数组中的一个元素）都可能触发一次系统调用。对于大量输入，如一个长度为 n 的数组，这将导致 n 次系统调用，严重拖慢程序执行速度。

解决此问题的核心思路是采用带缓冲的 I/O。通过一次性读取大量数据到内存缓冲区，后续操作直接从缓冲区获取，从而显著减少系统调用次数，大幅提升 I/O 效率。

Go 标准库中的 `bufio.Scanner` 是实现这一策略的理想工具，它能高效地从输入流中解析出单词、行或其他自定义分隔符的数据。以下是一个使用 `bufio.Scanner` 读取整数和整数数组的示例：

```go
var scanner *bufio.Scanner // 全局 scanner
func init() {
	// 从标准输入读取，并按空白字符（空格、制表符、换行符等）分割
	scanner = bufio.NewScanner(os.Stdin)
	// bufio.ScanLines 默认按行分割、bufio.ScanBytes、bufio.ScanRunes
	scanner.Split(bufio.ScanWords)
}
// readInt 读取下一个整数
func readInt() int {
	scanner.Scan() // 驱动 Scanner 向前读取直到下一个 token
	// scanner.Text() 将当前 token 作为一个新分配的字符串
	// scanner.Bytes() 将当前 token 作为一个 []bytes 切片，需要 copy 后使用
	num, _ := strconv.Atoi(scanner.Text()) 
	return num
}
// readArray 读取长度为 n 的整数数组
func readArray(n int) []int {
	arr := make([]int, n)
	for i := 0; i < n; i++ {
		arr[i] = readInt()
	}
	return arr
}
```

除了 `bufio.Scanner`，Go 还提供了 `bufio.Reader` 和 `bufio.Writer` 这两个更通用的带缓冲 I/O 接口。其中，`bufio.Reader` 提供了 `ReadByte()` 等底层方法，需要开发者自行处理数据解析逻辑，相对 `Scanner` 而言，在解析特定格式数据（如整数）时更为繁琐。`bufio.Writer` 则主要用于高效地写入数据，提供了 `WriteString` 和 `WriteByte` 等便捷方法。

## 5 字符与字符串处理

Go 语言在处理文本时，区分了字节、Unicode 码点（rune）和字符串。理解这些概念是高效处理文本的关键。

### 5.1 Unicode 码点 (`rune`)

在 Go 中，`rune` 类型代表一个 Unicode 码点，它等价于 `int32`。这与 C 语言中通常表示单个字节的 `char` 不同，`rune` 能够完整表示任何语言的字符，包括中文、emoji 等。

`unicode` 包提供了丰富的函数来判断和转换 `rune`：

*   `unicode.IsLetter(r rune)`：判断是否为字母。
*   `unicode.IsDigit(r rune)`：判断是否为数字 (0–9)。
*   `unicode.IsSpace(r rune)`：判断是否为空白字符。
*   `unicode.IsUpper(r rune)` / `unicode.IsLower(r rune)`：判断大小写。
*   `unicode.ToUpper(r rune)` / `unicode.ToLower(r rune)`：进行大小写转换。

### 5.2 字符串 (`string`) 操作

Go 语言的 `string` 是一个不可变的 UTF-8 字节序列。`strings` 包提供了大量用于字符串操作的实用函数：

*   **查找与计数**：
    *   `strings.Contains(s, sub)`：检查是否包含子串。
    *   `strings.Index(s, sub)` / `strings.LastIndex(s, sub)`：查找子串第一次/最后一次出现的位置。
    *   `strings.Count(s, sub)`：计算子串出现的次数。
*   **比较**：
    *   `strings.EqualFold(s1, s2)`：忽略大小写比较两个字符串。
*   **分割与拼接**：
    *   `strings.Split(s, sep)` / `strings.SplitAfter(s, sep)`：按分隔符分割字符串。
    *   `strings.Fields(s)`：按连续的空白字符分割字符串。
    *   `strings.FieldsFunc(s, f)`：使用自定义函数定义分割规则。
    *   `strings.Join(elems, sep)`：将字符串切片拼接成一个字符串。
*   **替换与修剪**：
    *   `strings.Replace(s, old, new, n)`：替换子串，`n=-1` 表示替换所有匹配项。
    *   `strings.Trim(s, cutset)` / `strings.TrimSpace(s)`：去除字符串首尾指定的字符集 / 空白字符。
*   **大小写转换**：
    *   `strings.ToUpper(s)` / `strings.ToLower(s)`：将字符串转换为大写 / 小写。

**高效字符串拼接**：
由于字符串的不可变性，频繁使用 `+` 进行拼接会导致性能问题。推荐使用 `strings.Builder` 来高效构建字符串：

```go
var b strings.Builder
b.WriteString("hello")
b.WriteByte(' ')   // 写入单字节
b.WriteRune('世')  // 写入 Unicode 字符
res := b.String()
```

### 5.3 字符串与数字转换 (`strconv`)

`strconv` 包提供了字符串和基本数据类型（如整数、浮点数）之间的转换功能：

*   `strconv.Atoi(s)`：将字符串转换为 `int`。
*   `strconv.Itoa(i)`：将 `int` 转换为字符串。
*   `strconv.ParseInt(s, base, bitSize)`：将指定进制的字符串解析为整数。
*   `strconv.FormatInt(i, base)`：将整数格式化为指定进制的字符串。

### 5.4 字节切片 (`[]byte`) 操作

`[]byte` 是 Go 语言中表示原始字节序列的切片。它与 `string` 之间可以方便地相互转换，并且 `bytes` 包提供了与 `strings` 包功能类似的 API，用于操作字节切片。

*   **字符串与字节切片互转**：
    *   `[]byte(s)`：将 `string` 转换为 `[]byte`。
    *   `string(b)`：将 `[]byte` 转换为 `string`。
*   **字符串与 `[]rune` 互转**：
    *   `[]rune(s)`：将 `string` 转换为 `[]rune`，按 Unicode 码点拆分，常用于处理多字节字符（如中文、emoji）。
    *   `string(runeSlice)`：将 `[]rune` 转换为 `string`。

`bytes` 包的 API 与 `strings` 包高度相似，例如：

*   `bytes.Contains(b, sub)`
*   `bytes.Split(b, sep)`
*   `bytes.TrimSpace(b)`

### 5.5 总结：`byte`、`rune`、`string` 的关系

理解这三者的关系对于 Go 语言的文本处理至关重要：

*   **`byte`**：等价于 `uint8`，表示一个 8 位字节。它是构成所有 Go 数据的最小单位，常用于处理原始二进制数据或 ASCII 字符。
*   **`rune`**：等价于 `int32`，表示一个 Unicode 码点。它是 Go 语言中处理单个字符（无论其编码长度）的标准方式。
*   **`string`**：是不可变的 UTF-8 编码的字节序列。它不直接存储字符，而是存储字符的 UTF-8 编码字节。

**遍历字符串的正确姿势**：
*   **按 `rune` 遍历**：使用 `for _, r := range s` 循环，Go 会自动解码 UTF-8 字节序列，每次迭代提供一个 `rune`。这是处理包含多字节字符（如中文、emoji）字符串的推荐方式。
*   **按 `byte` 遍历**：使用 `for i := 0; i < len(s); i++ { b := s[i] }` 循环，或者 `for _, b := range []byte(s)`。这适用于只处理 ASCII 字符或需要直接操作底层字节的场景。
