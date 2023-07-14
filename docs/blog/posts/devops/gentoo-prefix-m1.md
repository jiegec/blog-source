---
layout: post
date: 2023-07-08
tags: [gentoo,gentoo-prefix,macos,m1]
category: devops
title: 在 Apple M1 上试用 Gentoo/Prefix
---

## 背景

上一次折腾 Gentoo/Prefix 是[五年多以前](/devops/2017/12/27/try-gentoo-prefix-on-macos/)，当时还是用的 Intel Mac，最近需要探索一下在现在的 macOS 系统上用 Gentoo/Prefix 会遇到哪些问题，因此今天在 Apple M1 上重新尝试一次。

## 安装

按照[官网](https://wiki.gentoo.org/wiki/Project:Prefix/Bootstrap)的文档，下载脚本并运行：

```shell
wget https://gitweb.gentoo.org/repo/proj/prefix.git/plain/scripts/bootstrap-prefix.sh
chmod +x bootstrap-prefix.sh
./bootstrap-prefix.sh
```

按照提示输入即可。

编译使用了四到五个多小时，占用 3GB 的硬盘空间。成功以后进入 Gentoo Prefix：

```shell
./startprefix
```

## 折腾

编译并运行大概两个小时以后，遇到了编译错误：

```shell
Undefined symbols for architecture arm64:
  "_libintl_bindtextdomain", referenced from:
      __locale_bindtextdomain in _localemodule.o
  "_libintl_dcgettext", referenced from:
      __locale_dcgettext in _localemodule.o
  "_libintl_dgettext", referenced from:
      __locale_dgettext in _localemodule.o
  "_libintl_gettext", referenced from:
      __locale_gettext in _localemodule.o
  "_libintl_setlocale", referenced from:
      __locale_setlocale in _localemodule.o
      __locale_localeconv in _localemodule.o
  "_libintl_textdomain", referenced from:
      __locale_textdomain in _localemodule.o
ld: symbol(s) not found for architecture arm64
```

是在编译 python3.11.3 的时候遇到的问题，经过一番搜索，发现有一个错误信息比较相关：[dev-lang/python-3.11.3: bootstrap-prefix.sh stage3 fails (on MacOS/Darwin)](https://bugs.gentoo.org/906507)，也是在编译 python3.11.3 的时候出错，只不过错误信息不太一样。

我看到这个 bug report 时，里面说问题在新的 commit 已经修复了，但是我仔细看了一下，修复的时间正好在我跑 bootstrap 脚本后几个小时，也就是说我跑的版本是修复前的版本。于是我重新下载了最新版，重新 bootstrap，又等了两个小时，还是出现了同样的问题，说明问题并没有被解决。

### libintl

观察错误信息，发现是 libintl 相关的符号缺失。向 @heroxbd 学习到了 libintl 的机制：它是一套 API，在 glibc 和 musl 等一些 libc 中有实现，在 gettext 中也有实现，系统里只需要有一份就行。因此在常见的 Linux 发行版里，libintl 是由 libc 提供的，此时 gettext 编译的时候就不会附带 libintl；而如果在 macOS 上，由于 macOS 的 libc 没有 libintl 的 API，所以 gettext 编译的时候就要附带 libintl。

例如 Homebrew 的编译脚本里，就做了这个特殊处理：

```shell
$ brew cat gettext
# omitted
    args << if OS.mac?
      # Ship libintl.h. Disabled on linux as libintl.h is provided by glibc
      # https://gcc-help.gcc.gnu.narkive.com/CYebbZqg/cc1-undefined-reference-to-libintl-textdomain
      # There should never be a need to install gettext's libintl.h on
      # GNU/Linux systems using glibc. If you have it installed you've borked
      # your system somehow.
      "--with-included-gettext"
    else
      "--with-libxml2-prefix=#{Formula["libxml2"].opt_prefix}"
    end
# omitted
```

在 Gentoo 中，处理方式是这样的：把 gettext 的源码编译两份，对应两个包，一个包叫做 gettext，也就是 gettext 去掉 libintl 的部分；另一个包叫做 libintl，也就是 gettext 的 libintl 部分。两个包用同一份源码，只是编译选项不同，因此得到了不同的结果。

那么，接下来的问题就是，为什么会缺符号呢？比较一下 homebrew 和 gentoo 编译出来的 libintl.dylib 符号，可以发现区别：

```shell
$ objdump -t /opt/homebrew/opt/gettext/lib/libintl.a | grep bindtextdomain
0000000000000000 g     F __TEXT,__text _libintl_bindtextdomain
000000000000001c g     F __TEXT,__text _bindtextdomain
0000000000000000         *UND* _libintl_bindtextdomain
$ objdump -t $EPREFIX/tmp/usr/lib/libintl.dylib | grep bindtextdomain
0000000000009a34 l     F __TEXT,__text _bindtextdomain
0000000000004800 g     F __TEXT,__text _libintl_bindtextdomain
```

可以看到，两者的区别是 visibility 从 global 变成了 local，链接的时候也出现了 warning：

```
ld: warning: cannot export hidden symbol _bindtextdomain from .libs/intl-compat.o
```

@heroxbd 给出了临时的解决方法：

```shell
$ gl_cv_cc_visibility=no $EPREFIX/tmp/usr/bin/emerge -1v libintl
```

编译的时候强制把 `-fvisibility=hidden` 覆盖掉，这样就不会有 visibility 的问题：

```shell
$ objdump -t /Volumes/Data/gentoo/tmp/usr/lib/libintl.dylib | grep bindtextdomain
0000000000009a34 g     F __TEXT,__text _bindtextdomain
0000000000004800 g     F __TEXT,__text _libintl_bindtextdomain
```

此时问题就解决了，可以正常编译 python3。

### 其他问题

目前还遇到了一个小 bug：gettext 强制打开了 xattr（https://bugs.gentoo.org/910070），但是 attr 在 macOS 上编译不过，解决办法是再 force 把 xattr USE 删掉：

```shell
$ cat /etc/portage/profile/package.use.force
>=sys-devel/gettext-0.22-r1 -xattr
```
