---
layout: post
date: 2018-05-25
tags: [windows,wsl,getty,agetty,terminal,cu]
category: os
title: 在 WSL 上开启一个 getty 到串口的方法
---

为了测试一个硬件的 terminal，想在 Windows 上向串口开一个 tty，跑各种软件来测试。这件事情在 Linux 上和 macOS 上都有实践，但一直不知道 Windows 上怎么搞。经过了一番搜索，找到了 https://blogs.msdn.microsoft.com/wsl/2017/04/14/serial-support-on-the-windows-subsystem-for-linux/ 和 https://unix.stackexchange.com/a/123559 的方案。


以 COM5 为例：

```shell
$ sudo chmod 666 /dev/ttyS5
$ sudo agetty -s 115200 ttyS5 linux
```

这样就可以看到一个登录的界面了。

在 macOS 上 (https://superuser.com/questions/1059744/serial-console-login-on-osx)：

```shell
$ screen /dev/tty.SLAB_USBtoUART 115200
# type C-b : exec ::: /usr/libexec/getty std.115200
```
