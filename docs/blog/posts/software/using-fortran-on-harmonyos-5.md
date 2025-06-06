---
layout: post
date: 2025-06-06
tags: [huawei,arm64,harmonyos,fortran,clang,flang,llvm]
categories:
    - hardware
---

# 在 HarmonyOS 5 上运行 Fortran 程序

## 背景

前段时间把 SPEC CPU 2017 移植到了鸿蒙 5 上：<https://github.com/jiegec/SPECCPU2017Harmony>，由于 SPEC CPU 2017 里有不少 Fortran 程序，所以就研究了一下怎么编译 Fortran 代码，最终搞成了，在这里记录一下。

<!-- more -->

## 过程

HarmonyOS 5 的工具链用的是 LLVM 15，自带的编译器是 clang，那个时候还没有 LLVM flang。但是，经过实际测试，使用新版本的 flang，也是可以的，只是需要做一些额外的操作。例如 flang 有自己的 runtime（类比 libgcc 和 LLVM 的 compiler-rt），需要交叉编译一个 arm64 的版本，下面是仓库中 [build-flang.sh](https://github.com/jiegec/SPECCPU2017Harmony/blob/f02cbe4a043d4c1489ebfae8a190e4a1ab6ca2c8/build-flang.sh) 的内容：

```shell
#!/bin/sh
# build missing libraries for aarch64-linux-ohos target
# assume llvm-project is cloned at $HOME/llvm-project
set -x -e
mkdir -p flang
export PATH=~/command-line-tools/sdk/default/openharmony/native/llvm/bin:$PATH
DST=$PWD/flang
cd $HOME/llvm-project
git checkout main
# match hash in flang-new-20 --version
git reset 7cf14539b644 --hard

cd libunwind
rm -rf build
mkdir -p build
cd build
cmake .. -G Ninja \
	-DCMAKE_C_FLAGS="-target aarch64-linux-ohos -fuse-ld=lld" \
	-DCMAKE_C_COMPILER="clang" \
	-DCMAKE_CXX_FLAGS="-target aarch64-linux-ohos -fuse-ld=lld" \
	-DCMAKE_CXX_COMPILER="clang++"
ninja
cp lib/libunwind.a $DST/
cd ../../

cd flang/lib/Decimal
rm -rf build
mkdir -p build
cd build
cmake .. -G Ninja \
	-DCMAKE_C_FLAGS="-target aarch64-linux-ohos -fuse-ld=lld -fPIC" \
	-DCMAKE_C_COMPILER="clang" \
	-DCMAKE_CXX_FLAGS="-target aarch64-linux-ohos -fuse-ld=lld -fPIC" \
	-DCMAKE_CXX_COMPILER="clang++"
ninja
cp libFortranDecimal.a $DST/
cd ../../../../

cd flang/runtime
rm -rf build
mkdir -p build
cd build
cmake .. -G Ninja \
	-DCMAKE_C_FLAGS="-target aarch64-linux-ohos -fuse-ld=lld -fPIC" \
	-DCMAKE_C_COMPILER="clang" \
	-DCMAKE_CXX_FLAGS="-target aarch64-linux-ohos -fuse-ld=lld -fPIC" \
	-DCMAKE_CXX_COMPILER="clang++"
ninja
cp libFortranRuntime.a $DST/
cd ../../../

ls -al $DST
```

核心就是以 aarch64-linux-ohos 为 target，编译出三个 `.a` 文件，之后再链接上就可以了。需要注意的是，runtime 版本和 flang 版本需要一致。为了偷懒，直接用的是 LLVM APT 提供的 flang-new-20 的 binary，那么它是会随着 apt upgrade 而更新的，这个时候就需要重新编译一次 flang runtime，然后链接到程序里。如果版本不对上，可能遇到一些问题：

```
fatal Fortran runtime error(/home/jiegec/llvm-project/flang/runtime/descriptor.cpp:74): not yet implemented: type category(6)
```

参考 [[flang] fatal Fortran runtime error](https://github.com/llvm/llvm-project/issues/129877)，就知道是编译器版本和 runtime 不兼容的问题了。

编译好了 fortran runtime 之后，就可以用 flang-new-20 编译 fortran 代码了。这里给出 CMake 的配置方式，主要涉及到需要用的编译选项：

```cmake
set(CMAKE_Fortran_COMPILER_FORCED TRUE)
set(CMAKE_Fortran_COMPILER "flang-new-20")
set(CMAKE_Fortran_FLAGS "-target aarch64-linux-ohos -fuse-ld=lld -L ${CMAKE_CURRENT_SOURCE_DIR}/../../../../flang -nostdlib -L ${CMAKE_CURRENT_SOURCE_DIR}/../../../../../command-line-tools/sdk/default/openharmony/native/sysroot/usr/lib/aarch64-linux-ohos -lc -lm -L ${CMAKE_CURRENT_SOURCE_DIR}/../../../../../command-line-tools/sdk/default/openharmony/native/llvm/lib/clang/15.0.4/lib/aarch64-linux-ohos/ -lclang_rt.builtins -lFortranRuntime -lFortranDecimal")
enable_language(Fortran)
```

这里的相对路径，其实就是要找到新编译出来的 flang runtime，以及 HarmonyOS command line tools 里面的一些库，具体路径需要根据实际情况来调整，这里只是一个样例。

到这里，就可以在 HarmonyOS 5 上运行 Fortran 程序了。其实还可以考虑研究一下 GFortran，或许也是能实现的，但目前还没有去做进一步的尝试。
