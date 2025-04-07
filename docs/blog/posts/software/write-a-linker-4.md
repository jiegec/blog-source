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

### 观察可执行文件

首先要分析一下 ld 在实现动态链接的时候，做了什么事情。观察链接得到的可执行文件 `main`：

```shell
$ ld -dynamic-linker /lib64/ld-linux-x86-64.so.2 main.o libprinter.so -o main
$ readelf -a main
```

首先是 ELF Header 部分：

```shell
ELF Header:
  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00 
  Class:                             ELF64
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              EXEC (Executable file)
  Machine:                           Advanced Micro Devices X86-64
  Version:                           0x1
  Entry point address:               0x401030
  Start of program headers:          64 (bytes into file)
  Start of section headers:          12696 (bytes into file)
  Flags:                             0x0
  Size of this header:               64 (bytes)
  Size of program headers:           56 (bytes)
  Number of program headers:         8
  Size of section headers:           64 (bytes)
  Number of section headers:         15
  Section header string table index: 14
```

和之前看到的可执行文件没什么不同：Type 是 EXEC 表示可执行文件，入口地址指向了 `main` 的地址 `0x401030`。

接下来看 Section 部分：

```shell
Section Headers:
  [Nr] Name              Type             Address           Offset
       Size              EntSize          Flags  Link  Info  Align
  [ 0]                   NULL             0000000000000000  00000000
       0000000000000000  0000000000000000           0     0     0
  [ 1] .interp           PROGBITS         0000000000400200  00000200
       000000000000001c  0000000000000000   A       0     0     1
  [ 2] .hash             HASH             0000000000400220  00000220
       0000000000000018  0000000000000004   A       4     0     8
  [ 3] .gnu.hash         GNU_HASH         0000000000400238  00000238
       000000000000001c  0000000000000000   A       4     0     8
  [ 4] .dynsym           DYNSYM           0000000000400258  00000258
       0000000000000048  0000000000000018   A       5     1     8
  [ 5] .dynstr           STRTAB           00000000004002a0  000002a0
       000000000000001a  0000000000000000   A       0     0     1
  [ 6] .rela.plt         RELA             00000000004002c0  000002c0
       0000000000000030  0000000000000018  AI       4    11     8
  [ 7] .plt              PROGBITS         0000000000401000  00001000
       0000000000000030  0000000000000010  AX       0     0     16
  [ 8] .text             PROGBITS         0000000000401030  00001030
       000000000000000a  0000000000000000  AX       0     0     1
  [ 9] .eh_frame         PROGBITS         0000000000402000  00002000
       0000000000000000  0000000000000000   A       0     0     8
  [10] .dynamic          DYNAMIC          0000000000402ec8  00002ec8
       0000000000000120  0000000000000010  WA       5     0     8
  [11] .got.plt          PROGBITS         0000000000402fe8  00002fe8
       0000000000000028  0000000000000008  WA       0     0     8
  [12] .symtab           SYMTAB           0000000000000000  00003010
       00000000000000d8  0000000000000018          13     3     8
  [13] .strtab           STRTAB           0000000000000000  000030e8
       0000000000000043  0000000000000000           0     0     1
  [14] .shstrtab         STRTAB           0000000000000000  0000312b
       0000000000000069  0000000000000000           0     0     1
Key to Flags:
  W (write), A (alloc), X (execute), M (merge), S (strings), I (info),
  L (link order), O (extra OS processing required), G (group), T (TLS),
  C (compressed), x (unknown), o (OS specific), E (exclude),
  D (mbind), l (large), p (processor specific)

There are no section groups in this file.
```

可以看到，它出现了一些在上一篇博客里出现过的和动态链接相关的段：

1. `.hash` 和 `.gnu.hash`：不同格式的哈希表，提供了从符号名字到符号的映射，提高动态链接器查找符号的性能
2. `.dynsym`：Dynamic Symbol，和动态链接有关的动态符号表
3. `.dynstr`：Dynamic String，和动态链接有关的字符串的表
4. `.dynamic`：Dynamic，向动态链接器提供了一些信息

此外，还出现了一些新的段：

1. `.interp`：这个段记录了 Program Interpreter 的路径，也就是前面用命令行 `ld -dynamic-linker /lib64/ld-linux-x86-64.so.2` 所指定的 `/lib64/ld-linux-x86-64.so.2`，用来告诉操作系统，要运行这个可执行程序，需要依靠这个 Program Interpreter，它同时也是动态链接器
2. `.plt`：Procedure Linkage Table，涉及到动态链接库的函数，下面会详细介绍
3. `.rela.plt`：针对 Procedure Linkage Table 的重定位（Relocation）信息，下面会详细介绍
4. `.got.plt`：针对 Procedure Linkage Table 的 Global Offset Table，下面会详细介绍

