---
layout: post
date: 2024-01-25
tags: [linux,loongarch,chromium,port]
categories:
    - software
---

# Chromium 构建与移植

## 背景

Google Chrome 也用了很长时间了，但是一直没有尝试过构建 Chromium，这次趁着往 LoongArch 移植 Chromium 的机会，学习了一下 Chromium 的构建。

<!-- more -->

## 克隆代码

Chromium 官方的构建文档链接是 [Checking out and building Chromium on Linux](https://chromium.googlesource.com/chromium/src/+/main/docs/linux/build_instructions.md)，按照流程做就可以：

```shell
cd build-chromium

# setup depot_tools
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
# fish syntax to add depot_tools to PATH
set -x PATH $PWD/depot_tools $PATH

# clone chromium using fetch from depot_tools
mkdir chromium
cd chromium
fetch --nohooks chromium
# or
fetch --nohooks --no-history chromium

# setup build dependencies
cd src
./build/install-build-deps.sh
gclient runhooks
```

当然了，这个过程主要是为了开发 chromium 做的，实际上可以做一些简化：如果只是要编译一个已经发布正式版的 chromium，可以直接下载 tarball，例如 [https://commondatastorage.googleapis.com/chromium-browser-official/chromium-120.0.6099.216.tar.xz](https://commondatastorage.googleapis.com/chromium-browser-official/chromium-120.0.6099.216.tar.xz)，把链接里的版本号改掉即可；这样可以省去克隆 git repo 以及一堆 submodule 的大量时间。当然了，解压本身也需要比较长的时间，对付这种大型软件必须要有耐心。同理，depot_tools 也可以不要，毕竟自己把代码下载下来了，只需要再装一个 gn，就可以完成剩下的构建。

## 构建

按照默认配置构建，只需要：

```shell
gn gen out/Default
```

意思是用 `gn` 工具生成一套用 Ninja 构建的配置，目录在 `out/Default` 下面，然后不添加额外的设置。要构建 Chromium，那就在里面跑 ninja：

```shell
ninja -C out/Default chrome
# or
autoninja -C out/Default chrome
```

但是如果你去翻各个 Linux 发行版，就会发现它们都会传很多的参数给 gn，实现各种目的：

```shell
gn gen out/Default --args='...'
```


下面给出一些链接：

- [AOSC OS](https://github.com/AOSC-Dev/aosc-os-abbs/tree/stable/app-web/chromium/autobuild)
- [Arch Linux](https://gitlab.archlinux.org/archlinux/packaging/packages/chromium/-/blob/main/PKGBUILD?ref_type=heads)
- [Debian](https://salsa.debian.org/chromium-team/chromium/-/blob/master/debian/rules?ref_type=heads)
- [Fedora](https://src.fedoraproject.org/rpms/chromium/blob/rawhide/f/chromium.spec)

这里的门门道道就很多了，很多编译参数影响了最终 Chromium 的功能、性能等等重要的指标。

首先是工具链的选择：Chromium 开发的时候用的是很新的 Clang，还自带了一份 libc++，但是很自然地各大发行版都会倾向于用自己的工具链，那么这个工具链可能是稍微旧一些的 Clang，或者是 GCC，这里就会出现大量的问题：Chromium 开发的时候是不在旧 Clang 或者 GCC 上测试的，所以各个发行版都要维护一堆的 patch，使得用稍微旧一点的正式版 Clang/GCC 也可以构建 Chromium。这些 patch 可以在上面的链接中找到。

除了编译器以外，还有很多依赖也可以选择用 chromium 自带的版本，还是系统自带的版本，这里也有很多可能性。例如要用系统自带的 Clang：

```conf
host_toolchain="//build/toolchain/linux/unbundle:default"
custom_toolchain="//build/toolchain/linux/unbundle:default"
clang_base_path="/usr" 
clang_use_chrome_plugins=false
```

也可以尝试用 GCC，但是需要打不少的 patch：

```conf
CC=gcc CXX=g++ AR=ar NM=nm gn gen out/Default --args='is_clang=false ...'
```

等等，还有很多可能的配置选项，这些可以在 Chromium 的源码中找到：它们会用 gn 的配置语言编写，放在 `declare_args` 里面。

## 移植

除了在 amd64 构建以外，Chromium 主要还支持 arm64 架构，其他架构属于有第三方 patch，但是 Chromium 处于一个付出额外维护负担的状态，所以其他架构的补丁就没有合并，因此你会发现 riscv64 和 ppc64le 架构上能找到一些发行版自己维护的 patch，并且没有合并到上游。loongarch64 的处境也是类似的，龙芯之前做过一些移植，尝试提交上游，但是最后没有合并进去。

但是 Chromium 对于桌面来说又是比较重要的，无论是作为浏览器，还是用在 Electron 或者 QT 生态中。因此借着龙芯把移植 Electron 的 patch 放出来的机会，顺便把 Chromium 的移植做了：最早是 [@prcups](https://github.com/prcups) 把补丁移植到 qt6-webengine 上，证实了补丁的可用性；之后我又移植到了最新版的 Chromium 上，补丁发布在 [AOSC-Dev/chromium-loongarch64](https://github.com/AOSC-Dev/chromium-loongarch64)。目前 120 已经适配了，但是这几天 121 又发布了，需要再次更新补丁。新版 Electron 的补丁也还没有做。

在这个过程中，也发现龙芯原来的 patch 内置的 bug：与 seccomp sandbox 有关，原来的代码把对 stat 的处理照抄到了 statx 上，但是它的参数顺序和含义都是不一样的，不能直接照抄。对着代码，大概是正确地实现了出来。之前没有遇到这个问题，大概率是 Electron 下不会用到这个 sandbox。回顾下来，移植的补丁不算多，主要是 crashpad 和 sandbox 两部分代码，观察了一下 archriscv 维护的 riscv 补丁，其实也是类似的。

这个过程遇到了很多困难：一开始 Clang 构建遇到问题，于是改用 GCC，但是前面也说了，Chromium 没有用 GCC 测试，所以会出现很多问题，需要细心地修复；最后终于搞好了以后，再回到 Clang，发现 Clang 的问题已经被 Fedora/Debian 等发行版解决，只需要导入已有的补丁即可。这样折腾下来，终于是搞定了。而目前龙芯的构建机器（3C5000）性能还是不够好，构建一次完整的 Chromium 需要九个小时，未来等龙芯服务器性能提升以后，可以预见到维护成本的降低。