---
layout: post
date: 2023-04-07 00:48:00 +0800
tags: [sram,collision,readunderwrite,xpm,xilinx,bram]
category: hardware
title: RAM 读写冲突
---

## 背景

在 FPGA 或者 ASIC 中，通常都需要使用 RAM，通过读口、写口或者读写口来进行访问。常见的配置有单读写口（1RW），一读一写（1R1W）等等，读口通常有 1 个周期的延时。那么，如果在同一个周期内，读口和写口访问了同一个地址，会发生什么呢？可能会想到几种情况：

1. 读和写都失败，读出的数据未定义，数据没写进去
2. 数据写进去了，读出的数据未定义
3. 数据写进去了，读出了写之前的旧数据
4. 数据写进去了，读出了同一个周期写入的新数据

下面以具体的例子来看看，实际情况是什么样子。

## Xilinx FPGA

首先测试的是 Xilinx FPGA 上的 RAM，测试的对象是 XPM，统一设置读延迟为一个周期，使用 Vivado 仿真。

### 一读一写

首先测试一读一写，也就是 xpm_memory_sdpram 模块。模块支持三种模式：NO_CHANGE（默认值）、READ_FIRST 和 WRITE_FIRST，因此我例化了三份，输入一样的信号，设置为三种不同的模式，然后比较输出结果。为了简化，读写使用一个时钟。下面是测试的波形：

<script type="WaveDrom">
{
  signal:
    [
      { name: "clk", wave: "p...."},
      { name: "w_addr", wave: "2....", data: ["0000"]},
      { name: "w_data", wave: "2x2xx", data: ["1111", "2222"]},
      { name: "w_en", wave: "1010."},
      { name: "r_addr", wave: "2....", data: ["0000"]},
      { name: "r_en", wave: "0.1.0"},
      { name: "r_data_no_change", wave: "xxx22", data: ["xxxx", "2222"]},
      { name: "r_data_read_first", wave: "xxx22", data: ["1111", "2222"]},
      { name: "r_data_write_first", wave: "xxx22", data: ["xxxx", "2222"]},
    ]
}
</script>

图中第一个周期向地址 0 写入了 1111，然后第三个周期同时读写地址 0 的数据，此时 NO_CHANGE 和 WRITE_FIRST 两种模式中，写入成功，读取失败；READ_FIRST 模式读取成功，并且读取的是写入之前的数据。第四个周期时，读写没有出现冲突，三种模式都可以读出写入的新数据。

这有些出乎我的意料：之前在很多地方用过 XPM，但是都没考虑过读写地址相同的情况，而且默认设置（NO_CHANGE）下，输出结果是不确定的。实际上这个行为在 PG058 Block Memory Generator 里面提到了：

- Synchronous Write-Read Collisions: A synchronous Write-Read collision might occur if a port attempts to Write a memory location and the other port reads the same location. While memory contents are not corrupted in Write-Read collisions, the validity of the output data depends on the Write port operating mode.
  - If the Write port is in READ_FIRST mode, the other port can reliably read the old memory contents.
  - If the Write port is in WRITE_FIRST or NO_CHANGE mode, data on the output of the Read port is invalid.
  - In the case of byte-writes, only updated bytes are invalid on the Read port output.

与上面观察到的结果基本吻合，另外这里提到了带 Mask 的情况：即使是 WRITE_FIRST 或者 NO_CHANGE，也可以读出没写入的那部分（即 WEA[i] = 0）旧的数据。

对此，Xilinx 的建议是：

    For Synchronous Clocking and during a collision, the Write mode of port A
    can be configured so that a Read operation on port B either produces data
    (acting like READ_FIRST), or produces undefined data (Xs). For this reason,
    it is always advised to use READ_FIRST when configured as a Simple Dual-port
    RAM. For asynchronous clocking, Xilinx recommends setting the Write mode of
    Port A to WRITE_FIRST for collision safety.

也就是说同步时钟用 READ_FIRST，异步时钟用 WRITE_FIRST。甚至 Vivado 还可以贴心地帮你设置：

    For 7 series devices, the selected operating mode is passed to the block RAM
    when the RAM_MODE is set to TDP. For the primitives with RAM_MODE set to
    SDP, the write mode is READ_FIRST for synchronous clocking and WRITE_FIRST
    for asynchronous clocking.

但是 XPM 似乎就没有这个设定了，而是由用户来传入。

