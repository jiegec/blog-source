---
layout: post
date: 2018-05-09 10:02:00 +0800
tags: [linux,macos,tinc]
category: networking
title: 在 macOS 和 Linux 之间搭建 tinc 网络
---

一直听说 tinc 比较科学，所以尝试自己用 tinc 搭建一个网络。这里，macOS 这段没有固定 IP 地址，Linux 机器有固定 IP 地址 linux_ip 。假设网络名称为 example , macOS 端名为 macos 地址为 192.168.0.2, linux 端名为 linux 地址为 192.168.0.1。

在 macOS 上配置：
```shell
brew install tinc
mkdir -p /usr/local/etc/tinc/example
```

新建 /usr/local/etc/tinc/example/tinc.conf:
```
Name = macos
Device = utun0 # use an unused number
ConnectTo = linux
```

编辑 /usr/local/etc/tinc/example/tinc-up:
```
#!/bin/sh
ifconfig $INTERFACE 192.168.0.2 192.168.0.1 mtu 1500 netmask 255.255.255.255
route add -net 192.168.0.2 192.168.0.1 255.255.255.0
```

和 /usr/local/etc/tinc/example/tinc-down:
```
#!/bin/sh
ifconfig $INTERFACE down
```

然后将它们都设为可执行的：
```
chmod +x tinc-up
chmod +x tinc-down
```

编辑 /usr/local/etc/tinc/example/macos:
```
Port = 655
Subnet = 192.168.0.2/32
```

执行 `tincd -n example -K` 生成密钥。

到 Linux 机器上：
编辑以下文件：
```shell
$ mkdir -p /etc/tinc/example/hosts
$ cat /etc/tinc/example/tinc.conf
Name = linux
$ cat /etc/tinc/example/tinc-up
$!/bin/sh
ip link set $INTERFACE up
ip addr add 192.168.0.1/24 dev $INTERFACE
$ cat /etc/tinc/example/tinc-down
$!/bin/sh
ip addr del 192.168.0.1/24 dev $INTERFACE
ip link set $INTERFACE down
$ cat /etc/tinc/example/hosts/linux
Address = linux_ip
Port = 655
Subnet = 192.168.0.1/32
$ tincd -n example -K
```

接着，把 linux 上 /etc/tinc/example/hosts/linux 拷贝到 macos 的 /usr/local/etc/tinc/example/hosts/linux ，然后把 macos 上 /usr/local/etc/tinc/example/hosts/macos 拷贝到 /etc/tinc/example/hosts/macos 。在两台机器上都 `tinc -n example -D -d3` 即可看到连接的建立，通过 ping 即可验证网络建立成功。
