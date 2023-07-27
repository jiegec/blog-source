---
layout: post
date: 2023-05-06
tags: [linux,vivado]
categories:
    - software
---

# How a Linux 6.2.13 BUG stops Vivado from recognizing FPGA

[中文版本](linux-regression-vivado.md)

## TLDR

In short, the commit introduced by Linux 6.2.13:

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


While fixing a BUG, a new BUG is introduced, causing MAP_32BIT to fail to work sometimes, and Xilinx's Digilent driver uses this parameter, causing mmap to fail and unable to recognize the FPGA.

The new BUG has been fixed in [[PATCH v2] maple_tree: Make maple state reusable after mas_empty_area()](https://lore.kernel.org/linux-mm/20230505145829.74574-1-zhangpeng.00@bytedance.com/).

<!-- more -->

## Background

The background is that after @vowstar upgraded the kernel to 6.2.14, he found that Vivado could not find the FPGA. But restarting and switching to 6.2.12, it works.

## Troubleshooting

Because the kernel has been upgraded, the first reaction is whether it is a problem with the ftdi_sio driver. Comparing the dmesg logs of the two kernel versions, We found that Linux 6.2.12 will display `ftdi_sio: device disconnected` message: this is because the FPGA programmer has a built-in FTDI chip, which supports multiple modes. By default, after the kernel detects the usb device, the ftdi_sio driver will initialize the FTDI chip to the serial port mode to create a `/dev/ttyUSB*` device; and Vivado needs to use the MPSSE mode to communicate with the FPGA using the JTAG protocol. MPSSE mode conflicts with the serial port mode, so Vivado has to detach the kernel module so that it no longer occupies the USB device, and then let the FTDI chip enter MPSSE mode.

Following this line of thought, the first thing that comes to mind is the permission issue: by default, the USB device permissions are strict, so when Vivado is installed, it will install udev rules, to change the permissions of the usb device file of the Digilent programmer to 666, so that all users are allowed to access USB devices. But after checking, the device file permissions under /dev/bus/usb are correct:


```shell
kernel 6.2.12: crw-rw-rw- 1 root usb 189, 271 May  6 15:31 /dev/bus/usb/003/016
kernel 6.2.14: crw-rw-rw- 1 root usb 189, 262 May  6 15:32 /dev/bus/usb/003/016
```

At this time, we feel very strange. Only the kernel has been updated, and nothing else has changed. Why is the behavior different? So we looked through the ChangeLog of the Linux kernel, because 6.2.12 is good, while 6.2.14 is not working, so you only need to look at the changelog between the two:

- [6.2.13](https://cdn.kernel.org/pub/linux/kernel/v6.x/ChangeLog-6.2.13)
- [6.2.14](https://cdn.kernel.org/pub/linux/kernel/v6.x/ChangeLog-6.2.14)

Searching for keywords such as ftdi or usb, only one commit seems to be related: `USB: serial: option: add UNISOC vendor and TOZED LT70C product`, but after a closer look, it only adds a new VID/PID, and it has no conflict with Digilent programmer.

At this time, we feel that it is not a Linux problem. We continue to control the variables, by seeing if there is something wrong with the FTDI chip. At this time, OpenOCD was used to see if OpenOCD can configure the FTDI chip to enter MPSSE mode and find the FPGA. We tried it, it worked, ftdi_sio detached normally, and OpenOCD also found FPGA.

But at this time, when Vivado is opened again, the FPGA is still not found, indicating that it is not a problem in MPSSE mode. Considering that the process that Vivado accesses the hardware is hw_server, we wonder if we can look at the log of hw_server.

Run hw_server, printing all log types:

```shell
$ hw_server -L- -l alloc,eventcore,waitpid,events,protocol,context,children,discovery,asyncreq,proxy,tcflog,elf,stack,plugin,shutdown,disasm,jtag2,jtag,pcie,slave,dpc
```

Here `-L-` means to output the log to stderr, and the following `-l` string of parameters are various log switches. It is ran on both kernels, and the difference is found by comparing the logs:

```shell
Success (6.2.12):
TCF 08:39:37.247: jtagpoll: add node 0xxxxxxxx(jsn-JTAG-SMT2NC-XXXXXXXXXXXX)
TCF 08:39:37.247: Node 000000FF, added jsn-JTAG-SMT2NC-XXXXXXXXXXXX

Failed (6.2.14):
TCF 08:45:12.385: jtagpoll: cannot get port description list: ftdidb_lock failed: FTDMGR wasn't properly initialized
TCF 08:45:12.391: jtagpoll: cannot get port description list: JTAG device enumeration failed: Initialization of the DPCOMM library failed.
```

Finally saw the error message: `jtagpoll: cannot get port description list: ftdidb_lock failed: FTDMGR wasn't properly initialized`. Use it as a keyword to search, and sure enough, someone else has encountered the same problem:

- [XSDB fails with "ftdidb_lock failed: FTDMGR wasn't properly initialized"](https://support.xilinx.com/s/article/000033531?language=en_US)
- [Linux 多用户环境下 Vivado 无法连接 Digilent JTAG 适配器的解决方法 (Solution to Vivado unable to connect to Digilent JTAG adapter in Linux multi-user environment)](https://blog.t123yh.xyz:2/index.php/archives/1013)

We tried the solution from the first post, it didn't work. The problem pointed out in the second article is that in a multi-user environment, multiple users use the same file, and then there is a permission problem, so the file must be deleted. We tried the method in the second document, but it didn't solve the problem.

But the second article gives a debugging method: run the dadutil program provided by Digilent to see if it can recognize the programmer, and the problem reappears:

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

We have tried many times here and found that there is a one-third probability of failure, but it is enough to explain why hw_server does not work: there is a high probability that it also calls the code provided by Digilent and gets the same result, so it fails.

The second article above used strace to find the problem, so we use strace to locate the error:

```shell
$ strace dadutil enum
openat(AT_FDCWD, "/dev/shm/digilent-adept2-mtx-ftdmgr", O_RDWR|O_NOFOLLOW|O_CLOEXEC) = 7
ftruncate(7, 4)                         = 0
mmap(NULL, 4, PROT_READ|PROT_WRITE, MAP_SHARED|MAP_32BIT, 7, 0) = -1 ENOMEM (Cannot allocate memory)
close(7)                                = 0
```

The problem is that ENOMEM is returned, which is very strange, because `/dev/shm` is a tmpfs, and there is still a lot of space, how can it return ENOMEM?

## Found the culprit

Continue to research according to new clues: mmap returns an error that should not be returned, is that 6.2.13 or 6.2.14 introduced related changes? After checking, there are really:

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

It is related to mmap, click on the [email link](https://lkml.kernel.org/r/20230414185919.4175572-1-Liam.Howlett@oracle.com) to have a look, and found that this commit was proposed to fix a BUG, but introduced a new BUG:

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

Continue to follow the above [link](https://lore.kernel.org/linux-mm/cb8dc31a-fef2-1d09-f133-e9f7b9f9e77a@sony.com/), and you can see that in the error log inside, there is also a similar mmap call:

```shell
> mmap(NULL, 131072, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS|MAP_32BIT, -1, 0) = 0x40720000
> mmap(NULL, 131072, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS|MAP_32BIT, -1, 0) = 0x4124e000
> mmap(NULL, 131072, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS|MAP_32BIT, -1, 0) = -1 ENOMEM (Cannot allocate memory)
> dex2oatd F 03-01 10:32:33 74063 74063 mem_map_arena_pool.cc:65] Check failed: map.IsValid() Failed anonymous mmap((nil), 131072, 0x3, 0x22, -1, 0): Cannot allocate memory. See process maps in the log.
```

Look at the mmap log reported above by `dadutil enum`:

```shell
mmap(NULL, 4, PROT_READ|PROT_WRITE, MAP_SHARED|MAP_32BIT, 7, 0) = -1 ENOMEM (Cannot allocate memory)
```

The parameter also contains MAP_32BIT, and the result is also ENOMEM. Combined with other discussions on the mailing list, it can be basically confirmed that the author ignored the situation of MAP_32BIT, and the BUG is introduced by the commit.

After reverting the commit from Linux 6.2.14, the problem is gone.

## Summary

This is the whole debugging process. From the fact that Vivado can't find the FPGA, to the internal Linux kernel BUG, they seem irrelevant, but we can find the connection behind the scene.

I went through the whole debugging process with @vowstar and learned a lot, hence the blog post.