这时候你觉得很奇怪：通常看到 `.rela` 开头的段，都是在对象文件里，用来保存对应段的重定位信息。但是为啥可执行文件里还有呢？在前面的几篇博客中，静态链接器已经解决了所有重定位，所以最终的可执行文件里没有重定位。但是，对于动态库，由于静态链接器无法知道动态库会被加载到什么地址上去，只好保留了一些重定位信息，而这些会留给后来的动态链接器：动态链接器会负责加载动态库，也就知道了动态库的地址，因此就可以计算出剩下的这些针对动态库的重定位了。

继续往下看 Program Headers 部分：

```shell
Program Headers:
  Type           Offset             VirtAddr           PhysAddr
                 FileSiz            MemSiz              Flags  Align
  PHDR           0x0000000000000040 0x0000000000400040 0x0000000000400040
                 0x00000000000001c0 0x00000000000001c0  R      0x8
  INTERP         0x0000000000000200 0x0000000000400200 0x0000000000400200
                 0x000000000000001c 0x000000000000001c  R      0x1
      [Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]
  LOAD           0x0000000000000000 0x0000000000400000 0x0000000000400000
                 0x00000000000002f0 0x00000000000002f0  R      0x1000
  LOAD           0x0000000000001000 0x0000000000401000 0x0000000000401000
                 0x000000000000003a 0x000000000000003a  R E    0x1000
  LOAD           0x0000000000002000 0x0000000000402000 0x0000000000402000
                 0x0000000000000000 0x0000000000000000  R      0x1000
  LOAD           0x0000000000002ec8 0x0000000000402ec8 0x0000000000402ec8
                 0x0000000000000148 0x0000000000000148  RW     0x1000
  DYNAMIC        0x0000000000002ec8 0x0000000000402ec8 0x0000000000402ec8
                 0x0000000000000120 0x0000000000000120  RW     0x8
  GNU_RELRO      0x0000000000002ec8 0x0000000000402ec8 0x0000000000402ec8
                 0x0000000000000138 0x0000000000000138  R      0x1
```

可以看到，出现了一个 `INTERP` 项，它指向了 `.interp` 段的地址，这个段里保存的就是 `/lib64/ld-linux-x86-64.so.2` 这个字符串，其实就是在告诉操作系统，从这个地址读取 Program Interpreter 的路径。和之前的动态库一样，也出现了 `DYNAMIC`，指向了 `.dynamic` 段，意味着这即使是可执行文件，也和动态库有一些相似的地方。

下面可以看到 `.dynamic` 段的内容：

```shell
Dynamic section at offset 0x2ec8 contains 13 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libprinter.so]
 0x0000000000000004 (HASH)               0x400220
 0x000000006ffffef5 (GNU_HASH)           0x400238
 0x0000000000000005 (STRTAB)             0x4002a0
 0x0000000000000006 (SYMTAB)             0x400258
 0x000000000000000a (STRSZ)              26 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000015 (DEBUG)              0x0
 0x0000000000000003 (PLTGOT)             0x402fe8
 0x0000000000000002 (PLTRELSZ)           48 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0x4002c0
 0x0000000000000000 (NULL)               0x0
```

和之前看到的动态库对比，多出现了这些项：

1. `NEEDED`：表示运行这个可执行文件所需要加载的动态库文件名，如果找不到对应的动态库，就会出现熟悉的 `error while loading shared libraries` 错误
2. `DEBUG`：用于调试，这里不讨论
3. `PLTGOT`：指向了 `.got.plt` 段的地址
4. `PLTRELSZ`：记录了 `.rela.plt` 每一项的大小
5. `PLTREL`：`RELA` 表示 `.rela.plt` 每一项里包含 addend 项（RELA = REL with Addend）
6. `JMPREL`：指向了 `.rela.plt` 段的地址

动态链接器在加载程序的时候，会去寻找 `NEEDED` 所指向的那些动态库并加载进来。那么这些文件会保存在哪里呢？和执行程序要去 `PATH` 中寻找类似，动态库也会根据环境变量以及系统配置的路径去寻找。由于这是一个非常频繁进行的操作，为了提升性能，系统中会有一份缓存，这个缓存的内容可以通过 `ldconfig -p` 命令查看。

上面提到了很多次 Procedure Linkage Table（PLT），那么它到底是什么呢？下面来观察可执行文件的代码段。

### 观察代码段和 PLT

