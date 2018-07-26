---
layout: post
date: 2018-07-26 20:48:00 +0800
tags: [lenovo,newifi,uboot,lede,openwrt,go,ebtables,bridge,ipv6,goauthing,z4yx]
category: networking 
title: 向 Lenovo y1s 刷入 OpenWRT 17.01.5 固件，并把 IPv6 bridge 到内网中和配置认证脚本
---

首先参照[OpenWRT Wiki - Lenovo Y1 v1](https://wiki.openwrt.org/toh/lenovo/lenovo_y1_v1)找到刷固件教程：

1. 下载[Lenovo y1s 的固件](https://mirrors.tuna.tsinghua.edu.cn/lede/releases/17.01.5/targets/ramips/mt7620/lede-17.01.5-ramips-mt7620-y1s-squashfs-sysupgrade.bin)备用
2. 断开电源，等待一段时间，插入电源同时快速按下重置按钮，如果面板双闪，则说明进入了恢复模式
3. 电脑连接到四个 LAN 口中任意一个，配置静态地址在 192.168.1.0/24 网段
4. 打开 192.168.1.1 可以看到刷固件的页面
5. 上传固件，等待路由器重启
6. 配置 IP 地址为 DHCP 模式，打开 192.168.1.1 进行配置

然后就是常规的密码设置，opkg 源设置为 tuna 的源，配置 ssh 和 公钥。

接下来，我们为了使用学校的 SLAAC ，采用 ebtables 直接把学校的 IPv6 bridge 进来，而 IPv4 由于准入系统，需要 NAT 。

参考[Bridge IPv6 connections to WAN](https://tmikey.tech/tech_daily/lede/2017/08/25/bridge_ipv6_lede.html)，下载[v6brouter_openwrt.sh](https://github.com/cvmiller/v6brouter/blob/master/v6brouter_openwrt.sh)到某个地方，然后修改一下里面的一些参数：

```shell
# For Lenovo y1s
WAN_DEV=eth0.2
BRIDGE=br-lan
# the rest remain unchanged
```

然后跑起来之后，自己的电脑可以成功拿到原生的 IPv6 地址了，不需要用难用的 NAT66 技术。

下一步是采用[z4yx/GoAuthing](https://github.com/z4yx/GoAuthing)。

```shell
$ go get -u -v github.com/z4yx/GoAuthing
$ cd $GOPATH/src/github.com/z4yx/GoAuthing/cli
$ env GOOS=linux GOARCH=mipsle GOMIPS=softfloat go build main.go
$ mipsel-linux-gnu-strip main
$ scp main root@192.168.1.1:~/GoAuthing
```

这里参考了[解决GO语言编译程序在openwrt(mipsle架构)上运行提示Illegal instruction问题](https://blog.csdn.net/QQ531456898/article/details/80095707)，配置了 GOMIPS 环境变量。有毒的是，这个环境变量，在 macOS 上不能正常工作，而在 Linux 机子上是没有问题的。

然后就可以成功地跑起来 GoAuthing ，解决了上校园网认证的问题。

感谢[宇翔](https://github.com/z4yx)编写的 GoAuthing 小工具。
