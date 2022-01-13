---
layout: post
date: 2021-09-14 13:47:00 +0800
tags: [ooo,cpu,tomasulo,outoforder,renaming]
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

再分析一下寄存器堆需要哪些读写口。有一条规律是，寄存器堆的面积与读写口个数的平方成正比。对于每条发射的指令，都需要从寄存器堆读操作数，所以读口是操作数x指令发射数。当执行单元完成计算的时候，需要写入寄存器堆，所以每个执行单元都对应一个寄存器堆的写口。

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

## 其他优化的手段

在第一和第二种设计中，当一条指令计算完成时，结果会直接通过 CDB 转发到其他指令的输入，这样可以提高运行效率。在第三种设计中，为了提高效率，也可以做类似的事情，但因为中间多了一级寄存器堆读取的流水线级，处理会更加复杂一点。比如，有一条 ALU 指令，可以确定它在一个周期后一定会得到计算结果，那么我就可以提前把依赖这条指令的其他指令 Dispatch 出去，然后在 ALU 之间连接一个 bypass 网络，这样就可以减少一些周期。

此外，为了提高吞吐率，一般计算单元都被设计为每个周期可以接受一条指令，在内部实现流水线执行，每个周期完成一条指令的计算。当然了，很多时候由于数据依赖问题，可能并不能达到每个周期每个计算单元都满载的情况。

有些时候，一些指令不方便后端实现，就会加一层转换，从指令转换为 uop，再由后端执行。这在 x86 处理器上很普遍，因为指令集太复杂了。像 AArch64 指令集，它在 Load/Store 的时候可以对地址进行计算，这种时候也是拆分为两条 uop 来执行。一些实用的指令需要三个操作数，比如 `D = A ? B : C`，在 Alpha 21264 中，这条指令会转换为两条 uop，这两条 uop 的操作数就只有两个，便于后端实现，否则在各个地方都允许三个操作数会导致一定的浪费。

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


## 例子分析

[Alpha 21264](https://www.cis.upenn.edu/~milom/cis501-Fall09/papers/Alpha21264.pdf) 是一个采用了 Explicit Register Renaming 和 ReOrder Buffer（论文中叫 Inflight Window） 的一个处理器。可以看到，它把指令分为了两类，Integer 和 Floating Point。Issue Queue 大小分别为 20 和 15，而 Register File 大小分别为 80x2 和 72。ROB 大小为 80。

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

具体来说，在 [Reference Manual](http://www.bitsavers.org/pdf/dec/alpha/Sites_AlphaAXPArchitectureReferenceManual_2ed_1995.pdf) 中第 5.4.1 章节，可以看到当触发 Arithmetic Trap 的时候，会进入 Kernel 的 entArith 函数，并提供参数：a0 表示 exception summary，a1 表示 register write mask。exception summary 可以用来判断发生了什么类型的 exception，比如 integer overflow，inexact result 等等。一个比较特别的 exception 类型是 software completion。第二个参数表示的是触发异常的指令（一个或多个）会写入哪些寄存器（64位，低32位对应整数寄存器，高32位对应浮点寄存器），然后保存下来的 PC 值为最后一条执行的指令的下一个地址，从触发异常的第一条指令到最后一条指令就是 trap shadow，这部分指令可能执行了一部分，没有执行一部分，一部分执行结果是错误的。

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

## RISC-V CPU 处理器前端设计

再来分析一下乱序执行 CPU 的前端部分。以 RISC-V 为例，指令长度有 4 字节或者 2 字节两种，其中 2 字节属于压缩指令集。如何正确并高效地进行取指令译码？

首先，我们希望前端能够尽可能快地取指令，前端的取指能力要和后端匹配，比如对于一个四发射的 CPU，前端对应地需要一个周期取 `4*4=16` 字节的指令。但是，这 16 字节可能是 4 条非压缩指令，也可能是 8 条压缩指令，也可能是混合的情况。所以，这里会出现一个可能出现指令条数不匹配的情况，所以中间可以添加一个 Fetch Buffer，比如 [BOOM](https://github.com/riscv-boom/riscv-boom) 的实现中，L1 ICache 每周期读取 16 字节，然后进行预译码，出来 8 条指令，保存到 Fetch Buffer 中。这里需要考虑以下几点：首先从 ICache 读取的数据是对齐的，但是 PC 可能不是，比如中间的地址。其次，可能一个 4 字节的非压缩指令跨越了两次 Fetch，比如前 2 个字节在前一个 Fetch Bundle，后 2 个字节在后一个 Fetch Bundle；此外，每个 2 字节的边界都需要判断一下是压缩指令还是非压缩指令。

其次，需要配合分支预测。如果需要保证分支预测正确的情况下，能够在循环中达到接近 100% 的性能，那么，在 Fetch 分支结尾的分支指令的同时，需要保证下一次 Fetch 已经得到了分支预测的目的地址。这个就是 BOOM 里面的 L0 BTB (1-cycle redirect)。但是，一个周期内完成的分支预测，它的面积肯定不能大，否则时序无法满足，所以 BOOM 里面还设计了 2-cycle 和 3-cycle 的比较高级的分支预测器，还有针对函数调用的 RAS（Return Address Stack）。