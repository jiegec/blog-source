---
layout: post
date: 2021-07-24
tags: [homebridge,broadlink,rm]
categories:
    - software
---

# 配置 homebridge-broadlink-rm-pro

## 背景

最近发现空调遥控器电池有点不足，有时候会自动关机，于是拿出以前买的 Broadlink RM mini 3 充当远程的空调遥控器使用。为了方便手机上配置，分别采用了官方的 App 智慧星和 homebridge 进行配置。

## 步骤

首先用官方的智慧星配置好 Broadlink RM mini 3 的网络，然后配置 homebridge-broadlink-rm-pro。最早的插件作者不怎么更新了，这个版本是目前用的比较多的一个 fork。

安装好以后，在 Home 里面可以看到 Scan Code 的开关。打开以后，用遥控器在 Broadlink RM mini 3 附近按按键，就可以在 Homebridge 日志里看到 hex code 了。然后，就按照插件教程里的方法写配置，例子如下：

```json
{
        "platform": "BroadlinkRM",
        "name": "Broadlink RM",
        "accessories": [
        {
                "name": "Air Conditioner",
                "type": "air-conditioner",
                "noHumidity": true,
                "minTemperature": 26,
                "maxTemperature": 28,
                "defaultCoolTemperature": 27,
                "data": {
                        "off": "2600...",
                        "cool28": {
                                "data": "2600..."
                        },
                        "cool27": {
                                "data": "2600..."
                        },
                        "cool26": {
                                "data": "2600..."
                        }
                }
        }]
}
```

这样就可以在手机上方便地控制空调温度了。测试了一下，可以用 Siri 说“设置空调为 XX 度”，也是完全可以工作的。

P.S. 小米的空气净化器现在可以用插件 https://github.com/torifat/xiaomi-mi-air-purifier#readme，之前博客里写的那一个已经不更新了。