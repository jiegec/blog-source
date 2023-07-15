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

<!-- more -->

## 优化性能

既然遇到了性能问题，那么就尝试解决一下它：首先，开发的时候一些插件可以关闭，这个在 mkdocs-material 的文档里也有提到方法：

```yaml
plugins:
  - tags:
      enabled: !ENV [DEPLOY, false]
  - rss:
      enabled: !ENV [DEPLOY, false]
  - git-revision-date-localized:
      enabled: !ENV [DEPLOY, false]
```

只有在最终部署的时候，把 DEPLOY 环境变量设置上，这样就可以提高 `mkdocs serve` 的响应速度。

另一方面，利用 Python 自带的 profiler，以及 flameprof 软件来生成 flamegraph：

```shell
python3 -m cProfile -o mkdocs.prof /path/to/mkdocs build
python3 -m flameprof mkdocs.prof > output.svg
```

在浏览器打开 output.svg，可以看到热点是在我 fork 自别人的 mkdocs-wavedrom-plugin 插件中，这个插件在 `on_post_page` 里面用 bs4 解析了输出的 HTML，然后做一些改动。由于在我的场景下，wavedrom 代码到 `<script>` 这一步的转换已经由 pymdownx 完成了，剩下只需要插入一段用于激活 WaveDrom 渲染的代码，因此把复杂的 bs4 HTML 解析替换成了简单的文本操作，这时候这个插件就不是瓶颈了。Deploy 时间从 44 秒降到了 31 秒，效果还是很显著的。

接下来继续 profile，发现 `mkdocs serve` 主要的热点在 blog plugin 和 rss plugin 中，里面大部分时间在 render markdown，比较难优化。其中主要影响性能的是从正文中抽取摘要，它要渲染多一次 markdown，把 excerpt 部分取出来，扫描一遍链接，把链接指向实际 post。此外，pygments 给代码块上色占的时间也比较长。

而 Deploy 的时间主要花在 git-revision-date-localized 插件中，这也算正常，毕竟它要执行很多次 git 命令来获取时间。这个目前没什么办法，除非插件改成更加高效的获取手段，例如直接用 Git 的 binding 去读取 .git 目录下的信息，而不是跑一个 git 进程然后读取输出。

接下来要继续优化的话，可能就要找到哪些 markdown 文件对性能影响比较大。

