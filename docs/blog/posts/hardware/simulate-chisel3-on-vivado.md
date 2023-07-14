---
layout: post
date: 2020-02-10
tags: [vivado,chisel,verilog]
category: hardware
title: 在 Vivado 中对 chisel3 产生的 verilog 代码仿真
---

默认情况下，chisel3 生成的 verilog 代码在 Vivado 中仿真会出现很多信号大面积变成 X。解决方法在一个不起眼的 Wiki 页面：[Randomization flags](https://github.com/freechipsproject/chisel3/wiki/Randomization-flags)：

```verilog
`define RANDOMIZE_REG_INIT
`define RANDOMIZE_MEM_INIT
`define RANDOMIZE_GARBAGE_ASSIGN
`define RANDOMIZE_INVALID_ASSIGN
```

在生成的 verilog 前面加上这四句，就可以正常仿真了。