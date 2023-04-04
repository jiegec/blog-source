---
layout: post
date: 2023-04-04 20:33:00 +0800
tags: [chisel,verilog,hdl,firtool,circt]
category: hardware
title: firtool 尝试
---

## 背景

Chisel 3.6 很快就要发布了（目前最新版本是 3.6.0-RC2），这个大版本的主要更新内容就是引入了 CIRCT 的 firtool 作为 FIRRTL 到 Verilog 的转换流程：

    The primary change in Chisel v3.6.0 is the transition from the Scala FIRRTL
    Compiler to the new MLIR FIRRTL Compiler. This will have a minimal impact on
    typical Chisel user APIs but a large impact on custom compiler flows. For
    more information, please see the ROADMAP.

因此提前测试一下 firtool，看看其和 Scala FIRRTL Compiler 有哪些区别，是否有更好的输出。

## 使用 firtool

使用 firtool 有两种方法：

1. 使用 chisel3 3.6 的 `circt.stage.ChiselStage` 对象：

```scala
circt.stage.ChiselStage
  .emitSystemVerilogFile(new Top)
```

代码中会生成 Chisel 模块对应的 FIRRTL 文件，然后喂给 firtool。也可以通过 `circt.stage.ChiselMain` 来运行：

```shell
$ sbt "runMain circt.stage.ChiselMain --help"
[info] running circt.stage.ChiselMain --help
Usage: circt [options] [<arg>...]

Shell Options
  <arg>...                 optional unbounded args
  -td, --target-dir <directory>
                           Work directory (default: '.')
  -faf, --annotation-file <file>
                           An input annotation file
  -foaf, --output-annotation-file <file>
                           An output annotation file
  --show-registrations     print discovered registered libraries and transforms
  --help                   prints this usage text
Logging Options
  -ll, --log-level {error|warn|info|debug|trace}
                           Set global logging verbosity (default: None
  -cll, --class-log-level <FullClassName:{error|warn|info|debug|trace}>...
                           Set per-class logging verbosity
  --log-file <file>        Log to a file instead of STDOUT
  -lcn, --log-class-names  Show class names and log level in logging output
CIRCT (MLIR FIRRTL Compiler) options
  --target {chirrtl|firrtl|hw|verilog|systemverilog}
                           The CIRCT
  --preserve-aggregate <value>
                           Do not lower aggregate types to ground types
  --module <package>.<module>
                           The name of a Chisel module to elaborate (module must be in the classpath)
  --full-stacktrace        Show full stack trace when an exception is thrown
  --throw-on-first-error   Throw an exception on the first error instead of continuing
  --warnings-as-errors     Treat warnings as errors
  --source-root <file>     Root directory for source files, used for enhanced error reporting
  --split-verilog          Indicates that "firtool" should emit one-file-per-module and write separate outputs to separate files
FIRRTL Transform Options
  --no-dce                 Disable dead code elimination
  --no-check-comb-loops    Disable combinational loop checking
  -fil, --inline <circuit>[.<module>[.<instance>]][,...]
                           Inline selected modules
  -clks, --list-clocks -c:<circuit>:-m:<module>:-o:<filename>
                           List which signal drives each clock of every descendent of specified modules
  --no-asa                 Disable assert submodule assumptions
  --no-constant-propagation
                           Disable constant propagation elimination
AspectLibrary
  --with-aspect <package>.<aspect>
                           The name/class of an aspect to compile with (must be a class/object without arguments!)
MemLib Options
  -firw, --infer-rw        Enable read/write port inference for memories
  -frsq, --repl-seq-mem -c:<circuit>:-i:<file>:-o:<file>
                           Blackbox and emit a configuration file for each sequential memory
  -gmv, --gen-mem-verilog <blackbox|full>
                           Blackbox and emit a Verilog behavior model for each sequential memory
```

2. 在 Scala 中生成 FIRRTL 文件，然后用 firtool 命令转换 `.fir` 为 `.sv`。由于 Rocket Chip 还没有迁移，所以需要通过 firtool 来转换。

