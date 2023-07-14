---
layout: post
date: 2023-07-15
tags: [site]
categories:
    - meta
---

# 把博客生成器从 Hugo 迁移到 Mkdocs

距离上一次 [Jekyll 迁移到 Hugo](migrate-from-jekyll-to-hugo.md) 已经过去了四年，这次正好 mkdocs-material 发了新的 beta 版本，加入了对博客的支持，所以就当小白鼠，把博客迁移到了 Mkdocs + Mkdocs-Material。

这次迁移比较顺利，除了 tag 和 category 少了一些页面以外，原来的文章的链接都是正常的。为什么要迁移呢，主要是最近写各种文档，Mkdocs 用的比较多，但是 Mkdocs 的 Markdown 很多地方和 Hugo 不太一样，下面列一些最难以忍受的 Hugo 的问题：

1. 数学公式：Hugo 的 `\` 需要转义，导致很多地方写数学公式都很麻烦，然后因为我经常要在 Hugo 和 Mkdocs 之间复制 Markdown，此时就需要很多手动工作。
2. 资源路径：Hugo 的资源路径默认都是绝对路径，要引用其他文章的话，要么用啰嗦的 relref，要么就写绝对路径，比较头疼。Mkdocs 就很好，自动检测，帮我计算出实际的地址。

迁移的时候有很多细节上的不同，不过基本靠 VSCode 的正则表达式替换解决了。

不过，Mkdocs 又出现了 Jekyll 的老问题，就是性能比较差。当然了，不一定是 Mkdocs 本身的问题，也可能是 Mkdocs-Material 加各种插件的问题，目前还有待观察。无论如何，Python 调起来总归是比 Ruby 要容易。希望不要在未来的某一天，由从 Mkdocs 迁移回 Hugo。
