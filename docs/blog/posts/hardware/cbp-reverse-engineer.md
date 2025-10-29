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

### 历史长度

首先观察这个更新公式，它把最近的 $\lceil n / \mathrm{shamt} \rceil$ 条跳转的分支信息压缩存储到了 $n$ 位的 $\mathrm{PHR}$ 寄存器当中。而更早的分支的历史信息，随着移位的累积，对 $\mathrm{PHR}$ 的贡献为零。

那么首先第一个实验要做的是，观察 $\mathrm{PHR}$ 能够记录最近多少条分支的历史。具体做法是，构建一个分支历史序列：

1. 首先是一个条件分支，按照 50% 的概率随机跳或者不跳
2. 然后是若干条无条件分支
3. 最后也是一个条件分支，跳转方向和第一个条件分支相同

接下来分情况讨论：

1. 如果在预测最后一个条件分支时，分支历史 $\mathrm{PHR}$ 中，依然记录了第一个条件分支的历史，那么预测器应当可以准确地预测最后一个条件分支的方向
2. 反之，如果中间的无条件分支个数足够多，使得第一个条件分支的跳转与否，对预测最后一个条件分支时的分支历史 $\mathrm{PHR}$ 没有影响，那么预测器只能以 50% 的概率预测正确

所以我们可以构造上面的程序，调整中间无条件分支的数量，通过性能计数器来统计分支预测器的错误率，可以找到一个拐点，当无条件分支超过这个数量的时候，第二个条件分支会从 0% 的错误预测率提升到 50%，这就对应了 $\mathrm{PHR}$ 能记录的多少条分支的历史信息，也就是 $\lceil n / \mathrm{shamt} \rceil$。

