---
title: CMU15445 - Project 0 - C++ Primer
categories:
  - CMU15445
tags:
  - CMU15445
abbrlink: 6f3503f7
---

### 环境搭建

1. 实验说明：

> https://15445.courses.cs.cmu.edu/fall2022/project0/

2. 下载源代码：

```
git clone https://github.com/cmu-db/bustub.git
```

3. 安装依赖

可以在本地安装，那么只需要执行 `sudo ./build_support/packages.sh` 即可（要求是 `ubuntu` 系统）；同时我们也注意到，提供了 `Dockerfile` 文件，因此，我们可以直接使用 `docker` 来配置环境，执行下面几条命令，然后就能在 `vscode` 中使用了。

```
docker build . -t bustub
docker create -t -i --name bustub -v $(pwd):/bustub bustub bash
```

进入容器（或者在本地安装完依赖）后，编译代码：

```
mkdir build
cd build
cmake ..
make [-j 8] # 指定线程
```

4. 项目说明

> 这个实验要求我们实现一个并发 `trie` 树，主要实现插入、删除和查找这三个算法。可以参考 `leetcode` 的 `trie` 树（前缀树）的题。数据在 `trie` 树中以 `key-value` 键值对形式存储，键是非空可变长度的字符串。例如，考虑在 `trie` 中插入 `kv` 对 `("ab", 1)` 和 `("ac", "val")`，树的结构如下：
>
> ![Trie example](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/graph.png)

### C++ 前置知识

这个 project 主要目的就是测试 C++ 水平，所以语言和代码贴的比较多。

```cpp
explicit TrieNode(char key_char) : key_char_(key_char) {}
```

> `explicit` 这个关键字用来说明这个类的构造不支持隐式类型转换。举个例子吧：
>
> ```cpp
> class Person
> {
> public:
>     int age;
>     std::string name;
>     explicit Person(const std::string &name_) : name(name_) {}
>     Person(int age_) : age(age_) {}
> };
> 
> Person a = 22; // 隐式构造，存在这样的构造函数
> // Person b = std::string("ceyewan"); wrong，明确了不能使用隐式构造
> Person b("ceyewan"); // 只能这样构造
> std::cout << a.age << "\n" << b.name << std::endl;
> ```
>
> 同样，这样初始化不仅代码风格简单，而且可以避免性能浪费，如果不这样的话，`“ceyewan“`（`const char*` 类型）会调用 `string` 的构造函数得到 `name_`，然后再次调用 `string` 的构造函数得到 `name`。

```cpp
TrieNode(TrieNode &&other_trie_node) noexcept {
    this->key_char_ = other_trie_node.key_char_;
    this->is_end_ = other_trie_node.is_end_;
    this->children_ = std::move(other_trie_node.children_);
}
```

> `noexcept` 简单的理解成阻止抛出异常。
>
> 这里，我们使用了右值引用，因为 `children_` 中存储的是 `unique_ptr` 不能使用拷贝构造，只能使用移动构造。`move` 函数的作用就是将参数强制转换为右值，用于移动。

```cpp
bool IsEndNode() const { return is_end_; }
```

> `const` 表示类中的这个函数不能修改类，可以理解为只读属性。我们可以重载函数，当 `const Entity` 就会调用有 `const` 的，普通的 `Entity` 对象调用没用 `const` 的。如果我们想在 `const` 的方法中修改类的某个成员，需要把这个类成员标记为 `mutable` 。
>
> 优点在于安全，保证 `const Entity` 就一定是 `const` 的。

```cpp
std::unique_ptr<TrieNode> *InsertChildNode(char key_char, std::unique_ptr<TrieNode> &&child) {
    if (children_.count(key_char) > 0 || child->GetKeyChar() != key_char) {
      return nullptr;
    }
    children_[key_char] = std::move(child);
    return &children_[key_char];
}
```

> `std::unique_ptr<TrieNode>` 表示 `TrieNode` 类型的智能独占指针，所以返回的时候只能返回指向这个指针的指针，如果返回它，那么指针本身就被销毁了。
>
> `children_[key_char] = std::move(child);` 使用 `move` 函数来进行移动构造，`child` 作为一个右值引用，执行完这个语句就消亡了。独占指针，只有一份！！！

```cpp
TrieNodeWithValue(TrieNode &&trieNode, T value) : TrieNode(std::forward<TrieNode>(trieNode)) {
    value_ = value;
    is_end_ = true;
}
```

> `TrieNode(std::forward<TrieNode>(trieNode))` 是 `TrieNode` 的移动构造函数，上面写了。
>
> `std::forward<type>()` 和 `move` 的差不多，但是有区别，简单来说，遇到右值就转发右值并启动移动语义，遇到左值就转发左值启动复制语义。

