---
layout: post
date: 2019-10-19 10:14:00 +0800
tags: [telegraf,cisco,wlc,snmp,mib]
category: devops
title: 为 Cisco WLC 配置 Telegraf
---

最近想到可以给 Cisco WLC 也配置一下监控，查了一下，果然有一些方法。大概研究了一下，找到了方法：

把 https://github.com/haad/net-snmp/tree/master/mibs 和 https://github.com/zampat/neteye4/tree/master/monitoring/monitoring-plugins/wireless/cisco/mibs 目录下的所有 .txt 文件放到 /usr/share/snmp/mibs 目录下。

然后把 https://github.com/zampat/neteye4/blob/master/monitoring/monitoring-plugins/wireless/cisco/telegraf.conf 下面 snmp 的配置复制到 telegraf 配置中，然后修改一下 IP 地址。

确保 Cisco WLC 的 SNMP 的 Public Community 已经配置好，然后就可以拿到数据了。

目前可以拿到 WLC 自身的一些运行˙状态信息、AP 的信息、SSID 的信息和 Client 的信息，基本满足了我们的需求。

参考：https://www.neteye-blog.com/2019/08/monitoring-a-cisco-wireless-controller/
