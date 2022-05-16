---
layout: post
date: 2019-02-12 11:35:00 +0400
tags: [rust,os,stanford,cs140e,kernel]
category: programming
title: 近来做 Stanford CS140e 的一些进展和思考（9）
---

距离[上一篇 CS140e 系列文章]({{< relref "thoughts-on-stanford-cs140e-8.md" >}})已经过去了很久，距离第一篇文章过了一年零几天。在后来这一段时间内，CS140e 结束了课程，又开始了新一年的 winter 2019 课程，迎来的却是 C 版本的 CS140e ，不禁让人感到失望。还好，Sergio Benitez 放出了原来的 CS140e 的[镜像](https://cs140e.sergio.bz)，如果大家仍然想回去查看原版优质的 CS140e ，可以点进去参考。

后来因为机缘巧合参与到了清华的 Rust OS 课程，又想到回来把原来的 CS140e 进行更新，于是顺带把跑在 QEMU 下的一些需要的工作给做了，另外把 Rust nightly 版本更新了（一年前的 nightly 还能叫 nightly ？），才发现标准库变化还是蛮大的，由于 nightly 版本变了，而且原来是内嵌了一个阉割过的 std ，所以主要是从新的 std 里抄代码到内嵌的 std 中。另外，原来的 xargo 也不再维护了，转而使用 rust-xbuild 进行交叉编译。

然后又顺手实现了 backtrace 和从 backtrace 中配合 dward symbols 找函数名的功能，不过实践证明，这些东西还是 addr2line 做得更好，所以也就没有做下去，在 relocation 上也是遇到了各种问题。这个经验也是应用到了 rCore 那边。

再之后也就是寒假写驱动了，见之前的一个博文，我就没有在 CS140e 上去实现它了。有时间有兴趣的时候再考虑做一下 Raspberry Pi 的网卡驱动吧。

写于迪拜雨天。