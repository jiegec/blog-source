---
layout: post
date: 2022-07-11 22:53:00 +0800
tags: [macos,ld,linking,common,fortran]
category: software
title: Archive 中 COMMON 符号的链接问题
---

## 背景

最近看到一个 [issue: irssi 1.4.1 fails to build on darwin arm64](https://github.com/NixOS/nixpkgs/issues/180308)，它的现象是，链接的时候会报错：

```
Undefined symbols for architecture arm64:
  "_current_theme", referenced from:
      _format_get_text_theme in libfe_common_core.a(formats.c.o)
      _format_get_text in libfe_common_core.a(formats.c.o)
      _strip_codes in libfe_common_core.a(formats.c.o)
      _format_send_as_gui_flags in libfe_common_core.a(formats.c.o)
      _window_print_daychange in libfe_common_core.a(fe-windows.c.o)
      _printformat_module_dest_charargs in libfe_common_core.a(printtext.c.o)
      _printformat_module_gui_args in libfe_common_core.a(printtext.c.o)
      ...
  "_default_formats", referenced from:
      _format_find_tag in libfe_common_core.a(formats.c.o)
      _format_get_text_theme_args in libfe_common_core.a(formats.c.o)
      _printformat_module_dest_args in libfe_common_core.a(printtext.c.o)
      _printformat_module_gui_args in libfe_common_core.a(printtext.c.o)
ld: symbol(s) not found for architecture arm64
```

代码 `themes.c` 定义了这两个全局变量：

```cpp
THEME_REC *current_theme;
GHashTable *default_formats;
```

并且 `themes.c` 编译出来的 `themes.c.o` 也在 archive 文件中：

```shell
$ ar t src/fe-common/core/libfe_common_core.a | grep themes.c.o
themes.c.o
```

并且 `themes.c.o` 也定义了这两个符号：

```shell
$ objdump -t src/fe-common/core/libfe_common_core.a.p/themes.c.o | grep COM
0000000000000008         01 COM    00 0300 _current_theme
0000000000000008         01 COM    00 0300 _default_formats
0000000000000008         01 COM    00 0300 _themes
```

那么，问题在哪呢？看起来，链接的时候提供了 `libfe_common_core.a` 的参数，并且 `.a` 里面也有 `themes.c.o`，我们要找的符号也有定义，那么为什么会出现 `Undefined symbols` 的问题呢？

答案出在 COMMON 符号上。

## COMMON 符号

COMMON 符号的原因和原理，详细可以见 [MaskRay 的博客 All about COMMON symbols](https://maskray.me/blog/2022-02-06-all-about-common-symbols)，里面从链接器的角度很详细地讲述了这个问题。

简单来说，COMMON 符号的引入是为了和 Fortran 进行互操作。它在 C 中对应了没有初始化语句的全局变量。实际上到最后，还是会保存到 .bss 段中，默认清零。所以：

```cpp
int common_symbol;
int not_common_symbol = 0;
```

两个语句最终结果是类似的，只不过第一个是 COMMON Symbol，第二个就是普通的 GLOBAL Symbol。

这看起来和 `Undefined symbols` 错误还是没有关系。问题在哪？

## Archive

静态库通常是以 Archive 的方式给出，后缀是 `.a`。它实际上是一堆 `.o` 打包的集合，外加一个索引，即单独保存一个表，保存了每个 `.o` 定义了哪些符号。这样的好处是找符号的时候，不用遍历 `.o`，而是直接在索引里面找相关的符号。

为了创建一个 Archive，Linux 上可以用 `ar` 命令：

```shell
ar cr libxxx.a a.o b.o c.o
```

其中 `c` 表示 create，`r` 表示插入（和覆盖）。

macOS 上要用 `libtool -static` 来创建 Archive：

```shell
libtool -static libxxx.a a.o b.o c.o
```

否则链接的时候会报错：

```
ld: warning: ignoring file libxxx.a, building for macOS-arm64 but attempting to link with file built for unknown-unsupported file format
```

然后用 `ar t` 命令就可以看 Archive 有哪些内容：

```shell
$ ar t libxxx.a
a.o
b.o
c.o
```

可以用 `nm --print-armap` 命令查看 Archive 的索引：

```shell
$ nm --print-armap libxxx.a
Archive index:
symbol1 in a.o
symbol2 in b.o
symbol3 in c.o

a.o:
0000000000000000 T symbol1
```

所以我们已经了解了 Archive 的情况：它是多个 `.o` 文件的集合，并且实现了索引。链接的时候，会通过索引来找 `.o`，而不是遍历所有的 `.o` 文件。

## 链接问题

那么，回到一开始的链接问题，既然我们已经确认了，`.o` 文件中定义了符号，并且这个 `.o` 也确实在 `.a` 文件中，那就只剩下最后一个可能了：索引里面没有这个符号。

用 `nm --print-armap` 命令尝试，发现上面的 `_default_formats` 和 `_current_theme` 只在对应的 `.o` 中有定义，在 Archive index 部分是没有的。

网友 @ailin-nemui 指出了这个问题，并且提供了一个链接：[OS X linker unable to find symbols from a C file which only contains variables](https://stackoverflow.com/questions/19398742/os-x-linker-unable-to-find-symbols-from-a-c-file-which-only-contains-variables/26581710#26581710)。它讲了很重要的一点，是 macOS 的 ar/ranlib/libtool 版本默认情况下不会为 COMMON 符号创建索引。所以，解决方案也很明确了：

1. 第一种 不要创建 COMMON 符号：添加编译选项 `-fno-common`，这个选项在比较新的编译器里都是默认了
2. 第二种 为 COMMON 符号创建索引：用 `libtool -static -c` 命令，其中 `-c` 选项就是打开为 COMMON 符号创建索引
3. 第三种 修改代码：给全局变量设置一个初始化值

这样，这个问题就得到了妥善的解决。

## 附录

下面是 [macOS libtool manpage](https://www.unix.com/man-page/osx/1/LIBTOOL/) 中写的相关文档：

```
-c     Include common symbols as definitions with respect to the table of contents.  This is seldom the intended behavior for linking  from
	      a library, as it forces the linking of a library member just because it uses an uninitialized global that is undefined at that point
	      in the linking.  This option is included only because this was the original behavior of ranlib.  This option is not the default.
```