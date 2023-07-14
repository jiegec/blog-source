---
layout: post
date: 2022-08-02
tags: [nix,rust]
categories:
    - software
---

# 用 Nix 编译 Rust 项目

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

### 卖点

cargo2nix 的 README 提到了它的卖点：

- Development Shell - knowing all the dependencies means easy creation of complete shells. Run nix develop or direnv allow in this repo and see!
- Caching - CI & CD pipelines move faster when purity guarantees allow skipping more work!
- Reproducibility - Pure builds. Access to all of nixpkgs for repeatable environment setup across multiple distributions and platforms

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

### 卖点

crane 的 README 提到了它的卖点：

- Source fetching: automatically done using a Cargo.lock file
- Incremental: build your workspace dependencies just once, then quickly lint, build, and test changes to your project without slowing down
- Composable: split builds and tests into granular steps. Gate CI without burdening downstream consumers building from source.

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

crane 会把所有的依赖下载起来用 cargo 进行一次构建，把生成的 target 目录打成 `target.tar.zst`，然后再加上项目的源代码再构建一次，这样来实现 incremental compilation。它还提供了一些 check lint 等实用的命令。但是，它的目的和其他项目不大一样，它并不考虑跨项目的依赖缓存。

## crate2nix

### 卖点

crate2nix 在 README 中写的卖点：

- Same dependency tree as cargo: It uses cargo_metadata to obtain the dependency tree from cargo. Therefore, it will use the exact same library versions as cargo and respect any locked down version in Cargo.lock.
- Smart caching: It uses smart crate by crate caching so that nix rebuilds exactly the crates that need to be rebuilt. Compare that to docker layers...
- Nix ecosystem goodness: You can use all things that make the nix/NixOS ecosystem great, e.g. distributed/remote builds, build minimal docker images, deploy your binary as a service to the cloud with NixOps, ...
- Out of the box support for libraries with non-rust dependencies: It builds on top of the buildRustCrate function from NixOS so that native dependencies of many rust libraries are already correctly fetched when needed. If your library with native dependencies is not yet supported, you can customize defaultCrateOverrides / crateOverrides, see below.
- Easy to understand nix template: The actual nix code is generated via templates/build.nix.tera so you can fix/improve the nix code without knowing rust if all the data is already there.

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

## naersk

### 安装

