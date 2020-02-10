---
layout: post
date: 2020-02-10 15:08:00 +0800
tags: [fpga,riscv,rocketchip,bscan,jtag,openocd]
category: hardware
title: 通过 BSCAN JTAG 对 Rocket Chip 进行调试
---

# 前言

在上一个 [post](https://jiege.ch/hardware/2020/02/09/rocket-chip-bscan-analysis/) 里研究了原理，今天也是成功在 Artix 7 上实现了调试。效果如下：

OpenOCD 输出：

```
Info : JTAG tap: riscv.cpu tap/device found: 0x0362d093 (mfg: 0x049 (Xilinx), part: 0x362d, ver: 0x0)
Info : datacount=1 progbufsize=16
Info : Disabling abstract command reads from CSRs.
Info : Examined RISC-V core; found 1 harts
Info :  hart 0: XLEN=32, misa=0x40801105
Info : Listening on port 3333 for gdb connections
```

GDB 输出：

```
Remote debugging using localhost:3333
0x0001018c in getc () at bootloader.c:36
36        while (!(*UART_LSR & 0x1))
(gdb) 
```

# 过程

代码基本借鉴了 [sequencer/rocket-playground](https://github.com/sequencer/rocket-playground/tree/7fa3c51113be607add2034f3abe0ae973caac04a) 和 [KireinaHoro/rocket-zcu102](https://github.com/KireinaHoro/rocket-zcu102/tree/ab9112c951eeeb64482716394d926777862d9e86) 而来，代码方面主要是添加了 [BscanJTAG.scala](https://github.com/jiegec/rocket2thinpad/blob/ad1e86620c54bc0be29d08394d04f70031718b6d/src/main/scala/BscanJTAG.scala#L1)，然后在 Top 模块下把它连接到内部的 JTAG 中：

```scala
val boardJTAG = Module(new BscanJTAG)
val jtagBundle = target.debug.head.systemjtag.head

// set JTAG parameters
jtagBundle.reset := reset
jtagBundle.mfr_id := 0x233.U(11.W)
jtagBundle.part_number := 0.U(16.W)
jtagBundle.version := 0.U(4.W)
// connect to BSCAN
jtagBundle.jtag.TCK := boardJTAG.tck
jtagBundle.jtag.TMS := boardJTAG.tms
jtagBundle.jtag.TDI := boardJTAG.tdi
boardJTAG.tdo := jtagBundle.jtag.TDO.data
boardJTAG.tdoEnable := jtagBundle.jtag.TDO.driven
```

代码方面就足够了。然后，需要一个 riscv-openocd 和 riscv-gdb，分别从上游 repo 编译得来。然后采用以下的 openocd.cfg：

```
adapter_khz 20000
interface ftdi
ftdi_vid_pid 0x0403 0x6014
ftdi_layout_init 0x00e8 0x60eb
ftdi_tdo_sample_edge falling
reset_config none

set _CHIPNAME riscv
jtag newtap $_CHIPNAME cpu -irlen 6

set _TARGETNAME $_CHIPNAME.cpu

target create $_TARGETNAME.0 riscv -chain-position $_TARGETNAME
$_TARGETNAME.0 configure -work-area-phys 0x80000000 -work-area-size 10000 -work-area-backup 1
riscv use_bscan_tunnel 5
```

然后就可以用 GDB 调试了。