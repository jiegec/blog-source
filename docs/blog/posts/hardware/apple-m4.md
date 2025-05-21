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

### 取指带宽

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

[Apple M1](./apple-m1.md) 的 BTB 设计相对比较简单：1024 项的组相连 L1 BTB，接着是以 192KB L1 ICache 作为兜底的 3 周期的等效 BTB。但是 M4 上的 BTB 测试图像变化很大，下面进行仔细的分析。

#### P-Core

构造大量的无条件分支指令（B 指令），BTB 需要记录这些指令的目的地址，那么如果分支数量超过了 BTB 的容量，性能会出现明显下降。当把大量 B 指令紧密放置，也就是每 4 字节一条 B 指令时：

![](./apple-m4-p-core-btb-4b.png)

可以看到最低的 CPI 能达到接近 0.5（实际值在 0.55），说明 Apple M4 有了一定的每周期执行 2 taken branches 的能力，后面会着重讨论这一点。在经过 CPI 最低点之后，性能出现了先下降后上升再下降的情况，最终在 2048 个分支开始稳定在 2 左右（实际值在 2.10）的 CPI。

这个 2 左右的 CPI 一直稳定维持，一直延续到 49152 个分支。超出 BTB 容量以后，分支预测时，无法从 BTB 中得到哪些指令是分支指令的信息，只能等到取指甚至译码后才能后知后觉地发现这是一条分支指令，这样就出现了性能损失，出现了 2 CPI 的情况。49152 这个拐点，对应的是指令 footprint 超出 L1 ICache 的情况：L1 ICache 是 192KB，按照每 4 字节一个 B 指令计算，最多可以存放 49152 条 B 指令。

这个 2 CPI 的平台在 Apple M1 中是 3 CPI，这是一个巨大的优化，在大多数情况下，通过 L1 ICache 能以每 2 周期一条无条件分支的性能兜底。

接下来降低分支指令的密度，在 B 指令之间插入 NOP 指令，使得每 8 个字节有一条 B 指令，得到如下结果：

![](./apple-m4-p-core-btb-8b.png)

图像基本就是 4 字节间距情况下，整体左移的结果，说明各级 BTB 结构大概是组相连，当间距为 8 字节，PC[2] 恒为 0 的时候，只有一半的组可以被用到。

继续降低分支指令的密度，在 B 指令之间插入 NOP 指令，使得每 16 个字节有一条 B 指令，得到如下结果：

![](./apple-m4-p-core-btb-16b.png)

每 32 个字节有一条 B 指令：

![](./apple-m4-p-core-btb-32b.png)

从间距为 4 字节到间距为 32 字节，整个的图像都是类似的，只是不断在左移。但是当每 64 个字节有一条 B 指令的时候，情况就不同了：

![](./apple-m4-p-core-btb-64b.png)

整体的 CPI 有比较明显的下降，最低的 CPI 也在 2 以上，这和 Apple M1 上依然是在 4 字节间距的图像的基础上左移有显著的不同。

前面提到，Apple M4 P-Core 出现了每周期 2 taken branches，但是当分支不在同一个 64B 内的时候，性能会有明显下降；另一方面，以 ARM Neoverse V2 为例，它实现的每周期 2 taken branches，即使分支不在同一个 64B 内，也是可以做到的，下面是在 64B 间距下 ARM Neoverse V2 的测试结果：

![](./apple-m4-neoverse-v2-2-taken.png)

