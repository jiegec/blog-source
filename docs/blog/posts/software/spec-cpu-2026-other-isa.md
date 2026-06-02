---
layout: post
date: 2026-05-21
tags: [benchmark,spec,speccpu2026]
categories:
    - software
---

# SPEC CPU 2026 在其他指令集上的编译

SPEC CPU 2026 官方只附带了 aarch64/ppc64le/riscv64/x86_64 指令集的预编译 tools，如果要在其他指令集上使用，就需要首先编译 tools，过程如下：

```shell
cd /mnt && tar xvf install_archives/tools-src.tar
wget -O config.guess 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD'
wget -O config.sub 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD'
cp config.* /mnt/tools/src/make-4.2.1/config/
# build tools
mkdir -p /mnt/config
cd /mnt && echo 'y' | SKIPTOOLSINTRO=1 FORCE_UNSAFE_CONFIGURE=1 MAKEFLAGS=-j16 ./tools/src/buildtools
mkdir -p /mnt/config
cd /mnt && . ./shrc && packagetools linux-loong64
```

例如下面是在 LoongArch 上编译 SPEC CPU 2026 的 Dockerfile，假设 SPEC CPU 2026 已经解压到 `/mnt`：

```dockerfile
RUN cd /mnt && tar xvf install_archives/tools-src.tar
RUN wget -O config.guess 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD'
RUN wget -O config.sub 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD'
RUN cp config.* /mnt/tools/src/make-4.2.1/config/
# build tools
RUN mkdir -p /mnt/config
RUN cd /mnt && echo 'y' | SKIPTOOLSINTRO=1 FORCE_UNSAFE_CONFIGURE=1 MAKEFLAGS=-j16 ./tools/src/buildtools
RUN mkdir -p /mnt/config
RUN cd /mnt && . ./shrc && packagetools linux-loong64
RUN /mnt/install.sh -f
```

参考官方文档：[Building the SPEC CPU®2026 Toolset](https://www.spec.org/cpu2026/Docs/tools-build.html)。
