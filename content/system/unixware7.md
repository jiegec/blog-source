---
layout: post
date: 2023-04-10 19:11:00 +0800
tags: [unixware,unix]
category: system
title: UnixWare 7.1.4 虚拟机安装
draft: true
---

## 安装过程

在 <https://www.sco.com/support/update/download/product.php?pfid=1&prid=6> 可以看到 UnixWare 7.1.4 的相关下载，其中首先要下载 UnixWare 的安装 ISO：<https://www.sco.com/support/update/download/release.php?rid=346>，用 QEMU 启动，需要图形界面：

```shell
qemu-img create -f qcow2 unixware-hdd.qcow2 4G
qemu-system-i386 -accel kvm -m 16384 -serial mon:stdio -drive file=unixware-hdd.qcow2,if=ide -cdrom ../../ISOs/uw714.CD1.Jun2008.iso
```

启动时，要按照 <https://www.scosales.com/ta/kb/125312.html> 的方法添加启动参数，否则安装过程会无法读取 cdrom：

``` shell
# Press <space>
[boot] ATAPI_DMA_DISABLE=YES 
[boot] boot
```

安装过程中会询问 License，选择 defer，进行 60 天的试用。

但是后续安装的时候，会提示硬盘损坏，不知如何解决。

## 参考文档

本博客参考了以下文档中的命令：

- <https://virtuallyfun.com/2018/01/31/revisiting-a-unixware-7-1-1-install-on-qemu-kvm/comment-page-1/>
