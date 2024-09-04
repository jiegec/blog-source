---
layout: post
date: 2024-09-01
tags: [cpu,oryon,qualcomm,xelite,performance]
categories:
    - hardware
---

# Qualcomm Oryon 微架构评测

## 背景

最近借到一台 Surface Laptop 7 可以拿来折腾，它用的是高通 Snapdragon X Elite 处理器，借此机会测试一下这个微架构在各个方面的表现。

<!-- more -->

## 官方信息

高通关于 Oryon 微架构有两个 slides，内容可以在以下的链接中看到：

- [The Qualcomm Snapdragon X Architecture Deep Dive: Getting To Know Oryon and Adreno X1 - Anandtech](https://www.anandtech.com/show/21445/qualcomm-snapdragon-x-architecture-deep-dive/2)
- [Hot Chips 2024: Qualcomm’s Oryon Core - Chips and Cheese](https://chipsandcheese.com/2024/08/26/hot-chips-2024-qualcomms-oryon-core/)

两次内容大体一致，Hot Chips 2024 的内容更加详细，但也出现了一些前后矛盾的地方。

## 现有评测

网上已经有较多针对 Oryon 微架构的评测和分析，建议阅读：

- [高通 X Elite Oryon 微架构评测：走走停停](https://zhuanlan.zhihu.com/p/704707254)
- [Qualcomm’s Oryon Core: A Long Time in the Making](https://chipsandcheese.com/2024/07/09/qualcomms-oryon-core-a-long-time-in-the-making/)
- [Qualcomm’s Oryon LLVM Patches](https://chipsandcheese.com/2024/05/15/qualcomms-oryon-llvm-patches/)
- [高通自研 PC 芯片 X Elite 实测：真能干翻苹果英特尔？](https://www.bilibili.com/video/BV1Ue41197Qb/)
- [太贵了，它没你想的那么美好！高通骁龙 X Elite 78-100 笔记本详细评测](https://www.bilibili.com/video/BV1z1421r7dZ/)
- [Snapdragon X Elite](https://www.qualcomm.com/products/mobile/snapdragon/laptops-and-tablets/snapdragon-x-elite)
- [Qualcomm Oryon CPU](https://www.qualcomm.com/products/technology/processors/oryon)

下面分各个模块分别记录官方提供的信息，以及实测的结果。读者可以对照已有的第三方评测理解。

## 前端

### 取指

官方信息：取指可以达到每周期最多 16 指令

### L1 ICache

官方信息：192KB 6-way L1 ICache

为了测试 L1 ICache 容量，构造一个具有巨大指令 footprint 的循环，由大量的 nop 和最后的分支指令组成。观察在不同 footprint 大小下的 IPC：

![](./qualcomm_oryon_fetch_bandwidth.png)

可以看到 footprint 在 192 KB 之前时可以达到 8 IPC，之后则快速降到 2 IPC，这里的 192 KB 就对应了 L1 ICache 的容量。

### L1 ITLB

官方信息：256-entry 8-way L1 ITLB，支持 4KB 和 64KB 的页表大小

### Decode

官方信息：8 inst/cycle decoded

### Return Stack

官方信息：50-entry return stack

构造不同深度的调用链，测试每次调用花费的平均时间，得到下面的图：

![](./qualcomm_oryon_rs.png)

可以看到调用链深度为 50 时性能突然变差，因此 Return Stack 深度为 50。

### Branch Predictor

官方信息：80KB Conditional Predictor, 40KB Indirect Predictor

### BTB

官方信息：2K+ entry BTB

构造大量的无条件分支指令（B 指令），BTB 需要记录这些指令的目的地址，那么如果分支数量超过了 BTB 的容量，性能会出现明显下降。当把大量 B 指令紧密放置，也就是每 4 字节一条 B 指令时：

![](./qualcomm_oryon_btb_4b.png)

可见在 2048 个分支之内可以达到 1 的 CPI，超过 2048 个分支，出现了 3 CPI 的平台，一直延续到 32768 个分支或更多。超出 BTB 容量以后，分支预测时，无法从 BTB 中得到哪些指令是分支指令的信息，只能等到取指甚至译码后才能后知后觉地发现这是一条分支指令，这样就出现了性能损失，出现了 3 CPI 的情况。

降低分支指令的密度，在 B 指令之间插入 NOP 指令，使得每 8 个字节有一条 B 指令，得到如下结果：

![](./qualcomm_oryon_btb_8b.png)

可以看到 CPI=1 的拐点前移到 1024 个分支，同时 CPI=3 的平台也出现了新的拐点，在 16384 和 32768 之间。拐点的前移，意味着 BTB 采用了组相连的结构，当 B 指令的 PC 的部分低位总是为 0 时，组相连的 Index 可能无法取到所有的 Set，导致表现出来的 BTB 容量只有部分 Set，例如此处容量减半，说明只有一半的 Set 被用到了。

出现新的拐点，对应的是指令 footprint 超出 L1 ICache 的情况：L1 ICache 是 192KB，按照每 8 字节一个 B 指令计算，最多可以存放 24576 条 B 指令，这个值正好处在 16384 和 32768 之间，和拐点吻合。

小结：BTB 容量为 2048 项，采用组相连方式，当所有分支命中 BTB 时，可以达到 1 CPI；如果超出了 BTB 容量，但没有超出 L1 ICache 容量，可以达到 3 CPI。

### Branch Mispredict Latency

官方信息：13 cycle Branch Mispredict Latency

## 后端

### 物理寄存器堆

官方信息：400+ registers Integer pool, 400+ registers Vector pool

### Reservation Stations

官方信息：

- IXU 6-wide 64-bit, each with 20 entry queue
- VXU 4-wide 128-bit, each with 48 entry queue
- LSU 4-wide 128-bit, each with 16 entry queue (注：Hot Chips 上的 Slides 写的是四个 64-entry，出现了不一致)

### 执行单元

官方信息：

- Up to 6 ALU/cycle
- Up to 2 Branch/cycle
- Up to 2 multiply/MLA per cycle

在循环中重复下列指令多次，测量 CPI，得到如下结果：

- `add x0, x0, 1`：CPI = 6.0，说明可以 6 ALU/cycle
- `cbnz xzr, target;target:`：CPI = 2.0，说明可以 2 Branch/cycle
- `mul x0, x1, x2`：CPI = 2.0，说明可以 2 Multiply/cycle

### Reorder Buffer

官方信息：

- Retirement 8 uOps/cycle
- Reorder Buffer is 650+ uOps

### Load Store Unit + L1 DCache

官方信息：

- 96KB 6-way L1 DCache
- 224-entry 7-way L1 DTLB, supports 4KB and 64KB translation granules
- Up to 4 Load-Store operations per cycle
- 192 entry Load Queue, 56 entry Store Queue
- Full 64B/cycle for both fills and evictions to L2 cache

构造不同大小 footprint 的 pointer chasing 链，测试不同 footprint 下每条 load 指令耗费的时间：

![](./qualcomm_oryon_l1dc.png)

可以看到 96KB 出现了明显的拐点，对应的就是 96KB 的 L1 DCache 容量。

用类似的方法测试 L1 DTLB 容量，只不过这次 pointer chasing 链的指针分布在不同的 page 上，使得 DTLB 成为瓶颈：

![](./qualcomm_oryon_dtlb.png)

可以看到 224 Page 出现了明显的拐点，对应的就是 224 的 L1 DTLB 容量。从每个 page 一个指针改成每 32 page 一个指针并注意对齐尽量保证 Index 为 0，此时 L1 DTLB 容量降为 7，说明 L1 DTLB 是 7 路组相连结构，这些页被映射到了相同的 Set 当中：

![](./qualcomm_oryon_dtlb_7.png)

### MMU

官方信息：

- 4KB and 64KB translation granules
- 1 cycle access for L1 ITLB & L1 DTLB
- Unified L2 TLB, 8-way >8K entry

### L2 Cache

官方信息：

- 12MB 12-way L2 Cache
- MOESI
- 17 cycle latency for L1 miss to L2 hit

### Memory

官方信息：

- 6MB System Level Cache, 26-29ns latency, 135GB/s bandwidth in each direction
- LPDDR5x DRAM, 8448 MT/s, 8 channel of 16 bits, 135GB/s bandwidth, 102-104ns latency
