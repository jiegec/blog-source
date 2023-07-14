---
layout: post
date: 2021-01-02
tags: [debian,macos,m1,qemu,aarch64]
category: software
title: 在 M1 上用 QEMU 运行 Debian 虚拟机
---

## 背景

看到 @jsteward 在 M1 的 QEMU 中运行了 Windows on ARM，所以我先来试试 Debian on AArch64，这样会简单一些。

参考：https://gist.github.com/niw/e4313b9c14e968764a52375da41b4278#file-readme-md

大约需要 3G 的硬盘空间。

## 安装 QEMU w/ M1 patches

目前上游的 QEMU 还不支持 M1 的 Hypervisor framework，需要打 patch：

```shell
git clone https://mirrors.tuna.tsinghua.edu.cn/git/qemu.git
cd qemu
git checkout master -b wip/hvf
curl 'https://patchwork.kernel.org/series/400619/mbox/'|git am --3way
mkdir build
cd build
../configure --target-list=aarch64-softmmu --enable-cocoa --disable-gnutls
make -j4
```

编译后，得到 `qemu-system-aarch64` 的二进制

## 准备好文件系统

需要下载 [EFI 固件](https://gist.github.com/niw/4f1f9bb572f40d406866f23b3127919b/raw/f546faea68f4149c06cca88fa67ace07a3758268/QEMU_EFI-cb438b9-edk2-stable202011-with-extra-resolutions.tar.gz) 和 [Debian 安装镜像](https://mirrors.tuna.tsinghua.edu.cn/debian-cd/current/arm64/iso-cd/debian-10.7.0-arm64-xfce-CD-1.iso)，解压前者以后把文件放同一个目录中，并且创建需要的文件：

```shell
$ ls *.fd
QEMU_EFI.fd   QEMU_VARS.fd
$ dd if=/dev/zero of=pflash0.img bs=1m count=64
$ dd if=/dev/zero of=pflash1.img bs=1m count=64
$ dd if=QEMU_EFI.fd of=pflash0.img conv=notrunc
$ dd if=QEMU_VARS.fd of=pflash1.img conv=notrunc
$ $QEMU/qemu-img create -f qcow2 disk.qcow2 40G
```

## 安装 Debian 系统

接着，执行以下的命令，然后按照提示安装系统：

```shell
$ $QEMU/qemu-system-aarch64 \
  -serial mon:stdio \
  -M virt,highmem=off \
  -accel hvf \
  -cpu cortex-a72 \
  -smp 4 \
  -m 4096 \
  -drive file=./pflash0.img,format=raw,if=pflash,readonly=on \
  -drive file=./pflash1.img,format=raw,if=pflash \
  -device virtio-scsi-pci \
  -device virtio-gpu-pci \
  -device qemu-xhci \
  -device usb-kbd \
  -device usb-tablet \
  -drive file=./disk.qcow2,if=none,id=boot,cache=writethrough \
  -device nvme,drive=boot,serial=boot \
  -drive if=none,id=cd,file=debian-10.7.0-arm64-xfce-CD-1.iso,media=cdrom \
  -device scsi-cd,drive=cd \
  -display default,show-cursor=on
```

需要注意的是，如果用 `-cdrom` 选项，Debian 会无法识别，所以需要走 SCSI。安装完成后，第一次重启可能会显示失败，不用管。另外，安装界面只在串口处显示，但不会显示在 GUI 中，估计是因为 [BUG](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=977466)（感谢 @Harry-Chen 指出）。

## 启动系统

安装好后，运行下面的命令来启动 Debian 系统：

```shell
$ $QEMU/qemu-system-aarch64 \
  -monitor stdio \
  -M virt,highmem=off \
  -accel hvf \
  -cpu cortex-a72 \
  -smp 4 \
  -m 4096 \
  -drive file=./pflash0.img,format=raw,if=pflash,readonly=on \
  -drive file=./pflash1.img,format=raw,if=pflash \
  -device virtio-gpu-pci \
  -device virtio-scsi-pci \
  -device qemu-xhci \
  -device usb-kbd \
  -device usb-tablet \
  -drive file=./disk.qcow2,if=none,id=boot,cache=writethrough \
  -device nvme,drive=boot,serial=boot \
  -display default,show-cursor=on \
  -nic user,model=virtio
```

注意参数和上面有所不同。启动后就可以在 GUI 上看到 Debian 登录的界面了。

## 网络

起来以后，可以看到一个网卡 `enp0s1` 启动并获取 IP 地址：

```shell
$ ip l set enp0s1 up
$ dhclient enp0s1
```

获取到一个 IP 地址后，就可以上网了。

## 已知问题

在虚拟机内重启以后，可能会启动失败。退出 QEMU 进程重新启动即可。
