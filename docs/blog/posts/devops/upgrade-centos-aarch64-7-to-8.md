---
layout: post
date: 2023-07-31
tags: [centos,aarch64]
categories:
    - devops
---

# 记录一次 CentOS AArch64 7 到 8 的升级

## 背景

有一台 AArch64 机器安装了 CentOS 7，想要升级到 CentOS 8，这篇博客主要讲讲折腾的整个过程，而不是教程：如果真要说，就是不要升级 CentOS 大版本，直接重装吧。如果真的想折腾，可以看看下面的内容。

<!-- more -->

## 过程

### 配置 yum repo

之前升级过很多 Debian/Ubuntu，操作都很简单，替换 `/etc/apt/sources.list` 的版本代号，然后一路 `apt` 就可以了，遇到的都是小问题。但是 CentOS 7 到 CentOS 8 有一些不同：

1. repos 路径变了，不能简单地替换 7 为 8
2. CentOS 7 的 aarch64 在 centos-altarch 里面，而 CentOS 8 的 aarch64 并不是单独的，但又因为 CentOS 8 EOL 了，所以在 centos-vault 里面

因此需要首先安装 centos 8 的 repos 包，再按照 TUNA 镜像的文档去配置。

但这里又有个坑：CentOS 8 用 dnf 替代了 yum，yum 是 dnf 的 alias。而 CentOS 7 默认只有 yum，如果直接用 yum 配合 CentOS 8 的 repo，会出现错误：`Invalid version flag If`。所以要先安装一个 dnf，再升级 yum repo。

按照 repos 包的时候，在 TUNA 镜像 <https://mirrors.tuna.tsinghua.edu.cn/centos-vault/8.5.2111/BaseOS/aarch64/os/Packages/> 里找这么几个包：

1. centos-linux-release
2. centos-linux-repos
3. centos-gpg-keys

然后用 `rpm` 安装。安装完以后，按照 TUNA 镜像文档环源。

这里介绍几个常用的 rpm 命令，因为后面会经常用：

1. `rpm -qa`：列出所有已经安装的 rpm
2. `rpm -i xxx.rpm yyy.rpm`：安装新的 rpm，但不会卸载同名的旧 rpm
3. `rpm -e xxx`：卸载某个包
4. `rpm -U xxx.rpm`：安装新的 rpm，同时卸载旧 rpm

此外安装和卸载的时候，经常要用下面的参数：

1. `--nodeps`：忽略不符合的依赖，注意这很危险，但是也很必要
2. `--force`：覆盖已有的文件，这是因为很多 CentOS 7 的包在 CentOS 8 改了名字，所以即使 `rpm -U` 也会出冲突，此时可以覆盖

**重要：备好一份静态的 busybox，多开一个 ssh session 并且在 root 用户下。这可以保证出事的时候，可以用 busybox 抢救一下。busybox 自带了 wget 和 rpm 实现，非常重要！**

此时虽然可以跑 `dnf`，不会出现前面提到的 `Invalid version flag If` 的问题，但是 `dnf` 对升级也无能为力：各种依赖冲突。所以接下来就是手动 `rpm` 的环节

### 安装 rpm 包

接下来要做的是，逐渐替换系统中的包，升级到新系统中。首先比较需要升级的几个东西：

1. rpm
2. dnf
3. glibc
4. platform-python
5. bash

怎么升级呢，还是在 TUNA 镜像上查：

1. BaseOS: <https://mirrors.tuna.tsinghua.edu.cn/centos-vault/8.5.2111/BaseOS/aarch64/os/Packages/>
2. AppStream: <https://mirrors.tuna.tsinghua.edu.cn/centos-vault/8.5.2111/AppStream/aarch64/os/Packages/>

大部分包都会在这两个路径里，下载下来然后 `rpm -U`，发现冲突，就递归地下载它依赖的其他包。这里要对常见的动态库敏感，大部分包的名字和动态库的名字是匹配的，但是也有例外，比如 libssl，libcrypto 对应 openssl，liblzma 对应 xz 等等。不知道叫什么就在网上搜。

这个过程是漫长而枯燥的，需要不断尝试，直到某一刻，新的 `dnf` 可以安装，`dnf update` 可以工作，让它接管剩下的大部分工作。我列了一下，最后用 wget 手动下载的 rpm 有 92 个。如果你比较幸运，可能不需要这么多。

### rescue

当然了，实际过程并没有这么简单，因为在升级 systemd 的时候，系统卡住了，还好有 BMC，但是在 BMC 上重启以后，进入到 switching root 阶段的时候也卡住了，看不到输出。

这时候只好用 LiveCD 大法了。还好网络里配置了 PXE，这里推荐一个 iPXE 配置：<https://github.com/shankerwangmiao/tuna-ipxe>，可以用它方便地启动 Ubuntu/Debian/Arch Linux。我就直接起了一个 Debian Installer，然后切换到新的 TTY，就可以拿到 Shell 了。然后就是熟悉的 mount，手动 [arch-chroot](https://wiki.archlinux.org/title/chroot#Using_chroot)，然后重复之前的 rpm 安装的过程。由于在 BMC 的 Remote Console 里输入比较麻烦，可以开一个临时的 sshd，然后 ssh 上去。重启前，检查 grub 是否安装好，UEFI 启动项是否正确，都没问题以后，就可以重启进入 CentOS 8 了。

另外，在替换一些重要的库的时候，也发生了问题，比如 rpm 找不到动态库，这时候要么用 busybox 的 rpm，要么就在别的机器手动解压 CentOS 7 的 rpm，把里面的动态库 scp 上去（所以要保证 openssh server 还在），复制到对应目录下。

### stream

升级到 CentOS 8 以后，用 `rpm -qa` 会发现还有很多包遗留在 el7，这是因为版本号上，可能 el7 比 el8 还要高。所以我干脆把系统升级到了 CentOS 8 Stream 上，这次不用这么折腾，直接换 CentOS 8 Stream 的源（`centos-stream-repos` 和 `centos-stream-release`），然后 `dnf update` 即可。剩下的少量 el7 包手动升降级即可。