经过[测试](https://github.com/jiegec/cpu-micro-benchmarks/blob/master/src/phr_size_gen.cpp)：

```csv
# 第一列：第二步插入的无条件分支数量加一
# 第二列到第四列：分支预测错误概率的 min/avg/max
# 第五列：每次循环的周期数
size,min,avg,max,cycles
97,0.00,0.00,0.01,216.87
98,0.00,0.00,0.01,221.02
99,0.00,0.00,0.01,225.18
100,0.00,0.00,0.01,229.17
101,0.45,0.50,0.53,331.97
102,0.47,0.50,0.54,336.27
103,0.46,0.50,0.54,339.85
```

可以发现这个阈值是 100：Apple M1 Firestorm 上，最多可以记录最近 100 条分支的历史信息。

!!! question "分支预测错误率是怎么测量的？"

    处理器内置了性能计数器，会记录分支预测错误次数。在 Linux 上，可以用 perf 子系统来读取；在 macOS 上，可以用 kpep 私有 API 来获取。我开源的代码中对这些 API 进行了封装，可以实现跨平台的性能计数器读取。

### 分支地址 B 的贡献

接下来，需要推测 $\mathrm{footprint}$ 是如何计算的，也就是说，分支地址和目的地址是以如何形式参与到 $\mathrm{PHR}$ 的更新公式上的。约定分支地址记为 $B$（Branch 的首字母），目的地址记为 $T$（Target 的首字母），用 $B[i]$ 表示分支地址从低到高第 $i$ 位（下标从 0 开始）的值，$T[i]$ 同理。假设 $\mathrm{footprint}$ 的每一位都是由若干个 $B[i]$ 和 $T[i]$ 通过异或计算而来。

!!! question "分支指令本身占用了多个字节，那么分支地址指的是哪一个字节的地址呢？"

    经过测试，AMD64 架构下，分支地址用的是分支指令最后一个字节的地址，而 ARM64 架构下，分支指令用的是分支指令第一个字节的地址。这大概是因为 AMD64 架构下分支指令是变长的，并且可以跨越页的边界；ARM64 则是定长的，并且不会跨越页的边界。

设计如下的程序，来推测某个 $B[i]$ 是如何参与到 $\mathrm{footprint}$ 的计算当中的：

1. 根据上面的分析，Apple M1 Firestorm 最多可以记录最近 100 条分支的历史信息，为了让 $\mathrm{PHR}$ 进入一个稳定的初始值，执行 100 个无条件分支
2. 设计两条分支指令，第一条是条件分支，按 50% 的概率跳或不跳；第二条是无条件分支；这两条分支的分支地址只在 $B[i]$ 上不同，其余的位都相同，目的地址相同
3. 执行若干条无条件分支，目的是把 $B[i]$ 对 $\mathrm{PHR}$ 的贡献往前移
4. 执行一条条件分支指令，其跳转方向与第二步中条件分支的方向一致

约等于下面的代码：

```c
// step 1.
// 100 jumps forward
goto jump_0;
jump_0: goto jump_1;
// ...
jump_98: goto jump_99;
jump_99:

// step 2.
int d = rand();
// the follow two branches differ in B[i]
// first conditional branch, 50% taken or not taken
if (d % 2 == 0) goto target;
// second unconditional branch
else goto target;
target:

// step 3.
// variable number of jumps forward
goto varjump_0;
varjump_0: goto varjump_1;
// ...
varjump_k: goto last;

// step 4.
// conditional branch
last:
if (d % 2 == 0) goto end;
end:
```

第二步中条件分支跳转与否，会影响分支历史中 $B[i]$ 一个位的变化，它会经过哈希函数，影响到 $\mathrm{footprint}$ 当中，进而异或到 $\mathrm{PHR}$ 当中。通过调整第三步执行的无条件分支个数，可以把 $B[i]$ 对 $\mathrm{PHR}$ 的影响左移到不同的位置。如果 $B[i]$ 对 $\mathrm{PHR}$ 造成了影响，那就可以正确预测最后一条条件分支指令的方向。当左移的次数足够多，就会使得 $B[i]$ 对 $\mathrm{PHR}$ 的贡献为零，那么对最后一条条件分支指令的方向预测只有 50% 的正确率。在 Apple M1 Firestorm 上[测试](https://github.com/jiegec/cpu-micro-benchmarks/blob/master/src/phr_branch_bits_location_gen.cpp)，得到如下结果：

![](./cbp-reverse-engineer-phrb.png)

横坐标 `Dummy branches` 指的是上面第三步插入的无条件分支的个数，纵坐标 `Branch toggle bit` 代表修改的是具体哪一个 $B[i]$，颜色对应分支预测的错误率，浅色部分对应最后一条分支只能正确预测 50%，深色部分对应最后一条分支总是可以正确预测。

从这个图可以得到什么信息呢？首先观察 $B[2]$ 对应的这一行，可以看到它确实参与到了 $\mathrm{PHR}$ 的计算当中，但是，仅仅经过 28 次移位，这个贡献就被移出了 $\mathrm{PHR}$，为了保留在 $\mathrm{PHR}$ 内，最多移动 27 次。类似地，在移出 $\mathrm{PHR}$ 之前，$B[3]$ 最多移动 26 次，$B[4]$ 最多移动 25 次，$B[5]$ 最多移动 24 次。

但实际上，这些 $B$ 是同时进入 $\mathrm{PHR}$ 的：这暗示了，它们对应了 $\mathrm{footprint}$ 的不同位置。如果某个 $B[i]$ 出现在 $\mathrm{footprint}$ 更高位的地方，它也会进入 $\mathrm{PHR}$ 更高位的地址，经过更少的移位次数就会被移出 $\mathrm{PHR}$；反之，如果 $B[i]$ 出现中 $\mathrm{footprint}$ 更低位的地方，它能够在 $\mathrm{PHR}$ 中停留更长的时间。

根据上面的实验，可见 $B[5], B[4], B[3], B[2]$ 参与到了 $\mathrm{footprint}$ 计算当中，而 $B$ 其他的位则没有。但比较奇怪的是，$\mathrm{PHR}$ 理应可以记录最近 100 条分支的信息，但实际上只观察到了 28。所以一定另外有别的信息。

### 目的地址 T 的贡献

刚刚测试了 $B$，接下来测试 $T$ 各位对 $\mathrm{PHR}$ 的贡献，方法类似：

1. 为了让 $\mathrm{PHR}$ 进入一个稳定的初始值，执行 100 个无条件分支
2. 设计一个间接分支，根据随机数，随机跳转到两个不同的目的地址，这两个目的地址只在 $T[i]$ 上不同，其余的位都相同，分支地址相同
3. 执行若干条无条件分支，目的是把 $T[i]$ 对 $\mathrm{PHR}$ 的贡献往前移
4. 执行一条条件分支指令，其跳转方向取决于第二步中间接分支所使用的随机数

约等于下面的代码：

```c
// step 1.
// 100 jumps forward
goto jump_0;
jump_0: goto jump_1;
// ...
jump_98: goto jump_99;
jump_99:

// step 2.
int d = rand();
// indirect branch
// the follow two targets differ in T[i]
auto targets[2] = {target0, target1};
goto targets[d % 2];
target0:
// add many nops
target1:

// step 3.
// variable number of jumps forward
goto varjump_0;
varjump_0: goto varjump_1;
// ...
varjump_k: goto last;

// step 4.
// conditional branch
last:
if (d % 2 == 0) goto end;
end:
```

在 Apple M1 Firestorm 上[测试](https://github.com/jiegec/cpu-micro-benchmarks/blob/master/src/phr_target_bits_location_gen.cpp)，得到如下结果：

![](./cbp-reverse-engineer-phrt.png)

!!! question "为了测试 T[31]，岂不是得插入很多个 NOP，一方面二进制很大，其次还要执行很长时间？"

    是的，所以这里在测试的时候，采用的是类似 JIT 的方法，通过 mmap `MAP_FIXED` 在内存中特定位置分配并写入代码，避免了用汇编器生成一个巨大的 ELF。同时，为了避免执行大量的 NOP，考虑到前面已经发现 $B[6]$ 或更高的位没有参与到 $\mathrm{PHR}$ 计算当中，所以可以添加额外的一组无条件分支来跳过大量的 NOP，它们的目的地址相同，分支地址低位相同，因此对 PHR 不会产生影响。

由此我们终于找到了分支历史最长记录 100 条分支是怎么来的：$T[2]$ 会经过 $\mathrm{footprint}$ 被异或到 $\mathrm{PHR}$ 的最低位，然后每次执行一个跳转的分支左移一次，直到移动 100 次才被移出 $\mathrm{PHR}$。类似地，$T[3]$ 只需要 99 次就能移出 $\mathrm{PHR}$，说明 $T[3]$ 被异或到了 $\mathrm{PHR}[1]$。依此类推，可以知道涉及到 $T$ 的 $\mathrm{footprint} = T[31:2]$，其中 $T[31:2]$ 代表一个 30 位的数，每一位从高到低分别对应 $T[31], T[30], \cdots, T[2]$。

那么，问题来了，前面测试 $B$ 的时候，移位次数那么少，明显少于 $T$ 的移位次数。这有两种可能：

1. 硬件上只有一个 $\mathrm{PHR}$ 寄存器，然后 $T[31:2]$ 被异或到 $\mathrm{PHR}$ 的低位，而 $B[5:2]$ 被异或到 $\mathrm{PHR}$ 的中间的位置
2. 硬件上有两个 $\mathrm{PHR}$ 寄存器，其中一个是 100 位，只记录 $T[31:2]$ 的历史，记为 $\mathrm{PHRT}$；另一个是 28 位，只记录 $B[5:2]$ 的历史，记为 $\mathrm{PHRB}$

随着后续的测试，基本确认硬件实现的是第二种。有意思的是，在我的论文发表后不久，在 Apple 公开的专利 [Managing table accesses for tagged geometric length (TAGE) load value prediction](https://patents.google.com/patent/US12159142B1/en) 当中，就出现了相关的表述，证明了逆向结果的正确性。

按照这个方法，我还逆向了 Apple、Qualcomm、ARM 和 Intel 的多代处理器的分支历史的记录方法，[并进行了公开](https://jia.je/cpu/cbp.html)。

## 引用文献

- [Dissecting Conditional Branch Predictors of Apple Firestorm and Qualcomm Oryon for Software Optimization and Architectural Analysis](https://arxiv.org/abs/2411.13900)
- [Half&Half: Demystifying Intel’s Directional Branch Predictors for Fast, Secure Partitioned Execution](https://cseweb.ucsd.edu/~tullsen/halfandhalf.pdf)
