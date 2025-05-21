---
layout: post
date: 2025-05-21
tags: [cpu,apple,m4,performance,uarch-review]
draft: true
categories:
    - hardware
---

# Apple M4 微架构评测

## 背景

最近拿到了 Apple M4 的环境，借此机会测试一下 Apple M4 的微架构，和之前[分析的 Apple M1 的微架构](./apple_m1.md)做比较。由于 Asahi Linux 尚不支持 Apple M4，所以这里的测试都在 macOS 上进行。

<!-- more -->

## 官方信息

Apple M4 的官方信息乏善可陈，关于微架构的信息几乎为零，但能从操作系统汇报的硬件信息中找到一些内容。

## 现有评测

网上已经有较多针对 Apple M4 微架构的评测和分析，建议阅读：

- [苹果M4性能分析：尽力了，但芯片工艺快到头了！](https://www.bilibili.com/video/BV1NJ4m1w7zk/)

下面分各个模块分别记录官方提供的信息，以及实测的结果。读者可以对照已有的第三方评测理解。官方信息与实测结果一致的数据会加粗。

## 前端

### 取指

#### P-Core

#### E-Core

### L1 ICache

#### P-Core

#### E-Core

### BTB

#### P-Core

#### E-Core

### L1 ITLB

#### P-Core

#### E-Core

### Decode

#### P-Core

#### E-Core

### Return Stack

#### P-Core

#### E-Core

### Conditional Branch Predictor

#### P-Core

#### E-Core

## 后端

### 物理寄存器堆

#### P-Core

#### E-Core

### Load Store Unit + L1 DCache

#### L1 DCache 容量

##### P-Core

##### E-Core

#### L1 DTLB 容量

##### P-Core

##### E-Core

#### Load/Store 带宽

##### P-Core

##### E-Core

#### Memory Dependency Predictor

##### P-Core

##### E-Core

#### Store to Load Forwarding

##### P-Core

##### E-Core

#### Load to use latency

##### P-Core

##### E-Core

#### Virtual Address UTag/Way-Predictor

##### P-Core

##### E-Core

### 执行单元

#### P-Core

#### E-Core

### Scheduler

#### P-Core

#### E-Core

### Reorder Buffer

#### P-Core

#### E-Core

### L2 Cache

### L2 TLB

#### P-Core

#### E-Core
