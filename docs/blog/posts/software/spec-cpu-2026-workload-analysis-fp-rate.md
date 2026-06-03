---
layout: post
date: 2026-05-29
tags: [benchmark,spec,speccpu2026]
categories:
    - software
---

# SPEC CPU 2026 负载特性分析（FP Rate 篇）

## 背景

继 [INT Rate 篇](./spec-cpu-2026-workload-analysis-int-rate.md) 后，本文继续分析 SPEC FP 2026 Rate 的负载特性。

<!-- more -->

测试环境与先前的 [INT Rate 篇](./spec-cpu-2026-workload-analysis-int-rate.md) 相同，这里不再赘述。

推荐阅读：[Evaluating SPEC CPU2026](https://chipsandcheese.com/p/evaluating-spec-cpu2026) 和 [SPEC CPU2026: Characterization, Representativeness, and Cross-Suite Comparison](https://arxiv.org/abs/2605.03713v2)

## SPEC FP 2026 Rate 分析

### 709.cactus_r

Cactus 是一个计算框架，这里用它来求解真空中的爱因斯坦方程。命令参数如下：

```shell
cactus ShiftedGaugeWave.par
```

实测数据显示，运行时间为 103.4s，reftime 是 858s，对应 8.30 分。不同编译器和编译选项对 709.cactus_r 的优化情况如下：

| 编译器 + 选项               | 时间 (s) | 分数  | 相比 GCC 14 `-O3` 性能提升 (%) |
|-----------------------------|----------|-------|--------------------------------|
| GCC 14 `-O3`                | 103.4    | 8.30  | 0                              |
| GCC 14 `-O3 -march=native`  | 83.9     | 10.23 | 23                             |
| GCC 14 `-O3 -ffast-math`    | 101.2    | 8.48  | 2                              |
| GCC 14 `-O3 -ljemalloc`     | 100.7    | 8.52  | 3                              |
| LLVM 22 `-O3`               | 94.6     | 9.07  | 9                              |
| LLVM 22 `-O3 -march=native` | 90.5     | 9.48  | 14                             |

可见 `-march=native` 能提供巨大的性能提升，LLVM 22 在 `-O3` 下比 GCC 14 快，不过 GCC 14 的 `-O3 -march=native` 又反超了 LLVM 22 的 `-O3 -march=native`，后面会具体分析。

通过 `perf` 观察性能瓶颈：

- `ML_CCZ4::ML_CCZ4_EvolutionInteriorSplitBy2_Body` 来自 `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_EvolutionInteriorSplitBy2.cc`：占总时间 41.30%，下同；
- `ML_CCZ4::ML_CCZ4_EvolutionInteriorSplitBy3_Body` 来自 `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_EvolutionInteriorSplitBy3.cc`：31.26%；
- `ML_CCZ4::ML_CCZ4_ConstraintsInterior_Body` 来自 `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_ConstraintsInterior_Body.cc`：6.71%；
- `ML_CCZ4::ML_CCZ4_EvolutionInteriorSplitBy1_Body` 来自 `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_EvolutionInteriorSplitBy3.cc`：6.44%。

这些热点函数的代码模式都是类似的：在三层循环里，读取对应三维空间中的点的数据，进行一系列的 Stencil 访存和浮点运算，包括大量的浮点乘法加法减法、pow 和 fabs，最后把结果写入对应数组。从指令来看，就是用大量的 SSE 指令来进行标量的双精度浮点运算，没有进行向量化。实验的时候，还观察到了编译器对 `pow` 和 `fabs` 的优化。在 `-O3` 时，`pow(a, 1)` 被编译成 `a`，`pow(a, 2)` 被编译成 `a * a`，`pow(a, -1)` 被编译成 `1.0 / a`，不过其他的例如 `pow(a, 3)` 和 `pow(a, -2)` 就只能转为 `libm` 的 `pow` 实现了。如果开了 `-O3 -ffast-math`，那么 `pow(a, 3)` 会编译成 `a * a * a`，`pow(a, -2)` 会被编译为 `1.0 / (a * a)`。两种编译选项的对比见 [Godbolt](https://godbolt.org/z/nKfGMfE49)。代码中，出现的主要就是 `pow(a, -1)`，`pow(a, 2)`、`pow(a, -2)` 和 `pow(a, runtimeVariable)`，其中 `runtimeVariable` 指一个在运行时才知道的数，在代码中对应 `shiftAlphaPower` 或 `harmonicN`。`fabs` 被编译成了位运算 `andpd` 指令，直接把符号位置零。

开启 `-O3 -march=native` 后，其实依然没有向量化，用 AVX2 指令计算双精度标量浮点，依然能看到对 `libm` 的 `pow` 的调用，就是上面提到的 `pow(a, -2)` 或 `pow(a, runtimeVariable)`，不过其余的计算部分因为能用 [`vfmadd132sd`](https://www.felixcloutier.com/x86/vfmadd132sd:vfmadd213sd:vfmadd231sd)/`vfnmadd132sd` 而获得了性能提升，同时 [`vaddsd`](https://www.felixcloutier.com/x86/addsd) 相比 [`addsd`](https://www.felixcloutier.com/x86/addsd) 从两操作数变为三操作数，还允许访存，进一步节省了指令数。而在 ARM64 平台上，开 `-march=native` 就没有性能提升，这是因为它的浮点乘加融合指令即使在没开 `-march=native` 的情况下也是可以使用的，见 [Godbolt](https://godbolt.org/z/nqMjY4EoY)。某种意义上来说，AMD64 上开 `-march=native` 有性能巨大提升，也是吃了先发劣势的亏：基线对应的处理器太早，缺少很多重要的指令集扩展，这种兼容性负担在很多其他指令集上不会出现，例如乘加融合 FMA 指令很多指令集里已经在基线当中，在这些指令集上，开 `-march=native` 的提升就会相对来说更低。所以现在很多软件会曲线救国，为了保证兼容性，针对多个不同指令集扩展分别做手动适配，在运行时根据可用性选择性能最好的那一个。如果编译器能很好地自动完成这一点，将会在保持兼容性和开发便捷性的前提下，带来不错的系统整体性能提升。

不同编译选项的情况对比：

| 编译器 + 选项               | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|
| GCC 14 `-O3`                | 103.4    | 1423.6   | 747.8    | 110.1     | 9.8      | 677.0        | 5.2          |
| GCC 14 `-O3 -march=native`  | 83.9     | 988.5    | 711.9    | 89.5      | 8.9      | 686.1        | 2.6          |
| GCC 14 `-O3 -ffast-math`    | 101.8    | 1387.7   | 742.2    | 103.4     | 5.3      | 641.0        | 5.6          |
| GCC 14 `-O3 -ljemalloc`     | 100.7    | 1423.6   | 747.8    | 110.1     | 9.8      | 677.0        | 5.2          |
| LLVM 22 `-O3`               | 94.6     | 1323.1   | 659.1    | 96.6      | 6.1      | 659.0        | 15.2         |
| LLVM 22 `-O3 -march=native` | 90.5     | 1054.5   | 690.7    | 119.4     | 5.4      | 681.4        | 5.4          |

其中总指令数来自 `instructions`，Load 指令数来自 `mem_inst_retired.all_loads`，Store 指令数来自 `mem_inst_retired.all_stores`，分支指令数来自 `branch-instructions`，浮点标量指令数用 `fp_arith_inst_retired.scalar`，浮点向量指令数用 `fp_arith_inst_retired.vector` 性能计数器，下同。需要注意的是，`vfmadd132sd` 等乘加融合指令在 `fp_arith_inst_retired.scalar/vector` 计数器中会被计算两次。

从表里可以看出，`-O3` 下基本是一半指令在 Load，另一半指令在做浮点标量运算，这个计算访存比还是挺低的，这是 Stencil 计算的典型特征，在网格邻域里，Load 一个值进来，做一次乘加。开 `-O3 -march=native` 后，因为乘加融合指令的加持，指令数减少了很多，但因为乘加融合会算两倍的贡献，并且那些同时进行访存和计算的 AVX2 指令也会被同时计入到 Load 和浮点指令数，估计微架构是统计的拆分后的微码数量，那么总指令数不再等于各类指令数求和。这里 `-O3 -ljemalloc` 带来了些许的性能优势，不过指令数上并没有体现，它的性能提升主要是来自缓存局部性的改进。GCC 14 和 LLVM 22 在不同编译选项下各有千秋，大概看了一下生成的指令，其实实现方法都差不多，主要是地址计算、栈的使用和寄存器分配有一些区别。

值得注意的是，709.cactus_r 的缓存缺失率较高：GCC 14 `-O3` 下，L1 ICache 的 MPKI 达到 `118.6B/1423.6B*1000=83.30`，L1 DCache 也有 `125.6B/1423.6B*1000=88.23` 的 MPKI，在 SPEC FP 2026 Rate 和 SPEC INT 2026 Rate 中都是最高的。因此 L1 ICache 更大的核心更占优势，32KB 时遇到的 L1 ICache 瓶颈，换成 64KB 可能就消失了。开 `-O3 -ljemalloc` 后，L1 DCache 的 MPKI 降低到 `111.7B/1423.6B*1000=78.46`，在指令数与 `-O3` 持平的情况下获得了约 3% 的性能提升。

### 722.palm_r

palm 是一个天气预报相关的程序，做的是 Navier Stokes 方程的求解，命令如下：

```shell
palm_r < runfile_atmos
```

实测数据显示，运行时间为 174.0s，reftime 是 1320s，对应 7.59 分。不同编译器和编译选项对 722.palm_r 的优化情况：

| 编译器 + 选项               | 时间 (s) | 分数  | 相比 GCC 14 `-O3` 性能提升 (%) |
|-----------------------------|----------|-------|--------------------------------|
| GCC 14 `-O3`                | 174.0    | 7.59  | 0                              |
| GCC 14 `-O3 -march=native`  | 157.8    | 8.34  | 10                             |
| GCC 14 `-O3 -ffast-math`    | 168.4    | 7.84  | 3                              |
| GCC 14 `-O3 -ljemalloc`     | 172.4    | 7.66  | 1                              |
| LLVM 22 `-O3`               | 144.0    | 9.17  | 21                             |
| LLVM 22 `-O3 -march=native` | 118.6    | 11.13 | 47                             |

趋势和 709.cactus_r 类似，`-O3 -march=native` 对性能提升巨大，LLVM 22 也明显比 GCC 14 快。

热点函数：

- `advec_s_ws_ij` 来自 `src/advec_ws.F90`：9.80%，经典的 3 维上的 Stencil 计算，访存和计算的比例接近，基本是 load 一个点的数值然后就做对应的乘加，用 SSE 指令来做计算，有部分向量化计算，例如 addpd/subpd/mulpd 等，每条指令处理 2 个双精度浮点元素，不过也有一些循环没能成功向量化，退化到 addsd/subsd/mulsd 等浮点标量指令；
- `advec_u_ws_ij` 来自 `src/advec_ws.F90`：8.80%，同上；
- `advec_v_ws_ij` 来自 `src/advec_ws.F90`：8.54%，同上；
- `advec_w_ws_ij` 来自 `src/advec_ws.F90`：8.24%，同上；
- `diffusion_e_ij` 来自 `src/turbulence_closure_mod.F90`：5.14%，有一些比较复杂的浮点运算，比如 min/sqrt/div 等等，还有位运算，用 `MERGE` 来进行 ternary operator，无向量化，用 SSE 指令来做标量浮点计算。

以下是 `advec_s_ws_ij` 中的 Stencil 计算代码，按 i,j,k 的顺序进行三层循环：

```fortran
flux_r(k) = u_comp * (                                                                &
              37.0_wp * ( sk(k,j,i+1) + sk(k,j,i)   )                                 &
            -  8.0_wp * ( sk(k,j,i+2) + sk(k,j,i-1) )                                 &
            +           ( sk(k,j,i+3) + sk(k,j,i-2) ) ) * adv_sca_5
```

不同编译选项的情况对比：

| 编译器 + 选项               | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|
| GCC 14 `-O3`                | 174.0    | 3416.6   | 1267.4   | 271.1     | 155.6    | 779.0        | 318.5        |
| GCC 14 `-O3 -march=native`  | 157.8    | 2710.0   | 1212.8   | 242.5     | 147.1    | 785.9        | 172.6        |
| GCC 14 `-O3 -ffast-math`    | 168.4    | 3373.5   | 1204.7   | 278.0     | 134.0    | 612.8        | 363.1        |
| GCC 14 `-O3 -ljemalloc`     | 172.4    | 3368.4   | 1259.7   | 260.7     | 141.6    | 779.0        | 318.5        |
| LLVM 22 `-O3`               | 144.0    | 2640.4   | 835.5    | 216.3     | 90.4     | 179.5        | 609.7        |
| LLVM 22 `-O3 -march=native` | 118.6    | 1643.8   | 586.5    | 165.6     | 67.6     | 180.8        | 306.7        |

开 `-O3 -march=native` 后，能看到大量的 AVX2 向量化指令：vmulpd/vdivsd/vaddpd/vsubpd/vfmadd213sd/vfmsub132pd/vfmsub231pd/vmovupd 等等，每次处理 4 个双精度浮点元素，向量化程度很高，如果放在支持 AVX512 的处理器上，性能可能还会更高。相比 709.cactus_r 被 pow 等问题限制没能向量化，722.palm_r 的向量化收益要明显得多。LLVM 22 在 `-O3` 下比 GCC 14 更好，是因为它在热点函数如 `advec_u/v/w_ws_ij` 中成功进行了向量化，而 GCC 14 仍用标量，体现在数据上就是浮点向量指令数明显增多，浮点标量指令数明显减少。LLVM 22 下，上述热点函数被优化得较好后，`flow_statistics`（来自 `src/flow_statistics.F90`，时间占比 5.79%）成为了新的热点函数。它能向量化的部分比较少，因而时间占比提升。即使开了 `-O3 -march=native`，也还是用 AVX2+FMA 指令来做标量计算，时间区别不大。其他部分时间降低后，它的时间占比进一步提高到 6.95%，类似 Amdahl 定律。

709.cactus_r 和 722.palm_r 的计算模式其实都是 Stencil。物理相关的模拟经常做这类事情：在三维空间里求解微分方程，数值求解时需要对每个点的邻域进行反复计算，落到最后就是 Stencil。

### 731.astcenc_r

astcenc 是一个针对 ASTC 有损压缩图片格式的编码器，运行三次，命令如下：

```shell
# 1. linear
astcenc_r ref-inputs-linear.txt
# 2. hdr
astcenc_r ref-inputs-hdr.txt
# 3. precision
astcenc_r ref-inputs-precision.txt
```

实测运行时间为 49.9s、72.1s 和 53.8s，总时间 175.8s，reftime 是 840s，对应 4.78 分。不同编译器和编译选项的优化情况如下：

| 编译器 + 选项               | 总时间 (s) | 1. linear 时间 (s) | 2. hdr 时间 (s) | 3. precision 时间 (s) | 分数 | 相比 GCC 14 `-O3` 性能提升 (%) |
|-----------------------------|------------|--------------------|-----------------|-----------------------|------|--------------------------------|
| GCC 14 `-O3`                | 175.8      | 49.9               | 72.1            | 53.8                  | 4.78 | 0                              |
| GCC 14 `-O3 -march=native`  | 157.3      | 44.0               | 63.2            | 50.0                  | 5.34 | 12                             |
| GCC 14 `-O3 -ffast-math`    | 160.5      | 44.6               | 67.2            | 48.7                  | 5.23 | 10                             |
| LLVM 22 `-O3`               | 134.0      | 38.5               | 56.1            | 39.3                  | 6.27 | 31                             |
| LLVM 22 `-O3 -march=native` | 117.2      | 34.4               | 48.6            | 34.1                  | 7.17 | 50                             |

又是 LLVM 22 相比 GCC 14 有明显优势的一个基准测试。其他对性能几乎没有影响的优化选项包括 `-flto` 和 `-ljemalloc`，这里就不具体列举了。731.astcenc_r 是 SPEC FP 2026 Rate 中 MPKI 最高的那一个，高达 5.0，相比其他大多数不到 1.0 的 MPKI 来说很高（第二高的是 737.gmsh_r，MPKI 达到了 3.33，第三高 767.nest_r 的 MPKI 只有 0.83），也比 SPEC INT 2026 Rate 的不少基准测试更高。下面分负载来进行分析。

#### 1. linear

主要热点函数：

- `compute_angular_endpoints_for_quant_levels` 来自 `src/astcenc_weight_align.cpp`：18.93%，主要瓶颈是在中间的循环，在用 SSE 做一些单精度浮点的标量计算，中间还有一些对来自 `libm` 的 `nearbyint` 调用，进行 round 操作，从代码来看，开发者有意识地写一些适合编译器去向量化的代码，比如用 `vfloat4` 类型来做一些批量操作，还有 `vmask4` 类型保存 `vfloat4` 比较的结果（`vmask4` 保存了四个 int，用 0 代表 false，用 -1 代表 true），再用 `select` 函数来进行向量化的 ternary operator，可惜编译器并不领情，编译出来依然是标量 SSE；
- `compute_avgs_and_dirs_3_comp_rgb` 来自 `src/astcenc_averages_and_directions.cpp`：14.70%，模式和上面类似，在循环中做一些 `vfloat4` 和 `vmask4` 的计算，但 SSE 指令都是标量的；
- `compute_quantized_weights_for_decimation` 来自 `src/astcenc_ideal_endpoints_and_weights.cpp`：13.34%，在循环中做一些不过因为涉及到量化，有一些 `vint` 参与以及查表 `vtable_lookup_32bit`，这里 `vfloat`/`vint` 本来代表的是根据平台能提供的 SIMD 宽度进行一个自动的映射（定义在 `src/astcenc_vecmathlib.h` 中，比如 AVX 就是 8 个元素，vfloat 映射到 vfloat8；SSE 就是 4 个元素，vfloat 映射到 vfloat4），不过显然这些在 SPEC 里都被禁用了，fallback 到了 4 个元素的情况；
- `compute_ideal_weights_for_decimation` 来自 `src/astcenc_ideal_endpoints_and_weights.cpp`：9.57%，主要瓶颈是在一个 gather 操作 `gatherf_byte_inds` 里，不过因为 SSE 不支持 gather，所以是拆成四个元素分别进行 load 和标量计算的；
- `bilinear_infill_vla` 来自 `src/astcenc_ideal_endpoints_and_weights.cpp`：7.80%，瓶颈一样是 gather，即 `gatherf_byte_inds` 函数；
- `compute_error_squared_rgb` 来自 `src/astcenc_averages_and_directions.cpp`：6.39%，瓶颈一样是 gather，以及 gather 之后的一系列向量计算，但 GCC 14 都编译成了 SSE 标量计算。

原生 SIMD 写法编译出来却是标量指令，反过来也说明，如果能正确向量化，性能还会有明显的提升空间。进一步，如果开了 `-O3 -march=native`，向量更宽来到 256 位，还多了 [`vblendvps`](https://www.felixcloutier.com/x86/blendvps) 指令来实现上述 `select` 函数。前面提到过，LLVM 22 明显更快，下面看看不同编译器和编译选项的对比：

| 编译器 + 选项               | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) | 错误预测 (M) | MPKI |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|--------------|------|
| GCC 14 `-O3`                | 49.9     | 835.7    | 259.3    | 55.6      | 63.2     | 188.6        | 28.6         | 3136.0       | 3.75 |
| GCC 14 `-O3 -march=native`  | 44.0     | 652.4    | 234.0    | 46.3      | 52.9     | 184.6        | 28.5         | 3148.2       | 4.83 |
| GCC 14 `-O3 -ffast-math`    | 44.6     | 780.5    | 259.8    | 54.6      | 49.3     | 159.9        | 43.2         | 2139.0       | 2.74 |
| LLVM 22 `-O3`               | 38.5     | 829.7    | 235.0    | 34.8      | 36.1     | 68.8         | 155.6        | 1095.5       | 1.32 |
| LLVM 22 `-O3 -march=native` | 34.4     | 620.9    | 179.5    | 17.7      | 19.6     | 42.1         | 125.7        | 823.4        | 1.33 |

从计数器可以看到，GCC 14 整体性能比 LLVM 22 差，是因为 LLVM 22 做了更多的向量化，它浮点向量指令明显比浮点标量要多，并且错误预测明显更少，MPKI 小很多。下面进行深入的分析。

首先看 GCC 14 是怎么实现 731.astcenc_r 的这类 SIMD 原生代码的。以上面分析的热点函数为例，一个常见的模式是用 `vfloat4` 的比较加 `select` 来实现向量化的最大值计算：

```cpp
vfloat4 vmax(vfloat4 a, vfloat4 b) {
  vmask4 mask = b > a;
  return select(a, b, mask);
}
```

这段代码在 `-O3` 编译选项下会被 GCC 14 编译成这样的汇编：

```asm
vmax(vfloat4 a, vfloat4 b):
        # a 向量保存在 xmm0（a[0] 和 a[1]）和 xmm1（a[2] 和 a[3]）寄存器
        # b 向量保存在 xmm2（b[0] 和 b[1]）和 xmm3（b[2] 和 b[3]）寄存器
        # 虽然每个元素都是单精度，但每个 xmm 寄存器只保存了两个元素
        movq    %xmm1, %rax       # rax = a3 | a2
        movq    %xmm3, %rcx       # rcx = b3 | b2
        movq    %xmm0, %rsi       # rsi = a1 | a0
        movd    %ecx, %xmm1       # xmm1 = b2
        movd    %eax, %xmm6       # xmm6 = a2
        shrq    $32, %rcx         # rcx = b3
        movdqa  %xmm2, %xmm5      # xmm5 = b1 | b0
        shrq    $32, %rax         # rax = a3
        movdqa  %xmm2, %xmm0      # xmm0 = b1 | b0
        movd    %ecx, %xmm4       # xmm4 = b3
        shufps  $85, %xmm5, %xmm5 # xmm5 = b1 | b1 | b1 | b1
        movd    %eax, %xmm2       # xmm2 = a3
        movd    %esi, %xmm7       # xmm7 = a0
        shrq    $32, %rsi         # rsi = a1
        movdqa  %xmm5, %xmm3      # xmm3 = b1 | b1 | b1 | b1
        comiss  %xmm2, %xmm4      # 比较 a3 和 b3
        movd    %esi, %xmm5       # xmm5 = a1
        seta    %al               # al = (b3 > a3)
        comiss  %xmm6, %xmm1      # 比较 b2 和 a2
        jbe     .L14              # 如果 a2 >= b2 就跳转到 .L14
        testb   %al, %al
        jne     .L15              # 如果 b3 > a3 就跳转到 .L15
        # 此时 a2 < b2, a3 >= b3
        maxss   %xmm7, %xmm0      # xmm0 = max(a0, b0)
        maxss   %xmm5, %xmm3      # xmm3 = max(a1, b1)
        unpcklps        %xmm2, %xmm1 # xmm1 = a3 | b2
        unpcklps        %xmm3, %xmm0 # xmm0 = max(a1, b1) | max(a2, b2)
        ret
.L14:                             # 处理 a2 >= b2 的情况
        testb   %al, %al
        jne     .L16              # 如果 b3 > a3 就跳转到 .L16
        #3 此时 a2 >= b2, a3 >= b3
        movaps  %xmm6, %xmm1      # xmm1 = a2
        # 下略，就是分类讨论 a2 vs b2，a3 vs b3 的四种情况
.L17:
        maxss   %xmm7, %xmm0
        maxss   %xmm5, %xmm3
        unpcklps        %xmm2, %xmm1
        unpcklps        %xmm3, %xmm0
        ret
.L16:
        movaps  %xmm4, %xmm2
        movaps  %xmm6, %xmm1
        jmp     .L17
.L15:
        maxss   %xmm7, %xmm0
        maxss   %xmm5, %xmm3
        movaps  %xmm4, %xmm2
        unpcklps        %xmm2, %xmm1
        unpcklps        %xmm3, %xmm0
        ret
```

很奇怪的是，它首先用通用寄存器把输入的数值拆分出来，然后分别比较后两个元素 a2 vs b2，a3 vs b3，用分支来处理四种可能的情况，这四种情况是已知后两个元素最大值都来自哪里，结果针对前两个元素又用 `maxss` 来计算，为啥不一开始就对所有四个元素都用 `maxss` 呢？结果开 `-O3 -ffast-math` 后，它莫名其妙就学会了这一点：

```asm
vmax(vfloat4, vfloat4):
        movq    %xmm0, %rsi
        movq    %xmm1, %rcx
        movq    %xmm2, %rdx
        movd    %esi, %xmm1
        movq    %xmm3, %rax
        movdqa  %xmm2, %xmm0
        shrq    $32, %rdx
        maxss   %xmm1, %xmm0
        shrq    $32, %rsi
        movdqa  %xmm3, %xmm1
        shrq    $32, %rax
        movd    %ecx, %xmm3
        shrq    $32, %rcx
        movd    %edx, %xmm2
        movd    %esi, %xmm4
        maxss   %xmm3, %xmm1
        movd    %ecx, %xmm5
        movd    %eax, %xmm3
        maxss   %xmm4, %xmm2
        maxss   %xmm5, %xmm3
        unpcklps        %xmm2, %xmm0
        unpcklps        %xmm3, %xmm1
        ret
```

但依然是用 SSE 做标量，而 LLVM 22 就懂得如何用 `maxps` 指令向量化：

```asm
vmax(vfloat4, vfloat4):
        movlhps %xmm3, %xmm2
        movlhps %xmm1, %xmm0
        maxps   %xmm2, %xmm0
        movaps  %xmm0, %xmm1
        unpckhpd        %xmm0, %xmm1
        retq
```

剩余的指令只是为了解决调用约定的数据存放位置问题，实际在函数内部计算的时候，通常就一条 `maxps` 指令完成所有 4 个元素的 max 计算。从这个例子也可以看出，为啥 LLVM 22 比 GCC 14 要快得多：GCC 14 多了很多无用的分支来解决 `select` 里的比较，而且还不能向量化 max 操作。即使给 GCC 14 开 `-march=native`，它依然还在用 AVX 指令进行标量 max 运算，真是难绷。上述编译结果可见 [Godbolt](https://godbolt.org/z/Y8Ps15n39)。GCC 14 的 MPKI 那么高，其实都是这么来的，也挺搞笑。我还测试了一下，发现相同的代码在 LoongArch 下也没有得到很好的向量化支持（见 [Godbolt](https://godbolt.org/z/qTsaMnzhe)），因此提了一个 [issue](https://github.com/loongson-community/discussions/issues/120)，仅考虑向量化 fmax 内核，用 `vfcmp.slt.s` + `vbitsel.v` 的优化实现大概是目前 LLVM 22 编译结果的 2.9 倍性能。这里有一个小冷知识，就是 x86 的 SSE/AVX max 指令都实现的都是 `a > b ? a : b` 的逻辑，而 LoongArch 的 fmax 指令实现的是 IEEE754 的 `maxNum`，二者在出现 NaN 时的行为不同：前者只要 a 或 b 出现一个 NaN，就都返回 b；后者只有一个 NaN 时，会返回另一个非 NaN 的数。

#### 2. hdr

主要热点函数：

- `compute_angular_endpoints_for_quant_levels` 来自 `src/astcenc_weight_align.cpp`：19.80%，描述见上；
- `compute_avgs_and_dirs_3_comp_rgb` 来自 `src/astcenc_averages_and_directions.cpp`：15.37%，描述见上；
- `compute_quantized_weights_for_decimation` 来自 `src/astcenc_ideal_endpoints_and_weights.cpp`：12.40%，描述见上；
- `compute_error_squared_rgb` 来自 `src/astcenc_averages_and_directions.cpp`：6.91%，描述见上；
- `compute_ideal_weights_for_decimation` 来自 `src/astcenc_ideal_endpoints_and_weights.cpp`：5.68%，描述见上。

热点函数基本和 1. linear 一致，那么各方面基本也和它一样，GCC 14 生成大量分支和标量 SSE 指令，而 LLVM 22 能更好地向量化，避免一些无谓的分支。对比如下：

| 编译器 + 选项               | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) | 错误预测 (M) | MPKI |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|--------------|------|
| GCC 14 `-O3`                | 72.1     | 1091.8   | 306.9    | 78.6      | 91.7     | 245.8        | 30.4         | 4928.9       | 4.51 |
| GCC 14 `-O3 -march=native`  | 63.1     | 851.4    | 271.2    | 65.2      | 77.4     | 240.1        | 30.4         | 4890.6       | 5.74 |
| GCC 14 `-O3 -ffast-math`    | 67.1     | 1036.6   | 311.0    | 85.5      | 73.7     | 200.8        | 54.3         | 4077.0       | 3.93 |
| LLVM 22 `-O3`               | 55.9     | 1107.9   | 276.5    | 55.9      | 56.9     | 111.8        | 129.9        | 1943.2       | 1.75 |
| LLVM 22 `-O3 -march=native` | 48.6     | 825.2    | 209.3    | 30.7      | 34.1     | 85.2         | 139.7        | 1411.6       | 1.71 |

#### 3. precision

热点函数大多还是和 1. linear 以及 2.hdr 一样，就是多了一个 `find_best_partition_candidates` 函数，来自 `src/astcenc_find_best_partitioning.cpp`，主要瓶颈在 `a / sqrt(length)` 的计算上。这次 GCC 14 在 `-O3` 时倒是能够正确向量化这一步，通过一次标量的 `sqrtss` 加 `shufps` 把结果复制到所有 lane，再用 `divps` 进行批量的除法，不过其余的热点函数还是一如既往的编译出很慢的代码。下面给出性能计数器上的对比：

| 编译器 + 选项               | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) | 错误预测 (M) | MPKI |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|--------------|------|
| GCC 14 `-O3`                | 53.8     | 711.5    | 176.8    | 62.0      | 61.3     | 177.0        | 9.3          | 5119.2       | 7.19 |
| GCC 14 `-O3 -march=native`  | 49.2     | 570.5    | 161.3    | 57.1      | 54.7     | 176.1        | 9.2          | 5113.1       | 8.96 |
| GCC 14 `-O3 -ffast-math`    | 48.7     | 655.9    | 168.3    | 64.6      | 49.8     | 156.5        | 19.5         | 4227.6       | 6.56 |
| LLVM 22 `-O3`               | 39.3     | 729.9    | 149.2    | 42.8      | 35.9     | 75.3         | 77.2         | 1906.7       | 2.61 |
| LLVM 22 `-O3 -march=native` | 34.1     | 544.9    | 112.5    | 28.0      | 23.2     | 52.0         | 87.1         | 1445.7       | 2.65 |

#### 小结

731.astcenc_r 用了 SIMD 原生的写法来编程：`vfloat4`、`vint4` 和 `vmask4` 等等，编写时就是奔着 SIMD 指令去的。只可惜 GCC 14 辜负了开发者的期望，不能正确识别代码意图并利用硬件指令，还莫名生成了一堆分支来实现 `select` 函数。相比之下，LLVM 22 就做得好很多，该向量化的地方就向量化。同时也能看到，像 LoongArch 这样稍微小众一些的指令集，在这些代码模式下的优化还比较欠缺，无论 GCC 还是 LLVM 都是如此。

### 736.ocio_r

ocio 是 OpenColorIO 的缩写，和 731.astcenc_r 类似，也是在图片上的处理，不过更侧重于图像处理，而非图像压缩。该基准测试包括如下四个负载：

```shell
# 1. lut1d
ocioperf --spec-validation-offset 101 --spec-validation-stride 17 --spec-validation-pixels 131 --bitdepths ui16 ui16 --iter 100 --test -1 --transform ctf/lut1d_halfdom.ctf
# 2. mntr
ocioperf --spec-validation-offset 202 --spec-validation-stride 19 --spec-validation-pixels 132 --bitdepths ui16 f32 --iter 200 --8kres --test 0 --transform ctf/mntr_srgb_identity.ctf
# 3. aces
ocioperf --spec-validation-offset 303 --spec-validation-stride 23 --spec-validation-pixels 133 --bitdepths f32 f32 --iter 20 --8kres --test -1 --transform clf/aces_to_video_with_look.clf
# 4. heavy
ocioperf --spec-validation-offset 404 --spec-validation-stride 29 --spec-validation-pixels 134 --bitdepths f32 f32 --iter 25 --test -1 --transform clf/heavy_transform.clf
```

reftime 是 875s，不同编译器和编译选项的运行情况如下：

| 编译器 + 选项               | 总时间 (s) | 1. lut1d 时间 (s) | 2. mntr 时间 (s) | 3. aces 时间 (s) | 4. heavy 时间 (s) | 分数 | 相比 GCC 14 `-O3` 性能提升 (%) |
|-----------------------------|------------|-------------------|------------------|------------------|-------------------|------|--------------------------------|
| GCC 14 `-O3`                | 139.8      | 6.1               | 11.2             | 67.8             | 54.6              | 6.26 | 0                              |
| GCC 14 `-O3 -march=native`  | 105.0      | 4.2               | 10.2             | 49.6             | 40.1              | 8.33 | 33                             |
| GCC 14 `-O3 -ffast-math`    | 139.4      | 6.4               | 11.4             | 67.8             | 53.9              | 6.28 | 0.3                            |
| LLVM 22 `-O3`               | 128.9      | 6.8               | 11.3             | 61.7             | 49.0              | 6.79 | 8                              |
| LLVM 22 `-O3 -march=native` | 105.3      | 5.4               | 9.6              | 49.3             | 40.9              | 8.31 | 33                             |

可见又是一个 `-O3 -march=native` 带来明显提升的基准测试，且 LLVM 22 依然比 GCC 14 在 `-O3` 下有性能优势，在 `-O3 -march=native` 时基本打平。下面进行具体分析。

#### 1. lut1d

热点函数：

- `OpenColorIO_v2_2dev::BitDepthCast<BIT_DEPTH_F32, BIT_DEPTH_UINT16>::apply` 来自 `src/ASWF-OpenColorIO/src/OpenColorIO/CPUProcessor.cpp`：45.16%，主要做的计算是，在循环中对取值在零到一之间的单精度浮点元素，乘以 65535 从而放缩到 uint16_t 的范围，加 0.5 后 clamp 到 uint16_t 的范围，最后再 float 转换为 uint16_t，这个过程被编译为 SSE 的向量指令；
- `OpenColorIO_v2_2dev::Lut1DRendererHalfCode<BIT_DEPTH_UINT16, BIT_DEPTH_F32>::apply` 来自 `src/ASWF-OpenColorIO/src/OpenColorIO/ops/lut1d/Lut1DOpCPU.cpp`：33.70%，在循环中对输入的 uint16_t 进行查表，其实就是从预先计算好的数组里读取 uint16_t 对应的 float 值，瓶颈是 SSE 标量间接访存；
- `__memmove_avx_unaligned_erms` 来自 libc：13.28%，memmove 的 AVX 加速实现；
- `__memset_avx2_unaligned_erms` 来自 libc：3.55%，memset 的 AVX 加速实现。

对于这类可以高度向量化的代码，`-O3 -march=native` 的提升是很明显的，在 `OpenColorIO_v2_2dev::BitDepthCast<BIT_DEPTH_F32, BIT_DEPTH_UINT16>::apply` 函数里，体现就是用上了 AVX2 的 256 位向量计算以及 FMA 指令，正好把放缩和加 0.5 这两步融合在了一起，后续则是继续用位运算来实现 clamp 操作，使得这个函数在 `-O3 -march=native` 下的时间占比降低到了 27.82%，那么依然在用 SSE 标量进行间接访存的 `OpenColorIO_v2_2dev::Lut1DRendererHalfCode<BIT_DEPTH_UINT16, BIT_DEPTH_F32>::apply` 就成为了主要的性能瓶颈，时间占比提升到 42.85%。

在该基准测试里，GCC 14 比 LLVM 22 更快一些。以下是二者在不同编译选项下的对比：

| 编译器 + 选项               | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) | 错误预测 (M) |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|--------------|
| GCC 14 `-O3`                | 6.1      | 106.2    | 23.3     | 11.7      | 4.2      | 2.6          | 5.0          | 2.6          |
| GCC 14 `-O3 -march=native`  | 4.2      | 63.8     | 22.0     | 11.0      | 3.6      | 2.6          | 2.5          | 2.5          |
| GCC 14 `-O3 -ffast-math`    | 6.4      | 104.8    | 23.2     | 11.7      | 4.2      | 2.5          | 5.0          | 2.6          |
| LLVM 22 `-O3`               | 6.8      | 106.1    | 23.3     | 11.7      | 3.6      | 2.5          | 5.0          | 2.6          |
| LLVM 22 `-O3 -march=native` | 5.4      | 72.5     | 24.8     | 11.0      | 1.4      | 2.5          | 2.5          | 2.5          |

具体到汇编层面上，可以观察到，GCC 14 和 LLVM 22 在实现上有一些不同，开头都是乘法和加法，主要是 clamp 的部分用的指令不同，为了解决 16 位和 32 位的位宽转换的问题，GCC 14 主要用 punpcklwd 类指令，而 LLVM 22 更多使用 pshufd 类指令，详见 [Godbolt](https://godbolt.org/z/KP3vznq1j)。虽然总指令数很接近，但毕竟硬件执行这些指令需要的时间不同，所以体现在 IPC 上也有一定的差距。开 `-O3 -march=native` 之后也是类似的情况。

#### 2. mntr

热点函数：

- `OpenColorIO_v2_2dev::BitDepthCast<BIT_DEPTH_UINT16, BIT_DEPTH_F32>::apply` 来自 `src/ASWF-OpenColorIO/src/OpenColorIO/CPUProcessor.cpp`：55.41%，这次转换的方向反过来了，是从 uint16_t 到 float，于是计算过程变成先从 uint16_t 转成 float，再乘以 `1.0/65535.0`，当然这次就没有 clamp 了，编译器依然能正确向量化，不过因为位宽从 16 变成 32 的问题，花了不少功夫；
- `OpenColorIO_v2_2dev::ScaleRenderer::apply` 来自 `src/ASWF-OpenColorIO/src/OpenColorIO/ops/matrix/MatrixOpCPU.cpp`：41.52%，代码逻辑就是很简单的对每个像素的四个分量分别乘以一个 scale（从 `out[0] = in[0] * m_scale[0]` 到 `out[3] = in[3] * m_scale[3]`），不同像素的 scale 来自同一个数组 `m_scale`，理应是比较好向量化的，但实际上并没有向量化成功，这是因为指针没有标记 restrict，编译器无法判断 `out` 和 `m_scale` 是否可能重合，只有在不重合的前提下，才能直接直接向量化用 mulps 进行计算，见 [Godbolt](https://godbolt.org/z/E6nqrK48a)。

由于 AMD64 缺少对混合宽度计算的向量指令，其实很大开销是在向量之间搬运数据，而非进行实际的计算和访存，这方面，RISC-V Vector 的特殊设计还确实带来了更简洁的指令生成，见 [Godbolt](https://godbolt.org/z/qvzMK47rf)。不同编译器在不同编译选项下的对比：

| 编译器 + 选项               | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) | 错误预测 (M) |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|--------------|
| GCC 14 `-O3`                | 11.2     | 209.9    | 56.5     | 33.3      | 7.5      | 26.8         | 6.6          | 1.9          |
| GCC 14 `-O3 -march=native`  | 10.2     | 159.6    | 54.8     | 29.9      | 7.1      | 26.8         | 3.3          | 1.8          |
| GCC 14 `-O3 -ffast-math`    | 11.4     | 209.7    | 56.5     | 33.3      | 7.5      | 26.7         | 6.6          | 1.8          |
| LLVM 22 `-O3`               | 11.3     | 194.5    | 56.5     | 33.3      | 8.6      | 26.5         | 6.7          | 1.9          |
| LLVM 22 `-O3 -march=native` | 9.6      | 149.4    | 58.2     | 29.9      | 2.8      | 26.5         | 3.4          | 2.0          |

#### 3. aces

热点函数：

- `OpenColorIO_v2_2dev::Lut3DTetrahedralRenderer::apply` 来自 `src/ASWF-OpenColorIO/src/OpenColorIO/ops/lut3d/Lut3DOpCPU.cpp`：50.74%，做的操作还挺复杂，每个元素首先进行一次乘法，然后进行一次 clamp，floor 和 ceil 后分别转化为 int，再根据 int 去进行对一个表进行间接访存，查表的结果再经过一系列的加权平均完成计算，向量化程度不高；
- `OpenColorIO_v2_2dev::MatrixRenderer::apply` 来自 `src/ASWF-OpenColorIO/src/OpenColorIO/ops/matrix/MatrixOpCPU.cpp`：11.55%，进行矩阵的运算，把输入的四维向量和一个 4x4 矩阵进行乘法，得到输出的四维向量，向量化程度较高；
- `__log2f_fma` 来自 libm：10.02%，计算浮点 log2；
- `OpenColorIO_v2_2dev::CameraLin2LogRenderer::apply` 来自 `src/ASWF-OpenCOlorIO/src/OpenColorIO/ops/log/LogOpCPU.cpp`：9.76%，判断输入的范围，如果小于一个阈值 `m_linb`，就用线性的乘加计算结果，否则就会调用上述 log2 函数，结合一些乘加以及 max 操作来进行计算，向量化程度低。

不同编译器和编译选项的对比：

| 编译器 + 选项               | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) | 错误预测 (M) |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|--------------|
| GCC 14 `-O3`                | 67.8     | 1258.9   | 299.3    | 86.3      | 100.5    | 260.6        | 28.0         | 146.6        |
| GCC 14 `-O3 -march=native`  | 49.6     | 873.7    | 289.0    | 84.9      | 84.0     | 257.4        | 14.0         | 135.4        |
| GCC 14 `-O3 -ffast-math`    | 67.8     | 1251.5   | 296.4    | 94.4      | 109.9    | 213.7        | 43.8         | 150.6        |
| LLVM 22 `-O3`               | 61.7     | 1152.4   | 416.6    | 136.7     | 133.7    | 329.0        | 15.4         | 168.5        |
| LLVM 22 `-O3 -march=native` | 49.3     | 857.8    | 342.8    | 92.6      | 84.4     | 329.0        | 13.0         | 151.6        |

GCC 14 和 LLVM 22 在 `-O3` 下的性能差距主要来自于 floor 和 ceil 的处理：GCC 14 生成了一系列 SSE 指令来计算，由于没有 SSE4.1 的 roundps 指令，所以实现比较复杂，而 LLVM 22 转为采用 libm 的加速实现 `__floorf_sse41`，它的函数体就是一条 SSE4.1 的 roundps 指令加 return，虽然有函数调用的开销，不仅要 call/ret，还多了一些寄存器到栈的 Load 和 Store，但总体还是赚的。不过，如果处理器确实没有 SSE4.1 指令，那么 GCC 14 又该比 LLVM 22 更快了。这种取舍，在不开 `-march=native` 的时候确实无法实现，此时只能猜测，哪种情况发生的概率更高了，例如现在来看，有 SSE4.1 的 AMD64 处理器肯定是比没有 SSE4.1 的 AMD64 处理器要多。

开 `-O3 -march=native` 后，因为有了 `vroundps` 指令，原来的 ceil 和 floor 操作可以用向量指令代替，相比之前的向量化实现（GCC 14）或调用 libm 里的加速实现（LLVM 22），GCC 14 和 LLVM 22 都有不错的提升，来到了同一水平线上。同时 fma 也成功融合了不少浮点乘加计算。

#### 4. heavy

热点函数：

- `__powf_fma` 来自 libm：26.17%；
- `OpenColorIO_v2_2dev::Lut3DRenderer::apply` 来自 `src/ASWF-OpenColorIO/src/OpenColorIO/ops/lut3d/Lut3DOpCPU.cpp`：25.69%，模式和上面的 `OpenColorIO_v2_2dev::Lut3DTetrahedralRenderer::apply` 比较类似，也有 clamp/floor/ceil 和查表等动作，就是最后的计算部分不太一样，也都是标量的 SSE 指令；
- `OpenColorIO_v2_2dev::Lut1DRenderer<BIT_DEPTH_F32, BIT_DEPTH_F32>::apply` 来自 `src/ASWF-OpenColorIO/src/OpenColorIO/ops/lut1d/Lut1DOpCPU.cpp`：15.63%，模式和上述 `OpenColorIO_v2_2dev::Lut3DRenderer::apply` 类似，不过查表的部分更简单，因为只有一维，但也是全程标量；
- `OpenColorIO_v2_2dev::CDLRendererFwd<true>::apply`：10.88%，里面调用了 pow，导致 `__powf_fma` 占用了很多时间，其余部分做了浮点乘法、加减法以及 Clamp 操作，还是全程标量；
- `OpenColorIO_v2_2dev::GammaMoncurveOpCPUFwd::apply`：5.41%，同样调用了 pow，除了 pow 以外还有一些浮点运算以及比较。

不同编译器和编译选项的对比：

| 编译器 + 选项               | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) | 错误预测 (M) |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|--------------|
| GCC 14 `-O3`                | 54.6     | 1013.5   | 209.4    | 57.0      | 80.8     | 253.7        | 5.8          | 32.0         |
| GCC 14 `-O3 -march=native`  | 40.9     | 764.7    | 204.0    | 54.8      | 70.8     | 260.2        | 3.3          | 31.8         |
| GCC 14 `-O3 -ffast-math`    | 53.9     | 971.0    | 202.1    | 50.5      | 80.6     | 252.3        | 6.6          | 29.1         |
| LLVM 22 `-O3`               | 49.0     | 861.5    | 250.4    | 77.3      | 102.7    | 215.6        | 29.9         | 28.8         |
| LLVM 22 `-O3 -march=native` | 40.9     | 726.8    | 206.9    | 55.4      | 67.3     | 255.6        | 25.7         | 28.5         |

LLVM 22 相比 GCC 14 的主要性能区别和 3. aces 一样，就是 ceil/floor 的处理。此外，就是和 731.astcenc_r 类似的情况，在遇到向量化的 min/max 操作的时候，LLVM 22 会正确向量化为对应的 maxps/minps 指令，而 GCC 14 生成的代码就会比较冗长。

#### 小结

736.ocio_r 依然是一个比较适合向量化的应用，虽然它不像 731.astcenc_r 那样直接用 `vfloat4` 格式，但因为它是图像处理，每次循环处理一个像素，然后每个像素有四个通道，在很多情况下，这四个通道的计算过程是一样的，因此也非常适合向量化。而 LLVM 22 在 `-O3` 下做出了比 GCC 14 更好的指令生成，从 floor/ceil 到 libm 函数的映射，以及更好的向量化实现。当然，开 `-O3 -march=native` 后，GCC 14 和 LLVM 22 的性能差距非常小，说明在两方都开启足够的指令集扩展以后，基本会收敛到差不多的代码实现上，这也反过来说明，GCC 14 的 SSE 代码生成上有一些欠缺，可能的情况是，并非 GCC 14 不能向量化（因为开 `-O3 -march=native` 后就学会了），而是尝试向量化后，不知道怎么用 SSE 表达向量化后的代码，于是退回到了标量。

### 737.gmsh_r

737.gmsh_r 是 3D 的 CAD 软件，包括七个负载：

```shell
# 1. choi
gmsh_r -option gmsh.opts -nt 0 choi.geo
# 2. mediterranean
gmsh_r -option gmsh.opts -nt 0 mediterranean.geo
# 3. projection
gmsh_r -option gmsh.opts -nt 0 projection.geo
# 4. gasdis
gmsh_r -option gmsh.opts -nt 0 gasdis.geo
# 5. Torus
gmsh_r -option gmsh.opts -nt 0 Torus.geo
# 6. spec
gmsh_r -option gmsh.opts -nt 0 spec.geo -clscale 0.175 -algo del2d -algo hxt
# 7. p19
gmsh_r -option gmsh.opts -nt 0 p19.geo
```

各负载运行时间为 17.1s、11.8s、11.2s、16.9s、9.2s、13.4s、12.8s，总时间 92.2s，reftime 是 459s，对应 4.98 分。`-O3 -ffast-math` 和 `-O3 -march=native` 收益都很小，LLVM 22 反而比 GCC 14 更慢，因此这里就不做具体比较了。

用 `-O3 -march=native` 编译的时候，发现如果 CC 只传了 gcc，而没有传 `-std=c18`，就会在 4. gasdis 这一个负载里死循环，一直报错：`Info    : Symbolic perturbation failed (2 superposed vertices ?)`。经过对比，两者的区别在于是否进行乘加融合：`-O3 -std=c18 -march=native` 时，不会进行融合，而 `-O3 -march=native` 或 `-O3 -std=gnu18 -march=native` 时会进行融合，见 [Godbolt](https://godbolt.org/z/58fTP5fnG)。在其他程序里，融合对性能更优，但这里很不幸，融合了就会导致死循环。这和 [`-fp-contract`](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html) 有关：

```
-ffp-contract=style

    -ffp-contract=off disables floating-point expression contraction. -ffp-contract=fast enables floating-point expression contraction such as forming of fused multiply-add operations if the target has native support for them. -ffp-contract=on enables floating-point expression contraction if allowed by the language standard. This is implemented for C and C++, where it enables contraction within one expression, but not across different statements.

    The default is -ffp-contract=off for C in a standards compliant mode (-std=c11 or similar), -ffp-contract=fast otherwise.
```

可见它只对 C 语言有效，对 C++ 无效，实际上就是只对 737.gmsh_r 有影响；虽然 709.cactus_r 也有 C 代码，但它的主要计算都在 C++ 语言的部分。

接下来针对各负载进行热点分析。

#### 1. choi

热点函数：

- `netgen::ADTree6::GetIntersecting` 来自 `src/gmsh/contrib/Netgen/libsrc/gprim/adtree.cpp`：18.40%，实现了一个 6 维的 KD-Tree 的搜索算法，主要瓶颈在于中间的数据依赖的分支 `if (node->pi != -1)`，预测错误率较高；
- `__ieee754_atan2_fma` 来自 libm：6.64%；
- `reparamMeshVertexOnFace` 来自 `src/gmsh/src/geo/MVertex.cpp`：6.03%，不确定实现的是什么算法，不过能看到有很多分支，错误预测也比较多。

虽然用到了浮点，但计算模式并不适合向量化，毕竟是 KD-Tree 的搜索。执行了 204.7B 条指令，错误预测 744.3M 次，MPKI 等于 `744.3M/204.7B*1000=3.64`，属于 SPEC FP 2026 Rate 中第二高的，其中第一高 731.astcenc_r 如上面所述，其实是 GCC 的实现不够好，完全可以把 MPKI 优化到 LLVM 22 的 1.3 左右，那样的话，737.gmsh_r 就是 MPKI 最高的负载了。树的搜索，MPKI 高是正常现象。

#### 2. mediterranean

热点函数：

- `meshGEdgeProcessing` 来自 `src/gmsh/src/mesh/meshGEdge.cpp`：36.55%，主要瓶颈在循环中的 gauss seidel 迭代，标量除法和比较耗费了比较多的时间；
- `KDTreeSingleIndexAdaptor::searchLevel` 来自 `src/gmsh/src/numeric/nanoflann.hpp`：33.50%，又一个经典的 KD-Tree 的搜索算法，根据输入的值递归到左子树或右子树；
- `InterpolateCurve` 来自 `src/gmsh/src/geo/GeoInterpolation.cpp`：6.53%，递归进行一些插值的计算。

虽然用到了浮点，但计算模式依然不适合向量化，因为中间的计算结果还被用于 if 分支，分支内也有若干浮点计算。

#### 3. projection

热点函数：

- `laplaceSmoothing` 来自 `src/gmsh/src/mesh/meshGFaceOptimize.cpp`：11.73%，主要瓶颈是 `std::set` 的操作，，而 `std::set` 是用 `std::map` 实现的，因此会调用下面的 `std::map` 的代码；
- `std::map::_M_get_insert_unique_pos` 来自 libstdc++：7.49%，`std::map` 的插入算法实现；
- `__ieee754_atan2_fma` 来自 libm：7.21%；
- `reparamMeshVertexOnFace`：6.66%，描述见上；
- `std::map::_M_get_insert_unique` 来自 libstdc++：6.09%，`std::map` 的插入实现；
- `SetRotationMatrix` 来自 `src/gmsh/src/geo/Geo.cpp`：5.01%，代码是多层循环，适合向量化，编译器也确实向量化了，不过时间占比并不高。

可见，该负载主要还是 `std::map` 相关的操作为主要瓶颈。

#### 4. gasdis

热点函数：

- `MakeHybridHexTetMeshConformalThroughTriHedron` 来自 `src/gmsh/src/mesh/meshCombine3D.cpp`：30.18%，主要瓶颈是在循环里对 `std::map` 进行搜索；
- `parallelDelaunay3D` 来自 `src/gmsh/contrib/hxt/tetMesh/src/hxt_tetDelaunay.c`：9.05%，实现了 Delaunay 三角剖分算法；
- `hxtRefineTetrahedra` 来自 `src/gmsh/contrib/hxt/tetMesh/src/hxt_tetRefine.c`：5.18%，主要是指循环中做一些浮点计算，包括加减法，乘除法和 sqrt。

瓶颈主要还是在 `std::map`。

#### 5. Torus、6.spec 和 7.p19

最后三个负载，其热点函数都与 4.gadis 相同，不再赘述。

#### 小结

各负载的情况：

| 负载             | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) | 错误预测 (M) | MPKI |
|------------------|----------|----------|----------|-----------|----------|--------------|--------------|--------------|------|
| 1. choi          | 17.0     | 204.7    | 59.3     | 25.6      | 39.4     | 22.1         | 0.3          | 744.3        | 3.64 |
| 2. mediterranean | 11.7     | 190.7    | 57.4     | 23.2      | 24.0     | 28.5         | 2.4          | 71.0         | 0.37 |
| 3. projection    | 11.1     | 109.0    | 29.1     | 14.4      | 20.3     | 13.3         | 2.2          | 183.0        | 1.68 |
| 4. gasdis        | 16.9     | 157.8    | 46.3     | 17.8      | 27.6     | 19.6         | 0.2          | 689.9        | 4.37 |
| 5. Torus         | 9.2      | 77.3     | 21.9     | 8.2       | 13.4     | 9.4          | 0.5          | 380.4        | 4.92 |
| 6. spec          | 13.3     | 101.4    | 30.2     | 10.8      | 18.1     | 10.9         | 0.2          | 546.1        | 5.39 |
| 7. p10           | 12.7     | 96.3     | 28.8     | 10.2      | 17.2     | 10.4         | 0.1          | 529.3        | 5.50 |

可见整体的 MPKI 还是偏高的，并且很大程度上归功于 KD-Tree 的查询以及 `std::map` 的查询或插入，只不过这些树的 key 都是单精度浮点数。并且根据上面的分析，确实相关的代码不适合向量化，浮点乘加融合还被禁用了，否则就可能不收敛。

### 748.flightdm_r

flightdm 是一个飞行动力学模拟器，该基准测试包括如下八项负载：

```shell
# 1. weather
JSBSim --nohighlight scripts/weather-balloon2.xml
# 2. B747
JSBSim --nohighlight scripts/B747_script1.xml
# 3. x153
JSBSim --nohighlight scripts/x153.xml
# 4. c3104
JSBSim --nohighlight scripts/c3104.xml
# 5. ah1s
JSBSim --nohighlight scripts/ah1s_flight_test.xml
# 6. orbit_torque
JSBSim --nohighlight scripts/ball_orbit_g_torque.xml
# 7. orbit_torque2
JSBSim --nohighlight scripts/ball_orbit_g_torque2.xml
# 8. orbit
JSBSim --nohighlight scripts/ball_orbit.xml
```

各负载的运行时间分别为 5.9s、14.7s、10.9s、11.3s、24.8s、8.0s、9.8s 和 8.4s，一共 93.9s，reftime 是 716s，对应 7.63 分。开 `-O3 -march=native` 仅对性能有 2% 的提升，`-O3 -ljemalloc` 反而能提升 4%，`-O3 -flto` 能提升 11%。LLVM 22 性能不如 GCC 14，这里就不赘述了。下面对各负载进行分析。

#### 1. weather

热点函数：

- `__sincos_fma` 来自 libm：6.75%；
- `__ieee754_atan2_fma` 来自 libm：6.41%；
- `__strncmp_avx2` 来自 libc：5.04%；
- `parse_path` 来自 `src/JSB-FlightSim/src/simgear/props/props.cxx`：4.43%，路径字符串的解析，拆分成多个 component；
- `__ieee754_pow_fma` 来自 libm：4.05%。

热点也挺神奇的，都是一些 libm/libc 的函数，flightdm 自己的代码耗时最多的居然是个路径解析。各种优化选项没啥效果，也不足为奇了。

#### 2. B747

热点函数：

- `SGPropertyNode::getDoubleValue` 来自 `src/JSB-FlightSim/src/simgear/props/props.cxx`：5.65%，看起来是对配置文件的解析，然后从解析结果里提取浮点数；
- `__ieee754_atan2_fma` 来自 libm：5.42%；
- `__sincos_fma` 来自 libm：5.25%；

依然没啥好分析的。

#### 3. x153 和 4. c3104

热点函数和 2. B747 相同，不再赘述。

#### 5. ah1s

热点函数：

- `SGPropertyNode::getDoubleValue` 来自 `src/JSB-FlightSim/src/simgear/props/props.cxx`：8.45%，描述见上；
- `JSBSim::aFunc::getValue` 来自 `src/JSB-FlightSim/src/math/FGFunction.cpp`：7.20%，是一个带有 memo 能力的类似 `std::function` 的容器；
- `__sincos_fma` 来自 libm：6.04%；
- `__ieee754_atan2_fma` 来自 libm：5.35%；
- `JSBSim::FGPropertyValue::getValue` 来自 `src/JSB-FlightSim/src/math/FGPropertyValue.cpp`：5.11%，调用上面的 `getDoubleValue` 函数；

给人的感觉就是，不是在调用 libm 计算一些超越函数，就是在做配置文件内容的提取。

#### 6. orbit_torque

热点函数：

- `__ieee754_atan2_fma` 来自 libm：7.52%；
- `__sincos_fma` 来自 libm：6.82%；
- `__strncmp_avx2` 来自 libc：6.57%；
- `parse_path` 来自 `src/JSB-FlightSim/src/simgear/props/props.cxx`：6.12%，路径字符串的解析，拆分成多个 component；
- `SGPropertyNode::getChild` 来自 `src/JSB-FlightSim/src/simgear/props/props.cxx`：4.05%，遍历结点的子结点，通过字符串比较，找到匹配的子结点。

#### 7. orbit_torque2 和 8. orbit

热点函数与 6. orbit_torque 相同，不再赘述。

#### 小结

748.flightdm_r 是个没意思的基准测试，时间很多花在了 libm 和 libc 的函数上，自己的代码就是在配置文件里来回遍历，我愿称它为 libm 基准测试。除此之外，表现得更像一个 SPEC INT 2026 Rate 的负载：字符串操作，内存分配，很多小函数和 lambda，适合 `-O3 -flto` 优化。最后看一下 `-O3` 下各负载的情况：

| 负载             | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) | 错误预测 (M) | MPKI |
|------------------|----------|----------|----------|-----------|----------|--------------|--------------|--------------|------|
| 1. weather       | 5.9      | 106.1    | 30.8     | 15.4      | 19.5     | 12.9         | 0.6          | 11.6         | 0.11 |
| 2. B747          | 14.8     | 260.1    | 80.0     | 38.7      | 49.4     | 28.4         | 1.7          | 25.6         | 0.10 |
| 3. x153          | 10.8     | 193.3    | 59.1     | 28.7      | 37.3     | 20.0         | 1.0          | 20.9         | 0.11 |
| 4. c3104         | 11.4     | 194.6    | 58.9     | 29.1      | 35.7     | 23.9         | 1.3          | 18.2         | 0.09 |
| 5. ah1s          | 24.7     | 407.3    | 130.0    | 61.3      | 77.9     | 46.4         | 1.6          | 49.3         | 0.12 |
| 6. orbit_torque  | 7.9      | 152.8    | 41.9     | 22.7      | 28.3     | 16.3         | 1.1          | 24.2         | 0.16 |
| 7. orbit_torque2 | 9.9      | 191.4    | 52.5     | 28.4      | 35.3     | 21.0         | 1.2          | 17.1         | 0.09 |
| 8. orbit         | 8.4      | 161.6    | 44.3     | 23.9      | 30.0     | 17.2         | 1.0          | 16.3         | 0.10 |

