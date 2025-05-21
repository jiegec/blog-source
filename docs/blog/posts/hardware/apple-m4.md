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

寄存器堆大小和 M1 P-Core 比较类似，但是多了 32 位整数寄存器的优化。

#### E-Core

在 M4 E-Core 上复现相同的测试，发现性能非常不稳定，不确定是什么原因。

### Load Store Unit + L1 DCache

#### L1 DCache 容量

官方信息：通过 sysctl 可以看到，M4 P-Core 具有 128KB L1 DCache，M4 E-Core 具有 64KB L1 DCache：

```
hw.perflevel0.l1dcachesize: 131072
hw.perflevel1.l1dcachesize: 65536
```

和 M1 相同。

##### P-Core

构造不同大小 footprint 的 pointer chasing 链，在每个页的开头放一个指针，测试不同 footprint 下每条 load 指令耗费的时间，M4 P-Core 上的结果：

![](./apple-m4-p-core-l1dc.png)

可以看到 128KB 出现了拐点，对应的就是 128KB 的 L1 DCache 容量。当 footprint 比较小的时候，由于 Load Address/Value Predictor 的介入，打破了依赖链，所以出现了 latency 小于正常 load to use 的 3 cycle  latency 的情况。

##### E-Core

M4 E-Core 上的结果：

![](./apple-m4-e-core-l1dc.png)

可以看到 128KB 出现了明显的拐点，但实际上 M4 E-Core 的 L1 DCache 只有 64KB。猜测这是因为在测试的时候，是在每个 16KB 页的开头放一个指针，但如果 L1 DCache 的 Index 并非都在 16KB 内部，就会导致实际测出来的不是 L1 DCache 的大小。修改测试，使得每 8 字节一个指针，此时测出来的结果就是正确的 64KB 大小：

![](./apple-m4-e-core-l1dc-2.png)

此时 64KB 对应的就是 64KB 的 L1 DCache 容量。L1 DCache 范围内延迟是 3 cycle，之后提升到 14+ cycle。由此可见 M4 E-Core 没有 Load Address/Value Predictor，不能打断依赖链。

#### L1 DTLB 容量

##### P-Core

用类似的方法测试 L1 DTLB 容量，只不过这次 pointer chasing 链的指针分布在不同的 page 的不同 cache line 上，使得 DTLB 成为瓶颈，在 M4 P-Core 上：

![](./apple-m4-p-core-l1dtlb.png)

从 160 个页开始性能下降，到 200 个页时性能稳定在 9 CPI，认为 M4 P-Core 的 L1 DTLB 有 160 项，大小和 M1 P-Core 相同。9 CPI 包括了 L1 DTLB miss L2 TLB hit 带来的额外延迟。中间有时性能特别快，是 Load Address/Value Predictor 的功劳。

##### E-Core

M4 E-Core 测试结果:

![](./apple-m4-e-core-l1dtlb.png)

从 192 个页开始性能下降，到 224 个页时性能稳定在 9 CPI，认为 M4 E-Core 的 L1 DTLB 有 192 项，比 M1 E-Core 的 128 项更大，甚至大过了 P-Core。9 CPI 包括了 L1 DTLB miss L2 TLB hit 带来的额外延迟，比 M1 E-Core 少了一个周期。

#### Load/Store 带宽

##### P-Core

针对 Load Store 带宽，实测 M4 P-Core 每个周期可以完成：

- 3x 128b Load + 1x 128b Store
- 2x 128b Load + 2x 128b Store
- 1x 128b Load + 2x 128b Store
- 2x 128b Store

如果把每条指令的访存位宽从 128b 改成 256b，读写带宽不变，指令吞吐减半。也就是说最大的读带宽是 48B/cyc，最大的写带宽是 32B/cyc，二者不能同时达到。和 M1 P-Core 相同。

##### E-Core

实测 M4 E-Core 每个周期可以完成：

- 2x 128b Load
- 1x 128b Load + 1x 128b Store
- 1x 128b Store

