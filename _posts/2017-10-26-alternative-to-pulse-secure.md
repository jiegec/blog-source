---
layout: post
date: 2017-10-26 07:50:34 +0800
tags: [THU,Networking]
category: others
title: 一个代替Pulse Secure客户端的工具
---

[清华的校外VPN服务](sslvpn.tsinghua.edu.cn)使用的是Pulse Secure,所以在外网我们需要在客户端上安装Pulse Secure才能使用内网的info和网络学堂等网站.但是Pulse Secure一是非自由软件二界面难看,所以我找到了一个代替它的工具:[OpenConnect](http://www.infradead.org/openconnect/).

安装后,输入以下命令:

```shell
sudo openconnect --user 你的学号 sslvpn.tsinghua.edu.cn --juniper --reconnect-timeout 60 --servercert sha256:398c6bccf414f7d71b6dc8d59b8e3b16f6d410f305aed7e30ce911c3a4064b31
```

然后输入你的info密码即可.