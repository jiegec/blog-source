---
layout: post
date: 2026-05-29
tags: [benchmark,spec]
draft: true
categories:
    - software
---

# SPEC CPU 2026 负载特性分析（FP Rate 篇）

## 背景

既 [INT Rate 篇](./spec-cpu-2026-workload-analysis-int-rate.md) 后，转到分析 SPEC FP 2026 Rate 的负载特性。

<!-- more -->

测试环境与先前的 [INT Rate 篇](./spec-cpu-2026-workload-analysis-int-rate.md) 相同，这里不再赘述。

推荐阅读：[Evaluating SPEC CPU2026](https://chipsandcheese.com/p/evaluating-spec-cpu2026) 和 [SPEC CPU2026: Characterization, Representativeness, and Cross-Suite Comparison](https://arxiv.org/abs/2605.03713v2)

## SPEC FP 2026 Rate 分析

### 709.cactus_r

Cactus 是一个计算框架，这里用它来求解真空中的爱因斯坦方程。命令参数如下：

```shell
cactus ShiftedGaugeWave.par
```

实测数据显示，运行时间 103.4s，reftime 是 858s，对应 8.30 分。不同编译器和编译选项对 709.cactus_r 的优化情况：

- GCC 14 `-O3 -march=native`，运行时间 83.9s，对应 10.23 分，相比 GCC 14 `-O3` 提升 23%；
- GCC 14 `-O3 -ffast-math`，运行时间 101.2s，对应 8.48 分，相比 GCC 14 `-O3` 提升 2%；
- GCC 14 `-O3 -ljemalloc`，运行时间 100.7s，对应 8.52 分，相比 GCC 14 `-O3` 提升 3%；
- LLVM 22 `-O3`，运行时间 94.6s，对应 9.07 分，相比 GCC 14 `-O3` 提升 9%；
- LLVM 22 `-O3 -march=native`，运行时间 90.5s，对应 9.48 分，相比 GCC 14 `-O3` 提升 14%。

可见 `-march=native` 能提供巨大的性能提升。

通过 `perf` 观察性能瓶颈：

- `ML_CCZ4::ML_CCZ4_EvolutionInteriorSplitBy2_Body` 来自 `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_EvolutionInteriorSplitBy2.cc`：41.30%；
- `ML_CCZ4::ML_CCZ4_EvolutionInteriorSplitBy3_Body` 来自 `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_EvolutionInteriorSplitBy3.cc`：31.26%；
- `ML_CCZ4::ML_CCZ4_ConstraintsInterior_Body` 来自 `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_ConstraintsInterior_Body.cc`：6.71%；
- `ML_CCZ4::ML_CCZ4_EvolutionInteriorSplitBy1_Body` 来自 `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_EvolutionInteriorSplitBy3.cc`：6.44%。

这些热点函数的代码模式都是类似的：在三层循环里，读取对应三维空间中的点的数据，进行一系列的 Stencil 访存和浮点运算，包括大量的浮点乘法加法减法、pow 和 fabs，最后把结果写入对应数组。从指令来看，就是用大量的 SSE 指令来进行标量的双精度浮点运算，没有进行向量化。实验的时候，还观察到了编译器对 `pow` 和 `fabs` 的优化。在 `-O3` 时，`pow(a, 1)` 被编译成 `a`，`pow(a, 2)` 被编译成 `a * a`，`pow(a, -1)` 被编译成 `1.0 / a`，不过其他的例如 `pow(a, 3)` 和 `pow(a, -2)` 就只能转为 `libm` 的 `pow` 实现了。如果开了 `-O3 -ffast-math`，那么 `pow(a, 3)` 会编译成 `a * a * a`，`pow(a, -2)` 会被编译为 `1.0 / (a * a)`。两种编译选项的对比见 [Godbolt](https://godbolt.org/z/nKfGMfE49)。代码中，出现的主要就是 `pow(a, -1)`，`pow(a, 2)`、`pow(a, -2)` 和 `pow(a, runtimeVariable)`，其中 `runtimeVariable` 指一个在运行时才知道的数，在代码中对应 `shiftAlphaPower` 或 `harmonicN`。`fabs` 被编译成了位运算 `andpd` 指令，直接把符号位置零。

开启 `-O3 -march=native` 后，其实依然没有向量化，用 AVX2 指令计算双精度标量浮点，依然能看到对 `libm` 的 `pow` 的调用，就是上面提到的 `pow(a, -2)` 或 `pow(a, runtimeVariable)`，不过其余的计算部分因为能用 [`vfmadd132sd`](https://www.felixcloutier.com/x86/vfmadd132sd:vfmadd213sd:vfmadd231sd)/`vfnmadd132sd` 而获得了性能提升，同时 [`vaddsd`](https://www.felixcloutier.com/x86/addsd) 相比 [`addsd`](https://www.felixcloutier.com/x86/addsd) 从两操作数变为三操作数，还允许访存，进一步节省了指令数。而在 ARM64 平台上，开 `-march=native` 就没有性能提升，这是因为它的浮点乘加融合指令即使在没开 `-march=native` 的情况下也是可以使用的，见 [Godbolt](https://godbolt.org/z/nqMjY4EoY)。

不同编译选项的情况对比：

| 编译器+选项                 | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|
| GCC 14 `-O3`                | 103.4    | 1423.6B  | 747.8B   | 110.1B    | 9.8B     | 677.0B       | 5.2B         |
| GCC 14 `-O3 -march=native`  | 83.9     | 988.5B   | 711.9B   | 89.5B     | 8.9B     | 686.1B       | 2.6B         |
| GCC 14 `-O3 -ffast-math`    | 101.8    | 1387.7B  | 742.2B   | 103.4B    | 5.3B     | 641.0B       | 5.6B         |
| GCC 14 `-O3 -ljemalloc`     | 100.7    | 1423.6B  | 747.8B   | 110.1B    | 9.8B     | 677.0B       | 5.2B         |
| LLVM 22 `-O3`               | 94.6     | 1323.1B  | 659.1B   | 96.6B     | 6.1B     | 659.0B       | 15.2B        |
| LLVM 22 `-O3 -march=native` | 90.5     | 1054.5B  | 690.7B   | 119.4B    | 5.4B     | 681.4B       | 5.4B         |

其中总指令数来自 `instructions`，Load 指令数来自 `mem_inst_retired.all_loads`，Store 指令数来自 `mem_inst_retired.all_stores`，分支指令数来自 `branch-instructions`，浮点标量指令数用 `fp_arith_inst_retired.scalar` 浮点向量指令数用 `fp_arith_inst_retired.vector` 性能计数器，下同。需要注意的是，`vfmadd132sd` 等乘加融合指令在 `fp_arith_inst_retired.scalar/vector` 计数器中会被计算两次。

从表里可以看出，`-O3` 下基本是一半指令在 Load，另一半指令在做浮点标量运算，这个计算访存比还是挺低的，这是 Stencil 计算的典型特征，在网格邻域里，Load 一个值进来，做一次乘加。开 `-O3 -march=native` 后，因为乘加融合指令的加持，指令数减少了很多，但因为乘加融合会算两倍的贡献，并且那些同时进行访存和计算的 AVX2 指令也会被同时计入到 Load 和浮点指令数，估计微架构是统计的拆分后的微码数量，那么总指令数不再等于各类指令数求和。这里 `-O3 -ljemalloc` 带来了些许的性能优势，不过指令数上并没有体现，不确定它的性能提升主要是来自哪里。GCC 14 和 LLVM 22 在不同编译选项下各有千秋，大概看了一下生成的指令，其实实现方法都差不多，主要是地址计算、栈的使用和寄存器分配有一些区别。

### 722.palm_r

palm 是一个天气预报相关的程序，做的是 Navier Stokes 方程的求解，命令如下：

```shell
palm_r < runfile_atmos
```

实测数据显示，运行时间 174.0s，reftime 是 1320s，对应 7.59 分。不同编译器和编译选项对 722.palm_r 的优化情况：

- GCC 14 `-O3 -march=native`，运行时间 157.8s，对应 8.34 分，相比 GCC 14 `-O3` 提升 10%；
- GCC 14 `-O3 -ffast-math`，运行时间 168.4s，对应 7.84 分，相比 GCC 14 `-O3` 提升 3%；
- GCC 14 `-O3 -ljemalloc`，运行时间 172.4s，对应 7.66 分，相比 GCC 14 `-O3` 提升 1%；
- LLVM 22 `-O3`，运行时间 144.0s，对应 9.17 分，相比 GCC 14 `-O3` 提升 21%；
- LLVM 22 `-O3 -march=native`，运行时间 118.6s，对应 10.37 分，相比 GCC 14 `-O3` 提升 47%。

可见 `-march=native` 能提供巨大的性能提升，而 LLVM 22 也明显比 GCC 14 要快。

热点函数：

- `advec_s_ws_ij` 来自 `src/advec_ws.F90`：9.80%，经典的 3 维上的 Stencil 计算，访存和计算的比例接近，基本是 load 一个点的数值然后就做对应的乘加，用 SSE 指令来做计算，有部分向量化计算，例如 addpd/subpd/mulpd 等，每条指令处理 2 个双精度浮点元素，不过也有一些循环没能成功向量化，退化到 addsd/subsd/mulsd 等浮点标量指令；
- `advec_u_ws_ij` 来自 `src/advec_ws.F90`：8.80%，同上；
- `advec_v_ws_ij` 来自 `src/advec_ws.F90`：8.54%，同上；
- `advec_w_ws_ij` 来自 `src/advec_ws.F90`：8.24%，同上；
- `diffusion_e_ij` 来自 `src/turbulence_closure_mod.F90`：5.14%，有一些比较复杂的浮点运算，比如 min/sqrt/div 等等，还有位运算，用 `MERGE` 来进行 ternary operator，无向量化，用 SSE 指令来做标量浮点计算。

不同编译选项的情况对比：

| 编译器+选项                 | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|
| GCC 14 `-O3`                | 174.0    | 3416.6B  | 1267.4B  | 271.1B    | 155.6B   | 779.0B       | 318.5B       |
| GCC 14 `-O3 -march=native`  | 157.8    | 2710.0B  | 1212.8B  | 242.5B    | 147.1B   | 785.9B       | 172.6B       |
| GCC 14 `-O3 -ffast-math`    | 168.4    | 3373.5B  | 1204.7B  | 278.0B    | 134.0B   | 612.8B       | 363.1B       |
| GCC 14 `-O3 -ljemalloc`     | 172.4    | 3368.4B  | 1259.7B  | 260.7B    | 141.6B   | 779.0B       | 318.5B       |
| LLVM 22 `-O3`               | 144.0    | 2640.4B  | 835.5B   | 216.3B    | 90.4B    | 179.5B       | 609.7B       |
| LLVM 22 `-O3 -march=native` | 118.6    | 1643.8B  | 586.5B   | 165.6B    | 67.6B    | 180.8B       | 306.7B       |

开 `-O3 -march=native` 后，能看到的是大量的 AVX2 向量化指令：vmulpd/vdivsd/vaddpd/vsubpd/vfmadd213sd/vfmsub132pd/vfmsub231pd/vmovupd 等等，每次处理 4 个双精度浮点元素，向量化程度很高，如果在有 AVX512 的处理器上，可能性能还会更高。相比 709.cactus_r 那样被 pow 等问题限制没能向量化，722.palm_r 的向量化收益是特别明显的。LLVM 22 在 `-O3` 下比 GCC 14 要好，是因为它在热点函数的更多部分成功进行向量化，体现在数据上就是浮点向量指令数明显增多，浮点标量指令数明显减少。在 LLVM 22 下，由于上述热点函数被优化地比较好，也出现了新的热点函数，时间占比 5.79%：`flow_statistics` 来自 `src/flow_statistics.F90`，它能正确向量化的部分比较少，因而时间占比提升，即使开了 `-O3 -march=native`，也还是用 AVX2+FMA 指令来做标量计算，时间区别不大，因为其他部分时间降低，自己的时间占比提高到 6.95%。