---
title: WebServer高并发服务器代码详解
categories:
  - WebServer
tags:
  - WebServer
abbrlink: fa02fba7
date: 2023-03-28 22:22:59
---

### Buffer

`Buffer` 是我们使用 `vector` 容器封装的一个用来存储数据的 `char` 数组。数组中有两个指针，分别表示读写指针，两个指针之间的区域是有效数据。

```C++
class Buffer {
public:
  Buffer(int initBuffSize = 1024);
  ~Buffer() = default;
  void Init();
  // 将可读部分的数据转化为 string
  std::string AllToStr();
  // 从 fd 中读取数据，为了防止空间不够，使用分散读 readv
  ssize_t ReadFd(int fd, int *Errno);
  // 将 buffer_ read 到 write 中的数据写入 fd 中
  ssize_t WriteFd(int fd, int *Errno);
  // 向 fd 中写入 str 数组，长度为 size，空间不够需要扩容
  void Append(const char *str, size_t size);
  // 重载 Append
  void Append(std::string str);
  // 可读的区间大小
  size_t ReadableBytes() const { return write_pos_ - read_pos_; }
  // 可写的区间大小
  size_t WriteableBytes() const { return buffer_.size() - write_pos_; }
  char *BeginPtr() { return &*buffer_.begin(); }
  char *CurReadPtr() { return BeginPtr() + read_pos_; }
  char *CurWritePtr() { return BeginPtr() + write_pos_; }
  // 将 read_pos_ 移动到特定指针位置
  void AddReadPtr(char *end) { read_pos_ += end - CurReadPtr(); }
  // 讲 read_pos_ 移动指定大小
  void AddReadPtr(size_t size) { read_pos_ += size; }

private:
  std::vector<char> buffer_;
  std::atomic<size_t> read_pos_;
  std::atomic<size_t> write_pos_;
};
```

在 `ReadFd` 中使用了分散读技术，函数声明如下：

```C++
#include <sys/uio.h>
ssize_t readv(int fd, const struct iovec *iov, int iovcnt);
/* - fd 表示要读取的文件描述符
- struct iov 结构体有 iov_base 和 iov_len 两个成员，分别是 char *指针和长度
- iovcnt 为结构体数组 iov 的长度 
- 如下，从 fd 中读取数据写入 CurWritePtr() 和 buff
*/
iov[0].iov_base = CurWritePtr();
iov[0].iov_len = writeable;
iov[1].iov_base = buff;
iov[1].iov_len = sizeof(buff);
const ssize_t size = readv(fd, iov, 2);
```

这样可以保证一次性将 `fd` 的数据全部读取出来，如果有超出的部分暂存在 `buff` 中，后续调用 `Append` 写入，在 `Append` 中判断是否需要扩容。为了空间的有效利用，当 `write_pos_` 后的空间和 `read_pos_` 前的空间足够时，将当前内容向前平移。（更好的方法是使用循环数组，但是实现难度更大）

### Timer

对于每一个连接，需要一个计时器，在适当的时候将其断开，防止不活跃的连接占用大量的资源。我们使用小根堆，使用时间来排序。但是不能使用 `priority_queue` 容器来实现，因为我们需要知道每一个连接在计时器中的位置，从而在连接活跃时更新其时间。

对于每个连接，在计时器中使用如下的结构：

```C++
typedef Clock::time_point TimeStamp;
typedef std::function<void()> TimeoutCallBack;

struct TimerNode {
  int id;
  TimeStamp expires;
  TimeoutCallBack callback;
  bool operator<(const TimerNode &t) { return expires < t.expires; }
};
```

其中 `id` 是连接的唯一标识符，`expires` 是连接剩余的的时间，`callback` 为回调函数，在连接超时后调用，可以看到是 `std::function<void()>` 类型，代表一个函数对象，比如我经常使用的：

```C++
std::function<void()> dfs = [&]() { ... };
```

对于这个结构体，我们实现了 `<` 运算符，因此在后续实现中，我们使用小于运算来比较。

计时器的结构如下：

```C++
class TimerManager {
public:
  TimerManager() { heap_.reserve(64); };
  ~TimerManager() {
    heap_.clear();
    hash_.clear();
  }
  // 调整 id 的超时时间
  void Adjust(int id, int newExpires);
  // 添加一个连接，超时时间为 timeOut，回调函数为 cb，回调函数将在 Delete 时调用
  void Add(int id, int timeOut, const TimeoutCallBack &cb);
  // 调用回调函数后，删除
  void Work(int id);
  // 调用 Tick 将所有超时连接删除，返回值等于 0 表示没有删除干净
  int GetNextTick();

private:
  // 将所有超时连接删除
  void Tick();
  // 小根堆操作
  void Delete(size_t i);
  void SiftDown(size_t i);
  void SiftUp(size_t i);
  void SwapNode(size_t i, size_t j);

private:
  // 小根堆底层数据结构
  std::vector<TimerNode> heap_;
  // id 到 TimerNode 的映射，hash_[id] 等于 id 这个 Node 在 heap 中的下标
  std::unordered_map<int, size_t> hash_;
};
```

