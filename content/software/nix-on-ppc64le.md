---
layout: post
date: 2022-10-29 18:54:00 +0800
tags: [nix,power,powerpc,ppc64le]
category: software
title: 在 ppc64le Linux 上运行 Nix
---

## 背景

之前尝试过在 ppc64le 的机器上运行 Nix，当时的尝试是把代码克隆下来编译，我还写了一个 Docker 脚本：

```docker
# Based on https://github.com/NixOS/nix/issues/6048
# Build nixos/nix from source
FROM ubuntu:20.04

RUN sed -i 's/ports.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    autoconf-archive autoconf automake pkg-config build-essential git gcc g++ jq libboost-all-dev libcrypto++-dev libcurl4-openssl-dev \
    libssh-dev libarchive-dev libsqlite3-dev libbz2-dev wget liblzma-dev libbrotli-dev libseccomp-dev bison flex libsodium-dev libgc-dev \
    libgtest-dev libgmock-dev cmake unzip

# Install editline - newer version required
WORKDIR /root
RUN wget https://github.com/troglobit/editline/releases/download/1.17.1/editline-1.17.1.tar.xz
RUN tar xf editline-1.17.1.tar.xz
WORKDIR /root/editline-1.17.1
RUN ./configure --prefix=/usr
RUN make all
RUN make install

# Install lowdown - not available via apt
WORKDIR /root
RUN wget https://github.com/kristapsdz/lowdown/archive/refs/tags/VERSION_0_10_0.tar.gz
RUN tar xf VERSION_0_10_0.tar.gz
WORKDIR /root/lowdown-VERSION_0_10_0
RUN ./configure
RUN make all
RUN make install  

# Install nlohmann_json - newer version required
WORKDIR /root
RUN wget https://github.com/nlohmann/json/archive/refs/tags/v3.10.5.tar.gz
RUN tar xf v3.10.5.tar.gz
WORKDIR /root/json-3.10.5
RUN mkdir build
WORKDIR /root/json-3.10.5/build
RUN cmake .. && make -j$(nproc)
RUN make install
WORKDIR /root
RUN wget https://github.com/nlohmann/json/releases/download/v3.10.5/include.zip && unzip include.zip
RUN mv include/nlohmann/* /usr/local/include/nlohmann/

# Compile & build nix
WORKDIR /root
RUN git clone -b 2.8.1 https://github.com/NixOS/nix.git
WORKDIR /root/nix
RUN ./bootstrap.sh
RUN ./configure
RUN make -j$(nproc)
RUN make install -k || true
```

但是发现问题在于，离开了 nix install 脚本，我并不知道如何配置一个 multi-user install。但是官方的 nix install 脚本会报错，因为没有 ppc64le 的 prebuilt tarball。

## 解决办法

因此，我在网上进行搜索，发现 [Getting started with Nix on ppc64le](https://discourse.nixos.org/t/getting-started-with-nix-on-ppc64le/12712/8?u=jiegec) 中有人提到，可以先在 x86 的机器上交叉编译出 ppc64le 的 nix，然后把 nix tarball 中的 x86 nix 替换成 ppc64le 版本，再复制到 ppc64le 上安装，其余的步骤就一样了。

我把脚本更新了一下，适配了最新的 nix 版本，最后得到了如下的脚本：

```shell
#!/bin/sh
# Based on https://discourse.nixos.org/t/getting-started-with-nix-on-ppc64le/12712/8?u=jiegec
nix-build '<nixpkgs>' -A pkgsCross.powernv.nix

# Get a donor copy of the installer
wget -c https://releases.nixos.org/nix/nix-2.11.1/nix-2.11.1-x86_64-linux.tar.xz
tar xf nix-2.11.1-x86_64-linux.tar.xz

# Keep the cert package
mkdir -p nix-ppc64le-linux/store
cp -r nix-2.11.1-x86_64-linux/store/*nss-cacert* nix-ppc64le-linux/store/

# Toss other packages, keep the scripts
rm -rf nix-2.11.1-x86_64-linux/store
mv nix-2.11.1-x86_64-linux/* nix-ppc64le-linux/

# Add ppc64le packages
cp -r $(nix-store -qR result) nix-ppc64le-linux/store/

# Generate a .reginfo for those ppc64le packages
nix-store --dump-db $(nix-store -qR result) > nix-ppc64le-linux/.reginfo

# Replace NIX_INSTALLED_NIX in install script
export NIX_INSTALLED_NIX=$(readlink result)
sed -i "s#NIX_INSTALLED_NIX=\".*\"#NIX_INSTALLED_NIX=\"$NIX_INSTALLED_NIX\"#" nix-ppc64le-linux/install-multi-user

echo "Done! Copy nix-ppc64le-linux to ppc64le machine and run ./install --daemon"
```

把生成的目录复制到 ppc64le 机器上就可以了。

## 编译问题

当然了，既然 ppc64le 的 Nixpkgs 没有什么人测试，所以肯定会遇到一些问题。下面是遇到的几个比较主要的问题，以及相应的解决方法：

- boehm-gc checkPhase 会失败，见 [ivmai/bdwgc#376](https://github.com/ivmai/bdwgc/issues/376)，一直没有修复。解决办法是添加 overlay，让它不要跑测试：

```
custom-overlay = final: prev: {
  # https://github.com/ivmai/bdwgc/issues/376
  boehmgc = prev.boehmgc.overrideAttrs (_: { doCheck = false; });
};
```

- linux-headers 编译失败，报告 unknown type name __vector128，见 [tools/bpf: Compilation issue on powerpc: unknown type name '__vector128'
](https://www.spinics.net/lists/netdev/msg694314.html)。目前的解决办法是让 procps/tmux 等包不要依赖 systemd，进而不会依赖 linux-headers：

```
custom-overlay = final: prev: {
  # systemd cannot build due to linux-headers
  procps = prev.procps.override { withSystemd = false; };
  tmux = prev.tmux.override { withSystemd = false; };
};
```

对于 home-manager，可以用下面的配置让它不要编译 systemd：

```
# systemd does not build
systemd.user.systemctlPath = "/bin/systemctl";
```

当然了，这个治标不治本，还是要等上游修复。