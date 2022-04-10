---
layout: post
date: 2022-04-10 09:36:00 +0800
tags: [vivado,svf,jtag,bitstream]
category: hardware
title: 导出 Vivado 下载 Bitstream 的 SVF 文件
---

## 背景

最近在研究如何实现一个远程 JTAG 的功能，目前实现在 [jiegec/jtag-remote-server](https://github.com/jiegec/jtag-remote-server)，实现了简单的 XVC 协议，底层用的是 libftdi 的 MPSSE 协议来操作 JTAG。但是，在用 Vivado 尝试的时候，SysMon 可以正常使用，但是下载 Bitstream 会失败，所以要研究一下 Vivado 都做了什么。

## SVF

SVF 格式其实是一系列的 JTAG 上的操作。想到这个，也是因为在网上搜到了一个 [dcfeb_v45.svf](https://www.asc.ohio-state.edu/physics/cms/firmwares/dcfeb_v45.svf)，里面描述的就是一段 JTAG 操作：

```svf
// Created using Xilinx Cse Software [ISE - 12.4]
// Date: Mon May 09 11:00:32 2011

TRST OFF;
ENDIR IDLE;
ENDDR IDLE;
STATE RESET;
STATE IDLE;
FREQUENCY 1E6 HZ;
//Operation: Program -p 0 -dataWidth 16 -rs1 NONE -rs0 NONE -bpionly -e -loadfpga 
TIR 0 ;
HIR 0 ;
TDR 0 ;
HDR 0 ;
TIR 0 ;
HIR 0 ;
HDR 0 ;
TDR 0 ;
//Loading device with 'idcode' instruction.
SIR 10 TDI (03c9) SMASK (03ff) ;
SDR 32 TDI (00000000) SMASK (ffffffff) TDO (f424a093) MASK (0fffffff) ;
//Boundary Scan Chain Contents
//Position 1: xc6vlx130t
TIR 0 ;
HIR 0 ;
TDR 0 ;
HDR 0 ;
TIR 0 ;
HIR 0 ;
TDR 0 ;
HDR 0 ;
TIR 0 ;
HIR 0 ;
HDR 0 ;
TDR 0 ;
//Loading device with 'idcode' instruction.
SIR 10 TDI (03c9) ;
SDR 32 TDI (00000000) TDO (f424a093) ;
//Loading device with 'bypass' instruction.
SIR 10 TDI (03ff) ;
//Loading device with 'idcode' instruction.
SIR 10 TDI (03c9) ;
SDR 32 TDI (00000000) TDO (f424a093) ;
// Loading device with a `jprogram` instruction. 
SIR 10 TDI (03cb) ;
// Loading device with a `isc_noop` instruction. 
SIR 10 TDI (03d4) ;
RUNTEST 100000 TCK;
// Check init_complete in ircapture.
//IR Capture using specified instruction.
SIR 10 TDI (03d4) TDO (0010) MASK (0010) ;
// Loading device with a `isc_enable` instruction. 
SIR 10 TDI (03d0) ;
SDR 5 TDI (00) SMASK (1f) ;
RUNTEST 100 TCK;
// Loading device with a `isc_program` instruction. 
SIR 10 TDI (03d1) ;
SDR 32 TDI (ffffffff) SMASK (ffffffff) ;
SDR 32 TDI (ffffffff) ;
SDR 32 TDI (ffffffff) ;
```

它的语法比较简单，大概就是 `SIR` 就是向 IR 输入，`SDR` 就是向 DR 输入，后面跟着的 TDO 和 MASK 表示对输出数据进行判断。比较核心的是下面这几步：

```svf
SIR JPROGRAM
SIR ISC_NOOP
RUNTEST 10000 TCK
SIR ISC_NOOP UNTIL ISC_DONE
SIR ISC_ENABLE
SIR ISC_PROGRAM
```

之后就是 bitstream 的内容了。有了 SVF 以后，就可以用其他的一些支持 SVF 语法的工具来烧写 FPGA，而不需要 Vivado。比如 OpenOCD 配置：

```tcl
# openocd config
# use ftdi channel 0
adapter speed 100000
adapter driver ftdi
transport select jtag
ftdi_vid_pid 0x0403 0x6011
ftdi_layout_init 0x0008 0x000b
ftdi_tdo_sample_edge falling
ftdi_channel 0
reset_config none

jtag newtap xcvu37p tap -irlen 18 -expected-id 0x14b79093

init

svf -tap xcvu37p.tap /path/to/program.svf progress

exit
```

### 从 Vivado 中导出 SVF

从文件头可以推测，这个功能是 Xilinx 官方提供的，一番搜索，果然找到了命令：[Creating SVF files using Xilinx Vivado](https://blog.xjtag.com/2016/07/creating-svf-files-using-xilinx-vivado/)

```tcl
program_hw_devices -force -svf_file {program.svf} [get_hw_devices xxx]
```

添加一个 `-svf_file` 参数后，就会生成一个 svf 文件。下面摘录一段：

```svf
// config/idcode
SIR 18 TDI (009249) ;
SDR 32 TDI (00000000) TDO (04b79093) MASK (0fffffff) ;
// config/jprog
STATE RESET;
STATE IDLE;
SIR 18 TDI (00b2cb) ;
SIR 18 TDI (014514) ;
// Modify the below delay for config_init operation (0.100000 sec typical, 0.100000 sec maximum)
RUNTEST 0.100000 SEC;
// config/jprog/poll
RUNTEST 15000 TCK;
SIR 18 TDI (014514) TDO (011000) MASK (031000) ;
// config/slr
SIR 18 TDI (005924) ;
SDR 226633216 TDI (0000000400000004e00000008001000c00000004d00000008001000c0000000466aa99550000000400000004000000040000000400000004000000040000
```

结合 Xilinx 官网可以下载的 BSDL 文件，可以找到每个 IR 对应的是什么：

```svf
// config/idcode
SIR 18 TDI (009249) ;
SDR 32 TDI (00000000) TDO (04b79093) MASK (0fffffff) ;
// BSDL:
"IDCODE           (001001001001001001)," & --   DEVICE_ID reg
attribute IDCODE_REGISTER of XCVU37P_FSVH2892 : entity is
        "XXXX" &        -- version
        "0100101" &     -- family
        "101111001" &   -- array size
        "00001001001" & -- manufacturer
        "1";            -- required by 1149.1
```

这一段是检查 IDCODE 是否是目标 FPGA 型号。

```svf
// config/jprog
STATE RESET;
STATE IDLE;
SIR 18 TDI (00b2cb) ;
SIR 18 TDI (014514) ;
// BSDL
"JPROGRAM         (001011001011001011)," & --   PRIVATE
"ISC_NOOP         (010100010100010100)," & --   PRIVATE, ISC_DEFAULT
// Modify the below delay for config_init operation (0.100000 sec typical, 0.100000 sec maximum)
RUNTEST 0.100000 SEC;
```

这一段发送了 JPROGRAM 和 ISC_NOOP 的 IR，然后进入 RUNTEST 状态一段时间。

```svf
// config/jprog/poll
RUNTEST 15000 TCK;
SIR 18 TDI (014514) TDO (011000) MASK (031000) ;
// BSDL
"ISC_NOOP         (010100010100010100)," & --   PRIVATE, ISC_DEFAULT
```
这里再次设置 ISC_NOOP，检查了 TDO 中的数据，意义不明。

```svf
// config/slr
SIR 18 TDI (005924) ;
SDR 226633216 TDI (0000000400000004e00000008001000c00000004d00000008001000c0000000466aa99550000000400000004000000040000000400000004000000040000
// BSDL
"CFG_IN_SLR0      (000101100100100100)," & --   PRIVATE
```

从这里就是开始往里面写入 bitstream，可以看到熟悉的 66aa9955 的同步字符，对比 Bitstream 文件内容：

```
000000c0: ffff ffff ffff ffff aa99 5566 2000 0000  ..........Uf ...
000000d0: 2000 0000 3002 2001 0000 0000 3002 0001   ...0. .....0...
000000e0: 0000 0000 3000 8001 0000 0000 2000 0000  ....0....... ...
000000f0: 3000 8001 0000 0007 2000 0000 2000 0000  0....... ... ...
00000100: 3000 2001 0000 0000 3002 6001 0000 0000  0. .....0.`.....
```

可以发现是每 32 字节按位颠倒：`aa995566(10101010 10011001 01010101 01100110) -> 66aa9955(01100110 10101010 10011001 01010101)`，后面的 `20000000 -> 00000004` 也是类似的。

Xilinx UG570 的 Table 6-5 也印证了上面的过程：

- Start loading the JPROGRAM instruction, LSB first:
- Load the MSB of the JPROGRAM instruction when exiting SHIFT-IR, as defined in the IEEE standard.
- Start loading the CFG_IN instruction, LSB first:
- Load the MSB of the CFG_IN instruction when exiting SHIFT-IR.
- Shift in the FPGA bitstream. Bit n (MSB) is the first bit in the bitstream.(3)(4)
- Shift in the last bit of the bitstream. Bit 0 (LSB) shifts on the transition to EXIT1-DR.

完成 CFG_IN 之后，再进行 JSTART:

```svf
// config/start
STATE IDLE;
RUNTEST 100000 TCK;
SIR 18 TDI (00c30c) ;
HIR 0 ;
TIR 0 ;
HDR 0 ;
TDR 0 ;
STATE IDLE;
RUNTEST 2000 TCK;
SIR 18 TDI (009249) TDO (031000) MASK (011000) ;
HIR 0 ;
TIR 0 ;
HDR 0 ;
TDR 0 ;
// BSDL
"JSTART           (001100001100001100)," & --   PRIVATE
"IDCODE           (001001001001001001)," & --   DEVICE_ID reg
```

然后再次进行 CFG_IN_SLR0, CFG_OUT_SLR0，验证是否真的写进去了：

```svf
// config/status
STATE RESET;
RUNTEST 5 TCK;
SIR 18 TDI (005924) ;
SDR 160 TDI (0000000400000004800700140000000466aa9955) ;
SIR 18 TDI (004924) ;
SDR 32 TDI (00000000) TDO (3f5e0d40) MASK (08000000) ;
STATE RESET;
RUNTEST 5 TCK;
// BSDL
"CFG_IN_SLR0      (000101100100100100)," & --   PRIVATE
"CFG_OUT_SLR0     (000100100100100100)," & --   PRIVATE
// config/status
STATE RESET;
RUNTEST 5 TCK;
SIR 18 TDI (005924) ;
SDR 160 TDI (0000000400000004800700140000000466aa9955) ;
SIR 18 TDI (004924) ;
SDR 32 TDI (00000000) TDO (3f5e0d40) MASK (08000000) ;
STATE RESET;
RUNTEST 5 TCK;
```

这段操作是进行 Status Register Readback，见 UG570 的 Table 10-4。MASK 设为 `08000000` 应该是判断它的第 4 位：END_OF_STARTUP_STATUS（Table 9-25）。

如果是 Quartus 用户，也可以 [生成 SVF](https://www.intel.com/content/www/us/en/support/programmable/articles/000085709.html)。