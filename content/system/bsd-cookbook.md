---
layout: post
date: 2023-01-21 20:18:00 +0800
tags: [freebsd,cookbook]
category: system
title: FreeBSD/NetBSD Cookbook
---

## 背景

最近在维护 lsof 的时候，需要在 FreeBSD/NetBSD 上进行开发和测试，于是就装了虚拟机，特此记录我在使用过程中，与 Linux 不一样的一些 FreeBSD/NetBSD 命令。

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

USTC <https://mirrors.ustc.edu.cn/help/freebsd-pkg.html>：

```shell
mkdir -p /usr/local/etc/pkg/repos/
echo 'FreeBSD: { url: "pkg+http://mirrors.ustc.edu.cn/freebsd-pkg/${ABI}/quarterly" }' \
        > /usr/local/etc/pkg/repos/FreeBSD.conf
pkg update
```

### truss

truss 相当于 Linux 中的 strace。

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

也可以从源码 pkgsrc 进行编译，在 /usr/pkg 路径下。