需要安装 [niv](https://github.com/nmattia/niv):

```shell
nix-env -iA nixpkgs.niv
```

### 使用

在项目目录下，首先用 `niv` 导入 naersk：

```shell
niv init
niv add nix-community/naersk
```

然后编写一个 `default.nix`：

```nix
let
  pkgs = import <nixpkgs> { };
  sources = import ./nix/sources.nix;
  naersk = pkgs.callPackage sources.naersk { };
in
naersk.buildPackage ./.
```

构建：

```shell
$ nix build -f default.nix
$ ./result/bin/webhookd --version
webhookd 0.2.1
```

### 原理

naersk 的原理和 crane 是类似的：把所有依赖下载下来，创建一个只有依赖的项目，然后用 cargo 预编译，编译完得到的 target 目录打成 `target.tar.zst`；然后基于预编译的结果再编译整个项目。

## nocargo

### 卖点

nocargo 的 README 提到了以下卖点：

- No IFDs (import-from-derivation). See meme.
- No cargo dependency during building. Only rustc.
- No need for hash prefetching or code generation1.
- Crate level caching, globally shared.
- nixpkgs integration for non-Rust dependencies.

README 也提到了 nocargo, cargo2nix, naersk 和 buildRustPackage 的对比。

### 使用

nocargo 目前[仅支持 x86_64-linux 平台](https://github.com/oxalica/nocargo/blob/90a6d0e8dcfc2205fa69423d42bff6fd1b997121/flake.nix#L13)。

在一个 Cargo 项目中，运行：

```shell
nix run github:oxalica/nocargo init
```

它会生成 `flake.nix` 文件如下：

```nix
# See more usages of nocargo at https://github.com/oxalica/nocargo#readme
{
  description = "Rust package webhookd";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    nocargo = {
      url = "github:oxalica/nocargo";
      inputs.nixpkgs.follows = "nixpkgs";
      # inputs.registry-crates-io.follows = "registry-crates-io";
    };
    # Optionally, you can override crates.io index to get cutting-edge packages.
    # registry-crates-io = { url = "github:rust-lang/crates.io-index"; flake = false; };
  };

  outputs = { nixpkgs, flake-utils, nocargo, ... }@inputs:
    flake-utils.lib.eachSystem [ "x86_64-linux" ] (system:
      let
        ws = nocargo.lib.${system}.mkRustPackageOrWorkspace {
          src = ./.;
        };
      in rec {
        packages = {
          default = packages.webhookd;
          webhookd = ws.release.webhookd.bin;
          webhookd-dev = ws.dev.webhookd.bin;
        };
      });
}
```

构建：

```shell
$ git add .
$ nix build
```

出现了编译错误，说明 crates.io index 版本不是最新的：

```
error: Package bytes doesn't have version 1.2.0 in index. Available versions: 0.0.1 0.1.0 0.1.1 0.1.2 0.2.0 0.2.1 0.2.10 0.2.11 0.2.2 0.2.3 0.2.4 0.2.5 0.2.6 0.2.7 0.2.8 0.2.9 0.3.0 0.4.0 0.4.1 0.4.10 0.4.11 0.4.12 0.4.2 0.4.3 0.4.4 0.4.5 0.4.6 0.4.7 0.4.8 0.4.9 0.5.0 0.5.1 0.5.2 0.5.3 0.5.4 0.5.5 0.5.6 0.6.0 1.0.0 1.0.1 1.1.0
(use '--show-trace' to show detailed location information)
```

按照 `flake.nix` 中的提示，使用最新的 crates.io index：

```nix
# See more usages of nocargo at https://github.com/oxalica/nocargo#readme
{
  description = "Rust package webhookd";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    nocargo = {
      url = "github:oxalica/nocargo";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.registry-crates-io.follows = "registry-crates-io";
    };
    # Optionally, you can override crates.io index to get cutting-edge packages.
    registry-crates-io = { url = "github:rust-lang/crates.io-index"; flake = false; };
  };

  outputs = { nixpkgs, flake-utils, nocargo, ... }@inputs:
    flake-utils.lib.eachSystem [ "x86_64-linux" ] (system:
      let
        ws = nocargo.lib.${system}.mkRustPackageOrWorkspace {
          src = ./.;
        };
      in rec {
        packages = {
          default = packages.webhookd;
          webhookd = ws.release.webhookd.bin;
          webhookd-dev = ws.dev.webhookd.bin;
        };
      });
}
```

继续构建就成功了：

```shell
$ nix build
• Updated input 'nocargo/registry-crates-io':
    'github:rust-lang/crates.io-index/1ce12a7e3367a2a673f91f07ab7cc505a0b8f069' (2022-07-17)
  → follows 'registry-crates-io'
• Added input 'registry-crates-io':
    'github:rust-lang/crates.io-index/627caba32f416e706bf3f2ceac55230ec79710c5' (2022-08-02)
$ ./result/bin/webhookd --version
webhookd 0.2.1
```

## 总结

可以看到，上面的不同工具采用了不同的方法，如果要比较的话：

- Nix drv 粒度：每个依赖（cargo2nix，crate2nix，nocargo）、所有依赖（crane，naersk）。前者的好处是会跨项目共享依赖，进一步可以传到 binary cache。
- 是否生成包括完整依赖信息的 nix 文件：是（cargo2nix，crate2nix）、否（crane，naersk，nocargo）。生成的话，仓库里的 Cargo.lock 和 Cargo.nix 的信息是重复的，如果修改了 Cargo.lock，需要重新同步 Cargo.nix。