乏善可陈。

### 749.fotonik3d_r

终于出现了一个 SPEC FP 2017 Rate 的老面孔，此前是 549.fotonik3d_r。fotonik3d 做的是 3D 空间里的麦克斯韦方程求解，又一个物理背景的基准测试，一般这种三维空间里的偏微分方程求解，必定会有 Stencil，下面看看这个猜测对不对。该基准测试只有一个负载：

```shell
fotonik3d_r
```

reftime 是 1156s，在不同编译选项下，749.fotonik3d_r 的运行情况：

| 编译器 + 选项                          | 时间 (s) | 分数  | 相比 GCC 14 `-O3` 性能提升 (%) | 指令数 (B) | Load 指令数 (B) | Store 指令数 (B) | 分支指令数 (B) | 浮点标量指令数 (B) | 浮点向量指令数 (B) |
|----------------------------------------|----------|-------|--------------------------------|------------|-----------------|------------------|----------------|--------------------|--------------------|
| GCC 14 `-O3`                           | 131.1    | 8.82  | 0                              | 1408.5     | 375.1           | 120.7            | 30.9           | 5.4                | 527.2              |
| GCC 14 `-O3 -march=native`             | 114.9    | 10.1  | 14                             | 670.1      | 274.1           | 82.4             | 27.1           | 5.5                | 249.4              |
| GCC 14 `-O3 -ffast-math`               | 116.7    | 9.91  | 12                             | 1117.6     | 378.4           | 120.8            | 30.7           | 4.8                | 396.2              |
| GCC 14 `-O3 -ffast-math -march=native` | 108.5    | 10.65 | 21                             | 599.5      | 276.3           | 82.3             | 26.9           | 4.8                | 204.8              |