由于目前 chisel3 并没有打包 firtool，目前需要自己装 firtool，例如通过 nix 或下载 GitHub 上的 Release 文件。本文采用的是 firtool 1.34.0。

## 对比

把同一份源码，通过两种方式来生成 Verilog 然后进行观察，下面是一些生成的代码的区别。

### 状态机

首先是一个状态机的例子（取自 chisel3 的 DetectTwoOnes 样例）：

```scala
is(State.sTwo1s) {
  when(!io.in) {
    state := State.sNone
  }
}
```

Scala FIRRTL:

```verilog
  wire [1:0] _GEN_2 = ~io_in ? 2'h0 : state; // @[src/main/scala/DetectTwoOnes.scala 33:20 34:15 15:22]
  // ...
    end else if (2'h2 == state) begin // @[src/main/scala/DetectTwoOnes.scala 19:17]
      state <= _GEN_2;
    end
```

CIRCT firtool:

```verilog
    else if (state == 2'h2 & ~io_in)	// src/main/scala/DetectTwoOnes.scala:15:22, :17:20, :19:17, :33:{12,20}, :34:15
      state <= 2'h0;	// src/main/scala/DetectTwoOnes.scala:15:22, :29:15
```

这个例子里，Scala FIRRTL Compiler 多生成了一个 `_GEN_2`，需要把前后一起看才知道是什么意思，而 CIRCT 生成的与源码比较接近，可读性较好。

### SyncReadMem

接下来看 SyncReadMem。在 Scala FIRRTL Compiler 中，默认是直接在模块中嵌入代码：

```scala
  reg [31:0] mem [0:31]; // @[src/main/scala/Memory.scala 10:24]
  wire  mem_rdata_MPORT_en; // @[src/main/scala/Memory.scala 10:24]
  wire [4:0] mem_rdata_MPORT_addr; // @[src/main/scala/Memory.scala 10:24]
  wire [31:0] mem_rdata_MPORT_data; // @[src/main/scala/Memory.scala 10:24]
  wire [31:0] mem_MPORT_data; // @[src/main/scala/Memory.scala 10:24]
  wire [4:0] mem_MPORT_addr; // @[src/main/scala/Memory.scala 10:24]
  wire  mem_MPORT_mask; // @[src/main/scala/Memory.scala 10:24]
  wire  mem_MPORT_en; // @[src/main/scala/Memory.scala 10:24]
  reg  mem_rdata_MPORT_en_pipe_0;
  reg [4:0] mem_rdata_MPORT_addr_pipe_0;
  assign mem_rdata_MPORT_en = mem_rdata_MPORT_en_pipe_0;
  assign mem_rdata_MPORT_addr = mem_rdata_MPORT_addr_pipe_0;
  assign mem_rdata_MPORT_data = mem[mem_rdata_MPORT_addr]; // @[src/main/scala/Memory.scala 10:24]
  assign mem_MPORT_data = wdata;
  assign mem_MPORT_addr = waddr;
  assign mem_MPORT_mask = 1'h1;
  assign mem_MPORT_en = 1'h1;
  assign rdata = mem_rdata_MPORT_data; // @[src/main/scala/Memory.scala 11:9]
  always @(posedge clock) begin
    if (mem_MPORT_en & mem_MPORT_mask) begin
      mem[mem_MPORT_addr] <= mem_MPORT_data; // @[src/main/scala/Memory.scala 10:24]
    end
    mem_rdata_MPORT_en_pipe_0 <= 1'h1;
    if (1'h1) begin
      mem_rdata_MPORT_addr_pipe_0 <= raddr;
    end
  end
```

当然了，它有 repl-seq-mem 的选项，可以生成 BlackBox 方便替换为实际的 SRAM IP：

