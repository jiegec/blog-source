---
layout: post
date: 2021-09-14
tags: [ooo,cpu,tomasulo,outoforder,renaming,brief-into-ooo]
categories:
    - hardware
---

# 浅谈乱序执行 CPU（一：乱序）

本文的内容已经整合到[知识库](/kb/hardware/ooo_cpu.html)中。

## 背景

最早学习乱序执行 CPU 的时候，是在 Wikipedia 上自学的，后来在计算机系统结构课上又学了一遍，但发现学的和现在实际采用的乱序执行 CPU 又有很大区别，后来又仔细研究了一下，觉得理解更多了，就想总结一下。

本文主要讨论乱序执行的部分。

本系列的所有文章：

- [浅谈乱序执行 CPU（一：乱序）](./brief-into-ooo.md)
- [浅谈乱序执行 CPU（二：访存）](./brief-into-ooo-2.md)
- [浅谈乱序执行 CPU（三：前端）](./brief-into-ooo-3.md)

<!-- more -->

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

## ROB (ReOrder Buffer)

[参考教材](https://web.stanford.edu/class/cs349g/cs349g-speculation.pdf)

为了实现精确异常，我们需要引入 ROB。在上面的 Tomasulo 算法中，计算单元计算完成的时候，就会把结果写入到寄存器堆中，因此精确异常时难以得到正确的寄存器堆取值。既然我们希望寄存器堆的状态与顺序执行的结果一致，我们需要引入 ROB。

ROB 实际上就是一个循环队列，队列头尾指针之间就是正在执行的指令，每个 ROB 表项记录了指令的状态、目的寄存器和目的寄存器将要写入的值。ROB 会检查队列头的指令，如果已经执行完成，并且没有异常，就可以让结果生效，并把指令从队列头中删去，继续检查后面的。Decode 出来的指令则会插入到 ROB 的尾部，并且随着指令的执行过程更新状态。遇到异常的指令，就把队列中的指令、保留站和执行单元清空，从异常处理地址开始重新执行。

为了保证寄存器堆的正确性，运算单元的运算结果会写入 ROB 项中，当这一项在 ROB 队列头部被删去时，就会写入寄存器堆。在经典 Tomasulo 中，寄存器重命名为保留站的 ID，但在这种设计中，应该重命名为 ROB 的 ID，也就是说，需要维护一个寄存器到 ROB ID 的映射，当指令进入保留站的时候，需要从寄存器堆或者 ROB 中去读取操作数的值。在 CDB 上广播的也是 ROB 的 ID，而不是保留站的 ID。

这种方法中，ROB 的大小成为了一个新的瓶颈，因为每条在正在执行的指令都需要在 ROB 中记录一份。不过好处是实现了精确异常。

Pentium III 采用的就是这种方法，在 [The Microarchitecture of the Pentium4 Processor](https://courses.cs.washington.edu/courses/cse378/10au/lectures/Pentium4Arch.pdf) 中是这么描述的：

> It allocates the data result registers and the ROB entries as a single, wide
> entity with a data and a status field. The ROB data field is used to store the
> data result value of the uop, and the ROB status field is used to track the
> status of the uop as it is executing in the machine. These ROB entries are
> allocated and deallocated sequentially and are pointed to by a sequence number
> that indicates the relative age of these entries.  Upon retirement, the result
> data is physically copied from the ROB data result field into the separate
> Retirement Register File (RRF). The RAT points to the current version of each of
> the architectural registers such as EAX.  This current register could be in the
> ROB or in the RRF.

这和上面描述的方法是一致的：ROB 会存指令的结果，RAT 记录每个架构寄存器对应的 ROB 或者 RRF 的表项，指令从 ROB 提交时，指令的结果会从 ROB 复制到 RRF 上，同时更新 RAT。而 Intel 在 NetBurst 微架构把实现换成了下面要讲的方法。

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

和 @CircuitCoder 讨论并参考 [BOOM 文档](https://docs.boom-core.org/en/latest/sections/reorder-buffer.html#parameterization-rollback-versus-single-cycle-reset) 后发现，另一种办法是记录一个 Committed Map Table，也就是，只有当 ROB Head 的指令被 Commit 的时候，才更新 Committed Map Table，可以认为是顺序执行的寄存器映射表。当发生异常的时候，把 Committed Map Table 覆盖到 Register Map Table 上。这样需要的周期比较少，但是时序可能比较差。从 [The Microarchitecture of the Pentium4 Processor](https://courses.cs.washington.edu/courses/cse378/10au/lectures/Pentium4Arch.pdf) 的图 5 来看，Pentium 4 也是采用这种实现方法，分别维护 Frontend RAT 和 Retirement RAT。

## Implicit Renaming(ROB) 和 Explicit Renaming 的比较

这两种方法主要区别：

1. Implicit Renaming 在分发的时候，就会从寄存器堆读取数据，保存到保留站中；而 Explicit Renaming 是指令从 Issue Queue 到执行单元时候从寄存器堆读取数据
2. Implicit Renaming 的寄存器堆读取口较少，只需要考虑发射数乘以操作数个数，但所有类型的寄存器堆（整数、浮点）都需要读取；Explicit Renaming 的寄存器堆读取口更多，对于每个 Issue Queue，都需要操作数个数个读取口，但好处是可以屏蔽掉不需要访问的读取口，比如浮点 FMA 流水不需要读取整数寄存器堆。写和读是类似的：Implicit Renaming 中，寄存器堆的写入是从 ROB 上提交；而 Explicit Renaming 则是执行单元计算完后写入寄存器堆。

## 其他优化的手段

在第一和第二种设计中，当一条指令计算完成时，结果会直接通过 CDB 转发到其他指令的输入，这样可以提高运行效率。在第三种设计中，为了提高效率，也可以做类似的事情，但因为中间多了一级寄存器堆读取的流水线级，处理会更加复杂一点。比如，有一条 ALU 指令，可以确定它在一个周期后一定会得到计算结果，那么我就可以提前把依赖这条指令的其他指令 Dispatch 出去，然后在 ALU 之间连接一个 bypass 网络，这样就可以减少一些周期。

此外，为了提高吞吐率，一般计算单元都被设计为每个周期可以接受一条指令，在内部实现流水线执行，每个周期完成一条指令的计算。当然了，很多时候由于数据依赖问题，可能并不能达到每个周期每个计算单元都满载的情况。

有些时候，一些指令不方便后端实现，就会加一层转换，从指令转换为 uop，再由后端执行。这在 x86 处理器上很普遍，因为指令集太复杂了。像 AArch64 指令集，它在 Load/Store 的时候可以对地址进行计算，这种时候也是拆分为两条 uop 来执行。一些实用的指令需要三个操作数，比如 `D = A ? B : C`，在 Alpha 21264 中，这条指令会转换为两条 uop，这两条 uop 的操作数就只有两个，便于后端实现，否则在各个地方都允许三个操作数会导致一定的浪费。

## RAT 的更新和恢复

在前面提到，使用 Explicit Renaming + ROB 方法的处理器，需要维护一个最新的 Frontend RAT，也要保证出了异常的时候，还要能够恢复到正确的 RAT。方法上面也提到过，可以在 ROB 里记录 Rename 信息的变化，出现异常的时候按照逆过程来恢复，或者保存一份 Retirement RAT，出现异常的时候，直接用 Retirement RAT 覆盖 Frontend RAT 即可。由于异常出现的频率通常比较小，所以实现对性能的影响不会很大。

但是，除了异常，现代处理器通常还会有很多小范围的微架构级别的回滚，例如分支预测错误，内存序错误等等，由于微架构上的一些预测执行，预测失败导致需要回滚部分指令再执行新的指令，此时回滚的位置就可能在 ROB 中间的某个位置了，并且由于这些微架构的回滚相比异常会更加频繁，如何高效地实现 Frontend RAT 的回滚，就成为了新的问题。

如果还是像之前那样在 ROB 每个表项里记录 Rename 信息的变化，可以按照逆过程来恢复；也可以从 Retirement RAT 开始按照 Rename 信息正向过程来恢复，只是换了个方向；如果想要一步直接得到正确的 RAT，就需要在之前预测执行的时候就存档一份 RAT，那么空间上的需求又比较大了，例如可能每个预测执行的分支执行都要记录一份 Checkpoint RAT。

但是结合实际的指令集，又会发现一个新问题：不同的指令要写入的寄存器个数不同，有的指令不写入寄存器，例如 store 指令，nop 指令等等，有的指令要写入多个寄存器，例如 x86 在计算的同时还要生成 flags，这样就要写入俩寄存器了。如果 ROB 要保存 Rename 信息，那就要按最多可能写入的寄存器个数来预留空间，这样就会造成浪费。因此可以把这些 Rename 信息独立出来，存到一个叫做 History File 的地方，只有要写入寄存器的指令才会分配 entry，如果要写入多个寄存器，那就分配多个 entry，不写入寄存器的指令就不用浪费空间。

## Move Elimination

现代的处理器很多会实现 Move Elimination，就是把寄存器之间的 move 指令，不经过 ALU，直接在重命名阶段实现，例如 `r1 = r0`，不需要给 r1 分配一个新的物理寄存器再把 r0 的结果写进去，而是直接把 r1 映射到 r0 对应的物理寄存器。这样，避免了寄存器的读写，也不需要占用 ALU，可以带来性能的提升。

但是，直接这么做会带来一个问题：我们前面提到，物理寄存器的释放规则是，同一个架构寄存器，在创建新的物理寄存器映射的指令从 ROB 提交的时候，旧的物理寄存器可以释放。举个例子：

1. 假如 r0 一开始映射到物理寄存器 p0
2. 来了一条指令，要写入 r0，这时候分配了一个新的物理寄存器 p1，把 r0 映射到 p1
3. 当这条指令提交的时候，所有可能读取 p0 的指令都已经提交过了，因此可以把 p0 释放掉

现在问题来了，如果实现了 Move Elimination，把 r1 直接指向了 r0 的物理寄存器，也就是 p0，此时同一个物理寄存器被两个架构寄存器所使用，如果按照上面的方法做，p0 会被错误的释放掉。那么就需要改进寄存器释放的实现方法。

[Zero cycle move 专利](https://patents.google.com/patent/US20130275720A1/) 和 [Zero cycle move using free list counts 专利](https://patents.google.com/patent/US20160026463A1) 提到了一个方法，对于在 Move Elimination 被重复映射的物理寄存器，在 Duplicated Register Array 中记录它的重复次数，类似于引用计数法，Move Elimination 的时候增加引用计数，当引用计数到零的时候再释放：

1. 假如 r0 一开始映射到物理寄存器 p0
2. 执行 Move Elimination，把 r1 也指向了 p0，在 Duplicated Register Array 中记录 p0 重复了两次
2. 来了一条指令 A，要写入 r0，这时候分配了一个新的物理寄存器 p1，把 r0 映射到 p1
3. 当指令 A 提交的时候，发现 Duplicated Register Array 中记录 p0 重复了两次，由于 r0 不再映射到 p0，所以计数减去一，如果后续有指令写入 r1，提交的时候才会把 p0 最终释放掉

[Last physical register reference scheme 专利](https://patents.google.com/patent/US20210064376A1) 提到了另一种办法：Rename 的时候，“遍历”一下 RAT，看看旧的物理寄存器还有多少人在用，如果只剩下一个，打标记，当指令提交的时候，释放旧的物理寄存器；如果剩下不止一个，那就不释放旧的物理寄存器。举个例子：

1. 假如 r0 一开始映射到物理寄存器 p0，此时的 RAT 是 r0 -> p0
2. 执行 Move Elimination，把 r1 也指向了 p0，此时的 RAT 是 r0 -> p0，r1 -> p0
3. 来了一条指令 A，要写入 r0，r0 之前指向 p0，扫描 RAT，发现 p0 原来有两个架构寄存器的映射：r0 -> p0 和 r1 -> p0，于是标记指令 A 为 Not Last Reference，同时分配了一个新的物理寄存器 p1，把 r0 映射到 p1，此时的 RAT 是 r0 -> p1，r1 -> p0
4. 又来了一条指令 B，要写入 r1，r1 之前指向 p0，扫描 RAT，发现 p0 只有一个架构寄存器的映射：r1 -> p0，意味着当指令 B 要提交的时候，p0 可以释放了，所以标记指令 B 为 Last Reference
5. 当指令 A 提交的时候，因为标记为 Not Last Reference，所以不会释放 p0
6. 当指令 B 提交的时候，因为标记为 Last Reference，所以要释放 p0

它的思路也很简单：与其记录引用计数，不如就去查查 RAT，看看实际上到底引用了多少次，如果只剩下一次了，那提交的时候就要释放；如果引用了不止一次，那就不释放。但是这个方法的难点是，怎么在硬件上快速查询 RAT，知道有多少个架构寄存器映射到这个物理寄存器上。

这部分内容参考了 [AArch64-Explore: Exploration of Apple CPUs](https://github.com/name99-org/AArch64-Explore) 的分析。

## 精确异常 vs 非精确异常

精确异常是指发生异常的指令之前的指令都完成，之后的没有执行。一般来说，实现方式是完成异常指令之前的所有指令，并撤销异常指令之后的指令的作用。非精确异常则是不保证这个性质，[网上资料](http://bwrcs.eecs.berkeley.edu/Classes/cs152/lectures/lec12-exceptions.pdf) 说，这种情况下硬件实现更简单，但是软件上处理比较困难。

一个非精确异常的例子是 [Alpha](https://courses.cs.washington.edu/courses/cse548/99wi/other/alphahb2.pdf)，在章节 4.7.6.1 中提到，一些浮点计算异常可能是非精确的，并且说了一句：`In general, it is not feasible to fix up the result value or to continue from the trap.`。同时给出了一些条件，只有当指令序列满足这些条件的时候，异常才是可以恢复的。还有一段描述，摘录在这里：

	Alpha lets the software implementor determine the precision of
	arithmetic traps.  With the Alpha architecture, arithmetic traps (such
	as overflow and underflow) are imprecise—they can be delivered an
	arbitrary number of instructions after the instruction that triggered
	the trap. Also, traps from many different instructions can be reported
	at once. That makes implementations that use pipelining and multiple
	issue substantially easier to build.  However, if precise arithmetic
	exceptions are desired, trap barrier instructions can be explicitly
	inserted in the program to force traps to be delivered at specific
	points.

具体来说，在 [Reference Manual](http://www.bitsavers.org/pdf/dec/alpha/Sites_AlphaAXPArchitectureReferenceManual_2ed_1995.pdf) 中第 5.4.1 章节，可以看到当触发 Arithmetic Trap 的时候，会进入 Kernel 的 entArith 函数，并提供参数：a0 表示 exception summary，a1 表示 register write mask。exception summary 可以用来判断发生了什么类型的 exception，比如 integer overflow，inexact result 等等。一个比较特别的 exception 类型是 software completion。第二个参数表示的是触发异常的指令（一个或多个）会写入哪些寄存器（64 位，低 32 位对应整数寄存器，高 32 位对应浮点寄存器），然后保存下来的 PC 值为最后一条执行的指令的下一个地址，从触发异常的第一条指令到最后一条指令就是 trap shadow，这部分指令可能执行了一部分，没有执行一部分，一部分执行结果是错误的。

Linux 处理代码在 `arch/alpha/kernel/traps.c` 的 `do_entArith` 函数中。首先判断，如果是 software completion，那就要进行处理；否则直接 SIGFPE 让程序自己处理或者退出。如果是精确异常，那就对 PC-4 进行浮点模拟；如果是非精确异常，就从 trap shadow 的最后一条指令开始往前搜索，并同时记录遇到的指令写入的寄存器，如果发现指令的写入的寄存器已经覆盖了 register write mask，就说明找到了 trap shadow 的开头，则模拟这条指令，然后从下一条开始重新执行。具体代码如下：

```cpp
long
alpha_fp_emul_imprecise (struct pt_regs *regs, unsigned long write_mask)
{
	unsigned long trigger_pc = regs->pc - 4;
	unsigned long insn, opcode, rc, si_code = 0;

	/*
	 * Turn off the bits corresponding to registers that are the
	 * target of instructions that set bits in the exception
	 * summary register.  We have some slack doing this because a
	 * register that is the target of a trapping instruction can
	 * be written at most once in the trap shadow.
	 *
	 * Branches, jumps, TRAPBs, EXCBs and calls to PALcode all
	 * bound the trap shadow, so we need not look any further than
	 * up to the first occurrence of such an instruction.
	 */
	while (write_mask) {
		get_user(insn, (__u32 __user *)(trigger_pc));
		opcode = insn >> 26;
		rc = insn & 0x1f;

		switch (opcode) {
		      case OPC_PAL:
		      case OPC_JSR:
		      case 0x30 ... 0x3f:	/* branches */
			goto egress;

		      case OPC_MISC:
			switch (insn & 0xffff) {
			      case MISC_TRAPB:
			      case MISC_EXCB:
				goto egress;

			      default:
				break;
			}
			break;

		      case OPC_INTA:
		      case OPC_INTL:
		      case OPC_INTS:
		      case OPC_INTM:
			write_mask &= ~(1UL << rc);
			break;

		      case OPC_FLTC:
		      case OPC_FLTV:
		      case OPC_FLTI:
		      case OPC_FLTL:
			write_mask &= ~(1UL << (rc + 32));
			break;
		}
		if (!write_mask) {
			/* Re-execute insns in the trap-shadow.  */
			regs->pc = trigger_pc + 4;
			si_code = alpha_fp_emul(trigger_pc);
			goto egress;
		}
		trigger_pc -= 4;
	}

egress:
	return si_code;
}
```

ARM 架构也有 imprecise asynchronous external abort：

	Normally, external aborts are rare. An imprecise asynchronous external
	abort is likely to be fatal to the process that is running. An example
	of an event that might cause an external abort is an uncorrectable
	parity or ECC failure on a Level 2 Memory structure.
	
	Because imprecise asynchronous external aborts are normally fatal to the
	process that caused them, ARM recommends that implementations make
	external aborts precise wherever possible.

不过这更多是因为内存的无法预知的错误，这种时候机器直接可以拿去维修了。

[文章](https://community.arm.com/developer/ip-products/processors/f/cortex-a-forum/5056/can-anyone-provide-an-example-of-asynchronous-exceptions) 提到了两个 precise/imprecise async/sync的例子：

1. 外部中断是异步的，同时也是 precise 的。
2. 对于一个 Write-allocate 的缓存，如果程序写入一个不存在的物理地址，那么写入缓存的时候不会出现错误，但当这个 cache line 被写入到总线上的时候，就会触发异常，这个异常是异步并且非精确的，因为之前触发这个异常的指令可能已经完成很久了。这种时候这个进程也大概率没救了，直接 SIGBUS 退出。

## 处理器仿真模型

最后列举一下科研里常用的一些处理器仿真模型：

- gem5: [论文 The gem5 Simulator: Version 20.0+](https://arxiv.org/abs/2007.03152) [代码](https://gem5.googlesource.com/public/gem5)
- Multi2Sim: [论文 Multi2Sim: A simulation framework for CPU-GPU computing](https://ieeexplore.ieee.org/document/7842946) [代码](https://github.com/Multi2Sim/multi2sim)
- Scarab: [代码](https://github.com/hpsresearchgroup/scarab)
- Sniper: [论文 Sniper: exploring the level of abstraction for scalable and accurate parallel multi-core simulation](https://dl.acm.org/doi/abs/10.1145/2063384.2063454) [官网](https://snipersim.org/w/The_Sniper_Multi-Core_Simulator) [仓库](https://github.com/snipersim/snipersim)
- ZSim: [论文 ZSim: fast and accurate microarchitectural simulation of thousand-core systems](https://people.csail.mit.edu/sanchez/papers/2013.zsim.isca.pdf) [代码](https://github.com/s5z/zsim)
- PTLsim: [论文 PTLsim: A Cycle Accurate Full System x86-64 Microarchitectural Simulator](https://ieeexplore.ieee.org/document/4211019)