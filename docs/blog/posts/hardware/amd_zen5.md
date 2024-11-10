---
layout: post
date: 2024-11-11
tags: [cpu,amd,ryzen,zen5,performance]
draft: true
categories:
    - hardware
---

# AMD Zen 5 微架构评测

## 背景

Zen 5 是 AMD 最新的一代微架构，在很多地方和之前不同，因此测试一下这个微架构在各个方面的表现。

<!-- more -->

## 官方信息

AMD 一向公开得比较大方，关于 Zen 5 的信息有：

- [Software Optimization Guide for the AMD Zen5 Microarchitecture](https://www.amd.com/content/dam/amd/en/documents/processor-tech-docs/software-optimization-guides/58455.zip)
- [5TH GEN AMD EPYC™ PROCESSOR ARCHITECTURE](https://www.amd.com/content/dam/amd/en/documents/epyc-business-docs/white-papers/5th-gen-amd-epyc-processor-architecture-white-paper.pdf)

## 现有评测

网上已经有较多针对 Zen 5 微架构的评测和分析，建议阅读：

- [AMD Reveals More Zen 5 CPU Core Details](https://www.phoronix.com/review/amd-zen-5-core)
- [Zen 5’s 2-Ahead Branch Predictor Unit: How a 30 Year Old Idea Allows for New Tricks](https://chipsandcheese.com/2024/07/26/zen-5s-2-ahead-branch-predictor-unit-how-30-year-old-idea-allows-for-new-tricks/)
- [Zen 5’s Leaked Slides](https://chipsandcheese.com/2023/10/08/zen-5s-leaked-slides/)
- [AMD’s Strix Point: Zen 5 Hits Mobile](https://chipsandcheese.com/2024/08/10/amds-strix-point-zen-5-hits-mobile/)
- [AMD’s Ryzen 9950X: Zen 5 on Desktop](https://chipsandcheese.com/2024/08/14/amds-ryzen-9950x-zen-5-on-desktop/)
- [Discussing AMD’s Zen 5 at Hot Chips 2024](https://chipsandcheese.com/2024/09/15/discussing-amds-zen-5-at-hot-chips-2024/)

下面分各个模块分别记录官方提供的信息，以及实测的结果。读者可以对照已有的第三方评测理解。官方信息与实测结果一致的数据会加粗。

## Benchmark

AMD Zen 5 的性能测试结果见 [SPEC](../../../benchmark.md)。

## 前端

### 取指

官方信息：每周期共 64B，可以取两个 32B 对齐的指令块

### Decode

官方信息：2x 4-wide Decode Pipeline

### Op Cache

官方信息：64 set, 16 way, 6 inst/entry, 供指 2x6 inst/cycle

### L1 ICache

官方信息：32KB, 8-way set associative

### L1 ITLB

官方信息：64-entry, fully associative

### L2 ITLB

官方信息：2048-entry, 8-way set associative

### BTB

官方信息：16K-entry L1 BTB, 8K-entry L2 BTB

### Return Address Stack

官方信息：52-entry per thread

### Indirect Target Predictor

官方信息：3072-entry Indirect Target Array

### Move Elimination (Zero Cycle Move) and Zeroing/Ones Idiom

官方信息：支持 xor/sub/cmp/sbb/vxorp/vandnp/vpcmpgt/vpandn/vpxor/vpsub 的 Zeroing Idiom，支持 pcmpeq/vpcmpeq 的 Ones Idiom，支持 mov/movsxd/xchg/(v)vmovap/(v)movdp/(v)movup 的 Zero Cycle Move。

## 后端

### Dispatch

官方信息：8 MOP/cycle, up to 2 taken branches/cycle

### ROB

官方信息：224-entry per thread

### Register File

官方信息：240-entry integer physical register file, 192-entry flag physical register file

### L1 DCache

官方信息：48KB, 12-way set associative

### Load Store Unit

官方信息：每周期最多四个内存操作。每周期最多四个读，其中最多两个 128b/256b/512b 读；每周期最多两个写，其中最多一个 512b 写。load to use latency，整数是 4-5 个周期，浮点是 7-8 个周期。跨越 64B 边界的读会有额外的一个周期的延迟。

### L1 DTLB

官方信息：96-entry, fully associative

### L2 DTLB

官方信息：4096-entry, 16-way set associative

### L2 Cache

官方信息：16-way set associative, inclusive, 1MB, >= 14 cycle load to use latency

### L3 Cache

官方信息：16-way set associative, exclusive
