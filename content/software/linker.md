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

生成动态库的方法是，编译的时候添加 `-fPIC` 选项，链接的时候添加 `-shared` 编译参数：

```shell
gcc -fPIC -c source1.c -o source1.o
gcc -shared source1.o -o libtest.so.0.0.0
# oneliner:
gcc -fPIC -shared source1.c -o libtest.so.0.0.0
```

此时代码中定义的函数会出现在 Dynamic Symbol Table 中，可以用 `objdump -T` 命令查看：

```shell
$ cat source1.c
int simple_function() {}
$ objdump -T libtest.so.0.0.0

libtest.so.0.0.0:     file format elf64-x86-64

DYNAMIC SYMBOL TABLE:
0000000000000000  w   D  *UND*  0000000000000000 __cxa_finalize
0000000000000000  w   D  *UND*  0000000000000000 _ITM_registerTMCloneTable
0000000000000000  w   D  *UND*  0000000000000000 _ITM_deregisterTMCloneTable
0000000000000000  w   D  *UND*  0000000000000000 __gmon_start__
00000000000010f9 g    DF .text  0000000000000007 simple_function
```

如果代码中用了 libc 的一些函数，那么这些函数则会以 undefined symbol 的形式出现在 Dynamic Symbol Table 中：

```shell
$ cat source1.c
#include <stdio.h>
int simple_function() {
  printf("Simple function");
  return 0;
}
$ objdump -T libtest.so.0.0.0

libtest.so.0.0.0:     file format elf64-x86-64

DYNAMIC SYMBOL TABLE:
0000000000000000  w   D  *UND*  0000000000000000  Base        _ITM_deregisterTMCloneTable
0000000000000000      DF *UND*  0000000000000000 (GLIBC_2.2.5) printf
0000000000000000  w   D  *UND*  0000000000000000  Base        __gmon_start__
0000000000000000  w   D  *UND*  0000000000000000  Base        _ITM_registerTMCloneTable
0000000000000000  w   DF *UND*  0000000000000000 (GLIBC_2.2.5) __cxa_finalize
0000000000001109 g    DF .text  000000000000001b  Base        simple_function
```

### 符号版本

中间出现的 Base 或者 GLIBC_2.2.5 是符号的版本号，这样做的目的是为了兼容性：假如某天 glibc 想要给一个函数添加一个新的参数，但是现有的程序编译的时候动态链接了旧版本的 glibc，新旧两个版本的函数名字一样，但是功能却不一样，如果直接让旧程序用新 glibc 的函数，就会出现问题。即使参数不变，如果函数的语义变了，也可能带来不兼容的问题。

解决办法是给符号添加版本号，这样旧版本的程序会继续找到旧版本的符号，解决了兼容性的问题。例如 memcpy 在 glibc 中就有两个版本：

```shell
$ objdump -T /lib/x86_64-linux-gnu/libc.so.6 | grep memcpy
00000000000a2b70 g    DF .text  0000000000000028 (GLIBC_2.2.5) memcpy
000000000009bc50 g   iD  .text  0000000000000109  GLIBC_2.14  memcpy
```

