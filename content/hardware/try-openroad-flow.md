---
layout: post
date: 2022-03-12 22:52:00 +0800
tags: [openroad,synthesis,yosys]
category: hardware
title: OpenROAD Flow 初尝试
---

## 背景

最近在尝试接触一些芯片前后端的知识。正好有现成的开源工具链 OpenROAD 来做这个事情，借此机会来学习一下整个流程。

## 尝试过程

首先 clone 仓库 OpenROAD-flow-scripts，然后运行：`./build_openroad.sh`，脚本会克隆一些仓库，自动进行编译。

编译中会找不到一些库，比如可能需要安装这些依赖：`liblemon-dev libeigen3-dev libreadline-dev swig`，此外运行的时候还需要 `klayout` 依赖。

如果遇到解决 cmake 找不到 LEMON 的问题，这是一个 [BUG](https://lemon.cs.elte.hu/trac/lemon/ticket/628)，可以运行下面的命令解决：

```shell
cd /usr/lib/x86_64-linux-gnu/cmake/lemon
cp lemonConfig.cmake LEMONConfig.cmake
```

编译后整个目录大概有 4.8G，输出的二进制目录是 133M。

如果要跑一下样例里的 nangate45 工艺的 gcd 例子，运行：

```
cd flow
make DESIGN_CONFIG=./designs/nangate45/gcd/config.mk
```

## 分析 GCD 测例

这个测例的代码提供了这样一个接口：

```verilog
module gcd
(
  input  wire clk,
  input  wire [  31:0] req_msg,
  output wire req_rdy,
  input  wire req_val,
  input  wire reset,
  output wire [  15:0] resp_msg,
  input  wire resp_rdy,
  output wire resp_val
);
endmodule
```

从名字可以推断出，外部通过 req 发送请求到 GCD 模块，然后模块计算出 GCD 后再返回结果。

根据日志可以看到，从 verilog 到最终的 gds 文件，经过了这些步骤：

1. 第一步用 yosys 综合（1_1_yosys），把 verilog 代码转化为网表，网表中的单元就是形如 `NAND2_X1` `DFF_X1` 等这样由工艺库定义的一些单元。
2. 第二步进行 floorplan（2_1_floorplan），规划出芯片的大小，逻辑放在哪个位置，输入输出引脚放在什么位置（2_2_floorplan_io），还要考虑 SRAM 等宏或者 IP（2_4_mplace），电源网络 PDN（2_6_floorplan_pdn）
3. 第三步是 Placement，就是把前面得到的一些 cell 放到芯片上的 (x,y) 坐标上
4. 第四步是 Clock Tree Synthesis（4_1_cts），简称 CTS，生成时钟树
5. 第五步是进行路由连线，OpenROAD 有两个路由：FastRoute（5_1_fastroute） 和 TritonRoute（5_2_TritonRoute）
6. 第六步输出结果到 gds 文件（6_1_merge）。

这些步骤可以在仓库的 `flow/Makefile` 里面看得比较清晰，英文版摘抄如下：

1. SYNTHESIS
    1. Run Synthesis using yosys
2. FLOORPLAN
    1. Translate verilog to def
    2. IO Placement (random)
    3. Timing Driven Mixed Size Placement (tdms)
    4. Macro Placement
    5. Tapcell and Welltie insertion
    6. PDN generation
3. PLACE
    1. Global placement without placed IOs, timing-driven, and routability-driven
    2. IO placement (non-random)
    3. Global placement with placed IOs, timing-driven, and routability-driven
    4. Resizing & Buffering
    5. Detail placement
4. CTS(Clock Tree Synthesis)
    1. Run TritonCTS
    2. Filler cell insertion
5. ROUTING
    1. Run global route (FastRoute)
    2. Run detailed route (TritonRoute)

最后生成的 gds，用 KLayout 打开，可以看到这个样子：

![](/gcd_gds.png)

日志里可以看到，预测的总功耗是 1.71 mW，面积占用是 703 um^2。

还跑了一下其他样例设计的 gds，比如 ibex：

![](/ibex_gds.png)

日志里可以看到，预测的总功耗是 10.1 mW，面积占用是 32176 um^2。

还有 tiny rocket：

![](/tiny_rocket_gds.png)

日志里可以看到，预测的总功耗是 36.8 mW，面积占用是 52786 um^2。

## 工艺库常见术语：

- slvt/lvt/rvt/hvt: super-low/low/regular/high V threshold 前者速度快：阈值电压低，同时漏电流大
- ss/tt/ff: slow-slow/typical-typical/fast-fast 后者速度快：电压高，温度低，比如 SS（0.99V 125C）TT（1.10V 25C） FF（1.21V -40C）

## 参考文档

- [GETTING STARTED WITH OPENROAD APP – PART 1](https://theopenroadproject.org/2019/12/11/getting-started-with-openroad-app-part-1/)