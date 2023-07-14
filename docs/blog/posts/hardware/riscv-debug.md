---
layout: post
date: 2021-12-12
tags: [riscv,cpu,debug,jtag,teaching]
categories:
    - hardware
---

# 「教学」RISC-V Debug 协议


## 背景

之前用过一些 RISC-V 核心，但是遇到调试相关的内容的时候就两眼一抹黑，不知道原理，出了问题也不知道如何排查，趁此机会研究一下工作原理。

## 架构

为了调试 RISC-V 核心，需要很多部件一起工作。按 RISC-V Debug Spec 所述，有这么几部分：

1. Debugger: GDB，连接到 OpenOCD 启动的 GDB Server
2. Debug Translator: OpenOCD，向 GDB 提供 Server 实现，同时会通过 FTDI 等芯片控制 JTAG
3. Debug Transport Hardware: 比如 FTDI 的芯片，可以提供 USB 接口，让 OpenOCD 控制 JTAG 信号 TMS/TDI/TCK 的变化，并读取 TDO
4. Debug Transport Module: 在芯片内部的 JTAG 控制器（TAP），符合 JTAG 标准
5. Debug Module Interface：RISC-V 自定义的一系列寄存器，通过这些寄存器来控制 Debug Module 的行为
6. Debug Module：调试器，控制 RISC-V 核心，同时也支持直接访问总线，也有内部的 Program Buffer

可以看到，DMI 是实际的调试接口，而 JTAG 可以认为是一个传输协议。

## JTAG

首先什么是 JTAG？简单来说，它工作流程是这样的：

1. JTAG TAP 维护了一个状态机，由 TMS 信号控制
2. 当状态机进入 CaptureDR/CaptureIR 状态的时候，加载数据到 DR/IR 中
3. 在 ShiftDR/ShiftIR 状态下，寄存器从 TDI 移入，从 TDO 移出
4. 当进入 UpdateDR/UpdateIR 状态的时候，把 DR/IR 的结果输出到其他单元

具体来说，JTAG 定义了两类寄存器：IR 和 DR。可以把 JTAG 理解成一个小的总线，我通过 IR 选择总线上的设备，通过 DR 向指定的设备上进行数据传输。比如在 RISC-V Debug Spec 里面，规定了以下的 5 位 IR 地址定义：

1. 0x00/0x1f: BYPASS
2. 0x01: IDCODE
3. 0x10: dtmcs
4. 0x11: dmi

可以类比为有四个设备：BYPASS，IDCODE，dtmcs，dmi，对应了一些地址。如果要选择 dtmcs 这个设备，就在 ShiftIR 阶段向 TDI 输入二进制的 00001 即可。选择地址以后，再向 DR 写入时，操作的就是 dtmcs 设备。

那么，每个设备是怎么操作的呢？假如我已经通过 IR 设置了当前设备是 dtmcs，然后进入 ShiftDR 模式时，JTAG 会同时输入和输出。输入的就是当前要输入的数据，输出的就是原来寄存器里的结果，这个结果可能是固定的，也可能是表示上一次输入对应的结果。

举个例子：IDCODE 设备，在 CaptureDR 阶段的时候，DR 总会被设为一个固定的 IDCODE，表示设备的 ID；在 Shift 的时候，这个 IDCODE 就会一位一位从 TDO 中输出，而 TDI 输入的数据都会被忽略掉。BYPASS 设备则是一个 1 位的寄存器，直接从 TDI 到寄存器，寄存器到 TDO，数据就这么流过去了。

那么，在 RISC-V Debug 里面，JTAG 是怎么用的呢？我们可以这么类比一下：CaptureDR 相当于读取寄存器到缓冲区，然后 ShiftDR 在读取缓冲区的同时写入缓冲区，最后 UpdateDR 则是把缓冲区中的数据写入到寄存器中。这和 MMIO 有点类似，只不过每次操作不是单独的写和读，而是一次操作等于先读后写。

还是来看例子。dtmcs 这个设备表示的是 DTM 当前的状态，它有 32 位，读取的时候可以得到 DMI 的状态和配置，写入的时候可以 reset DMI。以 OpenOCD 代码 `dtmcontrol_scan` 为例子，它做了这么几个事情：

1. 首先设置 IR 为 0x10，对应 dtmcs。
2. 向 DR 中写入数据，同时读取数据。
3. 设置 IR 为 0x11，对应 dmi，因为 dmi 操作是比较多的，所以它默认恢复到 dmi。

