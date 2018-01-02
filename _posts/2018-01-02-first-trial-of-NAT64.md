---
layout: post
date: 2018-01-02 19:41:22 +0800
tags: [networking, NAT, IPv6, NAT64, DNS, DNS64]
category: networking
title: NAT64 初尝试
---

最近宿舍里有线网络的 IPv4 总是拿不到地址，只能连无线网，不禁对计算机系学生的可怕的设备数量有了深刻的认识。不过，作为一个有道德（误）的良好青年，还是不要给已经枯竭的 IPv4 地址填堵了，还是赶紧玩玩 IPv6 的网络吧。然后在 TUNA 群里受青年千人续本达 (@heroxbd) 的安利，本地搭建一下 NAT64+DNS64 的环境。不过考虑到宿舍还是拿不到有线的 IPv4 地址，我就先利用苹果先前在强制 iOS 的应用支持 NAT64 网络的同时，在 macOS 上为了方便开发者调试，提供的便捷的建立 NAT64 网络的能力。

首先在设置中按住 Option 键打开 Sharing ， 点击 Internet Sharing ，勾上 Create NAT64 Network 然后把网络共享给设备。然后在手机上关掉 Wi-Fi 和 Cellular ，发现还能正常上网。此时可以打开 Wireshark 验证我们的成果了：

在手机上打开浏览器，浏览千度，得到如下的 Wireshark 截图：
![baidu-nat64](/assets/baidu-nat64.jpg)

这里，`2001:2:0:aab1::1` 是本机在这个子网中的地址，`2001:2::aab1:cda2:5de:87f6:fd78` 是我的 iOS 设备的地址，然后 iOS 向 macOS 发出了 DNS请求， macOS 发送 DNS 请求后得到 `baidu.com` 的 IPv4 地址之一为 `111.13.101.208` ：
![baidu-dns](/assets/baidu-dns.jpg)

上图中，我们可以看到， `baidu.com` 的 `AAAA` 记录是 `2001:2:0:1baa::6f0d:65d0` ，这个就是 DNS64 转译的地址，前面为网关的 `prefix` ，后面就是对应的 IPv4 地址： `0x6f=111, 0x0d=13, 0x65=101, 0xd0=208` ，当客户端向这个地址发包的时候，网关发现前缀符合条件，把最后的这部分 IPv4 地址取出来，自己把包发送到真实的地址上去，再把返回来的包再转为 IPv6 的地址返还给客户端。可以验证，剩下的几个地址也符合这个转译规则。

这就实现了：利用一台连接着 IPv6 和 IPv4 两种网络的网关，可以使得 IPv6 这个网络通过网关访问 IPv4 。通过配置，也可以使得 IPv4 访问 IPv6 中的地址（即 Stateful 和 Stateless 的区分，需要手动配置映射）。

好处：作为比较成熟的 IPv4 到 IPv6 过渡方案之一，可以让自己组建的 IPv6 网络访问一些仅 IPv4 的网站。
坏处：依赖于 DNS64 ，必须要经过一层翻译，一些应用或协议可能写死了 IPv4 的地址，该方法可能会失效。
