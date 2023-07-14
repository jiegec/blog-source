---
layout: post
date: 2022-03-09
tags: [fpga,riscv,rocketchip,jtag,openocd,vcu128,ft4232]
category: hardware
title: 通过 JTAG 对 VCU128 上的 Rocket Chip 进行调试
---

## 前言

两年前，我尝试过用 BSCAN JTAG 来配置 Rocket Chip 的调试，但是这个方法不是很好用，具体来说，如果有独立的一组 JTAG 信号，配置起来会更方便，而且不用和 Vivado 去抢，OpenOCD 可以和 Vivado hw_server 同时运行和工作。但是，苦于 VCU128 上没有 PMOD 接口，之前一直没考虑过在 VCU128 上配置独立的 JTAG。然后最近研究了一下，终于解决了这个问题。

## 寻找 JTAG 接口

前几天在研究别的问题的时候，看到 VCU128 文档中的这段话：

    The FT4232HL U8 multi-function USB-UART on the VCU128 board provides three level-shifted
    UART connections through the single micro-AB USB connector J2.
    • Channel A is configured in JTAG mode to support the JTAG chain
    • Channel B implements 4-wire UART0 (level-shifted) FPGA U1 bank 67 connections
    • Channel C implements 4-wire UART1 (level-shifted) FPGA U1 bank 67 connections
    • Channel D implements 2-wire (level-shifted) SYSCTLR U42 bank 501 connections

其中 Channel A 是到 FPGA 本身的 JTAG 接口，是给 Vivado 用的，如果是通过 BSCAN 的方式，也是在这个 Channel 上，但是需要经过 FPGA 自己的 TAP 再隧道到 BSCAN 上，比较麻烦。Channel B 和 C 是串口，Channel D 是连接 VCU128 上的 System Controller 的。之前的时候，都是直接用 Channel B 做串口，然后突发奇想：注意到这里是 4-wire UART，说明连接到 FPGA 是四条线，那是不是也可以拿来当 JTAG 用？

查询了一下 FT4232H 的文档，发现它的 Channel A 和 Channel B 是支持 MPSSE 模式的，在 MPSSE 模式下，可以当成 JTAG 使用：

| Signal | Channel A | Channel B |
| ------ | --------- | --------- |
| TCK    | 12        | 22        |
| TDI    | 13        | 23        |
| TDO    | 14        | 24        |
| TMS    | 15        | 25        |

对照 VCU128 的 Schematic 看，虽然引脚的编号不大一样，可以发现，Channel A 和 B 分别对应了 ADBUS0-4 和 BDBUS 0-4，对应到 schematic 上的名字是：

- ADBUS0 - FT4232_TCK
- ADBUS1 - FT4232_TDI
- ADBUS2 - FMCP_HSPC_TDO
- ADBUS3 - FT4232_TMS

这一组是直接连到 FPGA 上专用的 JTAG 引脚，其中 TDO 是连接了额外的逻辑，可以把 FMC 接口上的 JTAG 连接成 daisy chain。

- ADBUS0 - FTDI_UART0_TXD_LS - UART0_RXD - BP26 -> TCK
- ADBUS1 - FTDI_UART0_RXD_LS - UART0_TXD - BN26 -> TDI
- ADBUS2 - FTDI_UART0_RTS_B_LS - UART0_RTS_B - BP22 -> TDO
- ADBUS3 - FTDI_UART0_CTS_B_LS - UART0_CTS_B - BP23 -> TMS

这里的 RXD/TXD 名字交换也是很容易看错，要小心，只要记住 FT4232H 要求的顺序一定是 TCK-TDI-TDO-TMS 即可。对应到 vivado 内的 xdc 就是这么写：

