---
layout: post
date: 2025-09-10
tags: [cpu,arm,neoverse,cortex,c1]
categories:
    - hardware
---

# ARM 公版核微架构演进

## 背景

ARM 公版核微架构的演进频繁，型号又比较多，相关信息散落在各种地方，为了方便查阅，在这里做一个收集。

<!-- more -->

## 2026 年

### C2-Ultra

- [Arm’s C2-Ultra, G2-Ultra NX, and CSS N4 IP](https://chipsandcheese.com/p/arms-c2-ultra-g2-ultra-nx-and-css)
    - More accurate prediction
    - Stronger instruction delivery
    - Faster recovery
    - Larger execution window
    - Smart speculation
    - Faster load availability
    - More memory operations in flight
    - Smarter prefetching
- [Arm® C2-Ultra Core Technical Reference Manual](https://support.arm.com/documentation/109736/0001/?lang=en)
    - 128-entry L1 ITLB
    - 96-entry L1 DTLB
    - 2048-entry L2 TLB
    - 64KB 4-way L1 ICache
    - 128KB 4-way L1 DCache
    - 2MB 8-way set associative with 4 banks or 3MB 12-way set associative with 4 banks L2 cache
    - The C2-Ultra core implements a scalable vector length of 128 bits
- [Arm® C2-Ultra Core Software Optimization Guide](https://support.arm.com/documentation/112421/3-0/?lang=en)
    - 3x Branch, 6x Integer Single Cycle, 2x Integer Single/Multi-Ccyle, 6x FP/SIMD, 2x Load/Store, 2x Load, 2x Store data
    - The dispatch stage can process up to 10 MOPs per cycle and dispatch up to 20 µOPs per cycle, with the following limitations on the number of µOPs of each type that may be simultaneously dispatched.
    - Up to 9 µOPs utilizing the S or B pipelines
    - Up to 3 µOPs utilizing the M pipelines
    - Up to 9 µOPs utilizing the V pipelines
    - Up to 8 µOPs utilizing the L pipelines
    - Dispatch of CME M OPs staying in-order are directly sent to the C pipeline. The C pipeline can receive up to 4 MOPs directly from the rename stage.
    - The C2 - Ultra core allows data to be forwarded from store instructions to a load instruction with the restrictions mentioned below:
    - Load start address should align with the start or middle address of the older store supported from a wider range of offsets. For 1B loads, forwarding is
    - Loads of size greater than 8 bytes can get the data forwarded from a maximum of 2 stores. If there are 2 stores, then each store should forward to either first or second half of the load
    - Loads of size less than or equal to 4 bytes can get their data forwarded from only 1 store

### C2-Pro

- [Arm C2 CPU cluster](https://www.arm.com/products/silicon-ip-cpu/c2-cpu-cluster)
    - The C2-Pro CPU leverages the same power-efficient microarchitecture as C1-Pro while implemented with the latest process technologies available on the market. 

### Neoverse N4

- [Arm’s C2-Ultra, G2-Ultra NX, and CSS N4 IP](https://chipsandcheese.com/p/arms-c2-ultra-g2-ultra-nx-and-css)
    - 64KB L1 I/D cache
    - 2MB L2 cache

## 2025 年

### C1-Ultra

- [Arm の新しい CPU「C1」は 2 桁パーセントの性能アップ。電力効率も大幅改善](https://pc.watch.impress.co.jp/docs/column/ubiq/2046162.html)
- [Inside Arm's New C1‑Ultra CPU: Double‑Digit IPC Gains Again!](https://www.youtube.com/watch?v=U1tPpV0RWNw)
    - C1-Ultra: successor to Cortex X925
    - Branch prediction: Additional tracking for local/per-PC history
    - 33% increase in L1 I-Cache available bandwidth
    - Out of order window size growth: Up to 25% growth, Up to ~2K instruction in flight
    - 2x L1 data cache capacity (128KB)
    - Data prefetchers: array-indexing coverage
- [Arm® C1-Ultra Core Technical Reference Manual](https://developer.arm.com/documentation/108014/latest/)
    - Implementation of the Scalable Vector Extension (SVE) with a 128-bit vector length and Scalable Vector Extension 2 (SVE2)
    - Implementation of the Scalable Matrix Extension (SME) and Scalable Matrix Extension 2 (SME2), and support for the C1-SME2 unit
    - configure the L2 cache to be 2048KB or 3072KB
    - A 64KB, 4-way set associative L1 instruction cache with 64-byte cache lines
    - A fully associative L1 instruction Translation Lookaside Buﬀer (TLB) with native support for 4KB, 16KB, 64KB, and 2MB page sizes
    - A 128KB, 4-way set associative cache with 64-byte cache lines
    - A fully associative L1 data TLB with native support for 4KB, 16KB, and 64KB page sizes and 2MB and 512MB block sizes
    - L2 cache is private to the core and can be configured to be 2MB 8-way set associative or 3MB 12-way set associative
    - L1 instruction TLB, Fully associative, 128 entries
    - L1 data TLB, Fully associative, 96 entries
    - L1 Statistical Profiling Extension (SPE) TLB, Located in the SPE block, VA to PA translations of any page and block size, 1 entry
    - L1 TRace Buﬀer Extension (TRBE) TLB, VA to PA translations of any page and block size, 1 entry
    - L2 TLB, Shared by instructions and data, 8-way set associative, 2048 entries
    - L1 instruction cache, 64KB, 4-way set associative, Virtually Indexed, Physically Tagged (VIPT) behaving as Physically Indexed, Physically Tagged (PIPT), Pseudo-Least Recently Used (LRU) cache replacement policy for L1, 32 bytes per cycle interface with L2
    - L1 data cache, 128KB, 4-way set associative, Virtually Indexed, Physically Tagged (VIPT) behaving as Physically Indexed, Physically Tagged (PIPT), Re-Reference Interval Prediction (RRIP) replacement policy, 4×64-bit read paths and 4×64-bit write paths for the integer execute pipeline, 4×128-bit read paths and 4×128-bit write paths for the vector execute pipeline
    - L2 cache, 2MB 8-way set associative with 4 banks or 3MB 12-way set associative with 4 banks, Physically Indexed, Physically Tagged (PIPT), Dynamic biased cache replacement policy, One CHI Issue E compliant interfaces with 256-bit read and write DAT channel widths
- [Arm® C1-Ultra Core Software Optimization Guide](https://developer.arm.com/documentation/111027/latest/)
    - 23 issue pipelines: 3x Branch, 6x Integer Single-Cycle, 2x Integer Single/Multi-Cycle, 6x FP/ASIMD, 2x Load/Store, 2x Load, 2x Store data
    - The dispatch stage can process up to 10 MOPs per cycle and dispatch up to 20 µOPs per cycle, with the following limitations on the number of µOPs of each type that may be simultaneously dispatched.
    - Up to 9 µOPs utilizing the S or B pipelines
    - Up to 3 µOPs utilizing the M pipelines
    - Up to 9 µOPs utilizing the V pipelines
    - Up to 8 µOPs utilizing the L pipelines
    - Dispatch of CME MOPs staying in-order are directly sent to the C pipeline. The C pipeline can receive up to 4 MOPs directly from the rename stage.
    - Implements FEAT_MOPS: memory copying (CPY*) up to 32 bytes/cycle, memset to 0 (SET*) up to 64 bytes/cycle, memset to non-zero up to 32 bytes/cycle

### C1-Premium

- [Arm® C1-Premium Core Technical Reference Manual](https://support.arm.com/documentation/109416/0001/?lang=en)
    - 128-bit SVE/SVE2 vector length
    - Implementation of the SME/SME2 and support for the C1-SME2 unit
    - L1 instruction cache, 64KB, 4-way set associative, 64-byte cache lines, VIPT behaving as PIPT, Pseudo-LRU cache replacement policy, 32 bytes per cycle interface with L2
    - L1 data cache, 64KB, 4-way set associative, 64-byte cache lines, VIPT behaving as PIPT, RRIP replacement policy, 4×64-bit read paths and 4×64-bit write paths for the integer execute pipeline, 4×128-bit read paths and 4×128-bit write paths for the vector execute pipeline
    - L2 cache, 1MB or 2MB 8-way set associative with 4 banks, PIPT, Dynamic biased cache replacement policy, One CHI Issue E compliant interface with 256-bit read and write DAT channel widths
    - L1 instruction TLB, Caches entries at the 4KB, 16KB, 64KB, or 2MB granularity only, Fully associative, 128 entries
    - L1 data TLB, Caches entries at the 4KB, 16KB, 64KB, 2MB, or 512MB granularity only, Fully associative, 96 entries
    - L2 TLB, Shared by instructions and data, 8-way set associative, 2048 entries

### C1-Pro

- [Arm Lumex C1-Pro CPU Core: What You Need to Know](https://www.youtube.com/watch?v=yUqEhahvAVE)
    - C1-Pro: successor to Cortex-A725
    - Larger direction predictor and branch history
    - 2x capacity 0-cycle BTB
    - 16x capacity 1-cycle BTB
    - 50% more L1 Instruction TLB capacity
    - Increase effective L1D cache bandwidth
    - Lower latency L2 TLB hit
    - New indirect prefetcher
- [Arm® C1-Pro Core Technical Reference Manual](https://support.arm.com/documentation/107771/0102/?lang=en)
    - L1 instruction cache, 32KB or 64KB, 4-way set associative, 64-byte cache lines, PIPT, PLRU cache replacement policy, 32 bytes per cycle interface with L2
    - L1 data cache, 32KB or 64KB, 4-way set associative, 16 banks, 64-byte cache lines, VIPT behaving as PIPT, PLRU cache replacement policy, 3×64-bit read paths and 4×64-bit write paths for the integer execute pipeline, 3×128-bit read paths and 2×128-bit write paths for the vector execute pipeline
    - L2 cache, 128KB-1024KB, 8-way set associative, 2 banks, PIPT, Dynamic biased cache replacement policy, One CHI Issue E compliant interface with 256-bit read and write channel widths
    - L1 instruction TLB, Caches entries at the 4KB, 16KB, 64KB, or 2MB granularity only, Fully associative, 48 entries
    - L1 data TLB, Caches entries at the 4KB, 16KB, 64KB, or 2MB granularity only, Fully associative, 48 entries
    - L2 TLB, Made of two translation caches: a Small page TLB (6-way, 1536 entries, or 4-way with reduced area, 1024 entries) and a Medium page TLB (4-way, 256 entries)

### C1-Nano

- [Arm® C1-Nano Core Technical Reference Manual](https://support.arm.com/documentation/107753/0002/?lang=en)
    - In-order pipeline with direct and indirect branch prediction
    - 128-bit SVE/SVE2 SIMD (optional 2×64-bit or 2×128-bit vector datapaths)
    - Optional SME/SME2 via the C1-SME2 unit
    - L1 instruction cache, 32KB or 64KB, 4-way set associative, 64-byte cache lines, VIPT behaving as PIPT, Pseudo-random cache replacement policy
    - L1 data cache, 32KB or 64KB, 4-way set associative, 64-byte cache lines, VIPT behaving as PIPT, Pseudo-random cache replacement policy, Dual 128-bit read path, 128-bit write path
    - L1 instruction TLB, Fully associative, 16 entries
    - L1 data TLB, Fully associative, 16 entries
    - L2 TLB, 8-way set associative, shared between cores of a dual-core complex
    - Optional unified L2 cache, 128KB, 192KB, 256KB, 384KB, or 512KB, 8-way set associative, PIPT, Dynamic biased cache replacement policy, weakly-exclusive with L1 data caches, weakly-inclusive with L1 instruction caches

## 2024 年

### Cortex X925

- [Arm Unveils 2024 CPU Core Designs, Cortex X925, A725 and A520: Arm v9.2 Redefined For 3nm](https://www.anandtech.com/show/21399/arm-unveils-2024-cpu-core-designs-cortex-x925-a725-and-a520-arm-v9-2-redefined-for-3nm-/2) [Archive](https://web.archive.org/web/20250626065356/https://www.anandtech.com/show/21399/arm-unveils-2024-cpu-core-designs-cortex-x925-a725-and-a520-arm-v9-2-redefined-for-3nm-/2)
    - Decode & Dispatch: 10-wide
    - SIMD/FP execution: 6x 128b
    - Integer ALU pipelines: 1- and 2-cycle operations
    - Integer multiply execution: 4x versus Cortex-X4
    - FP compare execution: 2x versus Cortex-X4
    - `>2x` increase in SIMD/FP issue queues
    - 2x increase in max instruction-window capacity（注：Cortex X4 是 384x2，推测 Cortex X925 是 768x2）
    - Sign-extension instruction elimination
    - Branch prediction: 2x instruction window size
    - Instruction Fetch: 2x increase in L1 I$ available bandwidth, 2x increase in L1 iTLB size, Fold out unconditional direct branches
    - 3 -> 4 load pipelines
    - 2x increase in L1 D$ available bandwidth
    - 25-40% in back-end OoO growth
- [Arm® Cortex-X925 Core Technical Reference Manual](https://developer.arm.com/documentation/102807/0001)
    - Implementation of the Scalable Vector Extension (SVE) with a 128-bit vector length and Scalable Vector Extension 2 (SVE2)
    - configure the L2 cache to be 2048KB or 3072KB
    - A 64KB, 4-way set associative L1 instruction cache with 64-byte cache lines
    - A fully associative L1 instruction Translation Lookaside Buﬀer (TLB) with native support for 4KB, 16KB, 64KB, and 2MB page sizes
    - A 64KB, 4-way set associative cache with 64-byte cache lines
    - A fully associative L1 data TLB with native support for 4KB, 16KB and 64KB page sizes and 2MB and 512MB block sizes
    - L2 cache is private to the core and can be configured to be 2MB 8-way set associative or 3MB 12-way set associative
    - L1 instruction TLB, Caches entries at the 4KB, 16KB, 64KB, or 2MB granularity of Virtual Address (VA) to Physical Address (PA) mapping only, Fully associative, 128 entries
    - L1 data TLB, Caches entries at the 4KB, 16KB, 64KB, 2MB, or 512MB granularity of VA to PA mappings only, Fully associative, 96 entries
    - L2 TLB, Shared by instructions and data, VA to PA mappings for 4KB, 16KB, 64KB, 2MB, 32MB, 512MB, and 1GB block sizes, Intermediate Physical Address (IPA) to PA mappings for: 2MB and 1GB block sizes in a 4KB translation granule, 32MB block size in a 16KB translation granule, 512MB block size in a 64KB granule; Intermediate PAs (descriptor PAs) obtained during a translation table walk, 8-way set associative, 2048 entries
    - L1 instruction cache, 64KB, 4-way set associative, Virtually Indexed, Physically Tagged (VIPT) behaving as Physically Indexed, Physically Tagged (PIPT)
    - The Cortex®-X925 core supports the AArch64 prefetch memory instructions, PRFM PLI, into the L1 instruction cache or L2 cache
    - L1 data cache, 64KB, 4-way set associative, Virtually Indexed, Physically Tagged (VIPT) behaving as Physically Indexed, Physically Tagged (PIPT), Re-Reference Interval Prediction (RRIP) replacement policy, 4×64-bit read paths and 4×64-bit write paths for the integer execute pipeline, 4×128-bit read paths and 4×128-bit write paths for the vector execute pipeline
    - L2 cache, 2MB 8-way set associative with 4 banks or 3MB 12-way set associative with 4 banks, Physically Indexed, Physically Tagged (PIPT)
- [Arm® Cortex-X925 Core Software Optimization Guide](https://developer.arm.com/documentation/109842/latest/)

### Neoverse V3

- [Arm® Neoverse™ V3 Core Technical Reference Manual](https://documentation-service.arm.com/static/65d62242c8cb3a42117cb7ba)
- [Arm AGI Hot Chips 2026 Neoverse IP Blocks](https://www.servethehome.com/arms-agi-data-center-cpu-at-hot-chips-2026/arm-agi-hot-chips-2026-neoverse-ip-blocks/)
    - 64KB ICache
    - 10-wide front end
    - 10-way decode
    - 384+ OoO window
    - 10-wide dispatch
    - 8-wide retire
    - 1LS + 2LD + 1ST per cycle
    - 64KB DCache
    - 8-ALU + 3-branch
    - Dual 128-bit low-latency datapath
    - 10-cycle load-to-use, 12B/cycle 2MB private L2
    - 32B DAT AMBA CHI

### Neoverse N3

- [Arm® Neoverse™ N3 Core Technical Reference Manual](https://documentation-service.arm.com/static/65d62242c8cb3a42117cb7ba)
    - L1 instruction cache, 32KB or 64KB, 4-way set associative, 64-byte cache lines, PIPT, PLRU cache replacement policy, 32 bytes per cycle interface with L2
    - L1 data cache, 32KB or 64KB, 4-way set associative, 16 banks, 64-byte cache lines, VIPT behaving as PIPT, LRU cache replacement policy, 3×64-bit read paths and 4×64-bit write paths for the integer execute pipeline, 3×128-bit read paths and 2×128-bit write paths for the vector execute pipeline
    - L2 cache, 128KB-2048KB, 8-way set associative, 2 banks, PIPT, Dynamic biased cache replacement policy, One CHI Issue E compliant interface with the DSU-120 (256-bit read and write channel widths)
    - L1 instruction TLB, Caches entries at the 4KB, 16KB, 64KB, or 2MB granularity only, Fully associative, 32 entries
    - L1 data TLB, Caches entries at the 4KB, 16KB, 64KB, or 2MB granularity only, Fully associative, 48 entries
    - L2 TLB, Made of two translation caches: a Small page TLB (6-way, 1536 entries, or 4-way with reduced area, 1024 entries) and a Medium page TLB (4-way, 256 entries)

## 2023 年

### Cortex X4

- [Arm Unveils 2023 Mobile CPU Core Designs: Cortex-X4, A720, and A520 - the Armv9.2 Family](https://www.anandtech.com/show/18871/arm-unveils-armv92-mobile-architecture-cortex-x4-a720-and-a520-64bit-exclusive/2) [Archive](https://web.archive.org/web/20250622110728/http://www4.anandtech.com/show/18871/arm-unveils-armv92-mobile-architecture-cortex-x4-a720-and-a520-64bit-exclusive/2)
    - Support for larger L2 (2M)
    - Dispatch width: 10 instrs vs Cortex-X3 (6 instrs `I$`, 8 instrs `Mop$`)
    - Overall pipeline depth (branch mispredict penalty): 10 cycles vs Cortex-X3 (11 cycles `I$`, 9 cycles `Mop$`)
    - ALUs: 8 vs 6 (Cortex-X3)
    - Branch units: 3 vs 2 (Cortex-X3)
    - Integer MAC: 2 vs 1 (Cortex-X3)
    - Pipelined FP divider / sqrt: Y vs N (Cortex-X3)
    - MCA capacity: 320x2 -> 384x2
    - 4th LS address generation: LS LS LD -> LS LD LD ST
    - New L1 temporal data prefetcher
    - Reduced L1 data bank conflicts
    - Larger L1 data TLB: 48 -> 96
- [Arm® Cortex-X4 Core Technical Reference Manual](https://developer.arm.com/documentation/102484/latest/)
    - L1 instruction cache, 64KB, 4-way set associative, 64-byte cache lines, VIPT behaving as PIPT, Pseudo-LRU cache replacement policy
    - L1 data cache, 64KB, 4-way set associative, 64-byte cache lines, VIPT behaving as PIPT, RRIP replacement policy, 4×64-bit read paths and 4×64-bit write paths for the integer execute pipeline, 3×128-bit read paths and 2×128-bit write paths for the vector execute pipeline
    - L2 cache, 512KB-2048KB, 8-way set associative with 4 banks, PIPT, Dynamic biased cache replacement policy, One CHI Issue E compliant interface with the DynamIQ Shared Unit-120 (256-bit read and write channel widths)
    - L1 instruction TLB, Caches entries at the 4KB, 16KB, 64KB, or 2MB granularity only, Fully associative, 48 entries
    - L1 data TLB, Caches entries at the 4KB, 16KB, 64KB, 2MB, or 512MB granularity only, Fully associative, 96 entries
    - L2 TLB, Shared by instructions and data, 8-way set associative, 2048 entries

### Cortex A720

- [Arm Unveils 2023 Mobile CPU Core Designs: Cortex-X4, A720, and A520 - the Armv9.2 Family](https://www.anandtech.com/show/18871/arm-unveils-armv92-mobile-architecture-cortex-x4-a720-and-a520-64bit-exclusive/3) [Archive](https://web.archive.org/web/20250522224324/https://www.anandtech.com/show/18871/arm-unveils-armv92-mobile-architecture-cortex-x4-a720-and-a520-64bit-exclusive/3)
    - 11-cycle mispredict penalty, vs 12 (Cortex-A715)
    - Improved 2-taken branch prediction
    - Pipelined FDIV/FSQRT unit
    - Faster transfers from Floating-Point/NEON/SVE2 to Integer
    - Earlier deallocation of mops from Load-Store Issue Queues
    - Lower latency for L2 cache hits, 9-cycle latency to access L2, vs 10 (Cortex-A715)
    - Up to 2x memset(0) bandwidth in L2
    - New L2 spatial-prefetch engine
- [Arm® Cortex-A720 Core Software Optimization Guide](https://developer.arm.com/documentation/109720/latest/)
    - Executes SVE2/SVE with a 128-bit vector length
    - 13 issue pipelines: 2x Branch, 2x Integer Single-Cycle, 2x Integer Single/Multi-Cycle, 2x FP/ASIMD/Vector Store data, 2x Load/Store, 1x Load, 2x Integer Store data
    - Each issue pipeline can accept one µOP per cycle

## 2022 年

### Cortex X3

- [Arm Unveils Next-Gen Flagship Core: Cortex-X3](https://fuse.wikichip.org/news/6855/arm-unveils-next-gen-flagship-core-cortex-x3/)
    - 50% larger L1 + L2 (new) BTB capacity
    - 10x larger L0 BTB capacity
    - New predictor dedicated for indirect branches
    - Double return-stack capacity (32 entries)
    - Mop cache 50% capacity (1.5K entries)
    - Removed 1 pipeline stage in Mop Cache fetch, 10->9 cycles for a branch mispredict
    - Increase decode bandwidth: 5->6
    - Integer ALUs increase 4->6: 2->4 single-cycle (SX), 2 single-/multi-cycle (MX)
    - ROB/MCQ: 288x2 -> 320x2
    - Integer load bandwdith: 24B -> 32B
    - Additional data prefetch engines: Spatial, Pointer/Indirect
- [Arm® Cortex‑X3 Core Technical Reference Manual](https://developer.arm.com/documentation/101593/latest/)

### Neoverse V2

- [Arm Neoverse V2 platform: Leadership Performance and Power Efficiency for Next-Generation Cloud Computing, ML and HPC Workloads](https://hc2023.hotchips.org/assets/program/conference/day1/CPU1/HC2023.Arm.MagnusBruce.v04.FINAL.pdf)
    - 6-wide/8-wide front-end
    - 64KB ICache
    - 320+ OoO window
    - 8-wide dispatch
    - 8-wide retire
    - 2 LS + 1 LD / cycle
    - 64KB DCache
    - 6-ALU + 2-branch
    - Quad 128-bit low latency SIMD datapath
    - L2 10-cycle load-to-use, 128B/cycle, private L2 cache 1 or 2 MB
    - Two predicted branches per cycle
    - Predictor acts as ICache prefetcher
    - 64kB, 4-way set-associative L1 instruction cache
    - Two-level Branch Target Buffer
    - 8 table TAGE direction predictor with staged output
    - 10x larger nanoBTB
    - Split main BTB into two levels with 50% more entries
    - TAGE: 2x larger tables with 2-way associativity, Longer history
    - Indirect branches: Dedicated predictor
    - Fetch bandwidth: Doubled instruction TLB and cache BW
    - Fetch Queue: Doubled from 16 to 32 entries
    - Fill Buffer: Increased size from 12 to 16 entries
    - Decode bandwidth: Increased decoder lanes from 5 to 6, Increased Decode Queue from 16 to 24 entries
    - Rename checkpoints: Increased from 5 to 6 total checkpoints, Increased from 3 to 5 vector checkpoints
    - Late read of physical register file – no data in IQs
    - Result caches with lazy writeback
    - Added two more single-cycle ALUs
    - Larger Issue Queues, SX/MX: Increased from 20 to 22 entries, VX: Increased from 20 to 28 entries
    - Predicate operations: Doubled predicate bandwidth
    - Zero latency MOV; Subset of register-register and immediate move operations execute with zero latency
    - Instruction fusion: More fusion cases, including CMP + CSEL/CSET
    - Two load/store pipes + one load pipe
    - 4 x 8B result busses (integer)
    - 3 x 16B result busses (FP, SVE, Neon)
    - ST to LD forwarding at L1 hit latency
    - RST and MB to reduce tag and data accesses
    - Fully-associative L1 DTLB with multiple page sizes
    - 64kB 4-way set associative Dcache
    - TLB Increased from 40 to 48 entries
    - Replacement policy Changed from PLRU to dynamic RRIP
    - Larger Queues: Store Buffer, ReadAfterRead, ReadAfterWrite
    - Efficiency: VA hash based store to load forwarding
    - Multiple prefetching engines training on L1 and L2 accesses: Spatial Memory Streaming, Best Offset, Stride, Correlated Miss Cache, Page
    - New PF engines: Global SMS – larger offsets than SMS, Sampling Indirect Prefetch – pointer dereference, TableWalk – Page Table Entrie
    - Private unified Level 2 cache, 8-way SA, 4 independent banks
    - 64B read or write per 2 cycles per bank = 128B/cycle total
    - 96-entry Transaction Queue
    - Inclusive with L1 caches for efficient data and instruction coherency
    - AMBA CHI interface with 256b DAT channels
    - Capacity 2MB/8-way with latency of 1MB (10-cycle ld-to-use)
    - Replacement policy 6-state RRIP (up from 4)
- [Hot Chips 2023: Arm’s Neoverse V2](https://chipsandcheese.com/p/hot-chips-2023-arms-neoverse-v2)
- [Arm® Neoverse™ V2 Core Technical Reference Manual](https://developer.arm.com/documentation/102375/latest/)
- [Arm Neoverse V2 Software Optimization Guide](https://developer.arm.com/documentation/109898/latest/)

## 2021 年

### Cortex X2

- [Cortex X2: Arm Aims High](https://chipsandcheese.com/2023/10/27/cortex-x2-arm-aims-high/)
- [Arm® Cortex®‑X2 Core Technical Reference Manual](https://developer.arm.com/documentation/101803/0200)
- [Arm Announces Mobile Armv9 CPU Microarchitectures: Cortex-X2, Cortex-A710 & Cortex-A510](https://www.anandtech.com/show/16693/arm-announces-mobile-armv9-cpu-microarchitectures-cortexx2-cortexa710-cortexa510/2)

### Neoverse N2

- [Arm Neoverse N2: Arm’s 2nd generation high performance infrastructure CPUs and system IPs](https://hc33.hotchips.org/assets/program/conference/day1/20210818_Hotchips_NeoverseN2.pdf)
    - Branch Prediction, 2x 8 instrs (up to 2 taken per cycle), 2x improvement
    - Nano BTB (0 cyc taken-branch bubble), 64 entry, 4x improvement
    - Conditional branch direction state, 1.5x improvement
    - Main BTB, 8K entry, 1.33x improvement
    - Alt-Path Branch Prediction
    - 64KB Instruction cache
    - 1.5K entry Mop Cache
    - 16-entry Fetch Queue, 1.33x improvement
    - Fetch Width: 4 instr from `i$`, 5 instr from `MOP$`, Up to 1.5x improvement
    - Early branch redirect: uncond + cond
    - Decode width: 4 (I-cache) or 5 (Mop cache), Up to 1.25x improvement
    - Branch predict up to 16-inst/cycle, 2-taken/cycle
    - New Macro-op (MOP) cache with 1.5k entries
    - 50% larger branch direction predicton
    - 33% larger BTB with shorter average latency
    - Early re-steering for conditional branches that miss the BTB
    - Rename width: 5 instrs, 1.2x improvement
    - Rename Checkpointing: Yes
    - ROB size: 160+, 1.25x improvement
    - ALUs: 4, 1.33x improvement
    - Branch resolution: 2 per cycle, 2x improvement
    - Overall Pipeline Depth: 10 cycles, 1.1x improvement
    - 64KB L1 Data cache
    - Private 512KB/1MB L2 Cache
    - AGU: 2-LD/ST + 1 LD, 1.5x improvement
    - L1 LD Hit bandwidth: 3x 16B/cycle, 1.5x improvement
    - Store data B/W: 32B/cycle, 2x improvement
    - L2 bandwidth: 64B read + 64B write, 2x improvement
    - L2 transactions: 64, 1.3x improvement
    - Data Prefetch Engines: Stride, spatial/region, stream, temporal
    - Correlated Miss Caching (CMC) prefetching

## 2020 年

### Neoverse V1

- [SW defined cars: HPC, from the cloud to the dashboard for an amazing driver experience](https://teratec.eu/library/pdf/forum/2021/A05-03.pdf)
    - Faster run-ahead for prefetching into the I$ (2x32B bandwidth)
    - 33% larger BTBs (8K entry)
    - 6x nano BTB (96 entry), zero-cycle bubble
    - 2x number of concurrent code regions tracked in front-end
    - Introduction of Mop Cache, L0 decoded instruction cache (3K entry)
    - high dispatch bandwidth, 8-instrs per cycle, 2x increase, I$ decode bandwidth increased from 4x to 5x
    - Lower latency decode pipeline by 1 stage
    - OoO window size, 2x+ ROB (256 entry + compression)
    - Increase superscalar integer execution bandwidth, 1->2 Branch Execution, 3->4 ALU
    - 2x vector/fp bandwidth, 2x256b – SVE (new), 4x128b – Neon/FP
    - 3rd LD AGU/pipe (50% incr), LS LS LD
    - LD/ST data bandwidth, LD: 2x16B -> 3x16B, LD (SVE): 2x32B, ST: 16B -> 32B (2x), broken out into separate issue pipes
    - Number of outstanding external memory transactions (48->96)
    - MMU capacity 1.2K->2K entry (67% incr)
    - L2 latency reduced by 1 cycle for 1M (now 10cyc load to use)
    - 11+ stage accordion pipeline
    - 8-wide front-end / 15-wide issue
    - Four 64-bit integer ALUs + two dedicated Branch units
    - 2x 256-bit SVE datapaths
    - 4x 128-bit Neon/FP datapaths
    - 3x load / store addr
    - 3x load data & 2x store data pipeline
    - 8-wide Instruction fetch
    - 5-8 wide decode / rename
    - pipeline: P1 P2 F1 F2 DE1 RR RD I0 I1 I2 ...

### Cortex X1

- [Arm's New Cortex-A78 and Cortex-X1 Microarchitectures: An Efficiency and Performance Divergence](https://www.anandtech.com/show/15813/arm-cortex-a78-cortex-x1-cpu-ip-diverging/3) [Archive](https://web.archive.org/web/20250716133719/https://www.anandtech.com/show/15813/arm-cortex-a78-cortex-x1-cpu-ip-diverging/3)
    - 50% larger L0-BTB capacity, 96 entries, zero-cycle bubble taken-branch latency
    - Increased fetch bandwidth available, 5 instruction fetch from the instruction cache, 8 Mop fetch from the Mop cache
    - 2x Mop cache capacity over Cortex-A77, 3K entries
    - 33% increase in dispatch bandwidth, up to 8-instr/cycle
    - 40% increase in out-of-order window size, 224 entry instruction window
    - 2x FP/ASIMD execution bandwidth, 4x128b total bandwidth
    - Doubling available L1-D, L2 bandwidth
    - Doubleing of maximum L2 capacity
    - Up to 33% increase in window growth for in-flight loads and stores
    - 66% larger L2-TLB capacity, 2K entries
- [Arm Cortex-X1: The First From The Cortex-X Custom Program](https://fuse.wikichip.org/news/3543/arm-cortex-x1-the-first-from-the-cortex-x-custom-program/)
- [Arm® Cortex®‑X1 Core Technical Reference Manual](https://developer.arm.com/documentation/101433/0102)

### Cortex A78

- [Arm's New Cortex-A78 and Cortex-X1 Microarchitectures: An Efficiency and Performance Divergence](https://www.anandtech.com/show/15813/arm-cortex-a78-cortex-x1-cpu-ip-diverging/2) [Archive](https://web.archive.org/web/20250529000334/https://www.anandtech.com/show/15813/arm-cortex-a78-cortex-x1-cpu-ip-diverging/2)
    - Expand prediction support to 2 taken branches per cycles
    - Additional IMUL bandwidth, up to 2x per cycle
    - 50% increase in load bandwidth over Cortex-A77, additional load AGU / result
    - Double store-data bandwidth, 32B per cycle
    - Double L2 interface bandwidth

## 2019 年

### Neoverse N1

- [The Arm Neoverse N1 Platform: Building Blocks for the Next-Gen Cloud-to-Edge Infrastructure SoC](https://www.arm.com/-/media/global/solutions/infrastructure/arm-neoverse-n1-platform.pdf)
    - 4-wide front-end
    - dispatching/committing up to 8 instructions per cycle
    - three ALUs, a branch execution unit, two Advanced SIMD units, and two load/store execution units
    - minimum misprediction penalty is 11-cycle
    - fetch up to 4 instructions per cycle
    - large 6K-entry main branch target buffer with 3-cycle access latency
    - 64-entry micro-BTB and a 16-entry nano-BTB
    - 12-entry fetch queue
    - fully associative 48-entry instruction TLB
    - 4-way set-associative 64KB I-cache
    - I-cache can deliver up to 16B of instructions per cycle
    - up to 8 outstanding I-cache refill requests
    - 4-wide decoder
    - renaming unit can receive up to 4 macro-ops per cycle
    - up to 8 micro-operations can be dispatched into the out-of-order engine each cycle
    - The commit queue can track up to 128 micro operations
    - up to 8 micro-ops can be committed per cycle
    - a distributed issue queue with more than 100 micro-operations
    - 4 integer execution pipelines, 2 load/store pipelines, and 2 Advanced SIMD pipelines
    - 64kB 4-way set associative L1 data cache, 4-cycle load to use latency and a bandwidth of 32 bytes/cycle
    - The core-private 8-way set associative L2 cache is up to 1MB in size and has a load-to-use latency of 11 cycles
    - can also be configured with smaller L2 cache sizes of 256kB and 512kB with a load-to-use latency of 9 cycles
    - L2 cache connects to the system via an AMBA 5 CHI interface with 16-byte data channels
    - L3 cluster cache can be up to 2MB, with a load-to-use latency ranging between 28 and 33 cycles
    - up to 256MB of shared system-level cache



