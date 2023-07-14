---
layout: post
date: 2019-03-24
tags: [rcore,x86,x86_64,static,musl,sqlite]
categories:
    - software
---

# 静态编译 sqlite3

最近 rCore 支持了动态链接库，于是想着在测试 sqlite 的时候直接用动态的，不过出现了玄学的问题，它会访问一个不存在的地址，看代码也没看出个所以然来。所以研究了一下 sqlite 的静态编译。首先在 `configure` 的时候尝试了一下：

```bash
$ ./configure CC=x86_64-linux-musl-gcc --disable-shared --enabled-static
```

发现 `libsqlite` 确实是静态了，但是 `sqlite3` 并不是。一番研究以后，发现是 `libtool` 的原因，只要这样编译：

```bash
$ make LTLINK_EXTRAS=-all-static
```

就可以编译出静态的 `sqlite3` ：

```bash
sqlite3: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked, with debug_info, not stripped
```

