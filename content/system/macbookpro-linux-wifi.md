---
layout: post
date: 2020-01-05 00:53:00 +0800
tags: [linux,wifi,broadcom,bcm43602,brcmfmac,macbookpro]
category: system
title: MacBookPro 14,3 Wi-Fi 驱动问题解决方案
---

之前在 MacBookPro 14,3 安装 Linux 后，很多东西的驱动都有了解决方法，[参考 1](https://gist.github.com/TRPB/437f663b545d23cc8a2073253c774be3)，[参考 2](https://github.com/roadrunner2/macbook12-spi-driver)，触摸板和键盘等等都可以正常使用，触摸板的使用效果比我意料要好一些，虽然还是没有 macOS 原生那么好。但 Wi-Fi 一直有能扫到信号但连不上的问题，最近终于有了比较完善的解决方案，[地址](https://bugzilla.kernel.org/show_bug.cgi?id=193121#c52)，也是两个月前才出来的方案，我测试了一下，确实可以很好的解决网络问题。

另一方面，带 T2 的 MacBook 似乎也有了支持，见 [aunali1/linux-mbp-arch](https://github.com/aunali1/linux-mbp-arch)，有一些尚未 upstream 的 patch，但我没有设备，就没有测试了。需要吐槽的是 ArchWiki 不怎么更新新 Model 的 MacBook 的教程，都是到处找散落的 github repo 和 gist 找别人的方案。
