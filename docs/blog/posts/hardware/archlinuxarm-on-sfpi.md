---
layout: post
date: 2018-11-06
tags: [sfpi,saltedfishpi,dd,extfs,ext4]
categories:
    - hardware
title: 向咸鱼派写入 ArchlinuxARM
---

之前由于我的 macOS 上不知道为啥不能把我的 TF 卡设备放到我的虚拟机里，所以之前就没能刷 ArchLinuxARM 上去。今天我想到了一个方法，完成了这件时期：

```
$ wget https://mirrors.tuna.tsinghua.edu.cn/archlinuxarm/os/ArchLinuxARM-armv7-latest.tar.gz
$ dd if=/dev/zero of=archlinuxarm.img bs=1M count=1024
$ mkfs.ext4 archlinuxarm.img
$ sudo mkdir -p /mnt/archlinuxarm
$ sudo mount -o loop archlinuxarm.img /mnt/archlinuxarm
$ sudo bsdtar -xpf ArchLinuxARM-armv7-latest.tar.gz -C /mnt/archlinuxarm
$ sudo umount /mnt/archlinuxarm
```

这样就获得了一个 ext4 的 ArchlinuxARM 镜像。刚好解压出来不到 1G，所以开了 1G 的镜像刚好放得下。然后把 archlinuxarm.img 拷回 macOS，然后用 dd 写进去：

```
$ sudo dd if=archlinuxarm.img of=/dev/rdisk4s2 bs=1048576
```

这时候可以确认，我们确实是得到了一个正确的 ext4fs：

```
$ sudo /usr/local/opt/e2fsprogs/sbin/tune2fs -l /dev/disk4s2
```

不过，我们实际的分区大小可能不止 1G，所以可以修改一下大小：

```
$ sudo /usr/local/opt/e2fsprogs/sbin/resize2fs -p /dev/disk4s2
```

这样就成功地把 ArchlinuxARM 写进去了。默认的用户名和密码都是 root，可以成功通过串口登录。