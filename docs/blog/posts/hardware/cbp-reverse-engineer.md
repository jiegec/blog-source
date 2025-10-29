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

去年做了针对 Apple 和 Qualcomm 的条件分支预测器（Conditional Branch Predictor）的逆向，发到了 [arXiv](https://arxiv.org/abs/2411.13900) 上，也公开了[源码](https://arxiv.org/abs/2411.13900)。因为发现大家对处理器逆向比较感兴趣，但可能考虑到其复杂性而没有上手去实践，所以就拿这篇论文的方法，以 Apple M1 Firestorm 为例，讲述一下条件分支预测器具体是怎么逆向的，也是对论文的一个补充。

<!-- more -->

## 背景知识

首先介绍一下背景知识，我们要逆向条件分支预测器，那就要知道它是怎么工作的。条件分支预测器的思路大体上是：

1. 条件分支跳或不跳，其行为是高度可预测的
2. 预测的输入是，条件分支的地址，可能还有近期执行的若干条分支的历史；输出就是条件分支是跳或不跳

为了在硬件上实现这个算法，硬件上会维护一个表，表里的每一项记录了一个 2 位的饱和计数器，用来预测跳或不跳；查表时会对条件分支的地址以及近期执行的若干条分支的历史进行哈希，用哈希结果作为下标去读取表项，然后根据计数器的值来预测跳转方向。

![](./cbp-reverse-engineer-basic.png)

（图源 CMU ECE740 Computer Architecture: Branch Prediction）

目前主流的处理器，采用的都是 [TAGE](https://inria.hal.science/hal-03408381/document) 预测器，它在上述查表的思路以外，做了改进：

1. 观察到不同的分支，其预测所依赖的分支历史长度是不同的，有的分支不需要任何历史也可以预测地很好，有的分支会依赖距离比较近的某个或某些历史分支的跳转结果，有的分支会依赖更久远的历史
2. 分支历史越长，路径的种类就越多，那么分支预测器训练过程就会变慢，而训练过程中预测错误率会比较高，希望尽量在更短的时间内收敛
3. 为了解决不同分支对不同的历史长度的需求，TAGE 设计了多个表，采用从小到大不同的分支历史长度，同时进行预测，如果有多个表都提供了预测（只有 tag 匹配时提供预测），则取其中使用了最长的历史长度的预测结果

![](./cbp-reverse-engineer-tage.png)

（图源 [Half&Half: Demystifying Intel’s Directional Branch Predictors for Fast, Secure Partitioned Execution](https://cseweb.ucsd.edu/~tullsen/halfandhalf.pdf)）

因此为了逆向处理器的条件分支预测器，需要做的事情包括：

1. 找到它是如何记录分支历史的，通常来说，是使用分支的地址以及分支的目的地址，经过一系列的移位和异或，保存在寄存器当中
2. 找到它的 TAGE 算法包括多少个表，每个表有多大，是如何索引的，使用了多少长度的分支历史

## 分支历史的逆向

第一步是逆向处理器是如何记录分支历史的。教科书上讲分支历史的记录方法，主要是通过一个寄存器，每遇到一个条件分支，就记录它跳（记为 1）还是不跳（记为 0），每个分支记录 1 bit 的信息。但目前的很多处理器（Intel、Apple、Qualcomm、ARM 和部分 AMD），采用的是叫做 [Path History Register](https://ieeexplore.ieee.org/document/476809/) 的方式记录分支历史，它的思路是，设计一个长度为 $n$ 的寄存器 $\mathrm{PHR}$，每次遇到一个跳转的分支（不仅限于条件分支），就对寄存器进行左移，再把当前跳转的分支的地址和跳转地址经过一个哈希函数的映射，把哈希的结果异或到移位寄存器当中。用数学来表示的话，就是：

$\mathrm{PHR}_{\mathrm{new}} = (\mathrm{PHR}_{\mathrm{old}} \ll \mathrm{shamt}) \oplus \mathrm{footprint}$

其中 $\mathrm{footprint}$ 是通过分支的地址以及分支的目的地址计算哈希而来。那么，接下来要做的事情，就是，找到 $\mathrm{PHR}$ 的长度是多少位，每次左移了多少位，异或进去的 $\mathrm{footprint}$ 是如何计算而来的。

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
