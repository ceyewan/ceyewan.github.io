## 两套 Git 账号配置

最近在公司实习，需要配置一套公司 Repo 的 Git 配置，但是平时自己也摸点鱼，干点自己的活，需要把代码提交到自己的 Github 上，因此搞出来这份教程，总体思路如下：

1. **文件结构**：我们将创建两个主目录，例如 `~/dev/work` 用于存放公司项目，`~/dev/personal` 用于存放个人项目。
2. **SSH Keys**：为公司和个人账户分别生成一对独立的 SSH Key。
3. **SSH Config**：配置 SSH (`~/.ssh/config`)，使其能根据你访问的远程仓库地址（我们会创建别名）自动选择正确的 SSH Key。
4. **Git Config**：配置 Git (`~/.gitconfig`)，使其能根据项目所在的目录（`~/dev/work` 或 `~/dev/personal`）自动加载对应的用户名和邮箱。

我是使用的不同算法生成的两套 SSH Keys，也可以使用同一个算法，分别自定义一个名称即可。

```shell
ssh-keygen -t ed25519 -C "your-personal-email@example.com"
ssh-keygen -t res -C "your-work-email@example.com"
```

然后将两个公钥分配拷贝到不同平台上进行配置。

**配置 SSH (`~/.ssh/config`) 自动选择密钥**。这是实现自动化的关键，通过域名的不同，使用不同的 Key 来连接：

```txt
# 个人 GitHub 账户 (默认)
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes # 只使用明确指定的密钥

# 公司 Gitee 账户
Host gitee.com
  HostName gitee.com
  User git
  IdentityFile ~/.ssh/id_rsa
  IdentitiesOnly yes
```

如果都是 Github，可以使用别名来解决这个问题，稍微麻烦一点点。

**配置 Git (`~/.gitconfig`) 条件化加载**。编辑你的主 `~/.gitconfig` 文件，设置默认（个人）配置和条件包含规则：

```txt
[user]
    # 这是你的默认个人配置 (用于 GitHub)
    name = Your Personal Name
    email = your-personal-github-email@example.com

[core]
    autocrlf = input

# 当 Git 命令在 ~/dev/work/ 目录或其子目录下运行时，
# 就额外加载 ~/.gitconfig-work 文件中的配置。
[includeIf "gitdir:~/dev/work/"]
    path = ~/.gitconfig-work
```

默认使用个人账号，**如果在特定目录下的 git repo 下**，会使用另一个配置，另一个配置里面的内容如下：

```txt
[user]
    # Gitee/公司项目使用的配置
    name = Your Work Name
    email = your-work-gitee-email@company.com
```

到此，配置完成。可以使用下面这些命令来进行一下测试：

```shell
ssh -T git@github.com
ssh -T git@gitee.com
cd ~/dev/work/repo
git config user.name/email
cd xxx # 别的路径下
git config user.name/email
```
