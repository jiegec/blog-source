---
layout: post
date: 2018-10-23
tags: [docker,secoder,mongodb]
category: software
title: 部署 adminMongo 的 Docker 镜像
---

之前在软工的平台上部署了一个 MongoDB，但是自然是仅内网访问，想要浏览内容只能通过网页上的 Console 进去看，体验特别不好。所以想着能不能找一个在线的 MongoDB 浏览器。由于软工平台只能部署 Docker 镜像，所以我找到了[mongo-express](https://hub.docker.com/_/mongo-express/)和[adicom/admin-mongo](https://hub.docker.com/r/adicom/admin-mongo/)。但软工平台现在还没实现环境变量的配置，所以我选了后者。

首先本地创建一个 app.json，让它监听 0.0.0.0:80，通过 deployer 传到平台上的配置，然后再把配置 mount 到 /app/config 路径上。现在就可以成功地在网页上浏览 MongoDB 了。
