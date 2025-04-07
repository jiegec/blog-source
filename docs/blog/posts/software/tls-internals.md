---
layout: post
date: 2025-04-07
tags: [linux,glibc,tls]
draft: true
categories:
    - software
---

# glibc 2.31 的 TLS 实现探究

## 背景

TLS 是 thread local storage 的缩写，可以很方便地存储一些 per-thread 的数据，但它内部是怎么实现的呢？本文对 glibc 2.31 版本的 TLS 实现进行探究。

<!-- more -->

## 参考

- [ELF Handling For Thread-Local Storage](https://www.akkadia.org/drepper/tls.pdf)
