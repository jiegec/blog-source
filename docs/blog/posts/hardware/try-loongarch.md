---
layout: post
date: 2023-06-12
tags: [loongarch,la64,la32,la32r,qemu]
category: hardware
title: LoongArch 初尝试
---

## 背景

最近应龙芯要求把监控程序移植到了 LoongArch 32 Reduced 架构上，趁此机会体验了一下 LoongArch 相关的软件和系统。

## 在 QEMU 中运行 LoongArch Arch Linux

主页：https://github.com/loongarchlinux

环境：Debian Bookworm

QEMU 启动流程，参考[官方文档](https://mirrors.wsyu.edu.cn/loongarch/archlinux/images/README.html)：

```shell
wget https://mirrors.wsyu.edu.cn/loongarch/archlinux/images/archlinux-xfce4-2023.05.10-loong64.qcow2.zst
zstd -d archlinux-xfce4-2023.05.10-loong64.qcow2.zst
wget https://mirrors.wsyu.edu.cn/loongarch/archlinux/images/QEMU_EFI_7.2.fd
```

然后就可以启动 QEMU 7.2.2 了：

```shell
qemu-system-loongarch64 \
    -m 4G \
    -cpu la464-loongarch-cpu \
    -machine virt \
    -smp 4 \
    -bios ./QEMU_EFI_7.2.fd \
    -serial stdio \
    -device virtio-gpu-pci \
    -net nic -net user \
    -device nec-usb-xhci,id=xhci,addr=0x1b \
    -device usb-tablet,id=tablet,bus=xhci.0,port=1 \
    -device usb-kbd,id=keyboard,bus=xhci.0,port=2 \
    -hda archlinux-xfce4-2023.05.10-loong64.qcow2
```

启动后，可以正常看到 Xfce4 的界面，用 loongarch:loongarch 登录：

![](/images/loongarchlinux.png)

如果不想用 UI，可以先在虚拟机里启动 SSHD，再打开 SSH 转发：

```shell
# in vm
sudo systemctl enable --now sshd
# in host
qemu-system-loongarch64 \
    -m 4G \
    -cpu la464-loongarch-cpu \
    -machine virt \
    -smp 4 \
    -bios ./QEMU_EFI_7.2.fd \
    -nographic \
    -device virtio-net,netdev=net0 \
    -netdev user,id=net0,hostfwd=tcp::4444-:22 \
    -hda archlinux-xfce4-2023.05.10-loong64.qcow2
```

然后就可以通过 SSH 访问 LoongArch 虚拟机了：

```shell
$ ssh loongarch@localhost -p 4444
loongarch@localhost's password:
[loongarch@archlinux ~]$ uname -a
Linux archlinux 6.3.0-12 #1 SMP Thu, 27 Apr 2023 12:24:56 +0000 loongarch64 GNU/Linux
```

## LoongArch 架构

LoongArch 分为三个版本：

1. LoongArch 32 Reduced：精简版本，系统和用户态都是 32 位
2. LoongArch 32：系统和用户态都是 32 位
3. LoongArch 64：系统是 64 位，用户态可以是 32 位，也可以是 64 位

目前上游工具链支持的是 LoongArch 64。

龙芯杯采用的是 LoongArch 32 Reduced 版本，相比 LoongArch 32 的区别有：

1. 删掉了部分算术指令
2. 删掉了位操作指令
3. 删除了边界检查访存指令
4. 删除了 Atomic 原子指令，只保留了 LL+SC
5. 删除了部分浮点运算指令
6. 删除了 IOCSR 访问指令
7. 删除了软件页表遍历指令
8. TLB Refill 异常的相关 CSR（ERA/BADV/PRMD/EHI/ELO0/ELO1/SAVE）不再单独提供一份，而是和其他异常共用
9. 去掉了 STLB，只保留了 MTLB
10. 去掉了部分 CSR
11. 直接映射配置窗口数量砍到了两个
12. 删除了 RAS，PMU，Watchpoint 和硬件调试功能

从用户态来看，主要是差了一些运算指令，需要编译器注意生成的指令范围。内核态上删减的比较多。

## LoongArch 32 Reduced

龙芯提供了一些 LoongArch 32 Reduced 的工具链：

1. GCC + Binutils：[loongarch32r-linux-gnusf-2022-05-20-x86.tar.gz
](https://gitee.com/loongson-edu/la32r-toolchains/releases/download/v0.0.2/loongarch32r-linux-gnusf-2022-05-20-x86.tar.gz)，有源码。
2. GDB：[loongarch32r-linux-gnusf-gdb-x86](https://gitee.com/loongson-edu/la32r-toolchains/releases/download/v0.0.2/loongarch32r-linux-gnusf-gdb-x86)，依赖的动态库较多，建议起一个 CentOS Docker。没有找到源码。
3. QEMU：[qemu-system-loongarch32_centos_x86_64](https://gitee.com/loongson-edu/la32r-QEMU/releases/download/v0.0.1-alpha/qemu-system-loongarch32_centos_x86_64)，依赖的动态库较多，建议克隆下来自己编译：`mkdir build; cd build; ../configure --target-list=loongarch32-softmmu --disable-werror --enable-debug`

在 [la32r-QEMU](https://gitee.com/loongson-edu/la32r-QEMU) 中运行 [la32r-Linux](https://gitee.com/loongson-edu/la32r-Linux/)：

```shell
wget https://gitee.com/loongson-edu/la32r-Linux/releases/download/v0.2/vmlinux
qemu-system-loongarch32 -m 4G -kernel vmlinux -M ls3a5k32 -nographic
loongson32_init: num_nodes 1
loongson32_init: node 0 mem 0x100000000
[    0.000000] Linux version 5.14.0-rc2-g32a8c74db8fc-dirty (mengfanrui@5.5) (loongarch32r-linux-gnusf-gcc (GCC) 8.3.0, GNU ld (GNU Binutils) 2.31.1.20190122) #26 PREEMPT Tue May 31 13:46:54 CST 2022
[    0.000000] Standard 32-bit Loongson Processor probed
[    0.000000] the link is empty!
[    0.000000] Scan bootparam failed
[    0.000000] printk: bootconsole [early0] enabled
[    0.000000] Can't find EFI system table.
[    0.000000] start_pfn=0x0, end_pfn=0x8000, num_physpages:0x8000
[    0.000000] The BIOS Version: (null)
[    0.000000] Initrd not found or empty - disabling initrd
[    0.000000] CPU0 revision is: 00004200 (Loongson-32bit)
[    0.000000] Primary instruction cache 8kB, 2-way, VIPT, linesize 16 bytes.
[    0.000000] Primary data cache 8kB, 2-way, VIPT, no aliases, linesize 16 bytes
[    0.000000] Zone ranges:
[    0.000000]   DMA32    [mem 0x0000000000000000-0x00000000ffffffff]
[    0.000000]   Normal   empty
[    0.000000] Movable zone start for each node
[    0.000000] Early memory node ranges
[    0.000000]   node   0: [mem 0x0000000000000000-0x0000000007ffffff]
[    0.000000] Initmem setup node 0 [mem 0x0000000000000000-0x0000000007ffffff]
[    0.000000] eentry = 0xa0210000,tlbrentry = 0xa0201000
[    0.000000] Built 1 zonelists, mobility grouping on.  Total pages: 32480
[    0.000000] Kernel command line: earlycon
[    0.000000] Dentry cache hash table entries: 16384 (order: 4, 65536 bytes, linear)
[    0.000000] Inode-cache hash table entries: 8192 (order: 3, 32768 bytes, linear)
[    0.000000] mem auto-init: stack:off, heap alloc:off, heap free:off
[    0.000000] Memory: 117732K/131072K available (4926K kernel code, 1114K rwdata, 944K rodata, 2480K init, 473K bss, 13340K reserved, 0K cma-reserved)
[    0.000000] SLUB: HWalign=64, Order=0-3, MinObjects=0, CPUs=1, Nodes=1
[    0.000000] rcu: Preemptible hierarchical RCU implementation.
[    0.000000] rcu:     RCU event tracing is enabled.
[    0.000000]  Trampoline variant of Tasks RCU enabled.
[    0.000000]  Tracing variant of Tasks RCU enabled.
[    0.000000] rcu: RCU calculated value of scheduler-enlistment delay is 25 jiffies.
[    0.000000] NR_IRQS: 320
[    0.000000] ------------[ cut here ]------------
[    0.000000] WARNING: CPU: 0 PID: 0 at kernel/time/clockevents.c:38 cev_delta2ns.isra.15+0x17c/0x1c8
[    0.000000] CPU: 0 PID: 0 Comm: swapper Not tainted 5.14.0-rc2-g32a8c74db8fc-dirty #26
[    0.000000] Stack :
[    0.000000] Call Trace:
[    0.000000]
[    0.000000]
[    0.000000] random: get_random_bytes called from print_oops_end_marker+0x30/0x68 with crng_init=0
[    0.000000] ---[ end trace a8581308883ff14d ]---
[    0.000000] Constant clock event device register
[    0.000000] clocksource: Constant: mask: 0xffffffffffffffff max_cycles: 0xffffffffffffffff, max_idle_ns: 9007199254740991 ns
[    0.000000] Constant clock source device register
[    0.752000] Console: colour dummy device 80x25
[    0.816000] printk: console [tty0] enabled
[    0.856000] printk: bootconsole [early0] disabled
[    0.000000] Linux version 5.14.0-rc2-g32a8c74db8fc-dirty (mengfanrui@5.5) (loongarch32r-linux-gnusf-gcc (GCC) 8.3.0, GNU ld (GNU Binutils) 2.31.1.20190122) #26 PREEMPT Tue May 31 13:46:54 CST 2022
[    0.000000] Standard 32-bit Loongson Processor probed
[    0.000000] the link is empty!
[    0.000000] Scan bootparam failed
[    0.000000] printk: bootconsole [early0] enabled
[    0.000000] Can't find EFI system table.
[    0.000000] start_pfn=0x0, end_pfn=0x8000, num_physpages:0x8000
[    0.000000] The BIOS Version: (null)
[    0.000000] Initrd not found or empty - disabling initrd
[    0.000000] CPU0 revision is: 00004200 (Loongson-32bit)
[    0.000000] Primary instruction cache 8kB, 2-way, VIPT, linesize 16 bytes.
[    0.000000] Primary data cache 8kB, 2-way, VIPT, no aliases, linesize 16 bytes
[    0.000000] Zone ranges:
[    0.000000]   DMA32    [mem 0x0000000000000000-0x00000000ffffffff]
[    0.000000]   Normal   empty
[    0.000000] Movable zone start for each node
[    0.000000] Early memory node ranges
[    0.000000]   node   0: [mem 0x0000000000000000-0x0000000007ffffff]
[    0.000000] Initmem setup node 0 [mem 0x0000000000000000-0x0000000007ffffff]
[    0.000000] eentry = 0xa0210000,tlbrentry = 0xa0201000
[    0.000000] Built 1 zonelists, mobility grouping on.  Total pages: 32480
[    0.000000] Kernel command line: earlycon
[    0.000000] Dentry cache hash table entries: 16384 (order: 4, 65536 bytes, linear)
[    0.000000] Inode-cache hash table entries: 8192 (order: 3, 32768 bytes, linear)
[    0.000000] mem auto-init: stack:off, heap alloc:off, heap free:off
[    0.000000] Memory: 117732K/131072K available (4926K kernel code, 1114K rwdata, 944K rodata, 2480K init, 473K bss, 13340K reserved, 0K cma-reserved)
[    0.000000] SLUB: HWalign=64, Order=0-3, MinObjects=0, CPUs=1, Nodes=1
[    0.000000] rcu: Preemptible hierarchical RCU implementation.
[    0.000000] rcu:     RCU event tracing is enabled.
[    0.000000]  Trampoline variant of Tasks RCU enabled.
[    0.000000]  Tracing variant of Tasks RCU enabled.
[    0.000000] rcu: RCU calculated value of scheduler-enlistment delay is 25 jiffies.
[    0.000000] NR_IRQS: 320
[    0.000000] ------------[ cut here ]------------
[    0.000000] WARNING: CPU: 0 PID: 0 at kernel/time/clockevents.c:38 cev_delta2ns.isra.15+0x17c/0x1c8
[    0.000000] CPU: 0 PID: 0 Comm: swapper Not tainted 5.14.0-rc2-g32a8c74db8fc-dirty #26
[    0.000000] Stack :
[    0.000000] Call Trace:
[    0.000000]
[    0.000000]
[    0.000000] random: get_random_bytes called from print_oops_end_marker+0x30/0x68 with crng_init=0
[    0.000000] ---[ end trace a8581308883ff14d ]---
[    0.000000] Constant clock event device register
[    0.000000] clocksource: Constant: mask: 0xffffffffffffffff max_cycles: 0xffffffffffffffff, max_idle_ns: 9007199254740991 ns
[    0.000000] Constant clock source device register
[    0.752000] Console: colour dummy device 80x25
[    0.816000] printk: console [tty0] enabled
[    0.856000] printk: bootconsole [early0] disabled
[    1.024000] random: fast init done
[    1.240000] Calibrating delay loop... 0.65 BogoMIPS (lpj=1312)
[    1.444000] pid_max: default: 32768 minimum: 301
[    1.860000] Mount-cache hash table entries: 1024 (order: 0, 4096 bytes, linear)
[    1.868000] Mountpoint-cache hash table entries: 1024 (order: 0, 4096 bytes, linear)
[   10.740000] rcu: Hierarchical SRCU implementation.
[   13.408000] devtmpfs: initialized
[   15.948000] clocksource: jiffies: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 7645041785100000 ns
[   15.980000] futex hash table entries: 256 (order: -1, 3072 bytes, linear)
[   16.948000] NET: Registered PF_NETLINK/PF_ROUTE protocol family
[   28.832000] pps_core: LinuxPPS API ver. 1 registered
[   28.840000] pps_core: Software ver. 5.3.6 - Copyright 2005-2007 Rodolfo Giometti <giometti@linux.it>
[   32.492000] clocksource: Switched to clocksource Constant
[   32.492000] FS-Cache: Loaded
[   32.492000] NET: Registered PF_INET protocol family
[   32.492000] IP idents hash table entries: 2048 (order: 2, 16384 bytes, linear)
[   32.492000] tcp_listen_portaddr_hash hash table entries: 512 (order: 0, 4096 bytes, linear)
[   32.492000] TCP established hash table entries: 1024 (order: 0, 4096 bytes, linear)
[   32.492000] TCP bind hash table entries: 1024 (order: 0, 4096 bytes, linear)
[   32.492000] TCP: Hash tables configured (established 1024 bind 1024)
[   32.492000] UDP hash table entries: 256 (order: 0, 4096 bytes, linear)
[   32.492000] UDP-Lite hash table entries: 256 (order: 0, 4096 bytes, linear)
[   32.492000] NET: Registered PF_UNIX/PF_LOCAL protocol family
[   32.492000] workingset: timestamp_bits=14 max_order=15 bucket_order=1
[   32.492000] IPMI message handler: version 39.2
[   32.492000] ipmi device interface
[   32.492000] ipmi_si: IPMI System Interface driver
[   32.492000] ipmi_si: Unable to find any System Interface(s)
[   32.492000] Serial: 8250/16550 driver, 16 ports, IRQ sharing enabled
[   32.492000] 1fe001e0.serial: ttyS0 at MMIO 0x1fe001e0 (irq = 18, base_baud = 2062500) is a 16550A
[   32.492000] printk: console [ttyS0] enabled
[   32.492000] ls1a-nand driver initializing
[   32.492000] ls1a_nand : mtd struct base address is a102b800
[   32.492000] info->data_buff===================0x81130000
[   32.492000] nand: No NAND device found
[   32.492000] ls1a-nand 1fe78000.nand: failed to scan nand
[   32.492000] ITC MAC 10/100M Fast Ethernet Adapter driver 1.0 init
[   32.492000] libphy: Fixed MDIO Bus: probed
[   32.492000] mousedev: PS/2 mouse device common for all mice
[   32.492000] IR MCE Keyboard/mouse protocol handler initialized
[   32.492000] hid: raw HID events driver (C) Jiri Kosina
[   32.492000] NET: Registered PF_INET6 protocol family
[   32.492000] random: crng init done
[   32.492000] Segment Routing with IPv6
[   32.492000] sit: IPv6, IPv4 and MPLS over IPv4 tunneling driver
[   32.492000] Warning: unable to open an initial console.
[   32.492000] Freeing unused kernel image (initmem) memory: 2480K
[   32.492000] This architecture does not have kernel memory protection.
[   32.492000] Run /init as init process

Processing /etc/profile... Done

/ #
```

我在 la32r-QEMU 的基础上，把 LoongArch 32 Reduced 的支持部分移植到了 QEMU 8.0.0 上：<https://github.com/jiegec/qemu/commits/la32r-8.0.0>。

## 虚实地址映射

LoongArch 有两种虚实地址映射方法：

1. 直接地址翻译模式（CSR.CRMD.DA=1，CSR.CRMD.PG=0），此时物理地址等于虚拟地址，如果虚拟地址位数更多，则截断高位。
2. 映射地址翻译模式（CSR.CRMD.DA=0，CSR.CRMD.PG=1），此时按照顺序进行下面的翻译：
    1. 直接映射模式：CSR.DMW 定义了四个（LA32R 只有两个）窗口，这些窗口内的虚拟地址与物理地址是平移的关系。
    2. 页表映射模式：如果没有匹配上直接映射模式，则会查询 TLB。虽说是页表映射模式，但依然是 MIPS 传统的 TLB 做法。

相比 MIPS 来讲，LoongArch 的地址映射还是容易理解一些。

从复位中出来的时候，CSR.CRMD.DA=1，CSR.CRMD.PG=0，意味着是直接地址翻译模式。PC 是 0x1C000000，由于是直接地址翻译模式，所以物理地址也是 0x1C000000。

在遇到 TLB Refill 异常的时候，处理器会跳到 CSR.TLBRENTRY 的地址，同时进入直接地址翻译模式（CSR.CRMD.DA=1，CSR.CRMD.PG=0），意味着虚拟地址直接对应物理地址，所以此时需要做好相应的准备。LoongArch 提供了 lddir 和 ldpte 指令来加快页表到 TLB 项目的查询性能，例如下面是 [EDK2 的 TLB Refill 异常处理函数](https://github.com/tianocore/edk2-platforms/blob/4c3e742e931538a1ee6cb3b571b1281e7fba2564/Platform/Loongson/LoongArchQemuPkg/Library/MmuLib/Mmu.S#L37)：

```asm
ASM_PFX(HandleTlbRefill):
  csrwr T0, LOONGARCH_CSR_TLBRSAVE
  csrrd T0, LOONGARCH_CSR_PGD
  lddir T0, T0, 3   #Put pud BaseAddress into T0
  lddir T0, T0, 2   #Put pmd BaseAddress into T0
  lddir T0, T0, 1   #Put pte BaseAddress into T0
  ldpte T0, 0
  ldpte T0, 1
  tlbfill
  csrrd T0, LOONGARCH_CSR_TLBRSAVE
  ertn
```

比较有意思的是，csrwr 指令会把旧的 CSR 值写回到通用寄存器里，所以看起来名字是 write，其实是 swap。为了方便查表，还给用户态和内核态分别一个页表基地址：CSR.PGDL，CSR.PGDH，根据异常的高位判断要选择哪一个页表基地址。

