---
layout: post
date: 2014-10-06
tags: [java,intellijidea,android,androidstudio]
categories:
    - csdn
title: "@微信 SDK 开发者，发现一个 BUG~"
---

迁移自本人在 CSDN 上的博客：https://blog.csdn.net/build7601/article/details/39826065

经过测试，发现微信客户端登录 SDK 有一个 BUG。注：目前只在 iOS 上测试过，可以重现。

BUG 重现

1.做一个可以用微信登陆的软件，先安装到设备。
2.更改 project 的 Bundle Identifier，只更改大小写，重新安装到设备。P.S.实际情况是包名大小写修改过引发这个问题。
3.打开第二个安装的 APP，选择微信登陆，跳转到微信。
4.点击微信登陆，则会跳转到第一个 APP 中，而不会跳转到第二个 APP。

我的 BUG 分析

这可能是因为，微信 sdk 传到微信的是一个 bundle identifier+回调函数地址，回调时找到另一个 APP 再执行回调。
可能在某处进程的名称不分大小写，按照顺序找到了第一个去了。一旦两个 APP 版本不一致，可能执行到空的地址甚至发生不可预测的行为。
经过测试，发现同一样的版本的 APP 也发生了崩溃。