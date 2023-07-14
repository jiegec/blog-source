---
layout: post
date: 2021-03-29
tags: [ipmitool,static]
categories:
    - system
title: 静态编译 ipmitool
---

为了在 ESXi 上运行 ipmitool，需要静态编译 ipmitool。网上已经有一些解决方案：

https://github.com/ryanbarrie/ESXI-ipmitool
https://github.com/hobbsh/static-ipmitool
https://github.com/ewenmcneill/docker-build-static-ipmitool

我稍微修改了一下，用来编译最新 ipmitool：

```bash
#!/bin/bash
set -x
export VERSION=1.8.18
rm -rf ipmitool_$VERSION
curl -L -o ipmitool_$VERSION.tar.bz2 http://deb.debian.org/debian/pool/main/i/ipmitool/ipmitool_$VERSION.orig.tar.bz2
tar xvf ipmitool_$VERSION.tar.bz2
cd ipmitool-$VERSION
CC=gcc CFLAGS=-m64 LDFLAGS=-static ./configure
make -j24
cd src
../libtool --silent --tag=CC --mode=link gcc -m64 -fno-strict-aliasing -Wreturn-type -all-static -o ipmitool.static ipmitool.o ipmishell.o ../lib/libipmitool.la plugins/libintf.la
file $PWD/ipmitool.static
```

复制下来，编译完成后 scp 到 esxi 中即可使用。
