---
layout: post
date: 2018-08-25
tags: [slacc,ipv6,tuntaposx,tap]
categories:
    - networking
title: 在 macOS 上 TAP Interface 上启用 IPv6 自动配置
---

由于 macOS 对 TAP Interface 不会自动出现一个设置中对应的服务，所以需要手动进行配置。一番测试后，发现可以通过：

```
$ sudo ipconfig set [tap_if] automatic-v6
$ sudo ipconfig set [tap_if] dhcp
```

启用系统自带的 dhcp 和 ra 功能。也许有方法可以把这些 tap 搬到系统的设置中去。

UPDATE:

可以把 TAP Interface 加到系统的设置中去。方法参考[Virtual network interface in Mac OS X](https://stackoverflow.com/a/6375307)。完成以后可以直接通过系统设置界面进行配置。
