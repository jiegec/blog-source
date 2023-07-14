---
layout: post
date: 2018-10-22
tags: [ddns,gandi,openwrt,cron]
categories:
    - networking
---

# OpenWRT 上配置 Gandi DDNS

一直想给自己的 OpenWRT 路由器添加 DDNS 功能，但 Gandi 不在官方的 ddns-scripts 列表中，自己在网上找了一些脚本，发现是 Python 写的，尝试把 Python 安装到路由器上又发现空间不够，虽然可以安装到 USB 上，但总归是麻烦。

最后找到了官方的一个[脚本](https://github.com/Gandi/api-examples/blob/master/bash/livedns/mywanip.sh)，非常适合我的需求。简单修改一下，然后安装一下支持 HTTPS 的 cURL：

```
$ opkg update
$ opkg install ca-bundle
$ opkg install curl
```

然后把脚本添加到 crontab 即可。
