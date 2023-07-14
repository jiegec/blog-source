---
layout: post
date: 2018-07-04
tags: [mongodb,transaction]
categories:
    - programming
---

# 升级 MongoDB 到 4.0

MongoDB 4.0 刚刚发布，加入了我很想要的 Transaction 功能。不过，我一更新就发现 MongoDB 起不来了。研究了一下日志，发现由于我创建数据库时，MongoDB 版本是 3.4，虽然后来升级到了 3.6，但还是用着 3.4 的兼容模式。这个可以这样来检测：

```shell
$ mongo
> db.adminCommand( { getParameter: 1, featureCompatibilityVersion: 1 } )
```

如果不是 3.6，升级到 4.0 之前，需要先执行如下操作：

```shell
$ # MongoDB version 3.6
$ mongo
> db.adminCommand( { setFeatureCompatibilityVersion: "3.6" } )
```

然后再升级到 MongoDB 4.0，才能正常地启动 MongoDB 4.0。之后可以考虑尝试使用 MongoDB 4.0 的 Transaction 了。不知道什么时候进入 Debian 的 stretch-backports 源中。

为了使用 MongoDB 4.0 的新特性，输入以下命令：

```shell
$ mongo
> db.adminCommand( { setFeatureCompatibilityVersion: "4.0" } )
```

之后会尝试一下 MongoDB 4.0 的 Transaction 功能。
