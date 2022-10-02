---
layout: post
date: 2019-03-21 22:46:00 +0800
tags: [centos,alpine,slurm,redhat]
category: devops
title: 在古老的 OS 上运行一个干净的新的环境
---

由于某些课程的原因，需要在一个 CentOS 7 上跑一些编译和运行代码。看到这么古老的软件，我心想不行，肯定要找新一些的软件来用。首先想到的是 tmux，于是按照[网上的脚本](https://gist.github.com/ryin/3106801) 很快装了一个 tmux 2.8 版本，果然好了很多。但是常用的很多软件依然是个问题。试了一下最近比较新的 code-server，因为 ABI 问题跑不起来。

于是开始想玩骚操作。首先想到的是 Gentoo Prefix，不过既然是别人的机器，还是算了。又找了 fakeroot 配合 alpine rootfs 的方案，但编译不过，估计是内核版本问题。又试了一下 fakechroot，但它需要配合 fakeroot 使用，这就凉了。

然后又找了一些替代方案。一是 uchroot，但由于 CMake 版本太老也编译不过。最后发现了 [PRoot](<https://proot-me.github.io/>) ，直接提供 prebuilt 然后很容易就可以跑起来：

```bash
$ ./proot -b /proc -b /dev -r $CHROOT /bin/busybox sh
```

于是就进到了 alpine 的 rootfs 中，[下载地址](http://dl-cdn.alpinelinux.org/alpine/v3.9/releases/x86_64/alpine-minirootfs-3.9.2-x86_64.tar.gz)。进去以后发现没有编辑器，于是出来把 apk 的源改了，加了 resolv.conf，就成功地安装了很多很新的软件了。