---
layout: post
date: 2021-03-29 08:30:00 +0800
tags: [hpe,ilo,ilo4,ipmi,ipmitool]
category: system
title: 通过 ipmitool 配置 iLO 4 管理端口
---

ipmitool 自带了对 iDRAC 的支持，可以通过 `ipmitool delloem` 设置 iDRAC 的管理端口。但是对 iLO 的支持并没有实现。研究了一番，找到了通过 raw command 配置 iLO 4 管理端口的方法。

[这篇文章](https://computercheese.blogspot.com/2013/05/ipmi-lan-commands.html) 讲述了 `ipmitool lan` 命令实际会发送的命令：

读取配置：

```shell
$ ipmitool raw 0x0c 0x02 CHANNEL KEY SET BLOCK
```

一般来说 SET 和 BLOCK 都是 0。KEY 的常见取值：

- 3: IP 地址
- 4: IP 地址来源
- 5: MAC 地址
- 6: 子网掩码
- 12: 默认网关

返回的数据中，第一个字节忽略，剩下的就是数据了。

写入配置：

```shell
$ ipmitool raw 0x0c 0x01 CHANNEL KEY DATA...
```

知道如何读取配置后，接下来就是找到 iLO 4 配置 NIC 的地方了。一番搜索，找到了 [HPE iLO IPMI User Guide](https://support.hpe.com/hpesc/public/docDisplay?docId=c04530505&docLocale=en_US)。在第 101 页，可以找到一个用于配置 iLO NIC 选择的设置：

    Index: 224
    iLO Dedicated/Shared NIC Selection.
    data 3:
    • Selected iLO NIC.
    ◦ 0h = iLO Dedicated NIC is selected.
    ◦ 1h = iLO Shared NIC is selected.
    ◦ All others = reserved
    • To switch to another iLO NIC:
    1. Write this (and possibly parameter 197) to the desired NIC selection
    2. Configure all other relevant network parameters for the desin
    3. Reset iLO. The desired NIC will be in use after iLO reset.
    • When writing changes to data 3, NIC selection:
    ◦ data 1 must be AAh
    ◦ data 2 must be 55h
    ◦ data 4 must be FFh

有这样的信息以后，可以通过下面的命令来设置 Shared NIC：

```shell
$ ipmitool raw 0x0c 0x01 0x01 224 0xAA 0x55 0x01 0xFF
```

再读出来 224，发现它的 data 4 表示 `iLO reset needed for some settings changes that have been made`。于是，执行 `ipmitool mc reset warm` 之后，就可以看到 NIC 选择已经更新：

```shell
$ ipmitool raw 0x0c 0x02 0x01 197 0x00 0x00
11 02 01 02
```

数据分别表示：

- 0x02: Shared NIC Selection = ALOM
- 0x01: Shared NIC Port Number = Port 1
- 0x02: Platform supports ALOM shared NIC

如果想要的端口和默认选择不一样，可以写入 197 来更新。详见上面的文档链接。
