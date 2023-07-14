---
layout: post
date: 2018-09-13 14:27:00 +0800
tags: [mongodb,ubuntu]
category: software
title: 在 Ubuntu 上跨版本迁移 MongoDB
---

由于 MongoDB 只支持当前版本和上一个版本的数据库格式，然后刚刚滚系统升级的时候升级到了 3.6.x，而数据库格式仍然是 3.2.x 的，于是需要先安装回 3.4.x 版本的 MongoDB，输入命令把数据库升级到 3.4.x 版本后，再用 3.6.x 的数据库进行升级。

以 从 Ubuntu 14.04 LTS 升级到 Ubuntu 18.04.1 LTS 为例，方法如下：

```shell
$ wget https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu1604-3.4.17.tgz
$ tar xvf mongodb-linux-x86_64-ubuntu1604-3.4.17.tgz
$ cd mongodb-linux-x86_64-ubuntu1604-3.4.17/bin/
$ sudo ./mongod --config /etc/mongodb.conf &
$ mongo
> db.adminCommand( { setFeatureCompatibilityVersion: '3.4' } )
{ "ok" : 1 }
$ fg
^C
$ sudo chown -R mongodb:mongodb /var/lib/mongodb
$ sudo systemctl start mongodb
$ mongo
> db.adminCommand( { getParameter: 1, featureCompatibilityVersion: 1 } )
{ "featureCompatibilityVersion" : { "version" : "3.4" }, "ok" : 1 }
> db.adminCommand( { setFeatureCompatibilityVersion: '3.6' } )
{ "ok" : 1 }
> db.adminCommand( { getParameter: 1, featureCompatibilityVersion: 1 } )
{ "featureCompatibilityVersion" : { "version" : "3.6" }, "ok" : 1 }
$ # Okay now
```