优先队列使用 `vector` 为底层数据结构。上移操作，对于节点 `i` ，其父节点 `j` 为 `(i - 1) / 2`，如果 `node_i` 小于 `node_j`，那么调用 `SwapNode(i, j)`，接着递归的对 `j` 调用 `SiftUp` 函数。下移操作同理，其子节点 `j` 为 `i * 2 + 1` 或者 `i * 2 + 2`，选其中较小的一个，然后如果 `node_j` 小于 `node_i`，那么调用 `SwapNode(i, j)`，接着递归的对 `j` 调用 `SiftDown` 函数。

交换时不能简单的调用 `std::swap`，同时还得修改 `hash_` 中 `key` 对应的 `value` 。

删除时，将 `i` 与最后一个元素交换，然后 `pop_back`，接着对 `i` 调用 `SiftUp` 和 `SiftDown` 函数。

计时器主要有如下几个方法。

`Add` 方法，添加一个 `Node` 在 `heap_` 最后，然后调用 `ShiftUp` 方法。`Adjust` 方法，通过 `hash` 找到对应的 `Node`，然后修改其时间，记得调用 `Sift` 方法调整位置。`Work` 方法，调用回调函数后，将 `Node` 删除。`GetNextTick` 方法，将堆顶所有已经超时的连接全部 `Delete`，返回值为 0 表示失败，大于 0 表示成功。

时间的比较方法如下：

```C++
typedef std::chrono::high_resolution_clock Clock;
typedef std::chrono::milliseconds MS;
std::chrono::duration_cast<MS>(node.expires - Clock::now()).count() <= 0
```

### Threadpool

`WebServer` 随时都会有连接，如果每个连接都临时的创建线程来处理，处理完成后又将线程销毁，对资源的占用较大，因此，我们使用线程池技术，在初始阶段就创建足够的线程，有任务了就选择线程来处理即可，没有任务时线程睡眠。

线程池的结构如下：

```C++
class ThreadPool {
public:
  explicit ThreadPool(size_t thread_count = 8);
  ThreadPool() = default;
  ThreadPool(ThreadPool &&) = default;
  ~ThreadPool();
  // 向进程池中添加任务
  template <class T> void AddTask(T &&task);

private:
  struct Pool {
    std::mutex mutex;
    std::condition_variable cond;
    bool close;
    std::queue<std::function<void()>> tasks;
  };
  std::shared_ptr<Pool> pool_;
};
```

对于一个线程池，我们有一个队列 `tasks` 存储任务，这样可以保证任务 `FIFO`。`mutex` 锁用来保证 `tasks` 的并发，防止多个线程处理同一个任务的情况。为了使得线程能够在没有任务时等待，我们这里要使用条件变量。`close` 用来标识线程池是否关闭。

对于构造函数如下，使用智能指针管理线程池 `pool_`：

```C++
ThreadPool::ThreadPool(size_t thread_count) : pool_(std::make_shared<Pool>()) {
  assert(thread_count > 0);
  for (size_t i = 0; i < thread_count; i++) {
    std::thread([pool = pool_] {
      std::unique_lock<std::mutex> locker(pool->mutex);
      while (true) {
        if (!pool->tasks.empty()) {
          auto task = std::move(pool->tasks.front());
          pool->tasks.pop();
          locker.unlock();
          task();
          locker.lock();
        } else if (pool->close)
          break;
        else
          pool->cond.wait(locker);
      }
    }).detach();
  }
}
```

循环创建线程，其中 `detach()` 将线程分离，使之在后台运行。线程是使用的 `Lambda` 匿名函数创建的。线程无限循环，当有任务时，取出任务，解锁后执行任务。如果没有任务，调用 `pool->cond.wait(locker)` 睡眠。

在析构时，需要先拿到 `mutex` 锁，然后将 `close` 设置为 `true`，接着调用 `pool_->cond.notify_all()` 将所有正在等在的线程都唤醒，这些线程都会 `break` 之后结束。而线程池使用智能指针，会自行销毁。

```C++
template <class F> void ThreadPool::AddTask(F &&task) {
  {
    std::lock_guard<std::mutex> locker(pool_->mutex);
    pool_->tasks.emplace(std::forward<F>(task));
  }
  pool_->cond.notify_one();
}
```

注意内部大括号的必要性，在 `pool_->cond.notify_one()` 之前释放锁。注意这里的右值转发，`pool_->tasks.emplace(std::forward<F>(task))` 和上面构造函数中的移动语义。

