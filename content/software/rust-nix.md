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

下面出现的一些命令参考了对应项目的文档。

## cargo2nix

### 安装

cargo2nix 提供了 flakes 支持，不需要单独安装。

### 使用

cargo2nix 的运行比较简单，利用 flakes 的特性，直接 `nix run` 即可：

```shell
nix run github:cargo2nix/cargo2nix
```

它会生成一个 Cargo.nix 文件，还需要编写一个 `flake.nix` 配合使用，这里以 `jiegec/webhookd` 为例：

```nix
{
  inputs = {
    cargo2nix.url = "github:cargo2nix/cargo2nix/release-0.11.0";
    flake-utils.follows = "cargo2nix/flake-utils";
    nixpkgs.follows = "cargo2nix/nixpkgs";
  };

  outputs = inputs: with inputs;
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [cargo2nix.overlays.default];
        };

        rustPkgs = pkgs.rustBuilder.makePackageSet {
          rustVersion = "1.61.0";
          packageFun = import ./Cargo.nix;
        };

      in rec {
        packages = {
          webhookd = (rustPkgs.workspace.webhookd {}).bin;
          default = packages.webhookd;
        };
      }
    );
}
```

然后编译：

```shell
$ git add .
$ nix build
$ ./result-bin/bin/webhookd --version
webhookd 0.2.1
```

### 原理

cargo2nix 解析了 Cargo.lock，生成 Cargo.nix 文件，最后包装成 flake.nix。

## crane

### 安装

crane 不需要安装，直接用 flakes 即可。

### 使用

crane 使用的时候，直接在项目中编写 `flake.nix`：

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    crane.url = "github:ipetkov/crane";
    crane.inputs.nixpkgs.follows = "nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, crane, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system: {
      packages.default = crane.lib.${system}.buildPackage {
        src = ./.;
      };
    });
}
```

这样就可以了，不需要使用工具从 Cargo.lock 生成对应的 Cargo.nix。

但是由于 webhookd 依赖 native 库，所以还需要需要手动加入 native 依赖：

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    crane.url = "github:ipetkov/crane";
    crane.inputs.nixpkgs.follows = "nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, crane, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
      in
      {
        packages.default = crane.lib.${system}.buildPackage {
          src = ./.;

          buildInputs = with pkgs; [
            libiconv
            darwin.apple_sdk.frameworks.Security
          ];
        };
      });
}
```

构建：

```shell
$ nix build
$ ./result/bin/webhookd --version
webhookd 0.2.1
```

### 原理

crane 会把所有的依赖打包起来进行一次构建，然后再加上项目的源代码再构建一次，这样来实现 incremental compilation。它还提供了一些 check lint 等实用的命令。但是，它的目的和其他项目不大一样，它并不考虑跨项目的依赖缓存。

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

前面的 cargo2nix 没有出现这样的问题，应该是因为 cargo2nix 帮我们引入了 Security 的依赖，见 [overrides.nix](https://github.com/cargo2nix/cargo2nix/blob/9c3b846c727300f8146f20f01c5387b398d1e0e4/overlay/overrides.nix)。

根据 crate2nix 的文档，需要添加额外的 native 依赖：

```nix
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
```

然后构建：

```shell
$ nix build -f default.nix
$ ./result/bin/webhookd --version
webhookd 0.2.1
```

这样就可以正常运行了。

### 原理

它的原理是使用 `cargo_metadata` 库从 Cargo.lock 中获取各个 crate 的信息，然后翻译成 `Cargo.nix`，之后就是由 nix 来编译各个 crate 的内容。所以一开始还是需要先用 Cargo 创建项目，添加依赖，生成 `Cargo.lock`；之后再用 `crate2nix generate` 同步依赖信息到 `Cargo.nix` 文件，构建的时候就不需要 Cargo 参与了，直接 rustc。