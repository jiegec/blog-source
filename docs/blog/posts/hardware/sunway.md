---
layout: post
date: 2021-12-04
tags: [sunway,sw26010,cpu]
categories:
    - hardware
---

# Sunway 处理器架构分析

## 参考文档

- [高性能众核处理器申威 26010](https://crad.ict.ac.cn/CN/10.7544/issn1000-1239.2021.20201041)
- [稀疏矩阵向量乘法在申威众核架构上的性能优化](https://cjc.ict.ac.cn/online/onlinepaper/lyy-202065163512.pdf)
- [Sunway SW26010](https://en.wikipedia.org/wiki/Sunway_SW26010)
- [The Sunway TaihuLight supercomputer: system and applications](https://link.springer.com/content/pdf/10.1007/s11432-016-5588-7.pdf)
- [Report on the Sunway TaihuLight System](https://www.netlib.org/utk/people/JackDongarra/PAPERS/sunway-report-2016.pdf)
- [Closing the “Quantum Supremacy” Gap: Achieving Real-Time Simulation of a Random Quantum Circuit Using a New Sunway Supercomputer](https://dl.acm.org/doi/pdf/10.1145/3458817.3487399)
- [SW_Qsim: A Minimize-Memory Quantum Simulator with High-Performance on a New Sunway Supercomputer](https://dl.acm.org/doi/pdf/10.1145/3458817.3476161)
- [18.9-Pflops Nonlinear Earthquake Simulation on Sunway TaihuLight: Enabling Depiction of 18-Hz and 8-Meter Scenarios](https://dl.acm.org/doi/pdf/10.1145/3126908.3126910)
- [A FIRST PEEK AT CHINA’S SUNWAY EXASCALE SUPERCOMPUTER](https://www.nextplatform.com/2021/02/10/a-sneak-peek-at-chinas-sunway-exascale-supercomputer/)
- [THE NITTY GRITTY OF THE SUNWAY EXASCALE SYSTEM NETWORK AND STORAGE](https://www.nextplatform.com/2021/03/10/the-nitty-gritty-of-the-sunway-exascale-system-network-and-storage/)
- [Sunway supercomputer architecture towards exascale computing: analysis and practice](https://www.sciengine.com/publisher/scp/journal/SCIS/64/4/10.1007/s11432-020-3104-7?slug=fulltext)
- [China’s New(ish](https://chipsandcheese.com/2023/11/20/chinas-newish-sw26010-pro-supercomputer-at-sc23/)
- [5 ExaFlop/s HPL-MxP Benchmark with Linear Scalability on the 40-Million-Core Sunway Supercomputer](https://dl.acm.org/doi/abs/10.1145/3581784.3607030)

## SW26010

Sunway TaihuLight 的层次：

1. 1 Sunway TaihuLight = 40 Cabinet
2. 1 Cabinet = 4 Super nodes
3. 1 Super node = 256 nodes
4. 1 node = 4 core groups
5. 1 core group = 1 MPE(management processing element) + 8*8 CPE(computer processing element)

MPE 双精度性能：`16 FLOP/cycle * 1.45 GHz = 23.2 GFlops`
CPE 双精度性能：`8 FLOP/cycle * 1.45 GHz = 11.6 GFlops`
CPE 单精度性能：`8 FLOP/cycle * 1.45 GHz = 11.6 GFlops`
单节点双精度性能：`4 * 8 * 8 * 11.6 + 4 * 23.2 = 3.0624 TFlops`
Sunway TaihuLight 双精度性能：`40 * 4 * 256 * 3.0624 = 125.435904 PFlops`

MPE: 32KB L1I, 32 KB L1D, 256 KB L2(中文文献里写的是 512 KB)。乱序执行，4 译码，7 发射（5 整数 2 浮点）。指令预取，分支预测，寄存器重命名，预测执行。5 条整数流水线，2 条 256 位 SIMD 浮点流水线。

CPE：16KB L1I，无 DCache，有 64KB 可重构局部数据存储器（SPM scratch pad memory/LDM local data memory）。2 译码 2 发射，乱序执行，1 条 256 位 SIMD 流水线，1 条整数流水线。不同精度的 SIMD 宽度不同，单精度浮点运算 128 位（4 个单精度），双精度浮点运算 256 位（4 个双精度）。从 SPM 每个周期可以读取 32 字节的数据（正好一个 SIMD 寄存器）。

每个 core group 中还有一个 MC（Memory Controller），连接 8GB DDR3 memory，每个 MC 内存带宽 `128 bit * 2133 MT/s = 34.128 GB/s`，单节点内存带宽 `4 * 34.128 = 136.512 GB/s`。在 Stream Triad 测试，每个 core group 用 DMA 从内存到 SPM 传输数据带宽为 22.6 GB/s，而全局读写 gload/gstore 带宽只有 1.5 GB/s。访问全局内存需要 120+ 个周期。

8x8 矩阵中的从核可以在同行和同列方向上进行低延迟和高带宽的数据传递：2 个从核点对点通信延迟不超过 11 个周期，单个 core group 寄存器通信集合带宽达到 637 GB/s。

28nm 工艺流片，芯片 die 面积超过 500 mm^2，峰值功耗 292.7W，峰值能效比达 10.559 GFLOPS∕W（HPL 6.05 GFLOPS/W）。

## SW26010-Pro

SW26010-Pro 是升级版 SW26010，升级的内容在于：

1. 每个 node 从 4 个 core group 升级到 6 个，一共有 `6 * (8 * 8 + 1) = 390` 个核心。频率也提高了，MPE 频率 2.1GHz，CPE 频率 2.25 GHz。SIMD 宽度扩展到 512 位。
2. 每个 MC 连接了 16 GB DDR4 内存，带宽是 `128 bit * 3200 MT/s = 51.2 GB/s`；单节点总内存 96 GB，总内存带宽 `51.2 * 6 = 307.2 GB/s`。
3. 每个 CPE 的局部存储（LDM）从 64KB 升级到 256KB。
4. CPE 之间的通信可以通过 RMA 进行，而之前的 SW26010 只能在同一行/列之间进行寄存器通信。

## SW52020

在新闻稿和 Sunway supercomputer architecture towards exascale computing: analysis and practice 文章中出现，没有在今年发出来的论文里实际采用，名称可能是新闻稿自己编的，我猜可能没有实际采用，而是做了 SW26010P。和 SW26010 区别：

1. Core Group 从 4 个提升到了 8 个，所以每个 node 有 `8 * (8 * 8 + 1) = 520` 个核心。
2. MPE 和 CPE 向量宽度从 256 位扩展到了 512 位。添加了 16 位半精度浮点支持。
3. 每个 node 提供超过 12 TFlops 的双精度浮点性能。应该是靠两倍的 Core Group，乘上两倍的向量计算宽度，达到四倍的性能。