而对于异步时钟，文档直接说不要让冲突发生：

    Using asynchronous clocks, when one port writes data to a memory location,
    the other port must not Read or Write that location for a specified amount
    of time.

这点似乎经常被我们忽略。

那么，如果在 Verilog 中实现一个语义上 WRITE_FIRST 的 RAM，会发生什么呢：

```verilog
`timescale 1ns/1ps
module mem_1r1w (
  input clk,
  input [5:0] R0_addr,
  input R0_en,
  output [63:0] R0_data,
  input [5:0] W0_addr,
  input W0_en,
  input [63:0] W0_data
);

  reg [5:0] reg_R0_addr;
  reg [63:0] mem [63:0];

  always @(posedge clk) begin
    if (W0_en) begin
      mem[W0_addr] <= W0_data;
    end
  end

  always @(posedge clk) begin
    if (R0_en) begin
      reg_R0_addr <= R0_addr;
    end
  end

  assign R0_data = mem[reg_R0_addr];

endmodule
```

奇怪的是，综合出来会使用 BRAM 实现，并且采用 READ_FIRST 作为 RAMB36E1 的 WRITE_MODE_A 和 WRITE_MODE_B。如果写成语义 READ_FIRST：

```verilog
`timescale 1ns/1ps
module mem_1r1w (
  input clk,
  input [5:0] R0_addr,
  input R0_en,
  output [63:0] R0_data,
  input [5:0] W0_addr,
  input W0_en,
  input [63:0] W0_data
);

  reg [63:0] reg_R0_data;
  reg [63:0] mem [63:0];

  always @(posedge clk) begin
    if (W0_en) begin
      mem[W0_addr] <= W0_data;
    end
  end

  always @(posedge clk) begin
    if (R0_en) begin
      reg_R0_data <= mem[R0_addr];
    end
  end

  assign R0_data = reg_R0_data;

endmodule
```

会发现生成的 RAMB36E1 原语的 WRITE_MODE 依然是 READ_FIRST。经过测试发现，如果综合的时候用两个时钟信号，就会用 WRITE_FIRST；如果用了一个，就会用 READ_FIRST，与语义无关。所以如果依赖 Vivado 的 infer RAM，得到的结果和预期可能不一致。

又额外测试了一下 yosys：`yosys mem_1r1w.v -p "synth_xilinx"`，结果发现 yosys 会忠实地按照语义为 WRITE_FIRST 生成 bypass 逻辑。虽然 yosys 可以做的更好：把识别出来的 READ_FIRST 或 WRITE_FIRST 传给 RAMB36E1，但 yosys 至少尊重了代码。

### 一读写

接下来测试单读写口的场景。单读写口和上面不同，它的冲突点在于，写入的时候，读取的数据如何变化。下面用同样的方法，测试三种模式下 xpm_memory_spram 的行为，得到如下波形：

<script type="WaveDrom">
{
  signal:
    [
      { name: "clk", wave: "p......"},
      { name: "rw_addr", wave: "2...2..", data: ["0000", "0001"]},
      { name: "rw_wdata", wave: "2..22..", data: ["1111", "2222", "3333"]},
      { name: "rw_en", wave: "101...."},
      { name: "rw_we", wave: "10.1..."},
      { name: "ram[0]", wave: "x2..2..", data: ["1111", "2222"]},
      { name: "ram[1]", wave: "2....2.", data: ["0000", "3333"]},
      { name: "rw_rdata_no_change", wave: "xxx2...", data: ["1111"]},
      { name: "rw_rdata_read_first", wave: "xxx2.22", data: ["1111", "0000", "3333"]},
      { name: "rw_rdata_write_first", wave: "x2..22.", data: ["1111", "2222", "3333"]},
    ]
}
</script>

这个结果就比较有意思了，三种模式得到了三种不同的结果。第一个周期依然是写入 1111 到地址 0，然后 WRITE_FIRST 模式的输出结果第二个周期跟着变，就好像在写的时候同时也在读，只不过读取的结果就是最后一次写入的结果。第三个周期读取地址 0 的数据，然后第四个周期写入 2222 到地址 0，此时三种情况的读取都得到了写入前的值（也就是 1111）。第五个周期 WRITE_FIRST 模式的输出跟着变成了 2222，和预期一致。同时第五个周期写入 3333 到地址 1，接着第六个周期的时候，READ_FIRST 出现了 0000，实际上是读取了地址 1 的旧数据，也就是写入前的数据，而 WRITE_FIRST 更新为了 3333，也就是新写入的数据；NO_CHANGE 则是保持了最后一次读取的结果。

