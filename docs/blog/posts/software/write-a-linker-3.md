---
layout: post
date: 2024-04-06
tags: [linux,linker,elf,write-a-linker]
categories:
    - software
---

# 开发一个链接器（3）

## 前言

这个系列的前两篇博客实现了一个简单的静态链接器，它可以输入若干个 ELF .o 文件，输出 ELF 可执行文件。接下来，我们进一步支持动态库：输入若干个 ELF .o 文件，输出 ELF 动态库。

<!-- more -->

注意，本篇博客只讨论如何生成 ELF 动态库，并不涉及如何链接 ELF 动态库，这将会作为后续文章的内容。

## 回顾

首先回顾一下：在这个系列的前两篇博客中，我们观察了现有链接器的工作过程，并且实现了一个最简单的链接器：输入若干个 ELF object，链接成一个可以运行的 ELF 可执行文件。这个过程包括：

1. 解析输入的若干个 ELF，收集各个 section 需要保留下来的内容，合并来自不同 ELF 的同名 section
2. 规划将要生成的 ELF 可执行文件的内容布局：开始是固定的文件头，之后是各个 section，计算出它们从哪里开始到哪里结束
3. 第二步完成以后，就可以知道在运行时，各个 section 将会被加载到哪个地址上，进而更新符号表，得到每个符号在运行时会处在哪个地址上；此时我们就可以计算重定位，把地址按照预设的规则填入到对应的地方
4. 最后按照预设的文件布局，把文件内容写入到 ELF 文件中

接下来我们就要实现生成动态库文件，让我们首先分析一下，这里的不同在哪里。

## 分析

### 动态链接

本系列的前面两篇文章博客实现的都是静态链接：由静态链接器完成所有的事情，得到一个可执行文件，这个可执行文件加载到内存中就可以跑，不需要额外的操作。但是静态链接也有一些缺点：

1. 二进制体积大，同样的代码出现在很多个可执行文件中，同时因为这些代码经过了重定位，内容有些许差别，无法复用，浪费硬盘和内存空间
2. 如果某个底层库出现安全问题，由于这个库可能静态链接到了很多不同的程序里，为了去除有问题的代码，需要把所有用到这个库的程序都重新编译一遍，才能保证安全的代码被链接进去

为了解决这些问题，常用的解决办法是动态链接：静态链接器只完成一部分的链接，剩下的一部分工作，要等到程序启动的时候完成，那么程序在启动时由动态链接器完成的链接，就是动态链接。举个例子，一段 C 代码调用了标准库里的 C 函数，要么用静态链接，把整个标准库连接到可执行文件里；要么就用动态链接，在可执行文件里保留与函数调用相关的重定位，在程序执行时，再让动态链接器来完成最后的链接过程。动态链接解决了上面提到的问题：

1. 由于动态链接等到最后程序启动时才进行，所以可执行文件本身的体积就可以做到很小，不再需要静态链接一个可能巨大的静态库
2. 动态链接是每次程序启动时进行，所以如果动态库文件替换了，那么程序未来再次启动时，自然就会用到新的动态库文件，不需要重新编译程序

当然了，动态链接也带来了新的要求和挑战：

1. 静态链接的时候，因为内存地址空间里只会加载一个可执行文件，所以所有地址都可以预先算好，不用担心出现冲突；而动态链接的时候，同一个动态库没办法保证总是映射到同一个地址上：如果每个动态库都写死了自己要加载到的地址，那么不同的动态库选了同样的地址，是否就意味着不能同时用这两个动态库了？因此动态库要支持加载到不同的地址上，为了达到这个目标，就需要在编译动态库的时候，以 PIC（Position Independent Code，位置无关代码）的方式编译，使得无论动态库加载到哪里，程序都可以正常运行。下面会给出一个例子
2. 由于程序每次启动都需要动态链接，那么动态链接的性能就要尽量好；为了达到这个目的，后面会看到静态链接器和动态链接器是如何配合着提高性能的

### 生成动态库

回顾一下，在上一篇文章中，我们把代码分成了两部分：`main.s` 和 `printer.s`，前者调用后者实现的 `print` 和 `exit` 函数：

