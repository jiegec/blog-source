---
layout: post
date: 2021-07-16 00:16:00 +0800
tags: [nginx,http,post,disk]
category: software
title: Nginx 处理 POST 请求出现 Internal Server Error 排查一则
---

## 前言

最近一个服务忽然出现问题，用户反馈，HTTP POST 一个小的 body 不会出错，POST 一个大的 body 就会 500 Internal Server Error。


## 排查

观察后端日志，发现没有出错的那一个请求。观察 Nginx 日志，发现最后一次日志是几个小时前。最后几条 Nginx 日志写的是 `a client request body is buffered to a temporary file`。

## 结论

继续研究后，发现是硬盘满了。Nginx 在处理 POST body 的时候，如果 body 超过阈值，会写入到临时文件中：

```
Syntax: client_body_buffer_size size;
Default: client_body_buffer_size 8k|16k;
Context: http, server, location
Sets buffer size for reading client request body. In case the request body is larger than the buffer, the whole body or only its part is written to a temporary file. By default, buffer size is equal to two memory pages. This is 8K on x86, other 32-bit platforms, and x86-64. It is usually 16K on other 64-bit platforms.
```

详见 https://nginx.org/en/docs/http/ngx_http_core_module.html#client_body_buffer_size

这就可以解释为什么 Nginx 返回 500 而且没有转发到后端，也可以解释为什么 Nginx 没有输出新的错误日志。