LLVM 22 性能和 GCC 14 差不多，这里就不单列了。可见 `-O3 -march=native` 和 `-O3 -ffast-math` 都有不错的性能提升，下面进行热点分析：

- `power_dft` 来自 `src/power.F90`：30.92%，进行的是离散傅里叶变化 DFT，主要瓶颈是在循环中进行双精度浮点乘加运算，GCC 14 把它编译成 SSE 的向量指令；
- `UPML_updateE_simple` 来自 `src/UPML.F90`：24.73%，主要时间在进行三维的 Stencil 计算，果然物理模拟都离不开 Stencil 计算，GCC 14 编译出 SSE 向量指令进行计算；
- `UPML_updateH` 来自 `src/UPML.F90`：23.26%，依然是 3D 的 Stencil 计算，采用 SSE 向量指令；
- `mat_updateE` 来自 `src/material.F90`：11.04%，同样是 Stencil 计算，采用 SSE 向量指令；
- `updateH` 来自 `src/update.F90`：9.78%，也是 Stencil 计算，采用 SSE 向量指令。

由此可见，除了 `power_dft` 以外，大部分时间都在进行 Stencil 计算，这次 Stencil 计算的模式更加纯粹，因为 GCC 能够比较好地用 SSE 进行向量化。根据前面的经验，这类程序在 `-O3 -march=native`、`-O3 -ffast-math` 以及 `-O3 -ffast-math -march=native` 下都是有很大的提升的：