### Insert 方法

```cpp
bool Insert(const std::string &key, T value) {
    const size_t key_size = key.size();
    if (key_size == 0) {
      return false;
    }
    latch_.WLock();
    auto curr = &root_; // unique_ptr 我们只能使用它的指针
    std::unique_ptr<TrieNode> *parent;
    for (size_t i = 0; i < key_size; i++) {
      // 如果没有这个字符，就插入这个字符
      // curr->get() 等价于　(*curr).get() 
      if (curr->get()->GetChildNode(key[i]) == nullptr) {
        curr->get()->InsertChildNode(key[i], std::make_unique<TrieNode>(key[i]));
      }
      parent = curr;
      curr = curr->get()->GetChildNode(key[i]);
    }
    if (curr->get()->IsEndNode()) {
      latch_.WUnlock();
      return false;
    }
    // **curr 就是 TrieNode，然后强转右值引用，构造 TrieNodeWithValue 
    // 并通过 make_unique 方法返回智能指针
    auto new_node = std::make_unique<TrieNodeWithValue<T>>(std::move(**curr), value);
    (*parent)->RemoveChildNode(key[key_size - 1]);
    // 这里插入的实际上是 TrieNodeWithValue
    (*parent)->InsertChildNode(key[key_size - 1], std::move(new_node)); 
    latch_.WUnlock();
    return true;
}
```

遍历 `key` 寻找路径，如果缺少了就插入就可。到了最后一个节点，如果是 `EndNode` 说明重复插入了，直接返回。否则，删除原来的 `node`，插入新的 `node`，插入的 `node` 实际上是 `TrieNodeWithValue<T>` 类型。

### Remove 方法

```cpp
bool RemoveHelper(std::unique_ptr<TrieNode> *curr, size_t i, const std::string &key, bool *success) {
    // 最后一个节点，SetEndNode(false)，success 设为 true 表示成功，返回这个 node 还有子节点或者是 EedNode 吗，这用来给父节点判断这个节点能不能删除
    if (i == key.size()) {
      *success = true;
      (*curr)->SetEndNode(false);
      return !(*curr)->HasChildren() && !(*curr)->IsEndNode();
    }
    // 路线走不通
    if ((*curr)->GetChildNode(key[i]) == nullptr) {
      *success = false;
      return false;
    }
    bool can_remove = RemoveHelper((*curr)->GetChildNode(key[i]), i + 1, key, success);
    if (!*success) {
      return false;
    }
    // 子节点可以删除，那么就删除子节点
    if (can_remove) {
      (*curr)->RemoveChildNode(key[i]);
    }
    return !(*curr)->HasChildren() && !(*curr)->IsEndNode();
  }
  bool Remove(const std::string &key) {
    if (key.empty()) {
      return false;
    }
    auto curr = &root_;
    bool success;
    latch_.WLock();
    RemoveHelper(curr, 0, key, &success);
    latch_.WUnlock();
    return success;
}
```

按照意思就是我们要递归的删除节点，既然需要递归，我们就要一个 `helper` 函数，当然了，直接写个栈充当函数栈也行。`success` 用来说明删除是否成功，而 `remove_helper` 函数的返回值用来告诉 `parent` 这个 `child` 是否可以 `remove`。

### GetValue 方法

```cpp
template <typename T>
  T GetValue(const std::string &key, bool *success) {
    latch_.RLock();
    auto curr = &root_;
    size_t key_size = key.size();
    for (size_t i = 0; i < key_size; i++) {
      // 路线走不通
      if ((*curr)->GetChildNode(key[i]) == nullptr) {
        *success = false;
        latch_.RUnlock();
        return T();
      }
      curr = (*curr)->GetChildNode(key[i]);
    }
    if (!(*curr)->IsEndNode()) {
      *success = false;
      latch_.RUnlock();
      return T();
    }
    // curr->get() 会得到一个指向 node 的普通指针，dynamic_cast 转 TrieNodeWithValue<T> 指针
    // 如果 T 不同也不能转成功哦
    // dynamic_cast 只支持下转上（继承关系），但是这里为什么能转成功呢？
    // 因为 curr->get() 指向的指针看起来是 TrieNode,但是因为是 EndNode 所以实际上是 TrieNodeWithValue
    // dynamic_cast 借助 RTTI 信息能检测出来，所以转换会成功
    auto tmp_node = dynamic_cast<TrieNodeWithValue<T> *>(curr->get());
    if (tmp_node != nullptr) {
      *success = true;
      latch_.RUnlock();
      return tmp_node->GetValue();
    }
    *success = false;
    latch_.RUnlock();
    return T();
}
```

### 结果

![image-20221022001511026](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221022001511026.png)

