---
layout: post
date: 2018-09-14 23:57:00 +0800
tags: [virtualbox,macos]
category: os
title: 在 macOS 的 VirtualBox 上从 USB 启动
---

做了一个 Windows 10 安装 U 盘，想测试一下能不能启动，于是想用 VirtualBox 起一个虚拟机。但是发现，一般情况下要从 ISO 或者把 U 盘克隆成一个 vdi/vmdk etc 再启动。不过找到了 Cem Arslan 的 [VirtualBox - Booting From USB (MAC)](https://www.linkedin.com/pulse/virtualbox-booting-from-usb-mac-cem-arslan) 实验了一下，确实可以用，以 `/dev/disk2` 为例方法如下：

```shell
$ diskutil unmountDisk /dev/disk2
$ sudo chown $(whoami) /dev/disk2
$ VBoxManage internalcommands createrawvmdk -filename PATH_TO_VMDK -rawdisk /dev/disk2
$ # Now boot from VirtualBox
```

对于其它平台，可以参考 Tu Nguyen 的 [How to boot from USB in VirtualBox](https://www.aioboot.com/en/boot-from-usb-in-virtualbox/) 。

研究了一下生成的 vmdk 文件，大概是这样的：

```
# Disk DescriptorFile
version=1
CID=12345678
parentCID=ffffffff
createType="fullDevice"

# Extent description
RW 12345678 FLAT "/dev/disk2" 0

# The disk Data Base 
#DDB

ddb.virtualHWVersion = "4"
ddb.adapterType="ide"
ddb.geometry.cylinders="1234"
ddb.geometry.heads="1234"
ddb.geometry.sectors="1234"
ddb.uuid.image="12341234-1234-1234-1234-123412341234"
ddb.uuid.parent="00000000-0000-0000-0000-000000000000"
ddb.uuid.modification="00000000-0000-0000-0000-000000000000"
ddb.uuid.parentmodification="00000000-0000-0000-0000-000000000000"
ddb.geometry.biosCylinders="1234"
ddb.geometry.biosHeads="1234"
ddb.geometry.biosSectors="1234"
```

