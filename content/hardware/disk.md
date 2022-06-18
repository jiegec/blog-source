---
layout: post
date: 2021-05-06T11:37:00+08:00
tags: [disk,pcie,ahci,sata,sas,nvme]
category: hardware
title: 硬盘相关的概念
---

## ATA

[ATA](https://en.wikipedia.org/wiki/Parallel_ATA) 定义了发送给硬盘的命令，[标准](https://people.freebsd.org/~imp/asiabsdcon2015/works/d2161r5-ATAATAPI_Command_Set_-_3.pdf)定义了命令:

- ech IDENTIFY DEVICE: 获取设备信息
- 25h READ DMA EXT: 读取扇区
- 35h WRITE DMA EXT: 写入扇区

ATA 同时也是接口，图片如下。ATA 前身是 IDE，现在 ATA 叫做 PATA。

![PATA Pin](https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/ATA_Plug.svg/600px-ATA_Plug.svg.png)

## AHCI

[AHCI](https://en.wikipedia.org/wiki/Advanced_Host_Controller_Interface) 可以简单理解为 PCIe <-> SATA 的转换器。AHCI 暴露为一个 PCIe 设备：

```shell
$ lspci -vv
00:1f.2 SATA controller: Intel Corporation C600/X79 series chipset 6-Port SATA AHCI Controller (rev 05)
        Kernel modules: ahci
```

处理器通过 IO port/MMIO 访问 AHCI，然后 AHCI HBA 连接到 SATA 设备。

## SATA

[SATA](https://en.wikipedia.org/wiki/Serial_ATA) 一般说的是接口。它一般分为两个部分，数据和电源。数据部分只有 7 个 pin，三个 GND 和两对差分线（A+A- B+B-），图片如下：

![SATA Data](https://upload.wikimedia.org/wikipedia/commons/e/ef/SATA_Data_Cable.jpg)

电源部分有 15 个 pin，有 GND 3.3V 5V 和 12V，图片如下：

![SATA Power](https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/SATA_power_cable.jpg/400px-SATA_power_cable.jpg)

常见的 SATA 盘有 2.5 英寸（small form factor, SFF）和 3.5 英寸（large form factor，LFF）两种规格。

## M.2

[M.2](https://en.wikipedia.org/wiki/M.2) 又称 NGFF，有不同的 key 类型。常见的是 B 和 M：

- B key: 12-19 notched, PCIe x2, SATA
- M key: 59-66 notched, PCIe x4, SATA

都有部分引脚的位置是空的：

![M.2](https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/M2_Edge_Connector_Keying.svg/620px-M2_Edge_Connector_Keying.svg.png)

在[这里](https://pinoutguide.com/HD/M.2_NGFF_connector_pinout.shtml)可以看到两种 key 的 pinout。

- B key: SATA pin B(41,43) A(47,49), PCIe x2 pin R1(29,31) T1(35,37) R0(41,43) T0(47,49), USB 3.0 pin TX(29, 31) RX(35,37)
- M key: SATA 同上, PCIe x4 pin R3(5,7) T3(11,13) R2(17,19) T2(23,25) Lane 0,1 同上

可以看到，SATA pin 和 PCIe 的两个 lane 在 B 和 M key 中是一样的，物理上也是可以兼容的。

因为支持 SATA 和 PCIe，就有下面三种可能的使用方式：

- PCIe -- AHCI HBA(Board) -- SATA(M.2) -- Disk: 传统方式，只不过物理接口从 SATA 变成了 M.2
- PCIe -- PCIe Device(M.2) -- Disk(AHCI)：硬盘实现了 AHCI 的接口，通过 PCIe 连接到 CPU
- PCIe -- PCIe Device(M.2) -- Disk(NVMe)：硬盘实现了 NVMe 的接口，通过 PCIe 连接到 CPU

![](https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/SATA_Express_interface.svg/620px-SATA_Express_interface.svg.png)

## SATA express

[SATA express](https://en.wikipedia.org/wiki/SATA_Express) 在 SATA 3.2 引入，它用的很少，被 U.2 取代。提供了 PCIe x2 或者 SATA x2。

## U.2

[U.2](https://en.wikipedia.org/wiki/U.2) 也叫 [SFF-8639](https://members.snia.org/document/dl/26489)。它和 [SATA express](https://en.wikipedia.org/wiki/SATA_Express) 接口一样，但提供了 PCIe x4 或者 SATA x2。详见 [pinout](https://pinoutguide.com/HD/U.2_SATA_connector_pinout.shtml)。

![U.2](https://www.delock.com/infothek/U.2-NVMe/images/teaser.jpg)

## 速度比较

不同的协议的速度如下：

- SATA 3.0: 6Gb/s(8b/10b, 4Gb/s uncoded)
- SAS-1: 3Gb/s
- SAS-2: 6Gb/s
- SAS-3: 12Gb/s
- SAS-4: 22.5Gb/s
- PCIe 3.0 x4: 32Gb/s(8GT/s, 128b/130b, 31.5 Gb/s uncoded)

更完整的可以看[List of interface bit rates](https://en.wikipedia.org/wiki/List_of_interface_bit_rates)。

[Intel SSD DC P4618 Series](https://ark.intel.com/content/www/us/en/ark/products/192574/intel-ssd-dc-p4618-series-6-4tb-1-2-height-pcie-3-1-x8-3d2-tlc.html) 读写速度可以达到 40~50 Gb/s，它采用的是 PCIe 3.0 x8(64Gb/s) NVMe。

[Intel SSD 545s Series](https://ark.intel.com/content/www/us/en/ark/products/125024/intel-ssd-545s-series-1-024tb-2-5in-sata-6gb-s-3d2-tlc.html) 读写速度约 4Gb/s，采用的是 SATA 3.0 6Gb/s。

[SAMSUNG 970 EVO](https://www.samsung.com/semiconductor/minisite/ssd/product/consumer/970evo/) 读写速度 20~30 Gb/s，它采用的是 PCIe 3.0 x4(32Gb/s) NVMe。