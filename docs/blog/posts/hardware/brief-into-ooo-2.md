---
layout: post
date: 2022-03-31
tags: [ooo,cpu,lsu,cache,dram,brief-into-ooo]
categories:
    - hardware
---

# 浅谈乱序执行 CPU（二：访存）

本文的内容已经整合到[知识库](/kb/hardware/ooo_cpu.html)中。

## 背景

之前写过一个[浅谈乱序执行 CPU](brief-into-ooo.md)，随着学习的深入，内容越来越多，页面太长，因此把后面的一部分内容独立出来，变成了这篇博客文章。

本文主要讨论访存的部分。

本系列的所有文章：

- [浅谈乱序执行 CPU（一：乱序）](./brief-into-ooo.md)
- [浅谈乱序执行 CPU（二：访存）](./brief-into-ooo-2.md)
- [浅谈乱序执行 CPU（三：前端）](./brief-into-ooo-3.md)

<!-- more -->

## 内存访问

内存访问是一个比较复杂的操作，它涉及到缓存、页表、内存序等问题。在乱序执行中，要尽量优化内存访问对其他指令的延迟的影响，同时也要保证正确性。这里参考的是 [BOOM 的 LSU 设计](https://docs.boom-core.org/en/latest/sections/load-store-unit.html)。

首先是正确性。一般来说可以认为，Load 是没有副作用的（实际上，Load 会导致 Cache 加载数据，这也引发了以 Meltdown 为首的一系列漏洞），因此可以很激进地预测执行 Load。但是，Store 是有副作用的，写出去的数据就没法还原了。因此，Store 指令只有在 ROB Head 被 Commit 的时候，才会写入到 Cache 中。

其次是性能，我们希望 Load 指令可以尽快地完成，这样可以使得后续的计算指令可以尽快地开始进行。当 Load 指令的地址已经计算好的时候，就可以去取数据，这时候，首先要去 Store Queue 里面找，如果有 Store 指令要写入的地址等于 Load 的地址，说明后面的 Load 依赖于前面的 Store，如果 Store 的数据已经准备好了，就可以直接把数据转发过来，就不需要从 Cache 中获取，如果数据还没准备好，就需要等待这一条 Store 完成；如果没有找到匹配的 Store 指令，再从内存中取。不过，有一种情况就是，当 Store 指令的地址迟迟没有计算出来，而后面的 Load 已经提前从 Cache 中获取数据了，这时候就会出现错误，所以当 Store 计算出地址的时候，需要检查后面的 Load 指令是否出现地址重合，如果出现了，就要把这条 Load 以及依赖这条 Load 指令的其余指令重新执行。[POWER8 处理器微架构论文](http://ieeexplore.ieee.org/abstract/document/7029183/)中对此也有类似的表述：

	The POWER8 IFU also implements mechanisms to mitigate performance
	degradation associated with pipeline hazards. A Store-Hit-Load (SHL) is
	an out-of-order pipeline hazard condition, where an older store executes
	after a younger overlapping load, thus signaling that the load received
	stale data. The POWER8 IFU has logic to detect when this condition
	exists and provide control to avoid the hazard by flushing the load
	instruction which received stale data (and any following instructions).
	When a load is flushed due to detection of a SHL, the fetch address of
	the load is saved and the load is marked on subsequent fetches allowing
	the downstream logic to prevent the hazard. When a marked load
	instruction is observed, the downstream logic introduces an explicit
	register dependency for the load to ensure that it is issued after the
	store operation.

下面再详细讨论一下 LSU 的设计。

## Load Store Unit

LSU 是很重要的一个执行单元，负责 Load/Store/Atomic 等指令的实现。最简单的实现方法是按顺序执行，但由于 pipeline 会被清空，Store/Atomic/Uncached Load 这类有副作用（当然了，如果考虑 Meltdown 类攻击的话，Cached Load 也有副作用，这里就忽略了），需要等到 commit 的时候再执行。这样 LSU 很容易成为瓶颈，特别是在访存指令比较多的时候。

为了解决这个问题，很重要的是让读写也乱序起来，具体怎么乱序，受到实现的影响和 Memory Order/Program Order 的要求。从性能的角度上来看，我们肯定希望 Load 可以尽快执行，因为可能有很多指令在等待 Load 的结果。那么，需要提前执行 Load，但是怎么保证正确性呢？在 Load 更早的时候，可能还有若干个 Store 指令尚未执行，一个思路是等待所有的 Store 执行完毕，但是这样性能不好；另一个思路是用地址来搜索 Store 指令，看看是否出现对同一个地址的 Store 和 Load，如果有，直接转发数据，就不需要从 Cache 获取了，不过这种方法相当于做了一个全相连的 Buffer，面积大，延迟高，不好扩展等问题接踵而至。

为了解决 Store Queue 需要相连搜索的问题，[A high-bandwidth load-store unit for single-and multi-threaded processors](https://repository.upenn.edu/cgi/viewcontent.cgi?article=1001&context=cis_reports) 的解决思路是，把 Store 指令分为两类，一类是需要转发的，一类是不需要的，那么可以设计一个小的相连存储器，只保存这些需要转发的 Store 指令；同时还有一个比较大的，保存所有 Store 指令的队列，因为不需要相连搜索，所以可以做的比较大。

仔细想想，这里还有一个问题：Load 在执行前，更早的 Store 的地址可能还没有就绪，这时候去搜索 Store Queue 得到的结果可能是错的，这时候要么等待所有的 Store 地址都就绪，要么就先执行，再用一些机制来修复这个问题，显然后者 IPC 要更好。

修复 Load Store 指令相关性问题，一个方法是当一个 Store 提交的时候，检查是否有地址冲突的 Load 指令（那么 Load Queue 也要做成相连搜索的），是否转发了错误的 Store 数据，这也是 [Boom LSU](https://docs.boom-core.org/en/latest/sections/load-store-unit.html#memory-ordering-failures) 采用的方法。另一个办法是 Commit 的时候（或者按顺序）重新执行 Load 指令，如果 Load 结果和之前不同，要把后面依赖的刷新掉，这种方式的缺点是每条 Load 指令都要至少访问两次 Cache。[Store Vulnerability Window (SVW): Re-Execution Filtering for Enhanced Load Optimization](https://repository.upenn.edu/cgi/viewcontent.cgi?article=1228&context=cis_papers) 属于重新执行 Load 指令的方法，通过 Bloom filter 来减少一些没有必要重复执行的 Load。还有一种办法，就是预测 Load 指令和哪一条 Store 指令有依赖关系，然后直接去访问那一项，如果不匹配，就认为没有依赖。[Scalable Store-Load Forwarding via Store Queue Index Prediction](https://ieeexplore.ieee.org/document/1540957) 把 Load 指令分为三类，一类是不确定依赖哪条 Store 指令（Difficult Loads），一类是基本确定依赖哪一条 Store 指令，一类是不依赖 Store 指令。这个有点像 Cache 里面的 Way Prediction 机制。

分析完了上述一些优化方法，我们也来看一些 CPU 设计采用了哪种方案。首先来分析一下 [IBM POWER8](https://ieeexplore.ieee.org/abstract/document/7029183) 的 LSU，首先，可以看到它设计了比较多项目的 virtual STAG/LTAG，然后再转换成比较少项目的 physical STAG/LTAG，这样 LSQ 可以做的比较小，原文：

	A virtual STAG/LTAG scheme is used to minimize dispatch holds due to
	running out of physical SRQ/LRQ entries. When a physical entry in the
	LRQ is freed up, a virtual LTAG will be converted to a real LTAG. When a
	physical entry in the SRQ is freed up, a virtual STAG will be converted
	to a real STAG. Virtual STAG/LTAGs are not issued to the LSU until they
	are subsequently marked as being real in the UniQueue. The ISU can
	assign up to 128 virtual LTAGs and 128 virtual STAGs to each thread.

这个思路在 2007 年的论文 [Late-Binding: Enabling Unordered Load-Store Queues](https://people.csail.mit.edu/emer/papers/2007.06.isca.late_binding.pdf) 里也可以看到，也许 POWER8 参考了这篇论文的设计。可以看到，POWER8 没有采用那些免除 CAM 的方案：

	The SRQ is a 40-entry, real address based CAM structure. Similar to the
	SRQ, the LRQ is a 44-entry, real address based, CAM structure. The LRQ
	keeps track of out-of-order loads, watching for hazards. Hazards
	generally exist when a younger load instruction executes out-of-order
	before an older load or store instruction to the same address (in part
	or in whole). When such a hazard is detected, the LRQ initiates a flush
	of the younger load instruction and all its subsequent instructions from
	the thread, without impacting the instructions from other threads. The
	load is then re-fetched from the I-cache and re-executed, ensuring
	proper load/store ordering.

而是在传统的两个 CAM 设计的基础上，做了减少物理 LSQ 项目的优化。比较有意思的是，POWER7 和 POWER8 的 L1 Cache 都是 8 路组相连，并且采用了 set-prediction 的方式（应该是通常说的 way-prediction）。

此外还有一个实现上的小细节，就是在判断 Load 和 Store 指令是否有相关性的时候，由于地址位数比较多，完整比较的延迟比较大，可以牺牲精度的前提下，选取地址的一部分进行比较。[POWER9 论文](https://ieeexplore.ieee.org/document/8409955) 提到了这一点：

	POWER8 and prior designs matched the effective address (EA) bits 48:63
	between the younger load and the older store queue entry. In POWER9,
	through a combination of outright matches for EA bits 32:63 and hashed
	EA matches for bits 0:31, false positive avoidance is greatly improved.
	This reduces the number of flushes, which are compulsory for false
	positives.

这里又是一个精确度和时序上的一个 tradeoff。

具体到 Load/Store Queue 的大小，其实都不大：

1. [Zen 2](https://ieeexplore.ieee.org/document/9000513) Store Queue 48
2. [Intel Skylake](https://en.wikichip.org/wiki/intel/microarchitectures/skylake_(client)#Memory_subsystem) Store Buffer 56 Load Buffer 72
3. [POWER 8](https://ieeexplore.ieee.org/document/7029183?arnumber=7029183) Store Queue 40 Load Queue 44 (Virtual 128+128)
4. [Alpha 21264](http://ieeexplore.ieee.org/document/755465/) Store Queue 32 Load Queue 32

### Load Pipeline

下面来举例分析 LSU 中 Load Pipeline 每一拍需要做些什么。

以[香山雁栖湖](https://raw.githubusercontent.com/OpenXiangShan/XiangShan-doc/main/slides/20210625-RVWC-%E8%AE%BF%E5%AD%98%E6%B5%81%E6%B0%B4%E7%BA%BF%E7%9A%84%E8%AE%BE%E8%AE%A1%E4%B8%8E%E5%AE%9E%E7%8E%B0.pdf)微架构为例，它的 Load Pipeline 分为三级流水线：

1. 第一级：计算虚拟地址（基地址 + 立即数偏移），把虚拟地址送进 DTLB 和 L1 DCache（因为 VIPT，虚拟地址作为 index 访问 L1 DCache），从 DTLB 读取物理地址，从 L1 DCache Tag Array 读取各路的 Tag
2. 第二级：从 DTLB 得到了物理地址，根据物理地址计算出 Tag，和 L1 DCache 读出的 Tag 做比较，找到匹配的 Way，从 L1 DCache 的 Data Array 读取对应 Way 的数据；把物理地址送到 Store Queue，查找匹配的 Store
3. 第三级：根据从 L1 DCache 读取的数据和 Store to Load Forwarding 得到的数据，得到最终的读取结果，写回

以[香山南湖](https://raw.githubusercontent.com/OpenXiangShan/XiangShan-doc/main/slides/20220825-RVSC-%E5%8D%97%E6%B9%96%E6%9E%B6%E6%9E%84%E8%AE%BF%E5%AD%98%E5%AD%90%E7%B3%BB%E7%BB%9F%E7%9A%84%E8%AE%BE%E8%AE%A1%E4%B8%8E%E5%AE%9E%E7%8E%B0.pdf)微架构为例，它的 Load Pipeline 分为四级流水线：

1. 第一级：计算虚拟地址（基地址 + 立即数偏移），把虚拟地址送进 DTLB 和 L1 DCache（因为 VIPT，虚拟地址作为 index 访问 L1 DCache），从 DTLB 读取物理地址，从 L1 DCache Tag Array 读取各路的 Tag
2. 第二级：从 DTLB 得到了物理地址，根据物理地址计算出 Tag，和 L1 DCache 读出的 Tag 做比较，找到匹配的 Way，从 L1 DCache 的 Data Array 读取对应 Way 的数据；把物理地址送到 Store Queue，查找匹配的 Store
3. 第三级：由于 L1 DCache 容量较大，需要的延迟比较高，在这一级完成数据的读取和 Store to Load Forwarding
4. 第四级：根据从 L1 DCache 读取的数据和 Store to Load Forwarding 得到的数据，得到最终的读取结果，写回

可见香山南湖相比雁栖湖的主要区别就是留给 L1 DCache 读取的时间更长了，4 周期也是一个比较常见的 Load to use latency。

为了减少额外的 1 个周期对 pointer chasing 场景的性能影响，南湖架构针对 pointer chasing 做了优化：pointer chasing 场景下，读取的数据会成为后续 load 指令的地址。为了优化它，南湖架构在流水线的第四级上做了前传，直接传递到下一条 load 指令的由虚拟地址计算出的 index，这样的话可以做到 3 cycle 的 load to use latency。为了优化时序，前传的时候，假设基地址加上 imm 以后，不会影响 index，这样预测的时候就不用加上 imm，时序上会好一些，不过这也限制了优化可以生效的 imm 范围。

注：PPT 里绘制的是第三级前传，但是如果是这样的话，就是 2 cycle 的 load to use latency 了，和描述不符。

类似的优化在商用处理器上也可以看到，正常的 load to use latency 是 4 周期，load to load 则可以 3 周期。例如苹果的专利 [Reducing latency for pointer chasing loads](https://patents.google.com/patent/US9710268B2) 提到了它的 LSU 流水线设计以及前传的做法：

![](brief-into-ooo-2-apple-lsu.png)

和香山南湖类似，它的 Load Pipeline 也是四级流水线（对应图中 Stage 3-6），功能也类似。不过它的 3 周期 load to load 前传的实现方法则不同。

这个专利的前传是从第三级前传到读寄存器的阶段，这样也可以实现 3 周期的的 load to load latency。这样的好处是，AGU 阶段保留，这对于 AGU 阶段比较复杂的 ARM 架构是比较好的，因为 ARM 架构下 AGU 阶段可能涉及到加法和移位，而 RISCV 只有立即数加法。不过这样也要求 Load 不命中 Store Queue，而是从 L1 DCache 获得，因为 Store to Load Forwarding 的合并操作是在第四级流水线，为了能在第三级流水线前传，只能预测它不命中 Store Queue，数据完全从 L1 DCache 中取得。

图中把 AGU 和 DTLB Lookup 并着画可能有一些问题，应该是先由 AGU 计算出虚拟地址，再走 DTLB Lookup。

## Load Address Prediction

下面来分析一个来自苹果公司的专利：[Early load execution via constant address and stride prediction](https://patents.google.com/patent/US20210049015A1)，它实现的优化是，当一条 load 指令的地址是可预测的，例如它总是访问同一个地址（`constant address`），或者访问的地址按照固定的间隔（`constant stride`）变化，那就按照这个规律去预测这条 load 指令要访问的地址，而不用等到地址真的被计算出来，这样就可以提前执行这条 load 指令。

既然是一个预测算法，首先就要看它是怎么预测的。专利里提到了两个用于预测的表：

1. Load Prediction Table，给定 PC，预测 Load 指令要访问的地址
2. Load Prediction Learning Table，用于跟踪各个 PC 下的 Load 指令的访存模式以及预测正确率

一开始，两个表都是空的，随着 Load 指令的执行，首先更新的是 Load Prediction Learning Table，它会跟踪 Load 指令的执行历史，训练预测器，计算预测器的准确率。

当 Load Prediction Learning Table 发现能够以较高的准确率预测某条 Load 指令时，就会在 Load Prediction Table 中分配一个 entry，那么之后前端（IFU）再次遇到这条 Load 指令时，通过检查 Load Prediction Table，就可以预测要访问的地址。

当 Load Prediction Learning Table 发现某条 Load 指令的预测错误次数多了，就会把对应的表项从 Load Prediction Table 和 Load Prediction Learning Table 中删除，此时就会回退到正常的执行过程，Load 指令需要等待地址计算完成才可以执行。

为了避免浪费功耗，如果 Load 指令的地址很快就可以算出来，那么预测也就没有必要了，此时即使做了预测，也不会带来很高的性能提升。判断的依据是，计算从预测地址到计算出地址耗费的周期数，如果超过一个阈值，那么优化就有效果；如果没有超过阈值，那就不预测。

那么，如果 Load 的地址需要比较长的时间去计算，但实际上又是可以预测的，那就可以通过 Load Address Prediction 的方法，来提升性能。

## 缓存/内存仿真模型

最后列举一下科研里常用的一些缓存/内存仿真模型：

- DRAMSim2: [论文 DRAMSim2: A Cycle Accurate Memory System Simulator](https://user.eng.umd.edu/~blj/papers/cal10-1.pdf) [代码](https://github.com/umd-memsys/DRAMSim2)
- DRAMsim3: [论文 DRAMsim3: A Cycle-Accurate, Thermal-Capable DRAM Simulator](https://ieeexplore.ieee.org/document/8999595) [代码](https://github.com/umd-memsys/DRAMsim3)
- DRAMSys4.0：[论文 DRAMSys4.0: A Fast and Cycle-Accurate SystemC/TLM-Based DRAM Simulator](https://link.springer.com/chapter/10.1007/978-3-030-60939-9_8) [4.0 代码](https://github.com/tukl-msd/DRAMSys/releases/tag/v4.0) [5.0 代码](https://github.com/tukl-msd/DRAMSys/releases/tag/v5.0)
- CACTI: [论文 CACTI 2.0: An Integrated Cache Timing and Power Model](https://www.hpl.hp.com/research/cacti/cacti2.pdf) [代码](https://github.com/HewlettPackard/cacti)
- McPAT: [论文 McPAT: An integrated power, area, and timing modeling framework for multicore and manycore architectures](https://ieeexplore.ieee.org/document/5375438) [代码](https://github.com/HewlettPackard/mcpat)
- Ramulator: [论文 Ramulator: A Fast and Extensible DRAM Simulator](https://users.ece.cmu.edu/~omutlu/pub/ramulator_dram_simulator-ieee-cal15.pdf) [代码](https://github.com/CMU-SAFARI/ramulator)
