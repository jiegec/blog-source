---
layout: post
date: 2017-12-27 20:25:23 +0800
tags: [gentoo,gentoo-prefix,macos,package-manager]
category: devops
title: 在 macOS 上试用 Gentoo/Prefix
---

前几天参加了[许朋程](https://keybase.io/jsteward)主讲的Tunight，对Gentoo有了一定的了解，不过看到如此复杂的安装过程和长久的编译时间，又看看我的CPU，只能望而却步了。不过，有Gentoo/Prefix这个工具，使得我们可以在其它的操作系统（如macOS,Solaris等）上在一个 $EPREFIX 下跑 Portage ，也就是把 Portage 运行在别的操作系统，当作一个包管理器，并且可以和别的操作系统并存。

首先还是祭出官网：[Project:Prefix](https://wiki.gentoo.org/wiki/Project:Prefix)。

首先设定好环境变量 `$EPREFIX` ，之后所有的东西都会安装到这个目录下，把 `bootstrap-prefix.sh` 下载到 `$EPREFIX` ，然后 `./bootstrap-prefix.sh` ，会进行一系列的问题，一一回答即可。建议在运行前设置好 `GENTOO_MIRRORS=http://mirrors.tuna.tsinghua.edu.cn/gentoo` 由于TUNA没有对gentoo_prefix做镜像，只能把distfiles切换到TUNA的镜像上。

然后。。。

stage1...


stage2..


stage3.


`emerge -e @world` BOOM


经过 n 次跑挂以后，终于搞完了 stage3 ，然后 `SHELL=bash ./bootstrap-prefix.sh $EPREFIX startscript` 生成 `startprefix` ，在外面的SHELL中向切进来的时候运行这个即可。

然后就可以使用Gentoo/Prefix了。注意！此时的 `$PATH` 仅限于 `$EPREFIX` 下几个目录和 `/usr/bin` `/bin` 所以很多东西都会出问题（Emacs, Vim, Fish etc）。小心不要把自己的目录什么的搞挂了。

然后就可以假装试用Gentoo了！


哈哈哈哈哈哈哈


死于编译 libgcrypt 和 llvm 。
