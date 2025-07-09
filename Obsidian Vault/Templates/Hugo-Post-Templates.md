---
<%*
// --- 模板配置 ---
const defaultTags = ["标签"];
const defaultCategories = ["分类"];
// --- 模板配置结束 ---

// 1. 获取文章标题
// tp.file.title 会直接获取 QuickAdd 创建的中文文件名 (不含.md)
// 我们不需要对它做任何处理，直接作为标题使用
const title = tp.file.title;

// 2. 自动生成一个健壮、唯一的英文/数字 slug
// 格式为：YYYYMMDD-8位随机字母数字
const datePart = tp.date.now("YYYYMMDD");
const randomPart = Math.random().toString(36).substring(2, 10);
const slug = `${datePart}-${randomPart}`;

// 3. 构建完整的 Frontmatter
const frontmatter = `
date: ${tp.date.now("YYYY-MM-DDTHH:mm:ssZ")}
draft: true
title: '${title}'
slug: '${slug}'
tags:
  - ${defaultTags.join("\n  - ")}
categories:
  - ${defaultCategories.join("\n  - ")}
`;

tR += frontmatter;
%>---

在这里开始你的正文...
