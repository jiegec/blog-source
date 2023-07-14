---
layout: post
date: 2022-04-19
tags: [wch,ch32,ch32v307,riscv,eval]
categories:
    - hardware
---

# 试用沁恒 CH32V307 评估板

## 背景

之前有一天看到朋友在捣鼓 CH32V307，因此自己也萌生了试用 CH32V307 评估板的兴趣，于是在[沁恒官网申请样品](http://www.wch.cn/services/request_sample.html)，很快就接到电话了解情况，几天后就顺丰送到了，不过因为疫情原因直到现在才拿到手上，只能说疫情期间说不定货比人还快。

## 开箱

收到的盒子里有一个 [CH32V307 评估板](http://special.wch.cn/zh_cn/RISCV_MCU_Index/)，和一个 [WCH-Link](http://www.wch.cn/products/WCH-Link.html)，相关资料可以在 [官网](http://www.wch.cn/products/CH32V307.html) 或者 [openwch/ch32v307](https://github.com/openwch/ch32v307) 下载。在说明书中有如下的图示：

![](/images/ch32v307.png)

板子自带的跳线帽不是很多，建议自备一些，或者用杜邦线替代。比较重要的是 WCH-Link 子板上 CH549 和 CH2V307 连接的几个信号，和下面 BOOT0/1 的选择。

## WCH-Link

可以看到评估板自带了一个 WCH-Link，所以不需要附赠的那一个，直接把 11 号 Type-C 连接到电脑上即可。这里还遇到一个小插曲，用 Type-C to Type-C 的线连电脑上不工作，连 PWR LED 都点不亮，换一根 Type-A to Type-C 的就可以，没有继续研究是什么原因。电脑上可以看到 WCH-Link 的设备：VID=1a86, PID=8010。比较有意思的是，在 RISC-V 模式（CON 灯不亮）的时候 PID 是 8010，ARM 模式（CON 灯亮）的时候 PID 是 8011，从 RISC-V 模式切换到 ARM 模式的方法是连接 TX 和 GND 后上电，反过来要用 MounRiver，详见 WCH-Link 使用说明 [V1.0](http://www.wch.cn/uploads/file/20210707/1625645582172366.pdf) [V1.3](http://www.wch.cn/uploads/file/20210906/1630922260396691.pdf) 和原理图 [V1.1](http://www.wch.cn/uploads/file/20210104/1609725144187113.pdf)。

给沁恒开源 WCH-Link 原理图并开放固件点个赞，在淘宝上也可以看到不少 WCH-Link 的仿真器，挺有意思的。

在 ARM 模式下，它实现了类似 [CMSIS-DAP](https://www.keil.com/support/man/docs/dapdebug/dapdebug_introduction.htm) 的协议，可以用 OpenOCD 调试：

```tcl
source [find interface/cmsis-dap.cfg]
adapter speed 1000
cmsis_dap_vid_pid 0x1a86 0x8011
transport select swd
init
```

```shell
$ openocd -f openocd.cfg
Open On-Chip Debugger 0.11.0
Licensed under GNU GPL v2
For bug reports, read
        http://openocd.org/doc/doxygen/bugs.html
Info : CMSIS-DAP: SWD  Supported
Info : CMSIS-DAP: FW Version = 2.0.0
Info : CMSIS-DAP: Interface Initialised (SWD)
Info : SWCLK/TCK = 1 SWDIO/TMS = 1 TDI = 0 TDO = 0 nTRST = 0 nRESET = 1
Info : CMSIS-DAP: Interface ready
Info : clock speed 1000 kHz
Warn : gdb services need one or more targets defined
Info : Listening on port 6666 for tcl connections
Info : Listening on port 4444 for telnet connections
```

不过这里我们要用的是 RISC-V 处理器 CH32V307，上面的就当是 WCH-LINK 使用的小贴士。

给评估板插上 USB Type-C 以后，首先上面的 WCH-Link 部分中红色的 PWR 和绿色的 RUN 亮，CON 不亮，说明 WCH-LINK 的 CH549 已经启动，并且处在 RISC-V 模式（CON 不亮）。CH549 是一个 8051 指令集的处理器，上面的跑的 WCH-LINK 固件在网上可以找到，在下面提到的 MounRiver Studio 目录中也有一份。

## OpenOCD

目前开源工具上游还不支持 CH32V307 的开发，需要用 [MounRiver](http://www.mounriver.com/download)，支持 Windows 和 Linux，有两部分：

- [MRS_Toolchain_Linux_x64_V1.40.tar.xz](http://file.mounriver.com/tools/MRS_Toolchain_Linux_x64_V1.40.tar.xz): RISC-V GNU Toolchain 和 OpenOCD
- [MounRiver_Studio_Community_Linux_V110](http://file.mounriver.com/upgrade/MounRiver_Studio_Community_Linux_x64_V110.tar.xz)：基于 Eclipse 做的 IDE

解压缩后，可以看到它的 OpenOCD 配置：

```tcl
## wch-arm.cfg
adapter driver cmsis-dap
transport select swd
source [find ../share/openocd/scripts/target/ch32f1x.cfg]
## wch-riscv.cfg
#interface wlink
adapter driver wlink
wlink_set
set _CHIPNAME riscv
jtag newtap $_CHIPNAME cpu -irlen 5 -expected-id 0x00001

set _TARGETNAME $_CHIPNAME.cpu

target create $_TARGETNAME.0 riscv -chain-position $_TARGETNAME
$_TARGETNAME.0 configure  -work-area-phys 0x80000000 -work-area-size 10000 -work-area-backup 1
set _FLASHNAME $_CHIPNAME.flash

flash bank $_FLASHNAME wch_riscv 0x00000000 0 0 0 $_TARGETNAME.0

echo "Ready for Remote Connections"
```

其中 ch32f1x.cfg 就是 stm32f1x.cfg 改了一下名字，可以看到 WCH OpenOCD 把它的 RISC-V 调试协议称为 wlink，估计是取 wch-link 的简称吧。除了 wlink 部分，其他就是正常的 RISC-V CPU 调试的 OpenOCD 配置，比较有意思的就是 IDCODE 设为了 0x00001，比较有个性。

在网上一番搜索，找到了 WCH OpenOCD 的源码 [Embedded_Projects/riscv-openocd-wch](https://git.minori.work/Embedded_Projects/riscv-openocd-wch)，是网友向沁恒获取的源代码，毕竟 OpenOCD 是 GPL 软件。简单看了一下代码，是直接把 RISC-V Debug 中的 DMI 操作封装了一下，然后通过 USB Bulk 和 WCH-Link 通信。我从 riscv-openocd 找到了一个比较接近的 [commit](https://github.com/jiegec/riscv-openocd/commit/cc0ecfb6d5b939bd109ea84b07b5eab3cdf80316)，然后把 WCH 的代码提交上去，得到了 [diff](https://github.com/jiegec/riscv-openocd/commit/bfa3bc7f98d22fa60ef6d3b2f5d98859fa963f85)，有兴趣的可以看看具体实现，甚至把这个支持提交到上游。

有源码以后，就可以在 macOS 上编译了（需要修复三处 clang 报告的编译错误，[最终代码](https://github.com/jiegec/riscv-openocd/tree/wch)）：

```shell
$ ./bootstrap
$ ./configure --prefix=/path/to/prefix/openocd --enable-wlink --disable-werror CAPSTONE_CFLAGS=-I/opt/homebrew/opt/capstone/include/
$ make -j4 install
```

如果遇到 makeinfo 报错，把 homebrew 的 texinfo 加到 PATH 即可。

编译完成后，就可以用前面提到的 wch-riscv.cfg 进行调试了：

```shell
$ /path/to/prefix/openocd -f wch-riscv.cfg
Open On-Chip Debugger 0.11.0+dev-01623-gbfa3bc7f9 (2022-04-20-09:55)
Licensed under GNU GPL v2
For bug reports, read
        http://openocd.org/doc/doxygen/bugs.html
Info : only one transport option; autoselect 'jtag'
Ready for Remote Connections
Info : Listening on port 6666 for tcl connections
Info : Listening on port 4444 for telnet connections
Info : WCH-Link version 2.3 
Info : wlink_init ok
Info : This adapter doesn't support configurable speed
Info : JTAG tap: riscv.cpu tap/device found: 0x00000001 (mfg: 0x000 (<invalid>), part: 0x0000, ver: 0x0)
Warn : Bypassing JTAG setup events due to errors
Info : [riscv.cpu.0] datacount=2 progbufsize=8
Info : Examined RISC-V core; found 1 harts
Info :  hart 0: XLEN=32, misa=0x40901125
[riscv.cpu.0] Target successfully examined.
Info : starting gdb server for riscv.cpu.0 on 3333
Info : Listening on port 3333 for gdb connections
```

这也验证了上面的发现：因为绕过了 jtag，直接发送 dmi，所以 idcode 是假的：

```cpp
if(wchwlink){
        buf_set_u32(idcode_buffer, 0, 32, 0x00001);  //Default value,for reuse risc-v jtag debug
}
```

接下来就可以用 GDB 调试了。里面跑了一个样例的程序，就是向串口打印：

```shell
$ screen /dev/tty.usbmodem* 115200
SystemClk:72000000
111
   111
      111
         111
            111
```

之后则是针对各个外设，基于沁恒提供的示例代码进行相应的开发了。

## Baremetal 代码

接下来看看沁恒提供的代码是如何配置的。在 EVT/EXAM/SRC/Startup/startup_ch32v30x_D8C.S 可以看到初始化的汇编代码。比较有意思的是，这个核心扩展了 mtvec，支持 ARM 的 vector table 模式，即放一个指针数组，而不是指令：

```asm
    .section    .vector,"ax",@progbits
    .align  1
_vector_base:
    .option norvc;
    .word   _start
    .word   0
    .word   NMI_Handler                /* NMI */
    .word   HardFault_Handler          /* Hard Fault */
```

这些名字如此熟悉，只能说这是 ARVM 了（ARM + RV）。后面的部分比较常规，把 data 段复制到 sram，然后清空 bss：

```asm
handle_reset:
.option push 
.option	norelax 
        la gp, __global_pointer$
.option	pop 
1:
        la sp, _eusrstack 
2:
        /* Load data section from flash to RAM */
        la a0, _data_lma
        la a1, _data_vma
        la a2, _edata
        bgeu a1, a2, 2f
1:
        lw t0, (a0)
        sw t0, (a1)
        addi a0, a0, 4
        addi a1, a1, 4
        bltu a1, a2, 1b
2:
        /* Clear bss section */
        la a0, _sbss
        la a1, _ebss
        bgeu a0, a1, 2f
1:
        sw zero, (a0)
        addi a0, a0, 4
        bltu a0, a1, 1b
2:
```

最后是进行一些 csr 的配置，然后进入 C 代码：

```asm
    li t0, 0x1f
    csrw 0xbc0, t0

    /* Enable nested and hardware stack */
    li t0, 0x1f
    csrw 0x804, t0

    /* Enable floating point and interrupt */
    li t0, 0x6088           
    csrs mstatus, t0

    la t0, _vector_base
    ori t0, t0, 3           
    csrw mtvec, t0

    lui a0, 0x1ffff
    li a1, 0x300
    sh a1, 0x1b0(a0)
1:  lui s2, 0x40022
    lw a0, 0xc(s2)
    andi a0, a0, 1
    bnez a0, 1b

    jal  SystemInit
    la t0, main
    csrw mepc, t0
    mret
```

这里有一些自定义的 csr，比如 corecfgr(0xbc0)，intsyscr(0x804，设置了 HWSTKEN=1, INESTEN=1, PMTCFG=0b11, HWSTKOVEN=1)，具体参考 [QingKeV4_Processor_Manual](http://www.wch.cn/downloads/QingKeV4_Processor_Manual_PDF.html)。接着代码往 0x1ffff1b0 写入 0x300，然后不断读取 FLASH Interface (0x40022000) 的 STATR 字段，没有找到代码中相关的定义，简单猜测与 Flash 的零等待/非零等待区有关，因为后续代码要提高频率，因此 Flash 控制器需要增加 wait state。

## 编译

可以用 MounRiver 编译，也可以用 SiFive 的 riscv64-unknown-elf 工具链进行编译，参考 [Embedded_Projects/CH32V307_Template](https://git.minori.work/Embedded_Projects/CH32V307_Template) 项目中的编译方式，修改 `riscv64-elf.cmake` 为：

```cmake
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_C_COMPILER riscv64-unknown-elf-gcc)
set(CMAKE_CXX_COMPILER riscv64-unknown-elf-g++)
# Make CMake happy about those compilers
set(CMAKE_TRY_COMPILE_TARGET_TYPE "STATIC_LIBRARY")
```

然后交叉编译就可以了。需要注意的是对 libnosys 的处理，如果没有正确链接，就会出现 syscall，然后在 ecall handler 里面死循环。

如果不想用 CMake，也可以用下面的精简版 Makefile：

```make
USER := User/main.c User/ch32v30x_it.c User/system_ch32v30x.c
LIBRARY := ../../SRC/Peripheral/src/ch32v30x_misc.c \
	../../SRC/Peripheral/src/ch32v30x_usart.c \
	../../SRC/Peripheral/src/ch32v30x_gpio.c \
	../../SRC/Peripheral/src/ch32v30x_rcc.c \
	../../SRC/Debug/debug.c \
	../../SRC/Startup/startup_ch32v30x_D8C.S
LDSCRIPT = ../../SRC/Ld/Link.ld
# disable libc first
CFLAGS := -march=rv32imafc -mabi=ilp32f \
	-flto -ffunction-sections -fdata-sections \
	-nostartfiles -nostdlib \
	-T $(LDSCRIPT) \
	-I../../SRC/Debug \
	-I../../SRC/Core \
	-I../../SRC/Peripheral/inc \
	-I./User \
	-O2 \
	-Wl,--print-memory-usage
# link libc & libnosys in the end
CFLAGS_END := \
	-lc -lgcc -lnosys
PREFIX := riscv64-unknown-elf-

all: obj/build.bin

obj/build.bin: obj/build.elf
	$(PREFIX)objcopy -O binary $^ $@

obj/build.elf: $(USER) $(LIBRARY)
	$(PREFIX)gcc $(CFLAGS) $^ $(CFLAGS_END) -o $@

clean:
	rm -rf obj/*
```

## 烧写 Flash

编译好以后，根据 WCH OpenOCD 的文档，可以用下面的配置来进行烧写：

```tcl
#interface wlink
adapter driver wlink
wlink_set
set _CHIPNAME riscv
jtag newtap $_CHIPNAME cpu -irlen 5 -expected-id 0x00001

set _TARGETNAME $_CHIPNAME.cpu

target create $_TARGETNAME.0 riscv -chain-position $_TARGETNAME
$_TARGETNAME.0 configure  -work-area-phys 0x80000000 -work-area-size 10000 -work-area-backup 1
set _FLASHNAME $_CHIPNAME.flash

flash bank $_FLASHNAME wch_riscv 0x00000000 0 0 0 $_TARGETNAME.0

init
halt

flash erase_sector wch_riscv 0 last
program /path/to/firmware
verify_image /path/to/firmware
wlink_reset_resume
exit
```

输出：

```shell
$ openocd -f program.cfg
Open On-Chip Debugger 0.11.0+dev-01623-gbfa3bc7f9 (2022-04-20-09:55)
Licensed under GNU GPL v2
For bug reports, read
        http://openocd.org/doc/doxygen/bugs.html
Info : only one transport option; autoselect 'jtag'
Ready for Remote Connections
Info : WCH-Link version 2.3
Info : wlink_init ok
Info : This adapter doesn't support configurable speed
Info : JTAG tap: riscv.cpu tap/device found: 0x00000001 (mfg: 0x000 (<invalid>), part: 0x0000, ver: 0x0)
Warn : Bypassing JTAG setup events due to errors
Info : [riscv.cpu.0] datacount=2 progbufsize=8
Info : Examined RISC-V core; found 1 harts
Info :  hart 0: XLEN=32, misa=0x40901125
[riscv.cpu.0] Target successfully examined.
Info : starting gdb server for riscv.cpu.0 on 3333
Info : Listening on port 3333 for gdb connections
Info : device id = REDACTED
Info : flash size = 256kbytes
Info : JTAG tap: riscv.cpu tap/device found: 0x00000001 (mfg: 0x000 (<invalid>), part: 0x0000, ver: 0x0)
Warn : Bypassing JTAG setup events due to errors
** Programming Started **
** Programming Finished **
Info : Verify Success
```

访问串口 `screen /dev/tty.usbmodem* 115200`，可以看到正确地输出了内容。

## 转发

本文已授权转发到以下的地址：

- [公众号 物联网小生 试用沁恒 CH32V307 评估板](https://mp.weixin.qq.com/s/wJ0X8qdIWRxavGo9N37QSg)
- [语雀 硬件知识库 试用沁恒 CH32V307 评估板](https://www.yuque.com/zsafly/lfxyfc/zseeyx)