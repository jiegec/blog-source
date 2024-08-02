---
layout: post
date: 2024-08-02
tags: [cpu,ooo,branch,prediction,arm,cortex,predictor]
categories:
    - hardware
---

# 分支预测的 2-taken 和 2-ahead

## 背景

随着 Zen 5 的推出，更多 Zen5 的架构设计细节被公开，可以看到 Zen 5 前端出现了令人瞩目的变化：引入了 2-taken, 2-ahead 分支预测的设计。这是什么意思？它架构上是怎么实现的？可以带来哪些性能提升？

<!-- more -->

## 背景知识

首先还是回顾一下处理器前端在做的事情：根据 PC，从 ICache 读取指令，然后译码，发给后端取执行。但是执行的的指令里有大量的分支指令，它们会改变 PC，后续指令需要从新的 PC 处取，但是取指的时候并不知道分支指令未来会如何跳转，如果每次分支指令都要刷流水线重新取指，就会产生很多的流水线空泡，因此就有了分支预测。

分支预测和取指是同时进行的：取指令的同时，也在预测这些指令是否会跳转，如果会跳转，跳转的目的地址是多少，用于指导下一个周期从哪里取指。为了做到这个事情，首先需要知道有没有分支或跳转指令，这个信息会保存在 BTB 中，或者要等到取指完成，译码后才知道哪些是分支或跳转指令。如果有，对于条件分支指令来说，需要一个方向预测器（CBP），判断分支是否会跳转，还需要一个分支目的地址缓存（BTB），如果分支要跳的话，知道要跳到什么地方。除了条件分支指令以外，针对 return 指令，跳转的地址和此前 call 对应，需要记录调用的返回地址栈（RAS）。针对其他的间接跳转指令，例如函数指针调用，一个跳转可能有多个目的地址，还需要一个针对间接跳转的目的地址的预测器（IBP）。这些组件（CBP、BTB、RAS 和 IBP）构成了现代处理器的分支预测器。

在此基础上，目前比较流行分离式/解耦式前端（Decoupled Frontend）：和耦合/非分离式前端相对，耦合前端是说分支预测器和指令缓存紧密协作，分支预测器指导下一次取指的地址，取出的指令立即用于分支预测器。分离式前端把分支预测器变成了生产者，生产取指的地址，然后指令缓存是生产者，消费取指的地址，从缓存读取指令，进行后续的译码，消费者和生产者之间通过队列（Fetch Target Queue）隔开。这样，分支预测器可以独立指令缓存工作，在前面抢跑，即使指令缓存出现了缺失，也可以继续预测未来很多个指令之后的分支。更进一步，还可以根据抢跑的这些分支的信息，提前把指令从 L2 缓存预取到 L1 指令缓存，那么未来指令缓存要取指令的时候，大概率已经在缓存当中了。

当然了，解耦式前端的抢跑也是有代价的：此时分支预测器对未来取出的指令实际上会是什么样是不知道的，只能依赖 BTB 中记录的历史信息，所以 BTB 一般都会做的比较大。但与此同时，耦合式前端可以在 L1 指令缓存从 L2 加载指令时做预译码，找到其中的分支，然后拿 L1 指令缓存作为更大的 BTB，例如 Apple M1 Firestorm 就可以拿巨大的 192KB L1 指令缓存作为 BTB，等效 BTB 容量特别巨大。孰好孰坏，现在还看不清楚。

那么一个分支，从分支预测，到取指，执行，会经历哪些阶段呢？首先是分支预测，分支预测器会把那些会跳转的情况找出来，因为它会影响下一次取指的地址；如果没有分支跳转，或者有分支但是不跳转，那就比较简单，下一次取指地址就直接顺着地址往下算就可以。取指译码以后，会和之前预测的情况做比对，如果发现预测成了分支，结果实际上不是分支，说明分支预测器错了，及时修正。执行的时候，按照分支指令的操作数，实际判断一下要不要跳转，和之前预测的结果比对。如果对了，那就皆大欢喜；如果错了，那就要刷掉那些错误预测的指令。当然还要通知一下分支预测器，让他更新预测的计数器。

接下来回到本文的主题：分支预测最近几年来比较大的一些改动。

## 2 branch

刚才提到，分支参与到预测，取指，执行等阶段之中，其中执行阶段是比较简单的，所以比较容易扩展，例如 Cortex-A77 引入了第二个分支执行单元，每个周期可以执行两条分支指令，目前很多高性能处理器都采用了两个分支执行单元。但大部分处理器每个周期只能预测一个分支，这样每个周期只用访问一次 BTB 等结构，那似乎两个分支执行单元没有什么用？毕竟如果第一个分支跳转了，那第二个分支的地址需要依赖第一个分支的目的地址计算得出，这样这两个分支的预测就一定程度上就串行化了，这个是比较困难的。但如果第一个分支不跳转，去预测第二个分支跳转或者不跳转，这个还是相对比较好支持的。这样，分支预测时，每个周期可以最多预测一个 taken 分支，但同时还可以有 not taken 分支。此外，还有那种从来没有 taken 过的分支，这种一般为了节省 BTB 存储，一般是不记录在 BTB 内部的。考虑到这些情况，设计两个分支执行单元会有一些收益。

但是为什么没有增加到三个呢？还真有，Zen 5 就增加到了三个分支执行单元，但是增加到三个的前提是每周期可以预测两个 taken 分支，否则性能收益很小。这是怎么做到的呢？下面我们来讨论这个问题。

## 2-taken/2-ahead

