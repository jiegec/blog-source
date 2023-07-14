---
layout: post
date: 2018-04-10
tags: [rust,os,stanford,cs140e,rpi3,aarch64]
category: programming
title: 近来做 Stanford CS140e 的一些进展和思考（8）
---

在[上一篇文章](thoughts-on-stanford-cs140e-7.md)之后，我其实还是很忙，但是一直心理惦记着这件事，毕竟只剩最后的一点点就可以做完了，不做完总是觉得心痒。

今天做的部分是调度。我们目前只在 EL0 运行了一个 shell，每当触发 exception 时回到 kernel 进行处理，再回到原来的地方。但现在，我要实现一个 preemtive round-robin scheduler，就需要管理当前的所有进程，并且维护当前的进程状态，当时钟中断到来的时候，决定下一个 time slice 要执行的进程，再切换过去。这个过程当然会遇到不少的坑。

首先，我们需要判断一个进程是否可以执行了。考虑到阻塞的 IO，作者提供了一个优雅的方法：如果这个进程阻塞在 IO 上，那么，提供一个函数，在 scheduler 中调用，判断所需要的数据是否到达。这样，我们就可以一个循环把下一个 time slice 要执行的线程找到。如果找不到，就等待 interrupt 再尝试。

困难的地方在于，在启动的时候，切换到一个起始线程。并且在上下文切换的时候，在 process 1 -> kernel -> process 2 这两步过程中，有许多寄存器都需要仔细考虑如何实现。并且在这个过程中，我也发现了之前写的代码中的问题，最终修复了（目前来看是 working 了）。

我的代码实现在 [这里](https://github.com/jiegec/cs140e/commit/977f179a9b28e88e85f4ba9577a0682bf2b6c57b) 。下一步就要写 syscall 了。希望能在期中前抽时间赶紧把这个做完。

18:54 PM Update: 刚实现完了 sleep 的 syscall。比预想中要简单。果然找到了自己实现的调度器的 BUG。此系列大概是完结了。

2019-02-12 Update: [下一篇文章](thoughts-on-stanford-cs140e-9.md)。
