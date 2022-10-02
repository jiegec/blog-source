---
layout: post
date: 2018-11-04 10:47:00 +0800
tags: [homebridge,xiaomi,airpurifier,homekit]
category: software
title: 使用 HomeBridge 把小米空气净化器加入到 HomeKit 中
---

受 @NSBlink 安利，自己部署了一下 [HomeBridge](https://github.com/nfarina/homebridge) ，然后在 iOS 的家庭上就可以看到它。然后，通过 [homebrdige-mi-airpurifier](https://www.npmjs.com/package/homebridge-mi-airpurifier) 和 [miio](https://github.com/aholstenson/miio) 按照教程进行配置。然后就可以在家庭里看到小米空气净化器，包括空气质量，湿度，睡眠模式，温度，打开状态。然后我就可以做一些配置，如离开宿舍的时候自动关闭空气净化器，回来的时候自动打开。不过由于自己没有一个一直放在宿舍的 iPad、Apple TV 或者 HomePod，失去了中枢，这个功能可能会打折扣。

后续想买一些智能的灯啊，然后就可以用 Siri 进行打开 / 关闭了。

此外，我又试了下，可以用 [homebridge-camera-ffmpeg](https://github.com/KhaosT/homebridge-camera-ffmpeg) 把摄像头配置到 HomeKit 中。这样，就可以远程查看视频流了。