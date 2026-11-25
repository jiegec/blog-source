---
layout: post
date: 2026-11-25
tags: [cpu,loongson,loongarch,la464,performance,uarch-review]
draft: true
categories:
    - hardware
---

# Loongson LA664 微架构评测

## 背景

之前分析了很多国外的微架构，而龙芯的微架构一直都没怎么研究过。既然 LA864 快要来了，那就在它来之前分析一下 [LA464](./loongson-la464.md) 和 LA664。

<!-- more -->

## 官方信息

Loongson 关于 LA664 微架构有这些官方的信息：

- [龙芯 3A6000 产品页](https://www.loongson.cn/product/show?id=26)：2.0GHz-2.5GHz，240GFlops，典型功耗 38W@2.5GHz
- [龙芯 3A6000 发布报道](https://www.loongson.cn/news/show?id=638)（2023 龙芯产品发布暨用户大会，2023-11-28）
- [《龙芯 3A6000 数据手册》V1.5](https://www.loongson.cn/uploads/images/2025093014105554649.Loongson3A6000%20data%20book_V1.5.pdf)：六发射乱序执行、4 个定点 + 4 个向量 + 4 个访存单元、各级 Cache 容量
- [《龙芯 3A6000 处理器寄存器使用手册》V1.2](https://www.loongson.cn/uploads/images/2024072510054986439.Loongson3A6000%20user%20book_V1.2.pdf)：第 8 章为 LA664 处理器核
- [龙芯官网下载中心](https://www.loongson.cn/download/index)：上述手册的下载页面

2023 年的发布会上，胡伟武展示了 LA464 与 LA664 的微架构对比，这是目前公开的最具体的 LA664 官方参数：

![2023 龙芯产品发布暨用户大会上公布的 LA464 与 LA664 微架构对比（图源：快科技现场报道）](./loongson-la664-miniarch-table.jpg)

（本页及下文中的发布会幻灯片照片均出自[该报道](https://news.mydrivers.com/1/948/948522.htm)）

官方给出的逐项参数如下：

| 参数 | LA464 | LA664 |
| --- | --- | --- |
| 发射宽度 | 4 | 6 |
| ROB 项数 | 128 | 256 |
| 定点物理寄存器数 | 128 | 192 |
| 向量物理寄存器数 | 128 | 192 |
| 发射队列项数（访存+定点+向量） | 32+32+32 | 48+48+48 |
| 功能部件数（访存+定点+向量） | 2+4+2 | 4+4+4 |
| load 队列项数 | 64 | 80 |
| store 队列项数 | 48 | 64 |

3A6000 数据手册和寄存器使用手册还给出了完整的芯片级参数：

- 六发射 64 位超标量结构，支持 SMT2，每个物理核包含两个逻辑核，全芯片 4 物理核 8 逻辑核
- 4 个定点、4 个向量、4 个访存功能部件；每个向量部件 256 位，最多支持 8 个单精度或 4 个双精度乘加
- 每核 64KB L1I + 64KB L1D，4 路组相联；256KB Victim Cache 作为私有 L2，16 路组相联；片内 16MB 分体共享 L3
- 访存部件支持 256 位访问，虚地址 64 位、物理地址 48 位；支持 Non-blocking 访问和 Load-Speculation
- 2 个 72 位 DDR4-3200 控制器（支持 ECC），1 个 16 位 HT 3.0 控制器（最高 6.4Gbps）
- 双精度峰值 240GFlops@2.5GHz，典型功耗 38W@2.5GHz

发布会上展示的 3A6000 规格页如下：

![2023 发布会上公布的龙芯 3A6000 规格页](./loongson-3a6000-slide.jpg)

数据手册给出的 3A6000 芯片结构如图 1.1 所示，4 个 LA664 核通过 L1X/L2X 两级交叉开关连接 4 块共享三级 Cache，并连接到内存控制器和 IO-Ring：

![《龙芯 3A6000 数据手册》图 1.1 处理器结构示意图](./loongson-3a6000-chip.png)

## 现有评测

网上已经有较多针对 LA664 微架构的评测和分析，建议阅读：

- [Loongson 3A6000: A Star among Chinese CPUs](https://old.chipsandcheese.com/2024/03/13/loongson-3a6000-a-star-among-chinese-cpus/)

下面分各个模块分别记录官方提供的信息，以及实测的结果。读者可以对照已有的第三方评测理解。官方信息与实测结果一致的数据会加粗。

## Benchmark

Loongson LA664 的性能测试结果见 [SPEC](../../../benchmark/index.md)。

## 前端

### Fetch

官方信息：LA664 是六发射超标量处理器核，发布会上给出的发射宽度为 6。

### Decode

官方信息：译码宽度为六。

### L1 ITLB

### L1 ICache

官方信息：每核 **64KB**，4 路组相联。

为了测试 L1 ICache 容量，构造一个具有巨大指令 footprint 的循环，由大量的 4 字节 nop 和最后的分支指令组成。观察在不同 footprint 大小下的 IPC：

![](./loongson-la664-fetch-bandwidth.png)

可以看到 footprint 在 64 KB 之前时可以达到 6 IPC，之后开始下降，这里的 64 KB 就对应了 L1 ICache 的容量。

容量和 LA464 相同，不过 IPC 有所上升。

[测试过程详见测试代码](https://github.com/jiegec/cpu-micro-benchmarks/blob/master/src/fetch_bandwidth_gen.cpp)。

### Return Stack

### BTB

## 后端

### Register File

官方信息：定点物理寄存器 192 项、向量物理寄存器 192 项。

### Execution Units

官方信息：4 个定点、4 个向量、4 个访存功能部件。每个向量部件 256 位宽，最多支持 8 个单精度或 4 个双精度乘加运算。

### Scheduler

官方信息：译码后的指令分别进入访存、定点、向量三个发射队列，每类 48 项。

### LSU

官方信息：访存部件支持 256 位存储访问，虚地址 64 位、物理地址 48 位；load 队列 80 项、store 队列 64 项；支持 Non-blocking 访问和 Load-Speculation。

#### Load/Store Queue

#### Load Store 带宽

#### Store to Load Forwarding

### L1 DCache

官方信息：每核 64KB，4 路组相联。

### L1 DTLB

### L2 TLB

### L2 Cache

官方信息：每核 256KB Victim Cache，作为私有二级 Cache，16 路组相联。

### L3 Cache

官方信息：4 个核共享 16MB 分体三级 Cache。

### Prefetcher

### ReOrder Buffer

官方信息：ROB 256 项。