开启 `-march=native` 后，可以用更宽的 AVX2 向量，并行度更高，同时还能使用浮点乘加融合指令，例如 [`vfmaddsub231pd`](https://www.felixcloutier.com/x86/vfmaddsub132pd:vfmaddsub213pd:vfmaddsub231pd)。

开启 `-O3 -ffast-math` 以后，`power_dft` 中的核心计算，实际上计算的是，复数乘以实数再加复数，如下面的 Fortran 代码所示：

```c
subroutine update(Efreq1, Efreq2, expfuncE, Efield1, Efield2, n)
  implicit none
  integer, intent(in) :: n
  complex(8), intent(inout) :: Efreq1(n), Efreq2(n)
  complex(8), intent(in) :: expfuncE(n)
  real(8), intent(in) :: Efield1, Efield2
  integer :: i

  do i = 1, n
    Efreq1(i) = Efreq1(i) + expfuncE(i) * Efield1
    Efreq2(i) = Efreq2(i) + expfuncE(i) * Efield2
  end do
end subroutine update
```

在 `-O3` 时，GCC 14 会忠实地实现复数乘法，然而，实际上这里的 Efield1 和 Efield2 都是实数，转换过去的复数的虚部只能是零，因此通过 `-O3 -ffast-math` 的化简，直接把实部乘到 expfuncE 的实部和虚部即可，这样就可以简化指令。如果开 `-O3 -ffast-math -march=native`，将可以结合两个优化，直接用 AVX2 乘加融合指令 `vfmadd213pd` 完成这次运算，不需要像 `-O3 -march=native` 时用 `vfmaddsub231pd` 同时做加法和减法（原来的减，来自于复数乘法的定义，在这里减去的总是零，因为 Efield1/Efield2 的虚部是零），详见 [Godbolt](https://godbolt.org/z/v3W4e5xjP)。

小结一下，749.fotonik3d_r 是经典的浮点应用，大量 Stencil 加浮点向量运算，并行度高，适合向量化，还能享受 `-ffast-math` 带来的浮点计算顺序优化。

### 765.roms_r

又一个从 SPEC FP 2017 Rate 复活的基准测试，上一世是 554.roms_r，实现的是海洋模拟，不出意外依然是 Stencil，它只有一个负载：

```shell
roms_r < roms_benchmark2.in.x
```

reftime 是 1575s，不同编译器和编译选项下的运行情况：

| 编译器 + 选项               | 时间 (s) | 分数 | 相比 GCC 14 `-O3` 性能提升 (%) | 指令数 (B) | Load 指令数 (B) | Store 指令数 (B) | 分支指令数 (B) | 浮点标量指令数 (B) | 浮点向量指令数 (B) |
|-----------------------------|----------|------|--------------------------------|------------|-----------------|------------------|----------------|--------------------|--------------------|
| GCC 14 `-O3`                | 169.8    | 9.28 | 0                              | 2620.6     | 874.8           | 204.7            | 192.1          | 193.3              | 709.2              |
| GCC 14 `-O3 -march=native`  | 149.5    | 10.5 | 14                             | 1317.9     | 555.3           | 125.0            | 126.6          | 164.9              | 365.9              |
| GCC 14 `-O3 -ffast-math`    | 162.8    | 9.67 | 4                              | 2518.6     | 854.5           | 204.0            | 178.5          | 134.0              | 711.7              |
| LLVM 22 `-O3`               | 165.6    | 9.51 | 3                              | 2434.3     | 834.9           | 190.3            | 164.1          | 231.8              | 687.0              |
| LLVM 22 `-O3 -march=native` | 152.1    | 10.4 | 12                             | 1423.4     | 551.4           | 131.2            | 140.1          | 259.8              | 350.0              |

从以上数据就可以看出，浮点计算很多，高度可向量化，因此 `-O3 -march=native` 的性能提升是很正常的。

热点函数：

- `step2d_tile`，来自 `src/step2d_LF_AM3.h`：20.37%，主要瓶颈是 2D 的 Stencil 计算，向量化程度高；
- `pre_step3d` 来自 `src/pre_step3d.F90`：10.43%，主要瓶颈是在循环当中的浮点计算，向量化程度高；
- `lmd_skpp` 来自 `src/lmd_skpp.F90`：8.91%，主要瓶颈是循环中的复杂浮点计算，浮点标量计算为主；
- `step3d_t_tile` 来自 `src/step3d_t.F90`：7.04%，主要瓶颈是 3D 的 Stencil 计算，向量化程度高；
- `rhs3d` 来自 `src/rhs3d.F90`：6.04%，主要瓶颈是 2D 的 Stencil 计算，向量化程度高；
- `t3dmix2` 来自 `src/t3dmix2_geo.h`：5.86%，主要瓶颈是 3D Stencil 计算，向量化程度高；
- `step3d_uv_tile` 来自 `src/step3d_uv.F90`：5.85%，主要瓶颈是 3D Stencil 计算，向量化程度高；
- `_ZGVbN2v_exp_sse4` 来自 libmvec：4.66%，向量化版本的 exp。

还是典型的 Stencil 计算，向量化程度高。开 `-O3 -march=native` 后，向量宽度增加，加上 FMA 的引入，自然带来了不错的性能提升。

### 766.femflow_r

femflow 是流体动力学求解器，求解 Navier-Stokes 方程。该基准测试只包括一个负载：

```shell
femflow_r refrate.prm
```

reftime 是 1467s，不同编译器和编译选项下的运行情况：

| 编译器 + 选项               | 时间 (s) | 分数  | 相比 GCC 14 `-O3` 性能提升 (%) | 指令数 (B) | Load 指令数 (B) | Store 指令数 (B) | 分支指令数 (B) | 浮点标量指令数 (B) | 浮点向量指令数 (B) |
|-----------------------------|----------|-------|--------------------------------|------------|-----------------|------------------|----------------|--------------------|--------------------|
| GCC 14 `-O3`                | 188.7    | 7.77  | 0                              | 3862.4     | 1358.5          | 797.6            | 117.5          | 562.2              | 676.0              |
| GCC 14 `-O3 -march=native`  | 95.1     | 15.4  | 98                             | 1736.9     | 619.3           | 356.0            | 65.2           | 286.8              | 445.4              |
| GCC 16 `-O3`                | 153.6    | 9.55  | 23                             | 3178.6     | 1109.3          | 673.3            | 127.2          | 56.3               | 930.9              |
| GCC 16 `-O3 -march=native`  | 83.5     | 17.57 | 126                            | 1457.0     | 501.1           | 281.4            | 61.1           | 47.2               | 545.7              |
| LLVM 22 `-O3`               | 124.7    | 11.8  | 51                             | 2703.0     | 857.3           | 475.5            | 60.6           | 40.8               | 930.3              |
| LLVM 22 `-O3 -march=native` | 88.7     | 16.5  | 113                            | 1392.9     | 495.7           | 269.4            | 42.9           | 41.8               | 471.1              |

可见，LLVM 22 相比 GCC 14 有显著的性能提升，同时 `-O3 -march=native` 带来了更加显著的性能提升，是整个 SPEC FP 2026 Rate 当中，`-O3 -march=native` 带来提升第二高的基准测试，第一高是后面会看到的 772.marian_r。GCC 16 相比 GCC 14 也有不错的性能提升，开 `-O3 -march=native` 后反超 LLVM 22。

热点函数还不少，很多函数都是个位数百分比的占用，大多是一些算子：

- `Laplace::LaplaceOperator::local_apply_quadratic_geo` 来自 `src/laplace_operator.h`：5.49%，内部是大量的浮点向量计算，并行度高；
- `operator *(const dealii::VectorizedArray &, const dealii::VectorizedArray &)` 来自 `src/dealii/include/deal.ll/base/vectorization.h`：5.36%，两个向量的逐元素乘法。

其他还有一些 dealii:Tensor 的计算，包括来自 `src/dealii/include/deal.ll/matrix_free/tensor_product_kernels.h` 的 `dealii::internal::even_odd_apply`，里面都是大量的可向量化的浮点双精度运算。对于这类负载，`-O3 -march=native` 开启后，更快的向量长度带来了更好的浮点运算性能，同时还有 FMA 指令的加持。

LLVM 22 相比 GCC 14 的优势，主要来自于把更多代码进行了向量化，对比 GCC 14 和 LLVM 22 执行的指令数，可以看到 LLVM 22 执行的浮点标量指令数比 GCC 14 要少，而浮点向量指令又要多。GCC 16 也是类似的情况，向量化程度逼近 LLVM 22。

### 767.nest_r

nest 是个脉冲神经网络的模拟器，忽然出现一个熟悉的面孔，也挺难得。该基准测试分为三个负载：

```shell
# 1. cuba
nest_r cuba_stdp.sli
# 2. structural
nest_r structural_plasticity_benchmark
# 3. Artificial
nest_r ArtificialSynchrony
```

开 `-O3 -march=native` 只有 3% 的性能提升，LLVM 22 比 GCC 14 更慢，这里就不进行编译器和编译选项的对比了。三个负载在 GCC 14 `-O3` 下的对比：

| 负载          | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) |
|---------------|----------|----------|----------|-----------|----------|--------------|--------------|
| 1. cuba       | 14.1     | 176.3    | 54.5     | 21.6      | 22.4     | 29.2         | 0.0          |
| 2. structural | 24.6     | 413.3    | 136.3    | 42.8      | 52.5     | 93.2         | 0.0          |
| 3. Artificial | 48.6     | 1125.4   | 392.6    | 150.5     | 160.5    | 163.6        | 0.0          |

总时间 87.4s，reftime 是 793s，对应 9.07 分。下面进行负载的具体分析。

#### 1. cuba

热点函数：

- `nest::iaf_psc_exp::handle` 来自 `src/nest-simulator/models/iaf_psc_exp.cpp`：25.75%，处理该神经元接收到的脉冲，更新内部状态，主要瓶颈是间接访存，把脉冲的强度写入到对应的输入缓存区；
- `__ieee754_pow_fma` 来自 libm：11.96%，被后面的 `nest::Connector::send` 函数调用；
- `spec::poisson_distribution::operator()` 来自 `src/specrand-distributions/spec_random_distributions.cpp`：9.87%，生成随机数，以生成输入的脉冲；
- `nest::Connector::send` 来自 `src/nest-simulator/nestkernel/connector_base.h`：8.29%，负责脉冲在突触上的传播和 STDP，主要瓶颈是间接访存，以及内联了一些脉冲上的权重计算，还会调用 pow 和 exp；
- `nest::iaf_psc_exp::update` 来自 `src/nest-simulator/models/iaf_psc_exp.cpp`：6.91%，在每个时间步对神经元的状态进行更新，主要是标量的浮点运算。

算是一个比较经典的带 STDP 的 SNN 模拟，主要瓶颈就是脉冲传播和 STDP 的突触权重更新，向量化程度很低，还有间接访存。

#### 2. structural

热点函数：

- `spec::poisson_distribution::operator()` 来自 `src/specrand-distributions/spec_random_distributions.cpp`：24.26%，描述见上；
- `nest::iaf_psc_alpha::update` 来自 `src/nest-simulator/models/iaf_psc_alpha.cpp`：13.71%，做的事情和上面 `nest::iaf_psc_exp::update` 类似，就是换了个神经元模型；
- `__ieee754_pow_fma` 来自 libm：13.37%，描述见上；
- `nest::GrowthCurveGaussian::update` 来自 `src/nest-simulator/nestkernel/growth_curve.cpp`：6.60%，主要在用数值计算求解微分方程，频繁调用 exp 和 pow；
- `nest::iaf_psc_alpha::handle` 来自 `src/nest-simulator/models/iaf_psc_alpha.cpp`：25.75%，功能和上面 `nest::iaf_psc_exp::handle` 类似；
- `nest::Connector::send` 来自 `src/nest-simulator/nestkernel/connector_base.h`：6.60%，描述见上，这次没有 STDP，权重是静态的；
- `exp` 来自 `libm`：5.39%。

和 1. cuba 相比，换了一个神经元模型，去掉了 STDP，结果主要的瓶颈跑到了泊松分布的随机生成，其余部分还是比较典型的 SNN 模拟。

#### 3. Artificial

热点函数：

- `nest::iaf_psc_alpha_ps::update` 来自 `src/nest-simulator/models/iaf_psc_alpha_ps.cpp`：13.26%，神经元的状态更新函数；
- `nest::iaf_psc_alpha::update` 来自 `src/iaf_psc_alpha.cpp`：12.37%，描述见上；
- `nest::Connector::send` 来自 `src/nest-simulator/nestkernel/connector_base.h`：7.19%，描述见上，这次依然没有 STDP，权重是静态的；
- `nest::SimulationManager::update_` 来自 `src/nest-simulator/nestkernel/simulation_manager.cpp`：5.66%，核心的 SNN 模拟循环，调用上面的各种函数。
- `__ieee754_pow_fma` 来自 libm：5.17%，描述见上。

#### 小结

研究 SNN 的应该很熟悉，nest 是个很灵活的 SNN 模拟器，但单线程性能也确实不咋地，主要精力花在了多核/多线程上。不出所料，nest 的神经元更新部分没有向量化，所以挺慢的，而脉冲传播和 STDP 部分本来就很难优化。总之，这是个难以向量化的浮点应用，从上面的性能计数器来看，一条向量浮点指令都没有。

### 772.marian_r

marian_r 是一个基于神经网络的翻译器，又是一个神经网络推理，意味着又是一个 `-O3 -march=native` 非常有优势的测例，如果像 706.stockfish_r 那样有直接可以用的硬件加速指令，性能将会比 `-O3` 快得多。该基准测试包括两个负载：

```shell
# 1. TildeMODEL
marian-decoder --cpu-threads 1 -m model.alphas.npz -v vocab.spm vocab.spm --beam-size 1 --mini-batch 32 --maxi-batch 100 --maxi-batch-sort src -w 512 --skip-cost --gemm-type intgemm8 --intgemm-options precomputed-alpha standard-only --quiet --quiet-translation -i TildeMODEL-spec.en --log TildeMODEL-spec.log --log-level off -o TildeMODEL-spec.out
# 2. EuroPat
marian-decoder --cpu-threads 1 -m model.alphas.npz -v vocab.spm vocab.spm --beam-size 1 --mini-batch 32 --maxi-batch 100 --maxi-batch-sort src -w 512 --skip-cost --gemm-type intgemm8 --intgemm-options precomputed-alpha standard-only --quiet --quiet-translation -i EuroPat-spec.en --log EuroPat-spec.log --log-level off -o EuroPat-spec.out
```

reftime 是 1579s，下面是不同编译器版本和编译选项的对比：

| 编译器 + 选项              | 时间 (s) | 分数  | 相比 GCC 14 `-O3` 性能提升 (%) | 1. TildeMODEL 时间 (s) | 2. EuroPat 时间 (s) |
|----------------------------|----------|-------|--------------------------------|------------------------|---------------------|
| GCC 14 `-O3`               | 235.2    | 6.71  | 0                              | 88.8                   | 146.4               |
| GCC 14 `-O3 -march=native` | 78.4     | 20.14 | 200                            | 28.2                   | 50.3                |
| GCC 15 `-O3`               | 150.1    | 10.52 | 57                             | 56.0                   | 94.8                |
| GCC 15 `-O3 -march=native` | 77.5     | 20.37 | 203                            | 27.8                   | 49.7                |

可见 `-O3 -march=native` 带来的提升巨大，高达 200%，在 Apple M1 上有 47% 的提升，在 Apple M2 上更是提升了 92%，这种提升，之前只在 706.stockfish_r 上见到过。并且 GCC 15 也比 GCC 14 在 `-O3` 时有明显性能提升。下面分负载来讨论。

#### 1. TildeMODEL

热点函数：

- `marian::cpu::integer::affineOrDotTyped` 来自 `src/marian/tensors/cpu/intgemm_interface.h`：82.28%，主要时间在 `tiled_gemm` 函数里，做的是整数矩阵乘法，uint8_t 类型的 A 矩阵乘以 int8_t 类型的 B 矩阵，累加到 int32_t 类型，最后转换到 float 再加 float 的 C 矩阵；
- `marian::cpu::ProdBatched` 来自 `src/marian/tensors/cpu/prod.cpp`：10.30%，核心部分是 sgemm，这次确实是浮点的矩阵运算了，虽然被编译成了 SSE 的标量的浮点计算而不是向量，但考虑到时间占比，也无伤大雅了。

可以看到，主要的热点部分，和 706.stockfish_r 的 nnue 的计算模式完全一样，因此开 `-O3 -march=native` 后，一样可以用 vpdpbusd 指令优化，见 [Godbolt](https://godbolt.org/z/PTxK1evK3)。同理 GCC 15 因为更优的无符号扩展实现方式，性能比 GCC 14 要更好。具体的讨论，可以见之前 [INT Rate 篇](./spec-cpu-2026-workload-analysis-int-rate.md) 中 706.stockfish_r 的部分。

不同编译器和编译选项下的对比：

| 编译器 + 选项              | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) | 128 位整数向量 (B) | 256 位整数向量 (B) |
|----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|--------------------|--------------------|
| GCC 14 `-O3`               | 88.2     | 2038.9   | 217.8    | 57.8      | 53.2     | 58.7         | 2.1          | 514.6              | 0.0                |
| GCC 14 `-O3 -march=native` | 27.6     | 423.0    | 131.5    | 25.1      | 47.4     | 59.8         | 1.1          | 12.8               | 47.4               |
| GCC 15 `-O3`               | 55.6     | 1353.5   | 173.9    | 22.1      | 53.2     | 58.7         | 2.1          | 184.7              | 0.0                |
| GCC 15 `-O3 -march=native` | 27.3     | 415.1    | 128.9    | 23.5      | 47.5     | 59.8         | 1.1          | 12.8               | 47.4               |

其中 128 位整数向量来自 `int_vec_retired.128bit` 计数器，256 位整数向量来自 `int_vec_retired.256bit` 计数器。

#### 2. EuroPat

热点函数：

- `marian::cpu::integer::affineOrDotTyped`：78.96%，描述见上；
- `marian::cpu::ProdBatched`：14.25%，描述见上。

热点函数和 1. TileMODEL 完全相同，其余的分析对 2. EuroPat 也是成立的，这里直接给出性能计数器的对比：

不同编译器和编译选项下的对比：

| 编译器 + 选项              | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) | 128 位整数向量 (B) | 256 位整数向量 (B) |
|----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|--------------------|--------------------|
| GCC 14 `-O3`               | 145.6    | 3352.7   | 370.4    | 89.7      | 98.8     | 123.8        | 3.6          | 815.0              | 0.0                |
| GCC 14 `-O3 -march=native` | 49.7     | 777.2    | 228.7    | 36.6      | 88.3     | 123.9        | 1.7          | 19.9               | 72.6               |
| GCC 15 `-O3`               | 94.2     | 2268.5   | 301.7    | 33.1      | 98.8     | 123.8        | 3.6          | 293.6              | 0.0                |
| GCC 15 `-O3 -march=native` | 49.0     | 765.3    | 225.2    | 34.3      | 88.3     | 123.9        | 1.7          | 19.9               | 72.6               |

