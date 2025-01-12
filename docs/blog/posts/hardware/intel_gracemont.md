---
layout: post
draft: true
date: 2025-01-12
tags: [cpu,intel,gracemont,alderlake,performance,uarch-review]
categories:
    - hardware
---

# Intel Gracemont 微架构评测

## 背景

[之前](./intel_golden_cove.md) 测试了 Intel Alder Lake 的 P 核微架构，这次就来测一下 Alder Lake 的 E 核微架构 Gracemont。

<!-- more -->

## 官方信息

Intel 关于 Gracemont 微架构有这些官方的信息：

- [Intel Alder Lake CPU Architectures](https://ieeexplore.ieee.org/document/9747991)
- [Alder Lake Architecture on Hot Chips 33](https://hc33.hotchips.org/assets/program/conference/day1/HC2021.C1.1%20Intel%20Efraim%20Rotem.pdf)
- [Intel 64 and IA-32 Architectures Optimization Reference Manual Volume 1](https://www.intel.com/content/www/us/en/content-details/671488/intel-64-and-ia-32-architectures-optimization-reference-manual-volume-1.html)

## 现有评测

网上已经有较多针对 Gracemont 微架构的评测和分析，建议阅读：

- [Gracemont: Revenge of the Atom Cores](https://chipsandcheese.com/2021/12/21/gracemont-revenge-of-the-atom-cores/)
- [Intel’s Gracemont Small Core Eclipses Last-Gen Big Core Performance](https://fuse.wikichip.org/news/6102/intels-gracemont-small-core-eclipses-last-gen-big-core-performance/)

下面分各个模块分别记录官方提供的信息，以及实测的结果。读者可以对照已有的第三方评测理解。官方信息与实测结果一致的数据会加粗。

## Benchmark

Intel Gracemont 的性能测试结果见 [SPEC](../../../benchmark.md)。

## 前端

### Fetch

官方信息：

- 2x 32B/cycle

### Decode

官方信息：

- 2x 3-wide

### L1 ICache

官方信息：

- 64KB

### L1 ITLB

官方信息：

- 64 entries, fully associative

### Return Stack

## 后端

### Rename

官方信息：

- 5-wide

### Execution Units

官方信息：

- 6 alu ports: 0/1/2/3/30/31
    - P0: ALU/SHIFT
    - P1: ALU/SHIFT/MUL/DIV
    - P2: ALU/SHIFT/MUL/DIV
    - P3: ALU/SHIFT
    - P30: JMP
    - P31: JMP
- 3 simd ports: 20/21/22
    - P20: SALU/SIMUL/FMUL/FADD/FDIV/AES/SHA
    - P21: SALU/FMUL/FADD/AES
    - P22: SALU
- 2 load ports: 10/11
- 2 store address ports: 12/13
- 2 store data ports: 8/9
- 2 simd store data ports: 28/29
- ports 10/11/12/13 shares a reservation station
- ports 8/9/30/31 shares a reservation station
- ports 28/29 shares a reservation station
- ports 20/21/22 shares a reservation station

### LSU

官方信息：

- 2x 16B Load/cycle, 2x 16B Store/cycle
- Load latency 3-4 cycle

#### Load Store 带宽

#### Store to Load Forwarding

官方信息：

- 

### L1 DCache

官方信息：

- 32KB
- dual ported

### L1 DTLB

官方信息：

- 32 entries, fully associative

### L2 TLB

官方信息：

- 4-way 2048 entries for 4K/2M pages
- fully associative 8 entries for 1GB pages
- 4 page walkers

### L2 Cache

官方信息：

- 2MB/4MB Shared among 4 cores
- 64 B/cycle shared among 4 cores
- 17 cycle latency

### ReOrder Buffer

官方信息：

- 256 entries
- 8 wide retirement
