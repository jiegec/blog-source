---
layout: post
date: 2021-12-12 15:06:00 +0800
tags: [dram,ddr]
category: hardware
title: DRAM 分析
---

## 参考文档

- Memory systems: Cache, DRAM & Disk
- [译文： DDR4 SDRAM - Understanding the Basics（上）](https://zhuanlan.zhihu.com/p/262052220)
- [译文： DDR4 SDRAM - Understanding the Basics（下）](https://zhuanlan.zhihu.com/p/263080272)
- [JEDEC STANDARD DDR4 SDRAM JESD79-4B](http://www.softnology.biz/pdf/JESD79-4B.pdf)

## DRAM 是如何组织的

DRAM 分成很多层次：Bank Group，Bank，Row，Column，从大到小，容量也是各级别的乘积。

举例子：

- 4 Bank Group
- 4 Bank per Bank Group
- 32,768 Row per Bank
- 1024 Column per Row
- 4 Bits per Column

那么总大小就是 `4*4*32768*1024*4=2 Gb`。

## 访问模式

DRAM 的访问模式决定了访问内存的实际带宽。对于每次访问，需要这样的操作：

1. 用 ACT(Bank Activate) 命令打开某个 Bank Group 下面的某个 Bank 的某个 Row，此时整个 Row 的数据都会复制到 Sense Amplifier 中。这一步叫做 RAS（Row Address Strobe）
2. 用 RD(Read)/WR(Write) 命令按照 Column 访问数据。这一步叫做 CAS（Column Address Strobe）。
3. 在访问其他 Row 之前，需要用 PRE(Single Bank Precharge) 命令将 Sense Amplifier 中整个 Row 的数据写回 Row 中。

可以看到，如果访问连续的地址，就可以省下 ACT 命令的时间，可以连续的进行 RD/WR 命令操作。

除了显式 PRE 以外，还可以在某次读写之后自动进行 PRE：WRA(Write with Auto-Precharge) 和 RDA(Read with Auto-Precharge)。

总结一下上面提到的六种命令：

1. ACT: Bank Activate，激活一个 Row，用于接下来的访问
2. PRE: Single Bank Precharge，与 ACT 是逆操作，解除 Row 的激活状态
3. RD: Read，读取当前 Row 的某个 Column 数据
4. RDA: Read with Auto-Precharge，读取后执行 Precharge
5. WR: Write，写入当前 Row 的某个 Column 数据
6. WRA: Write with Auto-Precharge，写入后执行 Precharge

除此之外，还有一些常用命令：

1. REF: Refresh，需要定期执行，保证 DRAM 数据不会丢失。

## 参数

DRAM 有很多参数，以 [MTA36ASF2G72PZ-2G3A3](https://in.micron.com/products/dram-modules/rdimm/part-catalog/mta36asf2g72pz-2g3) 为例子：

- 16GB 容量，DDR4 SDRAM RDIMM
- PC4-2400
- Row address: 64K A[15:0]
- Column address: 1K A[9:0]
- Device bank group address: 4 BG[1:0]
- Device bank address per group: 4 BA[1:0]
- Device configuration: 4Gb (1Gig x 4), 16 banks
- Module rank address: 2 CS_n[1:0]
- Configuration: 2Gig x 72
- Module Bandwidth: 19.2 GB/s=2400 MT/s * 8B/T
- Memory Clock: 0.83ns(1200 MHz)
- Data Rate: 2400 MT/s
- Clock Cycles: CL-nRCD-nRP = 17-17-17

容量：每个 DRAM 颗粒 `64K*1K*4*4*4=4Gb`，不考虑 ECC，一共有 `16*2=32` 个这样的颗粒，实际容量是 16 GB。32 个颗粒分为两组，每组 16 个颗粒，两组之间通过 CS_n 片选信号区分。每组 16 个颗粒，每个颗粒 4 位 DQ 数据信号，合并起来就是 64 位，如果考虑 ECC 就是 72 位。

## 时序

可以看到，上面的 DRAM Datasheet 里提到了三个时序参数：

1. CL=17: CAS Latency，从发送读请求到第一个数据的延迟周期数
2. RCD=17: RAS Latency，ACT to internal read or write delay time，表示从 ACT 到读/写需要的延迟周期数
3. RP=17: Row Precharge Time，表示 Precharge 后需要延迟周期数

如果第一次访问一个 Row 中的数据，并且之前没有已经打开的 Row，那么要执行命令 ACT 和 RD，需要的周期数是 RCD+CL；如果之前已经有打开了的 Row，那么要执行命令 PRE，ACT 和 RD，需要的周期数是 RP+RCD+CL。但如果是连续访问，虽然还需要 CL 的延迟，但是可以流水线起来，充分利用 DDR 的带宽。
