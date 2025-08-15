---
title: Hexo+Cactus+GitHub搭建极简风格个人博客
categories:
  - ForFun
tags:
  - Hexo
  - Cactus
draft: false
slug: e06bcce9
date: 2024-03-23 23:32:25
---

## 安装 hexo

[Hexo](https://hexo.io/zh-cn/) 是一款基于 node.js 的静态博客框架，依赖少易于安装使用，可以方便的生成静态网页托管在 GitHub 上，是搭建博客的首选框架。

安装基本上包含如下几个基本步骤：

1.   安装 git

2.   安装 nodejs 和 npm

3.   安装 hexo，使用 `npm install -g hexo-cli` 命令

4.   查看上述安装的版本信息，使用 `hexo --version` 命令

     我们

5.   创建一个文件夹，比如 myblog，这个文件夹用来存储博客所有的数据。在这个文件夹目录下执行 `hexo init`

6.   执行 `hexo g` 就可以生成静态文件，执行 `hexo s` 就可以在本地部署

     ![image-20240323163452418](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240323163452418.png)

一个简易的博客就部署好了。

## 安装 cactus 主题

我选择的第三方主题是 cactus。之前使用的是 butterfly，一个很火很高度定制化的主题，用了两年之后，我腻了。我的小破博客没有大佬们的那么精美，想再搞好一点，但无奈于自己的时间、前端知识、审美，只能作罢。而且买的域名马上要到期了，服务器也快到期了，自己的钱包比三年前愈发的捉襟见肘。于是便想好好整理下乱七八糟的博客，换一个清爽的主题，我找到了 cactus。

1.   将 cactus 主题文件下载到 Hexo 的主题目录下，

     ```bash
     git clone https://github.com/probberechts/hexo-theme-cactus.git themes/cactus
     ```

2.   修改 Hexo 配置文件，将主题修改为使用 cactus，只需要更改 _config.yml 文件中的 theme 属性为 cactus。

3.   重复执行 `hexo g` 和 `hexo s` 命令，网站外观如下：

     ![image-20240323165743115](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240323165743115.png)

## 第一篇博客

1.   创建博客文件的命令是 `hexo new blog_name`，默认使用 scaffolds/post.md 文件为模板。我们就可以看到，在 source/_post 目录下，生成了一个 md 文件。

2.   编辑文件如下

     ```markdown
     ---
     title: 第一篇博客
     date: 2024-03-23 17:11:36
     tags:
         - test
     ---
     
     这是我的第一篇测试博客!
     ```

3.   再次执行 `hexo g && hexo s`，在浏览器中访问，结果如下：

     ![image-20240323172237416](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240323172237416.png)

## 将博客部署到 GitHub

1.   github 上创建一个 repository，这个仓库名称必须要是 username.github.io，比如我，一定要是 ceyewan.github.io。

2.   修改 _config.yml 文件最下面的 deploy 属性如下：

     ```yml
     deploy:
     - type: git
       repository: git@github.com:ceyewan/ceyewan.github.io.git
       branch: main
     ```

3.   我这里默认你已经用过 GitHub 了，并且已经配置了 SSH 密钥用于 git 上传文件到 GitHub。然后我们执行 `hexo d` 将博客部署到 GitHub。（需要 `npm install hexo-deployer-git --save` 安装部署的命令）

4.   最后，使用浏览器访问 https://ceyewan.github.io.git，大功告成。

     ![image-20240323173626363](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240323173626363.png)

## 个性化定制

第一第二点是在 _config.yml 文件修改，这是 Hexo 的默认配置文件；后续是在 cactus 主题的 _config.yml 文件中修改。

1.   修改网站的主要信息：

     ```yml
     # Site
     title: Ceyewan's Blog
     subtitle: ''
     description: 'ceyewan 折腾过的好玩的教程、信息安全、计算机技术的个人小站'
     keywords:
     author: ceyewan
     language: zh-CN
     timezone: 'Asia/Shanghai'
     ```

2.   修改网站 URL 和默认的文章链接格式。默认的链接地址很长，而且一般我们的 title 是中文，在 URL 中很丑。我们使用 hexo-abbrlink 插件，该插件会为每篇生成一个唯一字符串，并不受文章标题和发布时间的影响。使用命令 `npm install hexo-abbrlink --save` 安装插件，修改配置文件如下，最后我这个组合生成的就是 32 bit 以十六进制表示的 abbrlink，如 8ddf18fb。

     ```yml
     url: https://ceyewan.github.io
     # permalink: :year/:month/:day/:title/
     permalink: p/:abbrlink.html
     abbrlink:
       alg: crc32	# 算法： crc16(default) and crc32
       rep: hex		# 进制： dec(default) and hex
     ```

3.   修改导航栏。对于我们新添加的导航栏，需要执行 `hexo new page xxx`，如我们执行 `hexo new page categories`，就会在 source 目录下生成一个 categories 目录，我们修改其中的 index.md 文件，只保留 title 那行并添加 `type: categories` ，注意 key 值是固定的，不能随意的改动，在 en.yml 配置文件中可以看到支持的所有的 key 值。

     ```yml
     nav:
       home: /
       category: /categories/
       tag: /tags/
       articles: /archives/
       search: /search/
       about: /about/
     ```

4.   添加搜索功能，除了需要安装一个包之外，就是和上面的操作一样。

     1.   执行 `npm install hexo-generator-search --save`
     2.   执行 `hexo new page search`
     3.   进入 `/source/serch/index.md`，修改md文件的头为

     ```
     title: Search
     type: search
     ```

5.   在 /source 目录下创建 /_data/projects.json，修改文件内容如下，按照自己的需求更改即可：

     ```json
     [
         {
            "name":"Hexo",
            "url":"https://hexo.io/",
            "desc":"A fast, simple & powerful blog framework"
         },
         {
            "name":"Font Awesome",
            "url":"http://fontawesome.io/",
            "desc":"The iconic font and CSS toolkit"
         }
     ]
     ```

6.   仔细阅读配置文件，设置一些自己喜欢的配置。

7.   **TO DO LIST**：

     -   解决 tagcloud 字体大小的问题
     -   找到一个漂亮的代码高亮方案
     -   解决阅读文章屏幕不够宽时目录栏的显示问题

## 使用分支保存源码

在上面我们创建的仓库中创建一个分支 source，并将其设置为默认分支。然后我们将仓库 clone 下来，clone 的是默认分支。这个分支有一份 main 分支的副本，可以放心删除。然后我们将刚刚 myblog 下的文件全部复制到这个文件中，并添加 .gitignore 文件，内容如下：

```
.DS_Store
Thumbs.db
db.json
*.log
node_modules/
public/
.deploy*/
```

最后，使用 `git add . && git commit -m "hexo source" && git push` 将源码推向云端。这样，我们的代码就保存在 github 上了。

在任意一台有 nodejs 和 hexo 环境的电脑上，我们可以使用 git clone 下载源码，然后执行 `npm install && npm install hexo-deployer-git --save` 就可以写新博客了。

## 总结

在一通配置下来，深度了解了这个主题之后，发现简约风又感觉有点不足。。。且用着吧，后续稍微了解了解前端之后，做一些高度定制的东西。贴两张图纪念下上个博客吧：

![image-20240323234056618](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240323234056618.png)
![image-20240323234308378](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240323234308378.png)
![image-20240323234242085](https://ceyewan.oss-cn-beijing.aliyuncs.com/typora/image-20240323234242085.png)

## 参考链接

1.   [hexo 生成永久文章链接](https://zhuanlan.zhihu.com/p/134492757)
1.   [使用 hexo 基于 cactus 仙人掌主题最全美化客制教程](https://reinhart-l.cn/2022/01/19/%E4%BD%BF%E7%94%A8hexo%E5%9F%BA%E4%BA%8Ecactus%E4%BB%99%E4%BA%BA%E6%8E%8C%E4%B8%BB%E9%A2%98%E6%9C%80%E5%85%A8%E7%BE%8E%E5%8C%96%E5%AE%A2%E5%88%B6%E6%95%99%E7%A8%8B/#%E8%87%AA%E5%AE%9A%E4%B9%89%E9%A2%9C%E8%89%B2)
1.   [cactus 官方文档](https://github.com/probberechts/hexo-theme-cactus)
1.   [cactus 主题源代码修改及优化](https://www.plumstar.cn/2022/10/22/cactus%E4%B8%BB%E9%A2%98%E6%BA%90%E4%BB%A3%E7%A0%81%E6%94%B9%E8%BF%9B%E5%8F%8A%E4%BC%98%E5%8C%96/index.html)
1.   [hexo史上最全搭建教程](https://blog.csdn.net/sinat_37781304/article/details/82729029)
1.   [hexo 官方文档](https://hexo.io/zh-cn/docs/index.html)

