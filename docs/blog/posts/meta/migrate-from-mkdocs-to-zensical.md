---
layout: post
date: 2026-09-30
tags: [site]
categories:
    - meta
---

# 把博客生成器从 Mkdocs 迁移到 Zensical

距离上一次 [从 Mkdocs 迁移到 Zensical](./migrate-from-hugo-to-mkdocs.md) 已经过去了三年，这次 Zensical 终于是补齐了原来 Mkdocs 用到的大部分插件，所以就当小白鼠，把博客从 Mkdocs + Mkdocs-Material 迁移到了 Zensical。

<!-- more -->

这次迁移的背景，就是 Mkdocs-Material 团队对 Mkdocs 后续的更新计划不满，自己独立出来，RIIR 了一个尽量兼容 Mkdocs 生态的 Zensical。当然这个兼容不是 100% 的，所以我也在逐渐地做一些替换，从 [ctf-writeups](/ctf-writeups/) 开始，到 [cpu](/cpu/)，再到博客主站，未来等 i18n 插件到位了，再迁移 [kb](/kb/) 等等。其实用起来也没啥区别，连配置文件都不用改，然后就是构建速度确实快了很多，之前 mkdocs build 一次要好几十秒，zensical 明显更快。

回顾历史，本博客已经做了好几次迁移：

- [2019 年，从 Jekyll 到 Hugo](./migrate-from-jekyll-to-hugo.md)
- [2023 年，从 Hugo 到 Mkdocs](./migrate-from-hugo-to-mkdocs.md)
- 现在 2026 年，从 Mkdocs 到 Zensical

迁移的基本动力，要么是原来的生成器太慢了，要么就是有一些硬伤。不知道几年后，会不会再迁移到新的技术栈呢。
