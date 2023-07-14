---
layout: post
date: 2019-01-13
tags: [grafana,influxdb,telegraf]
categories:
    - software
title: Grafana 中可视化 Ping 时把 Timeout 显示为指定值
---

刚遇到一个需求，就是用 Telegraf 收集 ping 信息，然后在 Grafana 里可视化当前的延迟，如果超时了，就显示一个指定值，如 999，这样就可以放到一个 Gauge 里面可视化了。但是，问题在于，Telegraf 的 ping input 在超时的时候只会在 result_code 里写一个 [2](https://github.com/influxdata/telegraf/tree/master/plugins/inputs/ping) ，其他项都是空的，因而如果直接用 GROUP BY time(interval) fill(999) 会导致最新的一个数据经常得到 999。这意味着需要根据 "result_code" 来进行区分 Timeout 的情况。最后捣腾了很久，得到了这个方案：

```
 select "average_response_ms" * (2 - "result_code") / 2 + "result_code" / 2 * 999 from (select "average_response_ms", "result_code" from ping where $timeFilter fill(0))
```

最后的方法很粗糙：当 "result_code" 是 0 也就是成功的时候，得到延迟，而当 "result_code" 是 2 也就是超时的时候，直接得到 999。这样就解决了这个问题。