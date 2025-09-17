---
categories:
  - Golang
date: 2025-06-28T21:53:07+08:00
draft: false
slug: 21b8541d
summary: 本文详细解析了Go语言中常用标准库的使用方法与技巧，涵盖list、heap、unicode、strings等核心包的关键函数。适合开发者快速掌握数据结构操作、字符串处理及排序算法，提升编程效率与代码质量。
tags:
title: Go语言标准库常用包详解：List、Heap、Unicode与更多实用工具
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

Go 的排序能力主要分两层：

1. **`sort` 包**：经典接口 + 基于 `sort.Interface` 的通用排序。
2. **`slices` 包（Go 1.21+）**：泛型化、更简洁的排序 API。

### 3.1 `sort` 包

#### 3.1.1 基础方法

- `sort.Ints([]int)`
- `sort.Float64s([]float64)`
- `sort.Strings([]string)`

均为 **升序**。

#### 3.1.2 通用接口

实现 `sort.Interface` 即可用 `sort.Sort`：

```go
type Interface interface {
    Len() int
    Less(i, j int) bool
    Swap(i, j int)
}
```

`sort.Sort` 使用快速排序；`sort.Stable` 使用归并排序，保证相等元素相对次序不变。

#### 3.1.3 自定义比较

- `sort.Reverse(sort.IntSlice(ints))`：反转已有比较逻辑。
- `sort.Slice(x, func(i, j int) bool)`：直接在切片上提供比较函数。

#### 3.1.4 查找

`sort.Search(n, f func(int) bool) int`：二分查找，返回满足 `f(i)==true` 的最小索引。

### 3.2 `slices` 包（Go 1.21+）

`slices` 基于泛型，提供类型安全的 API，避免了 `sort.Interface` 的冗余。

常用函数：

- `slices.Sort([]T)`：对有序类型（整数、浮点、字符串等）排序，默认升序。
- `slices.SortFunc([]T, func(a, b T) int)`：自定义比较函数（返回负数/0/正数）。
- `slices.SortStableFunc([]T, func(a, b T) int)`：稳定排序。
- `slices.BinarySearch([]T, target T)` / `slices.BinarySearchFunc([]T, x T, cmp func(a, b T) int)`：二分查找。

示例：

```go
import (
    "cmp"
    "slices"
)

func main() {
    ints := []int{5, 2, 9, 1, 5, 6}
    // 升序
    slices.Sort(ints)
    // 降序
    slices.SortFunc(ints, func(a, b int) int {
        return cmp.Compare(b, a)
    })
}
```

## 4 Unicode（处理单个字符 `rune`）

Go 的 `rune` = Unicode 码点，等价于 `int32`，对应 C 里的 " 字符 "（但不是 1 字节的 char，而是完整的 Unicode 编码）。

- `unicode.IsLetter(r rune)`：是否是字母
- `unicode.IsDigit(r rune)`：是否是数字（0–9）
- `unicode.IsSpace(r rune)`：是否是空白字符
- `unicode.IsUpper(r rune)` / `unicode.IsLower(r rune)`：大写/小写
- `unicode.ToUpper(r rune)` / `unicode.ToLower(r rune)`：大小写转换

## 5 Strings（字符串操作）

字符串是不可变的 UTF-8 字节序列。常见操作：

- `strings.Contains(s, sub)`：是否包含子串
- `strings.Index(s, sub)` / `strings.LastIndex(s, sub)`：第一次/最后一次出现位置
- `strings.Count(s, sub)`：子串出现次数
- `strings.EqualFold(s1, s2)`：忽略大小写比较
- `strings.Split(s, sep)` / `strings.SplitAfter(s, sep)`：分割字符串
- `strings.Fields(s)`：按空白字符分割
- `strings.FieldsFunc(s, f)`：自定义分割规则
- `strings.Join(elems, sep)`：切片拼接成字符串
- `strings.Replace(s, old, new, n)`：替换，`n=-1` 表示替换全部
- `strings.Trim(s, cutset)` / `strings.TrimSpace(s)`：去掉首尾指定字符 / 空白
- `strings.ToUpper(s)` / `strings.ToLower(s)`：大小写转换

拼接效率推荐用 `strings.Builder`：

```go
var b strings.Builder
b.WriteString("hello")
b.WriteByte(' ')   // 写入单字节
b.WriteRune('世')  // 写入 Unicode 字符
res := b.String()
```

## 6 Strconv（字符串与数字转换）

- `strconv.Atoi(s)`：string → int
- `strconv.Itoa(i)`：int → string
- `strconv.ParseInt(s, base, bitSize)`：进制解析为整数
- `strconv.FormatInt(i, base)`：整数格式化为字符串

## 7 Bytes（字节切片操作）

`[]byte` 是原始字节序列，和 `string` 可以互转：

- `[]byte(s)`：string → `[]byte`
- `string(b)`：`[]byte` → string
- `[]rune(s)`：string → `[]rune`（按 Unicode 拆分，常用于处理中文或 emoji）
- `string(runeSlice)`：`[]rune` → string

`bytes` 包的 API 和 `strings` 几乎一样，比如：

- `bytes.Contains(b, sub)`
- `bytes.Split(b, sep)`
- `bytes.TrimSpace(b)`

## 8 常用 Math

- `math.Abs(x)`：绝对值
- `math.Max(x, y)` / `math.Min(x, y)`：最大/最小
- `math.Ceil(x)` / `math.Floor(x)` / `math.Round(x)` / `math.Trunc(x)`：取整相关

### 8.1 补充：rune / Byte / Char 对应关系

- `byte` = `uint8`，一个字节（C 的 `unsigned char`），常用来存放原始数据。
- `rune` = `int32`，表示一个 Unicode 码点（C 里没有完全对应，接近 `wchar_t`）。
- `string` = UTF-8 编码的不可变字节序列。
- **若要逐字符遍历字符串**：用 `for _, r := range s`（按 rune 遍历，支持中文、emoji）。
- **若只处理 ASCII**：可以直接把 `string` 转为 `[]byte`。
