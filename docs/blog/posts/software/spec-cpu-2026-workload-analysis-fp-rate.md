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

| 编译器+选项                 | 时间 (s) | 分数  | 相比 GCC 14 `-O3` 性能提升 (%) |
|-----------------------------|----------|-------|--------------------------------|
| GCC 14 `-O3`                | 103.4    | 8.30  | 0                              |
| GCC 14 `-O3 -march=native`  | 83.9     | 10.23 | 23                             |
| GCC 14 `-O3 -ffast-math`    | 101.2    | 8.48  | 2                              |
| GCC 14 `-O3 -ljemalloc`     | 100.7    | 8.52  | 3                              |
| LLVM 22 `-O3`               | 94.6     | 9.07  | 9                              |
| LLVM 22 `-O3 -march=native` | 90.5     | 9.48  | 14                             |

可见 `-march=native` 能提供巨大的性能提升，LLVM 22 在 `-O3` 下比 GCC 14 `-O3` 快，不过 GCC 14 的 `-O3 -march=native` 性能反超了 LLVM 22 的 `-O3 -march=native`，后面会进行具体分析。

通过 `perf` 观察性能瓶颈：

- `ML_CCZ4::ML_CCZ4_EvolutionInteriorSplitBy2_Body` 来自 `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_EvolutionInteriorSplitBy2.cc`：占总时间 41.30%，下同；
- `ML_CCZ4::ML_CCZ4_EvolutionInteriorSplitBy3_Body` 来自 `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_EvolutionInteriorSplitBy3.cc`：31.26%；
- `ML_CCZ4::ML_CCZ4_ConstraintsInterior_Body` 来自 `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_ConstraintsInterior_Body.cc`：6.71%；
- `ML_CCZ4::ML_CCZ4_EvolutionInteriorSplitBy1_Body` 来自 `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_EvolutionInteriorSplitBy3.cc`：6.44%。