```asm
# https://gist.github.com/adrianratnapala/1321776
# printer.s
    .section .rodata
hello:
    .string "Hello world!\n"


    .section .text
    .globl print
print:
    # write(1, hello, 13)
    mov     $1, %rdi
    mov     $hello, %rsi
    mov     $13, %rdx
    mov     $1, %rax
    syscall
    ret

    .globl exit
exit:
    # _exit(0)
    xor     %rdi, %rdi
    mov     $60, %rax
    syscall
```

```asm
# main.s
    .section .text
    .globl _start
_start:
    call print
    call exit
```

那么我们就想把 `printer.s` 编译成一个动态库 `libprinter.so`，然后 `main.s` 编译成可执行文件，动态链接到 `libprinter.so`。为了生成动态链接库，需要为 `ld` 添加 `-shared` 命令行参数：

```shell
$ as main.s -o main.o
$ as printer.s -o printer.o
# ld -shared: generate shared library
$ ld -shared printer.o -o libprinter.so
ld: printer.o: relocation R_X86_64_32S against `.rodata' can not be used when making a shared object; recompile with -fPIC
ld: failed to set dynamic section sizes: bad value
```

和往常一样，我们分别为 `main.s` 和 `printer.s` 调用汇编器 `as`，但这次，单独用 `printer.o` 链接出动态库 `libprinter.so`，不幸的是，它报错了，告诉我们生成动态库的时候，不允许出现 `R_X86_64_32S` 的 relocation 类型：`ld: printer.o: relocation R_X86_64_32S against ``.rodata' can not be used when making a shared object`。回忆第一篇博客，`R_X86_64_32S` 的意思是把目的符号的绝对地址以 32 位有符号数的形式填写，但前面也提到，动态库是无法提前知道自己会被加载到哪个地址上的，链接器没办法提前知道目的符号的绝对地址。这说明我们需要把 `printer.s` 改写成只用相对地址，不用绝对地址，这样就成为位置无关代码（PIC）了。链接器还贴心地告诉我们，可以给编译器传 `-fPIC` 参数来让编译器在编译 C 代码的时候生成位置无关代码（PIC）。不过我们正在手写汇编，那就必须手动改写成位置无关代码了，怎么改呢？

既然不允许出现的是 `R_X86_64_32S`，我们要找到产生这个 relocation 的汇编代码：

```asm
    mov     $hello, %rsi
```

它的目的是把 `hello` 的地址写到 `%rsi` 寄存器中，但是这个写法会要求链接器以立即数的形式把绝对地址写进去。而我们想要的是地址无关代码，那么就需要用到相对地址。在上一篇文章中，在什么地方出现了相对地址？上一篇文章中，`main.s` 调用 `print` 和 `exit` 时用到了 `R_X86_64_PC32`，它的立即数记录的是相对地址偏移。如果在这里，也让链接器生成一个相对的 relocation，就可以实现地址无关了，这条指令是：

```asm
    lea     hello(%rip), %rsi
```

`lea` 是 x86 的 LEA（Load Effective Address）指令，它的功能是计算 `%rip` 加立即数的值，写入到 `%rsi` 的值，而这个立即数就是 `hello` 相对于 `%rip` 的相对地址偏移。很遗憾，汇编器没办法帮我们做这个改写，必须在写代码的时候就想着要写地址无关代码。改写后的 `printer.s` 如下：

```asm
# https://gist.github.com/adrianratnapala/1321776
# printer.s
    .section .rodata
hello:
    .string "Hello world!\n"


    .section .text
    .globl print
print:
    # write(1, hello, 13)
    mov     $1, %rdi
    # this instruction requires absolute addressing
    # mov     $hello, %rsi
    # this one is position independent
    lea     hello(%rip), %rsi
    mov     $13, %rdx
    mov     $1, %rax
    syscall
    ret

    .globl exit
exit:
    # _exit(0)
    xor     %rdi, %rdi
    mov     $60, %rax
    syscall
```

可以观察到，它确实产生了一个相对的 relocation `R_X86_64_PC32`：

```shell
$ as printer.s -o printer.o
$ objdump -S -r printer.o

printer.o:     file format elf64-x86-64


Disassembly of section .text:

0000000000000000 <print>:
   0:   48 c7 c7 01 00 00 00    mov    $0x1,%rdi
   7:   48 8d 35 00 00 00 00    lea    0x0(%rip),%rsi        # e <print+0xe>
                        a: R_X86_64_PC32        .rodata-0x4
   e:   48 c7 c2 0d 00 00 00    mov    $0xd,%rdx
  15:   48 c7 c0 01 00 00 00    mov    $0x1,%rax
  1c:   0f 05                   syscall
  1e:   c3                      ret

000000000000001f <exit>:
  1f:   48 31 ff                xor    %rdi,%rdi
  22:   48 c7 c0 3c 00 00 00    mov    $0x3c,%rax
  29:   0f 05                   syscall
```