>   `std::lock_guard<std::mutex> locker(pool_->mutex)` 作用域锁，在 `lock_guard` 构造时，会对 `mutex` 加锁，在析构时，也就是离开 `lock_guard` 时会对 `mutex` 解锁。这样不仅仅是方便了代码编写，避免忘记解锁。同时也可以在函数出现异常退出时能及时解锁，避免死锁的产生。
>
>   `std::unique_lock<std::mutex> locker(pool->mutex)` 作用域锁，不过，我们可以视需求自行解锁，在析构时，如果已经解锁，就不会再解锁了。有时作用域太大，手动解锁更有利于性能。不过同等条件下，性能比 `lock_guard` 差，因为需要额外维护锁的状态。
>
>   `std::shared_lock<std::mutex> locker(pool->mutex)` 共享作用域锁，会调用 `mutex.lock_shared()` 获得共享锁。对于排他锁是阻塞的，但是可以和其他的共享锁同时使用，满足多线程读的需求。

### SqlconnRAII

对于一个 `MySQL` 的 `database`，会有很多个访问请求，因此，我们可以构造一个数据库访问的“线程池”。并不执行真正的访问，而是为多线程提供多个 “`MYSQL` 实例”。

```C++
class SqlConnPool {
public:
  static SqlConnPool *Instance(); // 返回一个 SqlConnPool 实例
  MYSQL *GetConn();
  void FreeConn(MYSQL *sql);
  int GetFreeConnCount();
  // 创建 connSize 个可以连接该特定数据库的 sql 实例
  void Init(const char *host, int port, const char *user, const char *pwd,
            const char *dbName, int connSize);
  void ClosePool();

private:
  SqlConnPool() = default;
  ~SqlConnPool() { ClosePool(); };

private:
  int MAX_CONN_{0};
  std::queue<MYSQL *> connn_queue_;
  std::mutex mutex_;
  sem_t sem_;
};
```

我们看到，其中主要的数据结构是队列，队列中的数据是 `MYSQL` 类型的指针（`MySQL` 句柄）。

在 `Init` 阶段，可以看到创建了多个相同（连接同一数据库）的 `sql` 加入了队列中。

```SQL
void SqlConnPool::Init(const char *host, int port, const char *user,
                       const char *pwd, const char *dbName, int connSize = 10) {
  assert(connSize > 0);
  for (int i = 0; i < connSize; i++) {
    MYSQL *sql = nullptr;
    sql = mysql_init(sql); // mysql_init MYSQL 类型的指针
    assert(sql);
    sql = mysql_real_connect(sql, host, user, pwd, dbName, port, nullptr, 0); // 实例化
    assert(sql);
    connn_queue_.push(sql);
  }
  MAX_CONN_ = connSize;
  sem_init(&sem_, 0, MAX_CONN_);
}
```

在  `GetConn` 中，返回一个 `sql` ，用于数据库连接；在 `FreeConn` 中，释放一个 `sql` 回队列中。我们可以看到在 `Get` 中先调用 `sem_wait(&sem_)` 然后再加锁。这里信号量用来控制最多 `push` 多少个 `sql` 出去，而锁用来控制 `queue` 的并发。信号量用来控制连接的次数，在线程池中我们用的是条件变量。

```C++
MYSQL *SqlConnPool::GetConn() {
  MYSQL *sql = nullptr;
  if (connn_queue_.empty())
    return nullptr;
  sem_wait(&sem_);
  std::lock_guard<std::mutex> locker(mutex_);
  sql = connn_queue_.front();
  connn_queue_.pop();
  return sql;
}

void SqlConnPool::FreeConn(MYSQL *sql) {
  assert(sql);
  std::lock_guard<std::mutex> locker(mutex_);
  connn_queue_.push(sql);
  sem_post(&sem_);
}
```

我们发现，每次调用 `GetConn` 都需要调用 `FreeConn`，为了让生活更美好，可以使用 `RAII` 特性，资源在对象构造时初始化，在对象析构时释放，这样可以避免忘记释放。我们看到类中的成员 `sql` 是一个指针，当指针指向的元素被释放了， `sql` 指向 `nullptr`，析构函数将不再调用 `FreeConn`。这种实现原理和 `unique_lock` 很相似。

```Java
class SqlConnRAII {
public:
  SqlConnRAII(MYSQL **sql, SqlConnPool *connpool) {
    assert(connpool);
    *sql = connpool->GetConn();
    sql_ = *sql;
    connpool_ = connpool;
  }
  ~SqlConnRAII() {
    if (sql_) {
      connpool_->FreeConn(sql_);
    }
  }

private:
  MYSQL *sql_;
  SqlConnPool *connpool_;
};
```

### Epoller

封装了 `IO` 多路复用技术 `epoll` 的一些 `API`，实现如下：

