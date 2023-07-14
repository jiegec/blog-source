---
layout: post
date: 2020-01-05
tags: [linux,wifi,tplink,rtl8822bu,dkms]
category: system
title: TP-Link Archer T4U V3 Linux 驱动安装
---

之前因为 MacBookPro 内置的 Wi-Fi 总是有问题，就找了个 USB 的无线网卡：TP-Link Archer T4U V3（VID：2357，PID：0115），这个网卡也没有主线的驱动，在网上找到了现成的驱动：[cilynx/rtl88x2bu](https://github.com/cilynx/rtl88x2bu)，按照 README 用 DKMS 安装即可，实测可用。

Update: Linux 6.2+ 已经支持，见 <https://linux-hardware.org/?id=usb:2357-0115>