---
layout: post
date: 2023-01-21
tags: [freebsd,cookbook]
categories:
    - system
---

# FreeBSD/NetBSD/OpenBSD/DragonFlyBSD Cookbook

## 背景

最近在维护 lsof 的时候，需要在 FreeBSD/NetBSD/OpenBSD/DragonFlyBSD 上进行开发和测试，于是就装了虚拟机，特此记录我在使用过程中，与 Linux 不一样的一些常用 FreeBSD/NetBSD/OpenBSD/DragonFlyBSD 命令。

<!-- more -->

## FreeBSD

文档参考：<https://docs.freebsd.org/en/books/handbook>

### 安装

在 <https://www.freebsd.org/where/> 找到最新版下载，对于虚拟机的需求，用 `-disk1.iso`，1 GB 左右。安装过程按照 UI 一步步走即可。

### root 权限

FreeBSD 的 su 默认只有 wheel 组可以 su 到 root，所以安装的时候，建议给创建的帐号加上 wheel 组。也可以通过 pw 命令：

```shell
pw groupmod wheel -m freebsd
```

sudo 需要通过包管理器安装，用法和 Linux 一样。

### 包管理

使用 `pkg` 命令进行包管理：

```shell
pkg update
pkg install -U sudo vim fish
```

`-U` 表示在 install 的时候不要再 update。

也可以从 Ports 源码编译，如：

```shell
git clone https://git.FreeBSD.org/ports.git /usr/ports
cd /usr/ports/sysutils/lsof
make install
```

### 升级

使用 `freebsd-update` 命令升级：

```shell
freebsd-update fetch
freebsd-update install
```

### 网络配置

显示路由表：

```shell
netstat -nr
```

修改路由：

```shell
# ip route add 1.2.3.0/24 via 4.5.6.7
route add -net 1.2.3.0/24 4.5.6.7
# ip route del 1.2.3.0/24
route delete -net 1.2.3.0/24
```

网络接口：

```shell
# ip a
ifconfig
# ip link set dev abc up
ifconfig abc up
# ip a add 1.2.3.4/24 dev abc
iconfig abc inet 1.2.3.4/24
```

网路配置在 `/etc/rc.conf`：

```
# DHCP
ifconfig_xxx="DHCP"
# Default Gateway
defaultrouter="1.2.3.4"
# Static IP
ifconfig_xxx="inet 1.2.3.4/24"
# Static route
static_routes="name1 name2"
route_name1="-net 1.2.3.0/24 4.5.6.7"
route_name2="-net 3.2.1.0/24 7.6.5.4"
# Bridge
cloned_interfaces="bridge0"
ifconfig_bridge0="addm net0 addm net1 up"
ifconfig_net0="up"
ifconfig_net1="up"
```

### 换源

USTC <https://mirrors.ustc.edu.cn/help/freebsd-pkg.html>:

```shell
mkdir -p /usr/local/etc/pkg/repos/
echo 'FreeBSD: { url: "pkg+http://mirrors.ustc.edu.cn/freebsd-pkg/${ABI}/quarterly" }' \
        > /usr/local/etc/pkg/repos/FreeBSD.conf
pkg update
```

### truss

truss 相当于 Linux 中的 strace。

### 编译内核

文档：<https://docs.freebsd.org/en/books/handbook/kernelconfig/>

首先下载内核源码，然后创建内核配置：

```shell
cd /path/to/kernel/src
cd sys/amd64/conf
cp GENERIC MYKERNEL
```

编译和安装：

```shell
make buildkernel KERNCONF=MYKERNEL
make installkernel KERNCONF=MYKERNEL
```

提交 patch：<https://wiki.freebsd.org/Phabricator>

### 关机

FreeBSD 的 shutdown 默认会停留在 halt 的状态，但是不会断电，需要添加 `-p` 选项。

## NetBSD

### 包管理

参考：<https://www.netbsd.org/docs/pkgsrc/using.html>

使用 pkgin 做二进制包的包管理，首先安装 pkgin：

```shell
PATH="/usr/pkg/sbin:/usr/pkg/bin:$PATH"
PKG_PATH="https://cdn.NetBSD.org/pub/pkgsrc/packages"
PKG_PATH="$PKG_PATH/NetBSD/amd64/9.3/All/"
export PATH PKG_PATH
pkg_add pkgin
```

包管理：

```shell
pkgin install sudo vim fish
pkgin upgrade
```