在 [glibc 代码](https://github.com/bminor/glibc/blob/a363f7075125fa654342c69331e6c075518ec28c/sysdeps/x86_64/multiarch/memcpy.c#LL38C11-L38C11)中，通过 `versioned_symbol` 宏来实现：

```c
versioned_symbol (libc, __new_memcpy, memcpy, GLIBC_2_14);
```

更多关于符号版本的内容，可以阅读 [All about symbol versioning](https://maskray.me/blog/2020-11-26-all-about-symbol-versioning)。

### 动态链接

编译好动态链接库以后，可以在链接的时候，作为参数引入：

```shell
$ cat main.c
extern void simple_function();
int main() { simple_function(); }
$ gcc main.c libtest.so.0.0.0 -o main
$ LD_LIRBARY_PATH=$PWD ./main
Simple function
```

可以观察一下发生了什么事情：首先，链接的时候，会找到 `libtest.so.0.0.0` 导出的符号表，发现它定义了 `main.c` 缺少的 `simple_function` 函数，因此链接不会出错。但是，函数本身没有被链接到 `main` 里面，需要在运行时去加载动态库，这样 `main` 才可以调用函数：

```shell
$ objdump -t main
0000000000000000       F *UND*  0000000000000000              simple_function
$ objdump -T main
0000000000000000      DF *UND*  0000000000000000  Base        simple_function
$ readelf -d ./main
Dynamic section at offset 0x2dd0 contains 27 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libtest.so.0.0.0]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
$ ./main
./main: error while loading shared libraries: libtest.so.0.0.0: cannot open shared object file: No such file or directory
$ ldd ./main
        linux-vdso.so.1 (0x00007ffe07dbc000)
        libtest.so.0.0.0 => not found
        libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f83ee3fb000)
        /lib64/ld-linux-x86-64.so.2 (0x00007f83ee602000)
$ LD_LIBRARY_PATH=$PWD ldd ./main
        linux-vdso.so.1 (0x00007fffb0bd5000)
        libtest.so.0.0.0 => /tmp/libtest.so.0.0.0 (0x00007f985b3db000)
        libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f985b1db000)
        /lib64/ld-linux-x86-64.so.2 (0x00007f985b3e7000)
```

首先可以看到，二进制里面 `simple_function` 依然属于 undefined 状态。但 `main` 也指定了 NEEDED libtest.so.0.0.0，那么在运行的时候，ld.so 就会去寻找这个动态库。由于当前路径不在系统默认路径中，直接运行是找不到的（`not found`），这里的解决办法是添加动态库的路径到 `LD_LIBRARY_PATH` 中。

### soname

上述例子中，编译出来的动态库名称带有完整的版本号：`major.minor.patch=0.0.0`，但一般认为，如果 `major` 版本号没有变，可以认为是 ABI 兼容的，可以更新动态库的版本，而不用重新编译程序。但是，上面的例子里，`readelf -d main` 显示 NEEDED 的动态库名字里也包括了完整的版本号，那就没有办法寻找到同 major 的不同版本了。

解决办法是让同 major 的不同版本共享同一个 soname，常见的做法就是只保留 major 版本号：`libtest.so.0`，而不是 `libtest.so.0.0.0`。在编译动态库的时候，通过 `-Wl,-soname,libtest.so.0` 参数来指定 soname：

```shell
$ gcc -fPIC -shared source1.c -Wl,-soname,libtest.so.0 -o libtest.so.0.0.0
$ gcc main.c libtest.so.0.0.0 -o main
$ readelf -d main
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libtest.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
```

此时可以看到 NEEDED 的动态库名字已经是预期的 `libtest.so.0`，这意味着 `main` 函数在动态加载的时候，不考虑小版本，只指定了 `major` 版本为 0 的 libtest 动态库。但单是这样还不能运行：

```shell
$ LD_LIBRARY_PATH=$PWD ./main
./main: error while loading shared libraries: libtest.so.0: cannot open shared object file: No such file or directory
```

毕竟 ld.so 要找的是 `libtest.so.0`，但是文件系统里只有 `libtest.so.0.0.0`，最后的这一步用符号链接来实现：

```shell
$ ln -s libtest.so.0.0.0 libtest.so.0
$ LD_LIBRARY_PATH=$PWD ./main
Simple function
```

这样，如果哪天发布了 libtest.so 的 0.0.1 版本，只需要修改符号链接 `libtest.so.0 -> libtest.so.0.0.1` 即可，不需要重新编译 `main` 程序。

想要查看动态库的 soname，可以用 `readelf -d` 查看：

```shell
$ readelf -d libtest.so.0.0.0
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x000000000000000e (SONAME)             Library soname: [libtest.so.0]
```

### dynamic linker/loader

前文讲到，动态链接库参与链接的时候，实际上函数本身没有链接进可执行程序，最后的加载是由 dynamic linker/loader 完成的，在 linux 上是 ld.so，在 macOS 上是 dyld。它在程序启动的时候，负责根据 NEEDED 信息，知道程序要加载哪些动态库，然后去文件系统里找，如果找到了，就把相应的动态库加载到内存中，然后把可执行程序中对动态链接库的函数调用，变成真实的地址。相当于把原来静态链接的时候，链接器做的事情，挪到了程序运行开始时，即 linking at run time。

那么这里就涉及到一个问题了：NEEDED 只记录了文件名，但是却没有路径。这意味着动态库也需要用类似 PATH 的机制，在一些路径里去寻找一个想要的动态库。例如前文修改 `LD_LIBRARY_PATH`，实际上就是告诉 ld.so，可以在这个环境变量指向的路径中寻找动态库的文件。

而用系统包管理器安装的动态库，一般不需要修改 `LD_LIBRARY_PATH` 也可以用。这是靠 `/etc/ld.so.cache` 文件实现的。在动态库相关的问题里，经常会看到运行 `ldconfig` 命令。这个命令的用途是，收集系统目录里的动态库，建立一个索引，保存在 `/etc/ld.so.cache` 文件中。然后 ld.so 直接去 `/etc/ld.so.cache` 中寻找 NEEDED 的动态库对应的文件系统中的路径，不需要再重新扫描一遍目录了。所以 `/etc/ld.so.cache` 就是一个文件系统中动态库的缓存，这也就是为啥叫做 `ld.so.cache`。

既然是缓存，就要考虑缓存和实际对不上的情况，这就是为啥要运行 `ldconfig` 命令更新缓存。当然了，包管理器会自动运行 `ldconfig`，只有自己 `make install` 一些库的时候，才需要手动进行 `ldconfig`。

`ldconfig` 会从 `/etc/ld.so.conf` 中配置的路径中扫描动态链接库，常见的路径包括：

- /lib/x86_64-linux-gnu
- /usr/lib/x86_64-linux-gnu
- /usr/local/lib
- /usr/local/lib/x86_64-linux-gnu

包管理器安装的动态库基本都在这些目录中。可以用 `ldconfig -p` 来查看缓存 `ld.so.cache` 的内容：

```shell
$ /sbin/ldconfig -p
1967 libs found in cache `/etc/ld.so.cache'
        libz3.so.4 (libc6,x86-64) => /lib/x86_64-linux-gnu/libz3.so.4
        libz3.so (libc6,x86-64) => /lib/x86_64-linux-gnu/libz3.so
        ld-linux.so.2 (ELF) => /lib/i386-linux-gnu/ld-linux.so.2
        ld-linux.so.2 (ELF) => /lib32/ld-linux.so.2
        ld-linux.so.2 (ELF) => /lib/ld-linux.so.2
        ld-linux-x86-64.so.2 (libc6,x86-64) => /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2
        ld-linux-x32.so.2 (libc6,x32) => /libx32/ld-linux-x32.so.2
```

维护了 soname 到文件系统中动态库文件的映射。并且添加了一些属性来帮助 ld.so 进行过滤和选择。

### rpath

除了 LD_LIBRARY_PATH 和 `/etc/ld.so.cache`，ld.so 还可以通过 rpath 来寻找动态库。设想要打包一个 Qt 程序，希望在别人的机器上可以直接跑，但是别人的机器上不一定有 Qt，因此需要把程序和 Qt 的各种动态库打包在一起。但是，这时候 Qt 的动态库不会在系统路径中，不会被 `ldconfig` 索引。一种办法就是写一个脚本，设置一下 `LD_LIBRARY_PATH`，再启动 Qt 程序。另一种办法，就是利用 rpath：在程序中就告诉 ld.so 去哪里找它依赖（NEEDED）的动态库。这个路径可以是相对于可执行文件的路径。

设置 `rpath` 的方法是，编译的时候添加 `-Wl,-rpath,RPATH` 选项，例如：

```shell
$ gcc main.c libtest.so.0.0.0 -o main
$ ./main
./main: error while loading shared libraries: libtest.so.0: cannot open shared object file: No such file or directory
$ gcc main.c libtest.so.0.0.0 -Wl,-rpath,$PWD -o main
$ ./main
Simple function
$ readelf -d main
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libtest.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x000000000000001d (RUNPATH)            Library runpath: [/tmp]
$ gcc main.c libtest.so.0.0.0 -Wl,-rpath,'$ORIGIN' -o main
$ ./main
Simple function
$ readelf -d main
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libtest.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x000000000000001d (RUNPATH)            Library runpath: [$ORIGIN]
```

第一个编译命令不带 `rpath`，因此 ld.so 会找不到动态库，可以添加 LD_LIBRARY_PATH 的办法来解决。第二个和第三个编译命令带 `rpath`，其中第二个使用了绝对路径，第三个使用了相对路径（`$ORIGIN` 表示可执行文件所在的目录）。那么，ld.so 在寻找 libtest.so.0 的时候，会在 RUNPATH 中进行寻找。

### 调试

动态链接经常会遇到各种找不到动态库的问题，需要使用一些工具来帮助找到问题。最常用的就是 `ldd` 命令，显示一个程序依赖的动态库以及路径：

```shell
$ ldd $(which vim)
        linux-vdso.so.1 (0x00007fff599a4000)
        libm.so.6 => /lib/x86_64-linux-gnu/libm.so.6 (0x00007f0504dfc000)
        libtinfo.so.6 => /lib/x86_64-linux-gnu/libtinfo.so.6 (0x00007f0504dc9000)
        libselinux.so.1 => /lib/x86_64-linux-gnu/libselinux.so.1 (0x00007f0504d9b000)
        libsodium.so.23 => /lib/x86_64-linux-gnu/libsodium.so.23 (0x00007f05049a6000)
        libacl.so.1 => /lib/x86_64-linux-gnu/libacl.so.1 (0x00007f0504d90000)
        libgpm.so.2 => /lib/x86_64-linux-gnu/libgpm.so.2 (0x00007f050499e000)
        libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f05047bd000)
        /lib64/ld-linux-x86-64.so.2 (0x00007f0504f07000)
        libpcre2-8.so.0 => /lib/x86_64-linux-gnu/libpcre2-8.so.0 (0x00007f0504723000)
        libpthread.so.0 => /lib/x86_64-linux-gnu/libpthread.so.0 (0x00007f0504d89000)
```

当然了，`ldd` 有一定的风险，不建议在不信任的程序上运行 `ldd`，详情见 [ldd.1](https://man7.org/linux/man-pages/man1/ldd.1.html)。更稳妥的方法是用 `objdump -p` 或者 `readelf -d`：

```shell
$ objdump -p $(which vim) | grep NEEDED
$ readelf -d $(which vim) | grep NEEDED
```

但是 ldd 可以打印出动态库依赖的动态库，而 objdump 和 readelf 只会打印直接依赖。也可以设置环境变量，让 ld.so 打印出加载的动态库：

```shell
$ export LD_DEBUG=files
$ ./main
   2243766:     file=libtest.so.0 [0];  needed by ./main [0]
   2243766:     file=libtest.so.0 [0];  generating link map
   2243766:       dynamic: 0x00007fcd57c23df8  base: 0x00007fcd57c20000   size: 0x0000000000004018
   2243766:         entry: 0x00007fcd57c20000  phdr: 0x00007fcd57c20040  phnum:                  9
   2243766:
   2243766:     file=libc.so.6 [0];  needed by ./main [0]
   2243766:     file=libc.so.6 [0];  generating link map
   2243766:       dynamic: 0x00007fcd57bf1b60  base: 0x00007fcd57a20000   size: 0x00000000001e0f50
   2243766:         entry: 0x00007fcd57a47350  phdr: 0x00007fcd57a20040  phnum:                 14
   2243766:
   2243766:     calling init: /lib64/ld-linux-x86-64.so.2
   2243766:     calling init: /lib/x86_64-linux-gnu/libc.so.6
   2243766:     calling init: /tmp/libtest.so.0
   2243766:     initialize program: ./main
   2243766:     transferring control: ./main
   2243766:     calling fini: ./main [0]
   2243766:     calling fini: /tmp/libtest.so.0 [0]
Simple function
```

### macOS

macOS 与 Linux 下动态库的使用方法基本类似，但有一些细微的差别。首先是 macOS 上的动态库的后缀用的是 dylib 而不是 so：

```shell
$ gcc -fPIC -shared source1.c -o libtest.dylib
$ gcc main.c libtest.dylib -o main
$ objdump -t libtest.dylib
libtest.dylib:  file format mach-o arm64

SYMBOL TABLE:
0000000000003f7c g     F __TEXT,__text _simple_function
0000000000000000         *UND* _printf
$ objdump -t main
main:   file format mach-o arm64

SYMBOL TABLE:
0000000100000000 g     F __TEXT,__text __mh_execute_header
0000000100003f94 g     F __TEXT,__text _main
0000000000000000         *UND* _simple_function
```

虽然这里用的是 gcc 命令，但实际上 macOS 上的 gcc 命令是 clang。这里直接用 clang 命令也是一样的。可以看到，这里的可执行文件中 `simple_function` 函数也是处于 undefined 状态，需要在运行时由 `libtest.dylib` 提供。

macOS 下的动态链接器是 dyld，它会解析 MachO 的 Load command 去加载动态库：

```shell
$ objdump -p main
Load command 13
          cmd LC_LOAD_DYLIB
      cmdsize 40
         name libtest.dylib (offset 24)
   time stamp 2 Thu Jan  1 08:00:02 1970
      current version 0.0.0
compatibility version 0.0.0
Load command 14
          cmd LC_LOAD_DYLIB
      cmdsize 56
         name /usr/lib/libSystem.B.dylib (offset 24)
   time stamp 2 Thu Jan  1 08:00:02 1970
      current version 1319.100.3
compatibility version 1.0.0
```

这就相当于 Linux 中的 NEEDED，告诉动态链接器要加载哪些动态库。可以用 `otool -L` 或者 `dyld_info` 命令列出可执行文件所有依赖的动态库：

```shell
$ otool -L main
main:
        libtest.dylib (compatibility version 0.0.0, current version 0.0.0)
        /usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1319.100.3)
