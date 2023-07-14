---
layout: post
date: 2018-11-20
tags: [linux,usbip,raspi,sfpi]
categories:
    - software
title: USB/IP 实践
---

之前一直想玩 USB/IP，但是一直没有找俩 Linux 设备然后共享，今天终于尝试了一下，没有什么大问题。这次采用的设备是 Raspberri Pi 3 和 SaltedFish Pi。一开始尝试从后者向前者共享，但总是出现这个错误：

```
libusbip: error: udev_device_get_sysattr_value failed
usbip: error: open vhci_driver
```

然后我反过来做就好了，比较神奇。

主要过程如下：

- `pacman -S usbip` 安装用户态软件
- `systemctl enable --now usbipd` 启动 USB/IP 的端口监听 daemon
- `usbip list -l` 查看本地有哪些 USB 设备可以共享
- `usbip bind -b [BUS_ID]` 把指定的 USB 设备共享出去，其中 BUS_ID 从上个命令中查看
- `usbip list -r [IP]` 在另一个设备上查看这个设备共享的 USB 设备，可以看到许多信息
- `usbip attach -r [IP] -b [BUS_ID]` 把对方共享的 USB 设备 attach 到本地

效果：把一个 U 盘成功映射到了本地：

```
$ lsusb -t
/:  Bus 04.Port 1: Dev 1, Class=root_hub, Driver=vhci_hcd/8p, 480M
    |__ Port 1: Dev 2, If 0, Class=Mass Storage, Driver=usb-storage, 480M
$ lsblk
NAME        MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sda           8:0    1 14.9G  0 disk
`-sda1        8:1    1 14.9G  0 part /tmp/mnt
```

尝试 mount 什么的，也都没有问题。以后可以考虑把本地的 LicheeTang 通过这种方式穿透到远端，然后在远端用它的 IDE 进行编程。

UPDATE: LicheeTang 烧写有一些问题，直接 JTAG 写上去没有作用，但是 SPI Flash 是可以成功写入并且有作用的，虽然需要强制打断。感觉还是网络延迟导致了一些问题。
