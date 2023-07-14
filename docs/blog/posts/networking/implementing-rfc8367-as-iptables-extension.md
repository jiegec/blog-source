---
layout: post
date: 2018-08-31
tags: [rfc,rfc8367,aprilfool,iptables,kernel,mod,xtables]
categories:
    - networking
---

# 通过 Ipfilter Extension 实现 RFC8367

前几天无聊闲逛看到了一个很有趣的 [RFC8367 - Wrongful Termination of Internet Protocol (IP) Packets](https://tools.ietf.org/html/rfc8367) ，看到日期大家应该都懂了，这是个粥客，不过里面还是反映了一些事情，咳。

之前看到闪客实现了 [shankerwangmiao/xt_PROTO](https://github.com/shankerwangmiao/xt_PROTO) ，想到自己也可以做一个 iptables 扩展，于是就写了 [jiegec/xt_EQUALIZE](https://github.com/jiegec/xt_EQUALIZE) 。它是这样使用的：

```shell
$ git clone git@github.com:jiegec/xt_EQUALIZE.git
$ make
$ sudo make install
$ sudo iptables -t filter -A INPUT -j EQUALIZE
$ sudo dmesg -w &
$ # Make some random network requests to see the effect!
$ ping 1.1.1.1
$ ping 8.8.8.8
$ ping ::1
```

目前还没有把参数都变成可以配置的。如果真的有人需要这个模块的话，我再改吧（逃
