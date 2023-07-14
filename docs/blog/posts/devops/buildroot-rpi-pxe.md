---
layout: post
date: 2020-09-12
tags: [buildroot,pxe,rpi,rpi4]
category: devops
title: 在 Rpi4 上运行 buildroot
---

## 背景

需要给 rpi 配置一个 pxe 的最小环境，在上一篇博文了提到可以用 alpine，但发现有一些不好用的地方，所以试了试 buildroot。

## PXE 设置和路由器设置

见“在 Rpi4 上运行 Alpine Linux”文章。

## Buildroot 配置

下载 buildroot：

```bash
> wget https://buildroot.org/downloads/buildroot-2020.08.tar.gz
> unar buildroot-2020.08.tar.gz
> cd buildroot-2020.08
> make raspberrypi4_64_defconfig
```

然后运行 `make menuconfig` ，在 `Filesystem images` 中打开 initramfs，并设置 cpio 压缩为 gz。然后直接编译：

```bash
> make -j4
$ ls -al target/images
bcm2711-rpi-4-b.dtb*  boot.vfat  Image  rootfs.cpio  rootfs.cpio.gz  rootfs.ext2  rootfs.ext4@  rpi-firmware/  sdcard.img
```

接着，在一个单独的目录里，把这些文件整理一下

```bash
> cd ~/rpi-buildroot
> cp -r ~/buildroot-2020.08/output/images/rpi-firmware/* .
> cp ~/buildroot-2020.08/output/images/bcm2711-rpi-4-b.dtb .
> cp ~/buildroot-2020.08/output/images/Image .
> cp ~/buildroot-2020.08/output/images/rootfs.cpio.gz .
> # edit cmdline.txt: remove root= and rootwait
> # edit config.txt: uncomment initramfs rootfs.cpio.gz line
# ls
bcm2711-rpi-4-b.dtb*  cmdline.txt  config.txt  fixup.dat  Image  overlays/  rootfs.cpio.gz  start.elf
```

最后开启 TFTP 服务器即可：

```bash
> sudo python3 -m py3tftp -p 69
```

## 树莓派启动

连接树莓派的串口，用 115200 Baudrate 打开，可以看到启动信息：

```
PM_RSTS: 0x00001000
RPi: BOOTLOADER release VERSION:a5e1b95f DATE: Apr 16 2020 TIME: 18:11:29 BOOTMODE: 0x00000006 part: 0 BUILD_TIMESTAMP=1587057086 0xa049cc2f 0x00c03111
uSD voltage 3.3V
... 
Welcome to Buildroot
buildroot login: root
#
```

默认用户是 root，没有密码。