虽然绝对地址无法确定，但静态链接器依然可以计算出相对地址偏移，完成 relocation 的计算。重新链接，发现它确实成功生成了动态库，不再报错：

```shell
$ ld -shared printer.o -o libprinter.so
```

### 观察动态库

接下来就来看看新生成的 `libprinter.so` 和之前的可执行文件有什么不同，首先是 `ELF Header` 部分：

```shell
$ readelf -a libprinter.so
ELF Header:
  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00 
  Class:                             ELF64
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              DYN (Shared object file)
  Machine:                           Advanced Micro Devices X86-64
  Version:                           0x1
  Entry point address:               0x0
  Start of program headers:          64 (bytes into file)
  Start of section headers:          12584 (bytes into file)
  Flags:                             0x0
  Size of this header:               64 (bytes)
  Size of program headers:           56 (bytes)
  Number of program headers:         6
  Size of section headers:           64 (bytes)
  Number of section headers:         12
  Section header string table index: 11
```

和可执行文件的区别在于，`Type` 是 `DYN (Shared object file)`，表示这是一个动态库文件；`Entry point address` 等于零，因为动态库没有入口，入口地址还是由可执行程序提供。

接下来是 Section 部分：

```shell
Section Headers:
  [Nr] Name              Type             Address           Offset
       Size              EntSize          Flags  Link  Info  Align
  [ 0]                   NULL             0000000000000000  00000000
       0000000000000000  0000000000000000           0     0     0
  [ 1] .hash             HASH             0000000000000190  00000190
       0000000000000018  0000000000000004   A       3     0     8
  [ 2] .gnu.hash         GNU_HASH         00000000000001a8  000001a8
       0000000000000028  0000000000000000   A       3     0     8
  [ 3] .dynsym           DYNSYM           00000000000001d0  000001d0
       0000000000000048  0000000000000018   A       4     1     8
  [ 4] .dynstr           STRTAB           0000000000000218  00000218
       000000000000000c  0000000000000000   A       0     0     1
  [ 5] .text             PROGBITS         0000000000001000  00001000
       000000000000002b  0000000000000000  AX       0     0     1
  [ 6] .rodata           PROGBITS         0000000000002000  00002000
       000000000000000e  0000000000000000   A       0     0     1
  [ 7] .eh_frame         PROGBITS         0000000000002010  00002010
       0000000000000000  0000000000000000   A       0     0     8
  [ 8] .dynamic          DYNAMIC          0000000000003f40  00002f40
       00000000000000c0  0000000000000010  WA       4     0     8
  [ 9] .symtab           SYMTAB           0000000000000000  00003000
       00000000000000a8  0000000000000018          10     5     8
  [10] .strtab           STRTAB           0000000000000000  000030a8
       0000000000000025  0000000000000000           0     0     1
  [11] .shstrtab         STRTAB           0000000000000000  000030cd
       0000000000000056  0000000000000000           0     0     1
Key to Flags:
  W (write), A (alloc), X (execute), M (merge), S (strings), I (info),
  L (link order), O (extra OS processing required), G (group), T (TLS),
  C (compressed), x (unknown), o (OS specific), E (exclude),
  D (mbind), l (large), p (processor specific)

There are no section groups in this file.
```

可以观察到多了几个没有见到过的 section，这里简要介绍一下，后面会详细解释：

1. `.hash` 和 `.gnu.hash`：从名字可以猜出来，这是某种哈希表，它的作用是提供一个符号名字到符号的映射，提高动态链接器查找符号的性能
2. `.dynsym`：Dynamic Symbol，和动态链接有关的动态符号表
3. `.dynstr`：Dynamic String，和动态链接有关的字符串的表
4. `.dynamic`：Dynamic，向动态链接器提供了一些信息

此外，这些段的地址都从 0 开始，而不是可执行文件那样，从 0x400000 开始，毕竟动态库是可能被加载到不同地址上的，是没办法提前确定的。

接下来是 Program Header 部分：

