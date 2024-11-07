---
layout: post
date: 2024-11-07
tags: [cpu,arm,neoverse,performance]
categories:
    - hardware
---

# ARM Neoverse V2 微架构评测

## 背景

ARM Neoverse V2 是目前（2024 年）在服务器上能用到的最新的 ARM 公版核平台（AWS Graviton 4），测试一下这个微架构在各个方面的表现。

<!-- more -->

## 官方信息

ARM 关于 Neoverse V2 微架构有如下公开信息：

- [Arm Neoverse V2 platform: Leadership Performance and Power Efficiency for Next-Generation Cloud Computing, ML and HPC Workloads](https://hc2023.hotchips.org/assets/program/conference/day1/CPU1/HC2023.Arm.MagnusBruce.v04.FINAL.pdf)
- [Arm® Neoverse™ V2 Core Technical Reference Manual](https://developer.arm.com/documentation/102375/latest/)
- [Arm Neoverse V2 Software Optimization Guide](https://developer.arm.com/documentation/109898/latest/)

考虑到 Neoverse V2 与 Cortex X3 的高度相似性，这里也列出 Cortex X3 的相关信息：

- [Arm Unveils Next-Gen Flagship Core: Cortex-X3](https://fuse.wikichip.org/news/6855/arm-unveils-next-gen-flagship-core-cortex-x3/)
- [Arm® Cortex‑X3 Core Technical Reference Manual](https://developer.arm.com/documentation/101593/latest/)

## 现有评测

网上已经有 Neoverse V2 微架构的评测和分析，建议阅读：

- [Hot Chips 2023: Arm’s Neoverse V2](https://chipsandcheese.com/p/hot-chips-2023-arms-neoverse-v2)

下面分各个模块分别记录官方提供的信息，以及实测的结果。读者可以对照已有的第三方评测理解。官方信息与实测结果一致的数据会加粗。

## Benchmark

Neoverse V2 (AWS Graviton 4) 的性能测试结果见 [SPEC](../../../benchmark.md)。

## 前端

## 后端
