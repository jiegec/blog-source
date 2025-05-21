---
layout: post
date: 2025-05-21
tags: [cpu,apple,m4,performance,uarch-review]
draft: true
categories:
    - hardware
---

# Apple M4 微架构评测

## 背景

最近拿到了 Apple M4 的环境，借此机会测试一下 Apple M4 的微架构，和之前[分析的 Apple M1 的微架构](./apple_m1.md)做比较。由于 Asahi Linux 尚不支持 Apple M4，所以这里的测试都在 macOS 上进行。

<!-- more -->

## 官方信息

Apple M4 的官方信息乏善可陈，关于微架构的信息几乎为零，但能从操作系统汇报的硬件信息中找到一些内容。

## 现有评测

网上已经有较多针对 Apple M4 微架构的评测和分析，建议阅读：

- [苹果M4性能分析：尽力了，但芯片工艺快到头了！](https://www.bilibili.com/video/BV1NJ4m1w7zk/)

下面分各个模块分别记录官方提供的信息，以及实测的结果。读者可以对照已有的第三方评测理解。官方信息与实测结果一致的数据会加粗。

## 前端

### 取指

#### P-Core

为了测试实际的 Fetch 宽度，参考 [如何测量真正的取指带宽（I-fetch width） - JamesAslan](https://zhuanlan.zhihu.com/p/720136752) 构造了测试。

其原理是当 Fetch 要跨页的时候，由于两个相邻页可能映射到不同的物理地址，如果要支持单周期跨页取指，需要查询两次 ITLB，或者 ITLB 需要把相邻两个页的映射存在一起。这个场景一般比较少，处理器很少会针对这种特殊情况做优化，但也不是没有。经过测试，把循环放在两个页的边界上，发现 M4 P-Core 微架构遇到跨页的取指时确实会拆成两个周期来进行。

在此基础上，构造一个循环，循环的第一条指令放在第一个页的最后四个字节，其余指令放第二个页上，那么每次循环的取指时间，就是一个周期（读取第一个页内的指令）加上第二个页内指令需要 Fetch 的周期数，多的这一个周期就足以把 Fetch 宽度从后端限制中区分开，实验结果如下：

![](./apple-m4-p-core-if-width.png)

图中蓝线（cross-page）表示的就是上面所述的第一条指令放一个页，其余指令放第二个页的情况，横坐标是第二个页内的指令数，那么一次循环的指令数等于横坐标 +1。纵坐标是运行很多次循环的总 cycle 数除以循环次数，也就是平均每次循环耗费的周期数。可以看到每 16 条指令会多一个周期，因此 M4 P-Core 的前端取指宽度确实是 16 条指令，和 Apple M1 的 P-Core 即 Firestorm 是相同的。

为了确认这个瓶颈是由取指造成的，又构造了一组实验，把循环的所有指令都放到一个页中，这个时候 Fetch 不再成为瓶颈（图中 aligned），两个曲线的对比可以明确地得出上述结论。

随着指令数进一步增加，最终瓶颈在每周期执行的 NOP 指令数，因此两条线重合。

#### E-Core

用相同的方式测试 M4 E-Core，结果如下：

![](./apple-m4-e-core-if-width.png)

由于两个曲线汇合的点太前（NOP 指令执行得不够快），无法确定 M4 E-Core 的取指宽度，但可以确认的是它每周期取值不少于 10 条指令，比 Apple M1 的 E-Core 即 Icestorm 要更快。如果读者想到什么办法来确认 M4 E-Core 的取指宽度，欢迎在评论区给出。

### L1 ICache

官方信息：通过 sysctl 可以看到，P-Core 具有 192KB L1 ICache，E-Core 具有 128KB L1 ICache：

```
hw.perflevel0.l1icachesize: 196608
hw.perflevel1.l1icachesize: 131072
```

延续了从 Apple M1 以来的大小。

#### P-Core

为了测试 L1 ICache 容量，构造一个具有巨大指令 footprint 的循环，由大量的 nop 和最后的分支指令组成。观察在不同 footprint 大小下 M4 P-Core 的 IPC：

![](./apple-m4-p-core-fetch-bandwidth.png)

可以看到 footprint 在 192 KB 之前时可以达到 10 IPC，之后则快速降到 2.5 IPC，这里的 192 KB 就对应了 M4 P-Core 的 L1 ICache 的容量。虽然 Fetch 可以每周期 16 条指令，也就是一条 64B 的缓存行，由于后端的限制，只能观察到 10 的 IPC。

#### E-Core

用相同的方式测试 M4 E-Core，结果如下：

![](./apple-m4-e-core-fetch-bandwidth.png)

可以看到 footprint 在 128 KB 之前时可以达到 5 IPC，之后则快速降到 2.0 IPC，这里的 128 KB 就对应了 M4 E-Core 的 L1 ICache 的容量。

### BTB

#### P-Core

#### E-Core

### L1 ITLB

#### P-Core

#### E-Core

### Decode

#### P-Core

#### E-Core

### Return Stack

#### P-Core

#### E-Core

### Conditional Branch Predictor

#### P-Core

#### E-Core

## 后端

### 物理寄存器堆

#### P-Core

#### E-Core

### Load Store Unit + L1 DCache

#### L1 DCache 容量

##### P-Core

##### E-Core

#### L1 DTLB 容量

##### P-Core

##### E-Core

#### Load/Store 带宽

##### P-Core

##### E-Core

#### Memory Dependency Predictor

##### P-Core

##### E-Core

#### Store to Load Forwarding

##### P-Core

##### E-Core

#### Load to use latency

##### P-Core

##### E-Core

#### Virtual Address UTag/Way-Predictor

##### P-Core

##### E-Core

### 执行单元

#### P-Core

#### E-Core

### Scheduler

#### P-Core

#### E-Core

### Reorder Buffer

#### P-Core

#### E-Core

### L2 Cache

### L2 TLB

#### P-Core

#### E-Core