如果把每条指令的访存位宽从 128b 改成 256b，读写带宽不变，指令吞吐减半。也就是说最大的读带宽是 32B/cyc，最大的写带宽是 16B/cyc，二者不能同时达到。和 M1 E-Core 相同。

#### Memory Dependency Predictor

为了预测执行 Load，需要保证 Load 和之前的 Store 访问的内存没有 Overlap，那么就需要有一个预测器来预测 Load 和 Store 之前在内存上的依赖。参考 [Store-to-Load Forwarding and Memory Disambiguation in x86 Processors](https://blog.stuffedcow.net/2014/01/x86-memory-disambiguation/) 的方法，构造两个指令模式，分别在地址和数据上有依赖：

- 数据依赖，地址无依赖：`str x3, [x1]` 和 `ldr x3, [x2]`
- 地址依赖，数据无依赖：`str x2, [x1]` 和 `ldr x1, [x2]`

初始化时，`x1` 和 `x2` 指向同一个地址，重复如上的指令模式，观察到多少条 `ldr` 指令时会出现性能下降。

##### P-Core

在 M4 P-Core 上测试：

![](./apple-m4-p-core-memory-dependency-predictor.png)

数据依赖没有明显的阈值，但从 72 开始出现了一个小的增长，且斜率不为零；地址依赖的阈值是 39。相比 M1 P-Core 有所减小。

##### E-Core

M4 E-Core:

![](./apple-m4-e-core-memory-dependency-predictor.png)

数据依赖的阈值是 20，地址依赖的阈值是 14。比 M1 E-Core 略大。

#### Store to Load Forwarding

##### P-Core

经过实际测试，M4 P-Core 上如下的情况可以成功转发，对地址 x 的 Store 转发到对地址 y 的 Load 成功时 y-x 的取值范围：

| Store\Load | 8b Load | 16b Load | 32b Load | 64b Load |
|------------|---------|----------|----------|----------|
| 8b Store   | {0}     | [-1,0]   | [-3,0]   | [-7,0]   |
| 16b Store  | [0,1]   | [-1,1]   | [-3,1]   | [-7,1]   |
| 32b Store  | [0,3]   | [-1,3]   | [-3,3]   | [-7,3]   |
| 64b Store  | [0,7]   | [-1,7]   | [-3,7]   | [-7,7]   |

从上表可以看到，所有 Store 和 Load Overlap 的情况，无论地址偏移，都能成功转发。甚至在 Load 或 Store 跨越 64B 缓存行边界时，也可以成功转发，代价是多一个周期。

一个 Load 需要转发两个、四个甚至八个 Store 的数据时，也可以成功转发。即使数据跨越缓存行，也可以转发，只是多耗费 1-2 个周期。但在跨 64B 缓存行的时候，代价可能多于一个周期。相比 M1 P-Core，M4 P-Core 在跨越缓存行的情况下也可以得到比较好的性能。

成功转发时 7 cycle 左右。

小结：Apple M4 P-Core 的 Store to Load Forwarding：

- 1 ld + 1 st: 支持
- 1 ld + 2 st: 支持
- 1 ld + 4 st: 支持
- 1 ld + 8 st: 支持
- 跨 64B 缓存行边界时，性能略微下降

##### E-Core

在 M4 E-Core 上，如果 Load 和 Store 访问范围出现重叠，当需要转发一个到两个 Store 的数据时，需要 7 Cycle，无论是否跨缓存行。如果需要转发四个 Store 的数据，则需要 8 Cycle；转发八个 Store 的数据需要 11 Cycle。相比 M1 E-Core，多数情况下获得了性能提升。

#### Load to use latency

##### P-Core

实测 M4 P-Core 的 Load to use latency 针对 pointer chasing 场景做了优化，在下列的场景下可以达到 3 cycle:

- `ldr x0, [x0]`: load 结果转发到基地址，无偏移
- `ldr x0, [x0, 8]`：load 结果转发到基地址，有立即数偏移
- `ldr x0, [x0, x1]`：load 结果转发到基地址，有寄存器偏移
- `ldp x0, x1, [x0]`：load pair 的第一个目的寄存器转发到基地址，无偏移

如果访存跨越了 8B 边界，则退化到 4 cycle。

在下列场景下 Load to use latency 则是 4 cycle：

- load 的目的寄存器作为 alu 的源寄存器（下称 load to alu latency）
- `ldr x0, [sp, x0, lsl #3]`：load 结果转发到 index
- `ldp x1, x0, [x0]`：load pair 的第二个目的寄存器转发到基地址，无偏移

注意由于 Load Address/Value Predictor 的存在，测试的时候需要排除预测器带来的影响。延迟方面，和 M1 P-Core 相同。

##### E-Core

实测 M4 E-Core 的 Load to use latency 针对 pointer chasing 场景做了优化，在下列的场景下可以达到 3 cycle:

- `ldr x0, [x0]`: load 结果转发到基地址，无偏移
- `ldr x0, [x0, 8]`：load 结果转发到基地址，有立即数偏移
- `ldr x0, [x0, x1]`：load 结果转发到基地址，有寄存器偏移
- `ldp x0, x1, [x0]`：load pair 的第一个目的寄存器转发到基地址，无偏移

如果访存跨越了 8B/16B/32B 边界，依然是 3 cycle；跨越了 64B 边界则退化到 7 cycle。

在下列场景下 Load to use latency 则是 4 cycle：

- load 的目的寄存器作为 alu 的源寄存器（下称 load to alu latency）
- `ldr x0, [sp, x0, lsl #3]`：load 结果转发到 index
- `ldp x1, x0, [x0]`：load pair 的第二个目的寄存器转发到基地址，无偏移

延迟方面，和 M1 E-Core 相同。

#### Virtual Address UTag/Way-Predictor

Linear Address UTag/Way-Predictor 是 AMD 的叫法，但使用相同的测试方法，也可以在 Apple M1 上观察到类似的现象，猜想它也用了类似的基于虚拟地址的 UTag/Way Predictor 方案，并测出来它的 UTag 也有 8 bit，M4 P-Core 和 M4 E-Core 都是相同的：

- VA[14] xor VA[22] xor VA[30] xor VA[38] xor VA[46]
- VA[15] xor VA[23] xor VA[31] xor VA[39] xor VA[47]
- VA[16] xor VA[24] xor VA[32] xor VA[40]
- VA[17] xor VA[25] xor VA[33] xor VA[41]
- VA[18] xor VA[26] xor VA[34] xor VA[42]
- VA[19] xor VA[27] xor VA[35] xor VA[43]
- VA[20] xor VA[28] xor VA[36] xor VA[44]
- VA[21] xor VA[29] xor VA[37] xor VA[45]

一共有 8 bit，由 VA[47:14] 折叠而来。和 Apple M1 相同。

#### Load Address/Value Predictor

Apple 从 M2 开始引入 Load Address Predictor，从 M3 开始引入 Load Value Predictor，相关的信息如下：

- Load Address Predictor：支持 Constant 和 Striding Address 两种模式，专利是 [Early load execution via constant address and stride prediction](https://patents.google.com/patent/US11829763B2/)
- Load Value Predictor（也称 Load Output Predictor）：只支持 Constant Value，专利是 [Shared learning table for load value prediction and load address prediction](https://patents.google.com/patent/US12067398B1/en)

这两个 Predictor 会对已有的基于 Load 的各种 microbenchmark 带来深刻的影响。

网上已有针对这两个 Predictor 的逆向和攻击：[SLAP: Data Speculation Attacks via Load Address Prediction on Apple Silicon;FLOP Breaking the Apple M3 CPU via False Load Output Predictions](https://predictors.fail/)。

##### P-Core

##### E-Core

M4 E-Core 没有实现 Load Address/Value Predictor。

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
