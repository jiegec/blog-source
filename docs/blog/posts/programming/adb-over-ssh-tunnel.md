---
layout: post
date: 2018-09-13
tags: [ssh,adb,forwarding]
categories:
    - programming
---

# 通过 SSH 隧道连接 ADB 和 Android 设备

由于本机算力不足，想要在远程[编译 LineageOS](building-lineageos-in-archlinux.md) ，其中有一步需要连接到已有的设备，于是突发奇想：

1. adb 可以通过 网络连接
2. ssh 可以进行端口转发，这里是把 remote 的端口转发到 Android 设备上的端口。

方法如下：

```shell
$ adb shell ip -f inet addr show wlan0
$ # remember the ip address here
$ adb tcpip PORT1
$ ssh -R PORT2:ANDROID_IP:PORT1 REMOTE
(remote)$ adb connect localhost:PORT2 # trust this device on Android
```

参考文档：

1. [How can I connect to Android with ADB over TCP?](https://stackoverflow.com/a/3623727)
2. [SSH PORT FORWARDING EXAMPLE](https://www.ssh.com/ssh/tunneling/example)