---
layout: post
date: 2024-09-21
tags: [cpu,microarchitecture,ibm,bp]
categories:
    - hardware
---

# IBM z15 Mainframe CPU 分支预测器学习笔记

## 背景

ISCA 2020 的一篇文章 [The IBM z15 High Frequency Mainframe Branch Predictor Industrial Product](https://ieeexplore.ieee.org/document/9138999) 非常详细地解析了 IBM z15 Mainframe CPU 的分支预测器设计。本文是对这篇论文的学习和整理的笔记。

<!-- more -->

## 设计思路

论文的第二节 Branch Prediction Design Considerations 提到了它设计分支预测器时需要考虑的事情。z15 处理器面向的是具有很大指令 footprint 的程序，为此准备了 128KB 的 L1 ICache，以及 4MB 的 L2 Private ICache。为了支撑 MB 级别的指令，BTB 也要相应增大。

IBM z 系列用的是变长指令集，指令长度可能是 2 或 4 或 6 字节，平均长度是 5 字节。考虑到每 5 条指令有一条分支指令，那就是每 25 个字节有一条分支指令，那么 4MB 的 L2 ICache 平均下来可能有 164K 条分支。因此，z15 设计了可以保存 128K 条分支的 L2 BTB。z15 的流水线很长，分支预测错误会带来 26 个周期的开销，因此分支预测的正确率就很重要。z15 处理器设计了两级的 BTB，L1 BTB（论文中称 BTB1）容量是 16K=2K x 8 way，L2 BTB（论文中称 BTB2）容量是 128K=32K x 4-way。为了加速 L1 BTB 的预测，z15 有 Column Predictor（CPRED，1K x 8）。为了预测分支的方向，z15 还引入了 PHT（short 和 long 两个 PHT，都是 512 x 8），Perceptron（16 x 2）。为了预测间接分支和返回指令的目的地址，z15 设计了 Changing Target Buffer（CTB，2K x 1）和 Call/Return Stack（CRS）。

## 具体实现

z15 采用的是分离式前端，分支预测器有 6 级的流水线，每一级分别记为 b0-b5。各级的功能如下：

> Indexing into the BTB arrays occurs in
> the b0 cycle, which when superimposed over the z15 core
> pipeline in figure 1 coincides with the very stage after a
> restart, but deviates away from the core pipeline after that.
> An array access cycle is in b1. Metadata from the arrays is
> obtained in b2, and hit detection and direction application
> on a per branch basis performed across the b2 and b3
> cycles. Ordering of the branches based on their low-order
> instruction address bits is also done in b3. In b4, the final
> prediction is prepared, including selection of the
> appropriate target address provider. The prediction is
> presented to the consumers, namely the IDU and ICM, in
> the b5 cycle.

如果等到 b5 才出预测结果就比较慢了，因此它还可以在 b2 周期出结果，利用的是 CPRED 预测器。在 CPRED 工作的情况下，每两个周期可以预测一个 taken branch，如果 CPRED 没有预测，那就需要每 5 个周期预测一个 taken branch，而在 SMT2 模式下，两个线程轮流访问 BTB，此时每个线程需要每 6 个周期预测一个 taken branch。

z15 的 L1 BTB 的 8-way 意味着在一个周期可以进行 8 条分支的预测，从 64B 的指令中，识别最多 8 条指令，从中找到第一条跳转的分支。为了优化性能和功耗，在面对连续的无分支指令的代码时，可以快速跳过，这里用的是 SKOOT（Skip Over OffseT）预测器，在 BTB 的分支记录了到下一次分支的距离，如果这个距离很长，那就可以快速跳过若干个 64B 指令块。

为了预测分支的方向，在 L1 BTB 里，也保存了 2 bit saturating counter，也就是 BTB 也充当了通常说的 BHT。除了 BHT 以外，为了预测分支方向，z15 记录了 Global Path Vector，也就是常说的 PHR，记录最近的 n 条 taken branch 的历史。z14 之前，GPV 记录了最近 9 条 taken branch 的历史，z14 和 z15，GPV 记录了最近 17 条 taken branch 的历史。GPV 中每个 taken branch 提供 2 bit 的信息。

GPV 和 PC 作为 TAGE 的输入，进行方向预测。z15 采用了两个 TAGE PHT，都是 512 x 8 way，一共是 8K 分支的容量，历史短的 TAGE PHT 只用最近 9 条 taken branch 的历史，历史长的 TAGE PHT 则会用完整的 17 条 taken branch 的历史。论文里比较详细地描述了 TAGE 的实现，基本和 A. Seznec 的设计是一样的，也做了 USE_ALT_ON_NA 的改进。除了 TAGE 以外，z15 还有 Perceptron 预测器，有 32 个 entry，16 x 2 way，把系数和 GPV 进行点积（GPV 的每个 bit 映射为 1 和 -1），根据结果的符号决定跳转的方向。

因此一共有 BHT、TAGE 和 Perceptron 可以提供方向预测。为了判断用哪个预测器来提供最终的方向，规则是：

1. 对于条件分支，记录它是否曾经跳和不跳过（Bidirectional），如果只往一个方向跳，就查 BHT
2. 如果两个方向都跳过，此时 Perceptron 优先级更高，如果 Perceptron 命中且置信度高，则用 Perceptron 的结果
3. 否则考察 TAGE 的预测结果，如果 TAGE 命中且置信度高，则用 TAGE 的结果
4. 如果 Perceptron 和 TAGE 都没有命中，再用 BHT 的结果

简单来说，优先级是 Perceptron > TAGE > BHT。

为了预测间接分支的目的地址，z15 上 PC 和 GPV 通过哈希映射到 CTB（Changing Target Buffer）的表项上，每个表项记录了分支的目的地址。

有意思的是，z15 指令集里没有单独的 call 和 return 指令，因此硬件需要识别间接分支里的 call 和 return 模式。论文里介绍了具体的识别方法，但目前主流指令集都做了区分（要么是单独的指令，要么建议编译器用特定的寄存器，标记 call 和 return），所以这个方法也没啥参考价值。

