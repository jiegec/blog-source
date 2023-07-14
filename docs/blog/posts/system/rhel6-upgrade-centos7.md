---
layout: post
date: 2021-08-30
tags: [rhel,centos,upgrade,linux]
categories:
    - system
title: 一次从 RHEL 6 到 CentOS 7 的更新
---

## 背景

有一台 RHEL 6 的服务器，各种软件版本太老了，用起来很难受，因此想升级。一开始想升级到 RHEL 7，但是发现必须要从 RedHat 下载 ISO，比较慢，所以我就先切换到 CentOS 6，再升级到 CentOS 7

## 过程

### RHEL 6 Pre upgrade

一开始还是打算升级到 RHEL 7，所以跟随 RedHat 的文档去做 pre upgrade check，发现有一步要跑好久，网上搜了一下，发现这个步骤会扫描已有的各种程序，检查升级以后会不会出现不能运行的问题。但是如果有很多小文件，这一个过程就会进行很久，好在可以设置 exclusion 目录。最后检查出来的结果就是 GNOME 没法升级，建议卸载。

倒腾了一下升级工具，发现需要离线安装，比较麻烦，我就干脆换 CentOS 了。

### RHEL 6 -> CentOS 6

首先，把软件源都切换到 CentOS，这一步很简单，因为包都是一样的。只不过，因为 CentOS 6 在 centos-vault 里面，所以用起来比较麻烦。

### CentOS 6 -> CentOS 7

由于 CentOS 6 到 CentOS 7 升级涉及的改动比较多，官方提供了一个升级工具。一开始，我想直接升级到 CentOS 7 最新版本，但是报错，看到网上说可以升级到 CentOS 7 的早期版本，试了一下，确实没问题。

一通升级以后，重启，进入更新过程，发现很多包都安装失败了。重启以后，因为找不到 rootfs，挂在了 dracut 的 initramfs 里面。

### 漫长的修复过程

简单试了一下，发现 dracut 的 initramfs 里程序太少了，调试起来很痛苦。所以，我在 BMC 里通过 Virtual Media 挂了一个 Arch Linux 的 Live CD。因为通过 Web 访问延迟太高，我设了一个 root 密码，然后直接 ssh 到 live cd 系统中。

接着，我发现，可以正常找到盘和里面的各个分区，所以怀疑是之前 initramfs 里缺了什么东西，导致找不到硬盘。我 arch-chroot 到 root 分区里，然后手动更新各个包，特别麻烦：我首先升级了 yum repos 到最新的 CentOS 7，然后手动删掉/升级 el6 的各个软件包。最后好不容易把 kernel 终于升级好了，又重新生成 grub2 的配置，因为 CentOS 6 是 grub1。这时候，重启进入系统，发现可以找到 rootfs 了，但是经过 selinux relabel 以后，仍然会遇到 systemd-logind 起不来的问题，伴随着一系列的 audit 报警。

最后，使出了暴力的解决办法：在 cmdline 中设置 selinux=0 audit=0，然后终于进入系统了。再继续删掉一些 el6 的包，然后升级各种包，最后终于是恢复了正常。