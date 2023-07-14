---
layout: post
date: 2018-11-27
tags: [macos,darkmode,googlechrome]
categories:
    - software
---

# 强制启用 Google Chrome 原生的 Dark Mode

Mojave 的 Dark Mode 真香，但是 Google Chrome 并不会随着系统的 Dark Mode 设置变化，所以 NightOwl 只能让部分软件按照时间变更 Dark/Light Mode。一番搜索，发现其实 Google Chrome 其实已经[支持了 Dark Mode](https://chromium-review.googlesource.com/c/chromium/src/+/1238796)，但只能设置，不能按照系统的状态自动切换，命令如下：

```
$ open -a Google\ Chrome --args --force-dark-mode
```

然后就可以看到 Google Chrome 已经是 Dark Mode 了。但可惜并不能自动切换。

