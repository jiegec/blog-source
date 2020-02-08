---
layout: post
date: 2020-02-09 00:35:00 +0800
tags: [openocd,fpga,artix7,macos]
category: hardware
title: 在 macOS 烧写 Artix7 FPGA
---

首先安装好openocd：

```brew install openocd --HEAD```

测试所用版本为 `0.10.0+dev-01052-g09580964 (2020-02-08-15:09)`。

然后编写如下的 openocd.cfg：

```
adapter driver ftdi
adapter speed 10000
ftdi_vid_pid 0x0403 0x6014
ftdi_layout_init 0x0008 0x004b

source [find cpld/xilinx-xc7.cfg]
init
xc7_program xc7.tap
pld load 0 /path/to/bitstream.bit
shutdown
```

上面的 ftdi 开头的两行按照实际的 JTAG Adapter 修改。可以参考 openocd 自带的一些 cfg。

然后在 openocd.cfg 的目录运行 `openocd` 即可：

```shell
$ openocd
Open On-Chip Debugger 0.10.0+dev-01052-g09580964 (2020-02-08-15:09)
Licensed under GNU GPL v2
For bug reports, read
        http://openocd.org/doc/doxygen/bugs.html
Info : auto-selecting first available session transport "jtag". To override use 'transport select <transport>'.
Info : ftdi: if you experience problems at higher adapter clocks, try the command "ftdi_tdo_sample_edge falling"
Info : clock speed 10000 kHz
Info : JTAG tap: xc7.tap tap/device found: 0x0362d093 (mfg: 0x049 (Xilinx), part: 0x362d, ver: 0x0)
Warn : gdb services need one or more targets defined
shutdown command invoked
Info : Listening on port 6666 for tcl connections
Info : Listening on port 4444 for telnet connections
```

这时 FPGA 已经烧写成功。