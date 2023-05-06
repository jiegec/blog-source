---
layout: post
date: 2023-05-06 12:09:00 +0800
tags: [linker,ld]
category: software
title: 链接器的工作原理
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
