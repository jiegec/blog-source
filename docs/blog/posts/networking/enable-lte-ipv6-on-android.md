---
layout: post
date: 2018-10-04
tags: [android,apn,ipv6]
categories:
    - networking
---

# 在 Android 上打开 LTE 的 IPv6

听闻北京移动给 LTE 配置了 SLAAC，但现在需要手动打开，方法如下：

Settings -> Network & Internet -> Mobile Network -> Advanced -> Access Point Names -> 中国移动 GPRS (China Mobile) -> 把 APN procotol 和 APN roaming protocol 两项都改成 IPv4/IPv6 

然后在 [test-ipv6.com](https://test-ipv6.com) 上可以看到确实分配了 IPv6 地址，不过目前评分只有 1/10。也就是说可用性还不佳。

而在 iOS 上，通过 HE 的 Network Tools 能看到，确实拿到了 IPv6 的地址，但是出不去，怀疑是运营商没有下发相关配置，所以还不能使用，只能继续等。

2018-11-06 更新：现在 iOS 用户也有 LTE 的 v6 了。评分是 9/10。目前可用性已经可以了，就是国内互联还不大好。