```C++
class Epoller {
public:
  // 调用 epoll_create 对 epollfd_ 初始化，并 resize(events_) 的大小为 1024
  Epoller(int maxEvent = 1024) : epollfd_(epoll_create(8)), events_(maxEvent) {};
  // 析构函数，close(epollfd_)
  ~Epoller();
  // 将 fd 加入 epoll 的监控，监控类型为 events
  bool AddFd(int fd, u_int32_t events);
  // 将 fd 的监控类型修改为 events
  bool ModFd(int fd, u_int32_t events);
  // 将 fd 移除 epoll 的监控
  bool DelFd(int fd);
  // 检测所有的文件描述符，返回发生变化的文件描述符的数量，默认为非阻塞
  int Wait(int timeoutMs = -1);
  // 返回第 i 个 event 的 fd 和 events
  int GetEventFd(size_t i) const;
  u_int32_t GetEvents(size_t i) const;

private:
  int epollfd_;
  std::vector<struct epoll_event> events_;
};

int epoll_ctl(epollfd_, EPOLL_CTL_DEL, fd, &ev);
int epoll_wait(epollfd_, &events_[0], static_cast<int>(events_.size()), timeoutMs);
```

操作函数都是调用 `epoll_ctl()` 执行，而 `Wait()` 函数调用的是 `epoll_wait()`，返回发生变化的文件描述符的个数，并将结果依次存储在 `events_` 中。`timeoutMs` 表示阻塞时间，0 表示不阻塞，-1 表示阻塞，直到 `fd` 发生变化，解除阻塞，大于 0 的数表示阻塞的时长，单位为毫秒。

### MYSQL 库常见函数

首先，需要安装 `mysql` 库才能使用。执行命令 `sudo apt-get install libmysqlclient-dev`

>   `MYSQL sql` 创建数据库句柄
>
>   `sql = mysql_init(&sql)` 初始化句柄
>
>   `sql = mysql_real_connect(&sql, "host", "user", "pwd", "db", port, nullptr, 0)` 连接到数据库
>
>   `mysql_real_query(&sql, buf, strlen(buf))` ：sql 这个句柄查询（执行）buf 这条 sql 语句。
>
>   `MYSQL_RES * res = mysql_store_result(&sql)` 装载结果到 res 中
>
>   `MYSQL_ROW row = mysql_fetch_row(res)` 取出结果集中的内容，返回结果为一个“数组”
>
>   `mysql_free_result(res)` 释放结果集
>
>   `mysql_close(&sql)` 关闭数据库连接

### HTTPrequest

处理 `http` 请求，主要为解析 `HTTP` 请求报文，包括请求方法、请求路径、`HTTP` 版本、请求体等。如果是 `POST` 请求，还需要处理 `sql` 查询。

```c++
class HTTPRequest {
public:
  HTTPRequest() { state_ = REQUEST_LINE; }
  ~HTTPRequest() = default;
  void Init();
  bool Parse(Buffer &buffer);
  std::string &Path() { return path_; };
  std::string Method() { return method_; };
  std::string Version() { return version_; };
  std::string GetPost(const std::string &key);
  std::string GetPost(const char *key);
  bool IsKeepAlive() const;
private:
  bool ParseRequestLine(const std::string &line);
  void ParseHeader(const std::string &line);
  void ParseBody(const std::string &line);
  void ParsePath();
  void ParsePost();
  void ParseFromUrlencoded();
  static bool UserVerify(const std::string &name, const std::string &pwd, bool isLogin);
  static int ConverHex(char ch);

  PARSE_STATE state_;                          // 处理的阶段
  std::string method_, path_, version_, body_; // 请求方法、路径、版本和请求体
  std::unordered_map<std::string, std::string> header_; // header kv 对
  std::unordered_map<std::string, std::string> post_;   // post 请求的 kv 对
  static const std::unordered_set<std::string> DEFAULT_HTML;
  static const std::unordered_map<std::string, int> DEFAULT_HTML_TAG;
};
```

我们可以看到，最主要的工作就是 `Parse()` 函数，也就是解析 `HTTP` 请求。要想知道怎么解析，需要知道 `HTTP` 请求报文的格式，如下：

```http
POST /login HTTP/1.1
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: max-age=0
Content-Length: 33
Content-Type: application/x-www-form-urlencoded
Host: ceyewan.top:8888
Origin: http://ceyewan.top:8888
Proxy-Connection: keep-alive
Referer: http://ceyewan.top:8888/login
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36
x-forwarded-for: 8.8.8.8

username=%E5%86%8C+yewan&password=ceyewan // 其中 username = 册 yewan
```

第一行为请求方法、请求路径和 `HTTP` 版本，之后的这些行全部都是 `Headers`，以键值对的形式排列。注意，`Proxy-Connection: keep-alive` 表示这是一个需要保持 `alive` 的连接。对于 `body` 字段，形式为 `key=value&key=value` ，但是如果存在中文就会被转化为 `%xx`，如果存在空格就会转化为 `+` 号。

那么，我们来看 `Parse` 方法：

