---
layout: post
date: 2018-06-29
tags: [tun,wireguard,systemd-networkd]
category: networking
title: Wireguard 隧道搭建
---

随着 Wireguard Go 版本的开发，在 macOS 上起 WireGuard Tunnel 成为现实。于是，搭建了一个 macOS 和 Linux 之间的 WireGuard Tunnel。假设 Linux 端为服务端，macOS 端为客户端。

macOS 端：

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

后续尝试在 Android 上跑通 WireGuard。

UPDATE 2018-07-11: 

成功在 Android 上跑通 WireGuard。在 Google Play 上下载官方的 App 即可。麻烦在于，将 Android 上生成的 Public Key 和服务器的 Public Key 进行交换。

然后又看到[WireGuard 在 systemd-networkd](https://wiki.debian.org/Wireguard#Step_2_-_Alternative_C_-_systemd)上的配置方案，自己也实践了一下。首先，如果用的是 stretch，请首先打开 stretch-backports 源并把 systemd 升级到 237 版本。

然后，根据上面这个连接进行配置，由于都是 ini 格式，基本就是复制粘贴就可以配置了。有一点要注意，就是，要保护 PrivateKey 的安全，注意配置 .netdev 文件的权限。
