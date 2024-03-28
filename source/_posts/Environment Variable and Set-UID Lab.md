---
title: Environment-Variable-and-Set-UID-Lab
categories:
  - SeedLabs/SoftwareSecurity
tags:
  - 
abbrlink: f9a30b6b
date: 2022-11-05 01:54:28
---

## Manipulating Environment Variables

我们可以使用 `printenv` 或者 `env` 这两个命令查看环境变量，也可以使用 `printenv xxx` 或者 `env | grep xxx` 查看特定的环境变量。

我们也能使用 `export` 或者 `unset` 这两个命令来设置或者 `unset` 环境变量。

## Passing Environment Variables from Parent Process to Child Process

我们编写程序如下：

```c
// filename : myprintenv.c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

extern char **environ;

void printenv() {
    int i = 0;
    while (environ[i] != NULL) {
        printf("%s\n", environ[i]);
        i++;
    }
}

void main() {
    pid_t childPid;
    switch (childPid = fork()) {
        case 0: /* child process */
            // printenv();
            exit(0);
        default: /* parent process */
            printenv();
            exit(0);
    }
}
```

编译后使用 `./a.out > parent.txt` 将父进程的环境变量保存到文件中，修改代码输出子进程的环境变量，编译后执行 `./a.out > child.txt` 命令，最后使用 `diff child.txt parent.txt` 比较两个文件，没有输出信息，说明父子进程的环境变量完全相同，子进程完全继承父进程的环境变量。

![image-20221104235053444](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221104235053444.png)

##  Environment Variables and execve()

编写程序如下：

```c
// filename : myenv.c
#include <unistd.h>

extern char **environ;

int main() {
    char *argv[2];

    argv[0] = "/usr/bin/env";
    argv[1] = NULL;

    // execve("/usr/bin/env", argv, environ);
	execve("/usr/bin/env", argv, NULL);
    return 0;
}
```

这里使用了 `execve` 系统调用执行了 `env` 命令，编译执行后没有输出；我们将第三个参数修改为 `environ` 再次编译执行，输出了环境变量。

![image-20221104235644117](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221104235644117.png)

这说明了 `execve` 系统调用可以通过第三个参数来指定是否继承父进程的环境变量。并且 `execve` 永不返回。

## Environment Variables and system()

```c
#include <stdio.h>
#include <stdlib.h>
int main() {
    system("/usr/bin/env");
    return 0;
}
```

编译执行之，可以看到它输出了环境变量，也就是说 `system` 环境变量默认继承环境变量。`system()` 会调用 `fork()` 产生子进程，由子进程来调用 `/bin/sh-c string` 来执行参数 `string` 字符串所代表的命令，此命令执行完后随即返回原调用的进程。

## Environment Variable and Set-UID Programs

我们编写一个打印当前进程环境变量的程序，并修改之为 `Set-UID` 程序，

```c
#include <stdio.h>
#include <stdlib.h>
extern char **environ;

void main() {
    int i = 0;
    while (environ[i] != NULL) {
        printf("%s\n", environ[i]);
        i++;
    }
}
```

![image-20221105000937101](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221105000937101.png)

其中 `4755` 中的 4 就是说明它是一个特权程序。

然后，我们在环境变量中添加一条自定义的数据，`export MY_NAME=ceyewan` 然后执行特权程序：

![image-20221105001337944](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221105001337944.png)

结果如上，这说明特权程序会使用当前用户的环境变量，那么这也就意味着给了用户使坏的机会。

##  The PATH Environment Variable and Set-UID Programs

```c
#include <stdlib.h>
int main() { system("ls"); }
```

我们看上面这个小程序，其实就是执行 `ls` 命令，我们将这个程序设为一个特权程序，然后呢？

随便写一个小代码，比如我写的就这一行 `printf("I am the bad ls!\n");` 并将其编译为一个叫做 `ls` 的可执行文件。最后我们使用 `export PATH=$pwd:$PATH` 将当前目录加入到环境目录中。

这个时候，我们执行上面这个代码，它调用的 `ls` 会是哪个？实验一下看看就知道了。主要就是因为这里使用的**不是绝对路径**，并且还是 `system` 这种**直接继承环境变量的不安全的系统调用**。导致查找的时候先查找到了我们写的恶意程序。

