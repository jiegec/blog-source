---
layout: post
date: 2025-06-23
tags: [cpu,arm,neoverse,btb]
categories:
    - hardware
---

# ARM Neoverse V1 (代号 Zeus) 的 BTB 结构分析

## 背景

ARM Neoverse V1 是 ARM Neoverse N1 的下一代服务器 CPU，之前我们分析过 [Neoverse N1 的 BTB 设计](./arm-neoverse-v1-btb.md)。而 ARM Neoverse V1 在很多地方都和 Cortex-X1 类似，有了一些改进，在这里对它的 BTB 做一些分析。

<!-- more -->

## 官方信息

首先收集了一些 ARM Neoverse V1 的 BTB 结构的官方信息：

- [SW defined cars: HPC, from the cloud to the dashboard for an amazing driver experience](https://teratec.eu/library/pdf/forum/2021/A05-03.pdf)
    - 64KB L1 ICache, 2x32B bandwidth
    - 8K-entry main BTB
    - 96-entry nano BTB, 0 cycle bubble
    - 2 stage prediction pipeline: P1 & P2
- [Arm Neoverse V2 platform: Leadership Performance and Power Efficiency for Next-Generation Cloud Computing, ML and HPC Workloads](https://hc2023.hotchips.org/assets/program/conference/day1/CPU1/HC2023.Arm.MagnusBruce.v04.FINAL.pdf)
    - 2 predicted branches per cycle

简单整理一下官方信息，大概有两级 BTB：

- 96-entry nano BTB, 1 cycle latency (0 cycle bubble)
- 8K-entry main BTB
- 2 predicted branches per cycle

但是很多细节是缺失的，因此下面结合微架构测试，进一步研究它的内部结构。

## 微架构测试

在之前的博客里，我们已经测试了各种处理器的 BTB，在这里也是一样的：按照一定的 stride 分布无条件（uncond）或有条件（cond）直接分支，构成一个链条，然后测量 CPI。

### stride=4B uncond

首先是 stride=4B uncond 的情况：

![](./arm-neoverse-v1-btb-4b-uncond.png)

可以看到，图像上出现了如下比较显著的台阶：

- 第一个台阶到接近 64 条分支，CPI=1，对应了 96-entry 的 nano BTB，但是没有体现出完整的 96 的容量
- 第二个台阶到 16384 条分支，CPI 在 5 到 6 之间，大于 main BTB 的 3 cycle latency，说明此时没有命中 main BTB，而是要等到取指和译码后，计算出正确的目的地址再回滚，导致了 5+ cycle latency；16384 对应 64KB L1 ICache 容量

那么 stride=4B uncond 的情况下就遗留了如下问题：

1. nano BTB 没表现出 96 的容量，只表现出接近 64 的容量
2. 没有观察到 2 predicted branches per cycle
3. 没有命中 main BTB

### stride=4B cond

stride=4B cond 的情况：

![](./arm-neoverse-v1-btb-4b-cond.png)

可以看到，图像上出现了如下比较显著的台阶：

- 第一个台阶到 48 条分支，CPI=1，对应了 96-entry 的 nano BTB，但是没有体现出完整的 96 的容量
- 之后没有明显的分界点，性能波动剧烈

nano BTB 只表现出 48 的容量，刚好是 96 的一半；同时没有观察到 2 predicted branches per cycle。考虑这两点，可以认为 nano BTB 的组织方式和分支类型有关，当分支过于密集（stride=4B）或者用条件分支（cond）时，不能得到完整的 96-entry 的大小，此时也会回落到 CPI=1 的情况。

那么 stride=4B cond 的情况下就遗留了如下问题：

1. 没有命中 main BTB

### stride=8B uncond

stride=8B uncond 的情况：

![](./arm-neoverse-v1-btb-8b-uncond.png)

可以看到，图像上出现了如下比较显著的台阶：

- 第一个台阶到 96 条分支，CPI=0.5，对应了 96-entry 的 nano BTB，体现了 2 predicted branches per cycle
- 第二个台阶到 8192 条分支，CPI=1，对应 main BTB，此时也对应了 64KB L1 ICache；此外，从 4096 开始有略微的上升

此时 nano BTB 完整地表现出了它的 96-entry 容量，并且实现了 CPI=0.5 的效果。main BTB 也实现了 CPI=1，考虑到它的容量不太可能单周期给出一个分支的结果，大概率是两个周期预测两条分支指令。

那么 stride=8B uncond 的情况下就遗留了如下问题：

1. 从 4096 条分支开始性能有略微的下降

### stride=8B cond

stride=8B cond 的情况：

![](./arm-neoverse-v1-btb-8b-cond.png)

可以看到，图像上出现了如下比较显著的台阶：

- 第一个台阶到 48 条分支，CPI=1，对应了 96-entry 的 nano BTB，没有 2 predicted branches per cycle，容量也只有 96 的一半
- 第二个台阶到 8192 条分支，CPI=2，对应 main BTB，此时也对应了 64KB L1 ICache

和之前一样，遇到 cond 分支，nano BTB 的容量只有一半，也观察不到 2 predicted branches per cycle。另一边，main BTB 的 CPI 也到了 2，意味着此时 main BTB 也只能两个周期预测一条分支指令，和之前的分析吻合。

那么为什么用条件分支，就不能预测两条分支指令了呢？猜测是，BTB 可以一次给出两条分支的信息，但是没有时间去同时预测这两条分支的方向。所以就回落到了普通的 2 cycle BTB 情况。

### stride=16B uncond

stride=16B uncond 的情况：

![](./arm-neoverse-v1-btb-16b-uncond.png)

可以看到，图像上出现了如下比较显著的台阶：

- 第一个台阶到 96 条分支，CPI=0.5，对应了 96-entry 的 nano BTB，体现了 2 predicted branches per cycle
- 第二个台阶到 2048 条分支，CPI=1；略微上升到 4096，此时是 64KB L1 ICache 的容量；到 8192 出现明显突变，对应 main BTB 容量

那么 stride=16B uncond 的情况下就遗留了如下问题：

1. 从 2048 条分支开始性能有略微的下降

### stride=16B cond

stride=16B cond 的情况：

![](./arm-neoverse-v1-btb-16b-cond.png)

可以看到，图像上出现了如下比较显著的台阶：

- 第一个台阶到 48 条分支，CPI=1，对应了 96-entry 的 nano BTB，没有 2 predicted branches per cycle，容量也只有 96 的一半
- 第二个台阶到 8192 条分支，CPI=2，对应 main BTB

预测的效果和 stride=8B cond 完全相同。

那么 stride=16B cond 的情况下就遗留了如下问题：

1. 64KB ICache 应该在 4096 条分支导致瓶颈，但是实际没有观察到

### stride=32B uncond

stride=32B uncond 的情况：

![](./arm-neoverse-v1-btb-32b-uncond.png)

可以看到，图像上出现了如下比较显著的台阶：

- 第一个台阶到 96 条分支，CPI=0.5，对应了 96-entry 的 nano BTB，体现了 2 predicted branches per cycle
- 第二个台阶到 1024 条分支，CPI=1；略微上升到 2048，此时是 64KB L1 ICache 的容量；到 8192 右侧出现明显突变

那么 stride=32B uncond 的情况下就遗留了如下问题：

1. 从 1024 条分支开始性能有略微的下降
2. 性能明显下降的点在 8192 右侧，而不是 8192

### stride=32B cond

stride=32B cond 的情况：

![](./arm-neoverse-v1-btb-32b-cond.png)

可以看到，图像上出现了如下比较显著的台阶：

- 第一个台阶到 48 条分支，CPI=1，对应了 96-entry 的 nano BTB，没有 2 predicted branches per cycle，容量也只有 96 的一半
- 第二个台阶到 2048 条分支，CPI=2，对应 64KB L1 ICache 容量，之后缓慢上升，到 8192 出现性能突变，对应 main BTB 容量

基本符合预期，只是在 stride=16B cond 的基础上，引入了 64KB L1 ICache 导致的性能下降。

### stride=64B uncond

stride=64B uncond 的情况：

![](./arm-neoverse-v1-btb-64b-uncond.png)

可以看到，图像上出现了如下比较显著的台阶：

- 第一个台阶到 96 条分支，CPI=0.5，对应了 96-entry 的 nano BTB，体现了 2 predicted branches per cycle
- 第二个台阶到 1024 条分支，CPI=1，对应 64KB L1 ICache 的容量
- 第三个台阶到 4096，CPI=3，对应 main BTB 的容量；main BTB 容量减半，意味着 main BTB 应当是个组相连结构

### stride=64B cond

stride=64B cond 的情况：

![](./arm-neoverse-v1-btb-64b-cond.png)

可以看到，图像上出现了如下比较显著的台阶：

- 第一个台阶到 48 条分支，CPI=1，对应了 96-entry 的 nano BTB，没有 2 predicted branches per cycle，容量也只有 96 的一半
- 第二个台阶到 1024 条分支，CPI=2，对应 64KB L1 ICache 容量，之后缓慢上升，到 4096 出现性能突变，对应 main BTB 容量；main BTB 容量只有 8192 的一半，意味着它是组相连结构

### 小结

测试到这里就差不多了，更大的 stride 得到的也是类似的结果，总结一下前面的发现：

- nano BTB 是 96-entry，1 cycle latency，对于 uncond 分支可以做到一次预测两条分支，大小不随着 stride 变化
- main BTB 是 8K-entry，2 cycle latency，对于 uncond 分支可以做到一次预测两条分支，此时可以达到 CPI=1；容量随着 stride 变化
- 64KB ICache 很多时候会比 main BTB 更早成为瓶颈

也总结一下前面发现了各种没有解释的遗留问题：

- stride=4B uncond/cond 的情况下，main BTB 没有像预期那样工作
- cond 分支情况下，没有 2 predicted branches per cycle，此时两级 BTB 分别可以做到 CPI=1 和 CPI=2，同时 nano BTB 容量减半到 48
- stride=8B uncond 的情况下，4096 条分支处出现了性能下降
- stride=16B uncond 的情况下，2048 条分支处出现了性能下降
- stride=32B uncond 的情况下，1024 条分支处出现了性能下降
- stride=32B uncond 的情况下，main BTB 导致的拐点应该在 8192，但实际上在右侧
- stride=16B cond 的情况下，64KB ICache 应该在 4096 条分支导致瓶颈，但是实际没有观察到

接下来尝试解析一下这些遗留问题背后的原理。部分遗留问题，并没有被解释出来，欢迎读者提出猜想。

## 解析遗留问题

## 总结

最后总结一下 Neoverse V1 的 BTB：

- 96-entry nano BTB, 1 cycle latency, at most 2 predicted branches per cycle
- 8K-entry main BTB, 2 cycle latency, at most 2 predicted branches every 2 cycles
