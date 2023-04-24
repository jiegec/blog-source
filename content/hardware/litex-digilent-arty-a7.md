---
layout: post
date: 2023-04-19 15:55:00 +0800
tags: [digilent,arty,xilinx,fpga,litex]
category: hardware
title: 在 Arty A7 上用 LiteX 和 VexRiscv 跑 Linux
---

## litex 安装

litex 安装过程按照 <https://github.com/enjoy-digital/litex/wiki/Installation> 进行，由于需要 pip install，建议用 venv 来开一个干净的环境：

```shell
python3 -m venv venv
source venv/bin/activate
cd litex
./litex_setup.py --init --install
```

## 构建 bitstream

litex-boards 已经内建了 Arty A7 的支持，直接运行下列命令，就可以得到 bitstream：

```shell
python3 -m litex_boards.targets.digilent_arty --build --with-ethernet
```

这样就可以在 build/digilent_arty/gateware 目录下找到 bitstream。可以通过命令行参数来自定义需要的功能，详见 <https://github.com/litex-hub/litex-boards/blob/f5e51d72bca6ed0325c1213791a78362326002f8/litex_boards/targets/digilent_arty.py#L162-L180>。

如果想切换 CPU 为 Rocket Chip 的话，克隆并安装 <https://github.com/litex-hub/pythondata-cpu-rocket>，添加 `--cpu-type rocket --cpu-variant small` 参数即可。

## 下载 bitstream

最后，连接 microUSB 和网线到电脑，然后下载 bitstream：

```shell
openFPGALoader -b arty digilent_arty.bit
screen /dev/tty.usbserial-XXXXXXXXXXXXX 115200
```

就可以看到 litex 的输出：

```shell
--=============== SoC ==================--
CPU:            VexRiscv @ 100MHz
BUS:            WISHBONE 32-bit @ 4GiB
CSR:            32-bit data
ROM:            128.0KiB
SRAM:           8.0KiB
L2:             8.0KiB
SDRAM:          256.0MiB 16-bit @ 800MT/s (CL-7 CWL-5)
MAIN-RAM:       256.0MiB

--========== Initialization ============--
Ethernet init...
Initializing SDRAM @0x40000000...
Switching SDRAM to software control.
Read leveling:
  m0, b00: |00000000000000000000000000000000| delays: -
  m0, b01: |00000000000000000000000000000000| delays: -
  m0, b02: |11111111110000000000000000000000| delays: 04+-04
  m0, b03: |00000000000000111111111111000000| delays: 19+-05
  m0, b04: |00000000000000000000000000000011| delays: 30+-00
  m0, b05: |00000000000000000000000000000000| delays: -
  m0, b06: |00000000000000000000000000000000| delays: -
  m0, b07: |00000000000000000000000000000000| delays: -
  best: m0, b03 delays: 19+-05
  m1, b00: |00000000000000000000000000000000| delays: -
  m1, b01: |00000000000000000000000000000000| delays: -
  m1, b02: |11111111110000000000000000000000| delays: 04+-04
  m1, b03: |00000000000000111111111111000000| delays: 19+-05
  m1, b04: |00000000000000000000000000000011| delays: 30+-00
  m1, b05: |00000000000000000000000000000000| delays: -
  m1, b06: |00000000000000000000000000000000| delays: -
  m1, b07: |00000000000000000000000000000000| delays: -
  best: m1, b03 delays: 19+-05
Switching SDRAM to hardware control.
Memtest at 0x40000000 (2.0MiB)...
  Write: 0x40000000-0x40200000 2.0MiB
   Read: 0x40000000-0x40200000 2.0MiB
Memtest OK
Memspeed at 0x40000000 (Sequential, 2.0MiB)...
  Write speed: 37.0MiB/s
   Read speed: 48.7MiB/s

--============== Boot ==================--
Booting from serial...
Press Q or ESC to abort boot completely.
sL5DdSMmkekro
Timeout
Booting from network...
Local IP: 192.168.1.50
Remote IP: 192.168.1.100
Booting from boot.json...
Booting from boot.bin...
Copying boot.bin to 0x40000000...
Network boot failed.
No boot medium found

--============= Console ================--

litex> 
```

可见是非常方便的。之后可以用 litex_term 来往里面传程序，也可以直接通过 TFTP 来传。

## 启动 Linux