```c++
bool HTTPRequest::Parse(Buffer &buffer) {
  const char *CRLF = "\r\n"; // 换行符
  while (state_ != FINISH) {
    // 找到换行符，然后将这之间的字符转化为 string
    char *lineEnd = std::search(buffer.CurReadPtr(), buffer.CurWritePtr(), CRLF, CRLF + 2);
    std::string line(buffer.CurReadPtr(), lineEnd);
    switch (state_) {
    case REQUEST_LINE:
      ParseRequestLine(line);
      ParsePath();
      break;
    case HEADERS:
      ParseHeader(line);
      break;
    case BODY:
      ParseBody(line);
      break;
    default:
      break;
    }
    buffer.AddReadPtr(lineEnd + 2);
  }
  return true;
}
```

我们将解析拆分为 4 个阶段，`REQUEST_LINE` 请求行、`HEADER` 请求头、`BODY` 请求体、`FINISH` 结束。对于请求行和请求体格式固定，我们使用正则表达式来解决，如下：

```c++
bool HTTPRequest::ParseRequestLine(const std::string &line) {
  std::regex patten("^([^ ]*) ([^ ]*) HTTP/([^ ]*)$");
  std::smatch subMatch;
  if (regex_match(line, subMatch, patten)) {
    method_ = subMatch[1];
    path_ = subMatch[2];
    version_ = subMatch[3];
    state_ = HEADERS;
    return true;
  }
  return false;
}
```

>    `^` 匹配字符串的开始位置，`[^ ]` 表示不匹配中括号中的空格，`*` 表示匹配前面的子表达式零次或者多次，`$` 表示匹配字符串的结尾位置。
>
>    因此，该正则表达式的含义是 `xxx xxx HTTP/xxx` 分别是请求方法、路径和版本号。

然后我们还要处理路径，如 `/` 处理成 `index.html`；默认的几个分类，如上面的 `login` 处理成 `login.html`。

对于 `HEADER` 同样也是正则表达式匹配，但是 `HEADER` 具有多行，因此只有当不匹配时才将状态切换为 `BODY`。接下来解析 `BODY`，然后将状态切换为 `FINISH`。

接下来，在解析 `BODY` 成功后，我们需要视路径情况（注册还是登录），来调用 `UserVerify(post_["username"], post_["password"], isLogin)` 来查询数据库。分两种情况，一种是注册，执行 `INSERT` 语句；一种是登录，执行 `SELECT` 语句。对于结果，如果成功则返回 `welcome` 页面，如果失败，则返回 `error` 页面。

```c++
bool HTTPRequest::UserVerify(const std::string &name, const std::string &pwd,
                             bool is_login) {
  if (name == "" || pwd == "")	return false;
  MYSQL *sql;
  SqlConnRAII sqlconn(&sql, SqlConnPool::Instance());
  assert(sql);
  char order[256] = {0};
  MYSQL_RES *res = nullptr;
  snprintf(order, 256, "SELECT username, password FROM user WHERE username='%s' LIMIT 1", name.c_str());
  if (mysql_query(sql, order)) {
    return false;
  }
  res = mysql_store_result(sql);
  while (MYSQL_ROW row = mysql_fetch_row(res)) {
    std::string password(row[1]);
    if (is_login && pwd == password) {
      return true;
    } else if (is_login && pwd != password) {
      return false;
    } else if (!is_login) {
      return false;
    }
  }
  if (!is_login) {
    mysql_free_result(res);
    bzero(order, 256);
    snprintf(order, 256, "INSERT INTO user(username, password) VALUES('%s','%s')",
           name.c_str(), pwd.c_str());
    if (mysql_query(sql, order)) {
      mysql_free_result(res);
      return false;
    }
    return true;
  }
  return false;
}
```

对于 `POST` 请求，我们先在数据库中查找 `user` 是否存在，如果存在那么就对比输入的 `password` 是否匹配，如果不匹配，那么就需要返回 `false`，如果匹配且为登录请求，自然可以返回 `true`。如果不存在，那么我们先判断不是登录，那么就是注册，执行 `INSERT` 命令。按照这种处理逻辑，可以保证数据库中的用户名是互不相同的。 

>   隐患：对于目前这种处理逻辑，是有 SQL 注入的风险的，比如用户名中有 `'` 等符号。

还有一个小方法，`IsKeepAlive()`，如果 `header` 中有 `keep-alive` 这个字段，就返回 `true`。

### HTTPresponse

向 `HTTP` 请求发送响应，分为响应头和响应体（文件）。主要结构如下：

```cpp
class HTTPResponse {
public:
  HTTPResponse();
  ~HTTPResponse();

  void Init(const std::string &srcDir, std::string &path,
            bool isKeepAlive = false, int code = -1);
  // 调用 stat() 判断 path 文件类型，如果不存在或者是
  void MakeResponse(Buffer &buff);
  void UnmapFile(){ munmap(file_, file_stat_.st_size); };
  char *File();
  size_t FileLen() const;
  void ErrorContent(Buffer &buff, std::string message);
  int Code() const { return code_; }

private:
  void AddStateLine(Buffer &buff);
  void AddHeader(Buffer &buff);
  void AddContent(Buffer &buff);
  void ErrorHtml();
  std::string GetFileType();

  int code_;
  bool isKeepAlive_;
  std::string path_;
  std::string srcDir_;
  char *mmFile_;
  struct stat mmFileStat_;
  static const std::unordered_map<std::string, std::string> SUFFIX_TYPE;
  static const std::unordered_map<int, std::string> CODE_STATUS;
  static const std::unordered_map<int, std::string> CODE_PATH;
};
```

