---
layout: post
date: 2021-09-14 13:47:00 +0800
tags: [ooo,cpu,tomasulo,outoforder,renaming,brief-into-ooo]
category: hardware
title: 浅谈乱序执行 CPU
---

## 背景

最早学习乱序执行 CPU 的时候，是在 Wikipedia 上自学的，后来在计算机系统结构课上又学了一遍，但发现学的和现在实际采用的乱序执行 CPU 又有很大区别，后来又仔细研究了一下，觉得理解更多了，就想总结一下。

## 经典 Tomasulo

参考 [Stanford 教材](https://people.eecs.berkeley.edu/~pattrsn/252F96/Lecture04.pdf)

经典 Tomasulo，也是 Wikipedia 上描述的 Tomasulo 算法，它的核心是保留站。指令在 Decode 之后，会被分配到一个保留站中。保留站有以下的这些属性：

1. Op：需要执行的操作
2. Qj，Qk：操作数依赖的指令目前所在的保留站 ID
3. Vj，Qk：操作数的值
4. Rj，Rk：操作数是否 ready（或者用特殊的 Qj，Qk 值表示是否 ready）
5. Busy：这个保留站被占用

此外还有一个 mapping（Wikipedia 上叫做 RegisterStat），记录了寄存器是否会被某个保留站中的指令写入。

指令分配到保留站的时候，会查询 RegisterStat，得知操作数寄存器是否 ready，如果不 ready，说明有一个先前的指令要写入这个寄存器，那就记录下对应的保留站 ID。当操作数都 ready 了，就可以进入计算单元计算。当一条指令在执行单元中完成的时候，未出现 WAW 时会把结果写入寄存器堆，并且通过 Common Data Bus 进行广播，目前在保留站中的指令如果发现，它所需要的操作数刚好计算出来了，就会把取值保存下来。

这里有一些细节：因为保留站中的指令可能要等待其他指令的完成，为了保证计算单元利用率更高，对于同一个计算类型（比如 ALU），需要有若干个同类的保留站（比如 Add1，Add2，Add3）。在 Wikipedia 的表述中，每个保留站对应了一个计算单元，这样性能比较好，但自然面积也就更大。如果节省面积，也可以减少计算单元的数量，然后每个计算单元从多个保留站中获取计算的指令。

可以思考一下，这种方法的瓶颈在什么地方。首先，每条指令都放在一个保留站中，当保留站满的时候就不能发射新的指令。其次，如果计算单元的吞吐跟不上保留站的填充速度，也会导致阻塞。

这种方法的一个比较麻烦的点在于难以实现精确异常。精确异常的关键在于，异常之前的指令都生效，异常和异常之后的指令不生效，但这种方法无法进行区分。

从寄存器重命名的角度来看，可以认为这种方法属于 Implicit Register Renaming，也就是说，把 Register 重命名为保留站的 ID。

再分析一下寄存器堆需要哪些读写口。有一条规律是，寄存器堆的面积与读写口个数的平方成正比。对于每条发射的指令，都需要从寄存器堆读操作数，所以读口是操作数 x 指令发射数。当执行单元完成计算的时候，需要写入寄存器堆，所以每个执行单元都对应一个寄存器堆的写口。

硬件实现的时候，为了性能，希望保留站可以做的比较多，这样可以容纳更多的指令。但是，保留站里面至少要保存操作数的值，会比较占用面积，并且时延也比较大。

## ROB（ReOrder Buffer）

[参考教材](https://web.stanford.edu/class/cs349g/cs349g-speculation.pdf)

为了实现精确异常，我们需要引入 ROB。在上面的 Tomasulo 算法中，计算单元计算完成的时候，就会把结果写入到寄存器堆中，因此精确异常时难以得到正确的寄存器堆取值。既然我们希望寄存器堆的状态与顺序执行的结果一致，我们需要引入 ROB。

ROB 实际上就是一个循环队列，队列头尾指针之间就是正在执行的指令，每个 ROB 表项记录了指令的状态、目的寄存器和目的寄存器将要写入的值。ROB 会检查队列头的指令，如果已经执行完成，并且没有异常，就可以让结果生效，并把指令从队列头中删去，继续检查后面的。Decode 出来的指令则会插入到 ROB 的尾部，并且随着指令的执行过程更新状态。遇到异常的指令，就把队列中的指令、保留站和执行单元清空，从异常处理地址开始重新执行。

为了保证寄存器堆的正确性，运算单元的运算结果会写入 ROB 项中，当这一项在 ROB 队列头部被删去时，就会写入寄存器堆。在经典 Tomasulo 中，寄存器重命名为保留站的 ID，但在这种设计中，应该重命名为 ROB 的 ID，也就是说，需要维护一个寄存器到 ROB ID 的映射，当指令进入保留站的时候，需要从寄存器堆或者 ROB 中去读取操作数的值。在 CDB 上广播的也是 ROB 的 ID，而不是保留站的 ID。

这种方法中，ROB 的大小成为了一个新的瓶颈，因为每条在正在执行的指令都需要在 ROB 中记录一份。不过好处是实现了精确异常。

## Explicit Register Renaming

上面两种设计都是采用的 Implicit Register Renaming 的方法，第一种方法重命名到了保留站，第二种方法重命名到了 ROB。还有一种设计，把寄存器编号映射到物理的寄存器。把 ISA 中的寄存器称为架构寄存器（比如 32 个通用寄存器），CPU 中实际的寄存器称为物理寄存器，物理寄存器一般会比架构寄存器多很多（一两百个甚至更多）。

Explicit Register Renaming 和 ReOrder Buffer 这两个设计方向可以同时使用，也可以单独使用。

映射的方法和前面的类似，也是维护一个 mapping，从架构寄存器到物理寄存器。当一条指令 Dispatch 的时候，操作数在 mapping 中找到实际的物理寄存器编号。如果这条指令要写入新的架构寄存器，则从未分配的物理寄存器中分配一个新的物理寄存器，并且更新 mapping，即把写入的架构寄存器映射到新的物理寄存器上。然后，放到 Issue Queue 中。

Issue Queue 可以理解为保留站的简化版，它不再保存操作数的取值，而仅仅维护操作数是否 ready。后面解释为什么不需要保存操作数的取值。在 Issue Queue 中的指令在所有操作数都 ready 的时候，则会 Issue 到不同的端口中。每个端口对应着一个执行单元，比如两个 ALU 端口分别对应两个 ALU 执行单元。指令首先通过寄存器堆，以物理寄存器为编号去读取数据，然后这个值直接传给执行单元，不会存下来。当执行单元执行完毕的时候，结果也是写到物理寄存器堆中，ROB 不保存数据。

可以发现，这种设计中，值仅保存在寄存器堆中，Issue Queue 和 ROB 都只保存一些状态位，因此它们可以做的很大，典型的 Issue Queue 有几十项，ROB 则有几百项。

接下来讨论一些细节。首先是，物理寄存器何时释放。当一条指令写入一个架构寄存器的时候，在下一次这个架构寄存器被写入之前，这个寄存器的值都有可能被读取，因此这个架构寄存器到物理寄存器的映射要保留。如果我们能保证读取这个值的指令都已经完成，我们就可以释放这个物理寄存器了。一个方法是，我在覆盖架构寄存器到物理寄存器的映射时，我还要记录原来的物理寄存器，当该指令在 ROB 中提交了（从队头出去了），说明之前可能依赖这个物理寄存器的所有指令都完成了，这时候就可以把原来的物理寄存器放到未映射的列表中。

还有一个问题，就是在遇到异常的时候，如何恢复在异常指令处的架构寄存器到物理寄存器的映射呢？一个办法是，利用我在 ROB 中记录的被覆盖的物理寄存器编号，从 ROB 队尾往前回滚，当发现一条指令覆盖了一个架构寄存器映射的时候，就恢复为覆盖之前的值。这样，当回滚到异常指令的时候，就会得到正确的映射。[MIPS R10K 的论文](https://ieeexplore.ieee.org/document/491460)中是这么描述的：

	The active list contains the logical-destination register number and its
	old physical-register number for each instruction. An instruction's
	graduation commits its new mapping, so the old physical register can
	return to the free list for reuse. When an exception occurs, however,
	subsequent instructions never graduate. Instead, the processor restores
	old mappings from the active list. The R1OOOO unmaps four instructions
	per cycle--in reverse order, in case it renamed the same logical
	register twice. Although this is slower than restoring a branch,
	exceptions are much rarer than mispredicted branches. The processor
	returns new physical registers to the free lists by restoring their read
	pointers.

和 @CircuitCoder 讨论并参考 [BOOM 文档](https://docs.boom-core.org/en/latest/sections/reorder-buffer.html#parameterization-rollback-versus-single-cycle-reset) 后发现，另一种办法是记录一个 Committed Map Table，也就是，只有当 ROB Head 的指令被 Commit 的时候，才更新 Committed Map Table，可以认为是顺序执行的寄存器映射表。当发生异常的时候，把 Committed Map Table 覆盖到 Register Map Table 上。这样需要的周期比较少，但是时序可能比较差。

## Implicit Renaming(ROB) 和 Explicit Renaming 的比较

这两种方法主要区别：

1. Implicit Renaming 在分发的时候，就会从寄存器堆读取数据，保存到保留站中；而 Explicit Renaming 是指令从 Issue Queue 到执行单元时候从寄存器堆读取数据
2. Implicit Renaming 的寄存器堆读取口较少，只需要考虑发射数乘以操作数个数，但所有类型的寄存器堆（整数、浮点）都需要读取；Explicit Renaming 的寄存器堆读取口更多，对于每个 Issue Queue，都需要操作数个数个读取口，但好处是可以屏蔽掉不需要访问的读取口，比如浮点 FMA 流水不需要读取整数寄存器堆。写和读是类似的：Implicit Renaming 中，寄存器堆的写入是从 ROB 上提交；而 Explicit Renaming 则是执行单元计算完后写入寄存器堆。

## 其他优化的手段

在第一和第二种设计中，当一条指令计算完成时，结果会直接通过 CDB 转发到其他指令的输入，这样可以提高运行效率。在第三种设计中，为了提高效率，也可以做类似的事情，但因为中间多了一级寄存器堆读取的流水线级，处理会更加复杂一点。比如，有一条 ALU 指令，可以确定它在一个周期后一定会得到计算结果，那么我就可以提前把依赖这条指令的其他指令 Dispatch 出去，然后在 ALU 之间连接一个 bypass 网络，这样就可以减少一些周期。

此外，为了提高吞吐率，一般计算单元都被设计为每个周期可以接受一条指令，在内部实现流水线执行，每个周期完成一条指令的计算。当然了，很多时候由于数据依赖问题，可能并不能达到每个周期每个计算单元都满载的情况。

有些时候，一些指令不方便后端实现，就会加一层转换，从指令转换为 uop，再由后端执行。这在 x86 处理器上很普遍，因为指令集太复杂了。像 AArch64 指令集，它在 Load/Store 的时候可以对地址进行计算，这种时候也是拆分为两条 uop 来执行。一些实用的指令需要三个操作数，比如 `D = A ? B : C`，在 Alpha 21264 中，这条指令会转换为两条 uop，这两条 uop 的操作数就只有两个，便于后端实现，否则在各个地方都允许三个操作数会导致一定的浪费。
