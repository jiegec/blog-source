---
layout: post
date: 2018-12-13 20:07:00 +0800
tags: [homebridge,mi,aqara,telegraf,influxdb]
category: software
title: 配置 homebridge-mi-aqara 并添加为 telegraf 的数据源
---

最近有了设备，想把设备拿到的数据都导一份存到 influxdb 里，但是目前找到的只有 [homebridge-mi-aqara](https://github.com/YinHangCode/homebridge-mi-aqara) 可以访问并拿到数据，然后它又提供了 mqtt 的数据获取方案，于是自己写了个脚本去读取这些数据。

首先当然是配置一下 homebridge-mi-aqara，按照网上的教程来，这个不难。然后本地开一个 MQTT Broker（如 mosquitto），配置为本地监听，然后我编写了[脚本 telegraf-mi-aqara.py](https://github.com/jiegec/tools/blob/master/telegraf-mi-aqara.py) ，使用前需要 `pip install paho-mqtt`，并且按照实际路径修改一下内容。验证能够跑起来后，写一个 telegraf 配置：

```toml
[[inputs.exec]]
        commands = ["/usr/bin/python3 /path/to/telegraf-mi-aqara.py"]
        timeout = "5s"
        data_format = "influx"
```

现在就可以读取到各项信息，如温度，湿度，是否开门，开关用电情况等等。

2018-12-16 更新：

研究了一下[绿米网关局域网通信协议](https://github.com/aqara/aiot-gateway-local-api)，得到了[第二个版本 telegraf-mi-aqara-v2.py](https://github.com/jiegec/tools/blob/master/telegraf-mi-aqara-v2.py)，它与第一版的区别是，第一版是主动向网关读取信息，而这一版则是监听组播包，等待网关发消息。这个脚本负责把读取到的组播信息发送到 MQTT，再让 telegraf 从 MQTT 里解析 JSON 消息，写入数据库。Telegraf 配置如下：

```toml
[[inputs.mqtt_consumer]]
        servers = ["tcp://127.0.0.1:1883"]
        qos = 0
        connection_timeout = "30s"
        topics = [
                "/telegraf-mi-aqara"
        ]
        persistent_session = true
        client_id = "Telegraf"
        data_format = "json"
        json_string_fields = ["model", "sid", "status"]
        tag_keys = ["model", "sid", "short_id"]
```

由于设备不全，有些字段可能不完整。如果大家自己要用的话，可能需要自行修改一下。