首先，我们需要知道响应的结构：

```
HTTP/1.1 200 OK
Content-Length: 3148
Connection: keep-alive
Content-Type: text/html
Keep-Alive: timeout=4
Proxy-Connection: keep-alive
```

在代码实现上，我们最重要的一个函数是 `MakeResponse(Buffer &buffer)`。

首先，通过 `int stat(const char *restrict path, struct stat *restrict buf)` 调用，将 path 的文件信息存储在结构体 buf 中，struct stat 中有一个重要的成员 st_mode 表示文件的类型，如果调用失败，或者 path 是一个文件夹而不是文件，将响应码设为 404。如果是其他用户的文件，则设置 code_=403 。

```c++
if (stat((src_dir_ + path_).c_str(), &file_stat_) < 0 || S_ISDIR(file_stat_.st_mode)) {
  code_ = 404;
}
```

 接下来，依次调用

 `ErrorHtml()` 在 `code_` 为错误码时，将 `path_` 设置为 `error.html` 的地址。

`AddStateLine(buffer)` 设置响应头。

`AddHeader(buffer)` 在添加 `Content-Type: text/html` 时，需要先通过文件的后缀判断文件的类型，再来设置这个字段的值。

```c++
std::string::size_type idx = path_.find_last_of('.'); // 找到最后一个 .
  if (idx == std::string::npos) {
    return "text/plain"; // 没有后缀
  }
  std::string suffix = path_.substr(idx); 
// 如 .html，然后通过既定哈希表得到文件类型
```

`AddContent(buffer)` 调用 `mmap()` 函数，将文件映射到程序的内存空间，然后通过 `stat.st_size()` 得到文件的长度。这样，就拥有了文件的起始地址(`mmap` 的返回值)和文件的长度。然后，还需要再在响应头中添加 `Content-Length: 3148` 字段。

```c++
int srcFd = open((src_dir_ + path_).data(), O_RDONLY);
file_ = mmap(0, file_stat_.st_size, PROT_READ, MAP_PRIVATE, srcFd, 0);
```

### HTTPConn

对于一个 `http` 连接，由 `httpconn` 全权负责，具体结构如下：

```c++
class HttpConn {
public:
  HttpConn();
  ~HttpConn();
  void init(int sockFd, const sockaddr_in &addr);
  ssize_t read(int *saveErrno);
  ssize_t write(int *saveErrno);
  void Close();
  int GetFd() const;
  int GetPort() const;
  const char *GetIP() const;
  sockaddr_in GetAddr() const;
  bool process();
  int ToWriteBytes() { return iov_[0].iov_len + iov_[1].iov_len; }
  bool IsKeepAlive() const { return request_.IsKeepAlive(); }
  static bool isET;
  static const char *srcDir;
  static std::atomic<int> userCount;

private:
  int fd_;					// socket 文件描述符
  struct sockaddr_in addr_;	// 连接方的 addr
  bool isClose_;			// 是否关闭连接
  int iovCnt_;				// 有效的 iov 的数量
  struct iovec iov_[2];		// 聚合写的辅助结构
  Buffer readBuff_;  		// 读缓冲区
  Buffer writeBuff_; 		// 写缓冲区
  HTTPRequest request_; 	// 请求
  HTTPResponse response_; 	// 响应
};
```

对于一个 `http` 连接，处理流程为：

1.   调用 `read()` 将数据全部读取到 `read_buffer_` 中。

```c++
// 伪代码，需要对 len 来做一些判断
do {
  len = readBuff_.ReadFd(fd_, saveErrno);
} while (isET);
```

2.   调用 `process()` 处理数据。首先调用 `request_.Init()` 然后调用 `request_.Parse()` 解析请求，解析成功，拿到请求的资源路径等信息后调用 `response_.Init()`，接着调用 `response_.MakeResponse()` 将响应写入到 `write_buffer_` 中，然后构造聚合写的辅助结构 `iov`_，其中 `iov_[0]` 为 `write_buffer_.CurReadPtr()` ，`iov_[1]` 为 `response_.File()` 文件的地址。
3.   调用 `write()` 将数据写入文件描述符中。

```c++
do {
  len = writev(fd_, iov_, iovCnt_);
} while (isET || ToWriteBytes() > 10240);
```

