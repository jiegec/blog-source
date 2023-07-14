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

接下来，我们为了使用学校的 SLAAC，采用 ebtables 直接把学校的 IPv6 bridge 进来，而 IPv4 由于准入系统，需要 NAT。

参考 [Bridge IPv6 connections to WAN](https://tmikey.tech/tech_daily/lede/2017/08/25/bridge_ipv6_lede.html)，下载 [v6brouter_openwrt.sh](https://github.com/cvmiller/v6brouter/blob/master/v6brouter_openwrt.sh) 到某个地方，然后修改一下里面的一些参数：

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
$ ssh root@192.168.1.1
$ opkg install ca-certificates
$ ./GoAuthing
```

这里参考了[解决 GO 语言编译程序在 openwrt(mipsle 架构) 上运行提示 Illegal instruction 问题](https://blog.csdn.net/QQ531456898/article/details/80095707)，配置了 GOMIPS 环境变量。为了访问 HTTPS 网站，参考了[OpenWRT Wiki - SSL and Certificates in wget](https://wiki.openwrt.org/doc/howto/wget-ssl-certs)。有毒的是，这个环境变量，在 macOS 上不能正常工作，而在 Linux 机子上是没有问题的。

然后就可以成功地跑起来 GoAuthing，解决了上校园网认证的问题。

感谢[宇翔](https://github.com/z4yx)编写的 GoAuthing 小工具。

更新：简化了一下 v6brouter 脚本：

```bash
#!/bin/sh
BRIDGE=br-lan
WAN_DEV=$(/sbin/uci get network.wan.ifname)
WHITELIST1="00:11:22:33:44:55"
WHITELIST2="55:44:33:22:11:00"

brctl addbr $BRIDGE 2> /dev/null
brctl addif $BRIDGE $WAN_DEV
ip link set $BRIDGE down
ip link set $BRIDGE up
brctl show

ebtables -F
ebtables -P FORWARD ACCEPT
ebtables -L

uci set dhcp.lan.ra='disabled'
uci set dhcp.lan.dhcpv6='disabled'
uci commit
/etc/init.d/odhcpd restart

echo 2 > /proc/sys/net/ipv6/conf/$BRIDGE/accept_ra
ebtables -t broute -F
ebtables -t broute -A BROUTING -i $WAN_DEV -p ! ipv6 -j DROP
ebtables -t broute -A BROUTING -s $WHITELIST1 -p ipv6 -j ACCEPT
ebtables -t broute -A BROUTING -d $WHITELIST1 -p ipv6 -j ACCEPT
ebtables -t broute -A BROUTING -s $WHITELIST2 -p ipv6 -j ACCEPT
ebtables -t broute -A BROUTING -d $WHITELIST2 -p ipv6 -j ACCEPT
ebtables -t broute -A BROUTING -p ipv6 -j DROP
ebtables -t broute -L
```

注意，这里添加了两个 WHITELIST 的 MAC 地址，表示只让这两个 MAC 地址的设备访问 v6。一般来说，外面网关的 MAC 地址也要放进来，不然可能接收不到 RA。如果不需要白名单的话，可以去掉 ebtables 的后几行规则。