接下来，可以使用项目 <https://github.com/litex-hub/linux-on-litex-vexriscv> 来启动 Linux。参考项目 README，编译 Linux 并启动。不想折腾的话，可以从 <https://github.com/litex-hub/linux-on-litex-vexriscv/issues/164> 下载编译好的结果。

首先克隆项目到本地，然后运行：

```shell
git clone https://github.com/litex-hub/linux-on-litex-vexriscv.git
cd linux-on-litex-vexriscv
./make.py --board=arty
```

这样就生成了 bitstream，接下来构建 Linux 和 rootfs：

```shell
git clone http://github.com/buildroot/buildroot
cd buildroot
make BR2_EXTERNAL=../linux-on-litex-vexriscv/buildroot/ litex_vexriscv_defconfig
make
```

再构建 OpenSBI：

```shell
git clone https://github.com/litex-hub/opensbi --branch 0.8-linux-on-litex-vexriscv
cd opensbi
# riscv32-unknown-elf toolchain is built by ct-ng
make CROSS_COMPILE=riscv32-unknown-elf- PLATFORM=litex/vexriscv
```

但是实践过程中发现 ct-ng 编译的是 hardfloat 工具链，而默认配置下 vexriscv 不带 FPU，所以编译时用的是 rv32ima 作为 target，链接的时候报错，最后就直接用编译好的版本。

最后得到如下的几个文件：

- boot.json: linux-on-litex-vexriscv/images/boot.json
- rv32.dtb: linux-on-litex-vexriscv/images/rv32.dtb
- Image: buildroot/output/images/Image
- rootfs.cpio: buildroot/output/images/rootfs.cpio
- opensbi.bin

把这些文件复制到 TFTP 服务的目录下，重新 Program linux-on-litex-vexriscv/build/arty/gateware/arty.bit，即可启动 Linux：

