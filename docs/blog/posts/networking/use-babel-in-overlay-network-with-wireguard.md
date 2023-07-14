---
layout: post
date: 2018-08-10 09:17:00 +0800
tags: [wireguard,babel,routing,go]
category: networking
title: 在 WireGuard 构建的 Overlay Network 上跑 babel 路由协议
---


受 [Run Babeld over Wireguard - Fugoes's Blog](https://blog.fugoes.xyz/2018/02/03/Run-Babeld-over-Wireguard.html) 和 [Route-based VPN on Linux with WireGuard](https://vincent.bernat.im/en/blog/2018-route-based-vpn-wireguard) 启发，自己也想尝试一下，在一个有多个结点的网络中，如何通过 WireGuard 构建一个 overlay network，并通过 babel 自动进行结点发现和路径选择。

首先建立点对点的 WireGuard Tunnel。由于我们用 babel 进行路由，所以我们不能采用 Wiregurad 本身基于目的地址的端口复用，所以每一个 WireGuard interface 都只有一个 Peer。

配置一个点对点的 WireGuard Tunnel：

```
$ # for wg-quick
$ cat wg0.conf
[Interface]
Address = IPV4/32, fe80::ID/64
PrivateKey = REDACTED
ListenPort = PORT1
Table = off # ask wg-quick not to insert peer address into routing table

[Peer]
PublicKey = REDACTED
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = REDACTED:PORT2
```

这里的 IPV4 和 ID 在同一设备上的不同 WireGuard Tunnel 上相同。只是通过 wg interface 编号来区分。

接着配置 babeld：

```
$ cat babeld.conf

router-id ID
local-port 33123 # for babelweb2

# one line for each wg interface
interface wg0 type tunnel rtt-max 512

redistribute ip PREFIX/LEN ge LEN le 32 local allow # tunnel neighbors
redistribute proto 42 # routes installed by babeld
redistribute local deny
# consult babeld man page for more
```

然后通过 BabelWeb2（很难用）进行可视化，然后通过手动触发一些网络波动即可达到效果。
