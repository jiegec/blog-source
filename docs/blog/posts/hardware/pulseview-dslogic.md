---
layout: post
date: 2019-08-02 23:15:00 +0800
tags: [la,logicanalyzer,sigrok,pulseview]
category: hardware
title: 用 PulseView 配合 DSLogic 调试 SPI Flash
---

最近需要用到逻辑分析仪来调试 SPI Flash，设备是 DreamSourceLab 的 DSLogic，最开始用的是官方的 DSView，确实能够抓到 SPI 的信号，也可以解析出一些 SPI Flash 的数据，但是很多是不完整的。

后来把源码下载下来，发现是基于 sigrok 和 PulseView 做的一个魔改版，然后 sigrok 官网上最新的版本已经支持了 DSLogic，于是就用 PulseView 替代 DSView。一开始遇到的问题是没有 firmware，一番搜索找到了[解决方案](https://sigrok.org/wiki/DreamSourceLab_DSLogic)，按照脚本下载好文件即可。

进到 PulseView 以后，把 SPI 的四路信号接上，然后抓了一段信号，解析：

![](/images/pulseview.png)

可以看到它正确地解析出来了 Fast Read 命令。由于 DSView 它 fork 自一个比较老的版本，所以它并不能正确解析出来。

P.S. Linux 下它界面显示比 macOS 下好看一些，估计是没有适配好。