>   `socket` 上的读写状态为 可读、不可读、可写、不可写。有数据就可读、没有数据就不可读、有空间就可写、没有空间就不可写。
>
>   ET 模式：边缘触发模式，只有一个事件从无到有才会触发。对于读事件 `EPOLLIN`，只有 `socket` 上的数据从无到有，`EPOLLIN` 才会触发；对于写事件 `EPOLLOUT`，只有在 `socket` 写缓冲区从不可写变为可写，`EPOLLOUT` 才会触发。
>
>   LT 模式：水平触发模式，一个事件只要有，就会一直触发。对于读事件 `EPOLLIN`，只要 `socket` 上有未读完的数据，`EPOLLIN` 就会一直触发；对于写事件 `EPOLLOUT`，只要 `socket` 可写（TCP 窗口一直不饱和/TCP 缓冲区未满时），`EPOLLOUT` 就会一直触发。

这就解释了，为何我们需要一个循环来调用 `read` 或者 `write`，当 `socket` 套接字中有可读时，ET 模式通知我们，这时，我们读取了数据（可能后续 `socket` 中还有数据继续来，却不会通知了），所以需要一个循环，确保读干净了。写同理，由于只通知一次，所以需要循环写，全部写完。

### WebServer

结构如下：

```c++
class WebServer {
public:
  WebServer(int port, int trigMode, int timeoutMS, bool OptLinger, int sqlPort,
            const char *sqlUser, const char *sqlPwd, const char *dbName,
            int connPoolNum, int threadNum);

  ~WebServer();
  void Start();

private:
  bool InitSocket();
  void InitEventMode(int trigMode);
  void AddClient(int fd, sockaddr_in addr);

  void DealListen();
  void DealWrite(HTTPConn *client);
  void DealRead(HTTPConn *client);

  void SendError(int fd, const char *info);
  void ExtentTime(HTTPConn *client);
  void CloseConn(HTTPConn *client);

  void OnRead(HTTPConn *client);
  void OnWrite(HTTPConn *client);
  void OnProcess(HTTPConn *client);

  static const int MAX_FD = 65536;

  static int SetFdNonblock(int fd);

  int port_;
  bool openLinger_;
  int timeoutMS_; /* 毫秒MS */
  bool isClose_;
  int listenFd_;
  char *srcDir_;

  uint32_t listenEvent_;
  uint32_t connEvent_;

  std::unique_ptr<TimerManager> timer_;
  std::unique_ptr<ThreadPool> threadpool_;
  std::unique_ptr<Epoller> epoller_;
  std::unordered_map<int, HTTPConn> users_;
};
```

对于构造函数，结构如下，依次为监听的端口、ET 模式、TimeoutMS、 优雅退出、MySQL 的配置、sql 的连接数量、和线程池数量。

```c++
WebServer::WebServer(int port, int trigMode, int timeoutMS, bool OptLinger,
                     int sqlPort, const char *sqlUser, const char *sqlPwd,
                     const char *dbName, int connPoolNum, int threadNum)
    : port_(port), openLinger_(OptLinger), timeoutMS_(timeoutMS),
      isClose_(false), timer_(new TimerManager()),
      threadpool_(new ThreadPool(threadNum)), epoller_(new Epoller()) {
  srcDir_ = getcwd(nullptr, 256);
  assert(srcDir_);
  strncat(srcDir_, "/resources/", 16);
  HTTPConn::userCount = 0;
  HTTPConn::srcDir = srcDir_;
  SqlConnPool::Instance()->Init("localhost", sqlPort, sqlUser, sqlPwd, dbName,
                                connPoolNum);
  InitEventMode(trigMode);
  if (!InitSocket()) {
    isClose_ = true;
  }
}
```

首先，需要初始化我们的模式。`InitEventMode(trigMode)` 中 `listenEvent` 和 `connEvent` 的初始模式分别为 `EPOLLRDHUP` 和 `EPOLLONESHOT | EPOLLRDHUP`。如果 `trigMode` 的最低位为 1 那么 `listenEvent |= EPOLLET`，如果 `trigMode` 的次低位为 1 那么 `connEvent |= EPOLLET`。默认参数为 3，也即都是 ET 模式。

>   `EPOLLONESHOT`：表示 `epoll` 只监听一次事件，当某个 `socket` 上有事件触发时，`epoll` 会把该 `socket` 的文件描述符加入到就绪队列中。事件只触发一次，如果想要继续监听该 `socket`，需要在下次 `epoll_wait()` 返回时再次添加该 `socket`。
>
>   `EPOLLRDHUP`：表示 TCP 连接被远程端关闭或者发送了 RST 信号，`epoll` 将会监听到 `EPOLLIN` 事件和 `EPOLLRDHUP` 事件，应用程序可以读取已经接收到的数据，但是不能再往该连接中写入数据。(否则只监听到 EPOLLIN 事件会误认为有请求到来)