这些热点函数的代码模式都是类似的：在三层循环里，读取对应三维空间中的点的数据，进行一系列的 Stencil 访存和浮点运算，包括大量的浮点乘法加法减法、pow 和 fabs，最后把结果写入对应数组。从指令来看，就是用大量的 SSE 指令来进行标量的双精度浮点运算，没有进行向量化。实验的时候，还观察到了编译器对 `pow` 和 `fabs` 的优化。在 `-O3` 时，`pow(a, 1)` 被编译成 `a`，`pow(a, 2)` 被编译成 `a * a`，`pow(a, -1)` 被编译成 `1.0 / a`，不过其他的例如 `pow(a, 3)` 和 `pow(a, -2)` 就只能转为 `libm` 的 `pow` 实现了。如果开了 `-O3 -ffast-math`，那么 `pow(a, 3)` 会编译成 `a * a * a`，`pow(a, -2)` 会被编译为 `1.0 / (a * a)`。两种编译选项的对比见 [Godbolt](https://godbolt.org/z/nKfGMfE49)。代码中，出现的主要就是 `pow(a, -1)`，`pow(a, 2)`、`pow(a, -2)` 和 `pow(a, runtimeVariable)`，其中 `runtimeVariable` 指一个在运行时才知道的数，在代码中对应 `shiftAlphaPower` 或 `harmonicN`。`fabs` 被编译成了位运算 `andpd` 指令，直接把符号位置零。

开启 `-O3 -march=native` 后，其实依然没有向量化，用 AVX2 指令计算双精度标量浮点，依然能看到对 `libm` 的 `pow` 的调用，就是上面提到的 `pow(a, -2)` 或 `pow(a, runtimeVariable)`，不过其余的计算部分因为能用 [`vfmadd132sd`](https://www.felixcloutier.com/x86/vfmadd132sd:vfmadd213sd:vfmadd231sd)/`vfnmadd132sd` 而获得了性能提升，同时 [`vaddsd`](https://www.felixcloutier.com/x86/addsd) 相比 [`addsd`](https://www.felixcloutier.com/x86/addsd) 从两操作数变为三操作数，还允许访存，进一步节省了指令数。而在 ARM64 平台上，开 `-march=native` 就没有性能提升，这是因为它的浮点乘加融合指令即使在没开 `-march=native` 的情况下也是可以使用的，见 [Godbolt](https://godbolt.org/z/nqMjY4EoY)。某种意义上来说，AMD64 上开 `-march=native` 有性能巨大提升，也是吃了先发劣势的亏：基线对应的处理器太早，缺少很多重要的指令集扩展，这种兼容性负担在很多其他指令集上不会出现，例如乘加融合 FMA 指令很多指令集里已经在基线当中，在这些指令集上，开 `-march=native` 的提升就会相对来说更低。所以现在很多软件会曲线救国，为了保证兼容性，针对多个不同指令集扩展分别做手动适配，在运行时根据可用性选择性能最好的那一个。如果编译器能很好地自动完成这一点，将会在保持兼容性和开发便捷性的前提下，带来不错的系统整体性能提升。

不同编译选项的情况对比：

| 编译器+选项                 | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|
| GCC 14 `-O3`                | 103.4    | 1423.6   | 747.8    | 110.1     | 9.8      | 677.0        | 5.2          |
| GCC 14 `-O3 -march=native`  | 83.9     | 988.5    | 711.9    | 89.5      | 8.9      | 686.1        | 2.6          |
| GCC 14 `-O3 -ffast-math`    | 101.8    | 1387.7   | 742.2    | 103.4     | 5.3      | 641.0        | 5.6          |
| GCC 14 `-O3 -ljemalloc`     | 100.7    | 1423.6   | 747.8    | 110.1     | 9.8      | 677.0        | 5.2          |
| LLVM 22 `-O3`               | 94.6     | 1323.1   | 659.1    | 96.6      | 6.1      | 659.0        | 15.2         |
| LLVM 22 `-O3 -march=native` | 90.5     | 1054.5   | 690.7    | 119.4     | 5.4      | 681.4        | 5.4          |

其中总指令数来自 `instructions`，Load 指令数来自 `mem_inst_retired.all_loads`，Store 指令数来自 `mem_inst_retired.all_stores`，分支指令数来自 `branch-instructions`，浮点标量指令数用 `fp_arith_inst_retired.scalar` 浮点向量指令数用 `fp_arith_inst_retired.vector` 性能计数器，下同。需要注意的是，`vfmadd132sd` 等乘加融合指令在 `fp_arith_inst_retired.scalar/vector` 计数器中会被计算两次。

从表里可以看出，`-O3` 下基本是一半指令在 Load，另一半指令在做浮点标量运算，这个计算访存比还是挺低的，这是 Stencil 计算的典型特征，在网格邻域里，Load 一个值进来，做一次乘加。开 `-O3 -march=native` 后，因为乘加融合指令的加持，指令数减少了很多，但因为乘加融合会算两倍的贡献，并且那些同时进行访存和计算的 AVX2 指令也会被同时计入到 Load 和浮点指令数，估计微架构是统计的拆分后的微码数量，那么总指令数不再等于各类指令数求和。这里 `-O3 -ljemalloc` 带来了些许的性能优势，不过指令数上并没有体现，不确定它的性能提升主要是来自哪里。GCC 14 和 LLVM 22 在不同编译选项下各有千秋，大概看了一下生成的指令，其实实现方法都差不多，主要是地址计算、栈的使用和寄存器分配有一些区别。

### 722.palm_r

palm 是一个天气预报相关的程序，做的是 Navier Stokes 方程的求解，命令如下：

```shell
palm_r < runfile_atmos
```

实测数据显示，运行时间 174.0s，reftime 是 1320s，对应 7.59 分。不同编译器和编译选项对 722.palm_r 的优化情况：

| 编译器+选项                 | 时间 (s) | 分数  | 相比 GCC 14 `-O3` 性能提升 (%) |
|-----------------------------|----------|-------|--------------------------------|
| GCC 14 `-O3`                | 174.0    | 7.50  | 0                              |
| GCC 14 `-O3 -march=native`  | 157.8    | 8.34  | 10                             |
| GCC 14 `-O3 -ffast-math`    | 168.4    | 7.84  | 3                              |
| GCC 14 `-O3 -ljemalloc`     | 172.4    | 7.66  | 1                              |
| LLVM 22 `-O3`               | 144.0    | 9.17  | 21                             |
| LLVM 22 `-O3 -march=native` | 118.6    | 10.37 | 47                             |

与 709.cactus_r 的趋势相同，`-O3 -march=native` 能提供巨大的性能提升，而 LLVM 22 也明显比 GCC 14 要快。

热点函数：

- `advec_s_ws_ij` 来自 `src/advec_ws.F90`：9.80%，经典的 3 维上的 Stencil 计算，访存和计算的比例接近，基本是 load 一个点的数值然后就做对应的乘加，用 SSE 指令来做计算，有部分向量化计算，例如 addpd/subpd/mulpd 等，每条指令处理 2 个双精度浮点元素，不过也有一些循环没能成功向量化，退化到 addsd/subsd/mulsd 等浮点标量指令；
- `advec_u_ws_ij` 来自 `src/advec_ws.F90`：8.80%，同上；
- `advec_v_ws_ij` 来自 `src/advec_ws.F90`：8.54%，同上；
- `advec_w_ws_ij` 来自 `src/advec_ws.F90`：8.24%，同上；
- `diffusion_e_ij` 来自 `src/turbulence_closure_mod.F90`：5.14%，有一些比较复杂的浮点运算，比如 min/sqrt/div 等等，还有位运算，用 `MERGE` 来进行 ternary operator，无向量化，用 SSE 指令来做标量浮点计算。

不同编译选项的情况对比：

| 编译器+选项                 | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|--------------|
| GCC 14 `-O3`                | 174.0    | 3416.6   | 1267.4   | 271.1     | 155.6    | 779.0        | 318.5        |
| GCC 14 `-O3 -march=native`  | 157.8    | 2710.0   | 1212.8   | 242.5     | 147.1    | 785.9        | 172.6        |
| GCC 14 `-O3 -ffast-math`    | 168.4    | 3373.5   | 1204.7   | 278.0     | 134.0    | 612.8        | 363.1        |
| GCC 14 `-O3 -ljemalloc`     | 172.4    | 3368.4   | 1259.7   | 260.7     | 141.6    | 779.0        | 318.5        |
| LLVM 22 `-O3`               | 144.0    | 2640.4   | 835.5    | 216.3     | 90.4     | 179.5        | 609.7        |
| LLVM 22 `-O3 -march=native` | 118.6    | 1643.8   | 586.5    | 165.6     | 67.6     | 180.8        | 306.7        |

开 `-O3 -march=native` 后，能看到的是大量的 AVX2 向量化指令：vmulpd/vdivsd/vaddpd/vsubpd/vfmadd213sd/vfmsub132pd/vfmsub231pd/vmovupd 等等，每次处理 4 个双精度浮点元素，向量化程度很高，如果在有 AVX512 的处理器上，可能性能还会更高。相比 709.cactus_r 那样被 pow 等问题限制没能向量化，722.palm_r 的向量化收益是特别明显的。LLVM 22 在 `-O3` 下比 GCC 14 要好，是因为它在热点函数的更多部分成功进行向量化，体现在数据上就是浮点向量指令数明显增多，浮点标量指令数明显减少。在 LLVM 22 下，由于上述热点函数被优化地比较好，也出现了新的热点函数，时间占比 5.79%：`flow_statistics` 来自 `src/flow_statistics.F90`，它能正确向量化的部分比较少，因而时间占比提升，即使开了 `-O3 -march=native`，也还是用 AVX2+FMA 指令来做标量计算，时间区别不大，因为其他部分时间降低，自己的时间占比提高到 6.95%。

709.cactus_r 和 722.palm_r 其实计算模式都是 Stencil，这在物理相关的模拟中很常见，因为要在三维空间里求解微分方程，为了数值求解，最后都落到了在每个点的邻域里进行计算，基本就是 Stencil。

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

| 编译器+选项                 | 总时间 (s) | 1. linear 时间 (s) | 2. hdr 时间 (s) | 3. precision 时间 (s) | 分数 | 相比 GCC 14 `-O3` 性能提升 (%) |
|-----------------------------|------------|--------------------|-----------------|-----------------------|------|--------------------------------|
| GCC 14 `-O3`                | 175.8      | 49.9               | 72.1            | 53.8                  | 4.78 | 0                              |
| GCC 14 `-O3 -march=native`  | 157.3      | 44.0               | 63.2            | 50.0                  | 5.34 | 12                             |
| GCC 14 `-O3 -ffast-math`    | 160.5      | 44.6               | 67.2            | 48.7                  | 5.23 | 10                             |
| LLVM 22 `-O3`               | 134.0      | 38.5               | 56.1            | 39.3                  | 6.27 | 31                             |
| LLVM 22 `-O3 -march=native` | 117.2      | 34.4               | 48.6            | 34.1                  | 7.17 | 50                             |

又是 LLVM 22 相比 GCC 14 有明显优势的一个测例。其他对性能几乎没有影响的优化选项包括 `-flto` 和 `-ljemalloc`，这里就不具体列举了。731.astcenc_r 是 SPEC FP 2026 Rate 中 MPKI 最高的那一个，高达 5.0，相比其他大多数不到 1.0 的 MPKI 来说很高（第二高的是 737.gmsh_r，MPKI 达到了 3.33，第三高 767.nest_r 的 MPKI 只有 0.83），也比 SPEC INT 2026 Rate 的不少测例更高。下面分命令来进行分析。

#### 1. linear

主要热点函数：

- `compute_angular_endpoints_for_quant_levels` 来自 `src/astcenc_weight_align.cpp`：18.93%，主要瓶颈是在中间的循环，在用 SSE 做一些单精度浮点的标量计算，中间还有一些对来自 `libm` 的 `nearbyint` 调用，进行 round 操作，从代码来看，开发者有意识地写一些适合编译器去向量化的代码，比如用 `vfloat4` 类型来做一些批量操作，还有 `vmask4` 类型保存 `vfloat4` 比较的结果（`vmask4` 保存了四个 int，用 0 代表 false，用 -1 代表 true），再用 `select` 函数来进行向量化的 ternary operator，可惜编译器并不领情，编译出来依然是标量 SSE；
- `compute_avgs_and_dirs_3_comp_rgb` 来自 `src/astcenc_averages_and_directions.cpp`：14.70%，模式和上面类似，在循环中做一些 `vfloat4` 和 `vmask4` 的计算，但 SSE 指令都是标量的；
- `compute_quantized_weights_for_decimation` 来自 `src/astcenc_ideal_endpoints_and_weights.cpp`：13.34%，在循环中做一些不过因为涉及到量化，有一些 `vint` 参与以及查表 `vtable_lookup_32bit`，这里 `vfloat`/`vint` 本来代表的是根据平台能提供的 SIMD 宽度进行一个自动的映射（定义在 `src/astcenc_vecmathlib.h` 中，比如 AVX 就是 8 个元素，vfloat 映射到 vfloat8；SSE 就是 4 个元素，vfloat 映射到 vfloat4），不过显然这些在 SPEC 里都被禁用了，fallback 到了 4 个元素的情况；
- `compute_ideal_weights_for_decimation` 来自 `src/astcenc_ideal_endpoints_and_weights.cpp`：9.57%，主要瓶颈是在一个 gather 操作 `gatherf_byte_inds` 里，不过因为 SSE 不支持 gather，所以是拆成四个元素分别进行 load 和标量计算的；
- `bilinear_infill_vla` 来自 `src/astcenc_ideal_endpoints_and_weights.cpp`：7.80%，瓶颈一样是 gather，即 `gatherf_byte_inds` 函数；
- `compute_error_squared_rgb` 来自 `src/astcenc_averages_and_directions.cpp`：6.39%，瓶颈一样是 gather，以及 gather 之后的一系列向量计算，但 GCC 14 都编译成了 SSE 标量计算。

针对这种用原生 SIMD 写法的程序，编译出来却又都是 SSE 标量指令，那意味如果能用 SSE 进行向量化，将会有明显的性能提升；进一步，如果开了 `-O3 -march=native`，向量更宽来到 256 位，并且还能用 [`vblendvps`](https://www.felixcloutier.com/x86/blendvps) 指令来实现上述 `select` 函数。前面提到过，LLVM 22 明显更快，于是做了不同编译器和编译选项下的对比：

| 编译器+选项                 | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 浮点标量 (B) | 浮点向量 (B) | 错误预测 (B) | MPKI |
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

剩余的指令只是为了解决调用约定的数据存放位置问题，实际在函数内部计算的时候，通常就一条 `maxps` 指令完成所有 4 个元素的 max 计算。从这个例子也可以看出，为啥 LLVM 22 比 GCC 14 要快得多：GCC 14 多了很多无用的分支来解决 `select` 里的比较，而且还不能向量化 max 操作。即使给 GCC 14 开 `-march=native`，它依然还在用 AVX 指令进行标量 max 运算，真是难绷。上述编译结果可见 [Godbolt](https://godbolt.org/z/Y8Ps15n39)。GCC 14 的 MPKI 那么高，其实都是这么来的，也挺搞笑。我还测试了一下，发现相同的代码在 LoongArch 下也没有得到很好的向量化支持（见 [Godbolt](https://godbolt.org/z/qTsaMnzhe)），因此提了一个 [issue](https://github.com/loongson-community/discussions/issues/120)。

#### 2. hdr

#### 3. precision
