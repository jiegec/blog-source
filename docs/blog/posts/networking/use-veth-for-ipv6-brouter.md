---
layout: post
date: 2018-10-07
tags: [brouter,ebtables,ipv6]
category: networking
title: 使用 veth 实现 IPv6-only 的 Brouter 功能
---

最近从 @shankerwangmiao 学到了一个方法：通过 veth 把两个 bridge 的 IPv6 桥接起来。方法如下：


```
$ ip link add veth-v6-in type veth peer name veth-v6-out
$ brctl addif br-in veth-v6-in
$ brctl addif br-out veth-v6-out
$ ebtables -t filter -A FORWARD -p ! IPv6 -o veth-v6-in -j DROP
$ ebtables -t filter -A FORWARD -p ! IPv6 -o veth-v6-out -j DROP
```

这样就可以看到 veth 上仅有 IPv6 的流量了。