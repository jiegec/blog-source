---
layout: post
date: 2023-05-06 22:16:00 +0800
tags: [linux,vivado]
category: software
title: Linux 6.2.13+ 引入的 BUG 导致 Vivado 无法识别 FPGA 
---

## TLDR

简单来说，Linux 6.2.13 引入的 commit：

```
commit 0d30989fe9a176565d360376d4bc2ea1c61cbbac
Author: Liam R. Howlett <Liam.Howlett@oracle.com>
Date:   Fri Apr 14 14:59:19 2023 -0400

    mm/mmap: regression fix for unmapped_area{_topdown}
    
    commit 58c5d0d6d522112577c7eeb71d382ea642ed7be4 upstream.
    
    The maple tree limits the gap returned to a window that specifically fits
    what was asked.  This may not be optimal in the case of switching search
    directions or a gap that does not satisfy the requested space for other
    reasons.  Fix the search by retrying the operation and limiting the search
    window in the rare occasion that a conflict occurs.
    
    Link: https://lkml.kernel.org/r/20230414185919.4175572-1-Liam.Howlett@oracle.com
    Fixes: 3499a13168da ("mm/mmap: use maple tree for unmapped_area{_topdown}")
    Signed-off-by: Liam R. Howlett <Liam.Howlett@oracle.com>
    Reported-by: Rick Edgecombe <rick.p.edgecombe@intel.com>
    Cc: <stable@vger.kernel.org>
    Signed-off-by: Andrew Morton <akpm@linux-foundation.org>
    Signed-off-by: Greg Kroah-Hartman <gregkh@linuxfoundation.org>
```

修复了 BUG 的同时，引入了新的 BUG，导致 MAP_32BIT 有时无法工作，而 Xilinx 的 Digilent 下载器代码使用了这个参数，导致 mmap 失败，无法识别 FPGA。

## 背景

事情的背景是，@vowstar 升级内核到 6.2.14 以后，发现 Vivado 找不到 FPGA 了，重启回到 6.2.12 就好了。

## 排查

因为升级了内核，第一反应是不是 ftdi_sio 驱动的问题。比对了一下二者的 dmesg 日志，发现 Linux 6.2.12 会显示 `ftdi_sio: device disconnected` 消息：这是因为 FPGA 下载器内置的是 FTDI 芯片，它支持多种模式，默认情况下，内核检测到设备以后，会由 ftdi_sio 驱动初始化为串口模式，创建 `/dev/ttyUSB*` 设备；而 Vivado 需要用的是 MPSSE 模式，从而使用 JTAG 协议与 FPGA 通讯。这与串口模式冲突，因此 Vivado 要做的事情，首先是把内核模块 detach，也就是不再占用 USB 设备，然后再让 FTDI 芯片进入 MPSSE 模式。

沿着这个思路，首先想到的是权限问题：默认情况下，USB 设备权限比较严格，所以 Vivado 在安装的时候，会安装 udev rule，把 Digilent 下载器的 usb 设备文件的权限改为 666，这样就允许所有用户访问 USB 设备。但是检查了一下，/dev/bus/usb 下的设备文件权限是正确的：

```shell
kernel 6.2.12: crw-rw-rw- 1 root usb 189, 271 May  6 15:31 /dev/bus/usb/003/016
kernel 6.2.14: crw-rw-rw- 1 root usb 189, 262 May  6 15:32 /dev/bus/usb/003/016
```

这时候就觉得很蹊跷，只更新了内核，其他都没有变，为什么行为就会不同。于是翻了翻 Linux 内核的 ChangeLog，因为 6.2.12 是好的，6.2.14 是不工作的，所以只需要看两者之间的 changelog：