```tcl
set_property -dict {PACKAGE_PIN BP26 IOSTANDARD LVCMOS18} [get_ports jtag_TCK]
set_property -dict {PACKAGE_PIN BN26 IOSTANDARD LVCMOS18} [get_ports jtag_TDI]
set_property -dict {PACKAGE_PIN BP22 IOSTANDARD LVCMOS18} [get_ports jtag_TDO]
set_property -dict {PACKAGE_PIN BP23 IOSTANDARD LVCMOS18} [get_ports jtag_TMS]
```

接下来，我们要把 Rocket Chip 的 JTAG 信号接出来。

## 配置 Rocket Chip 的 JTAG

配置 Rocket Chip 的 JTAG，大概需要如下几步：

1. 给 Config 加上 WithJtagDTM，以 JTAG 作为 DTM 模块
2. 给 Subsystem 加上 HasPeripheryDebug
3. 给 SubsystemModuleImp 加上 HasPeripheryDebugModuleImp
4. 把 JTAG 信号连到自己的顶层模块上

最后一步的相关代码，首先，按照 spec 要求，把 DM 输出的 ndreset 信号连到整个 Rocket 的 reset 上：

```scala
// ndreset can reset all harts
val childReset = reset.asBool | target.debug.map(_.ndreset).getOrElse(false.B)
target.reset := childReset
```

接着，把 JTAG 的信号连到顶层：

```scala
val systemJtag = target.debug.get.systemjtag.get
systemJtag.jtag.TCK := io.jtag.TCK
systemJtag.jtag.TMS := io.jtag.TMS
systemJtag.jtag.TDI := io.jtag.TDI
io.jtag.TDO := systemJtag.jtag.TDO
```

除了 JTAG 信号以外，还需要配置 IDCODE 相关的变量：

```scala
systemJtag.mfr_id := p(JtagDTMKey).idcodeManufId.U(11.W)
systemJtag.part_number := p(JtagDTMKey).idcodePartNum.U(16.W)
systemJtag.version := p(JtagDTMKey).idcodeVersion.U(4.W)
```

最后这一部分比较关键：首先，JTAG 部分的 reset 是独立于其余部分的，这里简单期间就连到了外部的 reset，其实可以改成 FPGA program 的时候进行 reset，然后等时钟来了就释放，实现方法可以参考文末的链接。resetctrl 是给 DM 知道哪些核心被 reset 了，最后是调用 rocket chip 自带的函数。这里踩的一个坑是，传给 systemJtag.reset 一定得是异步的，因为这个时钟域的时钟都是 jtag 的 TCK 信号，所以很可能错过一开始的 reset 信号，所以这里要用异步的 reset。

```scala
// MUST use async reset here
// otherwise the internal logic(e.g. TLXbar) might not function
// if reset deasserted before TCK rises
systemJtag.reset := reset.asAsyncReset
target.resetctrl.foreach { rc =>
  rc.hartIsInReset.foreach { _ := childReset }
}
Debug.connectDebugClockAndReset(target.debug, clock)
```

## 配置 JTAG 相关的约束

这部分是参考了 pulp 的 VCU118 中 jtag 信号的约束文件。照着抄就行：

```tcl
create_clock -period 100.000 -name jtag_TCK [get_ports jtag_TCK]
set_input_jitter jtag_TCK 1.000
set_property CLOCK_DEDICATED_ROUTE FALSE [get_nets jtag_TCK_IBUF_inst/O]
set_input_delay -clock jtag_TCK -clock_fall 5.000 [get_ports jtag_TDI]
set_input_delay -clock jtag_TCK -clock_fall 5.000 [get_ports jtag_TMS]
set_output_delay -clock jtag_TCK 5.000 [get_ports jtag_TDO]
set_max_delay -to [get_ports jtag_TDO] 20.000
set_max_delay -from [get_ports jtag_TMS] 20.000
set_max_delay -from [get_ports jtag_TDI] 20.000
set_clock_groups -asynchronous -group [get_clocks jtag_TCK] -group [get_clocks -of_objects [get_pins system_i/clk_wiz_0/inst/mmcme4_adv_inst/CLKOUT1]]
set_property ASYNC_REG TRUE [get_cells -hier -regexp "system_i/rocketchip_wrapper_0/.*/cdc_reg_reg.*"]
```

