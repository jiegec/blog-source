---
layout: post
date: 2023-04-09
tags: [sco,unixware,unix]
categories:
    - system
title: SCO OpenServer 5.0.7 虚拟机安装
---

## 安装过程

首先从 <https://www.sco.com/support/update/download/release.php?rid=218> 下载 SCO OpenServer 的安装 ISO 和从 <https://www.sco.com/support/update/download/release.php?rid=187> 下载 Supplement CD 5 ISO，然后用 QEMU 启动，这次需要用图形界面：

```shell
qemu-system-i386 -accel kvm -m 16384 -serial mon:stdio -drive file=sco-hdd.qcow2,if=ide -cdrom ../../ISOs/OpenServer-5.0.7Hw-10Jun05_1800.iso
```

安装过程中会询问 License number 和 License code，按照 <https://virtuallyfun.com/2020/11/03/fun-with-openserver-and-merge/> 进行输入。

安装的时候，在 hard disk setup 那一步，记得关掉 bad tracking，否则会把整个盘扫一遍，我一开始建了 20GB 的 qcow2，结果这一步跑了一晚上，而且把 qcow2 撑满了。

安装后，重新启动，这次打开网络，同时挂载 Supplement CD 5 ISO：

```shell
qemu-system-i386 -accel kvm -m 16384 -serial chardev:mouse -drive file=sco-hdd.qcow2,if=ide -cdrom osr507suppcd5.iso -net nic -net tap,script=no,ifname=tap0 -chardev msmouse,id=mouse
```

启动以后，运行 custom 命令，然后从 CD-ROM 安装 Graphics and NIC Drivers。我尝试了安装 Maintenance Pack 5，但是启动以后会找不到硬盘，只好恢复之前的 qcow2 备份。可能是缺少了运行 `/etc/conf/cf.d/link_unix` 命令。

为了让图形界面的鼠标工作，在命令行里运行 `mkdev mouse`，然后创建一个 Serial mouse -> Microsoft Serial Mouse，Relink kernel 再重启。注意要和 QEMU 的 `-serial chardev:mouse -chardev msmouse,id=mouse` 配合。但是外面鼠标和里面鼠标移动的距离不一样。

然后运行 `netconfig` 命令，添加 LAN adapter，选择 Intel 网卡，然后退出，Relink kernel 然后重启，就可以访问网络了。可以用 `ifconfig net0 10.0.2.16` 设置 IP 地址， `route add default 10.0.2.15` 来设置默认路由。可以通过降低安全性，兼容老系统来 SSH：

```shell
ssh -oCiphers=aes128-cbc -oHostKeyAlgorithms=ssh-rsa -oKexAlgorithms=+diffie-hellman-group1-sha1 root@10.0.2.16
```

类似地，scp 也要带上上面的参数，再打开 `-O` 模式。

## 安装软件

OpenServer 有自带的工具链：挂载安装 ISO，使用 custom 命令安装 OpenServer Development System 和 SCO OpenServer Linker and Application Development Libraries。但是需要 License 才能使用。

另一个方法是通过 FTP 访问 <ftp://ftp2.sco.com/pub/skunkware/osr5/vols/>，可以看到一些软件的安装包，在里面下载软件并安装。例如，要安装 gcc：

```shell
wget ftp://ftp2.sco.com/pub/skunkware/osr5/vols/gcc-2.95.2-VOLS.tar
scp -r -O -oCiphers=aes128-cbc -oHostKeyAlgorithms=ssh-rsa -oKexAlgorithms=+diffie-hellman-group1-sha1 gcc-2.95.2-VOLS.tar root@10.0.2.16:/
# in sco5
tar xf gcc-2.95.2-VOLS.tar
# Install from Media Images
custom
/usr/local/bin/gcc --version
```

依法炮制，可以安装 gcc、bash、make、git 等常用软件，只不过版本都很老。

## VirtualBox

测试了一下，在 VirtualBox 7.0.6 中，可以正常安装 SCO OpenServer 5，不需要额外的设置，按照上面一样的方法进行安装即可，鼠标选择 PS/2 Microsoft Mouse，和 QEMU 一样有移动距离不对的情况。安装完，把硬盘启动顺序调到前面，重启即可。

网卡的话，照常 `netconfig`，然后添加 AMD PCNet 网卡即可。

## 参考文档

本博客参考了以下文档中的命令：

- <https://virtuallyfun.com/2020/11/03/fun-with-openserver-and-merge/>