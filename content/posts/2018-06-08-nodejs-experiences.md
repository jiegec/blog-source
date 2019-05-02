---
layout: post
date: 2018-06-08 10:33:00 +0800
tags: [nodejs,mongodb,mongoose,session]
category: programming
title: 最近写 Node.js 遇到的若干坑
---

最近在做前后端分离，前端在用 Vue.js 逐步重写，后端则变为 api 的形式。同时，我尝试了用 autocannon 和 clinic 工具测试自己的 api endpoint 的性能，一开始发现有几个延迟会特别高，即使是一个很简单的 api 也有不正常的高延迟。

于是，我用 clinic 生成了 flamegraph ，发现了一些问题：

1. 我在 session 里保存了一些缓存的信息，这部分内容比较大， express-session 在保存到数据库前会先 JSON.stringify 再 crc 判断是否有改变，如果有改变则保存下来。但是由于我的这个对象嵌套层数多，所以时间花得很多。我调整了这个对象的结构，缩小了很多以后，果然这部分快了很多
2. 有一个 API 需要大量的数据库查询，原本是 O（结点总数）次查询，我考虑到我们数据的结构，改成了O（深度），果然快了许多
3. 之前遇到一个小问题，就是即使我没有登录，服务器也会记录 session 并且返回一个 cookie 。检查以后发现，是 connect-flash 即使在没有使用的时候，也会往 cookie 中写入一个空的对象，这就导致 express-session 认为需要保存，所以出现了问题。解决方案就是，换成了它的一个 fork ： connect-flash-plus ，它解决了这个问题