和原版本稍微改了一下，一个区别是 `set_clock_groups` 的时候，第二个时钟参数用的是 Clocking Wizard 的输出，同时也是 Rocket Chip 自己的时钟输入；另一个区别是用的 ASYNC_REG 查询语句不大一样。我没有具体分析过这些约束为什么这么写，不确定这些约束是否都合理，是否都是需要的，没有测试过不带这些约束会不会出问题。

## 运行 OpenOCD 和 GDB

最后，采用如下的 OpenOCD 配置来连接：

```tcl
# openocd config
# use ftdi channel 1
# vcu128 uart0 as jtag
adapter speed 10000
adapter driver ftdi
ftdi_vid_pid 0x0403 0x6011 # FT4232H
ftdi_layout_init 0x0008 0x000b # Output: TCK TDI TMS
ftdi_tdo_sample_edge falling
ftdi_channel 1 # channel B
reset_config none

set _CHIPNAME riscv
jtag newtap $_CHIPNAME cpu -irlen 5

set _TARGETNAME $_CHIPNAME.cpu

target create $_TARGETNAME.0 riscv -chain-position $_TARGETNAME
$_TARGETNAME.0 configure -work-area-phys 0x80000000 -work-area-size 10000 -work-area-backup 1
```

然后就可以连接到 Rocket Chip 上：

```shell
> openocd -f openocd.cfg
Open On-Chip Debugger 0.11.0-rc2
Licensed under GNU GPL v2
For bug reports, read
        http://openocd.org/doc/doxygen/bugs.html
Info : auto-selecting first available session transport "jtag". To override use 'transport select <transport>'.
Info : Listening on port 6666 for tcl connections
Info : Listening on port 4444 for telnet connections
Info : clock speed 10000 kHz
Info : JTAG tap: riscv.cpu tap/device found: 0x10000913 (mfg: 0x489 (SiFive Inc), part: 0x0000, ver: 0x1)
Info : datacount=2 progbufsize=16
Info : Disabling abstract command reads from CSRs.
Info : Examined RISC-V core; found 1 harts
Info :  hart 0: XLEN=64, misa=0x800000000094112d
Info : starting gdb server for riscv.cpu.0 on 3333
Info : Listening on port 3333 for gdb connections
> riscv64-unknown-elf-gdb
(gdb) target remote localhost:3333
Remote debugging using localhost:3333
0x00000000800001a4 in ?? ()
```

可以看到调试功能都正常了。

## 总结

调试这个功能大概花了一天的时间，主要遇到了下面这些问题：

1. 调试模块的 reset 信号需要是异步的，这个是通过仿真（Remote Bitbang 连接 OpenOCD）调试出来的
2. 看 schematic 的时候 rxd/txd 搞反了，后来仔细对比才找到了正确的对应关系
3. OpenOCD 配置的 irlen 一开始写的不对，dmcontrol 读出来是 0，一直以为是有别的问题，结果改了 irlen 后立马就成功了，这个问题可以让 OpenOCD 自动推断 irlen 来发现

## 参考

- [VCU128 User Guide](https://www.xilinx.com/support/documentation/boards_and_kits/vcu128/ug1302-vcu128-eval-bd.pdf)
- [FT4232H](https://ftdichip.com/wp-content/uploads/2020/08/DS_FT4232H.pdf)
- [DesignKeyWrapper from 中国 Chisel 之父 @sequencer](https://github.com/sequencer/rocket-doc/blob/e55f7af549c5859b3c8f5a52c81c4c802153ed60/sanitytests/vcu118/src/DesignKeyWrapper.scala)
- [pulp VCU118 constraints](https://github.com/pulp-platform/pulp/blob/770b4e1d69baf7daceaadcb301ba7212a4310577/fpga/pulp-vcu118/constraints/vcu118.xdc)