简单总结一下上面的现象，就是：

- NO_CHANGE：顾名思义，写的时候 rdata 不变，只有在读的下一个周期才会变
- WRITE_FIRST：写的同时也在读，只不过读取的是写入的新数据
- READ_FIRST：写的同时也在读，只不过读取的是写入前的旧数据

关于这个行为，在 [RAM IP Core 中 Write First Read First 和 No Change 的区别](https://xilinx.eetrend.com/blog/2020/100055273.html) 处可以看到比较清晰的解释。

## SRAM IP

接下来在仿真中看看 SRAM IP 的行为是什么样子。SRAM IP 有一个引脚 COLLDISN，其语义为：

- 如果 COLLDISN 为 1，那么如果出现读写冲突，那么写入是被保证的，但是读取会失败
- 如果 COLLDISN 为 0，那么如果出现读写冲突，读写都会失败

仿真得到如下波形：

<script type="WaveDrom">
{
  signal:
    [
      { name: "clk", wave: "p......."},
      { name: "w_addr", wave: "2.......", data: ["0000"]},
      { name: "w_data", wave: "2x...2x.", data: ["1111", "2222"]},
      { name: "w_en", wave: "10...10."},
      { name: "r_addr", wave: "2.......", data: ["0000"]},
      { name: "r_en", wave: "0.10.1.0"},
      { name: "mem_colldisn_0[0]", wave: "x2....2.", data: ["1111", "xxxx"]},
      { name: "r_data_colldisn_0", wave: "xxx2..2.", data: ["1111", "xxxx"]},
      { name: "mem_colldisn_1[0]", wave: "x2....2.", data: ["1111", "2222"]},
      { name: "r_data_colldisn_1", wave: "xxx2..22", data: ["1111", "xxxx", "2222"]},
    ]
}
</script>

第一个周期没有读写冲突，所以成功写入，第三个周期也可以正确地都出来。第六个周期读写冲突，此时如果 COLLDISN 等于 0，那么读写都失败，下一个周期读取结果是 xxxx，并且之后继续读取依然是 xxxx，因为内存中的数据被破坏了；而如果 COLLDISN 等于 1，那么写入成功，内存中的值变为 2222，但读取失败，下一个周期读取结果是 xxxx，但是再下一个周期就可以正常读取，得到 2222。

这就与 Xilinx FPGA 不一样：这里如果 COLLDISN 等于 0，读写冲突的时候，可能写入会失效，内存中的值变为不确定的内容。所以为了保证正确性，要么在 SRAM IP 外部进行读写冲突检查，如果要冲突了，就关掉读口，然后从写口 bypass 数据到读口；要么在 SRAM IP 内部进行读写冲突检查（设置 COLLDISN 等于 1），然后不要使用冲突时读取的数据。

## Chisel

Chisel 中 RAM 对应的是 SyncReadMem，它可以指定 Read under Write behavior：

- `SyncReadMem()`: unspecified in FIRRTL, `WriteFirst` in behavior model
- `SyncReadMem(Undefined)`: unspecified in FIRRTL, `WriteFirst` in behavior model
- `SyncReadMem(ReadFirst)`: `old` in FIRRTL, `ReadFirst` in behavior model
- `SyncReadMem(WriteFirst)`: `new` in FIRRTL, `WriteFirst` in behavior model

也就是说，在行为级模型中，只有 WriteFirst 和 ReadFirst 两种行为，并且默认是 `WriteFirst`。但是，前面也提到，实际上 XPM 只支持 `Undefined`（生成 `x`）和 `ReadFirst`（READ_FIRST）两种；上面的 SRAM IP 更是只支持 `Undefined`（生成 `x`）。

这就导致写 Chisel 代码的时候，如果不小心用了 1R1W，并且代码依赖了 Read Under Write 在行为级模型下的行为，那么在使用 XPM 或者 SRAM IP 进行替换的时候，就需要额外的逻辑来处理这个不同。例如，如果要模拟 `WriteFirst`，就比较地址，然后进行 bypass；但是 `ReadFirst` 就没办法模拟了。最好的解决方法还是，不要出现冲突，即使要冲突，也要在上层进行处理。