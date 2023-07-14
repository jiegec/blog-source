---
layout: post
date: 2022-03-30
tags: [hdl,yosys,sv2v,fpnew,fpu]
category: hardware
title: 用 sv2v+yosys 把 fpnew 转为 verilog 网表
---

## 背景

FPnew 是一个比较好用的浮点计算单元，但它是 SystemVerilog 编写的，并且用了很多高级特性，虽然闭源软件是支持的，但是开源拖拉机经常会遇到这样那样的问题。所以一直想用 sv2v 把它翻译成 Verilog，但此时的 Verilog 还有很多复杂的结构，再用 yosys 转换为一个通用可综合的网表。

## 步骤

经过一系列踩坑，一个很重要的点是要用最新的 sv2v(v0.0.9-24-gf868f06) 和 yosys(0.15+70)。Debian 打包的 yosys 版本比较老，不能满足需求。

首先，用 verilator 进行预处理，把一堆 sv 文件合成一个：

```shell
$ cat a.sv b.sv c.sv > test.sv
$ verilator -E test.sv > merged.sv
$ sed -i '/^`line/d' merged.sv
```

注意这里用 sed 去掉了无用的行号信息。然后，用 sv2v 进行转换：

```shell
$ sv2v merged.sv > merge.v
$ sed -i '/\$$fatal/d' merge.v
```

这里又用 sed 把不支持的 $fatal 去掉。最后，用 yosys 进行处理：

```shell
$ yosys -p 'read_verilog -defer merge.v' -p 'hierarchy -p fpnew_top' -p 'proc' -p 'opt' -p 'write_verilog -noattr output.v'
```

注意这里要用 `read_verilog -defer`，否则 yosys 会遇到 TAG_WIDTH=0 默认参数就直接例化，然后就出现 `[0:-1]` 这样的下标。`read_verilog` 的文档告诉了我们可以分两步做：

    -defer
        only read the abstract syntax tree and defer actual compilation
        to a later 'hierarchy' command. Useful in cases where the default
        parameters of modules yield invalid or not synthesizable code.

这样就得到了简化后的 verilog 代码：

```verilog
module \$paramod$011e4d7ee08c34f246a38322dc9967d23ecc8081\fpnew_opgroup_block_A94B6_B7406 (clk_i, rst_ni, operands_i, is_boxed_i, rnd_mode_i, op_i, op_mod_i, src_fmt_i, dst_fmt_i, int_fmt_i, vectorial_op_i, tag_i, in_valid_i, in_ready_o, flush_i, result_o, status_o, extension_bit_o, tag_o, out_valid_o, out_ready_i
, busy_o);
  wire _0_;
  wire _1_;
  wire [71:0] arbiter_output;
  output busy_o;
  wire busy_o;
  input clk_i;
  wire clk_i;
  input [2:0] dst_fmt_i;
  wire [2:0] dst_fmt_i;
  output extension_bit_o;
  wire extension_bit_o;
  input flush_i;
  // ...
endmodule
```

这样虽然比较丑陋，但是解决了 SystemVerilog 的问题。诚然，这样也失去了修改参数的能力，因为参数已经在 yosys 综合途中确定下来了。