---
layout: post
date: 2023-04-10
tags: [sco,unixware,unix]
categories:
    - system
title: SCO OpenServer 6.0.0 虚拟机安装
---

## 安装过程

首先从 <https://www.sco.com/support/update/download/product.php?pfid=12&prid=20> 下载 SCO OpenServer 的安装 ISO。尝试过用 QEMU 启动，但是会卡在无法读取硬盘的错误上。

最后使用 VirtualBox 7.0.6 成功启动，注意创建虚拟机的时候不要给太多内存，例如 4GB 就起不来，2GB 可以。硬盘我也只给了 4GB 的空间。

安装过程中会询问 License number 和 License code，可以选择使用 Evaluation License，或者使用下面参考文档中提供的 License。按照流程一直走就可以了。如果重启出现无法 mount root 的问题，就 poweroff 再开机。

## 参考文档

本博客参考了以下文档中的命令：

- <https://virtuallyfun.com/2020/11/21/fun-with-openserver-6-and-mergepro/>
