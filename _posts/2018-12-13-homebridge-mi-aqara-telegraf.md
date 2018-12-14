---
layout: post
date: 2018-12-13 20:07:00 +0800
tags: [homebridge,mi,aqara,telegraf,influxdb]
category: software
title: 配置 homebridge-mi-aqara 并添加为 telegraf 的数据源
---

最近有了设备，想把设备拿到的数据都导一份存到 influxdb 里，但是目前找到的只有 [homebridge-mi-aqara](https://github.com/YinHangCode/homebridge-mi-aqara) 可以访问并拿到数据，然后它又提供了 mqtt 的数据获取方案，于是自己写了个脚本去读取这些数据。

首先当然是配置一下 homebridge-mi-aqara ，按照网上的教程来，这个不难。然后本地开一个 MQTT Broker （如 mosquitto ），配置为本地监听，然后我编写了[脚本telegraf-mi-aqara.py](https://github.com/jiegec/tools/blob/master/telegraf-mi-aqara.py) ，使用前需要 `pip install paho-mqtt`，并且按照实际路径修改一下内容 。验证能够跑起来后，写一个 telegraf 配置：

```toml
[[inputs.exec]]
        commands = ["/usr/bin/python3 /path/to/telegraf-mi-aqara.py"]
        timeout = "5s"
        data_format = "influx"
```

现在就可以读取到各项信息，如温度，湿度，是否开门，开关用电情况等等。