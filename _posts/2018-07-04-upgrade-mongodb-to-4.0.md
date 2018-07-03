---
layout: post
date: 2018-07-04 07:22:00 +0800
tags: [mongodb,transaction]
category: programming
title: 升级 MongoDB 到 4.0
---

MongoDB 4.0 刚刚发布，加入了我很想要的 Transaction 功能。不过，我一更新就发现 Mongodb 起不来了。研究了一下日志，发现需要先执行如下操作：

```shell
$ # MongoDB version 3.6
$ mongo
> db.adminCommand( { setFeatureCompatibilityVersion: "3.6" } )
```

然后再升级到 MongoDB 4.0 ，才能正常地启动 MongoDB 4.0 。之后可以考虑尝试使用 MongoDB 4.0 的 Transaction 了。不知道什么时候进入 Debian 的 stretch-backports 源中。
