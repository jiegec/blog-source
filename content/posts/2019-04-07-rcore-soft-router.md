---
layout: post
date: 2019-04-07 12:13:00 +0800
tags: [rcore,router,ixgbe,os]
category: software
title: rCore 软路由实现
---

最近在研究软路由在 rCore 上的实现，但限于硬件限制，目前先在虚拟机里测试。软路由大概要做这些东西：

 	1. 抓包，解析包里的内容
 	2. 查路由表，找到下一跳在哪
 	3. 查ARP，知道下一跳的 MAC 地址
 	4. 减少TTL，更新 IP Checksum
 	5. 把包发出去

第一步直接拿 smoltcp 的 Raw Socket 即可，但是目前只能抓指定 IP Protocol 的包，我用的是 ICMP ，但其他的就还抓不了，需要继续改 Smoltcp 源代码。

第二步用的是之前刚修好的 treebitmap 库，它提供了路由表的查询功能，目前路由表还是写死的，之后会用已经部分实现好的 Netlink 接口读取出来。

第三步则是 ioctl 发请求，然后从 smoltcp 内部的 ARP cache 里读取。

第四步很简单，不用多说。

第五步则需要指定出端口，用了一个 index ，放在一个特定的 sockaddr 中。

最后的效果就是，能双向转发 ping 通。

网络拓扑：

![](/router_topo.png)

可以，这很玄学。

后续在想在真机上实验，但是还缺一个网卡驱动，不然就可以用神奇的办法来做这个实验了。