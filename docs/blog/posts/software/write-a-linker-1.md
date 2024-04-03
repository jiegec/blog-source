---
layout: post
date: 2024-02-18
tags: [linux,linker,elf,write-a-linker]
categories:
    - software
---

# 开发一个链接器（1）

## 前言

无论是在课程中还是实践中，都经常和链接器打交道。在这个过程中，大概了解了它的工作原理，对于常见的错误可以知道大概是怎么一回事，以及如何解决。但最近遇到一些涉及到链接器内部的问题，才发现自己对链接器的内部的了解还是比较匮乏的。因此想到自己开发一个链接器，在开发的过程中学习。

<!-- more -->

本文假定读者已经对链接器有了一定的了解，如果你还不了解链接的大致过程，可以先学习网络上的资料。

这个系列的第一篇博客的目标是：实现一个最简单的静态链接器，输入单个 ELF .o 文件，输出 ELF 可执行文件。

## 分析

开发一个链接器，先从最简单的情况开始：输入一个 ELF .o 文件，输出一个 ELF 可执行文件。为了避免引入 libc 等依赖，从网上找了一段直接用 syscall 打印字符串的汇编代码，做了简单修改：

```asm
# From https://gist.github.com/adrianratnapala/1321776
# Hello World on amd64 under Linux.
#
# One way to build this is with: 
#
#    gcc hello.S  -s -nostartfiles -nostdlib -o hello
#
# for syscall numbers look in /usr/include/asm/unistd_64.h
# for examples look at http://99-bottles-of-beer.net/language-assembler-(amd64)-933.html
# for inspiration look at http://www.muppetlabs.com/~breadbox/software/tiny/teensy.html

    .section .rodata
hello:
    .string "Hello world!\n"


    .section .text
    .globl _start
_start:
    # write(1, hello, 13)
    mov     $1, %rdi
    mov     $hello, %rsi
    mov     $13, %rdx
    mov     $1, %rax
    syscall

    # _exit(0)
    xor     %rdi, %rdi
    mov     $60, %rax
    syscall
```

