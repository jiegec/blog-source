---
layout: post
date: 2023-12-05
tags: [linux,packaging]
categories:
    - software
---

# 包管理器打包命令速查

随着 Linux 使用逐渐深入，开始尝试参与到一些发行版/包管理器的维护当中。在此记录一下打包相关命令，方便自己速查。

<!-- more -->

## AOSC OS

文档：[Intro to Package Maintenance: Basics](https://wiki.aosc.io/developer/packaging/basics/)

用 ciel 工具克隆软件源+在容器中构建。创建一个打包环境：

```shell
ciel new
```

此时目录下包括：

1. TREE 目录：[AOSC-Dev/aosc-os-abbs](https://github.com/AOSC-Dev/aosc-os-abbs) 的克隆
2. OUTPUT-* 目录：放置打包出来的 deb

可以在 TREE 目录下进行包的更新等等操作。如果要构建包，假设在上一步创建打包环境时，名字设置为 main，用命令：

```shell
ciel build -i main [packages]
```

构建完成的 deb 会放到 `OUTPUT-[branch]` 下，例如默认是 stable 分支的话，默认会放到 `OUTPUT-stable` 下。

构建完成后，如果要提交到软件源，进入某个 OUTPUT 目录，用 `pushpkg` 命令：

```shell
pushpkg [-d] [user_name] [branch]
```

`-d` 参数表示提交后删除本地的文件。

贡献流程：

1. 从 stable checkout 出新的分支
2. 修改 TREE 里面的内容
3. 用 `ciel build -i main [packages]` 构建，可以用社区提供的 Buildbot
4. （可选）pushpkg 推到软件源
5. Push 到 GitHub 的分支，打开 pr
6. 等待审核，审核通过后，合并并 pushpkg 到 stable

## Debian

我还没有成为 Debian 维护者，因此并不了解完整流程。

对于一个已有的包，用 `apt source` 下载源码和 debian 的文件。很多包已经挪到了 salsa，也就是 debian 的 gitlab 实例上，如果有，`apt source` 会提示你可以直接从 salsa 上克隆仓库。

下载了以后，得到的是一份源码，外加 `debian` 目录。里面比较重要的是 `debian/control`（记录了包的元数据）和 `debian/rules`（如何构建）。

为了构建包，简单的办法是用 `dpkg-buildpackage` 命令。常用参数：

1. `-b`：只构建二进制包
2. `-us -uc`：没有配置 GPG，没法签名，自用的时候选择不签名
3. `-nc`：构建前不 clean
4. `-d`：即使依赖不能满足，也要构建

此外，还可以设置环境变量：

1. `DEB_BUILD_PROFILES`：设置 profile，常见的有 nocheck nodoc 等等，和 debian/control 文件里的 `<profile>` 对应
2. [`DEB_BUILD_OPTIONS`](https://www.debian.org/doc/debian-policy/ch-source.html#debian-rules-and-deb-build-options)：和 profile 类似，但是用法略有不同，常见的有 nocheck nodoc noopt nostrip 等等

对于[基于 git 的包](https://wiki.debian.org/PackagingWithGit)，例如从 salsa 上 clone 的包，可以用 gbp 工具：

1. `gbp buildpackage`：功能对应 dpkg-buildpackage。
2. `gbp import-orig`：导入一个上游源码的 tarball 到仓库中，可以添加 `--uscan` 参数让它自动检测并下载新版；可以添加 `--pristine-tar` 参数让它保留一份原始 tarball（的 delta）。

dpkg-buildpackage 默认会在当前环境下构建新包，因此如果缺了依赖，就需要全局安装。如果不想这样，可以配置 sbuild，在 chroot 中进行构建。

配置 [sbuild](https://wiki.debian.org/sbuild) 的简单办法是用 [sbuild-debian-developer-setup](https://manpages.debian.org/unstable/sbuild/sbuild-debian-developer-setup.1) 命令。它会在 `/srv/chroot` 下创建一个用于容器的 sysroot，里面是一个干净的 debian 环境。之后，可以用 sbuild 命令，在容器里面构建。

## Nixpkgs

Nixpkgs 打包过程比较简单：

1. 修改 Nixpkgs 仓库
2. 用 nix 命令构建新包：`nix build -L .#package`
3. （可选）用 nixpkgs-review 构建所有需要重新构建的包
4. Push 到 GitHub，创建 PR
5. 等待审核和合并

Homebrew 也是类似的。
