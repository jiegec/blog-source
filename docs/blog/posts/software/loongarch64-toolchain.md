---
layout: post
date: 2022-05-02 20:35:00 +0800
tags: [loongarch,toolchain,gcc]
category: software
title: LoongArch64 工具链构建
---

最近因为龙芯杯的原因，想自己搞个 LoongArch64 的交叉编译工具链试试，结果遇到了很多坑，最后终于算是搞出来了。

一开始是想搞一个 newlib 的工具链，比较简单，而且之前做过一个仓库：[jiegec/riscv-toolchain](https://github.com/jiegec/riscv-toolchain)，就是构建的 riscv64-unknown-elf 工具链，照着 riscv-gnu-toolchain 就可以了。不过研究发现，newlib 还不支持 loongarch，目前只有 glibc 支持，只好硬着头皮上了。

于是我就在 riscv-toolchain 的基础上搞 loongarch64-unknown-linux-gnu，也就是带 glibc 的工具链，结果发现遇到很多坑。首先编译 libgcc 的时候就找不到头文件，于是先要从 glibc 和 linux 安装头文件到 sysroot 里面，对于 sysroot 里面的头文件路径到底是 include 还是 usr/include 也折腾了半天。然后编译 libgcc 又各种出问题，最后折腾了半天，结果是 gcc stage1 和 glibc 都没问题，gcc stage2 会报链接错误，但是不管它也能用，可以编译出正常的程序，毕竟 libc 是好的。

于是转念一想，要不要试试 crosstool-ng。克隆了一份上游的版本，照着 riscv 的部分抄了一份变成了 loongarch，然后把 config 里面的 linux/glibc/gcc/binutils-gdb 都替换为 custom location，这样我就可以用上游的最新版本了。中途还遇到了 [crosstool-ng 对 gcc 12/13 不兼容的 bug](https://github.com/crosstool-ng/crosstool-ng/issues/1564)，还好下面有人提出了解决方法。这些都搞定以后，终于构建出了一个完整的 loongarch64-unknown-linux-gnu 工具链。仓库地址是 [jiegec/ct-ng-loongarch64](https://github.com/jiegec/ct-ng-loongarch64)，需要配合添加了 LoongArch 的 [jiegec/crosstool-ng loongarch 分支](https://github.com/jiegec/crosstool-ng/tree/loongarch) 使用。

最后得到的工具链各组件版本如下：

```

   
loongarch64-unknown-linux-gnu-gcc (crosstool-NG 1.25.0_rc2.1_7e21141) 13.0.0 20220502 (experimental)
Copyright (C) 2022 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

GNU ld (crosstool-NG 1.25.0_rc2.1_7e21141) 2.38.50.20220502
Copyright (C) 2022 Free Software Foundation, Inc.
This program is free software; you may redistribute it under the terms of
the GNU General Public License version 3 or (at your option) a later version.
This program has absolutely no warranty.
GNU gdb (crosstool-NG 1.25.0_rc2.1_7e21141) 13.0.50.20220502-git
Copyright (C) 2022 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
```

之后有时间的话，再把 qemu 和系统搞起来跑跑。

UPDATE: GCC 12.1 发布了，试了一下这个正式版本可以正确地编译。目前还需要使用 HEAD 版本的 binutils 和龙芯的 glibc 和 linux。

参考文档：

- [手把手教你构建基于 LoongArch64 架构的 Linux 系统](https://github.com/sunhaiyong1978/CLFS-for-LoongArch/blob/main/CLFS_For_LoongArch64-20220108.md)
- [How to Build a GCC Cross-Compiler](https://preshing.com/20141119/how-to-build-a-gcc-cross-compiler/)