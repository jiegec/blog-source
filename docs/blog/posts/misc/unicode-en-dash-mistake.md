---
layout: post
date: 2018-10-13
tags: [unicode,pdf]
category: misc
title: Unicode En Dash 小坑
---

今天有同学问到我这个问题：

```
$ gcc -o ph ph.c –lpthread
```

为啥不工作。我怎么看都觉得没啥问题，一开始以为是找不到 pthread，但马上又排除了。想了下会不会是有隐藏的字符，于是让同学 `pbpaste | xxd` 一下，果然发现这里的 `–` 是 `\xe2\x80\x93` ，查了下是 Unicode 里的 En Dash。由于这是从 PDF 里直接拷贝出来的，所以凉了。改成正常的短横杠即可。