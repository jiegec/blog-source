---
layout: post
date: 2023-10-03
tags: [windows,wsl,wsl2,linux]
categories:
    - os
---

# WSL2 内部实现探究

## 背景

最近看到 [Windows Subsystem for Linux September 2023 update](https://devblogs.microsoft.com/commandline/windows-subsystem-for-linux-september-2023-update/) 声称 WSL2 最新的预览版本支持让 Linux 和 Windows 一定程度上共享网络地址空间，就像 WSL1 那样：

- IPv6 support
- Connect to Windows servers from within Linux using the localhost address 127.0.0.1
- Connect to WSL directly from your local area network (LAN)
- Improved networking compatibility for VPNs
- Multicast support

因此比较想知道这是怎么做到的，但目前我手上还没有预览版本的 windows，因此目前先研究 WSL2 已有的功能是如何实现的，未来再回来更新这一部分。

<!-- more -->

## WSL2

WSL1 实现的是 proxy kernel 模式，虽然跑的是 linux 程序，但其实还是 windows 内核，中间包了一层 syscall 的转换，没有开一个虚拟机。这个套路和 MinGW/Cygwin 类似，只不过是在不同层次上做的 syscall 转换。

WSL2 则是回归传统的虚拟机模式，基于 Hyper-V 开了虚拟机，然后做了比较多的集成，尽量保证和原来 WSL1 的功能一致。但此时就是两个分立的系统了，在虚拟机里跑一份 Linux 内核，这个内核有微软自己的一些修改，可以在 [microsoft/WSL2-Linux-Kernel](https://github.com/microsoft/WSL2-Linux-Kernel) 里看到。除此之外，我们看不到 bootloader，虚拟机启动的流程都被隐藏起来了，所以这里就有很多可以做骚操作的地方了，例如植入一些程序，提前做一些配置等等。

下面尝试探究 WSL2 的一些功能背后的原理。

### drvfs

drvfs 指的是从 WSL 里面访问 Windows 的文件系统，例如 C 盘会被映射到 `/mnt/c` 下面。在 WSL2 下面，用 `mount` 命令可以看到，它实际上是一个 9pfs：

```shell
drvfs on /mnt/c type 9p (rw,noatime,dirsync,aname=drvfs;path=C:\;uid=1000;gid=1000;symlinkroot=/mnt/,mmap,access=client,msize=262144,trans=virtio)
```

9pfs 类似 NFS，是一个远程的文件系统访问协议，只不过不走网络，而是走的 virtio（`trans=virtio`），从 PCIe 总线上也能看到一堆 virtio 设备：

```shell
2a99:00:00.0 System peripheral: Red Hat, Inc. Virtio file system (rev 01)
        Subsystem: Red Hat, Inc. Virtio file system
        Kernel driver in use: virtio-pci
lspci: Unable to load libkmod resources: error -2
47ee:00:00.0 SCSI storage controller: Red Hat, Inc. Virtio 1.0 filesystem (rev 01)
        Subsystem: Red Hat, Inc. Virtio 1.0 filesystem
        Kernel driver in use: virtio-pci
7cd4:00:00.0 SCSI storage controller: Red Hat, Inc. Virtio 1.0 filesystem (rev 01)
        Subsystem: Red Hat, Inc. Virtio 1.0 filesystem
        Kernel driver in use: virtio-pci
b9dc:00:00.0 SCSI storage controller: Red Hat, Inc. Virtio 1.0 console (rev 01)
        Subsystem: Red Hat, Inc. Virtio 1.0 console
        Kernel driver in use: virtio-pci
e7ba:00:00.0 SCSI storage controller: Red Hat, Inc. Virtio 1.0 filesystem (rev 01)
        Subsystem: Red Hat, Inc. Virtio 1.0 filesystem
        Kernel driver in use: virtio-pci
```

### 运行 Windows 程序

在 WSL2 里，可以运行 Windows 上的程序，这是通过 `binfmt_misc` 实现的：

```shell
$ cat /proc/sys/fs/binfmt_misc/WSLInterop
enabled
interpreter /init
flags: PF
offset 0
magic 4d5a
```

当 Linux 尝试执行 PE 文件的时候，匹配上 `magic 4d5a`（`MZ`），就会用 `/init` 去执行它。之后就由 `/init` 和 Windows 进行通信，把命令和参数传过去，最后在 Windows 上执行。

`/init` 则是一个 WSL2 自带的程序：它会作为 WSL2 内部的 init 程序，也就是 PID 1。同时它会跑多个进程，虽然都是用同一个可执行文件：

```shell
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0   2324  1512 ?        Sl   23:20   0:00 /init
root         4  0.0  0.0   2324     4 ?        Sl   23:20   0:00 plan9 --control-socket 5 --log-level 4 --server-fd 6 --pipe-fd 8 --log-truncate
root         7  0.0  0.0   2332   112 ?        Ss   23:20   0:00 /init
root         8  0.0  0.0   2348   116 ?        S    23:20   0:00 /init
```

WSL2 可以打开 systemd，见 [Advanced settings configuration in WS](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)，此时 PID 1 是 systemd，而 PID 2 还有其他几个进程就是 `/init`：可以猜测，启动过程中，首先启动还是的 `/init`，然后 PID 1 的 `/init` 调用 `exec` 切换到 systemd PID 1，其余进程继续执行。

### kernel 和 initramfs

如果查看 dmesg，会发现 Linux 的启动 cmdline 是：

```
initrd=\initrd.img WSL_ROOT_INIT=1 panic=-1 nr_cpus=8 bonding.max_bonds=0 dummy.numdummies=0 fb_tunnels=none swiotlb=force console=hvc0 debug pty.legacy_count=0
```

这个 `initrd.img` 可以在 `C:\Windows\System32\lxss\tools` 下面找到，也可以从 [WSL 安装包](https://github.com/microsoft/WSL/releases/download/1.2.5/Microsoft.WSL_1.2.5.0_x64_ARM64.msixbundle) 中解包出来。进一步可以发现 `initrd.img` 内部只有一个 `/init` 文件：

```shell
$ cpio -itv < initrd.img
-rwxrwxrwx   0 root     root      1978872 Apr 20 06:55 init
3866 blocks
```

也就是说所有启动以后的准备工作都在这个 init 程序里做完了。

kernel 的格式在不同版本也不一样：

```shell
# WSL 1.2.5
kernel: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked, BuildID[sha1]=e87c738e1e340eaf67d8d0c99369d458cdb5e6a0, stripped
# WSL 2.0.0
kernel: Linux kernel x86 boot executable bzImage, version 5.15.123.1-microsoft-standard-WSL2 (root@5a891d5fa777) #1 SMP Mon Aug 7 19:01:48 UTC 2023, RO-rootFS, swap_dev 0XD, Normal VGA
```

或许隐含了什么启动流程上的变化，这里并不确定。

### /init

在 WSL2 文件系统内，有多个到 `/init` 的符号链接：

```
/usr/bin/wslpath -> /init
/usr/sbin/mount.drvfs -> /init
```

同时还有上面出现过的 `plan9`，其实也是 `/init` 去执行的，说明 `/init` 内部会有逻辑，去判断 `argv[0]` 是什么，然后进行相应的操作。可以找到如下几个 usage 文本：

```shell
# wslpath
Usage:
    -a    force result to absolute path format
    -u    translate from a Windows path to a WSL path (default)
    -w    translate from a WSL path to a Windows path
    -m    translate from a WSL path to a Windows path, with '/' instead of '\'

EX: wslpath 'c:\users'
# mount.drvfs: no usage?
# localhost
Usage: localhost --port-tracker-fd fd [--bpf-fd fd] [--netlink-fd fd] [--localhost-relay fd]
# plan9
Usage: plan9 --control-socket fd --socket-path path --server-fd fd --log-file log-file --log-level level pipe-fd fd [--log-truncate]
# gns
Usage: gns [--socket fd] [--dns_socket fd] [--adapter guid] [--msg_type int]
# telagent: no usage?
```

其中 `localhost` 命令和 `gns` 命令应该就是 WSL 2.0.0 引入的 mirrored networking mode 所用到的子程序了。`telagent` 从名字来看应该是 telemetry agent。`plan9` 和 `mount.drvfs` 应该是配合 9pfs 使用的进程了。使用 `strings` 可以看到一些 mirrored networking mode 相关的文字：

```
GnsPortTracker: Failed to deallocate port
GnsPortTracker: Requested the host for port allocation on port (family %d, port %u, protocol %d) - returned %d
GnsPortTracker: Tracking bind call: family (%d) port (%u) protocol (%d)
GnsPortTracker: No longer tracking bind call: family (%d) port (%u) protocol (%d)
GnsPortTracker: Fetch to read bind() call info with ID %llu for pid %d, %s
GnsPortTracker: Request for a port that's already reserved (family %d, port %u, protocol %d)
GnsPortTracker: Failed to complete bind request, %s
GnsPortTracker: Failed to read bind request, %s
```

可以可以大概预测一下它的工作模式：观测 Linux 上的 bind 系统调用，如果发现有进程要 bind 端口，就去 Windows 上也分配同一个端口，然后启动一个端口转发程序，让 Windows 上的程序可以访问到 Linux 里面的服务。

此外 mirrored networking mode 还有一个特性是，同步 Windows 和 Linux 的 IP 地址等配置，这个功能看起来也是由 `gns` 来完成的：

```
SetAdapterConfiguration setting the IPv4 address on endpointID (%s) to %s on interfaceName %s
ModifyAddress: Restoring route %s after address change, on interfaceName %s
ProcessRouteChange: Reset routes on interfaceName %s
ProcessRouteChange: Remove route %s on interfaceName %s
ProcessRouteChange: Update route %s on interfaceName %s
```

新的 DNS tunneling 功能也能找到相应的文本：

```
DnsTunnelingManager::DnsTunnelingManager - using DNS server IP %s
```

### kernel

在内核方面，WSL2 打了一些自己的 [patch](https://github.com/microsoft/WSL2-Linux-Kernel/commits/linux-msft-wsl-5.15.y)，涵盖的范围有：

- 内存相关：memory-reclaim，page-reporting
- WSLg 相关：Hyper-V vGPU
- ARM64 相关：Hyper-V 支持

其中修改量最大的部分就是 WSLg 的 vGPU。

### WSLg

WSLg 是允许 WSL2 的程序在 Windows 上显示 UI 的功能。首先能看到的是，它设置了一个 `DISPLAY=:0`，同时还 mount 了不少文件进来：

```shell
none on /usr/lib/wsl/drivers type 9p (ro,nosuid,nodev,noatime,dirsync,aname=drivers;fmask=222;dmask=222,mmap,access=client,msize=65536,trans=fd,rfd=7,wfd=7)
none on /usr/lib/wsl/lib type overlay (rw,relatime,lowerdir=/gpu_lib_packaged:/gpu_lib_inbox,upperdir=/gpu_lib/rw/upper,workdir=/gpu_lib/rw/work)
none on /mnt/wslg type tmpfs (rw,relatime)
/dev/sdc on /mnt/wslg/distro type ext4 (ro,relatime,discard,errors=remount-ro,data=ordered)
none on /mnt/wslg/versions.txt type overlay (rw,relatime,lowerdir=/systemvhd,upperdir=/system/rw/upper,workdir=/system/rw/work)
none on /mnt/wslg/doc type overlay (rw,relatime,lowerdir=/systemvhd,upperdir=/system/rw/upper,workdir=/system/rw/work)
none on /tmp/.X11-unix type tmpfs (ro,relatime)
```

其中 `/tmp/.X11-unix` 是从 `/mnt/wslg/.X11-unix` bind-mount 而来：

```shell
/bin/mount -o bind,ro,X-mount.mkdir -t none /mnt/wslg/.X11-unix /tmp/.X11-unix
```

这点也可以在打开 systemd 的 WSL2 系统里，在 `/run/systemd/generator.early/wslg-mount.service` 文件里看到。

在 WSL2 的安装程序里，还能看到 RDP 的身影，因此让人怀疑，是否是在 Windows 上启动 RDP 客户端，远程连接到 WSL2 的 Linux 里面，而 Linux 里面启动了一个类似 xrdp 的程序，启动了一个 X11 Server，通过 RDP 把界面共享给 Windows。

### system.vhd

在 WSL2 安装包中，可以看到一个 `system.vhd` 文件，里面是一个 ext2 的 rootfs，解开以后，会看到是 [CBL-Mariner](https://github.com/microsoft/CBL-Mariner) 的发行版：

```shell
DISTRIB_ID="Mariner"
DISTRIB_RELEASE="2.0.20230630"
DISTRIB_CODENAME=Mariner
DISTRIB_DESCRIPTION="CBL-Mariner 2.0.20230630"
```

在这个发行版系统里，可以看到装了很多软件，包括很多图形界面的内容，可以想到是和 WSLg 有关（毕竟系统里只有一个用户目录 `/home/wslg`），把很多图形界面的依赖都打包进去了。甚至还有一个 `etc/wsl.conf`：

```shell
[boot]
command=/usr/bin/WSLGd
[user]
default=wslg
```

所以可以猜想，WSLg 运行的时候，为了避免污染 WSL2 Linux 的环境，把 WSLg 的很多图形界面的进程放到了一个单独的 ns 中，两个 ns 之间通过 X11 unix socket 进行互相访问，这样 WSLg 的内部实现对用户就是透明的，用户只会看到一个 `DISPLAY=:0`，用这个 DISPLAY 就可以在 Windows 上显示 UI。

更进一步猜想，结合 `mount` 看到的各种 overlayfs，还有不存在的目录，很容易想到，是不是自己访问的整个 WSL2 Linux 环境，其实是在一个容器里面，容器外面是这个 CBL-Mariner，容器里面才是我们看到的部分。这完全可以做到，毕竟 systemd-nspawn 容器是可以在里面 boot systemd 的。可以用来佐证这个猜测的一个现象是，系统里找不到监听 `/tmp/.X11-unix/X0` 的进程。

在 WSL2 Linux 里面，rootfs 是 `/dev/sdc`，`/dev/sdb` 是 SWAP 分区，如果 mount 一下 `/dev/sda`，就会发现它里面的内容就是 `systemd.vhd` 的内容，也就是上面的 CBL-Mariner 系统。同时，CBL-Mariner 的 `/etc/versions.txt` 内容和 WSL2 Linux 的 `/mnt/wslg/versions.txt` 内容一样：

```shell
none on /mnt/wslg/versions.txt type overlay (rw,relatime,lowerdir=/systemvhd,upperdir=/system/rw/upper,workdir=/system/rw/work)
```

可以猜测 `/dev/sda` 曾经被挂载到了 `/systemvhd`，然后在上面套了一层 overlayfs，最后 mount 到 `/mnt/wslg` 下面。同理，CBL-Mariner 的 `/usr/share/doc` 被挂载到了 `/mnt/wslg/doc` 路径：

```shell
none on /mnt/wslg/doc type overlay (rw,relatime,lowerdir=/systemvhd,upperdir=/system/rw/upper,workdir=/system/rw/work)
```

接下来就是验证猜想的时刻，事实上，你可以进入 CBL-Mariner 这个系统，这个系统称为 WSLg System Distro：

```shell
wsl --system
```

就可以看到它里面确实跑了一个 Xwayland，并且和 WSL2 Linux 拥有同样的 IP 地址：这说明它们共享了同一个 network namespace，但其他是独立的，甚至你还可以在 CBL-Mariner 看到你在 WSL2 Linux 里面的进程，就好像你运行了一个 `docker run --net=host` 的容器一样。

关于 WSL2 System Distro 的讨论，推荐阅读：<https://unix.stackexchange.com/a/732459/144358>，你甚至可以自己构建一个：[Building the WSLg System Distro](https://github.com/microsoft/WSLG/blob/main/CONTRIBUTING.md#building-the-wslg-system-distro)，并且替换掉自带的 WSLg System Distro。
