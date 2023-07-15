---
layout: post
date: 2023-03-23
tags: [riscv,cpu,spike,cosim,simulation,verilator]
categories:
    - hardware
---

# 单核处理器的协同仿真

## 背景

今年的龙芯杯又开始报名了，我来写一篇关于协同仿真（cosim）的博客蹭蹭热度。下面的内容参考了一些已有的协同仿真的框架，例如 [ibex co-sim](https://ibex-core.readthedocs.io/en/latest/03_reference/cosim.html) 和 [OpenXiangShan/difftest](https://github.com/OpenXiangShan/difftest)。

<!-- more -->

## 协同仿真

RTL 层次的协同仿真可以做不同层次的，这里讨论的是指令提交层次，具体来讲，就是把 CPU 和一个模拟器放在一起协同仿真，检查每条指令执行完以后的状态是否一致。基于代码样例的测试虽然可以覆盖很多情况，但是如果出了错误，报错的地方不一定是出现问题的地方，有些时候就需要往回找很久，才能找到刚出现问题的地方。软件上，大家经常苦于内存错误，经常找不到刚出现溢出的地方，所以要用 valgrind 或者 asan 等工具来直接定位第一次出错的地方。硬件上也是类似，为了精确定位到出错的波形，可以用 cosim。

cosim 是怎么工作的呢？模拟器是软件实现的，它原子地执行一条条指令，同时记录下当前的状态，例如寄存器的取值、内存的状态等等。如果可以让 CPU 和模拟器锁步运行，也就是 CPU 执行一条指令，模拟器执行一条指令，然后比对状态，一旦出现不一致，就直接报错。但实际上 CPU 可能会更加复杂，因为它指令的执行拆分成了很多部分，需要针对流水线进行一些修改，使得它可以生成一个匹配模拟器的原子的执行流。

整体的工作流程如下：

1. 选择一个模拟器，自己写或者使用一个现成的。考虑到模拟器实现的功能和 CPU 不一定一致，有时候需要修改模拟器的源码，所以可以考虑使用一些现成的开源软件，如果是为了 cosim 设计的就更好了。
2. 找到模拟器的单步执行接口，并且让模拟器可以把内部状态暴露出来。这一步可能需要修改源代码。
3. 修改 RTL，把指令的提交信息、寄存器堆的内容通过一些方法传递出来。
4. 修改仿真顶层，每当指令提交的时候，单步执行模拟器，然后比对双方的状态。

## 模拟器

选择模拟器，要根据你所实现的指令集来选择。下面以 Spike 为例，用来和 RISC-V CPU 进行协同仿真。spike 实现了比较完整的 RISC-V 指令集，并且以库的形式提供了它的 API，但还需要一些修改，让它更加适合协同仿真。这一部分参考了 [ibex co-sim](https://ibex-core.readthedocs.io/en/latest/03_reference/cosim.html)的文档。

首先，spike 提供了 step 函数，就是我们想要的单步执行。但是，spike 的 step 在遇到异常或者中断的时候也会返回，但实际上在处理器一侧，通常异常是单独处理的，所以这时候就要修改 spike 的 step 函数，如果遇到异常了，继续执行，直到执行了一条指令为止。与此同时，spike 没有记录最后一次执行的指令的 pc，只记录了下一个 PC，那么在发生异常的时候，就不会记录异常处理的第一条指令的 PC，这里也要进行针对性的修改。

```c
state.last_inst_pc = pc;
pc = execute_insn_logged(this, pc, fetch);
advance_pc();
```

做了这些修改以后，就足够在 cosim 中运行一些简单的程序了。

## 处理器

接下来，需要修改处理器，让它可以汇报每个周期完成执行的指令情况，具体的格式因实现而异，最后都需要把这些信息暴露给仿真顶层，可能的方法有：

1. 通过多级的 module output 一路传到顶层，最终是顶层模块的输出信号。这种方法改动比较大，而且麻烦。
2. 通过 DPI 函数，每个周期调用一次，把信息通过 DPI 的参数传递给 C 函数。这种方法比较推荐。
3. 通过仿真器的功能，例如 verilator 可以通过添加注释的方法，把信号暴露出去。

仿真顶层拿到信息以后，就可以进行 cosim 了：CPU 执行一条指令，就让模拟器也 step 一步，然后比较二者的状态。状态怎么比对呢？常见的有通用寄存器，RISC-V 的 CSR。既可以通过记录寄存器堆的写入来比对，又可以直接把整个寄存器堆的内容导出来比对。实际上这些部分的性能影响都是很小的。

那么，内存怎么比对呢？对于简单的顺序处理器，读写也是顺序的，那么可以把读写的日志放到一个队列 deque 中，然后让模拟器也记录下内存的读写，从 deque 进行 pop 和比对。但实际情况可能会比较复杂，例如更复杂的处理器里可能会出现乱序访存等情况，同时处理器还可能会进行写合并等操作，这时候就需要在仿真顶层做一些匹配和合并的操作。实在觉得麻烦，也可以先不管内存，直接比对寄存器，也足够定位很多内存问题，因为 RISC-V 读内存总是要加载到寄存器中的。

## 特殊情况

实现了前面的部分，就可以跑很多程序了，但是对于一些复杂的程序，例如 Linux，还缺少一样东西：外设和中断。能想到的第一种方法就是，用 C 代码再写一个外设的模型，然后接到模拟器的虚拟总线上。但是中断就会比较麻烦，因为中断的时机比较难保证同步，所以通常的方法是，把模拟器的中断处理关掉，当 CPU 发送 trap 的时候，让模拟器也发生一次 trap。

```c
// handle trap
if (interrupt) {
  trap_t trap = 0x8000000000000000 | interrupt;
  proc->take_trap(trap, proc->get_state()->pc);
  interrupt = 0;
}
```

但有一些外设不容易保证完全一致，例如 mtime 读取时间，很难保证 CPU 里读取的时间值和模拟器里的 mtime 一致。这时候就可以采用另一个办法：记录所有对外设的 load 指令，因为有副作用的关系，一定是顺序的，这时候就可以像前面提到的队列的方式，CPU 进行 uncached load 的时候，就把 load 的地址、数据和长度记录到队列中，当模拟器也要进行 load 的时候，匹配上地址和长度，返回数据。

```c
// match rtl uncached load event
if (!uncached_load_events.empty()) {
  uncached_load_event ev = uncached_load_events.front();
  if (ev.addr == addr && ev.len == len) {
    memcpy(bytes, (char *)&ev.data, len);
    uncached_load_events.pop_front();
    return true;
  }
}
```

但这样实际上就假设了外设实现是正确的。如果还需要验证外设实现是否正确，需要结合两种方法，对于不确定结果的 load（例如 mtime），就按照 CPU 的结果来，否则就用 C 实现的外设模型进行比对。

除了这些意外，处理器实现的 feature 可能会和模拟器有一些出入，这些都比较容易解决，直接修改代码，屏蔽掉没有实现的功能，保持一致即可。

## ChatGPT/Bard 的回复

提问：

How can I verify my RISC-V processor design via co-simulation with spike?

ChatGPT:

Co-simulation with Spike can be a great way to verify your RISC-V processor design. Here's a high-level overview of the process:

1. Write a testbench: You'll need to create a testbench that can generate inputs to your processor and check the outputs. This testbench can be written in any language you prefer, but most people use a hardware description language like Verilog or VHDL.

2. Connect your processor to Spike: To run a co-simulation with Spike, you'll need to connect your processor design to Spike using a TLM (transaction-level modeling) interface. Spike has a built-in TLM interface called the "Spike External Debug Interface" (S-EDI) that you can use.

注：查不到 Spike External Debug Interface

3. Configure the co-simulation: You'll need to configure the co-simulation by specifying the parameters of your processor design and Spike, such as the clock frequency and the reset signal.

4. Run the simulation: Once your testbench is written, your processor is connected to Spike, and the co-simulation is configured, you can run the simulation. Your testbench will generate inputs to your processor, which will be processed by Spike and your processor design. The output of your processor will be checked by your testbench to verify that it's correct.

5. Debug any issues: If you encounter any issues during the simulation, you'll need to debug them. This can involve looking at waveforms or logs to understand where things went wrong.

Here are some more detailed steps to follow:

1. Write your testbench in Verilog or VHDL. Your testbench should be able to generate inputs to your processor design and check the outputs. You can use any verification methodology you prefer, such as directed tests or random tests.

2. Connect your processor design to Spike using the S-EDI interface. The S-EDI interface is a TLM interface that allows Spike to communicate with your processor design. You'll need to instantiate the S-EDI module in your testbench and connect it to your processor design. You can find more information about the S-EDI interface in the Spike documentation.

3. Configure the co-simulation. You'll need to specify the clock frequency and reset signal for your processor design and Spike. You may also need to specify other parameters, such as the memory map for your processor design.

4. Run the simulation. Once your testbench is written, your processor is connected to Spike, and the co-simulation is configured, you can run the simulation. You can use a simulator like ModelSim or QuestaSim to run the simulation.

5. Debug any issues. If you encounter any issues during the simulation, you'll need to debug them. You can use the waveform viewer in your simulator to understand what's happening in your design. You can also use the Spike debugger to debug your processor design. The Spike debugger allows you to step through your code and examine the processor state.

By following these steps, you can use co-simulation with Spike to verify your RISC-V processor design.

Bard:

Co-simulation is a technique used in verification to run two or more models of a system in lockstep, with each model executing a different part of the system. This allows the models to be used together to verify that the system behaves as expected.

To co-simulate your RISC-V processor design with Spike, you will need to create a model of your processor in Spike and a model of the system that your processor will be embedded in. You will then need to configure the two models to run in lockstep, with each model communicating with the other through a shared memory buffer.

Once the co-simulation is running, you can use it to verify that your processor design behaves as expected. You can do this by running test cases on the system model and observing the behavior of your processor model. If the processor model behaves as expected, then you can be confident that your design is correct.

Here are some of the benefits of using co-simulation:

* It can help you to find errors in your design early in the development process.
* It can help you to verify that your design meets the requirements of the system that it will be embedded in.
* It can help you to optimize your design for performance and power consumption.

Here are some of the challenges of using co-simulation:

* It can be difficult to create accurate models of both your processor and the system that it will be embedded in.
* It can be difficult to configure the co-simulation to run in lockstep.
* It can be difficult to interpret the results of the co-simulation.

Overall, co-simulation is a powerful technique that can be used to verify your RISC-V processor design. However, it is important to be aware of the challenges involved in using co-simulation.

## 多核

以上的方法都是针对单核 CPU 进行协同仿真的，但多核会更加复杂，多核涉及到不同核心之间的同步、通信等等，很难把一个周期精确的 CPU 和一个不精确的模拟器匹配起来。香山提供了一个思路：<https://github.com/OpenXiangShan/XiangShan-doc/blob/main/slides/20210624-RVWC-SMP-Difftest%20%E6%94%AF%E6%8C%81%E5%A4%9A%E5%A4%84%E7%90%86%E5%99%A8%E7%9A%84%E5%B7%AE%E5%88%86%E6%B5%8B%E8%AF%95%E6%96%B9%E6%B3%95.pdf>