---
layout: post
date: 2019-03-04
tags: [rcore,rust,os,e1000,syscall,msi,pci,interrupt]
categories:
    - programming
title: 实现网络的 syscall
---

有了网卡驱动，接下来要做的就做网络的 syscall 了。为了测试，首先在 busybox 里找可以用来测试的 applet，由于没有实现 poll，所以 nc telnet 啥的都用不了。最后选择到了 ping 和 pscan 上。

ping 大家都很了解，pscan 就是一个扫端口的，对一个 ip 连续的若干个端口发起 tcp 请求。这就要求我提供 raw socket 和 tcp socket 状态的支持。由于网络栈本身是异步的，但 read connect 这些函数在不调 setsockopt 的前提下又是同步的，然而现在又没有 signal 可以用，要是 block 了就再也出不来了。于是就采用了 Condvar 的办法，拿一个全局的条件变量，当 poll 不到内容的时候，先把线程拿掉，等到网络栈更新了，再恢复。这样至少不会把 cpu 也 block 住。

然后就是把 socket 部分改了又改吧，数据结构的设计改了几次，为了解决 ownership 问题上锁啊也有点多，但是也更细了，虽然实际上可能没有必要，因为上面还有大的锁。不过性能还不是现在考虑的重点，关键还要先把 send recv accept bind listen 啥的写得差不多了，然后还有把 poll/select 实现了，这个很关键。

中间遇到的最大的坑就是，接收 pci interrupt 的时候总是啥也没有，然后靠万能的 qemu trace 发现，原来是 mask 掉了，所以啥也收不了，然后最后的解决方案就是用 MSI Interrupt #55 搞定了这个问题。至于为啥是 55 呢，因为 23 + 32 = 55 啊（误

总之是修好了。终于可以继续写其它的 syscall 了。还没想好 poll 要怎么写，orz。
