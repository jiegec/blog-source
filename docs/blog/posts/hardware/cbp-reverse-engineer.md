---
layout: post
date: 2025-10-28
tags: [cpu,apple,m1,firestorm,cbp,re]
draft: true
categories:
    - hardware
---

# 条件分支预测器逆向（以 Apple M1 Firestorm 为例）

## 背景

去年我完成了针对 Apple 和 Qualcomm 条件分支预测器（Conditional Branch Predictor）的逆向工程研究，相关论文已发表在 [arXiv](https://arxiv.org/abs/2411.13900) 上，并公开了[源代码](https://arxiv.org/abs/2411.13900)。考虑到许多读者对处理器逆向工程感兴趣，但可能因其复杂性而望而却步，本文将以 Apple M1 Firestorm 为例，详细介绍条件分支预测器的逆向工程方法，作为对原论文的补充说明。

<!-- more -->

## 背景知识

首先介绍一些背景知识。要逆向工程条件分支预测器，需要先了解其工作原理。条件分支预测器的基本思路是：

1. 条件分支的跳转行为（跳或不跳）通常是高度可预测的
2. 预测器的输入包括条件分支的地址，以及近期执行的若干条分支的历史记录；输出则是预测该条件分支是否跳转

为了在硬件上实现这一算法，处理器会维护一个预测表，表中每一项包含一个 2 位饱和计数器，用于预测跳转方向。查表时，系统会对条件分支地址以及近期执行的分支历史进行哈希运算，使用哈希结果作为索引读取表项，然后根据计数器的值来预测分支的跳转方向。

![](./cbp-reverse-engineer-basic.png)

（图源 CMU ECE740 Computer Architecture: Branch Prediction）

目前主流处理器普遍采用 [TAGE](https://inria.hal.science/hal-03408381/document) 预测器，它在上述基础查表方法的基础上进行了重要改进：

1. 观察到不同分支的预测所需的历史长度各不相同：有些分支无需历史信息即可准确预测，有些依赖近期分支的跳转结果，而有些则需要更久远的历史信息
2. 分支历史越长，可能的路径组合就越多，导致预测器训练过程变慢，训练期间的预测错误率较高，因此希望尽快收敛
3. 为满足不同分支对历史长度的需求，TAGE 设计了多个预测表，每个表使用不同长度的分支历史。多个表同时进行预测，当多个表都提供预测结果时（仅在 tag 匹配时提供预测），选择使用最长历史长度的预测结果

![](./cbp-reverse-engineer-tage.png)

（图源 [Half&Half: Demystifying Intel’s Directional Branch Predictors for Fast, Secure Partitioned Execution](https://cseweb.ucsd.edu/~tullsen/halfandhalf.pdf)）

因此，要逆向工程处理器的条件分支预测器，需要完成以下工作：

1. 确定分支历史的记录方式：通常涉及分支地址和目的地址，通过一系列移位和异或操作，将结果存储在寄存器中
2. 确定 TAGE 算法的具体实现：包括表的数量、每个表的大小、索引方式以及使用的分支历史长度

## 分支历史的逆向

第一步是逆向工程处理器记录分支历史的方式。传统教科书方法使用一个寄存器，每当遇到条件分支时记录其跳转方向（跳转记为 1，不跳转记为 0），每个分支占用 1 bit。然而，现代处理器（包括 Intel、Apple、Qualcomm、ARM 和部分 AMD）普遍采用 [Path History Register](https://ieeexplore.ieee.org/document/476809/) 方法。这种方法设计一个长度为 $n$ 的寄存器 $\mathrm{PHR}$，每当遇到跳转分支（包括条件分支和无条件分支）时，将寄存器左移，然后将当前跳转分支的地址和目的地址通过哈希函数映射，将哈希结果异或到移位寄存器中。用数学公式表示为：

$\mathrm{PHR}_{\mathrm{new}} = (\mathrm{PHR}_{\mathrm{old}} \ll \mathrm{shamt}) \oplus \mathrm{footprint}$

其中 $\mathrm{footprint}$ 是通过分支地址和目的地址计算得到的哈希值。接下来的任务是确定 $\mathrm{PHR}$ 的位宽、每次左移的位数，以及 $\mathrm{footprint}$ 的计算方法。

首先观察这个更新公式，它把最近的 $\lceil n / \mathrm{shamt} \rceil$ 条跳转的分支信息压缩存储到了 $n$ 位的 $\mathrm{PHR}$ 寄存器当中。而更早的分支的历史信息，随着移位的累积，对 $\mathrm{PHR}$ 的贡献为零。

那么首先第一个实验要做的是，观察 $\mathrm{PHR}$ 能够记录最近多少条分支的历史。具体做法是，构建一个分支历史序列：

1. 首先是一个条件分支，按照 50% 的概率随机跳或者不跳
2. 然后是若干条无条件分支
3. 最后也是一个条件分支，跳转方向和第一个条件分支相同

接下来分情况讨论：

1. 如果在预测最后一个条件分支时，分支历史 $\mathrm{PHR}$ 中，依然记录了第一个条件分支的历史，那么预测器应当可以准确地预测最后一个条件分支的方向
2. 反之，如果中间的无条件分支个数足够多，使得第一个条件分支的跳转与否，对预测最后一个条件分支时的分支历史 $\mathrm{PHR}$ 没有影响，那么预测器只能以 50% 的概率预测正确

所以我们可以构造上面的程序，调整中间无条件分支的数量，通过性能计数器来统计分支预测器的错误率，可以找到一个拐点，当无条件分支超过这个数量的时候，第二个条件分支会从 0% 的错误预测率提升到 50%，这就对应了 $\mathrm{PHR}$ 能记录的多少条分支的历史信息，也就是 $\lceil n / \mathrm{shamt} \rceil$。

经过测试，可以发现这个阈值是 100：Apple M1 Firestorm 上，最多可以记录最近 100 条分支的历史信息。

## 引用文献

- [Dissecting Conditional Branch Predictors of Apple Firestorm and Qualcomm Oryon for Software Optimization and Architectural Analysis](https://arxiv.org/abs/2411.13900)
- [Half&Half: Demystifying Intel’s Directional Branch Predictors for Fast, Secure Partitioned Execution](https://cseweb.ucsd.edu/~tullsen/halfandhalf.pdf)