??? question "这段汇编做了什么？"

    这段汇编要实现的是向标准输出打印 `Hello world!\n`，但为了避免引入 C 标准库（libc），只能直接进行系统调用来完成打印。在 Linux 中，向标准输出打印，实际上就是向标准输出对应的 file handle（简称 fd，通常约定标准输入 stdin 是 0，标准输出 stdout 是 1，标准错误输出 stderr 是 2）写入要打印的内容。而这个需要通过调用 `write` syscall 来实现。

    知道这一点以后，就要去查找 Linux 的 [write syscall](https://man7.org/linux/man-pages/man2/write.2.html) 的文档。文档告诉你，第一个参数是 `fd`，第二个参数 `buf` 指向要写入的数据，第三个参数 `count` 是要写入的数据的长度。结合上面的内容，为了打印 `Hello world!\n`，实际上要完成的相当于是 C 代码中的 `write(1, hello, 13)`，其中 1 就是 stdout 的 fd，`hello` 指向保存 `Hello world!\n` 字符串的地址，13 是字符串的长度。那么接下来就要研究，如何用汇编调用 syscall。

    接下来，要知道在 amd64 Linux 下，如何用汇编调用 syscall。首先找到 [amd64 Linux syscall 调用约定](https://www.ucw.cz/~hubicka/papers/abi/node33.html#features)，它告诉我们：

    1. syscall 编号保存在 rax 寄存器中
    2. syscall 的参数按顺序，依次保存在 rdi, rsi, rdx, r10, r8, r9 寄存器中
    3. 用 syscall 指令调用 syscall
    3. syscall 的返回值也会保存在 rax 寄存器中

    既然要调用 `write(1, hello, 13)`，那就按照上面的要求，设置 `rdi=1`、`rsi=hello` 和 `rdx=13`，最后在 [amd64 Linux syscall table](https://filippo.io/linux-syscall-table/) 中找到 `write` syscall 的编号是 1，所以设置 `rax=1`。到这里，调用 `write` syscall 的所有准备任务都已经完成，调用 `syscall` 指令即可完成系统调用。这样就完成了一次 `Hello world!\n` 的打印：

    ```asm
    # write(1, hello, 13)
    mov     $1, %rdi
    mov     $hello, %rsi
    mov     $13, %rdx
    mov     $1, %rax
    syscall
    ```

    后面 `exit(0)` 的系统调用也是类似的，不再赘述。代码中写 `_exit(0)` 是为了和 C 标准库中的 `exit(0)` 做区分：前者直接退出程序（只会结束当前线程，但是由于当前进程只有一个线程，所以整个进程都结束了），而后者会做一些清理工作，见 [_exit manpage](https://man7.org/linux/man-pages/man2/exit.2.html)。



由于是汇编代码，所以直接调用汇编器生成 ELF .o 文件，然后观察它的内容：

```shell
$ as helloworld_asm.s -o helloworld_asm.o
$ readelf -a helloworld_asm.o
# Output is shown below
```

下面观察 readelf 命令的输出，首先是 ELF 的头部，交代了文件类型，执行在什么指令集架构上等等：

```shell
ELF Header:
  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00 
  Class:                             ELF64
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              REL (Relocatable file)
  Machine:                           Advanced Micro Devices X86-64
  Version:                           0x1
  Entry point address:               0x0
  Start of program headers:          0 (bytes into file)
  Start of section headers:          320 (bytes into file)
  Flags:                             0x0
  Size of this header:               64 (bytes)
  Size of program headers:           0 (bytes)
  Number of program headers:         0
  Size of section headers:           64 (bytes)
  Number of section headers:         9
  Section header string table index: 8
```

接下来是比较重要的部分，ELF 包括多个 section，根据用途，不同的指令和数据会放在对应的 section 中，例如 .text 存放指令，.data .bss .rodata 存放各种数据，.rela 存放重定向（relocation）。

```shell
Section Headers:
  [Nr] Name              Type             Address           Offset
       Size              EntSize          Flags  Link  Info  Align
  [ 0]                   NULL             0000000000000000  00000000
       0000000000000000  0000000000000000           0     0     0
  [ 1] .text             PROGBITS         0000000000000000  00000040
       000000000000002a  0000000000000000  AX       0     0     1
  [ 2] .rela.text        RELA             0000000000000000  000000e8
       0000000000000018  0000000000000018   I       6     1     8
  [ 3] .data             PROGBITS         0000000000000000  0000006a
       0000000000000000  0000000000000000  WA       0     0     1
  [ 4] .bss              NOBITS           0000000000000000  0000006a
       0000000000000000  0000000000000000  WA       0     0     1
  [ 5] .rodata           PROGBITS         0000000000000000  0000006a
       000000000000000e  0000000000000000   A       0     0     1
  [ 6] .symtab           SYMTAB           0000000000000000  00000078
       0000000000000060  0000000000000018           7     3     8
  [ 7] .strtab           STRTAB           0000000000000000  000000d8
       000000000000000e  0000000000000000           0     0     1
  [ 8] .shstrtab         STRTAB           0000000000000000  00000100
       0000000000000039  0000000000000000           0     0     1
Key to Flags:
  W (write), A (alloc), X (execute), M (merge), S (strings), I (info),
  L (link order), O (extra OS processing required), G (group), T (TLS),
  C (compressed), x (unknown), o (OS specific), E (exclude),
  D (mbind), l (large), p (processor specific)
```

那么链接器需要特别关注和处理的就是里面的 relocation 以及符号表（Symbol table）了：在汇编生成 .o 文件的时候，由于指令引用了数据（"Hello world!\n"），但是又无法提前知道数据所处的地址，因此汇编器会生成一个 relocation 条目，也就是下面的 `R_X86_64_32S`：

```shell
Relocation section '.rela.text' at offset 0xe8 contains 1 entry:
  Offset          Info           Type           Sym. Value    Sym. Name + Addend
00000000000a  00010000000b R_X86_64_32S      0000000000000000 .rodata + 0
No processor specific unwind information to decode

Symbol table '.symtab' contains 4 entries:
   Num:    Value          Size Type    Bind   Vis      Ndx Name
     0: 0000000000000000     0 NOTYPE  LOCAL  DEFAULT  UND 
     1: 0000000000000000     0 SECTION LOCAL  DEFAULT    5 .rodata
     2: 0000000000000000     0 NOTYPE  LOCAL  DEFAULT    5 hello
     3: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT    1 _start
```

而当链接器确定了代码和数据的地址以后，发现部分 relocation 的地址已经可以确定下来，那么就可以直接把地址写入到指令中，不再需要动态的 relocation。符号表则提供了符号到地址的映射，做符号解析的时候会用到。

下面我们要实现一个最简单的链接器，就把这一个 ELF .o 生成一个可执行文件。可以先让现有的 ld 链接出来，看看它的最终效果是什么样的：

```shell
$ ld helloworld_asm.o -o helloworld_asm
$ readelf -a helloworld_asm
# Output is shown below
```

首先是 ELF 的头部，这次可以看到文件类型变成了可执行文件，并且有了一个入口地址（0x401000）：

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
  Entry point address:               0x401000
  Start of program headers:          64 (bytes into file)
  Start of section headers:          8472 (bytes into file)
  Flags:                             0x0
  Size of this header:               64 (bytes)
  Size of program headers:           56 (bytes)
  Number of program headers:         3
  Size of section headers:           64 (bytes)
  Number of section headers:         6
  Section header string table index: 5
```

而 section 也变得更少：没用到的 .data .bss 段都删掉了，并且也没有了 relocation，这是因为这个程序里所有的 relocation 都是内部的，链接的时候就直接计算出地址了并填进去了。

```shell
Section Headers:
  [Nr] Name              Type             Address           Offset
       Size              EntSize          Flags  Link  Info  Align
  [ 0]                   NULL             0000000000000000  00000000
       0000000000000000  0000000000000000           0     0     0
  [ 1] .text             PROGBITS         0000000000401000  00001000
       000000000000002a  0000000000000000  AX       0     0     1
  [ 2] .rodata           PROGBITS         0000000000402000  00002000
       000000000000000e  0000000000000000   A       0     0     1
  [ 3] .symtab           SYMTAB           0000000000000000  00002010
       00000000000000a8  0000000000000018           4     3     8
  [ 4] .strtab           STRTAB           0000000000000000  000020b8
       0000000000000030  0000000000000000           0     0     1
  [ 5] .shstrtab         STRTAB           0000000000000000  000020e8
       0000000000000029  0000000000000000           0     0     1
Key to Flags:
  W (write), A (alloc), X (execute), M (merge), S (strings), I (info),
  L (link order), O (extra OS processing required), G (group), T (TLS),
  C (compressed), x (unknown), o (OS specific), E (exclude),
  D (mbind), l (large), p (processor specific)
```

下面是一个可执行文件比较特殊的点，它有 segment 的概念，指示内核应该怎样把程序加载到内存里：

```shell
Program Headers:
  Type           Offset             VirtAddr           PhysAddr
                 FileSiz            MemSiz              Flags  Align
  LOAD           0x0000000000000000 0x0000000000400000 0x0000000000400000
                 0x00000000000000e8 0x00000000000000e8  R      0x1000
  LOAD           0x0000000000001000 0x0000000000401000 0x0000000000401000
                 0x000000000000002a 0x000000000000002a  R E    0x1000
  LOAD           0x0000000000002000 0x0000000000402000 0x0000000000402000
                 0x000000000000000e 0x000000000000000e  R      0x1000

 Section to Segment mapping:
  Segment Sections...
   00     
   01     .text 
   02     .rodata 
```

可以看到，它指示内核从文件的三个偏移处加载三个部分内容到内存里，分别是文件头、.text 段以及 .rodata 段。加载完以后，内核从头部里写的入口地址开始执行，就可以把程序跑起来。这时候再去看汇编，可以发现链接后的代码从 0x4001000 开始，并且直接把 .rodata 的地址写到了指令的立即数之中：

```shell
# objdump -S: Display assembly and intermix source code with disassembly
$ objdump -S helloworld_asm.o
0000000000000000 <_start>:
   0:   48 c7 c7 01 00 00 00    mov    $0x1,%rdi
   7:   48 c7 c6 00 00 00 00    mov    $0x0,%rsi
   e:   48 c7 c2 0d 00 00 00    mov    $0xd,%rdx
  15:   48 c7 c0 01 00 00 00    mov    $0x1,%rax
  1c:   0f 05                   syscall
  1e:   48 31 ff                xor    %rdi,%rdi
  21:   48 c7 c0 3c 00 00 00    mov    $0x3c,%rax
  28:   0f 05                   syscall
$ objdump -S helloworld_asm
0000000000401000 <_start>:
  401000:       48 c7 c7 01 00 00 00    mov    $0x1,%rdi
  401007:       48 c7 c6 00 20 40 00    mov    $0x402000,%rsi
  40100e:       48 c7 c2 0d 00 00 00    mov    $0xd,%rdx
  401015:       48 c7 c0 01 00 00 00    mov    $0x1,%rax
  40101c:       0f 05                   syscall
  40101e:       48 31 ff                xor    %rdi,%rdi
  401021:       48 c7 c0 3c 00 00 00    mov    $0x3c,%rax
  401028:       0f 05                   syscall
```

从这里可以归纳出，写一个最简单的链接器，把上述的 .o 链接成可执行文件，大致需要做哪些事情：

1. 解析 ELF 文件，解析里面的内容
2. 考虑将要输出的 ELF 文件的布局，计算出各个 section 需要保存的内容以及地址，需要考虑 segment 的布局以及对齐
3. 根据地址，完成 relocation 所需要的计算并填入对应的位置

## 实现

接下来描述一下实现的具体思路：

1. 第一步就是解析输入的 ELF 文件，提取出中间的内容，包括有哪些 section，解析 relocation 的内容等等；这个可以用现成的库来辅助，也可以自己写。
2. 把 section 的内容收集下来，例如 .text .rodata 等等，这些数据之后会写入到可执行 ELF 文件中。
3. 收集完以后，就知道输出的 ELF 大概需要哪些内容了。在进行 relocation 之前，因为目前实现的是采用绝对地址的可执行文件，所以需要先确定好各个 section 和 symbol 的地址，从而实现 relocation 的计算。观察 ld.bfd 输出的文件，可以看到 ELF 文件包括如下几个部分：
     1. ELF file header：ELF 头部，填写各种信息，以及到后续各个 header 的地址偏移
     2. ELF program header：让 ELF Loader 知道有哪些 Segment 要加载
     3. section data：各个 section 的内容，由于 section 需要保证对齐，因此中间需要填一些额外的零字节
     4. ELF section header：保存 section header，记录了 section 的信息
4. 而加载到内存里的时候，就是直接大段地连续地加载到内存中，所以可以提前计算好各个部分的地址。例如要把 ELF 加载到 0x400000，那就把 file header 和 program header 放在开头，然后因为 segment 需要对齐到页的边界 [^1] ，例如对齐到 0x1000（4 KB），那就把连续的相同访问权限的 section 放到一个 segment 内，然后第一个 segment 放到 0x401000，往后再对齐再放下一个 segment，依此类推，直到把所有 segment 都放下为止。
5. 计算好各个部分的地址以后，就可以知道各个 section 和 symbol 在最终的内存里会处于什么地址了。此时就按照 relocation 的要求进行计算（例如前面出现过的 `R_X86_64_32S` 就是后写入 64 位的地址的低 32 位，并且检查它符号扩展后等于原来 64 位的地址，如果检查失败，就会得到大家熟悉的 `relocation truncated to fit` 错误），直接把计算结果填入到数据中。由于目前只考虑最简单的情况，不涉及到动态重定向，所以可执行文件里所有重定向都会被链接器完成。
6. 针对可执行文件，还需要生成 segment 放到 program header 里。简单粗暴的办法，就是整个文件直接映射到内存的 0x400000，设置权限为 read + write + execute。更精细的做法，则是把不同类型的数据按照合适的权限映射，例如 .rodata 放到 read only 的 segment 里，.text 放到 read + execute 的 segment 里。
6. 再按照前面所述的流程，按照预计好的布局，把 ELF 的内容写到文件里。

[^1]: 这是为了在加载 ELF 时可以直接 mmap，而不需要立即把文件内容读取到内存里；更进一步，mmap 是允许多个虚拟页映射到同一个物理页上的，所以允许一些出现一些“不对齐”的情况，得以节省因为对齐而浪费的空间。对于这个话题的进一步了解，建议阅读 [Exploring the section layout in linker output](https://maskray.me/blog/2023-12-17-exploring-the-section-layout-in-linker-output)。

这里还有一些细节没有交代，例如 section string table (.shstrtab) 的维护等等。如果只是为了跑起来，符号表都可以直接删掉不要。

实现的过程中，灵活运用 readelf 和 objdump 等工具，确认自己输出的 ELF 文件内容是正确的。如果实现成功，就可以执行生成的可执行文件，成功打印 `Hello world！`。

这个过程我用 Rust 完成了实现，使用了现成的 ELF 读写库 `object`，链接器部分的代码量大概是 200 行。

## 参考

最后给出一些文档，可供实现时参考：

- [Tool Interface Standard (TIS) Executable and Linking Format (ELF) Specification](https://refspecs.linuxfoundation.org/elf/elf.pdf)
- [System V Application Binary Interface AMD64 Architecture Processor Supplement Draft Version 0.99.6](https://refspecs.linuxbase.org/elf/x86_64-abi-0.99.pdf)
