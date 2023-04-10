---
layout: post
date: 2023-04-10 20:21:00 +0800
tags: [sco,unixware,unix]
category: system
title: SCO OpenServer 6.0.0 虚拟机安装
draft: true
---

## 安装过程

首先从 <https://www.sco.com/support/update/download/product.php?pfid=12&prid=20> 下载 SCO OpenServer 的安装 ISO，然后用 QEMU 启动，需要用图形界面：

```shell
qemu-system-i386 -accel kvm -m 16384 -serial mon:stdio -drive file=sco-hdd.qcow2,if=ide -cdrom ../../ISOs/OpenServer-6.0.0Ni-2006-02-08-1513.iso
```

安装过程中会询问 License number 和 License code，按照 <https://virtuallyfun.com/2020/11/21/fun-with-openserver-6-and-mergepro/> 进行输入。

但是安装过程会出现问题，无法继续。

## 参考文档

本博客参考了以下文档中的命令：

- <https://virtuallyfun.com/2020/11/21/fun-with-openserver-6-and-mergepro/>