$ dyld_info -dependents main
main [arm64]:
    -dependents:
        attributes     load path
                       libtest.dylib
                       /usr/lib/libSystem.B.dylib
```

macOS 也提供了 rpath 的机制，在 `LC_LOAD_DYLIB` 中指定 `@rpath`，然后通过 `LC_RPATH` 指定有哪些 rpath，那么动态链接器就可以根据可执行文件的相对路径去寻找动态库：

```shell
$ objdump -p /Applications/Visual\ Studio\ Code.app/Contents/MacOS/Electron
Load command 8
          cmd LC_RPATH
      cmdsize 48
         path @executable_path/../Frameworks (offset 12)
Load command 13
          cmd LC_LOAD_DYLIB
      cmdsize 80
         name @rpath/Electron Framework.framework/Electron Framework (offset 24)
   time stamp 0 Thu Jan  1 08:00:00 1970
      current version 22.5.2
compatibility version 0.0.0
Load command 14
          cmd LC_LOAD_DYLIB
      cmdsize 56
         name /usr/lib/libSystem.B.dylib (offset 24)
   time stamp 0 Thu Jan  1 08:00:00 1970
      current version 1311.100.3
$ otool -L /Applications/Visual\ Studio\ Code.app/Contents/MacOS/Electron
/Applications/Visual Studio Code.app/Contents/MacOS/Electron:
        @rpath/Electron Framework.framework/Electron Framework (compatibility version 0.0.0, current version 22.5.2)
        /usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1311.100.3)
