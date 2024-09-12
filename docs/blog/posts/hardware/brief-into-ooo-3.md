---
layout: post
date: 2024-09-12
tags: [ooo,cpu,bp,prediction,frontend,brief-into-ooo]
categories:
    - hardware
---

# 浅谈乱序执行 CPU（三：前端）

本文的内容已经整合到[知识库](/kb/hardware/ooo_cpu.html)中。

## 背景

这是 [浅谈乱序执行 CPU](brief-into-ooo.md) 系列博客的第三篇。

本文主要讨论处理器前端的部分。

本系列的所有文章：

- [浅谈乱序执行 CPU（一：乱序）](./brief-into-ooo.md)
- [浅谈乱序执行 CPU（二：访存）](./brief-into-ooo-2.md)
- [浅谈乱序执行 CPU（三：前端）](./brief-into-ooo-3.md)

<!-- more -->

## 处理器前端

再来分析一下乱序执行 CPU 的前端部分。以 RISC-V 为例，指令长度有 4 字节或者 2 字节两种，其中 2 字节属于压缩指令集。如何正确并高效地进行取指令译码？

首先，我们希望前端能够尽可能快地取指令，前端的取指能力要和后端匹配，比如对于一个四发射的 CPU，前端对应地需要一个周期取 `4*4=16` 字节的指令。但是，这 16 字节可能是 4 条非压缩指令，也可能是 8 条压缩指令，也可能是混合的情况。所以，这里会出现一个可能出现指令条数不匹配的情况，所以中间可以添加一个 Fetch Buffer，比如 [BOOM](https://github.com/riscv-boom/riscv-boom) 的实现中，L1 ICache 每周期读取 16 字节，然后进行预译码，出来 8 条指令，保存到 Fetch Buffer 中。这里需要考虑以下几点：首先从 ICache 读取的数据是对齐的，但是 PC 可能不是，比如中间的地址。其次，可能一个 4 字节的非压缩指令跨越了两次 Fetch，比如前 2 个字节在前一个 Fetch Bundle，后 2 个字节在后一个 Fetch Bundle；此外，每个 2 字节的边界都需要判断一下是压缩指令还是非压缩指令。一个非常特殊的情况就是，一个 4 字节的指令跨越了两个页，所以两个页都需要查询页表；如果恰好在第二个页处发生了页缺失，此时 epc 是指令的起始地址，但 tval 是第二个页的地址，这样内核才知道是哪个页发生了缺失。

其次，需要配合分支预测。如果需要保证分支预测正确的情况下，能够在循环中达到接近 100% 的性能，那么，在 Fetch 分支结尾的分支指令的同时，需要保证下一次 Fetch 已经得到了分支预测的目的地址。这个就是 BOOM 里面的 L0 BTB (1-cycle redirect)。但是，一个周期内完成的分支预测，它的面积肯定不能大，否则时序无法满足，所以 BOOM 里面还设计了 2-cycle 和 3-cycle 的比较高级的分支预测器，还有针对函数调用的 RAS（Return Address Stack）。

分支预测也有很多方法。比较简单的方法是实现一个 BHT，每个项是一个 2 位的饱和计数器，超过一半的时候增加，少于一半时减少。但是，如果遇到了跳转/不跳转/跳转/不跳转这种来回切换的情况，准确率就很低。一个复杂一些的设计，就是用 BHR，记录这个分支指令最近几次的历史，对于每种可能的历史，都对应一个 2 位的饱和计数器。这样，遇到刚才所说的情况就会很好地预测。但实践中会遇到问题：如果在写回之前，又进行了一次预测，因为预测是在取指的时候做的，但是更新 BPU 是在写回的时候完成的，这时候预测就是基于旧的状态进行预测，这时候 BHR 就会出现不准确的问题；而且写回 BPU 的时候，会按照原来的状态进行更新，这个状态可能也是错误的，导致丢失一次更新，识别的模式从跳转/不跳转/跳转/不跳转变成了跳转/跳转/跳转/不跳转，这样又会预测错误。一个解决办法是，在取指阶段，BPU 预测完就立即按照预测的结果更新 BHR，之后写回阶段会恢复到实际的 BHR 取值。论文 [The effect of speculatively updating branch history on branch prediction accuracy, revisited](https://dl.acm.org/doi/10.1145/192724.192756) 和 [Speculative Updates of Local and Global Branch History: A Quantitative Analysis](https://jilp.org/vol2/v2paper1.pdf) 讨论了这个实现方式对性能的影响。

比较容易做预测更新和恢复的是全局分支历史，可以维护两个 GHR（Global History Register），一个是目前取指令最新的，一个是提交的最新的。在预测的时候，用 GHR 去找对应的 2-bit 状态，然后把预测结果更新到 GHR 上。在预测失败的时候，把 GHR 恢复为提交的状态。如果要支持一个 Fetch Packet 中有多个分支，可以让 GHR 对应若干个 2-bit 状态，分别对应相应位置上的分支的状态，当然这样面积也会增加很多。

除了记录条件分支的跳与不跳以外，通常还可以维护 taken branch 的地址，记录这样的分支历史的 GHR 就叫做 PHR（Path History Register）。

目前比较主流的分支预测算法就是 TAGE 了：维护多个表，每个表采取的历史长度不同，呈几何级数，使得需要比较短的历史就可以预测的分支可以更快的预热，需要比较长的历史才能预测的分支也可以有较好的准确度。

我在博客 [三星 Exynos CPU 微架构学习笔记](./samsung-exynos-cpu.md) 中详细分析了 Exynos 微架构的前端设计，建议感兴趣的读者阅读。

### Short Forward Branch

论文 [SonicBOOM: The 3rd Generation Berkeley Out-of-Order Machine](https://carrv.github.io/2020/papers/CARRV2020_paper_15_Zhao.pdf) 提到了一个有意思的优化：Short Forward Branch。它面对的场景是一些小的 if 语句，在 if 的条件满足时，执行少量的指令。正常来说，这样的代码会被编译成一个 Forward 的分支，被跳过的就是 if 条件满足时要执行的代码对应的指令。如果分支比较好预测，那现有的分支预测器就可以得到很好的性能，但如果分支不好预测，例如它会依赖数据的值，并且具有一定的随机性，这时候性能就会下降。为了解决这个问题，可以用条件执行来代替分支：把分支指令替换为比较指令，然后根据比较的结果来条件执行本来可能会被跳过的指令。下面是论文中给的例子，说的比较的清晰：

![](./brief-into-ooo-3-sfb.png)

比较有意思的是，这个优化是完全由硬件来做的，而不是编译器。当然了，如果编译器要做的前提是硬件支持这类标量的条件执行指令，虽然 Zicond 扩展确实提供了类似的功能，很多 RISC-V 实现还没有实现 Zicond。硬件上做的话，就不需要扩展指令集，直接在前端进行识别，当发现这种 Short Forward Branch 时，把分支指令本身改成一条 set-flag 指令，然后把分支到跳转目的地这一段的指令改为条件执行。这样就不需要进行分支预测了，无论原来的分支是否跳转，后续的这些指令都会进入流水线，看起来做了更多的事情，但很多时候反而比错误的分支预测还要快。

这个优化思路在 Intel 的专利 [Converting conditional short forward branches to computationally equivalent predicated instructions](https://patents.google.com/patent/US9367314B2/en) 也有阐述，不知道这个优化有没有实际加到 Intel 的处理器当中。

那么这样的指令序列在实际的程序里出现的多吗？论文 [The Effects of Predicated Execution on Branch Prediction](http://ieeexplore.ieee.org/document/717459/) 分析了这个问题，结论是还真不少。当然了，这篇论文主要的论点是，指令集应该引入各种条件执行指令，这样编译器就可以利用现有处理器的条件执行指令来优化，没有去讨论纯硬件的实现方法。


从 SiFive 提交给 GCC 的 [patch](https://patchwork.ozlabs.org/project/gcc/patch/20190430234741.8120-1-jimw@sifive.com/#2163277) 也可以看到，类似的优化被实装到了 SiFive 的 CPU 当中，不过这里做的会更加简单，只考虑了分支跳过一条指令的情况，这种也比较好实现，可以在现有的指令融合机制的基础上，把两条指令合成一条：

> The SiFive 7 series cores have macro fusion support to convert a branch over a
> single instruction into a conditionally executed instruction.  This adds a
> conditional move pattern, enabled only for the SiFive 7 series cores, that
> implements the initial optimization support for this feature.  This gives us
> about a 10% increase in coremark scores for this core.

SiFive 的专利 [Macro-op fusion](https://patents.google.com/patent/US10996952B2/en) 也提到了很多在 RISC-V 上实现的指令融合的优化，下面举几个例子：

```asm
    bne x1, x0, target
    add x3, x3, 1
target:
```

可以转化为：

```asm
    ifeqz_addi x3, x3, x1, 1
```

这就是上面所说的 SiFive 实现的只跳过单条指令的 Short Forward Branch，把 bne + add 指令变成了条件 add 指令，并且自带和 0 比较的逻辑：如果 x1 == 0（ifeqz，if equals to zero），就设置 x3 = x3 + 1，否则 x3 保持不变。类似地，把 add 换成 sub 也可以类似地做融合，甚至连函数调用 jal 指令也可以。

还有一个有趣的指令融合场景：

```asm
    beq x8, x9, skip
    j target
skip:
    // ...
target:
```

可以融合为：

```asm
    jne x8, x9, target
```

你可能会觉得，为什么编译器要多此一举，不直接生成一个 bne？答案是 RISC-V 的 bne 的立即数范围太小，要想跳到更大的范围，就需要用 j 指令，于是编译器只好用 beq + j 的组合来实现大范围的 bne。然后 SiFive 的处理器会识别这种模式，把它转换成一条 jne：条件分支，但又有 j 指令的 imm 跳转范围。这也挺有意思的，指令在设计的时候，不好做太多的 imm 位数，编译器因此生成了更复杂的代码，硬件再翻译回来。

苹果申请了 [Using a Next Fetch Predictor Circuit with Short Branches and Return Fetch Groups](https://patents.google.com/patent/US20240028339A1/en) 专利，它和上面提到的优化不太一样，但是有些类似。专利里提到了这么几种情况：

- 如果 Fetch Group 内有一个要跳转的分支指令会 Forward 跳转到同一个 Fetch Group 内部，原来的做法是从分支指令的目的地址再 Fetch 一次，但既然是同一个 Fetch Group，Fetch 分支指令的同时，已经把从分支的目的地址开始的指令取进来了，跳过中间的指令，把两段指令拼接起来，可以省下重新 Fetch 一次的时间。
- 如果 Fetch Group 内有一条 call 指令，在原来的做法里，call 指令之后的指令就被丢弃了，等到未来 return 回来的时候，再重新 Fetch 一次；专利里的做法是，在 call 的时候，把 call 指令之后的指令保存下来，当未来 return 回来的时候，不再重新 Fetch，而是取出保存下来的 call 指令之后的指令，这样就节省了重新 Fetch 一次的时间。

因此它的目的主要是解决重复 Fetch 的能耗问题。
