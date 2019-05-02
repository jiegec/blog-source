---
layout: post
date: 2019-04-30 17:39:00 +0800
tags: [libc,linux,c,dns]
category: software
title: 在 Linux 中用 C 代码获取 DNS 服务器列表
---

最近在做一个作业的时候，发现里面有个步骤是获取 Linux 系统中的 DNS 服务器列表，它的方法很粗暴，直接 cat grep cut 再处理。我就在想有没有完全代码的实现，然后搜了一下，果然有：

```c++
#include <resolv.h>
// ...
res_init();
// _res.nsaddr_list is an array of resolvers
```

用到了全局变量 `_res` ，虽然很 hacky ，但是至少是工作的，不清楚兼容性几何。