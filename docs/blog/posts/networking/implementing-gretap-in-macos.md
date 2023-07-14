---
layout: post
date: 2018-08-21
tags: [tuntaposx,tap,gre,gretap]
categories:
    - networking
title: 在 macOS 下实现 GRETAP
---

由于没有找到 macOS 下现成的 GRETAP 实现，我就想到自己实现一个。由于[tuntaposx](http://tuntaposx.sourceforge.net/)提供了一个和 Linux 下基本一样的 TAP Interface，于是自己利用 raw socket 和 TAP Interface 实现了一下，主要方法：


1. 打开 raw socket，读取收到的 proto 47 的包，判断是否为 GRETAP 包，是，则写入内层包到打开的 TAP Interface 中。
2. 从 TAP Interface 中读入包，自己加上 GRE 头和 IP 头，然后发送。

主要的难度是在 raw socket 部分，macOS 继承了 BSD，与 Linux 不大一样。于是参考了[SOCK_RAW Demystified](https://sock-raw.org/papers/sock_raw)，成功地实现了这个功能。

代码放在[jiegec/gretapmac](https://github.com/jiegec/gretapmac)。写得并不高效，仅仅可用，用了一百多行。

UPDATE: 之后又随手实现了一个类似的协议，L2TPv3 over UDP。代码在[jiegc/l2tpv3udptap](https://github.com/jiegec/l2tpv3udptap)。
