---
layout: post
date: 2026-11-24
tags: [cpu,loongson,loongarch,la464,performance,uarch-review]
draft: true
categories:
    - hardware
---

# Loongson LA464 微架构评测

## 背景

之前分析了很多国外的微架构，而龙芯的微架构一直都没怎么研究过。既然 LA864 快要来了，那就在它来之前分析一下 LA464 和 [LA664](./loongson-la664.md)。

<!-- more -->

## 官方信息

Loongson 关于 LA464 微架构有这些官方的信息：

- [龙芯 3A5000](https://www.loongson.cn/product/show?id=10)

## 现有评测

网上已经有较多针对 LA464 微架构的评测和分析，建议阅读：

- [Loongson’s 3A5000: China’s Best Shot?](https://old.chipsandcheese.com/2023/04/09/loongsons-3a5000-chinas-best-shot/)

下面分各个模块分别记录官方提供的信息，以及实测的结果。读者可以对照已有的第三方评测理解。官方信息与实测结果一致的数据会加粗。

## Benchmark

Loongson LA464 的性能测试结果见 [SPEC](../../../benchmark/index.md)。

## 前端

### Fetch

### Decode

### L1 ITLB

### L1 ICache

### Return Stack

## 后端

### Rename

### Execution Units

### LSU

#### Load Store 带宽

#### Store to Load Forwarding

### Memory Dependency Predictor

### L1 DCache

### L1 DTLB

### L2 TLB

### L2 Cache

### Prefetcher

#### 预取延迟

#### 预取距离

#### 是否跨页

### ReOrder Buffer
