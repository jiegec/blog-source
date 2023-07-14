---
layout: post
date: 2023-04-10
tags: [unixware,unix]
categories:
    - system
---

# UnixWare 7.1.4 虚拟机安装

## 安装过程

在 <https://www.sco.com/support/update/download/product.php?pfid=1&prid=6> 可以看到 UnixWare 7.1.4 的相关下载，其中首先要下载 UnixWare 的安装 ISO：<https://www.sco.com/support/update/download/release.php?rid=346>，尝试过用 QEMU 启动，会遇到找不到 CD-ROM 的问题，虽然通过设置 `ATAPI_DMA_DISABLE=YES` 解决了，但是又遇到了找不到硬盘的问题。

最后换成了 VirtualBox 7.0.6。用 VirtualBox 创建虚拟机的时候，不要给太多内存，4GB 就会无法启动，2GB 可以，硬盘也不要给太多，4GB 就足够。

剩下就是按照安装界面一路默认即可，License 可以选择 Defer，使用 Evaluation License。

关机以后，修改启动顺序，把硬盘放到 CD 前，然后启动，就可以进入系统了。如果重启出现无法 mount root 的问题，就 poweroff 再开机。

## 参考文档

本博客参考了以下文档中的命令：

- <https://virtuallyfun.com/2018/01/31/revisiting-a-unixware-7-1-1-install-on-qemu-kvm/>