根据这些现象，找到了 Apple 的一篇专利 [Using a Next Fetch Predictor Circuit with Short Branches and Return Fetch Groups](https://patents.google.com/patent/US20240028339A1/en)，它提到了一种符合上述现象的实现 2 taken branches 的方法：如果在一个 fetch group（在这里是 64B）内，有一条分支，它的目的地址还在这个 fetch group 内，由于 fetch group 的指令都已经取出来了，所以同一个周期内，可以从这条分支的目的地址开始，继续获取指令。下面是一个例子：

```asm
# the beginning of a fetch group
nop
# the branch
b target
# some instructions are skipped between branch and its target
svc #0
# the branch target resides in the same fetch group
target:
# some instructions after the branch target
add x3, x2, x1
ret
```

那么在传统的设计里，这段代码会被分成两个周期去取指，第一个周期取 `nop` 和 `b target`，第二个周期取 `add x3, x2, x1` 和 `ret`；按照这个专利的说法，可以在一个周期内取出所有指令，然后把中间被跳过的 `svc #0` 指令跳过去，不去执行它。当然了，分支预测器那边也需要做修改，能够去预测第二个分支的目的地址，用于下一个周期。

如果是这种实现方法，是可能在一个 Coupled 前端内，实现这种有限场景的每周期执行 2 taken branches，核心是每周期依然只访问一次 ICache。

#### E-Core

另一方面，M4 E-Core 的 BTB 设计和 Apple M1 的 E-Core 即 Icestorm 十分接近，当分支间距是 4 字节时：

![](./apple-m4-e-core-btb-4b.png)

可以看到 1024 的拐点，1024 之前是 1 IPC，之后增加到 3 IPC。比较奇怪的是，没有看到第二个拐点。

8B 的间距：

![](./apple-m4-e-core-btb-8b.png)

拐点前移到 512。

16B 的间距：

![](./apple-m4-e-core-btb-16b.png)

第一个拐点前移到 256，第二个拐点出现在 8192，而 Icestorm 的 L1 ICache 容量是 128KB，16B 间距下正好可以保存 8192 个分支。

可见 M4 E-Core 的前端设计和 M4 P-Core 有较大的不同。

### L1 ITLB

#### P-Core

构造一系列的 B 指令，使得 B 指令分布在不同的 page 上，使得 ITLB 成为瓶颈，在 M4 P-Core 上进行测试：

![](./apple-m4-p-core-itlb.png)

第一个拐点是由于 L1 BTB 的冲突缺失，之后在 192 个页时从 3 Cycle 快速增加到 12 Cycle，则对应了 192 项的 L1 ITLB 容量。这和 M1 是一样的。

#### E-Core

在 M4 E-Core 上重复实验：

![](./apple-m1-icestorm-itlb.png)

第一个拐点是由于 L1 BTB 的冲突缺失，之后在 192 个页时从 3 Cycle 快速增加到 10 Cycle，则对应了 192 项的 L1 ITLB 容量。相比 M1 的 128 项，容量变大了，和 M4 P-Core 看齐。

### Decode

从前面的测试来看，M4 P-Core 最大观察到 10 IPC，M4 E-Core 最大观察到 5 IPC，那么 Decode 宽度也至少是这么多，暂时也不能排除有更大的 Decode 宽度。相比 M1 的 P-Core 8 IPC，E-Core 4 IPC 都有拓宽。

### Return Stack

#### P-Core

构造不同深度的调用链，测试每次调用花费的平均时间，在 M4 P-Core 上得到下面的图：

![](./apple-m4-p-core-rs.png)

可以看到调用链深度为 60 时性能突然变差，因此 M4 P-Core 的 Return Stack 深度为 60，比 M1 P-Core 的 50 要更大。这里测试的两个 Variant，对应的是 Return 的目的地址不变还是会变化。

#### E-Core

在 M4 E-Core 上测试：

![](./apple-m4-e-core-rs.png)

可以看到调用链深度为 40 时性能突然变差，因此 M4 E-Core 的 Return Stack 深度为 40，比 M1 E-Core 的 32 要更大。

## 后端

### 物理寄存器堆

#### P-Core

为了测试物理寄存器堆的大小，一般会用两个依赖链很长的操作放在开头和结尾，中间填入若干个无关的指令，并且用这些指令来耗费物理寄存器堆。M4 P-Core 测试结果见下图：

![](./apple-m4-p-core-prf.png)

- 32b int：测试 speculative 32 位整数寄存器的数量，拐点在 720 左右
- 64b int：测试 speculative 64 位整数寄存器的数量，拐点在 360 左右，只有 32b 的一半，可见实际的物理寄存器堆有 360 左右个 64 位整数寄存器，但是可以分成两半分别当成 32 位整数寄存器用，这一个优化在 M1 是没有的，即用 32b 或者用 64b 整数，测出来的整数寄存器数量相同
- flags：测试 speculative NZCV 寄存器的数量，拐点在 175 左右
- 32b fp：测试 speculative 32 位浮点寄存器的数量，没有观察到明显的拐点

#### E-Core

在 M4 E-Core 上复现相同的测试，发现性能非常不稳定，不确定是什么原因。

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
