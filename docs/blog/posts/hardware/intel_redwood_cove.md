---
layout: post
date: 2025-04-23
draft: true
tags: [cpu,intel,redwoodcove,meteorlake,graniterapids,performance,uarch-review]
categories:
    - hardware
---

# Intel Redwood Cove 微架构评测

## 背景

之前我们测试了 Intel 的微架构 Golden Cove，这次就来测一下 Redwood Cove，它被用到了 Meteor Lake 以及 Granite Rapids 上。这次就以阿里云 [g9i](https://help.aliyun.com/zh/ecs/user-guide/overview-of-instance-families#g9i) 实例的 Granite Rapids 机器来测试一下 Redwood Cove 微架构的各项指标。

<!-- more -->

## 官方信息

Intel 关于 Redwood Cove 微架构有这些官方的信息：

- [Intel® 64 and IA-32 Architectures Optimization Reference Manual Volume 1](https://www.intel.com/content/www/us/en/content-details/814198/intel-64-and-ia-32-architectures-optimization-reference-manual-volume-1.html)
- [Meteor Lake Architecture Overview](https://www.thefpsreview.com/wp-content/uploads/2023/10/Meteor-Lake-Architecture-Overview.pdf)

## 现有评测

网上已经有较多针对 Redwood Cove 微架构的评测和分析，建议阅读：

- [Intel’s Redwood Cove: Baby Steps are Still Steps](https://chipsandcheese.com/p/intels-redwood-cove-baby-steps-are-still-steps)
- [Intel Unveils Meteor Lake Architecture: Intel 4 Heralds the Disaggregated Future of Mobile CPUs](https://www.anandtech.com/show/20046/intel-unveils-meteor-lake-architecture-intel-4-heralds-the-disaggregated-future-of-mobile-cpus/2)

## Benchmark

Intel Redwood Cove 的性能测试结果见 [SPEC](../../../benchmark.md)。

## 前端

### L1 ICache

官方信息：

- Larger instruction cache: 32K→64K.

### Instruction Decode Queue (IDQ) + Loop Stream Detector (LSD)

官方信息：

- Improved LSD coverage: the IDQ can hold 192 μops per logical processor in single-thread mode or 96 μops per
thread when SMT is active.

### Instruction Prefetch Instruction

官方信息：

- Code Software Prefetch x86 architecture extension (Granite Rapids only).
- PREFETCHIT0: (temporal code)—prefetch code into all levels of the cache hierarchy.
- PREFETCHIT1: (temporal code with respect to first level cache misses)—prefetch code into all but the first-level of the cache hierarchy.

## 后端

### 执行单元

官方信息：

- EXE: 3-cycle Floating Point multiplication.

### Prefetcher

官方信息：

- New HW data prefetcher to recognize and prefetch the “Array of Pointers” pattern.
