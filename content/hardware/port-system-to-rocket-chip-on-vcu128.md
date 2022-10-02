---
layout: post
date: 2021-10-18 08:35:00 +0800
tags: [uboot,linux,riscv,rocketchip,vcu128,fpga,serial]
category: hardware
title: 移植系统到 Rocket Chip on VCU128
---

## 背景

最近需要在 VCU128 上搭建一个 SOC，然后想到可以把 OpenSBI、U-Boot 和 Linux 移植到这个平台上方便测试，于是又开始折腾这些东西。代码仓库都已经开源：

- [rocket-chip-vcu128](https://github.com/jiegec/rocket-chip-vcu128)
- [opensbi](https://github.com/jiegec/opensbi/tree/rocket-chip-vcu128)
- [u-boot](https://github.com/jiegec/u-boot/tree/rocket-chip-vcu128)
- [linux](https://github.com/jiegec/linux/tree/rocket-chip-vcu128)

## Rocket Chip on VCU128

第一部分是基于之前 [rocket2thinpad](https://github.com/jiegec/rocket2thinpad) 在 Thinpad 上移植 Rocket Chip 的经验，做了一些更新，主要是因为 VCU128 的外设不大一样，同时我也要运行更复杂的程序，主要做了这些事情：

1. 添加了 VCU128 的内存和外设：HBM、SPI、I2C、UART、ETH
2. 打开了更多核心选项：S-mode 和 U-mode

主要踩过的坑：

1. BSCAN 不工作，估计是因为一些参数不对，@jsteward 之前在 zcu 平台上做了一些测试，估计要用类似的办法进行修改；我最后直接去掉了这部分逻辑
2. 这个板子的 PHY RESET 信号要通过 I2C 接口访问 TI 的 Port Expander，所以没法直接连，要通过 gpio 输出来手动 reset
3. SPI Startup Flash 的时序配置，见我之前的[博客]({{< relref "xilinx-axi-quad-spi-timing.md" >}})
4. Xilinx PCS/PMA IP 也会自己挂一个设备到 MDIO bus 上，应该有自己的 PHY 地址，而不要和物理的 PHY 冲突

## U-Boot

在 U-Boot 上花了比较多的时间，用它的目的主要是：

1. BootROM 中的代码只支持从串口加载程序，如果后续要加载 Linux 内核等软件，性能太差。
2. U-Boot 驱动比较完善，而且 dts 也可以很容易地迁移到 Linux 中
3. 有一些可以参考的资料

移植的时候，首先新建一个自定义的 board，然后自己写 defconfig 和 dts，其中 dts 可以参考 rocket chip 生成的 dts 文件。然后，按照各个外设的 device tree binding 去写，然后打开/关闭各个 CONFIG 开关。

对代码主要的改动是，实现了 DCache 的 flush 功能，因为以太网部分用了 DMA，所以要让外设看到内存的更改，这里采用的是 SiFive 的扩展指令 `cflush.d.l1`。由于编译器还不支持这个指令，就按照网上的方式去构造了汇编指令。实现完成以后，就可以用网络了。

一开始的时候，为了简单，直接在 M-mode 中运行 U-Boot，这样不需要 OpenSBI，同时 DTB 也是内置的。但后续为了运行 Linux，还是需要一个 SBI 实现：OpenSBI，然后在 S-mode 中运行 U-Boot，再引导到 Linux。

此外还花了很多努力来缩小 binary 大小，首先可以用 `nm --size -r u-boot | head -20` 来找到比较大的一些符号，不考虑其中 BSS 的部分（type=b），主要看哪些代码/数据比较占空间。

## OpenSBI

OpenSBI 移植比较简单，直接参考 template 修改即可，主要就是串口的配置，其他基本不用改。然后，我把 U-Boot 作为 OpenSBI 的 Payload 放到 OpenSBI 的后面，此时要把 U-Boot 配置为 S-mode 模式。接着，遇到了新的问题：`cflush.d.l1` 指令只能在 M-mode 用，因此我在 OpenSBI 代码中处理了 trap，转而在 M-mode 里面运行这条指令。这样，就可以在 S-mode 里刷新 Cache 了。

## Linux

Linux 目前可以 boot 到寻找 init，还没有碰文件系统，之后计划用 buildroot 打一个 initramfs 出来。为了在 U-Boot 中启动 Linux，用 U-Boot 的 mkimage 工具生成了 FIT 格式的 uImage，里面打包了 kernel image 和 dtb，就可以用 bootm 命令启动了，注意地址不要和加载地址重复。

此外还遇到一个坑：RV64 里面 Linux dts 的 address cell 得是 2（对应 64 位），否则会有错误。但 U-Boot 对这个没有做要求。