用 `objdump -S main` 观察可执行文件的代码段和 PLT：

```shell
$ objdump -S main

main:     file format elf64-x86-64


Disassembly of section .plt:

0000000000401000 <print@plt-0x10>:
  401000:	ff 35 ea 1f 00 00    	push   0x1fea(%rip)        # 402ff0 <_GLOBAL_OFFSET_TABLE_+0x8>
  401006:	ff 25 ec 1f 00 00    	jmp    *0x1fec(%rip)        # 402ff8 <_GLOBAL_OFFSET_TABLE_+0x10>
  40100c:	0f 1f 40 00          	nopl   0x0(%rax)

0000000000401010 <print@plt>:
  401010:	ff 25 ea 1f 00 00    	jmp    *0x1fea(%rip)        # 403000 <print>
  401016:	68 00 00 00 00       	push   $0x0
  40101b:	e9 e0 ff ff ff       	jmp    401000 <print@plt-0x10>

0000000000401020 <exit@plt>:
  401020:	ff 25 e2 1f 00 00    	jmp    *0x1fe2(%rip)        # 403008 <exit>
  401026:	68 01 00 00 00       	push   $0x1
  40102b:	e9 d0 ff ff ff       	jmp    401000 <print@plt-0x10>

Disassembly of section .text:

0000000000401030 <_start>:
  401030:	e8 db ff ff ff       	call   401010 <print@plt>
  401035:	e8 e6 ff ff ff       	call   401020 <exit@plt>
```

会发现在 `.plt` 段中出现了两个函数：`print@plt` 和 `exit@plt`，正好是 `main` 函数调用的，由动态链接库提供的函数。在 `main` 函数里，也不是直接调用动态链接库的 `print` 和 `exit`，而是调用 `.plt` 段里对应的带 `@plt` 后缀的版本，这是为什么？而且，`.plt` 段开头的那段代码又是做什么的？为什么 `print@plt` 和 `exit@plt` 函数都要跳到 `0x401000` 处的代码？

这时候就要了解 PLT 的用途了。在静态链接的时候，链接的时候，链接器可以知道所有函数的地址，所以重定位都可以计算出，跳转和调用可以直接写入实际的绝对地址或者偏移量。但如果链接了一个动态库，链接器无法知道动态库的地址，所以重定位还是得继续留着，交给最后的动态链接器来完成重定位。那么，一个朴素的方法就是，保留对动态库的所有重定位信息。简单地把工作推迟给了动态链接器。但是，动态链接器工作在程序启动的时候，用户肯定不期望程序每次启动的时候，都要花很长的时间在动态链接上，所以动态链接还得足够快：前面也看到了，各种哈希表各种优化，就是为了提升动态链接的性能。要是每个调用都有一个重定位需要处理，那么性能肯定不好。

那么怎么办呢？很多常用函数，比如 `malloc` 和 `free` 等等，调用的地方是非常多的。不过，转念一想，虽然调用的地方很多，但是被调用的函数相比之下却会少很多：可能有一千个地方调用 `malloc`，但是 `malloc` 函数只有一个，如果只重定位一次，就可以解决所有对 `malloc` 的调用，那该多好！但是重定位一次只能修改一个地方的代码，怎么办呢？那就让一千个地方都调用一个临时的 `malloc` 函数，这个临时的 `malloc` 函数通过重定位调用真实的 `malloc` 函数，这样重定位只有一次，代价就是多了一次跳转。我们把这个临时的 `malloc` 函数叫做 `malloc@plt`，把记录所有这些临时函数的表称为 Procedure Linkage Table（PLT），那么代码变成：

```asm
    .section .plt
malloc@plt:
    call real_malloc # emit relocation to the real malloc

    .section .text
func1:
    call malloc@plt
    # ...

func2:
    call malloc@plt
    # ...
```

这样就解决了重定位数量太多的问题：从每个调用都要一个重定位，降低到每个被调用的函数一个重定位。但是，这样的 PLT 和实际看到的还是有很大的区别：

```shell
0000000000401010 <print@plt>:
  401010:	ff 25 ea 1f 00 00    	jmp    *0x1fea(%rip)        # 403000 <print>
  401016:	68 00 00 00 00       	push   $0x0
  40101b:	e9 e0 ff ff ff       	jmp    401000 <print@plt-0x10>
```

这三条指令是在做什么呢？为什么不生成一个重定位，直接跳转到实际的 print 函数？而要搞得这么麻烦？