```shell
$ sbt "runMain firrtl.stage.FirrtlMain -i Memory.fir --repl-seq-mem -c:Memory:-o:Memory.conf"
$ cat Memory.v
module mem(
  input  [4:0]  R0_addr,
  input         R0_clk,
  output [31:0] R0_data,
  input  [4:0]  W0_addr,
  input         W0_clk,
  input  [31:0] W0_data
);
  wire [4:0] mem_ext_R0_addr;
  wire  mem_ext_R0_en;
  wire  mem_ext_R0_clk;
  wire [31:0] mem_ext_R0_data;
  wire [4:0] mem_ext_W0_addr;
  wire  mem_ext_W0_en;
  wire  mem_ext_W0_clk;
  wire [31:0] mem_ext_W0_data;
  mem_ext mem_ext (
    .R0_addr(mem_ext_R0_addr),
    .R0_en(mem_ext_R0_en),
    .R0_clk(mem_ext_R0_clk),
    .R0_data(mem_ext_R0_data),
    .W0_addr(mem_ext_W0_addr),
    .W0_en(mem_ext_W0_en),
    .W0_clk(mem_ext_W0_clk),
    .W0_data(mem_ext_W0_data)
  );
  assign mem_ext_R0_clk = R0_clk;
  assign mem_ext_R0_en = 1'h1;
  assign mem_ext_R0_addr = R0_addr;
  assign R0_data = mem_ext_R0_data;
  assign mem_ext_W0_clk = W0_clk;
  assign mem_ext_W0_en = 1'h1;
  assign mem_ext_W0_addr = W0_addr;
  assign mem_ext_W0_data = W0_data;
endmodule
$ cat Memory.conf
name mem_ext depth 32 width 32 ports write,read  
```

下游工具读取 Memory.conf 去生成对应的 mem_ext 模块。这里只考虑了 Read Latency 为 1 的情况，如果是 Mem，就不会生成 BlackBox，毕竟参数名字是 sequential memory。

CIRCT firtool 也有类似的表现，只不过默认情况下就会用一个单独的模块：

```verilog
module Memory(	// <stdin>:3:10
  input         clock,	// <stdin>:4:11
                reset,	// <stdin>:5:11
  input  [4:0]  raddr,	// src/main/scala/Memory.scala:4:17
                waddr,	// src/main/scala/Memory.scala:7:17
  input  [31:0] wdata,	// src/main/scala/Memory.scala:8:17
  output [31:0] rdata	// src/main/scala/Memory.scala:5:17
);

  mem_combMem mem_ext (	// src/main/scala/Memory.scala:10:24
    .R0_addr (raddr),
    .R0_en   (1'h1),	// <stdin>:3:10
    .R0_clk  (clock),
    .W0_addr (waddr),
    .W0_en   (1'h1),	// <stdin>:3:10
    .W0_clk  (clock),
    .W0_data (wdata),
    .R0_data (rdata)
  );
endmodule

module mem_combMem(	// src/main/scala/Memory.scala:10:24
  input  [4:0]  R0_addr,
  input         R0_en,
                R0_clk,
  input  [4:0]  W0_addr,
  input         W0_en,
                W0_clk,
  input  [31:0] W0_data,
  output [31:0] R0_data
);

  reg [31:0] Memory[0:31];	// src/main/scala/Memory.scala:10:24
  reg        _GEN;	// src/main/scala/Memory.scala:10:24
  reg [4:0]  _GEN_0;	// src/main/scala/Memory.scala:10:24
  always @(posedge R0_clk) begin	// src/main/scala/Memory.scala:10:24
    _GEN <= R0_en;	// src/main/scala/Memory.scala:10:24
    _GEN_0 <= R0_addr;	// src/main/scala/Memory.scala:10:24
  end // always @(posedge)
  always @(posedge W0_clk) begin	// src/main/scala/Memory.scala:10:24
    if (W0_en)	// src/main/scala/Memory.scala:10:24
      Memory[W0_addr] <= W0_data;	// src/main/scala/Memory.scala:10:24
  end // always @(posedge)
  assign R0_data = _GEN ? Memory[_GEN_0] : 32'bx;	// src/main/scala/Memory.scala:10:24
endmodule
```