```asm
Program Headers:
  Type           Offset             VirtAddr           PhysAddr
                 FileSiz            MemSiz              Flags  Align
  LOAD           0x0000000000000000 0x0000000000000000 0x0000000000000000
                 0x0000000000000224 0x0000000000000224  R      0x1000
  LOAD           0x0000000000001000 0x0000000000001000 0x0000000000001000
                 0x000000000000002b 0x000000000000002b  R E    0x1000
  LOAD           0x0000000000002000 0x0000000000002000 0x0000000000002000
                 0x0000000000000010 0x0000000000000010  R      0x1000
  LOAD           0x0000000000002f40 0x0000000000003f40 0x0000000000003f40
                 0x00000000000000c0 0x00000000000000c0  RW     0x1000
  DYNAMIC        0x0000000000002f40 0x0000000000003f40 0x0000000000003f40
                 0x00000000000000c0 0x00000000000000c0  RW     0x8
  GNU_RELRO      0x0000000000002f40 0x0000000000003f40 0x0000000000003f40
                 0x00000000000000c0 0x00000000000000c0  R      0x1

 Section to Segment mapping:
  Segment Sections...
   00     .hash .gnu.hash .dynsym .dynstr 
   01     .text 
   02     .rodata 
   03     .dynamic 
   04     .dynamic 
   05     .dynamic 
```

可以看到，除了已有的 `LOAD` 以外，还出现了新的项目：

1. `DYNAMIC`：告诉动态链接器，`.dynamic` section 在哪个地方
2. `GNU_RELRO`：这是 GNU 链接器安全性扩展，意思是在动态链接器完成重定位后，哪些内存区域可以设置为只读，防止程序篡改

紧接着就是 `.dynamic` section 的内容：

```shell
Dynamic section at offset 0x2f40 contains 7 entries:
  Tag        Type                         Name/Value
 0x0000000000000004 (HASH)               0x190
 0x000000006ffffef5 (GNU_HASH)           0x1a8
 0x0000000000000005 (STRTAB)             0x218
 0x0000000000000006 (SYMTAB)             0x1d0
 0x000000000000000a (STRSZ)              12 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000000 (NULL)               0x0
```

表示这个动态库向动态链接器提供了一些会在动态链接中用到的信息：

1. `HASH`：`.hash` section 的地址
2. `GNU_HASH`：`.gnu2hash` section 的地址
3. `STRTAB`: `.dynstr` section 的地址
4. `SYMTAB`: `.dynsym` section 的地址
5. `STRSZ`: `.dynstr` section 的大小
6. `SYMENT`: `.dynsym` 每一项的大小
7. `NULL`: 表示后面没有更多内容了

你可能会奇怪，这里面的地址和大小信息，其实都可以从 Section Headers 里找到，为什么还要多此一举，放到这里呢？首先，这里可以存的东西还有很多，不止是这些，后续会看到更多的例子；其次，前文提到，动态链接的性能要求是比较高的，为了减少它解析 ELF 的负担，提前把要用的数据准备好。

下面是 relocation 的部分，不出意料，没有 relocation，因为静态链接器已经把 `printer.s` 里涉及到的 relocation 都计算完成了。

```shell
There are no relocations in this file.
No processor specific unwind information to decode
```

接下来是符号表，有两份，`.dynsym` 是动态符号表，`.symtab` 是原来静态链接使用的符号表：

```shell
Symbol table '.dynsym' contains 3 entries:
   Num:    Value          Size Type    Bind   Vis      Ndx Name
     0: 0000000000000000     0 NOTYPE  LOCAL  DEFAULT  UND 
     1: 0000000000001000     0 NOTYPE  GLOBAL DEFAULT    5 print
     2: 000000000000101f     0 NOTYPE  GLOBAL DEFAULT    5 exit

Symbol table '.symtab' contains 7 entries:
   Num:    Value          Size Type    Bind   Vis      Ndx Name
     0: 0000000000000000     0 NOTYPE  LOCAL  DEFAULT  UND 
     1: 0000000000000000     0 FILE    LOCAL  DEFAULT  ABS printer.o
     2: 0000000000002000     0 NOTYPE  LOCAL  DEFAULT    6 hello
     3: 0000000000000000     0 FILE    LOCAL  DEFAULT  ABS 
     4: 0000000000003f40     0 OBJECT  LOCAL  DEFAULT    8 _DYNAMIC
     5: 0000000000001000     0 NOTYPE  GLOBAL DEFAULT    5 print
     6: 000000000000101f     0 NOTYPE  GLOBAL DEFAULT    5 exit
```

