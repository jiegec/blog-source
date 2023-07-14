---
layout: post
date: 2021-03-27 22:07:00 +0800
tags: [esxi,esxcli,ipv6]
category: networking
title: ESXi 网络配置
---

用过 ESXi 的大家都知道，它网页版对网络的配置功能有限，特别是 IPv6 的部分，有的事情无法实现。更好的办法是 SSH 到 ESXi 上直接用命令行进行配置。

可能会用到的一些命令：

1. esxcfg-vmknic: 用来给 vmkernel 配置地址
2. esxcfg-route: 设置系统路由表
3. esxcli: 大杂烩，很多功能都在里面
4. tcpdump-uw：魔改版 tcpdump

一些例子：

设置 IPv6 默认路由：

```shell
[root@esxi:~]esxcfg-route -f V6 -a default $IPV6
```

删除 vmkernel 的 IPv6 地址：

```shell
[root@esxi:~]esxcli network ip interface ipv6 address remove -i $VMKERNEL -I $IPV6/$PREFIX
```


参考：https://kb.vmware.com/s/article/1002662