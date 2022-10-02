---
layout: post
date: 2021-02-09 19:02:00 +0800
tags: [c++,fortran,gcc,clang,ld,linking,symbols,objdump]
category: software
title: COMMON 符号
---

## 背景

在编译一个程序的时候，遇到了 undefined symbol 的问题。具体情况是这样的：

1. 一开始的时候，直接把所有的源代码编译成 `.o`，再一次性链接，这样不会报错
2. 后来，把一些代码编译成静态库，即把其中一部分源代码编译成 `.o` 后，用 `ar` 合并到一个 `.a` 中，再和其余的 `.o` 链接在一起，这时候就报错了：

```text
Undefined symbols for architecture arm64:
  "_abcd", referenced from:
    ...
```

如果换台机器，编译（使用的是 gcc 10.2.0）就没有问题。

而如果去找这个符号存在的 `.o` 里，是可以找到的：

```shell
$ objdump -t /path/to/abcd.o
0000000000000028         *COM*  00000008 _abcd
```

在合成的静态库 `.a` 里，也是存在的（一个定义 + 若干个引用）：

```shell
$ objdump -t /path/to/libabc.a | grep abcd
0000000000000028         *COM*  00000008 _abcd
0000000000000000         *UND* _abcd
0000000000000000         *UND* _abcd
0000000000000000         *UND* _abcd
0000000000000000         *UND* _abcd
0000000000000000         *UND* _abcd
```

