---
layout: post
date: 2018-05-06 14:07:00 +0800
tags: [linux,nat,forwarding]
category: networking
title: 使用 iptables 和策略路由进行带源地址的 forwarding
---

陈老师打开他的服务器，突然发现 CPU 莫名高负载，然后发现是有一个用户被远程登录拿来挖矿了。但是这台机器在 NAT 后，所以登录的源地址全是 NAT 路由，所以不知道对方的地址是什么。我们为了能使用 fail2ban 来禁用多次尝试失败的 IP ，但又不想因为别人把 NAT 路由的地址给禁了，这样我们自己也用不了了。所以必须要让这台机器能够知道 ssh 的源地址，我们现在简单的 socat 方案不能满足这个需求。

需求：

1. 可以在外网连 NAT 路由的高端口（如2222）来访问这台机器。
2. 在内网中，既可以直接连它的内网地址，也可以连 NAT 路由的高端口来访问这台服务器。此时，由于连 ssh 的机器就在同一个子网中，如果保留了源地址，服务器发的包会直接回来不经过 NAT 。所以我们还是保留了 socat 的方案。

实现方法：

在 NAT Router 上配置 DNAT ，这样发到 NAT Router 上的包就可以转发到服务器上：

```shell
iptables -t nat -A PREROUTING -i external_interface -p tcp -m tcp --dport 2222 -j DNAT --to-destination internal_server_ip:22
```

但是，从服务器回来的包到了 NAT Router 上后，由于路由表的配置问题，默认的路由并不能把包送达对方。所以，我们首先给包打上 mark：

```shell
iptables -t mangle -A PREROUTING -i internal_interface -p tcp -m tcp --sport 22 -j MARK --set-mark 0x2222
```

然后配置策略路由：

```shell
ip rule add fwmark 0x2222 table 2222
ip route add table 2222 default via gateway_address
```

这样就可以保证 ssh 的回包可以原路返回了。

由于前面提到的原因，上面我们配置的 DNAT 规则只对外网过来的包有效。为了内网的访问，我们仍然采用了 socat 的方式：

```shell
socat TCP-LISTEN:2222,reuseaddr,fork TCP:internal_server_ip:22
```

从不同的机器测试，都可以在 `who` 看到，地址确实是我们想看到的源地址。接下来配置 `fail2ban `即可。