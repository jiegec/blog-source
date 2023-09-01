---
layout: post
date: 2023-08-11
tags: [bmc,openbmc,qemu]
categories:
    - system
---

# 在 QEMU 中运行 OpenBMC 

## 背景

最近想给某台机器配一个 BMC，于是调研 OpenBMC 发行版，但是还没有找到可以买到的合适的 BMC，因此先在虚拟机中进行尝试。

<!-- more -->

## 过程

运行过程参考官方的 [OpenBMC Development Environment](https://github.com/openbmc/docs/blob/master/development/dev-environment.md) 文档进行，首先安装依赖和克隆仓库：

```shell
sudo apt install git python3-distutils gcc g++ make file wget \
    gawk diffstat bzip2 cpio chrpath zstd lz4 bzip2
git clone git@github.com:openbmc/openbmc.git
cd openbmc
```

### romulus

接着，编译针对 romulus BMC 的系统镜像：

```shell
. setup romulus
bitbake obmc-phosphor-image
```

等待一段时间，就可以得到编译好的 32MB 的系统镜像：

```shell
ls -al tmp/deploy/images/romulus/obmc-phosphor-image-romulus.static.mtd
```

整个构建完用了 27 GB 的磁盘空间。

接着，不需要按照文档里的方法去用 qemu fork，而是直接可以用系统自带的上游版 qemu 启动虚拟机：

```shell
qemu-system-arm -m 256 -M romulus-bmc -nographic -drive file=./obmc-phosphor-image-romulus.static.mtd,format=raw,if=mtd -net nic -net user,hostfwd=:127.0.0.1:2222-:22,hostfwd=:127.0.0.1:2443-:443,hostfwd=udp:127.0.0.1:2623-:623,hostname=qemu
```

这样就把 SSH，HTTPS 和 IPMI 转发到本机上了，可以访问，默认用户是 root，默认密码是 0penBmc。

```shell
ssh root@localhost -p 2222
ipmitool -I lanplus -H 127.0.0.1 -U root -P 0penBmc -p 2623 mc info
```

这也是用 OpenBMC 的一大好处：有真正的 SSH 可以用，可以看到内部的情况。通过 uname 可以看到，模拟的处理器架构是 armv6l，还是比较旧的。根据 [QEMU 文档](https://www.qemu.org/docs/master/system/arm/aspeed.html)，romulus 是基于 AST2500 的 OpenPOWER Romulus POWER9 BMC。AST2500 采用的是 800MHz ARM11 核心，确实是比较老了。

### AST2600

接下来试试基于 Cortex-A7 的 AST2600，构建 evb-ast2600 target：

```shell
cd openbmc
. setup evb-ast2600
bitbake obmc-phosphor-image
```

这次也编译出了一个 64MB 的系统镜像：

```shell
ls -al tmp/deploy/images/evb-ast2600/obmc-phosphor-image-evb-ast2600.static.mtd
```

在 qemu 中运行：

```shell
qemu-system-arm -m 1024 -M ast2600-evb -nographic -drive file=./obmc-phosphor-image-evb-ast2600.static.mtd,format=raw,if=mtd -net nic -net user,hostfwd=:127.0.0.1:2222-:22,hostfwd=:127.0.0.1:2443-:443,hostfwd=udp:127.0.0.1:2623-:623,hostname=qemu
```

和之前一样，可以通过 SSH，HTTPS 和 IPMI 访问，但是没有 WebUI，只有 redfish。进系统以后可以看到 uname 的架构变成了 armv7l。

此时按照 [【OpenBMC 系列】4.启动流程 使用 qume 模拟 ast2600-evb](https://blog.csdn.net/Datapad/article/details/125929179) 的文档，给 ast2600-evb target 加上 webui：

进入 openbmc 目录，编辑 `build/evb-ast2600/conf/local.conf`，添加一行：

```
CORE_IMAGE_EXTRA_INSTALL  += "webui-vue"
```

编辑 `meta-phosphor/recipes-phosphor/images/obmc-phosphor-image.bbapend`，添加一行：

```
OBMC_IMAGE_EXTRA_INSTALL_${MACHINE} += "webui-vue"
```

注：CSDN 文章里路径打错了，image 应该为 images。

编辑 `meta-phosphor/recipes-phosphor/packagegroups/packagegroup-obmc-apps.bbappend`，添加一行：

```
RDEPENDS_${PN}-inventory_${MACHINE} += "webui-vue"
```

注：romulus 可以工作是因为在 `meta-ibm/meta-romulus/recipes-phosphor/packagegroups/packagegroup-obmc-apps.bbappend` 里面有 `RDEPENDS:${PN}-extras:append:romulus = " webui-vue phosphor-image-signing"`。

重新构建系统镜像：

```shell
cd openbmc
. setup evb-ast2600
bitbake obmc-phosphor-image -c clean
bitbake obmc-phosphor-image
```

此时就会把 webui-vue 也构建进去，再次启动 QEMU 的时候就有 WebUI 了。
