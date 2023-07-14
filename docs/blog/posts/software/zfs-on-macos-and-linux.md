---
layout: post
date: 2018-11-26
tags: [linux,zfs,macos,timemachine,backup]
category: software
title: Mac 上安装 Arch Linux，ZFS 真香
---

最近在 Mac 上装了 Arch Linux，按照 [Mac - Arch Linux Wiki](https://wiki.archlinux.org/index.php/Mac) 一路一路走，创建单独的一个 EFI 分区给 Arch Linux 放 GRUB 和内核，一个 ext4 作为根分区。由于 Arch ISO 不支持 Broadcom 的无线网卡，于是先拿 Apple Ethernet Adapter 连到路由器上装机。然后把一些需要的驱动装上了，桌面用的 KDE Plasma，Trackpad 用的 xf86-input-mtrack-git，HiDPI 设置为 2x Scale，各种体验都还可以，就是 Wi-Fi 的 802.1X 没配置好，然后 kwalletd5 老是崩没找到原因。常见的应用除了微信基本都有，也终于可以体验 Steam Play，利用 Proton 在 Linux 上跑一些只支持 Windows 的游戏，不过我已经很少玩游戏了。

然后我就想，怎么做 macOS 和 Linux 之间的文件共享。典型的操作可能是 exFAT，但是作为数据盘的话，这还是不大适合。或者就直接用 ext4，配合 extFS For Mac by Paragon 使用，也可以，最后我选择了 ZFS。

在 macOS 上安装 [OpenZFS on OSX](https://openzfsonosx.org/) ，在 Linux 上安装 [ZFS on Linux](https://zfsonlinux.org/) 。具体命令就是：

```shell
$ brew cask install openzfs # macOS
$ yay zfs-dkms-git # Arch Linux
```

由于硬盘空间所限，我只用了一个分区作为 vdev，没有采用 mirror、raidz 等方案。我首先在 macOS 上创建了一个 zpool，参考 [Creating a pool - OpenZFS on OSX](https://openzfsonosx.org/wiki/Zpool#Creating_a_pool) ：

```shell
$ sudo zpool create -f -o ashift=13 Data diskxsy
```

此时应该能够看到 /Volumes/Data 上已经挂载了一个 ZFS Dataset。我采用 [cbreak-black/ZetaWatch](https://github.com/cbreak-black/ZetaWatch) 在菜单栏里查看 ZFS 信息。此时回到 Arch Linux 上，通过 `zfs import` 可以找到并且挂载这个 ZFS Dataset 到 `/Data` 处。

我还尝试创建了一个加密的 ZFS Dataset，对加密的部分的粒度控制可以很细。另外，我参考 [Time Machine Backups - OpenZFS on OSX](https://openzfsonosx.org/wiki/Time_Machine_Backups) 也在移动硬盘上划出一个新的分区作为 ZFS，在上面创建了一个加密的 Sparse Bundle，把它作为 Time Machine 的目标。之后还会尝试一下 `zfs send` 作为替代的备份方案。