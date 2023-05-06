---
layout: post
date: 2023-05-06 12:09:00 +0800
tags: [linker,ld]
category: software
title: 链接器的工作原理
draft: true
---

## 背景

最近和同学讨论一些比较复杂的链接问题，遇到一些比较复杂的情况，因此复习一遍链接器的工作原理。

## 编译

编译器会把源文件编译成 obj，obj 里面有符号表，定义了不同的符号类型。常见的代码与符号的对应关系：

```c
// global in .bss section if -fno-common
// common symbol if -fcommon
int uninitialized;
// global in .bss section
int initialized = 0;
// global in .data section
int initialized_one = 1;
// global in .rodata section
const int const_initialized = 0;
// global in .rodata section
const int const_initialized_one = 1;
// global undefined symbol
extern int external;
// local in .bss section
static int static_uninitialized;
// local in .bss section
static int static_initialized = 0;
// local in .data section
static int static_initialized_one = 1;
// local in .rodata section
const static int const_static_initialized = 0;
// local in .rodata section
const static int const_static_initialized_one = 1;
// global in .text section
int simple_function() {
  // local in .bss section
  static int static_in_function = 0;
}
// global in .text section
void access_external() { external = 1; }
// global undefined symbol
extern double external_function();
// global in .text section
long call_external() { external_function(); }
// local in .text section
static int static_function() {}
// weak in .text section
__attribute__ ((weak)) float weak_function() {}
// global in .text section marked .hidden
__attribute__ ((visibility ("hidden"))) int hidden_function() {}
```

使用 `readelf -s` 查看符号表：

```
   Num:    Value          Size Type    Bind   Vis      Ndx Name
     6: 0000000000000008     4 OBJECT  LOCAL  DEFAULT    4 static_uninitialized
     7: 000000000000000c     4 OBJECT  LOCAL  DEFAULT    4 static_initialized
     8: 0000000000000004     4 OBJECT  LOCAL  DEFAULT    3 static_initializ[...]
     9: 0000000000000008     4 OBJECT  LOCAL  DEFAULT    5 const_static_ini[...]
    10: 000000000000000c     4 OBJECT  LOCAL  DEFAULT    5 const_static_ini[...]
    11: 0000000000000029     7 FUNC    LOCAL  DEFAULT    1 static_function
    12: 0000000000000010     4 OBJECT  LOCAL  DEFAULT    4 static_in_function.0
    16: 0000000000000000     4 OBJECT  GLOBAL DEFAULT    4 uninitialized
    17: 0000000000000004     4 OBJECT  GLOBAL DEFAULT    4 initialized
    18: 0000000000000000     4 OBJECT  GLOBAL DEFAULT    3 initialized_one
    19: 0000000000000000     4 OBJECT  GLOBAL DEFAULT    5 const_initialized
    20: 0000000000000004     4 OBJECT  GLOBAL DEFAULT    5 const_initialized_one
    21: 0000000000000000     7 FUNC    GLOBAL DEFAULT    1 simple_function
    22: 0000000000000007    17 FUNC    GLOBAL DEFAULT    1 access_external
    23: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT  UND external
    24: 0000000000000018    17 FUNC    GLOBAL DEFAULT    1 call_external
    25: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT  UND _GLOBAL_OFFSET_TABLE_
    26: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT  UND external_function
    27: 0000000000000030    11 FUNC    WEAK   DEFAULT    1 weak_function
    28: 000000000000003b     7 FUNC    GLOBAL HIDDEN     1 hidden_function
```

总结一下，每个符号有如下属性：

1. Bind：Local（static）、Global（extern 或者非 static）、Weak（标记 `__attribute__ ((weak))`）
2. Vis(Visibility): Default、Hidden（标记 `__attribute__ ((visibility ("hidden")))`）
3. Ndx：
    1. COMMON：如果打开了 -fcommon，那么没有初始化的全局变量（上面的 `uninitialized`）会生成 COMMON 符号；如果打开了 -fno-common，则不会有 COMMON 符号
    2. UNDEFINED：extern 符号
4. Section:
    1. const 变量放在 .rodata section
    2. 非 const 变量，如果没有初始化，如果开了 -fcommon，则生成 COMMON 符号；如果开了 -fno-common，则放在 .bss section
    3. 非 const 变量，如果初始化了，放在 .data section
    4. 函数放在 .text section

关于 COMMON 符号的详细内容，建议阅读 [All about COMMON symbols - MaskRay](https://maskray.me/blog/2022-02-06-all-about-common-symbols) 和 [COMMON 符号](/software/2022/07/11/archive-common-linking/)。

## 链接

链接要做的是把多个 obj 合并成一个可执行文件或者动态库，主要目的是将一个 obj 中定义的符号与另一个 obj 中 undefined 的符号对应起来。

链接器运行时，传入若干个 obj 文件，然后按照下面的流程进行：

1. 维护一个全局的符号表
2. 循环每个 obj 文件，循环其中的符号，找到其中的 GLOBAL/WEAK 符号
3. 把 GLOBAL/WEAK 符号插入到符号表中，处理各种情况，例如：
    1. 如果出现两个 defined 符号冲突，报告 multiple definition 错误
    2. 如果出现重名的 weak 符号和 strong 符号，选择保留 strong 的符号
4. 如果存在没有找到匹配的 defined 符号的 undefined 符号，报告 undefined reference 错误

符号表是在解析 obj 文件的同时动态更新的，因此，如果 A 使用了 B 的符号，那么应该把 A 放在前面，这样链接器解析 A 的时候会在符号表中创建 undefined 符号，然后 B 在后面，当链接器解析 B 的时候，就可以把 B 的 defined 符号与 A 的 undefined 符号进行匹配。

## 静态库

静态库将多个 .o 合并为一个 .a，并且创建了索引。具体来说，创建一个静态库的时候：

```shell
$ ar rcs libxxx.a obj1.o obj2.o obj3.o ...
```

生成的 .a 会包括所有的 .o，然后创建索引（`ar rcs` 中的 `s`，会运行 `ranlib` 命令），索引的内容是一个符号到 .o 文件的映射：

```shell
$ nm -s /lib/x86_64-linux-gnu/libc.a
Archive index:
__printf in printf.o
_IO_printf in printf.o
printf in printf.o
__scanf in scanf.o
scanf in scanf.o
```

因此，链接器在遇到参数是 .a 的静态库的时候，不会查看里面的每个 .o 文件，而是从 Archive index 入手，如果当前的符号表依赖了 Archive index 中的符号，那就加载相应的 .o 文件。

## 动态库