#### 小结

772.marian_r 鉴定为 706.stockfish_r 的 NNUE 翻版，热点就是 int8_t 乘 uint8_t 累加到 int32_t 的矩阵乘运算，整数向量指令比浮点指令还多，建议开除 SPEC FP 2026 Rate 籍。

### 782.lbm_r

lbm 是 lattice boltzmann method 的缩写，又是一个流体动力学的应用。该基准测试只有一个负载：

```shell
lbm_r 900 reference.dat 0 0 200_200_130_ldc.of
```

reftime 是 573s，不同编译选项下的性能对比：

| 编译器 + 选项              | 时间 (s) | 分数 | 相比 GCC 14 `-O3` 性能提升 (%) | 指令数 (B) | Load 指令数 (B) | Store 指令数 (B) | 分支指令数 (B) | 浮点标量指令数 (B) | 浮点向量指令数 (B) |
|----------------------------|----------|------|--------------------------------|------------|-----------------|------------------|----------------|--------------------|--------------------|
| GCC 14 `-O3`               | 105.8    | 5.42 | 0                              | 2232.2     | 473.3           | 242.4            | 14.5           | 1108.2             | 0.0                |
| GCC 14 `-O3 -ffast-math`   | 95.8     | 5.98 | 10                             | 1892.4     | 419.2           | 192.8            | 14.5           | 1009.5             | 0.0                |
| GCC 14 `-O3 -march=native` | 131.0    | 4.37 | -19                            | 1669.6     | 550.3           | 309.8            | 14.5           | 1228.8             | 0.0                |
| GCC 15 `-O3`               | 105.2    | 5.45 | 0.6                            | 2218.9     | 468.9           | 242.4            | 14.5           | 1108.2             | 0.0                |
| GCC 15 `-O3 -march=native` | 111.0    | 5.16 | -5                             | 1777.3     | 509.8           | 282.9            | 14.5           | 1108.2             | 0.0                |
| GCC 16 `-O3`               | 105.4    | 5.44 | 0.4                            | 2218.9     | 468.9           | 242.4            | 14.5           | 1108.2             | 0.0                |
| GCC 16 `-O3 -march=native` | 110.6    | 5.18 | -4                             | 1777.3     | 509.8           | 282.9            | 14.5           | 1108.2             | 0.0                |

