---
layout: post
date: 2018-02-06 12:52:59 +0800
tags: [rust,os,stanford,cs140e,kernel,gpio,hardware,rpi3,shell,bootloader,xmodem,uart]
category: programming
title: 近来做 Stanford CS140e 的一些进展和思考（2）
---

在[上一篇文章](/programming/2018/02/04/thoughts-on-stanford-cs140e/)之后，我又有了一些进展：`UART` ，简易的`shell` ，修复了之前写的 `xmodem` 中的 BUG，一个可以从 `UART` 接收一个 `kernel` 写入到内存中再跳转过去的 `bootloader` 。

首先是 `UART` ，就是通过两个 `GPIO pin` 进行数据传输，首先在 `memory mapped IO` 上进行相应的初始化，然后包装了 `io::Read` 和 `io::Write` （这里实现一开始有 BUG，后来修复了），然后很快地完成了一个仅仅能 `echo` 的 `kernel` 。

然后实现了 `CONSOLE` ，一个对 `MiniUart` 和单例封装，就可以用 `kprint!/kprintln!` 宏来输出到 `UART` ，接着实现了一个 `echo` 的 `shell` ，读入一行输出一行。然后实现退格键和方向键，这里的难点在于要控制光标并且用读入的或者空格覆盖掉屏幕上已经显示而不应该显示的内容。接着，利用 `skeleton` 中的 `Command` 做了一个简单的 `echo` 命令。

接着，利用之前编写的 `tty` ，配合上新编写的 `bootloader` ，实现通过 `UART` 把新的 `kernel` 通过 `XMODEM` 协议发送到设备，写入 `0x80000` 启动地址并且调转到新加载的 `kernel` 中执行。

最后，又实现了 `uptime` （输出设备启动到现在的时间）和 `exit` （跳转回 `bootloader` ，可以上传新的 `kernel` ）。并添加了 `TUNA` 作为 `shell` 启动时输出的 `BANNER` 。

整个过程挺虐的，踩了很多的坑，由于很多东西都没有，输入输出目前也只有 `UART` ，写了 `UART` 后又遇到 `XMODEM` 难以调试的问题。十分感谢 `#tuna` 上的 @BenYip 及时地指出了代码的几处问题，节省了我许多时间。

更新：[下一篇在这里](/programming/2018/02/16/thoughts-on-stanford-cs140e-3/)。
