---
layout: post
date: 2024-12-27
tags: [cpu,uarch-review]
categories:
    - hardware
---

# CPU 微架构逆向方法学

## 背景

最近做了不少微架构的评测，其中涉及到了很多的 CPU 微架构的逆向：

- [AMD Zen 5 微架构评测](./amd-zen5.md)
- [ARM Neoverse V2 微架构评测](./arm-neoverse-v2.md)
- [Apple M1 微架构评测](./apple-m1.md)
- [Apple M4 微架构评测](./apple-m4.md)
- [Intel Golden Cove 微架构评测](./intel-golden-cove.md)
- [Intel Gracemont 微架构评测](./intel-gracemont.md)
- [Intel Redwood Cove 微架构评测](./intel-redwood-cove.md)
- [Qualcomm Oryon 微架构评测](./qualcomm-oryon.md)

因此总结一下 CPU 微架构逆向方法学。

<!-- more -->

## 定义

首先定义一下：什么是 CPU 微架构逆向，我认为 CPU 微架构逆向包括两部分含义：

1. 在已经知道某 CPU 微架构采用某种设计，只是不知道其设计参数时，通过逆向，得到它的设计参数
2. 在不确定某 CPU 微架构采用的是什么设计，给出一些可能的设计，通过逆向，排除或确认其设计，再进一步找到它的设计参数

举一个例子，已经知道某 CPU 微架构有一个组相连的 L1 DCache，但不知道它的容量，几路组相连，此时通过微架构逆向的方法，可以得到它的容量，具体是几路组相连，进一步可能把它的 Index 函数也逆向出来。这是第一部分含义。

再举一个例子，已经知道某 CPU 微架构有一个分支预测器，但不知道它使用了什么信息来做预测，可能用了分支的地址，可能用了分支要跳转的目的地址，可能用了分支的方向，这时候通过微架构逆向的方法，对不同的可能性做排除，找到真正的那一个。如果不能排除到只剩一个可能，或者全部可能都被排除掉，说明实际的微架构设计和预期不相符。

第一部分含义，目前已经有大量的成熟的 Microbenchmark（针对微架构 Microarchitecture 设计的 Benchmark，叫做 Microbenchmark）来解决，它们针对常见的微架构设计，实现了对相应设计参数的逆向的 Microbenchmark，可以在很多平台上直接使用。第二部分含义，目前还只能逐个分析，去猜测背后的设计，再根据设计去构造对应该设计的 Microbenchmark。

下面主要来介绍，设计和实现 Microbenchmark 的方法学。

## 原理

首先要了解 Microbenchmark 的原理，它的核心思路就是，通过构造程序，让某个微架构部件成为瓶颈，接着在想要逆向的设计参数的维度上进行扫描，通过某种指标来反映是否出现了瓶颈，通过瓶颈对应的设计参数，就可以逆向出来设计参数的取值。这一段有点难理解，下面给一个例子：

比如要测试的是 L1 DCache 的容量，那就希望 L1 DCache 的容量变成瓶颈。为了让它成为瓶颈，那就需要不断地访问一片内存，它的大小比 L1 DCache 要更大，让 L1 DCache 无法完整保存下来，出现缓存缺失。为了判断缓存缺失是否出现，可以通过时间或周期，因为缓存缺失肯定会带来性能损失，也可以直接通过缓存缺失的性能计数器。既然要逆向的设计参数是 L1 DCache 的容量，那就在容量上进行一个扫描：在内存中开辟不同大小的数组，比如一个是 32KB，另一个是 64KB，每次测试的时候只访问其中一个数组。每个数组扫描访问若干次，然后统计总时间或周期数或缓存缺失次数。假如实际 L1 DCache 容量介于 32KB 和 64KB 之间，那么应该可以观察到 64KB 数组大小测得的性能相比 32KB 有明显下降。如果把测试粒度变细，每 1KB 设置一个数组大小，最终就可以确定实际的 L1 DCache 容量。

在上面这个例子里，成为瓶颈的微架构部件是 L1 DCache，想要逆向的设计参数是它的容量，反映是否出现瓶颈的指标是性能或缓存缺失次数，构造的程序做的事情是不断地访问一个可变大小的数组，其中数组大小和想要逆向的设计参数是挂钩的。

因此可以总结出 Microbenchmark 设计的几个要素：

1. 针对什么微架构部件
2. 针对该部件的什么设计参数
3. 反映出现瓶颈的指标是什么
4. 如何构造程序来导致瓶颈出现
5. 程序在什么情况下会导致瓶颈出现
6. 程序的参数如何对应到设计参数上

比如上面的 L1 DCache 容量的测试上，这几个要素的回答是：

1. 针对什么微架构部件：L1 DCache
2. 针对该部件的什么设计参数：L1 DCache 的容量
3. 反映出现瓶颈的指标是什么：时间，周期数，缓存缺失次数
4. 如何构造程序来导致瓶颈出现：在内存中开辟数组，然后不断地扫描访问
5. 程序在什么情况下会导致瓶颈出现：数组大小超过 L1 DCache 容量
6. 程序的参数如何对应到设计参数上：数组的大小对应到 L1 DCache 的容量

假如要设计一个针对 ROB(ReOrder Buffer) 容量的测试，思考同样的要素：

1. 针对什么微架构部件：ROB
2. 针对该部件的什么设计参数：ROB 能容纳多少条指令
3. 反映出现瓶颈的指标是什么：时间，周期数
4. 如何构造程序来导致瓶颈出现：在 ROB 开头和结尾各放一条长延迟指令，中间填充若干条指令
5. 程序在什么情况下会导致瓶颈出现：如果指令填充得足够多，导致结尾的长延迟指令不能进入 ROB，那么它无法被预测执行
6. 程序的参数如何对应到设计参数上：把结尾的长延迟指令阻拦在 ROB 之外时，在 ROB 中的指令数

