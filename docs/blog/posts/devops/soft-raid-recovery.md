---
layout: post
date: 2026-01-21
tags: [raid,md,mdadm,linux,soft-raid]
categories:
    - devops
---

# 记一次软 RAID1 坏盘的恢复过程

## 背景

最近遇到一个运维场景，两个 SATA 盘组了一个 RAID1，Linux 的根系统也在上面，启动时能进内核，但是内核一直在报错 `link is too slow to respond, please be patient` 以及 `COMRESET failed (errno=-16)`。下面记录一下故障排查以及恢复的过程。

<!-- more -->

## 恢复过程

考虑到 Linux 系统也在 RAID1 上面，所以找了另一台机器，接上两个 SATA 盘，然后观察到，其中一个盘直接无法识别，另一个盘可以正常访问，但它分区表里只有一个分区，参与到了 md 组的 RAID1 当中。遇到盘坏了又是 RAID，第一反应是买一个新盘，然后重建 RAID。但是一通询价，发现最近硬盘价格涨的比较多，所以先尝试如何单盘启动。由于是 UEFI 启动，推测 ESP 在已经坏的那个盘上面，好的盘上并没有 ESP，但它唯一的分区已经占满了整个空间，所以第一步是对 RAID 分区缩容，这就需要：

1. 首先用 `fsck -f /dev/md0 && resize2fs /dev/md0 newsize` 对根分区进行缩容
2. 用 `mdadm --grow --size=newsize /dev/md0` 对 RAID 进行缩容
3. 停止 RAID：`mdadm --stop /dev/md0`
4. 重新分区，缩小 RAID 分区大小：`cfdisk /dev/sda`
5. 重新启动 RAID，更新 device size：`mdadm --assemble --update=devicesize /dev/md0 /dev/sda1`

这些步骤完成以后，就可以在空余的空间里建 ESP 分区了：建分区，`mkfs.vfat`，挂载到 `/mnt/boot/efi`（假设 `/dev/sda1` 已经挂载到了 `/mnt`），接着 `arch-chroot /mnt`（或者手抄 [Archlinux Wiki](https://wiki.archlinux.org/title/Chroot#Using_chroot)），进去 `grub-install`，修改 `/etc/fstab`，重新 `update-grub`。

这个过程中，踩了一些小坑，比如：

1. 重启以后直接进 grub shell，没有菜单显示出来，后来发现是 UEFI 启动项里有之前的旧残留，导致 grub 没有能够正确加载 ESP 里面的 grub.cfg，如果在 grub shell 里手动 source 一下是正常的
2. 如果不更新 device size，那么 assemble 的时候会说 `does not have a valid v1.2 superblock` 报错，实际上就是它记录了旧的分区大小，和新的分区大小不匹配，此时要强制修改它
3. 最后买了个新盘，但是不够大：960GB vs 1TB，导致如果要重组 RAID1 还得再缩小一次已有的 RAID1 分区，之前缩小的时候只给 ESP 预留了足够的空间，但分区还不够小到能够在新盘里建一个相同大小的分区