- [6.2.13](https://cdn.kernel.org/pub/linux/kernel/v6.x/ChangeLog-6.2.13)
- [6.2.14](https://cdn.kernel.org/pub/linux/kernel/v6.x/ChangeLog-6.2.14)

以 ftdi 或 usb 为关键词搜索，只有一个看起来有一些相关的 commit：`USB: serial: option: add UNISOC vendor and TOZED LT70C product`，但是仔细一看，只是添加了新的 VID/PID，也没有和 Digilent 下载器冲突。

这时候，就觉得不是 Linux 的问题了。按照这个思路，继续控制变量法，看看是不是 FTDI 芯片出了问题。这时候就祭出了 OpenOCD，看看 OpenOCD 能否配置 FTDI 芯片进入 MPSSE 模式，并且找到 FPGA。试了一下，还真可以，ftdi_sio 正常 detach，然后 OpenOCD 也找到 FPGA 了。

但此时再打开 Vivado，还是找不到设备，说明不是 MPSSE 模式的问题。考虑到 Vivado 访问硬件的进程是 hw_server，想到能不能看看 hw_server 的日志。

运行 hw_server，打印所有日志类型：

```shell
$ hw_server -L- -l alloc,eventcore,waitpid,events,protocol,context,children,discovery,asyncreq,proxy,tcflog,elf,stack,plugin,shutdown,disasm,jtag2,jtag,pcie,slave,dpc
```

这里 `-L-` 表示输出日志到 stderr，后面的 `-l` 一串参数就是各种日志开关。在两个内核里都运行一次，比对日志，发现了不同：

```shell
Success (6.2.12):
TCF 08:39:37.247: jtagpoll: add node 0xxxxxxxx(jsn-JTAG-SMT2NC-XXXXXXXXXXXX)
TCF 08:39:37.247: Node 000000FF, added jsn-JTAG-SMT2NC-XXXXXXXXXXXX

Failed (6.2.14):
TCF 08:45:12.385: jtagpoll: cannot get port description list: ftdidb_lock failed: FTDMGR wasn't properly initialized
TCF 08:45:12.391: jtagpoll: cannot get port description list: JTAG device enumeration failed: Initialization of the DPCOMM library failed.
```

终于看到了错误信息：`jtagpoll: cannot get port description list: ftdidb_lock failed: FTDMGR wasn't properly initialized`。把这个作为关键词一搜索，果然有别人也遇到了同样的问题：

- [XSDB fails with "ftdidb_lock failed: FTDMGR wasn't properly initialized"](https://support.xilinx.com/s/article/000033531?language=en_US)
- [Linux 多用户环境下 Vivado 无法连接 Digilent JTAG 适配器的解决方法](https://blog.t123yh.xyz:2/index.php/archives/1013)

尝试了第一篇文章的解决方案，没有效果。第二篇文章指出的问题是，多用户环境下，多个用户抢同一个文件，然后出现权限问题，所以要删掉文件再启动。按照第二篇文档的方法尝试了一下，也没有解决问题。

但是第二篇文章给出了一个调试方法：运行 Digilent 提供的 dadutil 程序，看看它是否可以识别下载器，果然复现出问题了：

```shell
$ dadutil enum
ERROR: DmgrSetNetworkEnumTimeout failed, erc = 3090
$ dadutil enum
Found 1 device(s)
$ dadutil enum
Found 1 device(s)
$ dadutil enum
ERROR: DmgrSetNetworkEnumTimeout failed, erc = 3090
```

到这里多次尝试，发现有三分之一的概率会失败，但已经足够解释为什么 hw_server 不工作了：大概率它也调用了 Digilent 提供的代码，得到了同样的结果，所以失败了。

上面第二篇文章用 strace 的方法找到了问题，照葫芦画瓢，用 strace 找到出错的日志：

```shell
$ strace dadutil enum
openat(AT_FDCWD, "/dev/shm/digilent-adept2-mtx-ftdmgr", O_RDWR|O_NOFOLLOW|O_CLOEXEC) = 7
ftruncate(7, 4)                         = 0
mmap(NULL, 4, PROT_READ|PROT_WRITE, MAP_SHARED|MAP_32BIT, 7, 0) = -1 ENOMEM (Cannot allocate memory)
close(7)                                = 0
```

可以发现问题是返回了 ENOMEM，这就很奇怪了，`/dev/shm` 是个 tmpfs，还有很多空间，怎么会返回 ENOMEM 呢？

## 柳暗花明又一村

按照新线索继续研究：mmap 返回了不应该返回的错误，那是不是 6.2.13 或 6.2.14 引入了相关改动呢？一查，还真有：

```diff
# https://cdn.kernel.org/pub/linux/kernel/v6.x/ChangeLog-6.2.13
commit 0d30989fe9a176565d360376d4bc2ea1c61cbbac
Author: Liam R. Howlett <Liam.Howlett@oracle.com>
Date:   Fri Apr 14 14:59:19 2023 -0400

    mm/mmap: regression fix for unmapped_area{_topdown}
    
    commit 58c5d0d6d522112577c7eeb71d382ea642ed7be4 upstream.
    
    The maple tree limits the gap returned to a window that specifically fits
    what was asked.  This may not be optimal in the case of switching search
    directions or a gap that does not satisfy the requested space for other
    reasons.  Fix the search by retrying the operation and limiting the search
    window in the rare occasion that a conflict occurs.
    
    Link: https://lkml.kernel.org/r/20230414185919.4175572-1-Liam.Howlett@oracle.com
    Fixes: 3499a13168da ("mm/mmap: use maple tree for unmapped_area{_topdown}")
    Signed-off-by: Liam R. Howlett <Liam.Howlett@oracle.com>
    Reported-by: Rick Edgecombe <rick.p.edgecombe@intel.com>
    Cc: <stable@vger.kernel.org>
    Signed-off-by: Andrew Morton <akpm@linux-foundation.org>
    Signed-off-by: Greg Kroah-Hartman <gregkh@linuxfoundation.org>
```

和 mmap 相关，点进[邮件链接](https://lkml.kernel.org/r/20230414185919.4175572-1-Liam.Howlett@oracle.com)看看，发现有人提出这个 commit 虽然修复了一个 BUG，但是引入了新的 BUG：

```
* Re: [PATCH v2] mm/mmap: Regression fix for unmapped_area{_topdown}
  2023-04-14 18:59   ` [PATCH v2] " Liam R. Howlett
  2023-04-14 19:09     ` Andrew Morton
@ 2023-04-29 14:32     ` Tad
  2023-04-30 22:41       ` Michael Keyes
  1 sibling, 1 reply; 18+ messages in thread
From: Tad @ 2023-04-29 14:32 UTC (permalink / raw)
  To: liam.howlett; +Cc: akpm, linux-kernel, linux-mm, rick.p.edgecombe

This reintroduces the issue described in
https://lore.kernel.org/linux-mm/cb8dc31a-fef2-1d09-f133-e9f7b9f9e77a@sony.com/

Linux 6.2.13 can no longer successfully run the mmap-test reproducer linked
there.

Linux 6.2.12 passes.

Regards,
Tad.
```

再继续跟踪上面的[链接](https://lore.kernel.org/linux-mm/cb8dc31a-fef2-1d09-f133-e9f7b9f9e77a@sony.com/)，赫然看到里面的错误日志里，也出现了类似的 mmap 调用：

```shell
> mmap(NULL, 131072, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS|MAP_32BIT, -1, 0) = 0x40720000
> mmap(NULL, 131072, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS|MAP_32BIT, -1, 0) = 0x4124e000
> mmap(NULL, 131072, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS|MAP_32BIT, -1, 0) = -1 ENOMEM (Cannot allocate memory)
> dex2oatd F 03-01 10:32:33 74063 74063 mem_map_arena_pool.cc:65] Check failed: map.IsValid() Failed anonymous mmap((nil), 131072, 0x3, 0x22, -1, 0): Cannot allocate memory. See process maps in the log.
```

再看看上面 `dadutil enum` 报错的 mmap 日志：

```shell
mmap(NULL, 4, PROT_READ|PROT_WRITE, MAP_SHARED|MAP_32BIT, 7, 0) = -1 ENOMEM (Cannot allocate memory)
```

赫然也是 MAP_32BIT，结果也是 ENOMEM，那说明就是这个问题了。结合邮件列表的其他讨论，基本可以确认是作者忽略了 MAP_32BIT 的情况，所以出现了问题。

## 总结

这就是整个 Debug 流程，从 Vivado 找不到 FPGA 的表象，到内在的 Linux 内核 BUG，看起来毫不相关，但却能发现背后的逻辑。

我和 @vowstar 一起完成了整个调试的流程，学到了许多，因此写了这篇博客。