答案是还不满足于当前的性能：完整的代码里可能会调用动态库里的的一千个函数，但是实际运行的时候，并非所有代码都会被执行，于是可能只有一小部分动态库的函数会被调用。这时候，就希望实现一点：第一次调用动态库里的函数的时候，再进行重定位，之后就一直用这个重定位好的结果。那么如果一个函数从来没有被调用过，那就省下了重定位的时间。这就是惰性（Lazy）或者说延迟（Deferred）的思想。

为了实现这个功能，它是这么实现的：

1. 第一次调用的时候，会跳转到动态链接器里，让动态链接器完成重定位，然后跳转到实际的动态库里的函数
2. 第二次和之后调用的时候，直接跳转到实际的动态库里的函数

那么怎么去记录实际的动态库里的函数的地址呢？那就找个地方，把这个地址存下来就好。第一次调用的时候，想办法进入到动态链接器，让它进行重定位。重定位完以后，就把这个地址保存下来，下次调用就会直接跳转过去了。再回看 `print@plt` 的第一条指令：

```shell
0000000000401010 <print@plt>:
  401010:	ff 25 ea 1f 00 00    	jmp    *0x1fea(%rip)        # 403000 <print>
  401016:	68 00 00 00 00       	push   $0x0
  40101b:	e9 e0 ff ff ff       	jmp    401000 <print@plt-0x10>
```

它跳转到 `0x1fea(%rip) # 0x403000` 指向的地址的内容，这里保存了未来 `print` 在动态库中的真实地址。那么问题来了，怎么实现第一次调用 `print@plt` 的时候，可以进入到动态链接器呢？`0x1fea(%rip) # 0x403000` 指向的地址的内容的初始值又是什么呢？下面的 `push` 和 `jmp` 又是在做什么？

其实，多余的两条指令，结合前面的 `0x4010000` 地址的代码，就实现了第一次调用进动态链接器的功能：

```shell
0000000000401000 <print@plt-0x10>:
  401000:	ff 35 ea 1f 00 00    	push   0x1fea(%rip)        # 402ff0 <_GLOBAL_OFFSET_TABLE_+0x8>
  401006:	ff 25 ec 1f 00 00    	jmp    *0x1fec(%rip)        # 402ff8 <_GLOBAL_OFFSET_TABLE_+0x10>
  40100c:	0f 1f 40 00          	nopl   0x0(%rax)

0000000000401010 <print@plt>:
  401010:	ff 25 ea 1f 00 00    	jmp    *0x1fea(%rip)        # 403000 <print>
  401016:	68 00 00 00 00       	push   $0x0
  40101b:	e9 e0 ff ff ff       	jmp    401000 <print@plt-0x10>

0000000000401020 <exit@plt>:
  401020:	ff 25 e2 1f 00 00    	jmp    *0x1fe2(%rip)        # 403008 <exit>
  401026:	68 01 00 00 00       	push   $0x1
  40102b:	e9 d0 ff ff ff       	jmp    401000 <print@plt-0x10>
```

初始情况下，`0x403000` 地址保存的地址是 `0x401016`，也就是 `print@plt` 的 `push` 指令的地址。那么，第一次调用 `print@plt` 会发生的事情是：

