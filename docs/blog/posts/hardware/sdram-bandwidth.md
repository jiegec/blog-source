---
layout: post
date: 2026-03-26
tags: [cpu,sdram,dram,ddr]
categories:
    - hardware
---

# SDRAM 在不同访存模式下的带宽分析与实验 

## 背景

最近在和 [@CircuitCoder](https://github.com/CircuitCoder) 交流 SDRAM（通常简写为 DRAM，或更进一步简写为 DDR）的各种性能指标，于是想到利用现有的 [DRAMSim3](https://github.com/umd-memsys/DRAMsim3) 和 [Ramulator2](https://github.com/CMU-SAFARI/ramulator2) 做一些模拟测试，看看各种访存模式下可以实现峰值带宽的多少比例，再结合时序验证理论与模拟结果是否吻合。实验相关代码已开源至 [jiegec/dram-bench](https://github.com/jiegec/dram-bench)。

<!-- more -->

## SDRAM 背景

首先简单回顾 SDRAM 的背景，我的知识库中有更详细的介绍，这里仅提炼几个便于理解后续内容的要点，完整的 SDRAM 介绍请移步[知识库](https://jia.je/kb/hardware/sdram.html)：

- SDRAM 由多级层次组成：
    - Channel：对应内存控制器的通道数量，通常每个 Channel 对应 64 位的数据总线
    - Rank：每个 Channel 内可能有多个 Rank，这些 Rank 共享总线
    - Bank Group：在 DDR4 引入，每个 Rank 有多个 Bank Group
    - Bank：每个 Bank Group 有多个 Bank
    - Row：每个 Bank 内部同时只有一个 Row 被激活
    - Column：激活的 Row 内，每个 Column 对应保存数据的 Cell
- 如何读写 SDRAM 中的数据：
    - 首先根据数据的地址找到对应的 Channel/Rank/Bank Group/Bank/Row/Column，如：
        - Row 地址等于地址的 `[33:18]` 位，共 65536 个 Row
        - Rank 地址等于地址的 `[17:17]` 位，共 2 个 Rank
        - Bank 地址等于地址的 `[16:15]` 位，每个 Bank Group 内有 4 个 Bank
        - Bank Group 地址等于地址的 `[14:13]` 位，共 4 个 Bank Group
        - Column 地址等于地址的 `[12:6]` 位，共 1024 个 Column，每 8 个 Column 为一个 Burst
    - 通过 Activate 命令激活对应的 Row，如已激活可跳过，如当前激活了其他 Row，则需要先执行 Precharge 命令
    - 读写 Row 中保存的数据
- SDRAM 中可能的性能瓶颈：
    - 在 Row 内连续访问数据很快，但如果要访问的数据位于不同 Row，就需要频繁执行 Activate 和 Precharge
    - SDRAM 有周期性的 Refresh，会导致部分时间无法访问数据
    - 额外的时序参数，对各类命令的顺序和间隔提出了约束：
        - tCCD：两次 Read 之间的最小间隔
        - tREFI：平均 Refresh 间隔
        - tRFC：Refresh 到下一个 Activate/Refresh 的最小间隔
        - tRTP：同一个 Bank 的 Read 到 Precharge 的最小间隔
        - tRP：同一个 Bank 的 Precharge 到下一个命令的最小间隔
        - tRCD：同一个 Bank 的 Activate 到 Read/Write 的最小间隔
        - tRAS：同一个 Bank 的 Activate 到 Precharge 的最小间隔
    - 如何计算峰值带宽：按接口速率（需考虑 DDR）乘以总线位宽可得峰值带宽，但由于上述瓶颈，实际无法达到该值

## 不同访存模式下的带宽分析与实验结果

### 顺序访存

首先考虑最经典的顺序访存，从地址 0 开始，以 64 字节为跨步访问。直觉上顺序访存似乎能实现最大带宽，但实际未必如此。例如以下测试结果中，DDR3 确实接近峰值，而 DDR4 则相差甚远：

- 模拟 DDR3-1866，带宽达到峰值的 95.6%
- 模拟 DDR4-3200，带宽达到峰值的 66.4%

#### DDR3

先分析 DDR3-1866 的模拟结果。实验中发出 50000 次 Read，其中 49772 次命中了已激活的 Row，无需额外 Activate 或 Precharge；此外还有 53 次 Refresh，228 次 Activate 和 222 次 Precharge。由于 DDR3-1866 的时序参数中，tCCD（两次 Read 之间的最小间隔）仅为 4 个周期，而一次 Burst 为 8 拍，因为 DDR 在时钟上下边沿都传输数据，所以一次 Read 正好占用数据总线 4 个周期，因此如果所有命令都是 Read，理论上可以完美衔接，不浪费任何带宽。既然实测只有 95% 左右，必定是其他命令引入了空泡：

- Activate/Precharge：在顺序访存模式下，当一个 Row 的数据全部被访问后，就要进入下一个 Row，此时需要一次 Precharge 和一次 Activate。一个 Row 内有 2048 个 Column，意味着需要执行 $2048/8=256$ 次 Read 才能遍历完一个 Row，因此 50000 次 Read 对应约 $50000/256=195.3$ 次 Activate/Precharge。此外，Refresh 之前不能有激活的 Row，所以还需要少量额外的 Activate/Precharge 来配合 Refresh。
- Refresh：DDR3 SDRAM 要求平均每 tREFI 时间进行一次 Refresh，这里 tREFI 等于 7800 个周期。考虑到有两个 Rank 需要分别 Refresh，因此在 209168 个周期内，需要进行约 $209168\times2/7800=53.6$ 次 Refresh，与实际基本吻合。

尝试理论计算：每 $x$ 次 Read，对应 $x/256$ 次因 Row 结束带来的 Activate/Precharge，每轮 Activate/Precharge 带来 $\mathrm{tRTP}+\mathrm{tRP}+\mathrm{tRCD}$ 的开销；此外在大约 $4x$ 个周期内，每个 Rank 还需进行 $4x/\mathrm{tREFI}$ 次 Refresh，每次 Refresh 带来约 $\mathrm{tRFC}$ 的开销。将这些开销汇总，代入时序参数计算得到约 $0.30x$ 的额外周期数。但实际上，Activate/Precharge 的部分开销可以通过 Bank 级交错来隐藏，比如在访问一个 Bank 的同时，提前对下一个 Bank 执行 Activate/Precharge，因此主要开销来自 Refresh。即使只考虑一个 Rank 内的 Refresh 开销，也有约 $0.17x$ 的额外周期数，此时带宽约为峰值的 $4x/(4x+0.17x)=0.959$ 倍，与实际测得的 95.6% 高度吻合。

#### DDR4

但 DDR4 的带宽比例显著下降，显然出现了新瓶颈。DDR4 相比 DDR3 一个重大改动是，原本一个 Rank 内只有 Bank，现在一个 Rank 包含多个 Bank Group，每个 Bank Group 内又有多个 Bank。这种分层是因为 Bank Group 内部的 tCCD 无法像 DDR3 那样保持在 4 个周期，只能退化为 5-8 个周期，这个新时序参数称为 tCCD_L（L 代表 Long）；而 Bank Group 之间的 tCCD 仍能保持在 4 个周期。这意味着在 DDR4 下，只有交替对不同 Bank Group 发送 Read 命令，才能逼近峰值带宽；一旦局限在某个 Bank Group 内部，每次 Read 需间隔 tCCD_L 个周期，而每次 Read 仅提供 4 个周期的数据，导致巨大的带宽浪费。特别是在 DDR4-3200 速率下，tCCD_L 长达 8 个周期，数据总线有一半时间处于空闲。

为验证这一点，额外做了一个测试：不再单纯顺序访存，而是固定一个 Bank Group，交错读取不同 Bank，每个 Bank 内顺序访问 Row 和 Column，最终测得的带宽仅为峰值的 47.5%，这大致是考虑 Refresh 后数据带宽减半的结果。按前述 DDR3 的分析方法，计算此时 Refresh 的开销：每 $x$ 次 Read，对应 $8x\times\mathrm{tRFC}/\mathrm{tREFI}$ 的周期开销，代入时序参数约为 $0.36x$，性能可达峰值的 $4x/(8x+0.36x)=0.478$ 倍，与实际测试的 47.5% 高度吻合。

再回到顺序访存，为何能实现 66.4% 的峰值带宽？注意刚才假设访存总是映射到同一个 Bank Group，而 66.4% 突破了 47.5% 的极限，意味着必然访问了多个 Bank Group。此时需要深入分析地址映射方式，它采用的 RoChRaBaBgCo 映射方法，意味着从地址高位到低位依次是 Row、Channel、Rank、Bank、Bank Group 和 Column。因此随着地址每次增加 64，当 Column 溢出时就会访问下一个 Bank Group，两个 Bank Group 的 Read 命令可以交错执行，填补流水线空档。如果改变映射顺序，会得到不同结果：

- 将 Bank Group（Bg）从地址低位挪到高位：
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

可见，Bank Group 地址越向高位移动，带宽越低，说明 Bank Group 交错的频率降低，性能随之下降；除了 Bank Group，Rank 之间也可以交错来掩盖部分延迟，但效果不如 Bank Group 交错显著；若两者都置于最高位，则退化为前述 47.5% 的带宽，即数据总线一半时间为空泡，再加上 Refresh 开销。

再回头看 DDR3 的分析：若只考虑 Refresh 带来的性能损耗，理论上限为 95.9% 带宽，实际达到 95.6%；若将 Activate/Precharge 的损耗也计入，理论上限仅为 $4x/(4x+0.30x)=0.930$ 倍峰值，低于 95.6%，这说明在顺序访存模式下，通过地址映射在 Bank 或 Rank 层面实现了交错，从而隐藏了一部分延迟。为此再进行一组实验：仅访问一个 Bank 内的连续 Row 和 Column，测得带宽为峰值的 92.7%，与分析基本吻合。

#### 小结

即使是简单的顺序访存，由于地址映射的存在，地址的连续变化会映射到不同的 SDRAM 层次，从而产生不同的性能表现。例如，在 DDR3 上，通过 Bank 和 Rank 的交错，可以隐藏一部分 Activate/Precharge 开销，仅剩 Refresh 开销无法避免；在 DDR4 上，根据地址映射的不同，若能在 Bank Group 层面实现细粒度的交错，就能充分利用更短的 tCCD_S 填满数据总线；否则会产生大量空泡，最坏情况下带宽降至 $4/\mathrm{tCCD_L}$ 的比例。

### 随机访存

与顺序访存相对的另一个极端是随机访存：访问地址随机分布在各种 Bank 和 Row 上，此时 Row 命中率很低，几乎每次 Read 之前都需要 Precharge 和 Activate。在这种场景下，只能依靠 Bank 等层次上的交错来尽量掩盖开销。

#### DDR3

从 DDR3-1866 实验数据可以明显看出随机访存与顺序访存的差异：同样是 50000 次 Read，顺序访存仅有 228 次 Activate 和 222 次 Precharge，而随机访存则达到了 50086 次 Activate 和 50078 次 Precharge。接下来尝试理论分析该场景下的性能。首先，在每个 Bank 内，循环执行 Activate-Read-Precharge，这一组操作至少耗时 $\mathrm{tRAS}+\mathrm{tRP}$；其次，若共有 8 个 Bank（为简化，固定只用一个 Rank），则这 8 个 Bank 可以交错执行 Activate-Read-Precharge 循环，理想情况下在 $\mathrm{tRAS}+\mathrm{tRP}$ 时间内，8 个 Bank 各可完成一次 Read。代入时序参数，推测带宽为峰值的 $4\times8/45=0.71$ 倍，但实际仅测到 46.0%，说明还存在其他瓶颈。事实上，这里需要考虑另一个时序参数 tFAW，其含义是在连续的 tFAW 时间内，最多只能有 4 次 Activate，且该限制跨 Bank 生效。因此即使有 8 个 Bank，实际也只能达到 $4\times4/\mathrm{tFAW}=0.485$ 倍的峰值性能，与模拟值已较为接近，还需考虑 Refresh 开销。在另一组 DDR3-1866 时序参数下，tFAW 为 26 个周期，理论值为 $4\times4/26=0.615$ 倍峰值，模拟结果为 57.7%，同样比较接近。

#### DDR4

DDR4-3200 的情况类似。当 tFAW 为 34 个周期时，理论值为 $4\times4/34=0.471$ 倍峰值，模拟结果为 44.5%。尽管 DDR4-3200 有 4 个 Bank Group，每个 Bank Group 内含 4 个 Bank，总共 16 个 Bank，但在频繁 Activate 的场景下，依然受限于 tFAW。

#### 小结

因此，即使是随机访存，只要能将请求分散到不同 Bank 上，性能依然可以接受。当然，随机访存的困境还体现在其他方面：缓存命中率低，且每个缓存行可能只用到少量数据就被丢弃。

### 对同一个 Bank 的随机访存

前面分析提到，Bank 交错可以在一定程度上掩盖 Activate-Precharge 的开销，但如果连这种掩盖也失效了，会发生什么？下面进行一组模拟，固定在某 Bank Group 内的一个 Bank 中，对其内部随机 Row 进行访问。

#### DDR3

仍以 DDR3-1866 时序参数为例进行理论分析：每 $\mathrm{tRAS}+\mathrm{tRP}$ 时间只能完成一次 Read 操作，因此带宽仅为峰值的 $4/(\mathrm{tRAS}+\mathrm{tRP})$ 倍。代入实际时序参数得 $4/(32+13)=0.089$ 倍，模拟结果为 8.5%，与理论分析吻合。

#### DDR4

DDR4-3200 同样如此，代入时序参数得 $4/(52+22)=0.054$ 倍，实际模拟结果为 5.2%，基本吻合。

#### 小结

因此，如果对同一个 Bank 进行频繁的随机访存，性能会急剧下降。不过由于地址映射的存在，Row 通常位于地址高位，在实际应用中，绕过 Bank 和 Bank Group 对应的地址位，直接在 Row 地址位上随机访问的概率相对较低，但一旦发生，对性能的影响将是毁灭性的。

## 总结

简单总结上述分析，根据访存模式的不同：

- 顺序访存：DDR3 基本可以打满带宽，DDR4 则取决于地址映射能否在 Bank Group 层面实现细粒度的交错
- 随机访存：借助 Bank 交错，随机访存也能达到约一半的峰值带宽，主要受 tFAW 限制
- 对同一个 Bank 的随机访存：无法隐藏 Activate-Read-Precharge 延迟，性能最低，受限于 tRAS+tRP

如果读者感兴趣，也可以在代码基础上添加其他访存模式，进一步探索性能表现。