如果我只想读取 dtmcs 寄存器，那么只要设置写入数据为 0 即可，因为寄存器的设计里考虑到，如果写入全 0 是没有副作用的。同理，如果只想写入 dtmcs 寄存器，直接写入即可，因为设计的时候也保证读入寄存器的值是没有副作用的。这样，就在一个一读一写的操作中，实现了读或者写的功能。

那么，dmi 寄存器的用途是什么呢？我们前面提到过，JTAG 其实是一个传输层，而 DMI 又定义了一系列的寄存器，这会让人有点混乱，为啥到处都是寄存器？又是 JTAG 的 IR/DR，又是 dmi，dmi 又有一堆寄存器，这是什么关系？

首先我们来看 dmi 寄存器的定义。它由三部分组成：地址、数据和操作。由于 JTAG 每次操作是一读一写，虽然寄存器定义差不多，但是读和写的含义是不同的。

比如读的时候，它表示的是上一次 dmi 请求的结果。地址还是上一次请求的地址，数据则是上一次请求的结果，操作字段 0 表示成功，2 表示失败，3 表示还没执行完。而写的时候，地址和数据表示了对哪个寄存器写入什么数据，操作字段 0 表示无操作，1 表示读，2 表示写。

可以看到，如果想操作 dmi 定义的寄存器，需要如下几个步骤，这也是 OpenOCD `dmi_op_timeout` 要做的事情：

1. 设置 IR 为 0x11，对应 DMI。
2. 向 DR 写入请求的地址 + 数据 + 操作，丢弃读取的结果。
3. 等待若干个周期。
4. 向 DR 写入全 0，对应无操作，同时读取结果，这个结果就对应上面的请求。

可以预期，如果首先写入了一个写操作，那么第二次 DR scan 得到的结果就是是否成功写入；如果首先写入了一个读操作，那么第二次 DR scan 得到的结果就是目标寄存器的值。

可能看起来还是很绕，确实很绕，因为这里有一个封装的过程。首先，DMI 本身定义了一些寄存器，这些寄存器读/写都有一定的含义，比如控制某一个 RISC-V 核心暂停等等。接着，JTAG 需要传输 DMI 的读取和写入操作，同时还要考虑读写尚未完成的情况，怎么办？结论就是通过 DR 来实现，写入 DR 时，按照 DR 中的操作数，对应到 DMI 的写入/读取；然后读取 DR 的时候，按照 DMI 的状态，告诉 OpenOCD 目前是否已经完成了上一次 DMI 操作，和操作的结果。

## DMI

讲完 JTAG 以后，终于来到了 DMI。其实 DMI 就是一系列的寄存器，类似于 MMIO 设备，只不过访问方式不是我们通常的内存读写，而是通过 JTAG 的方式进行。它有很多个寄存器，摘录如下：

1. dmcontrol 0x10: Debug Module Control
2. dmstatus 0x11: Debug Module Status
3. hartinfo 0x12: Hart Info
4. hartsum 0x13: Hart Summary
5. command 0x16: Abstract Control and Status
6. data0 0x04: Abstract Data 0
7. progbuf0 0x20: Program Buffer 0
8. sbcs 0x38: System Bus Access Control and Status
9. sbaddress0 0x39: System Bus Address 31:0
10. sbdata0 0x3c: System Bus Data 31:0

OpenOCD 的 `examine` 函数对 DMI 初始化并进行一些参数的获取。它的操作如下：

1. 调用 dtmcontrol_scan，读取 JTAG 里的 dtmcs，可以得到 JTAG-DMI 的配置信息
2. 向 dmcontrol 写入，进行复位
3. 向 dmcontrol 写入，启用调试模块
4. 从 hartinfo 读取 hart 信息
5. 检查各个 hart 的状态

类似地，其他各种调试操作都是对这些 DMI 寄存器的读和写进行。RISC-V Debug Spec 附录里还提到了如何实现调试器的一些功能。

比如要读取 CPU 的寄存器（比如通用寄存器，CSR 等等）的话，有如下的方式：

第一种是 Abstract Command，直接向 DMI 写入要寄存器编号，就可以实现读/写。

第二种是 Program Buffer。它是一块小的代码存储，可以通过 DMI 向其中写入指令，比如 `csrw s0, mstatus; ebreak`，然后设置 s0 寄存器的值，再执行 Program Buffer 里的代码。

