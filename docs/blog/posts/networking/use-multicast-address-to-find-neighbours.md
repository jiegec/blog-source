---
layout: post
date: 2018-07-15
tags: [icmp,ping,multicast]
categories:
    - networking
title: 用 multicast 地址找到同一网段的主机
---

IPv4 :

```shell
$ ping -t1 224.0.0.1
```

IPv6:

```shell
$ ping -t1 ff02::1%iface
```
