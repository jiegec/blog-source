---
layout: post
date: 2018-10-12 00:09:00 +0800
tags: [secoder,softwarengineering,cd,ci,gitlab]
category: software
title: 软工平台踩坑记
---

老师要求我们搞 CI/CD ，CI 自然是很快就搞好了，不过 CD 还得配一下。今天研究了一下它的 Deployer 架构，发现了若干易用性问题：

1. 缺乏文档
2. 只有[样例配置](https://gitlab.secoder.net/SECoder-Examples/python-example/blob/master/.gitlab-ci.yml)没有讲解
3. [已有的文档](https://docs.secoder.net/service/deployer/) 语焉不详
4. 官方对此回复：功能太多，还没忙过来写文档

于是只好经常戳助教然后尝试理解这个东西。。然后遇到了很多的 BUG ：

1. 容器没有重启功能。。。
2. 容器死了还是活着看一个图的颜色。。。毫无说明
3. 容器虽然有 Console ，但是输入过长后直接回到行首没有换行。。。
4. 容器对外的域名里有下划线。。。 Django 上来就一句 `Invalid HTTP_HOST header: 'xxxx_xxx.app.secoder.net'. The domain name provided is not valid according to RFC 1034/1035.` Express 直接就 `Invalid Host header` 放弃治疗。。。
5. 助教对上一条的回复是，等我忙完 DDL 有空再做吧。。。也就是说现在要做只能自己再开一个 Nginx 容器然后自己在 `proxy_set_header` 上做手脚。。。

