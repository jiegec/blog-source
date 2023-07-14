---
layout: post
date: 2018-05-05 20:25:00 +0800
tags: [nat,mosh,upnp,miniupnpd]
category: networking
title: 利用 UPnP 协议进行 mosh NAT 穿透的研究
---

由于经常要从宿舍、教室等不同的 Wi-Fi 之间切换，但是 ssh 连接又总是断，所以想用 mosh 代替 ssh。但是 mosh 也有它的问题：

1. 不能滚动。这个可以在 mosh 中嵌套一层 tmux 解决。我目前写了一些自动 mosh 后打开 tmux 并且开启鼠标支持的脚本，但还是有缺陷。
2. 在高端口 60000+ 监听 UDP，这使得 NAT 后的服务器难以直接通过端口转发。如果直接转发到 NAT 后的机器，那么 NAT 后面如果有多台机器，这又失效了。

于是找了找网上的 NAT 穿透的一些文章，看到了 UPnP 的方法。大致就是，用户可以向路由器注册一个临时的转发规则，路由会自动在 iptables 上配置转发。但是，这样也会遇到一个问题：路由上的 mosh-server 不知道这个转发的存在，所以它可能会尝试监听同样的端口。解决方案下面会提到。

需求：

```
Server <---> NAT Router <---> My Laptop
On NAT Router, port 8022 is forwarded to Server:22
1. mosh router # works
2. mosh --ssh="ssh -p 8022" router # works
```

首先在 NAT Router 上配置 miniupnpd（以 Debian 为例）

```shell
sudo apt install miniupnpd
# you will get a dialog upon installation
# input your wan interface and listening ip accordingly
sudo vim /etc/default/miniupnpd
# edit START_DAEMON=0 to START_DAEMON=1
sudo vim /etc/miniupnpd/miniupnpd.conf
# edit ext_ifname, listening_ip accordingly
# set secure_mode=yes
# add 'allow 60000-60023 internal_ip/prefix 60000-60023'
# before the last line 'deny 0-65535 0.0.0.0/0 0-65535'
sudo systemctl enable --now miniupnpd
```

现在，复制 [我修改的 mosh-wrapper.js](https://github.com/jiegec/mosh-upnp-hole-puncher/blob/master/mosh-wrapper.js) 到用户的 home 目录下，在 Server 安装 `miniupnpc` 然后通过：

```shell
mosh --ssh="ssh -p 8022" --server=~/mosh-wrapper.js user@router
```

这样，mosh 首先会通过 ssh 和 Server 协商一个 AES 的密钥和 UDP 端口（如 60001），之后的通信都通过 UDP 端口走加密后的流量。我的 `mosh-wrapper.js` 通过 `miniupnpc` 向路由器请求把该 UDP 端口转发到 Server 上，这样， `mosh-server` 就能通过 NAT 路由穿透到后面的 Server 上。

等会！问题来了：

`mosh` 默认的 IP 范围是 `60000-61000` ，根据我的观察，它会从 60001 开始尝试监听本机地址，如果已经被占用，则 60002, 60003, ... 但是！Router 和 Server 实际上占用了相同的端口空间，并且 `mosh` 只知道本机哪些端口被占用了，而不知道 Router 和 Server 共同占用了多少端口。

我想到了一些可能的解决方案：

1. 在 Router 上让 miniupnpd 监听对应的端口，占住这个坑。这样，Router 上的 `mosh-server` 就不会用和 Server 相同的端口
2. 如果有多个 Server，则会出现抢夺相同端口的情况。我目前的想法是，让 `upnpc` 去询问 Router 找空闲的端口，然后再传给 `mosh-server` 使用。另一种方法则是，给不同的 Server 划分不同的端口范围，比如 Router 用 60001-60005, 然后 Server1 用 60006-60010, Server2 用 60011-60015 如此下去。

然后，新的问题又发现了：

当我在和 Server 同一个子网的时候，由于 `miniupnpd` 配置的 `iptables` 规则中来源只有 WAN interface，所以我在内网发的包是不会被转发的。当然，既然在内网了，为啥不直接用内网 IP 呢，不知道 `mosh` 有没有提供设置备用 IP 的功能。