思考明白这些要素，就可以知道怎么设计出一个 Microbenchmark 了。

原理介绍完了，下面介绍一些常用的方法。

## 指标的获取

上面提到，为了反映出瓶颈，需要有一个指标，它最好能够精确地反映出瓶颈的发生与否，同时也尽量要减少噪声。能用的指标不多，只有两类：

1. 时间：最通用，所有平台都可以用，在程序前后各记一次时间，取差
2. 性能计数器：使用起来比较麻烦，有时需要 root 权限，或者硬件相关信息不公开，又或者硬件就没有实现对应的性能计数器。各平台性能计数器可用情况：
    1. Windows：可用，有现成 [API](https://learn.microsoft.com/en-us/windows/win32/perfctrs/performance-counters-portal)
    2. macOS：可用，[有逆向出来的私有框架 API](https://gist.github.com/ibireme/173517c208c7dc333ba962c1f0d67d12)
    3. Linux：可用，[有现成 API](https://man7.org/linux/man-pages/man2/perf_event_open.2.html)
    4. iOS：在 iOS 外可以通过 Xcode Instruments 访问所有 PMU，但不方便自动化；在 iOS 内只能通过 [PROC_PIDTHREADCOUNTS](https://github.com/Androp0v/PowerMetricsKit/blob/3be0fd2d61785d848a32b6f5ea59aacad7739909/Sources/SampleThreads/sample_threads.c#L23) 获得周期数和指令数
    5. Android：需要 root 或通过 adb shell 使用，比较麻烦，[API](https://man7.org/linux/man-pages/man2/perf_event_open.2.html) 和 Linux 一样
    6. HarmonyOS NEXT：没找到方案

虽然测时间最简单也最通用，但它会受到频率波动的限制，如果在运行测试的时候，频率剧烈变化（特别是手机平台），引入了大量噪声，就会导致有效信息被淹没在噪声当中。

其中性能计数器是最为精确的，虽然使用起来较为麻烦，但也确实支撑了很多更深入的 CPU 微架构的逆向。希望硬件厂商看到这篇文章，不要为了避免逆向把性能计数器藏起来：因为它对于应用的性能分析真的很有用。具体怎么用性能计数器，可以参考一些现成的 Microbenchmark 框架。

在有异构核的处理器上，为了保证测试的是预期微架构的核心，一般还会配合绑核，绑核在除了 macOS 和 iOS 以外的系统都可以直接指定绑哪个核心，而 macOS 和 iOS 只能通过指定 QoS 来建议调度器调度到 P 核还是 E 核，首先是不能确定是哪个 P 核或哪个 E 核，其次这只是个建议，并非强制。

## 套路

接下来介绍一些构造瓶颈的一些常见套路：

1. 测试容量（比如各级 I/D Cache 和 TLB）：构造一个程序，去把容量用满，当容量被用满的时候，就可以观察到性能下降
2. 测试微架构队列或 Buffer 深度（比如 ROB，寄存器堆，调度队列）：在队列开头通过指令堵住队列的出队，接着不断地向队列中入队新的指令，当队列满的时候，不再能够入队新的指令，此时再引入一些原来不会被堵住的指令，现在因为队列被堵住了而进不去，导致性能下降
3. 测试组相连结构（比如 BTB，Cache 等组相连结构）：组相连结构下，每个 Index 内的容量是固定的，通过测试容量，可以得到有多少 Index 被覆盖了，如果通过修改 Index 函数的输入（比如 PC），使得某些 Index 无法被访问到，就可以观察到容量上的减少，并且实际容量也反馈出了还有多少 Index 能够被访问到的信息
4. 构造 pointer chasing：以 8B(对应 64 位指针)、缓存行大小或页大小为粒度，进行随机打乱，然后把它们用指针串联起来，前一个指针指向的内存中保存后一个指针的地址
5. 构造长延迟指令：在测试指令队列相关的场景下常用，通常可以用 pointer chasing long latency load 或者一段具有串行依赖的浮点除法或开根指令来实现

再介绍一些常见的坑：

1. 尽量用汇编来构造测例，C/C++ 编译器可能会带来不期望的行为
2. 链接器有一些行为可能是需要避免的，例如它可能会修改一些指令
3. 链接器还可能有一些局限性，例如它不支持巨大的对齐
4. Linux 内核会做优化，例如 Copy-on-Write 和 Transparent Huge Page

## 现成 Microbenchmark

实际上，现在已经有很多现成的 Microbenchmark，以及一些记录了 Microbenchmark 的文档：

- <https://www.agner.org/optimize/>
- <https://github.com/clamchowder/Microbenchmarks/>
- <https://github.com/JamesAslan/MicroArchBench>
- <https://github.com/name99-org/AArch64-Explore>
- <https://github.com/jiegec/cpu-micro-benchmarks>

以及一些用 Microbenchmark 做逆向并公开的网站：

- <https://chipsandcheese.com>
- <https://www.anandtech.com>（可惜不再更新）
- <https://blog.hjc.im/>
- <https://www.zhihu.com/people/jamesaslan>
- <https://uops.info>
- 本博客

如果你想要去逆向某个微架构的某个部件，但不知道怎么做，不妨在上面这些网站上寻找一下，是不是已经有现成的实现了。

如果你对如何编写这些 Microbenchmark 不感兴趣，也可以试试在自己电脑上运行这些程序，或者直接阅读已有的分析。
