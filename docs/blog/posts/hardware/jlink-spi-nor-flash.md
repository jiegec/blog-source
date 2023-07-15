---
layout: post
date: 2023-05-08
tags: [spi,nor,flash,jlink,jflash]
categories:
    - hardware
---

# 使用 JLink 操作 SPI NOR Flash

## 背景

最近设计了一款 [PMOD SPI NOR Flash](https://github.com/jiegec/PMOD-SPI-NOR-FLASH) 扩展板，搭载了 W25Q128 SPI NOR Flash 芯片。在 jlc 生产回来以后，通过 JLink 连接到电脑上进行测试，看看是否可以用 JLink 操作 SPI NOR Flash。

<!-- more -->

## 连接到 JLink

JLink 提供了 20 pin 的引脚，如果要连接 SPI，那么引脚定义如下：

![](https://c.a.segger.com/fileadmin/images/products/J-Link/Software/pinout-spi-20-pin.gif.webp)

图源 [JFlash SPI 文档](https://www.segger.com/products/debug-probes/j-link/tools/j-flash-spi/)。

连接的时候，至少需要连接以下的引脚：

1. JLink GND(pin 4/6/8/10) - SPI NOR Flash GND
2. JLink VTref(pin 1) - 3.3V - SPI NOR Flash VCC
3. JLink CLK(pin 9) - SPI NOR Flash CLK
4. JLink DI(pin 5) - SPI NOR Flash D0/DI/MOSI
5. JLink DO(pin 13) - SPI NOR Flash D1/DO/MISO
6. JLink nCS(pin 7) - SPI NOR Flash CS#

由于 SPI NOR Flash 无法接受 5V 的电压，所以要用额外的 3.3V 作为电源，同时接到 JLink 的 VTref 引脚上。

JFlash SPI 还支持 Quad SPI 模式，可以在它的文档里找到连接方式。

## JFlash SPI

连接了以后，就可以在 JFlash SPI 软件中识别出 SPI Flash 了：Flash ID 0xEF 40 18。有意思的是，JFlash SPI 软件会认为这个芯片是 Infineon 的 S25FL128K，而不是 Winbond 的 W25Q128。发邮件问了一下 SEGGER，得到的回复是这两个芯片的 Flash ID 都是 0xEF4018，所以无法区分。

## flashrom

如果想用开源软件，可以用 flashrom，编译的时候打开 jlink 支持，就可以用 flashrom 来通过 JLink 读写 SPI NOR Flash。

但是 flashrom 的 cs 信号并不是上面的 nCS(pin 7)，而是 nRESET(pin 15，默认) 或者 nTRST(pin 3，可以添加参数 `cs=trst`)。这就导致如果想用 flashrom 的话，就要修改引脚连接方式，把 pin 15 连接到 SPI NOR Flash 的 CS# 上。修改连接以后，就可以检测到芯片了：

```shell
$ flashrom --programmer jlink_spi
flashrom v1.3.0 on Darwin 22.4.0 (arm64)
flashrom is free software, get the source code at https://flashrom.org

Calibrating delay loop... OK.
Found Winbond flash chip "W25Q128.V" (16384 kB, SPI) on jlink_spi.
===
This flash part has status UNTESTED for operations: WP
The test status of this chip may have been updated in the latest development
version of flashrom. If you are running the latest development version,
please email a report to flashrom@flashrom.org if any of the above operations
work correctly for you with this flash chip. Please include the flashrom log
file for all operations you tested (see the man page for details), and mention
which mainboard or programmer you tested in the subject line.
Thanks for your help!
No operations were specified.
```

为了解决这个问题，我给 [flashrom](https://review.coreboot.org/c/flashrom/+/75011) 提交了 patch，如果合并了，就可以支持 `--programmer jlink_spi:cs=tms` 选项，此时就不需要修改连接方式了。