和 FreeBSD 一样，NetBSD 的 su 默认只有 wheel 组可以 su 到 root，建议在安装创建新用户的时候就把自己的帐号加入到 wheel 组中。sudo 使用之前需要 visudo 修改配置。

也可以从源码 pkgsrc 进行编译，在 /usr/pkgsrc 路径下，编译好的程序会安装到 /usr/pkg/bin。

克隆并初始化 pkgsrc：

```shell
cd /usr && cvs -q -z2 -d anoncvs@anoncvs.NetBSD.org:/cvsroot checkout -P pkgsrc
cd /usr/pkgsrc/bootstrap
./bootstrap
```

编译 pkgsrc 中的软件：

```shell
cd /usr/pkgsrc/sysutils/lsof
make
```

### 网络配置

网络配置的命令和 FreeBSD 基本一样：

- `netstat -nr`：查看路由表
- `route`：修改路由表
- `ifconfig`：配置网络接口

但是 `/etc/rc.conf` 的配置语法不同，见 `man rc.conf` 和 <https://www.netbsd.org/docs/network/#configuration_files>。

### 升级

参考 <https://www.netbsd.org/docs/guide/en/chap-upgrading.html>

使用 sysupgrade 命令升级：

```
pkgin install sysupgrade
sysupgrade auto https://cdn.NetBSD.org/pub/NetBSD/NetBSD-9.3/amd64
```

### 安装内核源码

内核源码可以从 <https://mirrors.tuna.tsinghua.edu.cn/NetBSD/NetBSD-9.3/source/sets/> 下载。对于 lsof 只需要其中的 syssrc.tgz。

解压：

```shell
tar -xzf syssrc.tgz -C /
```

## OpenBSD

### 安装

文档：<https://www.openbsd.org/faq/faq4.html>

下载 <https://mirrors.tuna.tsinghua.edu.cn/OpenBSD/7.2/amd64/install72.iso>，然后按照 UI 提示进行安装。使用 virt-manager 安装 OpenBSD 虚拟机的时候，在安装界面会遇到无法输入的问题，可以创建一个 USB Keyboard 来解决。

### 包管理

文档：<https://www.openbsdhandbook.com/package_management/>

常用命令：

```shell
# Use TUNA Mirrors
echo "https://mirrors.tuna.tsinghua.edu.cn/OpenBSD/" > /etc/installurl
# Search
pkg_info -Q fish
# Install
pkg_add sudo fish vim
# Update packages
pkg_add -u
```

另一个方法是从源码编译，首先下载 ports：

```shell
wget https://mirrors.tuna.tsinghua.edu.cn/OpenBSD/7.2/ports.tar.gz
cd /usr/src
tar xzf /path/to/ports.tar.gz
```

### 系统升级

参考：<https://www.openbsdhandbook.com/system_management/updates/>

```shell
syspatch -c
syspatch
```

### autotools

OpenBSD 允许存在多个版本的 autoconf/automake，所以在运行的时候需要用环境变量指定版本，如：

```shell
export AUTOCONF_VERSION=2.71
export AUTOMAKE_VERSION=1.16
```

### 获取内核源码

文档：<https://www.openbsd.org/faq/faq5.html>

命令：

```shell
# Add exampleuser to group wsrc
user mod -G wsrc exampleuser
# Download and extract
wget https://mirrors.tuna.tsinghua.edu.cn/OpenBSD/7.2/sys.tar.gz
cd /usr/src
tar xzf /path/to/sys.tar.gz
```

### ktrace

ktrace 相当于 Linux 中的 strace。结果会保存在文件中，用 kdump 命令显示。

## DragonFlyBSD

### 安装

下载 ISO 文件：<https://mirror-master.dragonflybsd.org/iso-images/dfly-x86_64-6.4.0_REL.iso>

用 installer 用户登录开始安装。

### 用户管理

和 FreeBSD 一样，su 需要 wheel 组，所以需要手动添加用户到 wheel 组中：

```shell
pw groupmod wheel -m username
```

### SSHD

DragonFlyBSD 默认 sshd 配置不允许密码登录，如果要允许，需要修改 `/etc/ssh/sshd_config`，然后重启 ssh：

```shell
/etc/rc.d/sshd restart
```

### 包管理

DragonFlyBSD 可以下载二进制包：

```shell
pkg update
pkg upgrade
pkg install sudo vim fish
```

也可以从源码编译，见 <https://www.dragonflybsd.org/docs/howtos/HowToDPorts/>