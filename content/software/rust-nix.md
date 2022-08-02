---
layout: post
date: 2022-08-02 14:28:00 +0800
tags: [nix,rust]
category: software
title: 用 Nix 编译 Rust 项目
---

## 背景

Rust 项目一般是用 Cargo 管理，但是它的缺点是每个项目都要重新编译一次所有依赖，硬盘空间占用较大，不能跨项目共享编译缓存。调研了一下，有若干基于 Nix 的 Rust 构建工具：

- cargo2nix: https://github.com/cargo2nix/cargo2nix
- carnix: 不再更新
- crane: https://github.com/ipetkov/crane
- crate2nix: https://github.com/kolloch/crate2nix
- naersk: https://github.com/nix-community/naersk
- nocargo: https://github.com/oxalica/nocargo

下面我分别来尝试一下这几个工具的使用。

## crate2nix

### 安装

首先要安装 crate2nix，由于它的稳定版本 0.10.0 已经是去年的版本了，我直接用了 master 分支。如果是直接安装，用：

```shell
nix-env -i -f https://github.com/kolloch/crate2nix/tarball/master
```

但我是用 flakes + home-manager 管理的，所以我实际的配置方法是：

1. 向 flake.nix 添加 crate2nix 到 inputs，并且设置 `crate2nix.flake = false`
2. 把 crate2nix 从 inputs 传到实际的 home manager 配置，然后在 `home.packages` 里加入 `callPackage crate2nix {}`

### 使用

接下来，找到一个 Rust 项目，在其中运行 `crate2nix generate`:

```shell
$ crate2nix generate
Generated ./Cargo.nix successfully.
```

构建：

```shell
nix build -f Cargo.nix rootCrate.build
```

编译的结果可以在 `result/bin` 下看到。

我编译的是 `jiegec/webhookd`，编译过程中出现了报错：

```
>   = note: ld: framework not found Security
>           clang-11: error: linker command failed with exit code 1 (use -v to see invocation)
>
>
> error: aborting due to previous error
```

根据 crate2nix 的文档，需要添加额外的 native 依赖：

```shell
$ cat default.nix
{ pkgs ? import <nixpkgs> { } }:

let
  generatedBuild = import ./Cargo.nix {
    inherit pkgs;
    defaultCrateOverrides = with pkgs; defaultCrateOverrides // {
      webhookd = attrs: {
        buildInputs =
          lib.optionals
            stdenv.isDarwin
            [ darwin.apple_sdk.frameworks.Security ];
      };
    };
  };
in
generatedBuild.rootCrate.build
$ nix build -f default.nix
$ ./result/bin/webhookd --version
webhookd 0.2.1
```

这样就可以正常运行了。

### 原理

它的原理是使用 `cargo_metadata` 库从 Cargo.lock 中获取各个 crate 的信息，然后翻译成 `Cargo.nix`，之后就是由 nix 来编译各个 crate 的内容。所以一开始还是需要先用 Cargo 创建项目，添加依赖，生成 `Cargo.lock`；之后再用 `crate2nix generate` 同步依赖信息到 `Cargo.nix` 文件，构建的时候就不需要 Cargo 参与了，直接 rustc。