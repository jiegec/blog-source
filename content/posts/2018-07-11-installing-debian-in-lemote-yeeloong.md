---
layout: post
date: 2018-07-11 23:12:00 +0800
tags: [debian,mips,loongson,lemote,yeeloong,jessie]
category: devops
title: 在 Lemote Yeeloong 上安装 Debian jessie
---

参考网站：

[gNewSense To MIPS](http://wiki.gnewsense.org/Projects/GNewSenseToMIPS)
[Run a TFTP server on macOS](https://rick.cogley.info/post/run-a-tftp-server-on-mac-osx/)
[Debian on Yeeloong](https://wiki.debian.org/DebianYeeloong)
[Debian MIPS port wiki](https://wiki.debian.org/MIPSPort)
[Debian MIPS port](https://www.debian.org/ports/mips/)

首先，进入设备的 PMON：
```
Press Del to enter PMON
```

然后，下载 Debian Jessie 的 netboot 文件：
```
$ wget https://mirrors.tuna.tsinghua.edu.cn/debian/dists/jessie/main/installer-mipsel/current/images/loongson-2f/netboot/vmlinux-3.16.0-6-loongson-2f
$ wget https://mirrors.tuna.tsinghua.edu.cn/debian/dists/jessie/main/installer-mipsel/current/images/loongson-2f/netboot/initrd.gz
```

以 macOS 为例，起一个 tftp 服务器以供远程下载：
```shell
# ln -s these files to /private/tftpboot:
# initrd.gz
# vmlinux-4.16.0-6-loongson-2f
$ sudo launchctl load -F /System/Library/LaunchDaemons/tftp.plist
# set addr manually to 192.168.2.1
```

回到 PMON ，配置远程启动：
```shell
> ifaddr rtl0 192.168.2.2
> load tftp://192.168.2.1/vmlinux-3.16.0-6-loongson-2f
> initrd tftp://192.168.2.1/initrd.gz
> g
```

之后就是熟悉的 Debian Installer 界面。起来之后，就可以顺手把 tftp 服务器关了：
```shell
$ sudo launchctl unload -F /System/Library/LaunchDaemons/tftp.plist
```

实测滚到 stretch 会挂。因为 stretch 虽然也有 mipsel 架构，但是它的 revision 与 Loongson-2f 不大一样，会到处出现 SIGILL 的问题，不可用。靠 jessie 和 jessie-backports 已经有不少的软件可以使用了。
