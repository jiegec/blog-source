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

DRAM 有很多参数，以服务器上的内存 [MTA36ASF2G72PZ-2G3A3](https://in.micron.com/products/dram-modules/rdimm/part-catalog/mta36asf2g72pz-2g3) 为例子：

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

再举一个 FPGA 开发板上内存的例子：[MT40A512M16LY-075E](https://www.micron.com/products/dram/ddr4-sdram/part-catalog/mt40a512m16ly-075)，参数如下：

1. Data Rate: 2666 MT/s, Clock Frequency: 1333 MHz, tCK=0.750ns=750ps
2. Target CL-nRCD-nRP: 18-18-18
3. tAA(Internal READ command to first data)=`13.50ns(=18*0.750)`
4. tRCD(ACTIVATE to internal READ or WRITE delay time)=`13.50ns(=18*0.750)`
5. tRP(PRECHARGE command period)=`13.50ns(=18*0.750)`
6. tRAS(ACTIVATE-to-PRECHARGE command period)=32ns
7. 512 Meg x 16
8. Number of bank groups: 2
9. Bank count per group: 4
10. Row addressing: 64K
11. Column addressing: 1K
12. Page size: 2KB=2K*16b

总大小：`2*4*64K*1K*16=1GB`。这个开发板用了 5 个 DRAM 芯片，只采用了其中的 4.5 个芯片：最后一个芯片只用了 8 位数据，这样就是 `4.5*16=72` 位的数据线，对应 64 位+ECC。

## 时序

可以看到，上面的 DRAM Datasheet 里提到了三个时序参数：

1. CL=17: CAS Latency，从发送读请求到第一个数据的延迟周期数
2. RCD=17: ACT to internal read or write delay time，表示从 ACT 到读/写需要的延迟周期数
3. RP=17: Row Precharge Time，表示 Precharge 后需要延迟周期数

如果第一次访问一个 Row 中的数据，并且之前没有已经打开的 Row，那么要执行 ACT 和 RD 命令，需要的周期数是 RCD+CL；如果之前已经有打开了的 Row，那么要执行 PRE，ACT 和 RD 命令，需要的周期数是 RP+RCD+CL。但如果是连续访问，虽然还需要 CL 的延迟，但是可以流水线起来，充分利用 DDR 的带宽。

如果把这个换算到 CPU 角度的内存访问延迟的话，如果每次访问都是最坏情况，那么需要 17+17+17=51 个 DRAM 时钟周期，考虑 DRAM 时钟是 1200MHz，那就是 42.5ns，这个相当于是 DRAM 内部的延迟，实际上测得的是 100ns 左右。

更严格来说，读延迟 READ Latency = AL + CL + PL，其中 AL 和 PL 是可以配置的，CL 是固有的，所以简单可以认为 READ Latency = CL。同理 WRITE Latency = AL + CWL + PL，可以简单认为 WRITE Latency = CWL。CWL 也是可以配置的，不同的 DDR 速率对应不同的 CWL，范围从 1600 MT/s 的 CWL=9 到 3200 MT/s 的 CWL=20，具体见 JESD79-4B 标准的 Table 7 CWL (CAS Write Latency)。


## 刷新

DRAM 的一个特点是需要定期刷新。有一个参数 tREFI，表示刷新的时间周期。在刷新之前，所有的 bank 都需要 Precharge 完成并等待 RP 的时间，这时候所有的 Bank 都是空闲的，再执行 REF(Refresh) 命令。等待 tRFC(Refresh Cycle) 时间后，可以继续正常使用。

为了更好的性能，DDR4 标准允许推迟一定次数的刷新，但是要在之后补充，保证平均下来依然满足每过 tREFI 时间至少一次刷新。

## 地址映射

如果研究 DRAM 内存控制器，比如 [FPGA 上的 MIG](https://www.xilinx.com/support/documentation/ip_documentation/ultrascale_memory_ip/v1_4/pg150-ultrascale-memory-ip.pdf)，可以发现它可以配置不同的地址映射方式，例如：

- ROW_COLUMN_BANK
- ROW_BANK_COLUMN
- BANK_ROW_COLUMN
- ROW_COLUMN_LRANK_BANK
- ROW_LRANK_COLUMN_BANK
- ROW_COLUMN_BANK_INTLV

就是将地址的不同部分映射到 DRAM 的几个地址：Row，Column，Bank。可以想象，不同的地址映射方式针对不同的访存模式会有不同的性能。对于连续的内存访问，ROW_COLUMN_BANK 方式是比较适合的，因为连续的访问会分布到不同的 Bank 上，这样性能就会更好。

此外，如果访问会连续命中同一个 Page，那么直接读写即可；反之如果每次读写几乎都不会命中同一个 Page，那么可以设置 Auto Precharge，即读写以后自动 Precharge，减少了下一次访问前因为 Row 不同导致的 PRE 命令。一个思路是在对每个 Page 的最后一次访问采用 Auto Precharge。