---
date: "{{ .Date }}"
draft: true
title: "{{ replace .File.ContentBaseName "-" " " | title }}"
slug: "{{ .Date.Format "20060102" }}-{{ substr (sha1 .File.Path) 0 8 }}"
tags:
  - 标签
categories:
  - 分类
---