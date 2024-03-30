---
layout: post
date: 2024-03-30
tags: [linux,linker,elf]
categories:
    - software
---

# 开发一个链接器（2）

## 前言

这个系列的第一篇博客实现了一个最简单的静态链接器，它可以输入单个 ELF .o 文件，输出 ELF 可执行文件。接下来，我们需要把它升级到支持输入两个或者更多的 ELF .o 文件。

<!-- more -->

## 回顾

首先回顾一下：在这个系列的上一篇博客中，我们观察了现有链接器的工作过程，并且实现了一个最简单的链接器：输入一个 ELF object，链接成一个可以运行的 ELF 可执行文件。这个过程包括：

1. 解析输入的 ELF，收集各个 section 需要保留下来的内容
2. 规划将要生成的 ELF 可执行文件的内容布局：开始是固定的文件头，之后是各个 section，计算出它们从哪里开始到哪里结束
3. 第二步完成以后，就可以知道在运行时，各个 section 将会被加载到哪个地址上；此时我们就可以计算重定向，把地址按照预设的规则填入到对应的地方
4. 最后按照预设的文件布局，把文件内容写入到 ELF 文件中

接下来我们就要实现单文件输入到多文件输入的跨越，让我们首先分析一下，这里的不同在哪里。

## 分析

输入只有一个 ELF object（.o）文件的时候，这个 object 文件里需要的所有东西都只能由这个 object 自己来提供，所以比较好实现。但如果要输入多个 ELF object 文件，此时可能会出现需要依赖的情况。首先回忆一下之前学习的 C/C++ 的内容，在编写代码的时候，经常会把声明（declaration）放到头文件（.h）里，实现（definition）放在源文件（.c/cpp）：这样可以在 `A.cpp` 中调用 `B.cpp` 里的函数，不会出现大家经常遇到的 `duplicate symbol` 错误。那么这是怎么实现的呢？

我们首先在汇编语言中模拟这个场景。首先回顾一下上一篇博客中用汇编实现的 Hello World 例子：

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
# for insipration look at http://www.muppetlabs.com/~breadbox/software/tiny/teensy.html

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

可以看到代码实际上做了两件事情，首先输出 Hello World，然后退出程序。我们把这两部分分别实现成一个函数，放到另一个 `.s` 文件（`printer.s`）中：

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

可以看到，这里把上面的两段汇编分别放在 `print` 和 `exit` 函数中，并且加上了 `ret` 指令以实现返回函数的调用者。`exit` 函数没有添加 `ret` ，是因为调用 `exit` 系统调用后，进程就退出了，后面的指令不会被执行。接下来，需要在入口函数中调用这两个函数来实现 `Hello world` 的打印：

```asm
# main.s
    .section .text
    .globl _start
_start:
    call print
    call exit
```

调用 GNU as 分别汇编两个文件然后链接，程序可以正常运行：

```shell
$ as main.s -o main.o
$ as printer.s -o printer.o
$ ld main.o printer.o -o helloworld
$ ./helloworld
Hello world!
```

这时候我们就要探究，汇编器和链接器是如何协作，使得 `main.s` 中的代码可以调用 `printer.s` 中的函数。当然了，在这里我们用的是汇编语言，汇编器遇到不存在的函数名就会认为是外部函数。如果是 C/C++ 语言，则要先在 `main.c` 中声明这两个函数（或者 `#include` 了一个声明了这两个函数的头文件）再调用（比较老的 C 标准允许不声明直接调用，但这是不推荐的）。

首先观察 `main.s` 经过汇编得到的 `main.o`，看它是怎么调用 `print` 和 `exit` 函数的：

```asm
$ objdump -S main.o

main.o:     file format elf64-x86-64


Disassembly of section .text:

0000000000000000 <_start>:
   0:   e8 00 00 00 00          call   5 <_start+0x5>
   5:   e8 00 00 00 00          call   a <_start+0xa>
```

反汇编出来可以看到两条 `call` 指令，但是它们的地址都很奇怪：第一条指令是 `call 5`，而 0x5 是第二条 call 地址的地址；第二条指令是 `call a`，按照规律，可以猜出来 0xa 是第二条指令之后的第一个字节的地址，每条指令 5 个字节，两条指令刚好 10 字节，也就是 0xa。这似乎与 `print` 和 `exit` 函数都没有关系，执行的时候怎么会得到正确的结果呢？

