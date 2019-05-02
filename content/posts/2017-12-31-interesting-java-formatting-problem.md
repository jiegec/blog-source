---
layout: post
date: 2017-12-31 10:55:23 +0800
tags: [java,datetime formatting]
category: programming
title: 有趣的 Java 日期格式化问题
---

今天在群里看到有人说， Java 的日期格式化有问题，如果用 `YYYY-MM-dd` ，今天的日期就会显示 `2018-12-31` 。我立马在本地用 Java REPL (aka Groovy) 跑了一下，果然如此：

```groovy
$ date = new Date()
===> Sun Dec 31 10:51:26 CST 2017
$ import java.text.SimpleDateFormat
===> java.text.SimpleDateFormat
$ new SimpleDateFormat("YYYY-MM-dd").format(date)
===> 2018-12-31
```

解决方案是，把格式换为 `yyyy-MM-dd` ，确实就可以了。于是我就去研究了一下文档： [Class SimpleDateFormat](https://docs.oracle.com/javase/7/docs/api/java/text/SimpleDateFormat.html) ，发现了问题：

`y` 代表 `year` ，而 `Y` 代表 `week year` 。根据 [week year](https://docs.oracle.com/javase/7/docs/api/java/util/GregorianCalendar.html#week_year) ，因为今年最后的一个星期在明年的部分更多，于是这个星期被归在了明年，所以这一周属于 2018 ，这就可以解释之前的那个输出问题了。