1. 调用 `print@plt`，执行 `401010:	ff 25 ea 1f 00 00    	jmp    *0x1fea(%rip)        # 403000 <print>`，此时 `0x403000` 地址保存的内容是 `0x401016`，也就是跳转到 `0x401016`
2. 执行 `401016:	68 00 00 00 00       	push   $0x0`，向栈上压入了 `0`，具体什么含义，下面会进行分析
3. 执行 `40101b:	e9 e0 ff ff ff       	jmp    401000 <print@plt-0x10>`，跳转到 `0x401000`
4. 执行 `401000:	ff 35 ea 1f 00 00    	push   0x1fea(%rip)        # 402ff0 <_GLOBAL_OFFSET_TABLE_+0x8>`，具体什么含义，下面会进行分析
5. 执行 `401006:	ff 25 ec 1f 00 00    	jmp    *0x1fec(%rip)        # 402ff8 <_GLOBAL_OFFSET_TABLE_+0x10>`，这一条指令跳转到 `0x402ff8` 地址保存的内容，这个内容就是动态链接器提供的函数（如果是 glibc 提供的动态链接器，这个函数是 [_dl_runtime_resolve](https://github.com/bminor/glibc/blob/master/sysdeps/x86_64/dl-trampoline.h)），它会负责进行重定位，重定位以后，就会把结果写到 `0x403000` 地址里

那么，之后调用 `print@plt` 会发生的事情是：

1. 调用 `print@plt`，执行 `401010:	ff 25 ea 1f 00 00    	jmp    *0x1fea(%rip)        # 403000 <print>`，此时 `0x403000` 地址保存的内容是经过重定位后的真实的 `print` 函数的地址

那么这个逻辑就清楚了：`0x403000` 保存了 `print` 函数的地址，如果还没有重定位，就指向初始化的代码 `0x401016`。这段代码向栈上压入了两个内容：

1. `print@plt` 压入了 0，`exit@plt` 压入了 1，这对应了动态符号表里这两个符号的位置，根据编号，就可以查到要找的符号名称
2. 压入了 `0x402ff0` 地址的内容，这个内容由动态链接器初始化，可以想到大概是用来表示当前可执行文件的某个指针

那么最后跳转到动态链接器里的时候，就可以根据压栈的内容，找到要重定位的函数，进行重定位。

为了保存上面的这些数据：`0x403000` 保存的 `print` 函数地址，或是动态链接器提供的 `0x402ff0` 以及 `0x402ff8`，添加了一个 `.got.plt` 段：

```shell
0000000000402fe8 <_GLOBAL_OFFSET_TABLE_>:
  402fe8:	c8 2e 40 00          	enter  $0x402e,$0x0
	...
  403000:	16                   	(bad)
  403001:	10 40 00             	adc    %al,0x0(%rax)
  403004:	00 00                	add    %al,(%rax)
  403006:	00 00                	add    %al,(%rax)
  403008:	26 10 40 00          	es adc %al,0x0(%rax)
  40300c:	00 00                	add    %al,(%rax)
	...
```

这个就叫做 Global Offset Table，这里展示的是用于 PLT 的 GOT。它的内容如下：

1. 0x402fe8 开始的 8 个字节：保存了 .dynamic 段的地址
2. 0x402ff0 开始的 8 个字节：保留给动态链接器
3. 0x402ff8 开始的 8 个字节：保留给动态链接器
4. 0x403000 开始的 8 个字节：`print` 的地址，初始化为 `0x401016`
5. 0x403008 开始的 8 个字节：`exit` 的地址，初始化为 `0x401026`

那么到这里，就完成了 PLT 以及 GOT 的分析了。

简单小结一下：

1. 为了减少动态链接要耗费的时间，采用了惰性重定位的方法
2. 为了减少重定位次数，在 PLT 里给每个要调用的动态库里的函数提供了一个跳板函数
3. 为了实现惰性重定位，第一次调用跳板函数，会调用动态链接器的函数来实现重定位，通过压栈来区分要重定位的函数
4. 惰性重定位完成以后，跳板函数直接 jmp 到目标函数

## 实现

综合以上的分析，落到实现上，需要做这些处理：

1. 遇到动态链接库的时候，不再复制动态链接库的内容到各个段中，更新符号表并打上标记
2. 生成 .plt 和 .got.plt 段的开头
    1. .plt 开头要生成 push，jmp 和 nop 的指令序列
    2. .got.plt 段开头保存 .dynamic 段的地址，然后预留 16 字节给动态链接器
2. 要调用动态链接库里的函数的时候，在 PLT 和 GOT 里生成对应的项：
    1. .plt 里要生成 jmp，push 和 jmp 三条指令的序列
    2. .got.plt 要添加用于保存实际地址的一项
    3. .rela.plt 也相应地更新，指向 .got.plt 里对应项的地址
3. 根据命令行参数，设置 DT_INTERP；对于依赖的动态库，添加 DT_NEEDED
4. 把 .plt、.got.plt 相关的信息记录到 .dynamic 段中

这个过程我用 Rust 完成了实现，链接器部分的代码量大概是 1000 行，比上一个版本多 400 行。

## 总结

这就是《开发一个链接器》系列博客的最后一篇博客了。回顾一下，我们都完成了哪些功能：

1. 第一篇博客：支持单个 ELF 对象文件的链接
2. 第二篇博客：支持多个 ELF 对象文件的链接
3. 第三篇博客：支持生成动态库
4. 第四篇博客：支持动态链接

这距离一个真正能用的链接器还差很多东西：PIE，Linker Script，前面出现过但是没有讨论的 `.eh_frame` 的处理等等。但希望这个系列博客可以让你对链接器的工作方式有进一步的了解。

我实现的链接器代码已经开源在 [jiegec/cold](https://github.com/jiegec/cold)，编写的过程和博客的时间基本是一致的，针对相应博客的进度，可以找 git commit 历史，查看对应版本的实现。

## 参考

最后给出一些文档，可供实现时参考：

- [All about Procedure Linkage Table](https://maskray.me/blog/2021-09-19-all-about-procedure-linkage-table)
