---
layout: post
date: 2021-12-13 20:06:00 +0800
tags: [dram,ddr,fpga,7series,xilinx,kintex7,mig]
category: hardware
title: DRAM 在 Kintex 7 FPGA 上内部 Vref 的性能问题
---

## 背景

最近我们设计的 Kintex 7 FPGA 开发板在测试 DDR SDRAM 的时候遇到了一个问题，因为采用了 Internel VREF，MIG 在配置的时候限制了频率只能是 400 MHz，对应 800 MT/s，这样无法达到 DDR 的最好性能。

## 原理

首先，VREF 在 DDR 中是用来区分低电平和高电平的。在 JESD79-4B 标准中，可以看到，对于直流信号，电压不小于 VREF+0.075V 时表示高电平，而电压不高于 VREF-0.075V 时表示低电平。VREF 本身应该介于 VDD 的 0.49 倍到 0.51 倍之间。

在连接 FPGA 的时候，有两种选择：

- Internal VREF: 从 FPGA 输出 VREF 信号到 DRAM
- External VREF：接入 FPGA 以外的 VREF

对于 7 Series 的 FPGA，Xilinx 要求如下：

	For DDR3 SDRAM interfaces running at or below 800 Mb/s (400 MHz),
	users have the option of selecting Internal VREF to save two I/O
	pins or using external VREF. VREF is required for banks containing
	DDR3 interface input pins (DQ/DQS).

进一步，Xilinx 在 UltraScale 文档下解释了背后的原因：

	The UltraScale internal VREF circuit includes enhancements compared
	to the 7 Series internal VREF circuit. Whereas 7 Series MIG had datarate
	limitations on internal VREF usage (see (Xilinx Answer 42036)), internal
	VREF is recommended in UltraScale. The VREF for 7 Series had coarse steps
	of VREF value that were based on VCCAUX. This saved pins but limited the
	performance because VCCAUX did not track with VCCO as voltage went up and
	down. Not being able to track with VCCO enforced the performance
	limitations of internal VREF in MIG 7 Series. UltraScale includes several
	changes to internal VREF including a much finer resolution of VREF for DDR4
	read VREF training. Additionally, internal VREF is based on the VCCO supply
	enabling it to track with VCCO. Internal VREF is not subject to PCB and
	Package inductance and capacitance. These changes in design now give internal
	VREF the highest performance.

用中文简单来说：

1. 7 Series FPGA 中，Internal VREF 可以节省引脚，代价是 VREF 不会随着 VCCO 变化而变化（而是随着 VCCAUX 变化而变化），当 DRAM 频率提高的时候，可能无法满足 VREF 约等于 VDD 一半的要求
2. UltraScale FPGA 中，Internal VREF 是随着 VCCO 变化而变化的，并且会比 External VREF 性能更好；因此 UltraScale FPGA 的 DDR4 只支持 Internal VREF。

以 MA703FA-35T 开发板为例，它使用的 FPGA 是 Artix7 35T，内存是 DDR3，采用的是 External VREF。它采用了 [TPS51200 Sink and Source DDR Termination Regulator](https://www.ti.com/lit/ds/symlink/tps51200.pdf) 芯片，将芯片的 REFOUT 芯片接到 DRAM 的 VREFDQ 和 VREFCA 引脚上。

## 参考文档

- [MIG 7 Series - Internal/External VREF Guidelines](https://support.xilinx.com/s/article/42036?language=en_US)
- [UltraScale/UltraScale+ Memory IP - Can either external or internal VREF be used?](https://support.xilinx.com/s/article/64410?language=en_US)