于是觉得很奇怪，就上网搜了一下，找到了一篇 [StackOverflow](https://stackoverflow.com/questions/63665653/different-behavior-between-clang-and-gcc-10-when-linking-to-static-library-conta) 讲了这个问题。解决方案很简单，就是：

**编译的时候打开 `-fno-common` 设置**

而 gcc 10 不会出错的原因是，它默认从 `-fcommon` 改成了 `-fno-common` 。

## COMMON 是什么

这时候，肯定不满足于找到一个解决方案，肯定还是会去找背后的原理。

首先，搜索了一下 COMMON 是什么，找到了 [Investigating linking with COMMON symbols in ELF](https://binarydodo.wordpress.com/2016/05/09/investigating-linking-with-common-symbols-in-elf/) 这篇文章。

文章里讲了 COMMON 是做什么的：

> Common symbols are a feature that allow a programmer to ‘define’ several variables of the same name in different source files.  This is in contrast with the more popular way of doing, where you define a variable once in a source file, and reference it everywhere else in other source files, using extern.  When common symbols are used, the linker will merge all symbols of the same name into a single memory location, the size of which is the largest type of the individual common symbol definitions.  For example, if fileA.c defines an uninitialized 32-bit integer myint, and fileB.c defines an 8-bit char myint, then in the final executable, references to myint from both files will point to the same memory location (common location), and the linker will reserve 32 bits for that location.

文章里还讲了具体的实现方法：一个没有初始化的全局变量，在 `-fcommon` 的情况下，会设为 COMMON；如果有初始化，就按照初始化的值预分配到 .bss 或者 .data。链接的时候，如果有多个同名的 symbol，会有一个规则决定最后的 symbol 放到哪里；如果有冲突的话，就是我们熟悉的 `multiple definition` 错误了。

为啥会有这种需求，多个 variable 同名，不会冲突而且共享内存？又在别的地方看到说法，COMMON 是给 `ancient` 代码使用的，还有的提到了 FORTRAN。于是去搜了一下，果然，FORTRAN 是问题的关键

## FORTRAN 里面的 COMMON

用关键词很容易可以搜索到讲 [COMMON BLOCK in FORTRAN 的文章](https://www.obliquity.com/computer/fortran/common.html)，FORTRAN 里面的 COMMON 是一种通过全局存储隐式传递参数的方法。拿文章里的例子：

```fortran
      PROGRAM MAIN
      INTEGER A
      REAL    F,R,X,Y
      COMMON  R,A,F
      A = -14
      R = 99.9
      F = 0.2
      CALL SUB(X,Y)
      END

      SUBROUTINE SUB(P,Q)
      INTEGER I
      REAL    A,B,P,Q
      COMMON  A,I,B
      END
```

在函数 MAIN 和 SUB 中，都有 COMMON 语句，而 COMMON 后面的变量，就是存储在一个 COMMON 的 symbol 之中，按照顺序映射到 symbol 的内存地址。尝试编译一下上面的代码，然后看一下 symbol：

```shell
$ gfortran -g -c test.f -o test.o
$ objdump -t test.o

test.o:	file format Mach-O arm64

SYMBOL TABLE:
0000000000000078 g     F __TEXT,__text _main
0000000000000000 g     F __TEXT,__text _sub_
000000000000000c         *COM*	00000010 ___BLNK__
```

可以看到，出现了一个叫做 `___BLNK__` 的 COMMON symbol，大小是 16 字节。看一下代码中是如何引用的：

```shell
$ objdump -S --reloc test.o

test.o:	file format Mach-O arm64

Disassembly of section __TEXT,__text:

0000000000000018 _MAIN__:
;         PROGRAM MAIN
      18: fd 7b be a9                  	stp	x29, x30, [sp, #-32]!
      1c: fd 03 00 91                  	mov	x29, sp
;         A = -14
      20: 00 00 00 90                  	adrp	x0, #0
		0000000000000020:  ARM64_RELOC_GOT_LOAD_PAGE21	___BLNK__
      24: 00 00 40 f9                  	ldr	x0, [x0]
		0000000000000024:  ARM64_RELOC_GOT_LOAD_PAGEOFF12	___BLNK__
      28: a1 01 80 12                  	mov	w1, #-14
      2c: 01 04 00 b9                  	str	w1, [x0, #4]
;         R = 99.9
      30: 00 00 00 90                  	adrp	x0, #0
		0000000000000030:  ARM64_RELOC_GOT_LOAD_PAGE21	___BLNK__
      34: 00 00 40 f9                  	ldr	x0, [x0]
		0000000000000034:  ARM64_RELOC_GOT_LOAD_PAGEOFF12	___BLNK__
      38: a1 99 99 52                  	mov	w1, #52429
      3c: e1 58 a8 72                  	movk	w1, #17095, lsl #16
      40: 20 00 27 1e                  	fmov	s0, w1
      44: 00 00 00 bd                  	str	s0, [x0]
;         F = 0.2
      48: 00 00 00 90                  	adrp	x0, #0
		0000000000000048:  ARM64_RELOC_GOT_LOAD_PAGE21	___BLNK__
      4c: 00 00 40 f9                  	ldr	x0, [x0]
		000000000000004c:  ARM64_RELOC_GOT_LOAD_PAGEOFF12	___BLNK__
      50: a1 99 99 52                  	mov	w1, #52429
      54: 81 c9 a7 72                  	movk	w1, #15948, lsl #16
      58: 20 00 27 1e                  	fmov	s0, w1
      5c: 00 08 00 bd                  	str	s0, [x0, #8]
;         CALL SUB(X,Y)
      60: e1 63 00 91                  	add	x1, sp, #24
      64: e0 73 00 91                  	add	x0, sp, #28
      68: 00 00 00 94                  	bl	#0 <_MAIN__+0x50>
		0000000000000068:  ARM64_RELOC_BRANCH26	_sub_
;         END
      6c: 1f 20 03 d5                  	nop
      70: fd 7b c2 a8                  	ldp	x29, x30, [sp], #32
      74: c0 03 5f d6                  	ret

```

可以看到，在 MAIN 中引用 `A` 的时候，取的地址是 `___BLNK__+4`，`R` 是 `___BLNK__+0`，`F` 是 `___BLNK__+8`。这和代码里的顺序也是一致的。所以在 SUB 中读 A I B 的时候，对应了 MAIN 中的 A R F。通过这种方式，可以在 MAIN 函数里面隐式地给所有函数传递参数。

此外，COMMON 还可以命名，这样就可以区分不同的参数用途：

```fortran
        PROGRAM MAIN
        INTEGER A
        REAL    F,R,X,Y
        COMMON  R,A,F
        COMMON /test/ X,Y
        A = -14
        R = 99.9
        F = 0.2
        CALL SUB(X,Y)
        END

        SUBROUTINE SUB(P,Q)
        INTEGER I
        REAL    A,B,P,Q
        COMMON  A,I,B
        END
```

代码添加了一行 `COMMON /test/`，观察一下 symbol：

```shell
$ objdump -t test.o

test.o:	file format Mach-O arm64

SYMBOL TABLE:
0000000000000088 g     F __TEXT,__text _main
0000000000000000 g     F __TEXT,__text _sub_
000000000000000c         *COM*	00000010 ___BLNK__
0000000000000008         *COM*	00000010 _test_
```

和预期的一致：出现了新的 COMMON symbol，对应了 named COMMON Block 里面的变量 X 和 Y。

再看一下汇编里怎么引用的：

```shell
;         CALL SUB(X,Y)
      60: 00 00 00 90                   adrp    x0, #0
                0000000000000060:  ARM64_RELOC_GOT_LOAD_PAGE21  _test_
      64: 00 00 40 f9                   ldr     x0, [x0]
                0000000000000064:  ARM64_RELOC_GOT_LOAD_PAGEOFF12       _test_
      68: 01 10 00 91                   add     x1, x0, #4
      6c: 00 00 00 90                   adrp    x0, #0
                000000000000006c:  ARM64_RELOC_GOT_LOAD_PAGE21  _test_
      70: 00 00 40 f9                   ldr     x0, [x0]
                0000000000000070:  ARM64_RELOC_GOT_LOAD_PAGEOFF12       _test_
      74: 00 00 00 94                   bl      #0 <_MAIN__+0x5c>
                0000000000000074:  ARM64_RELOC_BRANCH26 _sub_
```

可以看到，第一个参数（x0）为 `_test_`，第二个参数（x1）为 `_test_+4`，和预期也是一样的。

读到这里，就可以理解为啥有 COMMON symbol 了。可能是为了让 C 代码和 FORTRAN 代码可以互操作 COMMON symbol，就有了这么一出。也可能有的 C 库确实用了类似的方法来实现某些功能。

## 解决方案

但是，这种用法在现在来看是不推荐的，建议还是该 extern 就 extern，另外，在编译静态库的时候，记得加上 `-fno-common`。
