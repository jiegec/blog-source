---
layout: post
date: 2018-02-16 20:09:00 +0800
tags: [rust,os,stanford,cs140e,kernel,hardware,rpi3,shell,bootloader,mit 6.828,atags]
category: programming
title: 近来做 Stanford CS140e 的一些进展和思考（3）
---

由于 `Assignment 2: File System ` 延期发布，所以中间那段时间转向 `MIT 6.828` 稍微研究了一下。前几天放出了新的任务，在[上一篇文章]({{< relref "thoughts-on-stanford-cs140e-2.md" >}})之后，我又有了一些进展：实现了从内存中读取 `ATAGS(ARM Tags)` 信息的代码，从而可以获得内存大小的信息，根据这个信息，实现了 `bump` 和 `bin` 两种内存分配器，并且把二者之一注册为全局内存分配器，利用上更新了的 `std` 就可以使用需要动态分配内存的相关工具了。利用这个，我实现了 `shell` 输入历史的回溯，把输入历史保存在一个动态增长的数组中，再特殊处理上下键，把当前的行替换为历史。

这个过程也不是没有踩坑。一开始代码放出来了，但是题目说明还没出，我就自己按照代码做了 `ATAGS` 和 `bump` 分配器，后来做完了，看到说明出了以后，发现理解还是有偏差，把代码更改了并修复了分配器的 BUG。看到 `bin` 分配器的时候，我按照网上的 `buddy memory allocation` 实现了一个内存分配器，原理看起来简单实现起来还是有很多细节问题，后来按照新放出的单元测试，修修补补才写得差不多可用了。同时，原来的 `bootloader` 因为用了新的 `std` 而缺失了 `alloc` 不能编译，我就把 `kernel` 下的相关文件软连接过去，调了数次后把问题解决。此时， `kernel` 文件大小已经有 40K，按照 115200 Baudrate 发送需要几秒才能传输过去，我就调到了 230400 Baudrate，果然现在的传输速度就有所提升，可以接受了。等之后写了 `EMMC(SD card)` 的驱动和 `FAT32` 的文件系统后，就可以实现更多的 `shell` 的功能了。中间还遇到一个问题，就是如果给 `kernel` 开启了 `bin` 分配器，使用 `exit` 回到 `bootloader` 就无法传新的 `kernel` 上去了，结果发现是因为 `bin` 中用到的侵入式 `LinkedList` 实现覆盖了部分 `bootloader` 的代码，换回不能回收内存的 `bump` 分配器即可，反正目前远远还用不了那么多内存。

之后还要在 `aarch64` 上用 `MMU` 实现虚拟内存，之前在 `MIT 6.828` 里被页表整得脑子眩晕，希望到时我还活着吧（逃

更新：[下一篇在这里]({{< relref "thoughts-on-stanford-cs140e-4.md" >}})。
