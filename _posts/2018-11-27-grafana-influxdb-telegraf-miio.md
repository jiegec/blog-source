---
layout: post
date: 2018-11-27 20:33:00 +0800
tags: [macos,grafana,influxdb,telegraf,miio]
category: software
title: 配置 Grafana+InfluxDB+Telegraf 并添加 MIIO 数据来源
---

之前一直想配一个监控系统，现在有机会了，就简单配了一下。发现真的特别简单，用 Homebrew 安装这三个软件并且都跑起来，然后稍微动一下配置，就可以得到可观的效果了。

然后想利用 miio 配置一下，把宿舍的空气净化器各项参数拿到，以 Telegraf 的插件形式定时上报，然后通过 Grafana 进行可视化。插件放在了 [jiegec/tools](https://github.com/jiegec/tools/blob/master/telegraf/miio.py) 下，就是一个简单的 Python 脚本。配置方法如下：

编辑 `/usr/local/etc/telegraf.d/miio.conf`：

```ini
[[inputs.exec]]
	commands = ["/usr/local/bin/python3 /Volumes/Data/tools/telegraf/miio.py MIID_HERE"]
	timeout = "5s"
	data_format = "influx"
```

默认了 miio 路径为 `/usr/local/bin/miio` 。