回忆一下，在这个系列的上一篇博客中，反汇编 `.o` 文件的时候也出现过类似的情况：`_start` 函数需要知道 `.rodata` 段里的 `hello` 字符串的地址，但是汇编的时候这个地址无法知道，所以汇编器生成了一个 relocation（relocation 的中文翻译是重定向，但我不喜欢这个翻译，所以下文还是用 relocation），告诉链接器去填入正确的地址。这里也是类似的：汇编器在汇编 `main.s` 的时候，也无法知道 `print` 和 `exit` 函数会在什么地址，所以只能生成一个 relocation，把偏移初始化为零，等着链接器来填写。而 x86 上 `call` 指令的目的地址计算方法是 `call` 指令之后的第一个字节地址加上偏移，这个偏移初始化为 0，那么反汇编看到的就好像是 `call` 要调用它自己的下一条指令，这就解释了上面观察到的现象。

正好 `objdump` 可以帮我们显示出 relocation，只需要添加 `-r` 参数：

```shell
$ objdump -S -r main.o

main.o:     file format elf64-x86-64


Disassembly of section .text:

0000000000000000 <_start>:
   0:   e8 00 00 00 00          call   5 <_start+0x5>
                        1: R_X86_64_PLT32       print-0x4
   5:   e8 00 00 00 00          call   a <_start+0xa>
                        6: R_X86_64_PLT32       exit-0x4
```

这时候会发现，`print` 和 `exit` 果然出现了，所以汇编器是通过这两条 relocation 告诉链接器，这里实际上要调用哪个函数。但是这里出现的 `R_X86_64_PLT32` 是什么意思？`print` 和 `exit` 后面的 `-0x4` 是什么意思，为什么要减 4？如果考虑到前面所说的，`call` 指令占用 5 个字节，那不应该是减 5 才对吗？下面来解释这些问题：

!!! question "什么是 `R_X86_64_PLT32` ？"

    在上一篇博客中，出现过 `R_X86_64_32S` 这种 relocation 类型，它的意思是把目标符号的地址以 32 位有符号数的格式写到对应的位置，换句话说，用的是绝对地址，例如 `0x402000`。但是，刚才提到，x86 的 `call` 指令的目的地址计算方法是，`call` 指令后的第一个字节的地址，加上地址偏移。也就是说，这个地址偏移是相对的，再填入绝对地址就出错了。实际上，`R_X86_64_PLT32` 还涉及到一个新的还没有涉及到的概念 PLT（Procedure Linkage Table），在这里我们先不涉及 PLT，把它当成单纯的相对地址计算去处理。这个单纯的相对地址计算的 relocation 也有正式名字，也就是 `R_X86_64_PC32`，意思是根据 PC（Program Counter）计算出和目的地址的相对偏移（32 位）。
    
!!! question "为什么是 `print-0x4`？这个减去 0x4 是怎么来的？"
    
    刚才提到，x86 的 `call` 指令是用 `call` 指令后的第一个字节的地址加上地址偏移，求的和就是要调用的函数的地址。这个过程比较复杂，我们下面举一个具体的例子：

    以上面的 `call exit` 指令为例，也就是反汇编出来的第二条指令：

    ```asm
       5:   e8 00 00 00 00          call   a <_start+0xa>
                            6: R_X86_64_PLT32       exit-0x4
    ```

    假设我们已经知道 `print` 函数的地址就是 `0xbbbb`，也假设这条 `call` 指令最终在内存中的地址也是 `0x5`。那么我们应该怎么填写这条 `call` 指令的地址偏移呢？

    假设地址偏移等于 `X`，已知 `call` 指令的地址是 0x5，`call` 指令占用 0x5 个字节，那么 `call` 指令后的第一个字节的地址就是 `0x5 + 0x5`，按照 x86 的规定，要调用的函数的地址就是 `0x5 + 0x5 + X`。而我们知道要调用的函数是 `print`，`print` 函数的地址是 `0xbbbb`，反解出 `X = 0xbbb1`，那么要填进去的地址偏移就是 0xbbb1 这个数。

    如果按照这个逻辑，要计算 X 的话，应该是 `print - 0x5 - 0x5` 才对，第一个 `0x5` 是 `call` 指令的起始地址，第二个 `0x5` 是 `call` 指令的长度。但是为什么看到的是 `print - 0x4` 呢？为什么只减了一个数（`-0x4`），而不是两个（`- 0x5 - 0x5`）？

    细心的读者可能观察到，在 `R_X86_64_PLT32` 的前面，显示的是 `6:`，这表示的是 relocation 标记的地址是 0x6，而不是 0x5（`call` 指令的起始地址）。进一步观察，会发现 `call` 指令的第一个字节 `0xe8` 决定了这是一条 `call` 指令，剩下的四个字节都是地址偏移，而链接器要改的也就是这个地址偏移：既然要改的是从 0x6 开始的四个字节，那 relocation 自然指向的就是 0x6！换句话说，链接器不需要知道这是一条 `call` 指令，只需要按照 relocation 的规则计算出值填进去就好了。

    既然起始地址要从 0x6 开始算了，那么为什么出现 `0x4` 就可以解释了：从 relocation 的 0x6 地址开始算，只需要减去 4（`call` 指令内地址偏移的长度），而不是减去 5（`call` 指令的长度）。另一方面，`R_X86_64_PLT32` 本身就告诉链接器，让链接器计算的时候，要减去当前 relocation 的起始地址了。按照这个规则，我们再复现一遍刚才的例子：

    链接器观察到一个 `R_X86_64_PLT32` 的 relocation，relocation 自身的地址是 0x6，目标地址是 `print-0x4`，`print` 函数的地址是 `0xbbbb`，那么要填入的地址偏移就等于 `0xbbbb - 0x4 - 0x6 = 0xbbb1`。这个计算过程用 ABI 文档中的表示方法，就是 `S + A - P`，S（Symbol）表示符号的地址（`print` 的地址，`S=0xbbbb`），A（Addend）表示额外加或者减去的数（这里是减去 0x4，也就是 `A=-0x4`），P 表示 relocation 自己的地址（`P=0x6`）。
    
    计算结果和之前我们手动推导的是一致的，看起来这两个计算方法似乎没什么区别，反正结果都一样？区别在于，这种设计下，链接器不需要知道指令是什么，不管是不是 `call` 指令，只管计算和填数。那么在不同的场景下，或许可以复用相同的 relocation 类型。

