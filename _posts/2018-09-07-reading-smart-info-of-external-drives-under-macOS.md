---
layout: post
date: 2018-09-07 10:20:00 +0800
tags: [smart,macos,smartmontools,kext]
category: hardware
title: 在 macOS 上读取移动硬盘的 S.M.A.R.T. 信息
---

之前想看看自己各个盘的情况，但是发现只能看电脑内置的 SSD 的 S.M.A.R.T 信息，而移动硬盘的都显示：

```
$ smartctl -a /dev/disk2
smartctl 6.6 2017-11-05 r4594 [Darwin 17.7.0 x86_64] (local build)
Copyright (C) 2002-17, Bruce Allen, Christian Franke, www.smartmontools.org

/dev/disk2: Unable to detect device type
Please specify device type with the -d option.

Use smartctl -h to get a usage summary
```

一开始我怀疑是个别盘不支持，但换了几个盘都不能工作，问题应该出现在了 USB 上。查了下资料，果然如此。根据 [USB devices and smartmontools](https://www.smartmontools.org/wiki/USB) ，获取 S.M.A.R.T 信息需要直接发送 ATA 命令，但是由于经过了 USB ，于是需要进行一个转换，导致无法直接发送 ATA 命令。这个问题自然是有解决方案，大概就是直接把 ATA 命令发送过去（pass-through）。上面这个地址里写到，如果需要在 macOS 上使用，需要安装一个内核驱动。可以找到，源码在 [kasbert/OS-X-SAT-SMART-Driver](https://github.com/kasbert/OS-X-SAT-SMART-Driver) 并且有一个带签名的安装包在 [External USB / FireWire drive diagnostics support](https://binaryfruit.com/drivedx/usb-drive-support) 中可以下载。丢到 VirusTotal 上没查出问题，用 v0.8 版本安装好后就成功地读取到了移动硬盘的 S.M.A.R.T 信息了。

然后我又简单研究了一下各个 S.M.A.R.T 各个值的含义是什么。 `VALUE` 代表当前的值， `WORST` 代表目前检测到的最差的值， `THRESH` 代表损坏阈值。这些值都是从 `RAW_VALUE` 进行计算后归一化而来。然后 `TYPE` 分为两种，一是 `Pre-fail` ，代表如果这一项的值小于阈值，代表这个机器很危险了，赶紧拷数据丢掉吧。二是 `Old_age` ，代表如果这一项小于阈值，代表这个机器比较老了，但还没坏。真正要看是否坏了，可以看 `When_Failed` 一栏。