刚才提到，想要进一步提升分支预测和执行能力，需要支持每个周期预测更多的 taken 分支，刚才是 1 个，现在就要 2 个。ARM 在 Cortex-A78 上添加了 2-taken 分支预测的支持，也就是可以每周期最多可以预测两个 taken 的分支。这是怎么做到的？如果做的非常通用，就要像上面说的那样，先预测第一个分支，拿第一个分支预测的结果，再去预测第二个分支，这件事情要在一个周期内完成，这个挑战是很大的。我们来分析一下：

假如现在有四个基本块 A、B、C 和 D，并且按照这个顺序执行，也就是说，A 最后的指令是一个分支，跳转到 B，同理 B 跳转到 C，C 跳转到 D。经典的分支预测算法，用 A 去预测 B，用 B 去预测 C，用 C 去预测 D，这样每个周期预测一个 taken 分支。那么如果要实现 2-taken 预测算法，假如已知了 A，那就要预测 B 和 C，但是就必须先拿 A 预测 B，再拿 B 预测 C，这样就串行了，时序很难保证。当然也可以同时搞两套预测，一套用 A 预测 B，一套用 A 预测 C，但是这样每个分支要记录的信息就翻倍了。

在论文 Multiple-Block Ahead Branch Predictors 中可以看到一种更通用做法，称为 2-ahead：已知 A 和 B，用 A 去预测 C，用 B 去预测 D。此时分支预测的就是间隔一次以后的目的地址，而不是直接的目的地址，这样的设计下，BTB 等结构需要变成双端口，这样才能同时预测两个分支：A 和 B。预测出 C 和 D 以后，再用同样的办法去预测 E 和 F，这样持续下去。当然论文设计的比这里讲的更复杂一点，具体细节见论文。

我们不知道 ARM 具体如何实现的 2-taken，但是可以猜想它做了一些限制，例如虽然两个分支都是 taken，但是可能对偏移、地址有一些限制，例如要求在同一个 cacheline 内。Intel 的 Golden Cove 架构，AMD 的 Zen 4 架构也实现了 2-taken，都有或多或少类似的限制。因此，可以用 2-taken 表示限制比较多的每个周期可以预测 2 个 taken 的算法，而用 2-ahead 表示更加通用的预测 2 个 taken 的算法。

虽然做了 2-taken，只是分支预测的带宽增加了，每个周期可以预测更多的分支。但前面也提到了，分支预测器是生产者，指令缓存是消费者，生产者的性能提升了，那么消费者的性能也要相应提升才是。但是指令缓存是一片很大的 SRAM，功耗和时序都比较麻烦，所以改起来比较困难。如果单纯增加指令缓存一次取指的宽度，例如 8 字节提升到 16 字节，对于分支密度低的情况比较有效，但如果分支很多，那么这样效果也不会很好，要提升性能，就要考虑双端口，每个周期从两个不同的地址取指。这就是 Zen 5 做的事情。

## 2-fetch

Zen 5 除了 2-taken 以外，还实现了 2-fetch，也就是每个周期可以预测未来的两个分支，并从两个地址取指令，分别译码，然后再拼起来。此外，Zen 5 的双取指还可以服务于超线程，每个线程用一个取指流水线。当超线程空闲的时候，两个取值流水线可以服务于同一个线程，提供更高的性能。

目前 Zen 5 的实现细节还不清晰，期待未来更多的微架构解析。

## 参考文献

- [Zen 5’s 2-Ahead Branch Predictor Unit: How a 30 Year Old Idea Allows for New Tricks](https://chipsandcheese.com/2024/07/26/zen-5s-2-ahead-branch-predictor-unit-how-30-year-old-idea-allows-for-new-tricks/)
- [Arm's New Cortex-A78 and Cortex-X1 Microarchitectures: An Efficiency and Performance Divergence - Anandtech](https://www.anandtech.com/show/15813/arm-cortex-a78-cortex-x1-cpu-ip-diverging/2)
- [AMD Zen 5 Technical Deep Dive](https://www.techpowerup.com/review/amd-zen-5-technical-deep-dive/3.html)
- [AMD Zen 5 Architecture Reveal: A Ryzen 9000 And Ryzen AI 300 Deep Dive](https://hothardware.com/reviews/amd-ryzen-ai-zen-5-architecture-overview)
- [AMD deep-dives Zen 5 architecture — Ryzen 9000 and AI 300 benchmarks, RDNA 3.5 GPU, XDNA 2, and more](https://www.tomshardware.com/pc-components/cpus/amd-deep-dives-zen-5-ryzen-9000-and-strix-point-cpu-rdna-35-gpu-and-xdna-2-architectures/4)
- [Optimizations Enabled by a Decoupled Front-End Architecture](https://cseweb.ucsd.edu/~calder/papers/UCSD-CS00-645.pdf)
- [The Cortex-A77 µarch: Added ALUs & Better Load/Stores](https://www.anandtech.com/show/14384/arm-announces-cortexa77-cpu-ip/3)
- [Multiple-Block Ahead Branch Predictors](https://dl.acm.org/doi/pdf/10.1145/237090.237169)
- [Popping the Hood on Golden Cove](https://chipsandcheese.com/2021/12/02/popping-the-hood-on-golden-cove/)
- [AMD Zen 4 Ryzen 9 7950X and Ryzen 5 7600X Review: Retaking The High-End](https://www.anandtech.com/show/17585/amd-zen-4-ryzen-9-7950x-and-ryzen-5-7600x-review-retaking-the-high-end/8)
