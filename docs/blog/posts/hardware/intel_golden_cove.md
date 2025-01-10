---
layout: post
draft: true
date: 2025-01-10
tags: [cpu,intel,goldencove,alderlake,performance,uarch-review]
categories:
    - hardware
---

# Intel Golden Cove 微架构评测

## 背景

前段时间测试了 AMD/Apple/Qualcomm/ARM 的处理器的微架构，自然不能漏了 Intel。虽然 Intel 已经出了 Redwood Cove 和 Lion Cove，但手上没有设备，而且 Golden Cove 也是“相对比较成功”（“缩缸的是 Raptor Cove，和我 Golden Cove 有什么关系，虽然其实 Raptor Cove 是 Golden Cove Refresh”）的一代微架构，用在了 Alder Lake 和 Sapphire Rapids 上，因此就来分析它，后续有机会也会分析一下对应的 E 核架构 Gracemont。

<!-- more -->

## 官方信息

Intel 关于 Golden Cove 微架构有这些官方的信息：

- [Intel Alder Lake CPU Architectures](https://ieeexplore.ieee.org/document/9747991)
- [Alder Lake Architecture on Hot Chips 33](https://hc33.hotchips.org/assets/program/conference/day1/HC2021.C1.1%20Intel%20Efraim%20Rotem.pdf)
- [Sapphire Rapids on Hot Chips 33](https://hc33.hotchips.org/assets/program/conference/day1/HC2021.C1.4%20Intel%20Arijit.pdf)
- [Intel 64 and IA-32 Architectures Optimization Reference Manual Volume 1](https://www.intel.com/content/www/us/en/content-details/671488/intel-64-and-ia-32-architectures-optimization-reference-manual-volume-1.html)

## 现有评测

网上已经有较多针对 Golden Cove 微架构的评测和分析，建议阅读：

- [Popping the Hood on Golden Cove](https://chipsandcheese.com/2021/12/02/popping-the-hood-on-golden-cove/)
- [Golden Cove](https://en.wikipedia.org/wiki/Golden_Cove)
- [Golden Cove’s Vector Register File: Checking with Official (SPR) Data](https://chipsandcheese.com/2023/01/15/golden-coves-vector-register-file-checking-with-official-spr-data/)
- [4th Gen Intel Xeon Scalable Sapphire Rapids Leaps Forward](https://www.servethehome.com/4th-gen-intel-xeon-scalable-sapphire-rapids-leaps-forward/7/)
- [Intel Details Golden Cove: Next-Generation Big Core For Client and Server SoCs](https://fuse.wikichip.org/news/6111/intel-details-golden-cove-next-generation-big-core-for-client-and-server-socs/)
- [Sapphire Rapids: Golden Cove Hits Servers](https://chipsandcheese.com/2023/03/12/a-peek-at-sapphire-rapids/)
- [Golden Cove’s Lopsided Vector Register File](https://chipsandcheese.com/2022/12/25/golden-coves-lopsided-vector-register-file/)

下面分各个模块分别记录官方提供的信息，以及实测的结果。读者可以对照已有的第三方评测理解。官方信息与实测结果一致的数据会加粗。

## Benchmark

Intel Golden Cove 的性能测试结果见 [SPEC](../../../benchmark.md)。

## 前端

### Fetch

官方信息：

- Legacy decode pipeline fetch bandwidth is increased from 16 to 32 bytes/cycle

### Decode

官方信息：

- The number of decoders is increased from 4 to 6

### uOP Cache

官方信息：

- The micro-op cache size is increased to hold 4,000 micro-ops,
- and its bandwidth is increased to deliver up to 8 micro-ops per cycle.

### L1 ITLB

官方信息：

- the iTLBs is doubled to hold 256 entries for 4-KB pages and 32 entries for 2/4 million pages

### L1 ICache

官方信息：

- 32KB

## 后端

### Rename

官方信息：

- Rename/allocation width grows from 5 to 6 wide

### Execution Units

官方信息：

- The number of execution ports goes from 10 to 12
- five LEA units as well as five integer ALUs
- three-cycle fast adders, with two cycles bypass between back-to-back floating-point ADD operations
- five alu/simd ports: 0/1/5/6/10
    - P0: ALU/LEA/Shift/JMP/FMA/ALU/Shift/fpDIV
    - P1: ALU/LEA/Mul/iDIV/FMA/ALU/Shift/Shuffle/FADD
    - P5: ALU/LEA/MulHi/FMA512/ALU/AMX/Shuffle/FADD
    - P6: ALU/LEA/Shift/JMP
    - P10: ALU/LEA
- 3 load ports: 2/3/11
- 2 store address ports: 7/8
- 2 store data ports: 4/9

### LSU

官方信息：

- Port 11 provides a third load port with a dedicated address-generation unit
- Load 64Bx2 or 32Bx3 per cycle
- Store 64Bx2 or 32Bx3 per cycle
- The L1 load to use latency is 5 cycles

#### Store to Load Forwarding

官方信息：

- Partial store forwarding allowing forwarding data from store to load also when only part of the load was covered by the store (in case the load's offset matches the store's offset)

### L1 DCache

官方信息：

- 48KB

### L1 DTLB

官方信息：

- 96-entry 6-way 4-KB-page TLB
- 32-entry 4-way 2-MB/4-MB-page TLB
- 8-entry 1-GB-page TLB for loads
- A 16-entry TLB for stores server all page sizes

### L2 TLB

官方信息：

- 2,048-entry second level TLB (STLB)
- 4 page table walkers

### L2 Cache

官方信息：

- 1.25MB(Client)/2MB(Server)
- 64 bytes/cycle
- 15 cycle latency

### ReOrder Buffer

官方信息：

- 512-entry reorder buffer
- 8 wide retirement