relocation 的情况分析完了，我们学习到汇编器在遇到外部函数时，如何生成看起来错误的 `call` 指令，又是如何输出 relocation 让链接器填入正确的偏移，使得 `call` 指令可以调用正确的函数。

此时再看 `printer.o` 的反汇编结果：

```asm
$ objdump -S -r printer.o

printer.o:     file format elf64-x86-64


Disassembly of section .text:

0000000000000000 <print>:
   0:   48 c7 c7 01 00 00 00    mov    $0x1,%rdi
   7:   48 c7 c6 00 00 00 00    mov    $0x0,%rsi
                        a: R_X86_64_32S .rodata
   e:   48 c7 c2 0d 00 00 00    mov    $0xd,%rdx
  15:   48 c7 c0 01 00 00 00    mov    $0x1,%rax
  1c:   0f 05                   syscall
  1e:   c3                      ret

000000000000001f <exit>:
  1f:   48 31 ff                xor    %rdi,%rdi
  22:   48 c7 c0 3c 00 00 00    mov    $0x3c,%rax
  29:   0f 05                   syscall
```

不出意外，两个函数都出现了，同时也出现了上一篇博客中提到的 `R_X86_64_32S` 的 relocation 类型。仔细观察，会发现这个 relocation 的地址是 `0xa`，而不是 `mov` 指令的地址 `0x7`，聪明的你应该已经观察出来：`mov` 指令前三个字节表示了这是一条 `mov` 指令，目的寄存器是 `%rsi`，后四个字节就是要 `mov` 的立即数，所以 relocation 直接指向了后四个字节的地址。链接器不需要反汇编，不需要知道这是一条 `mov` 指令，只管找 relocation 往里填。

关于两个 `.o` 文件分析得差不多了，接下来看最后得到的可执行文件：

```asm

helloworld:     file format elf64-x86-64


Disassembly of section .text:

0000000000401000 <_start>:
  401000:       e8 05 00 00 00          call   40100a <print>
  401005:       e8 1f 00 00 00          call   401029 <exit>

000000000040100a <print>:
  40100a:       48 c7 c7 01 00 00 00    mov    $0x1,%rdi
  401011:       48 c7 c6 00 20 40 00    mov    $0x402000,%rsi
  401018:       48 c7 c2 0d 00 00 00    mov    $0xd,%rdx
  40101f:       48 c7 c0 01 00 00 00    mov    $0x1,%rax
  401026:       0f 05                   syscall
  401028:       c3                      ret

0000000000401029 <exit>:
  401029:       48 31 ff                xor    %rdi,%rdi
  40102c:       48 c7 c0 3c 00 00 00    mov    $0x3c,%rax
  401033:       0f 05                   syscall
```

可以得到几点观察：

