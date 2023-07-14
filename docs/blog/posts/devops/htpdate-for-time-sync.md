---
layout: post
date: 2019-05-25
tags: [ntp,ntpdate,http,httpdate]
categories:
    - devops
---

# 用 htpdate 替代 ntpdate 实现时间同步

最近用 ntpdate 的时候遇到了一些麻烦，时间同步总是遇到各种问题。后来搜了搜，发现了一个解决方案：htpdate，它通过 HTTP 头里的 Date 字段获取时间，虽然没有 ntp 那么精确，但是大多时候都够用。

用法见 [htpdate(8)](https://linux.die.net/man/8/htpdate) 。

