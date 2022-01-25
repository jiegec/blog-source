---
layout: post
date: 2022-01-25 21:41:00 +0800
tags: [riscv,vector,rvv,llvm,clang,binutils]
category: software
title: RISC-V Vector 1.0 工具链构建
---

不久前 RVV 1.0 标准终于是出来了，但是工具链的支持目前基本还处于刚 upstream 还没有 release 的状态。而目前 RVV 1.0 的支持主要在 LLVM 上比较活跃，因此也是采用 LLVM Clang + GCC Newlib Toolchain 的方式进行配合，前者做 RVV 1.0 的编译，后者提供 libc 等基础库。

LLVM Clang 直接采用 upstream 即可。编译选项：

```shell
$ cmake -G Ninja ../llvm -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_INSTALL_PREFIX=/prefix/llvm -DCMAKE_BUILD_TYPE=Release -DLLVM_ENABLE_PROJECTS="clang" -DLLVM_TARGETS_TO_BUILD="RISCV"
$ ninja
$ ninja install
$ /prefix/llvm/bin/clang --version
clang version 14.0.0 (https://github.com/llvm/llvm-project.git 8d298355ca3778a47fd6b3110aeee03ea5e8e02b)
Target: x86_64-unknown-linux-gnu
Thread model: posix
InstalledDir: /data/llvm/bin
```

还需要配合一个 GCC 工具链才可以完整地工作。可以直接采用 riscv-gnu-toolchain nightly 版本，比如 [riscv64-elf-ubuntu-20.04-nightly-2022.01.17-nightly.tar.gz](https://github.com/riscv-collab/riscv-gnu-toolchain/releases/download/2022.01.17/riscv64-elf-ubuntu-20.04-nightly-2022.01.17-nightly.tar.gz)。下载以后解压，得到 riscv 目录，GCC 版本是比较新的：

```shell
$ ~/riscv/bin/riscv64-unknown-elf-gcc --version
riscv64-unknown-elf-gcc (GCC) 11.1.0
Copyright (C) 2021 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
```

但是如果编译 C++ 程序，链接的时候就会报错：`prefixed ISA extension must separate with _`，这是因为 riscv-gnu-toolchain 仓库的 binutils 版本不够新，在 upstream 的 binutils 里面已经修复了这个问题。所以 clone 下来，然后编译，覆盖掉 riscv-gnu-toolchain 里面的 binutils：

```shell
$ ../configure --target=riscv64-unknown-elf --prefix=$HOME/riscv --disable-gdb --disable-sim --disable-libdecnumber --disable-readline
$ make
$ make install
$ ~/riscv/bin/riscv64-unknown-elf-ld --version
GNU ld (GNU Binutils) 2.38.50.20220125
Copyright (C) 2022 Free Software Foundation, Inc.
This program is free software; you may redistribute it under the terms of
the GNU General Public License version 3 or (at your option) a later version.
This program has absolutely no warranty.
```

然后编译程序的时候，使用 clang，配置参数 `--gcc-toolchain=~/riscv` 即可让 clang 找到 GNU 工具链。这样就可以编译出来 RVV 1.0 的程序了：


```shell
$ /llvm/bin/clang --target=riscv64-unknown-elf -O2 -march=rv64gcv1p0 -menable-experimental-extensions -mllvm --riscv-v-vector-bits-min=256 --gcc-toolchain=$HOME/riscv add.cpp -o add
$ /data/llvm/bin/llvm-objdump --mattr=+v -S add
   1020e: 57 70 04 c5   vsetivli        zero, 8, e32, m1, ta, mu
   10212: 07 64 03 02   vle32.v v8, (t1)
   10216: 87 e4 03 02   vle32.v v9, (t2)
   1021a: 93 07 07 fe   addi    a5, a4, -32
   1021e: 07 e5 07 02   vle32.v v10, (a5)
   10222: 87 65 07 02   vle32.v v11, (a4)
   10226: 57 14 85 02   vfadd.vv        v8, v8, v10
   1022a: d7 94 95 02   vfadd.vv        v9, v9, v11
   1022e: 93 07 05 fe   addi    a5, a0, -32
   10232: 27 e4 07 02   vse32.v v8, (a5)
   10236: a7 64 05 02   vse32.v v9, (a0)
```

可以看到 llvm 的自动向量化是工作的。此外，也可以编写 rvv intrinsic。