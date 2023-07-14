---
layout: post
date: 2023-02-26
tags: [netgear,wifi,wireless,dongle,usb,linux]
categories:
    - hardware
title: 在 Linux 上使用 Netgear A6210 USB 无线网卡
---

## 背景

最近要让一台 Linux 机器连接无线网，所以要买一个对 Linux 支持比较好的 USB 无线网卡。以前曾经用过一些 USB 无线网卡，但对 Linux 的支持大多不好，要么是需要 out of tree module，要么就忽然不能工作。因此前期的调研十分重要。

## 挑选 USB 无线网卡

在调研的时候，发现了 [morrownr/USB-WiFi](https://github.com/morrownr/USB-WiFi) 仓库，里面总结了一些 Linux 支持比较好的 USB 无线网卡，由于是外国人写的，所以里面很多型号在国内都买不到，但实际上 USB 无线网卡的芯片组一般就是那些，所以需要先确定芯片组，再根据芯片组找对应的 USB 无线网卡。

开发用于 USB 无线网卡的厂商常见的是：Mediatek（2011 年 MediaTek 收购了 Ralink）和 Realtek。国内直接买到的 USB 无线网卡大部分是 Realtek，但是 Realtek 的 Linux 驱动很长一段时间都是 out of tree 的状态，只有比较新的一些芯片组有内核支持，而 Mediatek 系列的芯片内核支持较好，缺点是比较贵。下面从上面的仓库里摘录了一些芯片组的 Linux 内核支持情况：

| Chipset    | Linux | Commit                                                                                                                                                                   | 802.11   | USB | Bluetooth | Package | Links                                                                                                                                                                                        |
|------------|-------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|-----|-----------|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| MT7601u    | 4.2+  | [mt7601u](https://github.com/torvalds/linux/commit/c869f77d6abb5d5f9f2f1a661d5c53862a9cad34)                                                                             | b/g/n    | 2.0 | N/A       |         | [Official](https://www.mediatek.cn/products/broadband-wifi/mt7601u)                                                                                                                          |
| MT7610u    | 4.19+ | [mt76x0u](https://github.com/torvalds/linux/commit/ff69c75ee5392320ab3a8dd01db46d3cd097eb46)                                                                             | b/g/n/ac | 2.0 | N/A       |         | [Official](https://www.mediatek.cn/products/broadband-wifi/mt7610u)                                                                                                                          |
| MT7612u    | 4.19+ | [mt76x2u](https://github.com/torvalds/linux/commit/ee676cd5017c5f71b8aac1f2d1016ba0f6e4f348)                                                                             | b/g/n/ac | 3.0 | 4.0       |         | [Official](https://www.mediatek.cn/products/broadband-wifi/mt7612u)                                                                                                                          |
| MT7662u    |       |                                                                                                                                                                          | b/g/n/ac | 3.0 | 4.0       |         | [Official](https://www.mediatek.cn/products/broadband-wifi/mt7662u)                                                                                                                          |
| MT7921au   |       |                                                                                                                                                                          |          |     |           |         |                                                                                                                                                                                              |
| MT7922u    |       |                                                                                                                                                                          |          |     |           |         |                                                                                                                                                                                              |
| RTL8188eus | 3.12+ | rtl8188eu/r8188eu/[rtl8xxxu](https://github.com/torvalds/linux/commit/3dfb8e844fa30cceb4b810613e2c35f628eb3e70) [LKDDB](https://cateee.net/lkddb/web-lkddb/R8188EU.html) | b/g/n    | 2.0 | N/A       | QFN-46  | [Official](https://www.realtek.com/en/products/communications-network-ics/item/rtl8188eus)                                                                                                   |
| RTL8188gu  | N/A   | [3rd party](https://github.com/McMCCRU/rtl8188gu) [patch](https://patchwork.kernel.org/project/linux-wireless/patch/5a9a264d-a59b-0d91-04f0-e5b38e6aaea0@gmail.com/)     |          |     |           |         |                                                                                                                                                                                              |
| RTL8723bu  | 4.6+  | [rtl8xxxu](https://github.com/torvalds/linux/commit/35a741febfae3cfc2a27d3b4935e255585ecfd81) [LKDDB](https://cateee.net/lkddb/web-lkddb/RTL8XXXU.html)                  | b/g/n    | 2.0 | 4.0       | QFN-56  | [USB 0bda:b720](https://linux-hardware.org/?id=usb:0bda-b720)，[Official](https://www.realtek.com/en/products/communications-network-ics/item/rtl8723bu)                                     |
| RTL8723du  | 6.2+  | [rtw88](https://github.com/torvalds/linux/commit/87caeef032fc3921bc866ad7becb6ed51aa8b27b) [LKDDB](https://cateee.net/lkddb/web-lkddb/RTW88_8723DU.html)                 | b/g/n    |     | 4.2       | QFN-48  | [Official](https://www.realtek.com/en/products/communications-network-ics/item/rtl8723du)                                                                                                    |
| RTL8811au  | N/A   | [3rd party](https://docs.alfa.com.tw/Support/Linux/RTL8811AU/)                                                                                                           | b/g/n/ac | 2.0 | N/A       | QFN-56  | [Official](https://www.realtek.com/en/products/communications-network-ics/item/rtl8811au) [Datasheet](https://datasheet.lcsc.com/lcsc/2205121200_Realtek-Semicon-RTL8811AU-CG_C3013607.pdf)  |
| RTL8821au  | N/A   |                                                                                                                                                                          | b/g/n/ac | 2.0 | 4.0       | QFN-56  | [Official](https://www.realtek.com/en/products/communications-network-ics/item/rtl8821au)                                                                                                    |
| RTL8811cu  | 6.2+  | [rtw88](https://github.com/torvalds/linux/commit/aff5ffd718de23cb8603f2e229204670e2644334) [LKDDB](https://cateee.net/lkddb/web-lkddb/RTW88_8821CU.html)                 | b/g/n/ac | 2.0 | N/A       | QFN-56  | [Official](https://www.realtek.com/en/products/communications-network-ics/item/rtl8811cu)，[Datasheet](https://datasheet.lcsc.com/lcsc/2302141730_Realtek-Semicon-RTL8811CU-CG_C2687136.pdf) |
| RTL8821cu  | 6.2+  | [rtw88](https://github.com/torvalds/linux/commit/aff5ffd718de23cb8603f2e229204670e2644334) [LKDDB](https://cateee.net/lkddb/web-lkddb/RTW88_8821CU.html)                 | b/g/n/ac | 2.0 | 4.2       | QFN-56  | [Official](https://www.realtek.com/en/products/communications-network-ics/item/rtl8821cu)，[Datasheet](https://datasheet.lcsc.com/lcsc/2202211630_Realtek-Semicon-RTL8821CU-CG_C2761145.pdf) |
| RTL8812au  | N/A   | [3rd party](https://docs.alfa.com.tw/Support/Linux/RTL8812AU/)                                                                                                           | b/g/n/ac | 3.0 | N/A       | QFN-76  | [Official](https://www.realtek.com/en/products/communications-network-ics/item/rtl8812au)                                                                                                    |
| RTL8812bu  | 6.2+  | [rtw88](https://github.com/torvalds/linux/commit/45794099f5e1d7abc5eb07e6eec7e1e5c6cb540d) [LKDDB](https://cateee.net/lkddb/web-lkddb/RTW88_8822BU.html)                 | b/g/n/ac | 3.0 | N/A       | TFBGA   | [Official](https://www.realtek.com/en/products/communications-network-ics/item/rtl8812bu)                                                                                                    |
| RTL8822bu  | 6.2+  | [rtw88](https://github.com/torvalds/linux/commit/45794099f5e1d7abc5eb07e6eec7e1e5c6cb540d) [LKDDB](https://cateee.net/lkddb/web-lkddb/RTW88_8822BU.html)                 | b/g/n/ac | 3.0 | 4.1       | TFBGA   | [Official](https://www.realtek.com/en/products/communications-network-ics/item/rtl8822bu)，[Datasheet](https://datasheet.lcsc.com/lcsc/2204071230_Realtek-Semicon-RTL8822BU-CG_C2803244.pdf) |
| RTL8822cu  | 6.2+  | [rtw88](https://github.com/torvalds/linux/commit/07cef03b8d44dee7488de3d1585387e603c78676) [LKDDB](https://cateee.net/lkddb/web-lkddb/RTW88_8822CU.html)                 |          |     |           |         |                                                                                                                                                                                              |
| RTL8814au  | N/A   | [3rd party](https://docs.alfa.com.tw/Support/Linux/RTL8814AU/)                                                                                                           | b/g/n/ac | 3.0 | N/A       | QFN-128 | [Official](https://www.realtek.com/en/products/communications-network-ics/item/rtl8814au)                                                                                                    |

可以观察到规律：Realtek 的产品型号中，881x 和 882x 有对应的关系，前者不带蓝牙，后者带。最后一位数字越大，则越新。

在内核源码中可以找到一些使用这个芯片组的 USB 无线网卡型号，但需要注意的是，有时候同样的型号，有 v1v2v3 之分，可能用的是不同的芯片组，购买前需要问清楚。

购买的时候，考虑芯片组的支持情况，Linux 内核版本等等因素，我最后购买了 Netgeat A6210 认证翻新版，使用芯片组 MT7612u，价格是 138 人民币。

## 使用

使用的 Linux 内核版本是 5.10，插上 USB 无线网卡即可使用：

```shell
$ lsusb
Bus 002 Device 002: ID 0846:9053 NetGear, Inc. A6210
```

在使用 iwd 的连接无线网的时候，还出现一个小插曲，就是 iwd 遇到很长的中文 SSID 时会崩溃，于是我进行了修复，并且发送给 iwd mailing list（[link](https://lore.kernel.org/iwd/20230226062526.3115588-1-c@jia.je/T/#u)），并等待修复。原理很简单，一是打印十六进制字符的时候没有考虑符号，二是缺少了缓冲区溢出的检查。

## Realtek 上游 Linux 内核驱动支持

归功于 Sascha Hauer <s.hauer@pengutronix.de> 老哥，最近 Linux 上游增加了不少对 realtek 网卡的支持，因此只要系统足够新，realtek 的网卡也值得考虑，如：

- RTL8723du: Linux 6.2+
- RTL8811cu: Linux 6.2+
- RTL8821cu: Linux 6.2+
- RTL8812bu: Linux 6.2+
- RTL8822bu: Linux 6.2+
- RTL8822cu: Linux 6.2+

RTL8188gu 也有正在 review 的 [patch](https://patchwork.kernel.org/project/linux-wireless/patch/5a9a264d-a59b-0d91-04f0-e5b38e6aaea0@gmail.com/)。经过我的测试也是工作的。