```

也可以让 dyld 动态打印日志：

```shell
$ export DYLD_PRINT_LIBRARIES=1
$ ./main
dyld[17486]: <F4E9A9E0-E958-3D0C-8D5A-7DC3ABA8E8C4> /Volumes/Data/temp/main
dyld[17486]: <DD5E30FB-753D-3746-8034-50C56971C47B> /Volumes/Data/temp/libtest.dylib
dyld[17486]: <4BEBCD61-9E62-39BE-BFD2-C7D0689A826D> /usr/lib/libSystem.B.dylib
dyld[17486]: <FEA038BA-CC59-3085-93B0-AB8437AA6CE2> /usr/lib/system/libcache.dylib
dyld[17486]: <34AC4B05-E145-3C58-8C24-1190770EAB31> /usr/lib/system/libcommonCrypto.dylib
dyld[17486]: <1D6552C4-49C4-374F-8371-198BCFC4174D> /usr/lib/system/libcompiler_rt.dylib
dyld[17486]: <E61C2838-9EA2-33CE-B96B-85FF38DB7744> /usr/lib/system/libcopyfile.dylib
dyld[17486]: <4A9F9101-A1B1-3FB7-89EA-746CFCE95099> /usr/lib/system/libcorecrypto.dylib
dyld[17486]: <C2FD3094-B465-39A4-B774-16583FF53C4B> /usr/lib/system/libdispatch.dylib
dyld[17486]: <A2947B47-B494-36D4-96C6-95977FFB51FB> /usr/lib/system/libdyld.dylib
dyld[17486]: <C4512BA5-7CA3-30AE-9793-5CC5417F0FC3> /usr/lib/system/libkeymgr.dylib
dyld[17486]: <91A88FDF-FD27-32AF-A2CE-70F7E4065C3B> /usr/lib/system/libmacho.dylib
dyld[17486]: <A2D17FF6-CBC6-3D19-89E1-F5E57191E8A3> /usr/lib/system/libquarantine.dylib
dyld[17486]: <2213EE66-253B-3234-AA4D-B46F07C3540E> /usr/lib/system/libremovefile.dylib
dyld[17486]: <68D76774-F8B4-36EA-AA35-0AB4044D56C7> /usr/lib/system/libsystem_asl.dylib
dyld[17486]: <5541DF62-A795-3F57-A54C-1AEC4DD3E44C> /usr/lib/system/libsystem_blocks.dylib
dyld[17486]: <95A70E20-1DF3-3DDF-900C-315ED0B2C067> /usr/lib/system/libsystem_c.dylib
dyld[17486]: <BEB9DE52-6F49-370A-B45B-CBE6780E7083> /usr/lib/system/libsystem_collections.dylib
dyld[17486]: <121F8B4D-3939-300D-BE22-979D6B476361> /usr/lib/system/libsystem_configuration.dylib
dyld[17486]: <7CE9526A-B673-363A-8905-71D080974C0E> /usr/lib/system/libsystem_containermanager.dylib
dyld[17486]: <54BF691A-0908-3548-95F2-34CFD58E5617> /usr/lib/system/libsystem_coreservices.dylib
dyld[17486]: <579733C7-851D-3B3E-83B5-FD203BA50D02> /usr/lib/system/libsystem_darwin.dylib
dyld[17486]: <4EFF0147-928F-3321-8268-655FE71DC209> /usr/lib/system/libsystem_dnssd.dylib
dyld[17486]: <5068382F-DC0F-3824-8ED5-18A24B35FEF9> /usr/lib/system/libsystem_featureflags.dylib
dyld[17486]: <4448FB99-7B1D-3E15-B7EE-3340FF0DA88D> /usr/lib/system/libsystem_info.dylib
dyld[17486]: <82E529F5-C4DF-3D42-9113-3A4F87FEF1A0> /usr/lib/system/libsystem_m.dylib
dyld[17486]: <0AC99C6E-CB01-30E5-AB10-65AB990652A5> /usr/lib/system/libsystem_malloc.dylib
dyld[17486]: <3B2CC4A9-A5EE-3627-8293-4AF4D891074E> /usr/lib/system/libsystem_networkextension.dylib
dyld[17486]: <E4AA6E5F-2501-3382-BFB3-64464E6D8254> /usr/lib/system/libsystem_notify.dylib
dyld[17486]: <99FDEFF2-36F1-3436-B8B2-DE0003B5A4BF> /usr/lib/system/libsystem_sandbox.dylib
dyld[17486]: <E529D1AC-D20A-3308-9033-E1712A9C655E> /usr/lib/system/libsystem_secinit.dylib
dyld[17486]: <42F503E2-9273-360A-A086-C1B19BBD3962> /usr/lib/system/libsystem_kernel.dylib
dyld[17486]: <F80C6971-C080-31F5-AB6E-BE01311154AF> /usr/lib/system/libsystem_platform.dylib
dyld[17486]: <46D35233-A051-3F4F-BBA4-BA56DDDC4D1A> /usr/lib/system/libsystem_pthread.dylib
dyld[17486]: <F9F1F4BE-D97F-37A7-8382-552C22DF1BB4> /usr/lib/system/libsystem_symptoms.dylib
dyld[17486]: <3F3E75B7-F0A7-30BB-9FD7-FD1307FE6055> /usr/lib/system/libsystem_trace.dylib
dyld[17486]: <E3BF7A76-2CBE-3DB9-8496-8BB6DBBE0CFC> /usr/lib/system/libunwind.dylib
dyld[17486]: <F3F19227-FF8F-389C-A094-6F4C16E458AF> /usr/lib/system/libxpc.dylib
dyld[17486]: <52AA13E2-567C-36C2-9494-7B892FDBF245> /usr/lib/libc++abi.dylib
dyld[17486]: <5BEAFA2B-3AF4-3ED2-B054-1F58A7C851EF> /usr/lib/libobjc.A.dylib
dyld[17486]: <FB664621-26AE-3F46-8F5A-DD5D890A5CE7> /usr/lib/liboah.dylib
dyld[17486]: <54E8FBE1-DF0D-33A2-B8FA-356565C12929> /usr/lib/libc++.1.dylib
Simple function
```