热点函数只有一个，就是 `LBM_performStreamCollideTRT` 函数来自 `src/lbm.c`，占了 99.35% 的时间，中间有大量的浮点计算，而且都是标量，难以向量化，访存也不算多。对于这种标量计算很多的情况，`-O3 -ffast-math` 通常能带来一定的提升，通过调整计算顺序，可以复用一些中间计算结果，从而节省一些计算。

开启 `-O3 -march=native` 后，性能相比 `-O3` 有所落后，GCC 14 落后的幅度最大，GCC 15/16 落后幅度较小，但还是比不上 `-O3`。分析汇编代码，怀疑是因为开 `-O3 -march=native` 后，对栈的访存指令变多导致的，，抵消了 FMA 乘加融合减少的指令数优势，详见 [Godbolt](https://godbolt.org/z/5Ynsjn5o8)。

## 讨论

### 编译器选项对比

综合来看，编译选项对 SPEC FP 2026 Rate 的性能影响同样不小：

- `-march=native` 对很多基准测试有不错的性能提升。毕竟 AVX2 相比 SSE 不仅在宽度上拓宽，还增加了很多好用的指令，可以减少指令数，还有 AVX-VNNI 这种对 772.marian_r 特攻的；
- `-ffast-math` 也有不错的提升，尤其 SPEC FP 2026 Rate 有不少浮点运算，完全按照源码的编写方式去计算，往往不如调整运算顺序后来得快。但也要注意，`-ffast-math` 可能会导致计算结果不符合 IEEE 754 标准。
- `-flto` 和 `-ljemalloc` 对 SPEC FP 2026 Rate 的多数基准测试效果不大，但对 748.flightdm_r 有些许提升。

还有一些常用的编译参数，比如 `-static`、`-fomit-frame-pointer` 等等，目前没有做太多测试，以后说不定会加上。

### 分支预测

SPEC FP 2026 Rate 中 MPKI 特别高的只有 731.astcenc_r 和 737.gmsh_r，其他最高也就是 767.nest_r 的 0.87。731.astcenc_r 如此的高，完全是 GCC 14 编译的锅，换成 LLVM 22 立马就正常了，希望后续 GCC 能修一修。

## 总结

本文深入分析了 SPEC CPU 2026 中 FP Rate 的负载，供编译器和处理器的设计者参考。从编译器的角度来说，可以集 GCC 和 LLVM 之长，进一步提升性能；从处理器的角度来说，针对程序的瓶颈进行优化，也能进一步提高分数。
