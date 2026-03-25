---
layout: post
date: 2026-03-26
tags: [cpu,sdram,dram,ddr]
categories:
    - hardware
---

# SDRAM 在不同访存模式下能达到的带宽分析与实验

## 背景

最近在和 [@CircuitCoder](https://github.com/CircuitCoder) 交流 SDRAM（通常简写为 DRAM，或更进一步简写为 DDR）的各种性能指标，于是想到利用现有的 [DRAMSim3](https://github.com/umd-memsys/DRAMsim3) 和 [Ramulator2](https://github.com/CMU-SAFARI/ramulator2) 做一些模拟测试，看看各种访存模式下，可以实现达到峰值带宽的多少比例，再结合时序来看看理论和模拟结果是否吻合。实验相关代码已经开源到 [jiegec/dram-bench](https://github.com/jiegec/dram-bench)。

<!-- more -->

## SDRAM 背景

首先要简单过一下 SDRAM 的背景，我的知识库中有比较详细的介绍，这里大概介绍几个方便理解后续内容的要点，具体的 SDRAM 介绍请移步[知识库](https://jia.je/kb/hardware/sdram.html)：

- SDRAM 由多级层次组成：
    - Channel：对应内存控制器的通道数量，通常每个 Channel 对应 64 位的数据总线
    - Rank：每个 Channel 内可能有多个 Rank，这些 Rank 共享总线
    - Bank Group：在 DDR4 引入，每个 Rank 有多个 Bank Group
    - Bank：每个 Bank Group 有多个 Bank
    - Row：每个 Bank 内部，同时只有一个 Row 被激活
    - Column：激活的 Row 内，每个 Column 对应保存数据的 Cell
- 如何读写 SDRAM 中的数据：
    - 首先根据数据的地址找到对应的 Channel/Rank/Bank Group/Bank/Row/Column，如：
        - Row 地址等于地址的 `[33:18]` 位，共 65536 个 Row
        - Rank 地址等于地址的 `[17:17]` 位，共 2 个 Rank
        - Bank 地址等于地址的 `[16:15]` 位，每个 Bank Group 内有 4 个 Bank
        - Bank Group 地址等于地址的 `[14:13]` 位，共 4 个 Bank Group
        - Column 地址等于地址的 `[12:6]` 位，共 1024 个 Column，每 8 个 Column 为一个 Burst
    - 通过 Activate 命令激活对应的 Row，如已激活可以跳过，如目前激活了其他的 Row，需要首先执行 Precharge 命令
    - 读写 Row 中保存的数据
- SDRAM 中可能的性能瓶颈：
    - 在 Row 中连续访问数据是很快的，但如果要访问的数据在不同的 Row，就需要频繁的 Activate 和 Precharge
    - SDRAM 有频繁的 Refresh，会导致一些时间无法访问数据
    - 额外的时序参数，对各种命令的顺序和间隔提出了额外的要求：
        - tCCD：两次 Read 之间的最小间隔
        - tREFI：平均 Refresh 间隔
        - tRFC：Refresh 到下一个 Activate/Refresh 的最小间隔
        - tRTP：同一个 Bank 的 Read 到 Precharge 的最小间隔
        - tRP：同一个 Bank 的 Precharge 到下一个命令的最小间隔
        - tRCD：同一个 Bank 的 Activate 到 Read/Write 的最小间隔
        - tRAS：同一个 Bank 的 Activate 到 Precharge 的最小间隔
    - 如何计算峰值带宽：按照接口速率，乘以总线位宽，可以得到峰值带宽，但它因为各种性能瓶颈并无法达到

## 不同访存模式下的带宽分析与实验结果

### 顺序访存

首先考虑最经典的顺序访存，从地址 0 开始，以 64 字节位跨步开始访问。按照直觉，似乎顺序访存应当能实现最大的带宽，但实际上并不一定如此，例如下面是一些测试结果，可见 DDR3 确实是距离峰值很接近，然而 DDR4 相差甚远：

- 模拟 DDR3-1866，带宽达到峰值的 95.6%
- 模拟 DDR4-3200，带宽达到峰值的 66.4%

#### DDR3

首先来分析 DDR3-1866 的模拟，在实验过程中，发出 50000 次 Read，其中 49772 次都命中了已经激活的 Row，此时不需要额外的 Activate 或 Precharge；此外还有 53 次 Refresh，228 次 Activate 和 222 次 Precharge。由于 DDR3-1866 的时序参数中，tCCD 也就是两次 Read 之间的最小间隔只有 4 个周期，而正好一次 Burst 是 8 拍，由于是 DDR 在时钟上下边沿都传输数据，所以正好一次 Read 会占用数据总线的 4 个周期，因此理论上如果所有命令都是 Read，可以完美地连接起来，不会浪费任何带宽。既然只有 95% 左右，那一定是因为其他命令导致了空泡：

- Activate/Precharge：顺序访存的模式下，当一个 Row 的数据全部被访问一遍后，就要进入下一个 Row，此时就需要一次 Prechange 和一次 Activate；一个 Row 内有 2048 个 Column，意味着需要执行 $2048/8=256$ 次 Read 才能遍历完一个 Row，所以 50000 次 Read 对应大约 $50000/256=195.3$ 次 Activate/Precharge；此外，由于在 Refresh 之前，必须没有激活的 Row，所以需要一些额外的 Activate/Precharge 以配合 Refresh
- Refresh：DDR3 SDRAM 要求平均每 tREFI 时间就进行一次 Refresh，这里 tREFI 等于 7800 个周期，考虑到有两个 Rank 需要分别 Refresh，因此在 209168 个周期内，需要进行大约 $209168\times2/7800=53.6$ 次 Refresh，和实际基本吻合

尝试理论计算的话，那就是每 $x$ 次 Read，对应 $x/256$ 次由于 Row 结束带来的 Activate/Precharge，每轮 Activate/Precharge 带来 $\mathrm{tRTP}+\mathrm{tRP}+\mathrm{tRCD}$ 的开销；此外在大约 $4x$ 个周期内，每个 Rank 还需要进行 $4x/\mathrm{tREFI}$ 次 Refresh，每次 Refresh 会带来大约 $\mathrm{tRFC}$ 的开销。这些开销合起来，代入各时序参数计算出来的结果是大约 $0.30x$ 的额外周期数，但实际上，Activate/Precharge 的部分开销可以通过分 Bank 来隐藏，比如在访问一个 Bank 的同时，提前对下一个 Bank 进行 Activate/Precharge，因此主要的开销其实是 Refresh，即使只需要考虑一个 Rank 内的 Refresh 开销，也有大约 $0.17x$ 的额外周期数，此时带宽大概就是峰值的 $4x/(4x+0.17x)=0.959$ 倍，与实际测出来的 95.6% 高度吻合。

#### DDR4

但是，DDR4 的带宽比例显著下降，显然出现了新的瓶颈。DDR4 相比 DDR3 有一个巨大的改动，就是从原来的一个 Rank 内只有 Bank，变成了一个 Rank 有多个 Bank Group，每个 Bank Group 有多个 Bank 的分层。这样做，是因为 Bank Group 内部的 tCCD 无法做到像 DDR3 那样，保持在 4 个周期，而只能退化到 5-8 个周期，这个新的时序参数就叫 tCCD_L（L 代表 Long）；而 Bank Group 之间的 tCCD 还能保持在 4 个周期。这意味着，在 DDR4 下，只有来回对不同的 Bank Group 发送 Read 命令，才有可能逼近峰值带宽；一旦局限到某个 Bank Group 内部，就会出现每 tCCD_L 各周期才能进行一次 Read，而每次 Read 只能给 4 周期的数据，这就导致了巨大的带宽浪费。尤其是在 DDR4-3200 的速率下，tCCD_L 足足有 8 个周期，此时数据总线有一半的时间都在空闲。

为了证明这一点，额外做了一个测试，这次不再是单纯的顺序访存，而是固定 Bank Group 为零，然后在交错地读取不同的 Bank，每个 Bank 内顺序访问 Row 和 Column，最后测试出来的带宽只有峰值带宽的 47.5%，这大约就是考虑了 Refresh 以后，数据带宽砍半后的结果。按上述 DDR3 的分析方法，计算 DDR4 在这种情况下 Refresh 的开销：每 $x$ 次 Read，对应 $8x\times\mathrm{tRFC}/\mathrm{tREFI}$ 的周期数开销，代入时序参数，大概是 $0.36x$，性能可以达到峰值的 $4x/(8x+0.36x)=0.478$ 倍，和实际测试的 47.5% 高度吻合。

那么再回到顺序访存，为什么可以实现 66.4% 的峰值带宽呢？注意到刚才假设了访存总是被映射到同一个 Bank Group，这里突破了 47.5% 的极限，意味着肯定是访问了多于一个 Bank Group。此时，就要深入分析地址是如何映射的，它采用的 RoChRaBaBgCo 映射方法，意味着从地址高位到低位，分别是 Row、Channel、Rank、Bank、Bank Group 和 Column。这意味着随着地址每次增加 64，直到 Column 溢出时，就会访问下一个 Bank Group，此时两个 Bank Group 的 Read 命令就可以交错进行，填补流水线的空缺。考虑到这一点，如果更换这些映射的顺序，会得到什么结果呢：

- 把 Bank Group（Bg）从地址低位挪到地址高位：
    - RoChRaBaCoBg：95.2%
    - RoChRaBaBgCo：66.4%
    - RoChRaBgBaCo：51.0%
    - RoChBgRaBaCo：49.4%
    - RoBgChRaBaCo：49.4%
    - BgRoChRaBaCo：49.4%
- 进一步调整 Rank（Ra）的位置：
    - BgRoChBaCoRa：76.6%
    - BgRoChBaRaCo：57.5%
    - BgRoChRaBaCo：49.4%
    - BgRaRoChBaCo：47.5%

可见随着 Bank Group 地址逐渐向高位移动，带宽也逐渐下降，说明通过 Bank Group 交错的频率越来越少，导致性能越来越差；除了 Bank Group，实际上 Rank 之间也可以交错，掩盖一些延迟，但效果显然是不如 Bank Group 交错好；如果两者的都挪到地址最高位，此时直接回退到前面分析的 47.5% 的带宽，即数据总线有一半时间都是空泡，还有 Refresh 带来的开销。

再回过头来，看看刚才 DDR3 的分析：如果只考虑 Refresh 带来的性能损耗，理论上限是 95.9% 带宽，实际能达到 95.6%；但如果把 Activate/Precharge 的损耗也计算进来，理论上限就只有 $4x/(4x+0.30x)=0.930$ 倍的峰值带宽，低于 95.6%，意味着顺序访存模式下，通过地址映射，在 Bank 或 Rank 上实现了交错，从而隐藏了一部分延迟。此时再进行一组实验，即只访问一个 Bank 内的连续 Row 和 Column，测得带宽是峰值的 92.7%，与分析基本吻合。

#### 小结

即使是简单的顺序访存，由于地址映射的存在，地址的连续变化会对应到不同 SDRAM 层次上的变化，而这些变化会导致不同的性能。例如，在 DDR3 上，通过 Bank 和 Rank 交错，隐藏了一部分的 Activate/Precharge 隐藏，只有 Refresh 带来的开销无法避免；在 DDR4 上，根据地址映射的不同，如果在 Bank Group 上可以比较细粒度地交错，就可以很好地利用更短的 tCCD_S 填满数据总线；否则，就会产生大量的空泡，最坏情况下，带宽降低到 $4/(4+\mathrm{tCCD_L})$ 比例。

### 随机访存

与顺序访存对应的另一个极端，就是随机访存：访问的地址随机分布在各种 Bank 和 Row 上，此时 Row 命中率很低，几乎每次 Read 之前都要 Precharge 和 Activate。在这种场景下，就只能依靠 Bank 等层次上的交错来尽量掩盖。

#### DDR3

从 DDR3-1866 实验数据来看，能看出随机访存和顺序访存的区别：同样是 50000 次 Read，顺序访存只有 228 次 Activate，222 次 Precharge，而随机访存就有 50086 次 Activate 和 50078 次 Precharge。接下来尝试通过理论来分析这种场景下面的性能。首先，考虑每一个 Bank 内，在循环执行 Activate-Read-Precharge，这一组耗费的时间至少是 $\mathrm{tRAS}+\mathrm{tRP}$；接着，考虑一共有 8 个 Bank（为了简化，固定只用一个 Rank），那么 8 个 Bank 可以交错地进行 Activate-Read-Precharge 循环，理想情况下，在 $\mathrm{tRAS}+\mathrm{tRP}$ 的时间里，8 个 Bank 分别可以进行一次 Read。如果是这样的话，代入时序参数，推测的带宽是峰值的 $4\times8/45=0.71$ 倍，但实际测下来，只有峰值的 46.0%，说明还有其他的瓶颈。事实上，这里需要考虑的是另一个时序参数 tFAW，它的意思是，连续的 tFAW 时间内，只能最多有 4 次 Activate，这个限制是跨 Bank 的。因此，即使有 8 个 Bank，实际上也只能达到 $4\times4/\mathrm{tFAW}=0.485$ 倍的峰值性能，这和模拟值已经比较接近了，因为还需要考虑 Refresh 带来的开销。在另一组 DDR3-1866 时序参数下，tFAW 是 26 个周期，理论是 $4\times4/26=0.615$ 倍峰值，模拟出来的是 57.7%，也比较接近。

#### DDR4

情况在 DDR4-3200 上也是类似的，当 tFAW 等于 34 个周期时，理论是 $4\times4/34=0.471$ 倍峰值，模拟出来是 44.5%。即使 DDR4-3200 对应 4 个 Bank Group，每个 Bank Group 内有 4 个 Bank，也就是一共有 16 个 Bank，但在频繁 Activate 的场景下，依然会受到 tFAW 的限制。

#### 小结

因此，即使是随机访存，只要能够分摊到不同的 Bank 上，性能还是可以接受的。当然了，随机访存困境还在其他地方：缓存命中率低，且每个缓存行可能只有少量的数据被用到就被丢弃了。

### 对同一个 Bank 的随机访存

刚才的分析中提到，由于 Bank 的交错，随机访存带来的 Activate-Precharge 开销一定程度上可以被掩盖，那么如果连这个掩盖也失效了，会发生什么呢？下面进行一组模拟，固定在某个 Bank Group 的 Bank 当中，在它内部进行随机 Row 的访问。

#### DDR3

首先还是在 DDR3-1866 时序参数下实验，首先是理论分析，每 $\mathrm{tRAS}+\mathrm{tRP}$ 的时间只能进行一次 Read 操作，那么带宽就只有峰值的 $4/(\mathrm{tRAS}+\mathrm{tRP})$ 倍。代入实际时序参数，就是 $4/(32+13)=0.089$ 倍，低得可怜，而模拟出来也只有 8.5%，与理论分析吻合。

#### DDR4

DDR4-3200 也是一样的，代入时序参数，理论是 $4/(52+22)=0.054$ 倍，实际模拟出来是 5.2%，基本吻合。

#### 小结

因此，如果是对同一个 Bank 进行频繁的随机访存，性能会急剧下降，不过由于地址映射的存在，Row 通常会在地址的高位，在实际应用中，绕过 Bank 和 Bank Group 对应的地址位数，直接在 Row 的地址位数上随机，这个概率还是比较低的，只是一旦遇到，对性能的影响就是毁灭性的。

## 总结

简单总结一下上面的分析，根据访存模式的不同：

- 顺序访存：DDR3 基本可以打满带宽，DDR4 则取决于地址映射，能否在 Bank Group 上实现细粒度的交错
- 随机访存：由于 Bank 交错，随机访存也能实现大约一半的峰值带宽，主要受到 tFAW 的限制
- 对同一个 Bank 的随机访存：不再能隐藏 Activate-Read-Precharge 延迟，性能最低，受 tRAS+tRP 的限制

如果读者感兴趣，也可以在代码的基础上，添加其他访存模式，看看跑出来的性能会如何。
