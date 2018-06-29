---
layout: post
date: 2018-06-29 10:59:00 +0800
tags: [tun,wireguard]
category: networking
title: Wireguard 隧道搭建
---

随着 Wireguard Go 版本的开发，在 macOS 上起 WireGuard Tunnel 成为现实。于是，搭建了一个 macOS 和 Linux 之间的 WireGuard Tunnel。假设 Linux 端为服务端， macOS 端为客户端。

macOS端：

```shell
$ brew install wireguard-tools
$ cd /usr/local/etc/wireguard
$ wg genkey > privatekey
$ wg pubkey < privatekey > publickey
$ vim tunnel.conf
[Interface]
PrivateKey = MACOS_PRIVATE_KEY

[Peer]
PublicKey = LINUX_PUBLIC_KEY # Generated below
AllowedIPs = 192.168.0.0/24
Endpoint = LINUX_PUBLIC_IP:12345
$ vim up.sh
#!/bin/bash
# change interface name when necessary
sudo wireguard-go utun0
sudo wg setconf utun0 tunnel.conf
sudo ifconfig utun0 192.168.0.2 192.168.0.1
$ chmod +x up.sh
$ ./up.sh
```

配置 Linux 端：
```shell
$ git clone https://git.zx2c4.com/WireGuard
$ make
$ sudo make install
$ sudo fish
$ cd /etc/wireguard
$ wg genkey > privatekey
$ wg pubkey < privatekey > publickey
$ vim wg0.conf
[Interface]
Address = 192.168.0.1/24
PrivateKey = LINUX_PRIVATE_KEY
ListenPort = 12345

[Peer]
PublicKey = MACOS_PUBLIC_KEY
AllowedIPs = 192.168.0.2/24
$ wg-quick up wg0
```

经过测试，两边可以互相 ping 通。

后续尝试在 Android 上跑通 WireGuard 。