在 `InitSocket()` 中，创建了 `socket` 套接字后，调用了 `setsockopt()` 设置套接字的属性，最后，调用 `SetFdNonblock(fd)`  来调用`fcntl(fd, F_SETFL, fcntl(fd, F_GETFD, 0) | O_NONBLOCK);` 将套接字设置为非阻塞的。（阻塞读时，没有数据会一直等待，有数据时，有多少读多少；非阻塞读时，如果没有数据直接返回，有数据也是有多少就读多少，并不会在等待，因此，判断读到数据长度来决定是否还要再继续读。阻塞写会一直阻塞到写完，非阻塞写采用能写多少就写多少）

```c++
int setsockopt(int sockfd , int level, int optname, void *optval, socklen_t *optlen);
/* -sockfd 指定一个 socket 文件描述符
   -level 协议层，SOL_SOCKET：通用套接字代码，IPPRO_TCP：TCP 协议
   - optname 指定要设置的选项的名称
   - optval 指定包含选项值的缓冲区
   - optlen 值得缓冲区的长度*/
optLinger.l_onoff = 1; // 是否启用SO_LINGER选项的布尔值
optLinger.l_linger = 1; // 指示内核等待的时间，以秒为单位
setsockopt(listenFd_, SOL_SOCKET, SO_LINGER, &optLinger, sizeof(optLinger));
/* SO_LINGER：延迟关闭连接，指定在关闭 TCP 套接字时
   内核应该等待多长时间来发送剩余数据并尝试完成传输 */
int optval = 1;
setsockopt(listenFd_, SOL_SOCKET, SO_REUSEADDR, (const void *)&optval,
                   sizeof(int));
/* SO_REUSEADDR：允许在使用 bind 函数绑定端口之前重新使用处于 TIME_WAIT 状态的端口，端口释放就可以再次使用 */
```

对于 `Start` 函数，是服务器的主线程，流程如下：

```c++
void WebServer::Start() {
  int timeMS = -1; /* epoll wait timeout == -1 无事件将阻塞 */
  while (!isClose_) {
    // 每一轮，释放超时的连接
    if (timeoutMS_ > 0) {
      timeMS = timer_->GetNextTick();
    }
    int eventCnt = epoller_->Wait(timeMS);
    for (int i = 0; i < eventCnt; i++) {
      int fd = epoller_->GetEventFd(i);
      uint32_t events = epoller_->GetEvents(i);
      if (fd == listenFd_) {
        // 调用 accept 后调用 epoll->AddFd 和 timer->Add，最后 SetFdNonblock(fd)
        DealListen();
      } else if (events & (EPOLLRDHUP | EPOLLHUP | EPOLLERR)) {
        assert(users_.count(fd) > 0);
        // 调用 epoller_->DelFd(client->GetFd()) 和 client->Close()
        CloseConn(&users_[fd]);
      } else if (events & EPOLLIN) {
        assert(users_.count(fd) > 0);
        // 读数据，调整超时时间、client->Read 读数据，client->Process 处理数据，如果处理成则调用 ModFd，添加监听 EPOLLOUT 事件；处理失败则调用 ModFd 添加监听 EPOLLIN。将这个过程封装为函数，添加进线程池任务列表。
        DealRead(&users_[fd]);
      } else if (events & EPOLLOUT) {
        assert(users_.count(fd) > 0);
        // 调用 client->Write()，如果 keepAlive 则调用继续 client->Process 处理数据，最后关闭连接。将这个过程封装为函数，添加进线程池任务列表。
        DealWrite(&users_[fd]);
      }
    }
  }
}
```

向线程池中添加任务：

```c++
// 第一个参数是函数指针，然后是参数列表
// 用占位符就可以保留参数，设好参数就可以不用参数了
// 这里没有占位符，这样就保证了可以匹配 AddTask 没有参数的要求
threadpool_->AddTask(std::bind(&WebServer::OnRead, this, client));
// 对于回调函数同样如此，满足 std::function<void()>
timer_->Add(fd, timeoutMS_, std::bind(&WebServer::CloseConn, this, &users_[fd]))
1. bind 绑定普通函数
int add(int x, int y) { return x + y; }

int main() {
    std::cout << "add(1, 2) = " << add(1, 2) << std::endl;
    auto func = std::bind(add, 1, std::placeholders::_1);
    std::cout << "func(1, 2) = " << func(2) << std::endl;
    return 0;
}
2. bind 绑定类的成员函数
class Cul {
public:
    int add(int x, int y) { return x + y; }
    int func() {
        auto func = std::bind(&Cul::add, this, 1, 2);
        return func();
    }
};

int main() {
    Cul c;
    std::cout << "add(1, 2) = " << c.add(1, 2) << std::endl;

    std::cout << "func(1, 2) = " << c.func() << std::endl;
    return 0;
}
```

### webbench

编译安装后，测试一下：

```shell
wget http://home.tiscali.cz/~cz210552/distfiles/webbench-1.5.tar.gz
tar zxvf webbench-1.5.tar.gz
cd webbench-1.5
make
make install
```

![image-20230328221227156](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20230328221227156.png)