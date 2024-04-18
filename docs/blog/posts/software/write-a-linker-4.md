---
layout: post
date: 2024-04-07
tags: [linux,linker,elf,write-a-linker]
categories:
    - software
---

# 开发一个链接器（4）

## 前言

这个系列的前三篇博客实现了一个简单的静态链接器，它可以输入若干个 ELF .o 文件，输出 ELF 可执行文件或者动态库。接下来，我们要进一步支持动态库，不仅可以生成动态库，还支持让动态库参与到静态链接当中。

<!-- more -->

## 回顾

首先回顾一下：在这个系列的前三篇博客中，我们观察了现有链接器的工作过程，并且实现了一个简单的链接器：输入若干个 ELF object，链接成一个可以运行的 ELF 可执行文件或者 ELF 动态库。这个过程包括：

1. 解析输入的若干个 ELF，收集各个 section 需要保留下来的内容，合并来自不同 ELF 的同名 section
2. 规划将要生成的 ELF 可执行文件的内容布局：开始是固定的文件头，之后是各个 section，计算出它们从哪里开始到哪里结束
3. 如果要生成动态库，还需要针对动态链接器，构造一些额外的 section（`.dynamic`，`.dynsym` 和 `.dynstr`）
4. 第二步完成以后，就可以知道在运行时，各个 section 将会被加载到哪个地址上，进而更新符号表，得到每个符号在运行时会处在哪个地址上；此时我们就可以计算重定位，把地址按照预设的规则填入到对应的地方
5. 如果要生成动态库，因为运行时动态库的加载地址不确定，所以在 ELF 中把加载地址设为 0，并且要求代码是地址无关代码（PIC，Position Independent Code）
6. 最后按照预设的文件布局，把文件内容写入到 ELF 文件中

接下来我们就要支持链接动态库，在上一篇博客中，最后的这一步是用 GNU ld 完成的：

```shell
# assemble sources
$ as main.s -o main.o
$ as printer.s -o printer.o
# ld -shared: generate shared library
# we have implemented this in the previous blog post
$ ld -shared printer.o -o libprinter.so

# ld -dynamic-linker: Set path to dynamic linker for the executable
# we are going to implement this one
$ ld -dynamic-linker /lib64/ld-linux-x86-64.so.2 main.o libprinter.so -o main

$ LD_LIBRARY_PATH=$PWD ./main
Hello world!
```

接下来，我们要实现的就是 `ld -dynamic-linker /lib64/ld-linux-x86-64.so.2 main.o libprinter.so -o main` 命令的功能。

## 分析

首先要分析一下 ld 在实现动态链接的时候，做了什么事情。观察链接得到的可执行文件 `main`：

```shell
$ ld -dynamic-linker /lib64/ld-linux-x86-64.so.2 main.o libprinter.so -o main
$ readelf -a main
```

## 实现

1. .plt, .got.plt
2. plt first entry & other entries, relocations to reuse code
3. .got.plt first three entries & other entries, add dynamic relocation
4. gnu hash handling
5. dynamic more DT fields
6. interp, needed, soname
7. pie

## 参考

最后给出一些文档，可供实现时参考：

- [All about Procedure Linkage Table](https://maskray.me/blog/2021-09-19-all-about-procedure-linkage-table)