```
--============== Boot ==================--
Booting from serial...
Press Q or ESC to abort boot completely.
sL5DdSMmkekro
Timeout
Booting from SDCard in SD-Mode...
Booting from boot.json...
Booting from boot.bin...
SDCard boot failed.
Booting from network...
Local IP: 192.168.1.50
Remote IP: 192.168.1.100
Booting from boot.json...
Copying Image to 0x40000000... (7726264 bytes)
Copying rv32.dtb to 0x40ef0000... (5294 bytes)
Copying rootfs.cpio to 0x41000000... (3566592 bytes)
Copying opensbi.bin to 0x40f00000... (53640 bytes)
Executing booted program at 0x40f00000

--============= Liftoff! ===============--

OpenSBI v0.8-1-gecf7701
   ____                    _____ ____ _____
  / __ \                  / ____|  _ \_   _|
 | |  | |_ __   ___ _ __ | (___ | |_) || |
 | |  | | '_ \ / _ \ '_ \ \___ \|  _ < | |
 | |__| | |_) |  __/ | | |____) | |_) || |_
  \____/| .__/ \___|_| |_|_____/|____/_____|
        | |
        |_|

Platform Name       : LiteX / VexRiscv-SMP
Platform Features   : timer,mfdeleg
Platform HART Count : 8
Boot HART ID        : 0
Boot HART ISA       : rv32imas
BOOT HART Features  : time
BOOT HART PMP Count : 0
Firmware Base       : 0x40f00000
Firmware Size       : 124 KB
Runtime SBI Version : 0.2

MIDELEG : 0x00000222
MEDELEG : 0x0000b101
[    0.000000] Linux version 6.1.0-rc2 (jiegec@linux) (riscv32-buildroot-linux-gnu-gcc.br_real (Buildroot 2023.02-270-gb100440bff) 11.3.0, GNU ld (GNU Binutils) 2.38) #1 SMP Wed Apr 19 16:21:39 CST 2023
[    0.000000] earlycon: liteuart0 at I/O port 0x0 (options '')
[    0.000000] Malformed early option 'console'
[    0.000000] earlycon: liteuart0 at MMIO 0xf0001000 (options '')
[    0.000000] printk: bootconsole [liteuart0] enabled
[    0.000000] Zone ranges:
[    0.000000]   Normal   [mem 0x0000000040000000-0x000000004fffffff]
[    0.000000] Movable zone start for each node
[    0.000000] Early memory node ranges
[    0.000000]   node   0: [mem 0x0000000040000000-0x000000004fffffff]
[    0.000000] Initmem setup node 0 [mem 0x0000000040000000-0x000000004fffffff]
[    0.000000] SBI specification v0.2 detected
[    0.000000] SBI implementation ID=0x1 Version=0x8
[    0.000000] SBI TIME extension detected
[    0.000000] SBI IPI extension detected
[    0.000000] SBI RFENCE extension detected
[    0.000000] SBI HSM extension detected
[    0.000000] riscv: base ISA extensions aim
[    0.000000] riscv: ELF capabilities aim
[    0.000000] percpu: Embedded 8 pages/cpu s11732 r0 d21036 u32768
[    0.000000] Built 1 zonelists, mobility grouping on.  Total pages: 65024
[    0.000000] Kernel command line: console=liteuart earlycon=liteuart,0xf0001000 rootwait root=/dev/ram0
[    0.000000] Dentry cache hash table entries: 32768 (order: 5, 131072 bytes, linear)
[    0.000000] Inode-cache hash table entries: 16384 (order: 4, 65536 bytes, linear)
[    0.000000] mem auto-init: stack:off, heap alloc:off, heap free:off
[    0.000000] Memory: 243336K/262144K available (5848K kernel code, 571K rwdata, 906K rodata, 215K init, 254K bss, 18808K reserved, 0K cma-reserved)
[    0.000000] SLUB: HWalign=64, Order=0-3, MinObjects=0, CPUs=1, Nodes=1
[    0.000000] rcu: Hierarchical RCU implementation.
[    0.000000] rcu:     RCU restricting CPUs from NR_CPUS=32 to nr_cpu_ids=1.
[    0.000000] rcu: RCU calculated value of scheduler-enlistment delay is 25 jiffies.
[    0.000000] rcu: Adjusting geometry for rcu_fanout_leaf=16, nr_cpu_ids=1
[    0.000000] NR_IRQS: 64, nr_irqs: 64, preallocated irqs: 0
[    0.000000] riscv-intc: 32 local interrupts mapped
[    0.000000] plic: interrupt-controller@f0c00000: mapped 32 interrupts with 1 handlers for 2 contexts.
[    0.000000] rcu: srcu_init: Setting srcu_struct sizes based on contention.
[    0.000000] riscv-timer: riscv_timer_init_dt: Registering clocksource cpuid [0] hartid [0]
[    0.000000] clocksource: riscv_clocksource: mask: 0xffffffffffffffff max_cycles: 0x171024e7e0, max_idle_ns: 440795205315 ns
[    0.000018] sched_clock: 64 bits at 100MHz, resolution 10ns, wraps every 4398046511100ns
[    0.010246] Console: colour dummy device 80x25
[    0.014169] Calibrating delay loop (skipped), value calculated using timer frequency.. 200.00 BogoMIPS (lpj=400000)
[    0.024255] pid_max: default: 32768 minimum: 301
[    0.033262] Mount-cache hash table entries: 1024 (order: 0, 4096 bytes, linear)
[    0.039790] Mountpoint-cache hash table entries: 1024 (order: 0, 4096 bytes, linear)
[    0.080128] ASID allocator using 9 bits (512 entries)
[    0.086947] rcu: Hierarchical SRCU implementation.
[    0.090826] rcu:     Max phase no-delay instances is 1000.
[    0.103556] smp: Bringing up secondary CPUs ...
[    0.107186] smp: Brought up 1 node, 1 CPU
[    0.118798] devtmpfs: initialized
[    0.169571] clocksource: jiffies: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 7645041785100000 ns
[    0.178637] futex hash table entries: 256 (order: 2, 16384 bytes, linear)
[    0.214981] NET: Registered PF_NETLINK/PF_ROUTE protocol family
[    0.455944] pps_core: LinuxPPS API ver. 1 registered
[    0.460007] pps_core: Software ver. 5.3.6 - Copyright 2005-2007 Rodolfo Giometti <giometti@linux.it>
[    0.469508] PTP clock support registered
[    0.476324] FPGA manager framework
[    0.493464] clocksource: Switched to clocksource riscv_clocksource
[    0.722433] NET: Registered PF_INET protocol family
[    0.731210] IP idents hash table entries: 4096 (order: 3, 32768 bytes, linear)
[    0.752236] tcp_listen_portaddr_hash hash table entries: 512 (order: 0, 4096 bytes, linear)
[    0.760269] Table-perturb hash table entries: 65536 (order: 6, 262144 bytes, linear)
[    0.767834] TCP established hash table entries: 2048 (order: 1, 8192 bytes, linear)
[    0.775654] TCP bind hash table entries: 2048 (order: 3, 32768 bytes, linear)
[    0.783026] TCP: Hash tables configured (established 2048 bind 2048)
[    0.789689] UDP hash table entries: 256 (order: 1, 8192 bytes, linear)
[    0.795620] UDP-Lite hash table entries: 256 (order: 1, 8192 bytes, linear)
[    0.816406] Unpacking initramfs...
[    0.926651] workingset: timestamp_bits=30 max_order=16 bucket_order=0
[    1.186672] io scheduler mq-deadline registered
[    1.190309] io scheduler kyber registered
[    1.570624] No litex,nclkout entry in the dts file
[    1.607895] LiteX SoC Controller driver initialized
[    2.358518] Initramfs unpacking failed: invalid magic at start of compressed archive
[    2.448554] Freeing initrd memory: 8192K
[    3.423827] f0001000.serial: ttyLXU0 at MMIO 0x0 (irq = 0, base_baud = 0) is a liteuart
[    3.431446] printk: console [liteuart0] enabled
[    3.431446] printk: console [liteuart0] enabled
[    3.440068] printk: bootconsole [liteuart0] disabled
[    3.440068] printk: bootconsole [liteuart0] disabled
[    3.499884] liteeth f0002000.mac eth0: irq 2 slots: tx 2 rx 2 size 2048
[    3.510055] i2c_dev: i2c /dev entries driver
[    3.520573] i2c i2c-0: Not I2C compliant: can't read SCL
[    3.525314] i2c i2c-0: Bus may be unreliable
[    3.577560] litex-mmc f0009000.mmc: LiteX MMC controller initialized.
[    3.623272] NET: Registered PF_INET6 protocol family
[    3.653652] Segment Routing with IPv6
[    3.657870] In-situ OAM (IOAM) with IPv6
[    3.662630] sit: IPv6, IPv4 and MPLS over IPv4 tunneling driver
[    3.683817] NET: Registered PF_PACKET protocol family
[    3.699016] Freeing unused kernel image (initmem) memory: 208K
[    3.704055] Kernel memory protection not selected by kernel config.
[    3.710506] Run /init as init process
Starting syslogd: OK
Starting klogd: OK
Running sysctl: OK
Saving 256 bits of non-creditable seed for next boot
Starting network: OK

Welcome to Buildroot
buildroot login: root
                   __   _
                  / /  (_)__  __ ____ __
                 / /__/ / _ \/ // /\ \ /
                /____/_/_//_/\_,_//_\_\
                      / _ \/ _ \
   __   _ __      _  _\___/_//_/         ___  _
  / /  (_) /____ | |/_/__| | / /____ __ / _ \(_)__ _____  __
 / /__/ / __/ -_)>  </___/ |/ / -_) \ // , _/ (_-</ __/ |/ /
/____/_/\__/\__/_/|_|____|___/\__/_\_\/_/|_/_/___/\__/|___/
                  / __/  |/  / _ \
                 _\ \/ /|_/ / ___/
                /___/_/  /_/_/
  32-bit RISC-V Linux running on LiteX / VexRiscv-SMP.

login[70]: root login on 'console'
root@buildroot:~# 
```

Linux 中也可以访问网络（通过主线内的 liteeth 驱动）：

```shell
$ dmesg | grep liteeth
[    3.499861] liteeth f0002000.mac eth0: irq 2 slots: tx 2 rx 2 size 2048
$ ip link set eth0 up
$ ip a add 192.168.1.50/24 dev eth0
$ ping 192.168.1.100
```

## 其他开发板

除了 Digilent Arty A7，我还做了以下开发板的 LiteX 支持：

- [VCU128](https://github.com/jiegec/litex-boards/tree/vcu128)，支持 UART，SDRAM 和 HBM；以太网因为是 SGMII 暂时无法解决
- [MA703FA-35T](https://github.com/jiegec/litex-boards/tree/ma703fa-35t)，支持 UART，SDRAM，ETH 和 HDMI；尚未测试 SD 卡，估计实现难度不大
- [Alinx AX7021](https://github.com/jiegec/litex-boards/tree/alinx_ax7021)，支持 UART over JTAG 和 HDMI
- [THU Digital Design](https://lab.cs.tsinghua.edu.cn/digital-design/doc/hardware/board/)，基于 @gaoyichuan 的实现，支持 UART，SDRAM，ETH，SD 卡和 VGA