观察可以发现，`.dynsym` 只保留了那些外部程序可能会用到的符号，也就是 `print` 和 `exit`，而内部自己用的 `hello` 没有放在里面，只保留可能要用到的东西，给动态链接器减负。

最后，`readelf` 还贴心地计算了一下哈希表的平均查询次数：

```shell
Histogram for bucket list length (total of 1 bucket):
 Length  Number     % of total  Coverage
      0  0          (  0.0%)
      1  0          (  0.0%)      0.0%
      2  1          (100.0%)    100.0%

Histogram for `.gnu.hash' bucket list length (total of 2 buckets):
 Length  Number     % of total  Coverage
      0  0          (  0.0%)
      1  2          (100.0%)    100.0%

No version information found in this file.
```

后面会再细讲一下它所采用的哈希表的架构。

结合上面的观察，可以得到一个初步的印象，比较生成可执行文件与生成动态链接库的区别：

1. ELF 文件类型不同，DYN (Shared object file) vs EXEC (Executable file)
2. 动态库有额外的一套用于动态链接的 section，包括动态的符号表，动态的字符串表，动态表（`.dynamic`），以及哈希表（实现符号名称到符号的映射）
3. 动态库的加载地址不确定，在 ELF 中从 0 开始计算，需要地址无关代码

### 使用动态库

生成动态库 `libprinter.so` 以后，最后还需要让 `main.o` 动态链接 `libprinter.so`，并运行：

```shell
# ld -dynamic-linker: Set path to dynamic linker for the executable
$ ld -dynamic-linker /lib64/ld-linux-x86-64.so.2 main.o libprinter.so -o main
$ LD_LIBRARY_PATH=$PWD ./main
Hello world!
```

这里特别指定了 `main` 的动态链接器路径为 `/lib64/ld-linux-x86-64.so.2`，这是因为 `main` 在启动时，需要由动态链接器来完成最后的动态链接，那么用哪个动态链接器去做这个事情呢？这里就是在指定动态链接器的路径。启动 `main` 程序的时候，为了让动态链接器找到当前目录下的 `libprinter.so`，添加了环境变量 `LD_LIBRARY_PATH` 并设置为当前目录。这样 `main` 程序就可以正常运行起来了。

虽然 `libprinter.so` 出现在了 `ld` 的命令行参数中，但并不代表它的内容会被静态链接到 `main` 当中：实际上，静态链接器会以某种形式告诉动态链接器，在 `main` 程序启动时，如何去动态链接 `libprinter.so`。这个具体形式，会在下一篇博客中详细介绍。现在先讨论一下，动态链接器可能需要做些什么：

1. 根据 `main` 程序记录的信息，去加载 `libprinter.so` 的内容，加载到某个内存地址上
2. `main` 程序需要调用 `print` 和 `exit` 函数，那么动态链接器就需要去查询，`libprinter.so` 有没有这些函数，如果有的话，地址是什么

这个时候，动态链接器就会用到上面出现的 `.dynamic` section，根据它的内容，记录下哈希表的位置。程序要调用 `print` 函数，那就在哈希表里查询 `print` 函数对应的符号，如果找到了，那就可以得到 `print` 函数在 `libprinter.so` 里的偏移，偏移再加上 `libprinter.so` 动态加载的基地址，就得到了实际是 `print` 函数的地址，就可以正常调用函数了。

这个查询过程可能会发生很多次，所以性能是很重要的，所以引入了哈希表。那么这个哈希表具体是怎么一个构造呢？以往在数据结构课上讲哈希表的时候，更多是在内存中用哈希表，用拉链法解决哈希冲突的话，直接用指针数组就可以了；而这里的哈希表需要保存在文件中，所以都是用下标来替代指针。

首先讲传统的 SystemV Hash 实现，它保存在 `.hash` 段内，使用拉链法解决哈希冲突。它的结构是这样的：

1. 两个 32 位数 `nbucket` 和 `nchain`，分别保存有多少个 bucket 和多少个 chain
2. 接下来是 `nbucket` 个 32 位数（bucket 数组），对应哈希表的 bucket，内容是 chain 数组的下标，也就是拉链法里，链表的起始结点下标
3. 最后是 `nchain` 个 32 位数（chain 数组），记录链表的下一个结点的下标，如果链表后继结点不存在，则保存 `STN_UNDEF`

chain 数组和动态符号表大小相同，元素一一对应。那么用哈希表查询符号的过程如下：

1. 对符号名称求哈希值，这个函数是规定好的，输入一个字符串，输出一个 32 位整数
2. 查询哈希值对应的 bucket，得到 chain 数组的下标，这个下标也对应了一个符号
3. 去符号表查看这个符号是否是要查询的符号（字符串比较），如果是，那就找到了目标符号
4. 如果不是，检查 chain 数组，查看链表是否有后继结点，如果有，那么沿着链表，逐个检查符号表中的符号
5. 如果遍历到 `STT_UNDEF` 都没有找到匹配的符号，说明目标符号不存在

可以看到，这是比较原始的哈希表实现方法，为了减少碰撞，就需要比较大的 `nbucket`，但就需要更多的空间了。

为了解决动态库日益增长的符号表大小和不够高的动态链接性能之间的矛盾，目前常见另一种哈希表的实现：GNU Hash，它保存在 `.gnu.hash` 段内。虽说是哈希表，但实际上是两种数据结构的组合：

1. Bloom Filter：Bloom Filter 是一种快速判断某个值是否不在某个集合中的数据结构 [^1]，在这里，就是判断符号是否不在该动态库的符号表中，如果不在，那就不需要进行后续的哈希查表
2. 哈希表：相比 SystemV Hash，做了这些改动：
    1. 拉链法的内存访问比较随机，缓存局部性差；所以改成了线性法：把符号按照 bucket 排序，使得同一个 bucket 内的所有符号在数组中连续存放，改进了缓存局部性
    2. 在 SystemV Hash 中，在链表遍历的时候，每个结点都需要进行一次字符串的比较，这是比较慢的；在 GNU Hash 中，不再需要保存链表的后继结点的变化，改为保存对应符号的哈希值，那么在遍历连续的 bucket 内的符号时，首先比较哈希值是否相等，不相等时就不需要进行字符串比较了
    3. 为了判断当前 bucket 内符号是否遍历完成，拿哈希的最低位做标识，比较哈希时不考虑最低位

[^1]: 这句话有点拗口，但是你没有看错，Bloom Filter 只能确定某个元素不在集合中，但反之，不能确定元素是否一定在集合中。它的原理是，计算集合的每个元素的哈希值，构建出一个 bitset，把哈希值对应的位设为 1，其余设为 0；查询时，计算元素的哈希值，检查 bitset 中对应位是否为 0：如果为 0，那么元素一定不在集合中；如果为 1，由于可能出现哈希冲突，不能确定该元素一定在集合中。

那么用 GNU Hash 查询符号表的过程如下：

1. 在 Bloom Filter 中查询目标符号是否不存在，如果不存在，那就说明目标符号不存在
2. 计算出符号名称的哈希，找到对应的 bucket，遍历 bucket 内的元素，判断目标符号与当前元素的哈希值是否相等，如果相等，并且字符串比较也相同，那就找到了目标符号；如果没查到，就查到直到 bucket 结束

可以看到，这个算法会比 SystemV Hash 性能更高，构建起来自然也更加复杂。

## 实现

结合以上的分析，我们就可以在上一次博客的基础上实现第三版的链接器，这个链接器可以支持输入多个 ELF .o 文件，输出可执行文件或者动态库。额外的需要实现的内容，包括：

1. 从符号表（`.symtab`）中，取出那些 GLOBAL 的符号，构建出动态符号表（`.dynsym`），计算出哈希表，保存在 `.hash` 和 `.gnu.hash` 段中
2. 构造 `.dynamic` section，并在 Program Header 中添加 DYNAMIC，告诉动态链接器，动态链接时所需要的各种信息

这个过程我用 Rust 完成了实现，链接器部分的代码量大概是 600 行，比上一个版本多 200 行。

## 参考

最后给出一些文档，可供实现时参考：

- [Dynamic Linking](https://refspecs.linuxbase.org/elf/gabi4+/ch5.dynamic.html)
- [ELF: better symbol lookup via DT_GNU_HASH](https://flapenguin.me/elf-dt-gnu-hash)
- [GNU Hash ELF Sections](https://blogs.oracle.com/solaris/post/gnu-hash-elf-sections)