![image-20221105003828483](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221105003828483.png)

> 在 `Ubuntu` 中 `system(cmd)` 会调用 `/bin/sh` 来执行 `cmd`，而 `/bin/sh` 有防御机制，导致实验不成功。可以使用 `sudo ln -sf /bin/zsh /bin/sh` 将 `sh` 链接到 `zsh` 上，而 `zsh` 是不安全的。 

## The LD_PRELOAD Environment Variable and Set-UID Programs

首先我们写一个 `sleep` 恶意代码，

```c
#include <stdio.h>
void sleep(int t) { printf("I am the bad sleeping\n"); }
```

并将其编译为一个动态链接库，最后，将我们的链接库加入到 `LD_PRELOAD` 中，`preload` 优先加载的意思嘛。

编写代码如下：

```c
#include <unistd.h>
int main() { sleep(1); }
```

编译执行后的结果竟然是：

![image-20221105010124705](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221105010124705.png)

我们可以看到，普通程序和特权程序相同的代码居然执行结果是不同的，为什么呢？我也不知道。不过肯定是可以知道的，将代码修改为输出环境变量，就可以看到**特权程序没有这个环境变量**。

![image-20221105010720561](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221105010720561.png)

## Invoking External Programs Using system() versus execve()

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char *argv[]) {
    char *v[3];
    char *command;
    if (argc < 2) {
        printf("Please type a file name.\n");
        return 1;
    }
    v[0] = "/bin/cat";
    v[1] = argv[1];
    v[2] = NULL;
    command = malloc(strlen(v[0]) + strlen(v[1]) + 2);
    sprintf(command, "%s %s", v[0], v[1]);
    // Use only one of the followings.
    system(command);
    // execve(v[0], v, NULL);
    return 0;
}
```

比如系统提供一个如上逻辑的特权程序给我们，保证我们只有查看的权限，没有执行权限。但是能搞乱的吗？

能的，比如我们传参为 `filename && rm filename`，或者为 `filename && xxx filename` 然后 `xxx` 是我们写的恶意代码，并且将路径加入到 `PATH` 中。

![image-20221105012801367](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221105012801367.png)

强制删除文件并且不抛出提醒，删的了无痕迹。但是 `execve` 就不行了，规定了第一个参数是命令，第二个参数是参数列表，第三个参数是环境变量。所以说，短的方便但是危险。

## Capability Leaking

```bash
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void main() {
    int fd;
    char *v[2];

    /* Assume that root.txt is an important system file,
     * and it is owned by root with permission 0644.
     * Before running this program, you should create
     * the file root.txt first. */
    fd = open("root.txt", O_RDWR | O_APPEND);
    if (fd == -1) {
        printf("Cannot open root.txt\n");
        exit(0);
    }

    // Print out the file descriptor value
    printf("fd is %d\n", fd);

    // Permanently disable the privilege by making the
    // effective uid the same as the real uid
    setuid(getuid());

    // Execute /bin/sh
    v[0] = "/bin/sh";
    v[1] = 0;
    execve(v[0], v, 0);
}
```

我们看代码，特权程序打开了文件后，主动调用了 `setuid(getuid())` 放弃了自己的特权，并进入了 `/bin/sh`，但是，真的放弃了吗？我们执行看看。

![image-20221105014621221](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20221105014621221.png)

我们可以看到，在 `sh` 中确实放弃了权限，无法执行 `echo bbbbb > root.txt`，但是，我们忘记关闭文件了，对文件描述符来说我们还是有写的权限，因此可以执行 `echo bbbbb >& 3` 向文件描述符中写入。

> 为了遵循最小特权原则，如果不再需要这些特权，`Set-UID` 程序通常会永久地放弃其根本特权。此外，有时程序需要将其控制移交给用户；在这种情况下，必须撤销根特权。可以使用 `setuid()` 系统调用来撤销特权。
>
> 当取消特权时，常见的错误之一是能力泄漏。当进程仍然处于特权状态时，可能已经获得了一些特权功能； 当特权被降级时，如果程序不清理这些功能，它们仍然可以被非特权进程访问。换句话说，虽然进程的有效 用户 `ID` 变得非特权，但进程仍然具有特权，因为它具有特权功能。

