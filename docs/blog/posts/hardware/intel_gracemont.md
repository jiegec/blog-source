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

- **2x 16B Load/cycle, 2x 16B Store/cycle**
- Load latency 3-4 cycle

#### Load Store 带宽

针对 Load Store 带宽，实测每个周期可以完成：

- 2x 128b Load
- 2x 128b Load + 2x 128b Store
- 2x 128b Store
- 1x 256b Load
- 1x 256b Load + 1x 256b Store
- 1x 256b Store

最大的读带宽是 32B/cyc，最大的写带宽是 32B/cyc，二者可以同时达到。

#### Store to Load Forwarding

官方信息：

- Loads that forward from stores can do so in the same load to use latency as cache hits for
cases where the store's address is known, and the store data is available.

经过实际测试，Gracemont 上如下的情况可以成功转发，对地址 x 的 Store 转发到对地址 y 的 Load 成功时 y-x 的取值范围：

| Store\Load | 8b Load | 16b Load | 32b Load | 64b Load |
|------------|---------|----------|----------|----------|
| 8b Store   | {0}     | {}       | {}       | {}       |
| 16b Store  | {0}     | {0}      | {}       | {}       |
| 32b Store  | {0}     | {0}      | {0}      | {}       |
| 64b Store  | {0}     | {0}      | {0,4}    | {0}      |

可以看到，Gracemont 在 Store 包含 Load 且地址相同时可以转发。特别地，针对 64b Store 到 32b Load 转发还允许 y-x=4。各种情况下的 CPI：

- 转发成功时，CPI 比较复杂，有的情况是介于 0.5 到 2 之间，有时候又是介于 2 到 4 之间，有时候是 6
- 重合但不能转发时，CPI 等于 11，特殊情况下还出现了 28.5

不支持多个 Store 对同一个 Load 的转发。跨缓存行时不能转发。

即使 Load 和 Store 不重合，但在一定情况下，也会出现 CPI 等于 11 的情况，例如：

- 对地址 3 的 16b Store 转发到地址 0 的 8b Load
- 对地址 1 的 64b Store 转发到地址 9/10/11 的 64b Load
- 对地址 0 的 8b Store 转发到地址 1/2/3 的 64b Load
- 对地址 0 的 8b Store 转发到地址 3 的 16b Load

在以上几种情况下，Load 和 Store 访问范围并不重合，但性能和访问范围重合且转发失败时相同（CPI 等于 11），由此猜测 Gracemont 判断是否重合是以对齐的 4B 为粒度，如果 Load 和 Store 访问了相同的对齐的 4B 块，即使不重合，一定情况下也可能会被当成重合的情况来处理，但由于实际上并没有重合，就没法转发，性能就比较差。

小结：Gracemont 的 Store to Load Forwarding：

- 1 ld + 1 st: 要求 st 完全包含 ld 且地址相同且不能跨缓存行；特别地，64b Store 到 32b Load 转发允许 y-x=4
- 1 ld + 2+ st: 不支持

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