以 OpenOCD 代码为例，`register_read_abstract` 做了以下操作：

1. 找到要读取的寄存器对应的 Abstract Register Number
2. 进行 transfer 命令，DM 会读取对应寄存器到 data0 中
3. 从 data0 中读取寄存器内容

如果要读取内存的话，也有两种方法。一种是直接向 DMI 写入要读取的总线地址，然后再向指定的寄存器中读取数据。第二种还是利用 Program Buffer，写入一条 `lw s0, 0(s0)` 指令，然后先向 s0 写入地址，执行 Program Buffer 后，再把 s0 寄存器的值读出来。

## Abstract Command 实现

那么，如何实现上面提到的 Abstract Command（比如读写寄存器，读写内存等）呢？Debug Spec 里面提到一种 Execution-Based 的方式，即在 Debug mode 下，核心依然在执行代码，只不过执行的是调试用的特殊代码。它做的就是轮询 Debug Module 等待命令，接受到命令以后，就去读写寄存器/内存，然后通过 data0-12 来传输数据。

这里还有一个比较特别的点，就是读取寄存器的时候，寄存器的编号是直接记录在指令中的，所以可以让 Debug Module 动态生成指令，然后让核心刷新 ICache 然后跳转过去。另外，还可以利用 dscratch0/dscratch1 寄存器来保存 gpr，然后用 dret 退出的时候再恢复，这样就有两个 gpr 可以用来实现功能了，实际上这已经够用了（一个技巧是，把地址设为 0 附近，然后直接用 zero 寄存器加偏移来寻址）。

## 单步调试实现

在 dcsr 中，有一个值 step 表示是否在单步调试状态。设 step 为 1 的时候，如果不在 debug mode 中，只需要记录以及执行的指令数，当执行了一条指令后，视为下一个指令发生了进入 debug mode 的异常，这样就实现了单步调试。

## 软件断点实现

调试器为了打断点，一种简单的方式是，往断点处写入 ebreak 指令，然后设置 dcsr 的 ebreakm/s/u，表示在这些特权集里，ebreak 是进入 debug mode，而不是原来的处理过程。然后，程序运行到 ebreak 指令的时候，进入 debug mode，openocd 发现核心进入 halted 状态后，让 gdb 继续进行调试。

硬件方面的实现方法就是，在遇到 ebreak 的时候，判断一下当前的特权集，结合 ebreakm/s/u 判断跳转到什么状态。此外，由于它会写入指令到内存，所以还需要执行 fence.i 指令，而 OpenOCD 需要依赖 progbuf 来执行 fence.i 指令，所以为了让这个方案工作，还得实现 Program Buffer。

当然了，软件断点也有局限性，比如内存不可写，比如 ROM，不能覆盖里面的指令，这样就有可能出问题。而且硬件断点性能也更好，不需要来回这样写指令。

## Semihosting

ARM 有一种 semihosting 机制，就是处理器执行一种特定的指令序列，然后调试器看到整个序列的时候，不是进入 GDB 调试状态，而是去进行一些操作，比如输出信息，读写文件等等，然后结果通过 JTAG 写回去。OpenOCD 给 RISC-V 也做了类似的 semihosting 机制，只不过触发的指令序列不大一样，但是机制是类似的。

如果用过 Rocket Chip 仿真的或者以前的 ucb-bar/fpga-zynq 项目的话，会知道还有一个目的有些类似的东西：HTIF + fesvr，它是通过 fromhost/tohost 两组地址来进行通信，但是这个方法缺点是需要 poll tohost/fromhost 地址的内容，相对来说比较麻烦。

## Program Buffer

此外，debug spec 还有一个可选的功能，就是 Program Buffer，调试器可以往里面插入自定义的指令，然后结合 abstract command 进行操作。这样就可以做一些比较高效的操作，比如 OpenOCD 实现的批量写入内存：

```asm
sw s1, 0(a0)
addi a0, a0, 4
ebreak
```

并且设置 abstractauto，然后重复的操作是往 s1 里面写入新的数据，然后跳转到 program buffer，进行上面的 sw 操作，这样就可以一次 dmi 请求完成一次内存的写入，比较高效。

## 参考文档

1. RISC-V Debug Spec 0.13
2. IEEE Standard for JTAG 1149.1-2013
3. OpenOCD 相关代码