1. `_start` 函数里函数调用的指令 `call print` 和 `call exit` 已经被链接器修复，`print` 函数内引用 `hello` 字符串地址也正确被填写
2. 来自两个 `.o` 文件的代码段 `.text` 的内容被拼接起来，得到了输出的 ELF 里的 `.text` 段内容；类似地，`printer.o` 里面的只读数据段 `.rodata` 的内容也复制到了输出的 ELF 中，地址是 `0x402000`
3. 虽然 `objdump` 参数里写了 `-r`，要求 `objdump` 显示代码中的 relocation，但是链接器已经完成了所有 relocation 的计算并更新了对应的数，因此输出的 ELF 里就没有 relocation 了。在未来的博客中，我们会看到，可执行文件里也可以有 relocation

按照这些观察，我们可以得出，为了支持第二版的链接器，也就是支持两个或者更多个 .o 文件的链接的静态链接器，需要做的额外工作：

!!! note "合并来自多个文件的同一个 section"

    上面已经观察到，来自不同 .o 的 `.text` 段被合并起来，写入到了最终输出的 ELF 的 `.text` 段。同理，其他需要输出到可执行文件里的段，也需要合并

!!! note "完善指向 section 的 relocation 的处理"

    上一篇文章里，只涉及到一个输入的 ELF object 文件，并且也只涉及到对 section 的 relocation，所以每个 section 只有一份，只需要保存每个 section 在内存中的起始地址。但此时，每个 ELF object 文件都可能有自己的 `.text` `.rodata` section，此时再出现对 section 的 relocation 时，是对输入的 ELF object 自己的 `.rodata`，而不是对输出 ELF executable 的 `.rodata`。
    
    在上面的例子里，如果 `main.s` 和 `printer.s` 都往 `.rodata` 段写了数据，假如 `main.s` 产生了 0x10 字节的数据，`printer.s` 产生了 0x20 字节的数据，假设输出的 `.rodata` 段从 `0x402000` 地址开始，先存 `main.o` 的 `.rodata` 的内容，再存 `printer.o` 的 `.rodata` 的内容，那么 `printer.o` 的 `.rodata` 的数据在内存中的起始地址就是 `0x402000 + 0x10 = 0x402010`。
    
    同时，在 `printer.o` 中，`print` 函数产生了对 `.rodata` 的 relocation，实际上是要得到 `printer.o` 的 `.rodata` 段中的 `Hello world` 字符串的起始地址。根据上面的分析，计算 relocation 的时候，应该用 `0x402010`（`printer.o` 的 `.rodata` 在内存中的起始地址），而不是 `0x402000`（输出的 `.rodata` 的起始地址） 作为 `Hello world` 字符串的地址。

    简而言之，现在需要记录来自不同 .o 文件的 section 的相对位置。实际上，这在实现上也并不复杂，只是不要忘记这件事情。

!!! note "解析和维护符号表，找到符号对应的地址"

    在这个例子中，需要维护一个符号表，记录各个符号在内存中的地址，那么后续计算 relocation 的时候，这个地址会参与到计算当中。

    在上面的例子里，`main.s` 和 `printer.s` 都往 `.text` 段写了指令。`main.s` 产生了 0xa 字节的指令，`printer.s` 产生了 0x2b 字节的指令。输出时，假如 `.text` 段从 `0x401000` 开始，按照下面的逻辑计算各个符号的地址：
    
    1. 先复制 `main.o` 的 `.text` 代码段的内容到输出的 `.text` 段，此时这部分指令的的起始内存地址就是 `0x401000`
    2. 由于 `_start` 函数在 `main.o` 的 `.text` 段内的偏移是 `0x0`，所以它在内存中的地址就是 `0x401000 + 0x0 = 0x401000`
    3. 接着复制 `printer.o` 的 `.text` 代码段的内容到输出的 `.text` 段，由于前面已经有 0xa 个字节的数据了，所以这部分指令的起始内存地址就是 `0x40100a`
    4. `print` 函数在 `printer.o` 的 `.text` 段内的偏移是 `0x0`，所以它在内存中的地址就是 `0x40100a + 0x0 = 0x40100a`
    5. `exit` 函数在 `printer.o` 的 `.text` 段内的偏移是 `0x1f`，所以它在内存中的地址就是 `0x40100a + 0x1f = 0x401029`

    所以在复制段内容的同时，各个符号的地址也就可以计算出来了。有了符号表以后，之后计算针对 `print` 和 `exit` 的 relocation 的时候，查符号表就可以知道地址了。

## 实现

结合以上的分析，我们可以在上一次博客的基础上实现第二版的链接器，这个链接器可以支持输入多个 ELF .o 文件。这个过程我用 Rust 完成了实现，链接器部分的代码量大概是 400 行，比上一个版本多 200 行。


