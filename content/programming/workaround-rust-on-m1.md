---
layout: post
date: 2020-12-04 09:27:00 +0800
tags: [rust,rustc,codesign,m1,bigsur,macos,aarch64,darwin]
category: programming
title: Rust 在 M1 上的 Code Signing 问题和临时解决方法
---

不久前，rust 添加了 Tier2 的 aarch64-apple-darwin 的支持，试了一下，确实可以运行，不过当我编译的时候，出现：

```
error: failed to run custom build command for `xxxx v1.0 (/path/to/xxxx)`

Caused by:
  process didn't exit successfully: `/path/to/xxx/target/debug/build/xxx-xxxx/build-script-build` (signal: 9, SIGKILL: kill)
```

看了一下 Console.app 里面的 crash 日志，发现是 codesigning 问题。解决方法是，用 codesign 命令来签名：

```shell
# for build.rs
codesign -s - target/debug/build/*/build-script-build
# for dylib of some crates
codesign -s - target/debug/deps/*.dylib
# for final executable
codesign -s - target/debug/xxx
```

多次编译并签名后，就可以正常运行最后的二进制了：

```shell
target/debug/xxxx: Mach-O 64-bit executable arm64
```

然后就可以了。等待上游添加 code signing 支持吧。

2020-12-07 更新：找了找 cargo 的 issues，找到了[同样的问题](https://github.com/rust-lang/cargo/issues/8913)，看来并不是 code signing 支持的问题，而是在 Intel 的 Alacritty 下面，运行 Apple 的 rustc 工具链的时候，才会出现的 BUG。我也自己试了一下，在 Apple 的 Terminal 下跑编译就没有问题。