---
layout: post
date: 2018-05-24 23:40:00 +0800
tags: [fedora,riscv,qemu]
category: os
title: 体验 Fedora on RISCV
---

看到 RISCV 很久了，但一直没能体验。最近工具链不断更新，QEMU 在 2.12.0 也正式加入了 riscv 的模拟。但是自己编译一个内核又太麻烦，就找到了 Fedora 做的 RISCV port，下载下来试用了一下。之前试过一次，但是遇到了一些问题，刚才总算是成功地搞出来了。

官方文档地址：https://fedorapeople.org/groups/risc-v/disk-images/readme.txt
首先下载 https://fedorapeople.org/groups/risc-v/disk-images/ 下的 bbl vmlinux 和 stage4-disk.img.xz 三个文件，然后解压 stage4-disk.img.xz，大约有 5G 的样子。之前作者在脚本里作死开得特别大，导致我以前光是解压这一步就成功不了。现在终于解决了。

然后启动 qemu 命令打开虚拟机：
```shell
qemu-system-riscv64 \
  -nographic \
  -machine virt \
  -m 2G \
  -kernel bbl \
  -object rng-random,filename=/dev/urandom,id=rng0 \
  -device virtio-rng-device,rng=rng0 \
  -append "console=ttyS0 ro root=/dev/vda" \
  -device virtio-blk-device,drive=hd0 \
  -drive file=stage4-disk.img,format=raw,id=hd0 \
  -device virtio-net-device,netdev=usernet \
  -netdev user,id=usernet,hostfwd=tcp::10000-:22
```

这段命令摘自 readme.txt，区别只在于把 -smp 4 去掉了。不知道为什么不能正常工作，可能和作者提到的 FPU patch 有关。然后系统就可以正常起来了（firewalld 和 systemd-logind 不止为啥起不来，但是不用管）。

可以验证一下我们的系统：
```shell
$ uname -a
Linux stage4.fedoraproject.org 4.15.0-00046-g48fb45691946 #27 SMP Mon May 14 08:25:14 UTC 2018 riscv64 riscv64 riscv64 GNU/Linux
```