firtool 也支持 `-repl-seq-mem` 参数，用法和输出与 Scala FIRRTL Compiler 类似。

### 复杂组合逻辑

再来看 Hardfloat 的例子。代码：

```scala
val exp = in(expWidth + sigWidth - 1, sigWidth - 1)
val isZero    = exp(expWidth, expWidth - 2) === 0.U
val isSpecial = exp(expWidth, expWidth - 1) === 3.U

val out = Wire(new RawFloat(expWidth, sigWidth))
out.isNaN  := isSpecial &&   exp(expWidth - 2)
```

Scala FIRRTL Compiler:

```scala
wire [8:0] rawA_exp = io_a[31:23]; // @[submodules/berkeley-hardfloat/src/main/scala/rawFloatFromRecFN.scala 51:21]
wire  rawA_isZero = rawA_exp[8:6] == 3'h0; // @[submodules/berkeley-hardfloat/src/main/scala/rawFloatFromRecFN.scala 52:53]
wire  rawA_isSpecial = rawA_exp[8:7] == 2'h3; // @[submodules/berkeley-hardfloat/src/main/scala/rawFloatFromRecFN.scala 53:53]
wire  rawA__isNaN = rawA_isSpecial & rawA_exp[6]; // @[submodules/berkeley-hardfloat/src/main/scala/rawFloatFromRecFN.scala 56:33]
```

基本是忠实的翻译。

CIRCT Firtool:

```verilog
wire        rawA_isNaN = (&(io_a[31:30])) & io_a[29];	// submodules/berkeley-hardfloat/src/main/scala/rawFloatFromRecFN.scala:51:21, :53:{28,53}, :56:{33,41}
```

可以看到，这里对代码进行了变换，把 `=== 3.U` 变成了 AND，不再忠实原来的代码，而是采取了更加间接的表达方式。

再看一个类似的例子，源码：

```scala
    val signProd = rawA.sign ^ rawB.sign ^ io.op(1)
```

Scala FIRRTL Compiler:

```verilog
  wire  rawA__sign = io_a[32]; // @[submodules/berkeley-hardfloat/src/main/scala/rawFloatFromRecFN.scala 59:25]
  wire  rawB__sign = io_b[32]; // @[submodules/berkeley-hardfloat/src/main/scala/rawFloatFromRecFN.scala 59:25]
  wire  signProd = rawA__sign ^ rawB__sign ^ io_op[1]; // @[submodules/berkeley-hardfloat/src/main/scala/MulAddRecFN.scala 96:42]
```

CIRCT firtool:

```verilog
  wire        signProd = io_a[32] ^ io_b[32] ^ io_op[1];	// submodules/berkeley-hardfloat/src/main/scala/MulAddRecFN.scala:96:{42,49}, submodules/berkeley-hardfloat/src/main/scala/rawFloatFromRecFN.scala:59:25
```

可以看到，CIRCT firtool 比较倾向于内联一些简单的连线。当然了，这个不是绝对的，通过修改命令行参数，可能得到不同的结果。

### Rocket Chip

在 rocket-chip-vcu128 项目中测试了一下，迁移到 CIRCT firtool 比较简单，只需要把 FirrtlMain 的调用改成直接运行 firtool。但是，在综合的时候，发现 Vivado 无法推断出一个 SyncReadMem，导致 LUT 和 Register 占用特别多。解决思路有两个：

1. 利用上面所说的 `--repl-seq-mem` 生成 BlackBox，然后生成 XPM Macro 接起来
2. 添加 `--lower-memories` 参数，简化 SRAM，然后 Vivado 就可以识别出来了。

### 速度

运行大项目的时候，Scala FIRRTL Compiler 的速度明显比 CIRCT Firtool 慢，体验还是不错的。
