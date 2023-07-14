---
layout: post
date: 2019-01-10
tags: [grafana,regex]
category: software
title: Grafana Variable 的 regex 过滤方式
---

用 InfluxDB 收集到 Mountpoint 数据的时候，经常会掺杂一些不关心的，如 TimeMachine，KSInstallAction 和 AppTranslocation 等等。所以，为了在 Variables 里过滤掉他们，需要用 Regex 进行处理。[网上](https://community.grafana.com/t/templating-regex-exclude-not-working/1077/4)有人提供了方案，就是通过 Negative Lookahead 实现：

```regexp
/^(?!.*TimeMachine)(?!.*KSInstallAction)(?!.*\/private)/
```

这样就可以把不想看到的这些 mountpoint 隐藏，节省页面空间了。当然了，这里其实也可以用白名单的方法进行处理，直接写 regex 就可以了。