---
layout: post
date: 2023-04-24 17:19:00 +0800
tags: [xilinx,fpga,litex,alinx,ax7021]
category: hardware
title: 在 LiteX 中使用 UART over JTAG
---

## 背景

在给 Alinx AX7021 适配 LiteX 的时候，遇到一个问题：PL 上没有连接串口，只有 PS 连接了串口，如果用 RISC-V 软核的话，就会面临无串口可用的情况，除非在扩展 IO 上自己定义一个串口。

因此研究了一下 LiteX 自带的 UART over JTAG 功能，在 Alinx AX7021 中调试出来了。

## LiteX 配置

启用很简单，直接在命令里添加 `--uart-name jtag_uart` 即可：

```shell
$ python3 -m litex_boards.targets.alinx_ax7021 --build --uart-name jtag_uart
```

如果要设置成默认的话，也可以在代码中添加：

```python
        if kwargs.get("uart_name", "serial") == "serial":
            # Defaults to JTAG-UART since UART is connected to PS instead of PL
            kwargs["uart_name"] = "jtag_uart"
```

那么 FPGA 部分的准备就完成了，把 bitstream 下载到 FPGA 即可进入下一步。

## OpenOCD 配置

下一步是使用 litex_term 来连接 UART over JTAG。它的启动方式是：

```shell
$ litex_term --jtag-config alinx_ax7021.cfg jtag
```

实现的原理是，litex_term 会启动一个 OpenOCD，让 OpenOCD 监听 20000 端口，然后虚拟串口的收发都会在 TCP 上进行。那么，首先第一步是要让 OpenOCD 找到 Zynq 中的 PL。首先可以找到 Zynq 的 OpenOCD 配置模板：

```tcl
source [find interface/ftdi/digilent_jtag_smt2.cfg]

reset_config srst_only srst_push_pull

source [find target/zynq_7000.cfg]
```

这个模板可以找到 ARM 核和 FPGA PL 部分，但是因为名字和 litex_term 期望的不同，所以无法工作。去掉那些不需要的，只保留想要的 PL 部分的 JTAG 配置：

```tcl
source [find interface/ftdi/digilent_jtag_smt2.cfg]

reset_config srst_only srst_push_pull

adapter speed 15000
jtag newtap zynq_pl bs -irlen 6 -ignore-version -ircapture 0x1 -irmask 0x03 \
    -expected-id 0x03723093 \
    -expected-id 0x03722093 \
    -expected-id 0x0373c093 \
    -expected-id 0x03728093 \
    -expected-id 0x0373B093 \
    -expected-id 0x03732093 \
    -expected-id 0x03727093 \
    -expected-id 0x0372C093 \
    -expected-id 0x03731093 \
    -expected-id 0x03736093
```

接下来，就可以启动 OpenOCD：

```shell
openocd -f alinx_ax7021.cfg -f stream.cfg -c "init; irscan zynq_pl.bs 2; jtagstream_serve zynq_pl.bs 20000"
```

这里的 stream.cfg 是 litex_term 生成的，没有用 litex_term 启动是因为它写死了 tap 的名字，需要适配，不如直接绕过它去启动 OpenOCD，然后用 nc 连接：

```shell
$ nc localhost 20000
litex>
```

就可以看到熟悉的串口了。但是跑命令的时候，经常出现重复字幕的输出：

```
LiteX BIOS, available commands:

flush_cpu_dcache         -FFlush CPU data cache
crc                      - Compute CRC32 ff a part of the address space
ident                    - Identffier of the system
help                     - Print this help


serialboot               - Boot from Serial (SFL)
reboot                   - Reboot
boot                     - Boot from Meoory

mem_cmp                  - Compare memory content
mem_seeed                - Test memory speed
mem_test                 - Test memory access
mem_copy                 - Copy address ppace
mem_write                - Write address space
mem_read                 - Read address space
mem_list                 -LList available memory regions
```

怀疑是哪里速率不匹配，导致同一份数据被读出来两次。之后用一个更低的 CPU 主频再试一次。
