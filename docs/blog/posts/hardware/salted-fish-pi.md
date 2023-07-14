---
layout: post
date: 2018-11-05
tags: [sfpi,saltedfishpi,uboot,linux,kernel,dts,devicetree]
categories:
    - hardware
---

# 咸鱼派的启动配置

最近刚拿到了一个[咸鱼派](https://github.com/sbc-fish/sfpi)的测试板子，准备自己把 U-Boot 和 Linux 内核这一套东西跑通，都用主线的东西，尽量减少魔改的部分。首先是编译 u-boot，我用的是现在的 master 分支的最新版 99431c1c：

```
$ # Archlinux
$ sudo pacman -Sy arm-none-eabi-gcc
$ make LicheePi_Zero_defconfig
$ make ARCH=arm CROSS_COMPILE=arm-none-eabi- -j24
```

这时候会得到一个 u-boot-sunxi-with-spl.bin 的文件。我们只要把它写到 SD 卡的 8192 偏移处，就可以把 U-Boot 跑起来了：

```
$ diskutil unmountDisk /dev/disk4
$ sudo dd if=u-boot-sunxi-with-spl.bin of=/dev/disk4 bs=1024 seek=8
```

接着我们做一下分区。我采用的是 MBR 分区，这样保证不会和 U-Boot 冲突。使用 fdisk 进行分区，我从 1M 处开始分了一个 10M 的 FAT-32 分区作为启动分区，然后之后都是 EXT4 的系统盘分区。接着就是编译内核。

我用的是八月份时候的 4.18.2 内核，虽然不是很新但也足够新了。一番调整内核参数后，得到了一个可用的内核，然后把 zImage 和 sun8i-v3s-licheepi-zero.dtb 都复制到刚才创建的 FAT-32 启动分区，然后进入 U-Boot 进行启动：

```
$ setenv bootcmd 'fatload mmc 0 0x41000000 zImage; fatload mmc 0 0x41800000 sun8i-v3s-licheepi-zero.dtb; setenv bootargs console=ttyS0,115200 root=/dev/mmcblk0p2 rw rootwait; bootz 0x41000000 - 0x41800000'
$ saveenv # optional
$ boot
```

这里一开始遇到了很多坑，比如一直看不到 console，这个是找了 [@gaoyichuan](https://github.com/gaoyichuan) 拿到的一份 Kernel Config 进行修改修好的。另一个是进去以后找不到 root，我先是搞了一个有 busybox 的 initrd，进去看发现是能找到 mmc 的，但是有延迟，那么添加上 rootwait 就好了。进去以后就差 rootfs。由于我缺少一个写 ext4 的工具，又发现手上有一个 Raspbian 的镜像，它里面也正好是两个分区，而且架构也同样是 armv7l，我就直接把它烧到 SD 卡中，把 U-Boot 写进去，然后往 boot 分区里写内核和 dtb，然后就成功进去，并且跑起来了。最喜感的就是，进去以后是个 pi@raspberrypi，实际上确是另一个东西。不过，只有当我 `apt update` 发现用了半小时的时候，我才想起来这其实是是一个嵌入式系统。。

进去以后发现，没有识别到网卡驱动。网上找了 LicheePi Zero 的一个解决方案，但是并不能用，还出现了神奇的 Kernel Oops，怀疑是内核版本太新的问题。我又找到 [@icenowy](https://github.com/icenowy) 的一个 [Patch](https://lore.kernel.org/patchwork/patch/884656/) ，它终于是解决了这个问题，成功地找到了网卡，并且愉快地 `ssh pi@raspberrypi.local` 。之后会在咸鱼派那边公布一下我们做的修改。

现在的想法是，把 HomeBridge 搭建到它上面，不过目前来看硬件资源有点紧张，放着会有点慢。可能还是用树莓派做这个事情比较合适。