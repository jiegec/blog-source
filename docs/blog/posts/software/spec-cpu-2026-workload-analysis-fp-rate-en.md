---
layout: post
date: 2026-05-29
tags: [benchmark,spec,speccpu2026]
categories:
    - software
---

# SPEC CPU 2026 Workload Analysis (FP Rate)

[中文版本](spec-cpu-2026-workload-analysis-fp-rate.md)

## Background

Following the [INT Rate article](./spec-cpu-2026-workload-analysis-int-rate-en.md), this article continues with the workload analysis of SPEC FP 2026 Rate.

<!-- more -->

The test environment is the same as the previous [INT Rate article](./spec-cpu-2026-workload-analysis-int-rate-en.md) and won't be repeated here.

Recommended reading: [Evaluating SPEC CPU2026](https://chipsandcheese.com/p/evaluating-spec-cpu2026) and [SPEC CPU2026: Characterization, Representativeness, and Cross-Suite Comparison](https://arxiv.org/abs/2605.03713v2)

## SPEC FP 2026 Rate Analysis

### 709.cactus_r

Cactus is a computational framework, used here to solve the Einstein equations in vacuum. Command:

```shell
cactus ShiftedGaugeWave.par
```

Measured runtime is 103.4s, reftime is 858s, corresponding to 8.30 points. Performance under different compilers and flags:

| Compiler + Flags            | Time (s) | Score | Improvement over GCC 14 `-O3` (%) |
|-----------------------------|----------|-------|-----------------------------------|
| GCC 14 `-O3`                | 103.4    | 8.30  | 0                                 |
| GCC 14 `-O3 -march=native`  | 83.9     | 10.23 | 23                                |
| GCC 14 `-O3 -ffast-math`    | 101.2    | 8.48  | 2                                 |
| GCC 14 `-O3 -ljemalloc`     | 100.7    | 8.52  | 3                                 |
| LLVM 22 `-O3`               | 94.6     | 9.07  | 9                                 |
| LLVM 22 `-O3 -march=native` | 90.5     | 9.48  | 14                                |

`-march=native` provides a significant performance boost. LLVM 22 is faster than GCC 14 under `-O3`, but GCC 14's `-O3 -march=native` overtakes LLVM 22's `-O3 -march=native`. Details below.

Performance bottlenecks observed via `perf`:

- `ML_CCZ4::ML_CCZ4_EvolutionInteriorSplitBy2_Body` from `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_EvolutionInteriorSplitBy2.cc`: 41.30% of total time (same format below);
- `ML_CCZ4::ML_CCZ4_EvolutionInteriorSplitBy3_Body` from `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_EvolutionInteriorSplitBy3.cc`: 31.26%;
- `ML_CCZ4::ML_CCZ4_ConstraintsInterior_Body` from `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_ConstraintsInterior_Body.cc`: 6.71%;
- `ML_CCZ4::ML_CCZ4_EvolutionInteriorSplitBy1_Body` from `src/repos/mclachlan/ML_CCZ4/src/ML_CCZ4_EvolutionInteriorSplitBy3.cc`: 6.44%.

These hotspot functions share a similar pattern: within three nested loops, they read data from corresponding 3D grid points, perform a series of Stencil memory accesses and floating-point operations (including heavy use of floating-point multiply, add, subtract, pow, and fabs), then write results back to arrays. The generated instructions use SSE for scalar double-precision floating-point without vectorization. During testing, compiler optimizations on `pow` and `fabs` were also observed. Under `-O3`, `pow(a, 1)` compiles to `a`, `pow(a, 2)` to `a * a`, and `pow(a, -1)` to `1.0 / a`, but others like `pow(a, 3)` and `pow(a, -2)` fall back to libm's `pow` implementation. With `-O3 -ffast-math`, `pow(a, 3)` becomes `a * a * a` and `pow(a, -2)` becomes `1.0 / (a * a)`. See the comparison at [Godbolt](https://godbolt.org/z/nKfGMfE49). In the code, the main occurrences are `pow(a, -1)`, `pow(a, 2)`, `pow(a, -2)`, and `pow(a, runtimeVariable)`, where `runtimeVariable` is a value only known at runtime, corresponding to `shiftAlphaPower` or `harmonicN` in the code. `fabs` is compiled into the bitwise `andpd` instruction, directly zeroing the sign bit.

With `-O3 -march=native`, vectorization still doesn't happen. It uses AVX2 instructions for scalar double-precision floating-point, with remaining calls to libm's `pow` for the cases mentioned above (`pow(a, -2)` or `pow(a, runtimeVariable)`). However, the rest of the computation benefits from [`vfmadd132sd`](https://www.felixcloutier.com/x86/vfmadd132sd:vfmadd213sd:vfmadd231sd)/`vfnmadd132sd`, and [`vaddsd`](https://www.felixcloutier.com/x86/addsd) becomes a three-operand instruction (compared to the two-operand [`addsd`](https://www.felixcloutier.com/x86/addsd)) that also allows memory operands, further reducing instruction count. On ARM64, `-march=native` provides no improvement because the floating-point fused multiply-add instruction is available even without `-march=native`, see [Godbolt](https://godbolt.org/z/nqMjY4EoY). In a sense, the huge improvement from `-march=native` on AMD64 reflects a first-mover disadvantage: the baseline corresponds to very old processors lacking many important ISA extensions. This compatibility burden doesn't exist on many other ISAs; for instance, fused multiply-add (FMA) is already part of the baseline in many ISAs, where `-march=native` brings relatively smaller improvements. As a workaround, many software projects manually provide multiple code paths for different ISA extensions and select the best one at runtime based on availability. If compilers could do this automatically, it would bring nice overall performance improvements while maintaining compatibility and developer convenience.

Performance counter comparison across compilation options:

| Compiler + Flags            | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) |
|-----------------------------|----------|-----------|----------|-----------|------------|---------------|---------------|
| GCC 14 `-O3`                | 103.4    | 1423.6    | 747.8    | 110.1     | 9.8        | 677.0         | 5.2           |
| GCC 14 `-O3 -march=native`  | 83.9     | 988.5     | 711.9    | 89.5      | 8.9        | 686.1         | 2.6           |
| GCC 14 `-O3 -ffast-math`    | 101.8    | 1387.7    | 742.2    | 103.4     | 5.3        | 641.0         | 5.6           |
| GCC 14 `-O3 -ljemalloc`     | 100.7    | 1423.6    | 747.8    | 110.1     | 9.8        | 677.0         | 5.2           |
| LLVM 22 `-O3`               | 94.6     | 1323.1    | 659.1    | 96.6      | 6.1        | 659.0         | 15.2          |
| LLVM 22 `-O3 -march=native` | 90.5     | 1054.5    | 690.7    | 119.4     | 5.4        | 681.4         | 5.4           |

Total instruction count comes from `instructions`, Load from `mem_inst_retired.all_loads`, Store from `mem_inst_retired.all_stores`, Branch from `branch-instructions`, FP Scalar from `fp_arith_inst_retired.scalar`, and FP Vector from `fp_arith_inst_retired.vector` performance counters (same format below). Note that fused multiply-add instructions like `vfmadd132sd` are counted twice in `fp_arith_inst_retired.scalar/vector`.

From the table, under `-O3` roughly half the instructions are Loads and the other half are floating-point scalar operations. This low compute-to-memory ratio is typical of Stencil computation: load a value from the grid neighborhood, do one multiply-add. With `-O3 -march=native`, FMA instructions reduce the instruction count substantially, but since FMA counts double and AVX2 instructions that perform both memory access and computation are counted in both Load and FP categories (the microarchitecture likely counts split micro-ops), the total instruction count no longer equals the sum of individual categories. The `-O3 -ljemalloc` option provides a slight performance advantage not reflected in instruction counts; its improvement mainly comes from better cache locality. GCC 14 and LLVM 22 have comparable performance under different flags. The generated instructions are similar in approach, with main differences in address computation, stack usage, and register allocation.

Notably, 709.cactus_r has high cache miss rates: under GCC 14 `-O3`, L1 ICache MPKI reaches `118.6B/1423.6B*1000=83.30`, and L1 DCache MPKI is `125.6B/1423.6B*1000=88.23`, the highest among both SPEC FP 2026 Rate and SPEC INT 2026 Rate. Cores with larger L1 ICache have an advantage here; L1 ICache bottlenecks at 32KB might disappear at 64KB. With `-O3 -ljemalloc`, L1 DCache MPKI drops to `111.7B/1423.6B*1000=78.46`, yielding about 3% improvement with identical instruction counts compared to `-O3`.

### 722.palm_r

palm is a weather forecasting program that solves Navier-Stokes equations. Command:

```shell
palm_r < runfile_atmos
```

Measured runtime is 174.0s, reftime is 1320s, corresponding to 7.59 points. Performance under different compilers and flags:

| Compiler + Flags            | Time (s) | Score | Improvement over GCC 14 `-O3` (%) |
|-----------------------------|----------|-------|-----------------------------------|
| GCC 14 `-O3`                | 174.0    | 7.59  | 0                                 |
| GCC 14 `-O3 -march=native`  | 157.8    | 8.34  | 10                                |
| GCC 14 `-O3 -ffast-math`    | 168.4    | 7.84  | 3                                 |
| GCC 14 `-O3 -ljemalloc`     | 172.4    | 7.66  | 1                                 |
| LLVM 22 `-O3`               | 144.0    | 9.17  | 21                                |
| LLVM 22 `-O3 -march=native` | 118.6    | 11.13 | 47                                |

The trend is similar to 709.cactus_r: `-O3 -march=native` provides a massive performance boost, and LLVM 22 is significantly faster than GCC 14.

Hotspot functions:

- `advec_s_ws_ij` from `src/advec_ws.F90`: 9.80%, classic 3D Stencil computation with balanced memory access and computation ratio, essentially load one point value then do multiply-add. Uses SSE for computation with partial vectorization (addpd/subpd/mulpd processing 2 double-precision elements per instruction), though some loops fail to vectorize and fall back to scalar instructions (addsd/subsd/mulsd);
- `advec_u_ws_ij` from `src/advec_ws.F90`: 8.80%, same as above;
- `advec_v_ws_ij` from `src/advec_ws.F90`: 8.54%, same as above;
- `advec_w_ws_ij` from `src/advec_ws.F90`: 8.24%, same as above;
- `diffusion_e_ij` from `src/turbulence_closure_mod.F90`: 5.14%, involves more complex floating-point operations like min/sqrt/div, plus bitwise operations using `MERGE` for ternary operations, no vectorization, scalar SSE floating-point.

Here is the Stencil computation code from `advec_s_ws_ij`, looping over i, j, k:

```fortran
flux_r(k) = u_comp * (                                                                &
              37.0_wp * ( sk(k,j,i+1) + sk(k,j,i)   )                                 &
            -  8.0_wp * ( sk(k,j,i+2) + sk(k,j,i-1) )                                 &
            +           ( sk(k,j,i+3) + sk(k,j,i-2) ) ) * adv_sca_5
```

Performance counter comparison:

| Compiler + Flags            | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) |
|-----------------------------|----------|-----------|----------|-----------|------------|---------------|---------------|
| GCC 14 `-O3`                | 174.0    | 3416.6    | 1267.4   | 271.1     | 155.6      | 779.0         | 318.5         |
| GCC 14 `-O3 -march=native`  | 157.8    | 2710.0    | 1212.8   | 242.5     | 147.1      | 785.9         | 172.6         |
| GCC 14 `-O3 -ffast-math`    | 168.4    | 3373.5    | 1204.7   | 278.0     | 134.0      | 612.8         | 363.1         |
| GCC 14 `-O3 -ljemalloc`     | 172.4    | 3368.4    | 1259.7   | 260.7     | 141.6      | 779.0         | 318.5         |
| LLVM 22 `-O3`               | 144.0    | 2640.4    | 835.5    | 216.3     | 90.4       | 179.5         | 609.7         |
| LLVM 22 `-O3 -march=native` | 118.6    | 1643.8    | 586.5    | 165.6     | 67.6       | 180.8         | 306.7         |

With `-O3 -march=native`, heavy AVX2 vectorized instructions appear: vmulpd/vdivsd/vaddpd/vsubpd/vfmadd213sd/vfmsub132pd/vfmsub231pd/vmovupd, each processing 4 double-precision elements. Vectorization degree is high; on AVX512-capable processors, performance could be even higher. Compared to 709.cactus_r where pow and similar issues prevent vectorization, 722.palm_r's vectorization benefits are much more apparent. LLVM 22 under `-O3` outperforms GCC 14 because it successfully vectorizes hotspot functions like `advec_u/v/w_ws_ij`, while GCC 14 still uses scalar instructions. This is reflected in significantly more FP vector instructions and fewer FP scalar instructions. Under LLVM 22, with those hotspot functions well-optimized, `flow_statistics` (from `src/flow_statistics.F90`, 5.79% time share) becomes the new bottleneck. It has limited vectorizable portions, hence its time share increases. Even with `-O3 -march=native`, it still uses AVX2+FMA instructions for scalar computation with little time difference. As other parts speed up, its time share further increases to 6.95%, similar to Amdahl's law.

709.cactus_r and 722.palm_r share the same Stencil computation pattern. Physics simulations frequently do this: solving differential equations in 3D space requires repeated computation over each point's neighborhood, which ultimately becomes Stencil.

### 731.astcenc_r

astcenc is an encoder for the ASTC lossy compressed image format. It runs three times:

```shell
# 1. linear
astcenc_r ref-inputs-linear.txt
# 2. hdr
astcenc_r ref-inputs-hdr.txt
# 3. precision
astcenc_r ref-inputs-precision.txt
```

Measured runtimes are 49.9s, 72.1s, and 53.8s, totaling 175.8s, reftime 840s, corresponding to 4.78 points. Performance under different compilers and flags:

| Compiler + Flags            | Total Time (s) | 1. linear (s) | 2. hdr (s) | 3. precision (s) | Score | Improvement over GCC 14 `-O3` (%) |
|-----------------------------|----------------|---------------|------------|------------------|-------|-----------------------------------|
| GCC 14 `-O3`                | 175.8          | 49.9          | 72.1       | 53.8             | 4.78  | 0                                 |
| GCC 14 `-O3 -march=native`  | 157.3          | 44.0          | 63.2       | 50.0             | 5.34  | 12                                |
| GCC 14 `-O3 -ffast-math`    | 160.5          | 44.6          | 67.2       | 48.7             | 5.23  | 10                                |
| LLVM 22 `-O3`               | 134.0          | 38.5          | 56.1       | 39.3             | 6.27  | 31                                |
| LLVM 22 `-O3 -march=native` | 117.2          | 34.4          | 48.6       | 34.1             | 7.17  | 50                                |

Another benchmark where LLVM 22 has a clear advantage over GCC 14. Other flags like `-flto` and `-ljemalloc` have almost no impact and are omitted. 731.astcenc_r has the highest MPKI in SPEC FP 2026 Rate at 5.0, much higher than most others which are below 1.0 (second highest is 737.gmsh_r at 3.33, third is 767.nest_r at only 0.83), and also higher than many SPEC INT 2026 Rate benchmarks. Below is per-workload analysis.

#### 1. linear

Main hotspot functions:

- `compute_angular_endpoints_for_quant_levels` from `src/astcenc_weight_align.cpp`: 18.93%, main bottleneck is in the inner loop doing single-precision floating-point scalar SSE computation, with calls to `nearbyint` from libm for rounding. The developers intentionally wrote SIMD-friendly code using `vfloat4` for batch operations, with `vmask4` storing comparison results (four ints, 0 for false, -1 for true), and a `select` function for vectorized ternary operations. Unfortunately the compiler doesn't cooperate, producing scalar SSE instead;
- `compute_avgs_and_dirs_3_comp_rgb` from `src/astcenc_averages_and_directions.cpp`: 14.70%, similar pattern with `vfloat4` and `vmask4` computations in loops, but SSE instructions are all scalar;
- `compute_quantized_weights_for_decimation` from `src/astcenc_ideal_endpoints_and_weights.cpp`: 13.34%, involves quantization with `vint` and table lookups (`vtable_lookup_32bit`). The `vfloat`/`vint` types are designed to automatically map to the platform's available SIMD width (defined in `src/astcenc_vecmathlib.h`, e.g., AVX maps to 8 elements with vfloat8, SSE to 4 elements with vfloat4), but these wider modes are disabled in SPEC, falling back to 4 elements;
- `compute_ideal_weights_for_decimation` from `src/astcenc_ideal_endpoints_and_weights.cpp`: 9.57%, main bottleneck is a gather operation `gatherf_byte_inds`. Since SSE doesn't support gather, it splits into four elements with individual loads and scalar computation;
- `bilinear_infill_vla` from `src/astcenc_ideal_endpoints_and_weights.cpp`: 7.80%, bottleneck is also the gather operation `gatherf_byte_inds`;
- `compute_error_squared_rgb` from `src/astcenc_averages_and_directions.cpp`: 6.39%, bottleneck is gather plus subsequent vector computation, but GCC 14 compiles everything to scalar SSE.

The fact that native SIMD code compiles to scalar instructions also suggests that correct vectorization would yield significant additional performance. Furthermore, with `-O3 -march=native`, vectors widen to 256 bits, and the [`vblendvps`](https://www.felixcloutier.com/x86/blendvps) instruction becomes available to implement the `select` function. As mentioned, LLVM 22 is significantly faster. Here's the comparison:

| Compiler + Flags            | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) | Mispred (M) | MPKI |
|-----------------------------|----------|-----------|----------|-----------|------------|---------------|---------------|-------------|------|
| GCC 14 `-O3`                | 49.9     | 835.7     | 259.3    | 55.6      | 63.2       | 188.6         | 28.6          | 3136.0      | 3.75 |
| GCC 14 `-O3 -march=native`  | 44.0     | 652.4     | 234.0    | 46.3      | 52.9       | 184.6         | 28.5          | 3148.2      | 4.83 |
| GCC 14 `-O3 -ffast-math`    | 44.6     | 780.5     | 259.8    | 54.6      | 49.3       | 159.9         | 43.2          | 2139.0      | 2.74 |
| LLVM 22 `-O3`               | 38.5     | 829.7     | 235.0    | 34.8      | 36.1       | 68.8          | 155.6         | 1095.5      | 1.32 |
| LLVM 22 `-O3 -march=native` | 34.4     | 620.9     | 179.5    | 17.7      | 19.6       | 42.1          | 125.7         | 823.4       | 1.33 |

The counters show GCC 14 performs worse overall because LLVM 22 does more vectorization: its FP vector instructions far exceed FP scalar, with significantly fewer mispredictions and much lower MPKI. Detailed analysis follows.

First, let's look at how GCC 14 compiles 731.astcenc_r's SIMD-native code. Taking the hotspot functions analyzed above as examples, a common pattern uses `vfloat4` comparison plus `select` to implement vectorized max:

```cpp
vfloat4 vmax(vfloat4 a, vfloat4 b) {
  vmask4 mask = b > a;
  return select(a, b, mask);
}
```

Under `-O3`, GCC 14 compiles this to:

```asm
vmax(vfloat4 a, vfloat4 b):
        # a vector in xmm0 (a[0] and a[1]) and xmm1 (a[2] and a[3]) registers
        # b vector in xmm2 (b[0] and b[1]) and xmm3 (b[2] and b[3]) registers
        # although each element is single-precision, each xmm register only holds two elements
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
        comiss  %xmm2, %xmm4      # compare a3 and b3
        movd    %esi, %xmm5       # xmm5 = a1
        seta    %al               # al = (b3 > a3)
        comiss  %xmm6, %xmm1      # compare b2 and a2
        jbe     .L14              # if a2 >= b2, jump to .L14
        testb   %al, %al
        jne     .L15              # if b3 > a3, jump to .L15
        # here a2 < b2, a3 >= b3
        maxss   %xmm7, %xmm0      # xmm0 = max(a0, b0)
        maxss   %xmm5, %xmm3      # xmm3 = max(a1, b1)
        unpcklps        %xmm2, %xmm1 # xmm1 = a3 | b2
        unpcklps        %xmm3, %xmm0 # xmm0 = max(a1, b1) | max(a2, b2)
        ret
.L14:                             # handles a2 >= b2
        testb   %al, %al
        jne     .L16              # if b3 > a3, jump to .L16
        #3 here a2 >= b2, a3 >= b3
        movaps  %xmm6, %xmm1      # xmm1 = a2
        # omitted below: case analysis for a2 vs b2, a3 vs b3
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

Strangely, it first extracts input values into general-purpose registers, then separately compares the last two elements a2 vs b2 and a3 vs b3, using branches to handle four possible cases (knowing where the last two max elements come from), yet still uses `maxss` for the first two elements. Why not just use `maxss` for all four elements from the start? With `-O3 -ffast-math`, it inexplicably learns this:

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

But it still uses scalar SSE, while LLVM 22 knows how to vectorize with `maxps`:

```asm
vmax(vfloat4, vfloat4):
        movlhps %xmm3, %xmm2
        movlhps %xmm1, %xmm0
        maxps   %xmm2, %xmm0
        movaps  %xmm0, %xmm1
        unpckhpd        %xmm0, %xmm1
        retq
```

The remaining instructions are only for handling calling convention data placement; within the function, typically a single `maxps` instruction completes the max computation for all 4 elements. This example illustrates why LLVM 22 is so much faster than GCC 14: GCC 14 generates many useless branches for the `select` comparison and fails to vectorize the max operation. Even with `-march=native`, GCC 14 still uses AVX instructions for scalar max operations. See [Godbolt](https://godbolt.org/z/Y8Ps15n39). GCC 14's high MPKI comes from exactly this. I also tested the same code on LoongArch, where vectorization support is similarly poor (see [Godbolt](https://godbolt.org/z/qTsaMnzhe)), so I filed an [issue](https://github.com/loongson-community/discussions/issues/120). Considering only the vectorized fmax kernel, an optimized implementation using `vfcmp.slt.s` + `vbitsel.v` would be roughly 2.9x the performance of LLVM 22's current output. A small trivia point: x86 SSE/AVX max instructions implement `a > b ? a : b` logic, while LoongArch's fmax implements IEEE754 `maxNum`. These differ when NaN is present: the former returns b whenever either a or b is NaN, while the latter returns the non-NaN value when only one operand is NaN.

#### 2. hdr

Main hotspot functions:

- `compute_angular_endpoints_for_quant_levels` from `src/astcenc_weight_align.cpp`: 19.80%, see above;
- `compute_avgs_and_dirs_3_comp_rgb` from `src/astcenc_averages_and_directions.cpp`: 15.37%, see above;
- `compute_quantized_weights_for_decimation` from `src/astcenc_ideal_endpoints_and_weights.cpp`: 12.40%, see above;
- `compute_error_squared_rgb` from `src/astcenc_averages_and_directions.cpp`: 6.91%, see above;
- `compute_ideal_weights_for_decimation` from `src/astcenc_ideal_endpoints_and_weights.cpp`: 5.68%, see above.

Hotspot functions are essentially the same as 1. linear. GCC 14 generates many branches and scalar SSE instructions, while LLVM 22 vectorizes better and avoids unnecessary branches. Comparison:

| Compiler + Flags            | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) | Mispred (M) | MPKI |
|-----------------------------|----------|-----------|----------|-----------|------------|---------------|---------------|-------------|------|
| GCC 14 `-O3`                | 72.1     | 1091.8    | 306.9    | 78.6      | 91.7       | 245.8         | 30.4          | 4928.9      | 4.51 |
| GCC 14 `-O3 -march=native`  | 63.1     | 851.4     | 271.2    | 65.2      | 77.4       | 240.1         | 30.4          | 4890.6      | 5.74 |
| GCC 14 `-O3 -ffast-math`    | 67.1     | 1036.6    | 311.0    | 85.5      | 73.7       | 200.8         | 54.3          | 4077.0      | 3.93 |
| LLVM 22 `-O3`               | 55.9     | 1107.9    | 276.5    | 55.9      | 56.9       | 111.8         | 129.9         | 1943.2      | 1.75 |
| LLVM 22 `-O3 -march=native` | 48.6     | 825.2     | 209.3    | 30.7      | 34.1       | 85.2          | 139.7         | 1411.6      | 1.71 |

#### 3. precision

Hotspot functions are mostly the same as 1. linear and 2. hdr, with the addition of `find_best_partition_candidates` from `src/astcenc_find_best_partitioning.cpp`, where the main bottleneck is `a / sqrt(length)` computation. This time GCC 14 under `-O3` actually vectorizes this step correctly via a scalar `sqrtss`, `shufps` to broadcast the result to all lanes, then `divps` for batch division. However, other hotspot functions still produce slow code as before. Performance counter comparison:

| Compiler + Flags            | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) | Mispred (M) | MPKI |
|-----------------------------|----------|-----------|----------|-----------|------------|---------------|---------------|-------------|------|
| GCC 14 `-O3`                | 53.8     | 711.5     | 176.8    | 62.0      | 61.3       | 177.0         | 9.3           | 5119.2      | 7.19 |
| GCC 14 `-O3 -march=native`  | 49.2     | 570.5     | 161.3    | 57.1      | 54.7       | 176.1         | 9.2           | 5113.1      | 8.96 |
| GCC 14 `-O3 -ffast-math`    | 48.7     | 655.9     | 168.3    | 64.6      | 49.8       | 156.5         | 19.5          | 4227.6      | 6.56 |
| LLVM 22 `-O3`               | 39.3     | 729.9     | 149.2    | 42.8      | 35.9       | 75.3          | 77.2          | 1906.7      | 2.61 |
| LLVM 22 `-O3 -march=native` | 34.1     | 544.9     | 112.5    | 28.0      | 23.2       | 52.0          | 87.1          | 1445.7      | 2.65 |

#### Summary

731.astcenc_r uses SIMD-native programming with `vfloat4`, `vint4`, `vmask4`, etc., written with SIMD instructions in mind. Unfortunately GCC 14 fails to recognize the code's intent and utilize hardware instructions, inexplicably generating branches for the `select` function. LLVM 22 does much better, vectorizing where appropriate. Meanwhile, slightly less mainstream ISAs like LoongArch still lack adequate optimization for these code patterns, in both GCC and LLVM.

### 736.ocio_r

ocio stands for OpenColorIO. Similar to 731.astcenc_r, it processes images, but focuses more on color transformation rather than compression. This benchmark includes four workloads:

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

reftime is 875s. Performance under different compilers and flags:

| Compiler + Flags            | Total Time (s) | 1. lut1d (s) | 2. mntr (s) | 3. aces (s) | 4. heavy (s) | Score | Improvement over GCC 14 `-O3` (%) |
|-----------------------------|----------------|--------------|-------------|-------------|--------------|-------|-----------------------------------|
| GCC 14 `-O3`                | 139.8          | 6.1          | 11.2        | 67.8        | 54.6         | 6.26  | 0                                 |
| GCC 14 `-O3 -march=native`  | 105.0          | 4.2          | 10.2        | 49.6        | 40.1         | 8.33  | 33                                |
| GCC 14 `-O3 -ffast-math`    | 139.4          | 6.4          | 11.4        | 67.8        | 53.9         | 6.28  | 0.3                               |
| LLVM 22 `-O3`               | 128.9          | 6.8          | 11.3        | 61.7        | 49.0         | 6.79  | 8                                 |
| LLVM 22 `-O3 -march=native` | 105.3          | 5.4          | 9.6         | 49.3        | 40.9         | 8.31  | 33                                |

Again, `-O3 -march=native` brings significant improvement. LLVM 22 still has a performance edge over GCC 14 under `-O3`, but they're essentially equal under `-O3 -march=native`. Detailed analysis below.

#### 1. lut1d

Hotspot functions:

- `OpenColorIO_v2_2dev::BitDepthCast<BIT_DEPTH_F32, BIT_DEPTH_UINT16>::apply` from `src/ASWF-OpenColorIO/src/OpenColorIO/CPUProcessor.cpp`: 45.16%, in a loop over float elements in the [0, 1] range, multiplies by 65535 to scale to uint16_t range, adds 0.5, clamps to uint16_t range, then converts float to uint16_t. Compiled to SSE vector instructions;
- `OpenColorIO_v2_2dev::Lut1DRendererHalfCode<BIT_DEPTH_UINT16, BIT_DEPTH_F32>::apply` from `src/ASWF-OpenColorIO/src/OpenColorIO/ops/lut1d/Lut1DOpCPU.cpp`: 33.70%, loops over input uint16_t values doing table lookup (reading float values from a precomputed array indexed by uint16_t), bottleneck is SSE scalar indirect memory access;
- `__memmove_avx_unaligned_erms` from libc: 13.28%, AVX-accelerated memmove;
- `__memset_avx2_unaligned_erms` from libc: 3.55%, AVX-accelerated memset.

For this highly vectorizable code, `-O3 -march=native` improvement is substantial. In `OpenColorIO_v2_2dev::BitDepthCast<BIT_DEPTH_F32, BIT_DEPTH_UINT16>::apply`, it uses AVX2 256-bit vector computation and FMA instructions to fuse the scale and add-0.5 steps, followed by bitwise operations for clamping. This function's time share drops to 27.82% under `-O3 -march=native`, making the still-scalar-SSE `OpenColorIO_v2_2dev::Lut1DRendererHalfCode<BIT_DEPTH_UINT16, BIT_DEPTH_F32>::apply` the primary bottleneck at 42.85%.

In this sub-benchmark, GCC 14 is slightly faster than LLVM 22. Comparison:

| Compiler + Flags            | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) | Mispred (M) |
|-----------------------------|----------|-----------|----------|-----------|------------|---------------|---------------|-------------|
| GCC 14 `-O3`                | 6.1      | 106.2     | 23.3     | 11.7      | 4.2        | 2.6           | 5.0           | 2.6         |
| GCC 14 `-O3 -march=native`  | 4.2      | 63.8      | 22.0     | 11.0      | 3.6        | 2.6           | 2.5           | 2.5         |
| GCC 14 `-O3 -ffast-math`    | 6.4      | 104.8     | 23.2     | 11.7      | 4.2        | 2.5           | 5.0           | 2.6         |
| LLVM 22 `-O3`               | 6.8      | 106.1     | 23.3     | 11.7      | 3.6        | 2.5           | 5.0           | 2.6         |
| LLVM 22 `-O3 -march=native` | 5.4      | 72.5      | 24.8     | 11.0      | 1.4        | 2.5           | 2.5           | 2.5         |

At the assembly level, GCC 14 and LLVM 22 differ in implementation. Both start with multiplication and addition, but differ in the clamping portion for handling 16-to-32-bit width conversion: GCC 14 mainly uses punpcklwd-type instructions, while LLVM 22 prefers pshufd-type instructions (see [Godbolt](https://godbolt.org/z/KP3vznq1j)). Although total instruction counts are close, different instructions require different execution times on hardware, resulting in some IPC difference. Similar situation after enabling `-O3 -march=native`.

#### 2. mntr

Hotspot functions:

- `OpenColorIO_v2_2dev::BitDepthCast<BIT_DEPTH_UINT16, BIT_DEPTH_F32>::apply` from `src/ASWF-OpenColorIO/src/OpenColorIO/CPUProcessor.cpp`: 55.41%, this time converting from uint16_t to float, so the computation becomes converting uint16_t to float then multiplying by `1.0/65535.0` (no clamping needed). The compiler vectorizes correctly, though the 16-to-32-bit width conversion takes considerable effort;
- `OpenColorIO_v2_2dev::ScaleRenderer::apply` from `src/ASWF-OpenColorIO/src/OpenColorIO/ops/matrix/MatrixOpCPU.cpp`: 41.52%, simple per-pixel scaling of four components (from `out[0] = in[0] * m_scale[0]` to `out[3] = in[3] * m_scale[3]`). All pixels share the same `m_scale` array, which should be easy to vectorize, but it isn't because the pointers lack `restrict` annotations. The compiler cannot determine whether `out` and `m_scale` might alias; only if they don't overlap can it directly vectorize with mulps (see [Godbolt](https://godbolt.org/z/E6nqrK48a)).

Since AMD64 lacks vector instructions for mixed-width computation, much overhead goes to shuffling data between vectors rather than actual computation and memory access. RISC-V Vector's design does produce more concise instruction sequences here (see [Godbolt](https://godbolt.org/z/qvzMK47rf)). Comparison:

| Compiler + Flags            | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) | Mispred (M) |
|-----------------------------|----------|-----------|----------|-----------|------------|---------------|---------------|-------------|
| GCC 14 `-O3`                | 11.2     | 209.9     | 56.5     | 33.3      | 7.5        | 26.8          | 6.6           | 1.9         |
| GCC 14 `-O3 -march=native`  | 10.2     | 159.6     | 54.8     | 29.9      | 7.1        | 26.8          | 3.3           | 1.8         |
| GCC 14 `-O3 -ffast-math`    | 11.4     | 209.7     | 56.5     | 33.3      | 7.5        | 26.7          | 6.6           | 1.8         |
| LLVM 22 `-O3`               | 11.3     | 194.5     | 56.5     | 33.3      | 8.6        | 26.5          | 6.7           | 1.9         |
| LLVM 22 `-O3 -march=native` | 9.6      | 149.4     | 58.2     | 29.9      | 2.8        | 26.5          | 3.4           | 2.0         |

#### 3. aces

Hotspot functions:

- `OpenColorIO_v2_2dev::Lut3DTetrahedralRenderer::apply` from `src/ASWF-OpenColorIO/src/OpenColorIO/ops/lut3d/Lut3DOpCPU.cpp`: 50.74%, complex operations per element: multiply, clamp, floor and ceil converted to int, then index-based table lookup with indirect memory access, followed by weighted averaging. Low vectorization;
- `OpenColorIO_v2_2dev::MatrixRenderer::apply` from `src/ASWF-OpenColorIO/src/OpenColorIO/ops/matrix/MatrixOpCPU.cpp`: 11.55%, matrix operations multiplying input 4D vectors by a 4x4 matrix. High vectorization;
- `__log2f_fma` from libm: 10.02%, computing float log2;
- `OpenColorIO_v2_2dev::CameraLin2LogRenderer::apply` from `src/ASWF-OpenCOlorIO/src/OpenColorIO/ops/log/LogOpCPU.cpp`: 9.76%, checks input range; if below threshold `m_linb`, uses linear multiply-add; otherwise calls log2 combined with multiply-add and max operations. Low vectorization.

Comparison:

| Compiler + Flags            | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) | Mispred (M) |
|-----------------------------|----------|-----------|----------|-----------|------------|---------------|---------------|-------------|
| GCC 14 `-O3`                | 67.8     | 1258.9    | 299.3    | 86.3      | 100.5      | 260.6         | 28.0          | 146.6       |
| GCC 14 `-O3 -march=native`  | 49.6     | 873.7     | 289.0    | 84.9      | 84.0       | 257.4         | 14.0          | 135.4       |
| GCC 14 `-O3 -ffast-math`    | 67.8     | 1251.5    | 296.4    | 94.4      | 109.9      | 213.7         | 43.8          | 150.6       |
| LLVM 22 `-O3`               | 61.7     | 1152.4    | 416.6    | 136.7     | 133.7      | 329.0         | 15.4          | 168.5       |
| LLVM 22 `-O3 -march=native` | 49.3     | 857.8     | 342.8    | 92.6      | 84.4       | 329.0         | 13.0          | 151.6       |

The performance gap between GCC 14 and LLVM 22 under `-O3` mainly comes from floor/ceil handling: GCC 14 generates a complex series of SSE instructions (lacking SSE4.1's roundps), while LLVM 22 calls libm's `__floorf_sse41`, whose function body is essentially a single SSE4.1 roundps instruction plus return. Although there's function call overhead (call/ret plus register save/restore with extra Loads and Stores), it's still a net win. However, on processors truly without SSE4.1, GCC 14's approach would be faster. This trade-off cannot be resolved without `-march=native`; one can only guess which case is more probable. Today, AMD64 processors with SSE4.1 far outnumber those without.

After enabling `-O3 -march=native`, the `vroundps` instruction replaces the previous ceil/floor implementations (GCC 14's vectorized approach or LLVM 22's libm calls), giving both compilers significant improvement and bringing them to the same level. FMA also successfully fuses many multiply-add computations.

#### 4. heavy

Hotspot functions:

- `__powf_fma` from libm: 26.17%;
- `OpenColorIO_v2_2dev::Lut3DRenderer::apply` from `src/ASWF-OpenColorIO/src/OpenColorIO/ops/lut3d/Lut3DOpCPU.cpp`: 25.69%, similar pattern to `Lut3DTetrahedralRenderer::apply` above with clamp/floor/ceil and table lookup, just with different final computation, all scalar SSE;
- `OpenColorIO_v2_2dev::Lut1DRenderer<BIT_DEPTH_F32, BIT_DEPTH_F32>::apply` from `src/ASWF-OpenColorIO/src/OpenColorIO/ops/lut1d/Lut1DOpCPU.cpp`: 15.63%, similar to `Lut3DRenderer::apply` but simpler 1D table lookup, still all scalar;
- `OpenColorIO_v2_2dev::CDLRendererFwd<true>::apply`: 10.88%, calls pow (causing `__powf_fma`'s high share), plus floating-point multiply, add/sub, and clamp. All scalar;
- `OpenColorIO_v2_2dev::GammaMoncurveOpCPUFwd::apply`: 5.41%, also calls pow, with additional floating-point operations and comparisons.

Comparison:

| Compiler + Flags            | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) | Mispred (M) |
|-----------------------------|----------|-----------|----------|-----------|------------|---------------|---------------|-------------|
| GCC 14 `-O3`                | 54.6     | 1013.5    | 209.4    | 57.0      | 80.8       | 253.7         | 5.8           | 32.0        |
| GCC 14 `-O3 -march=native`  | 40.9     | 764.7     | 204.0    | 54.8      | 70.8       | 260.2         | 3.3           | 31.8        |
| GCC 14 `-O3 -ffast-math`    | 53.9     | 971.0     | 202.1    | 50.5      | 80.6       | 252.3         | 6.6           | 29.1        |
| LLVM 22 `-O3`               | 49.0     | 861.5     | 250.4    | 77.3      | 102.7      | 215.6         | 29.9          | 28.8        |
| LLVM 22 `-O3 -march=native` | 40.9     | 726.8     | 206.9    | 55.4      | 67.3       | 255.6         | 25.7          | 28.5        |

The performance difference between LLVM 22 and GCC 14 is the same as in 3. aces: ceil/floor handling. Additionally, like 731.astcenc_r, for vectorized min/max operations, LLVM 22 correctly vectorizes to maxps/minps while GCC 14 produces verbose code.

#### Summary

736.ocio_r is another application well-suited for vectorization. Although it doesn't use `vfloat4` directly like 731.astcenc_r, it's image processing where each loop iteration handles one pixel with four channels. In many cases these four channels undergo identical computation, making it very amenable to vectorization. LLVM 22 under `-O3` generates better code than GCC 14, from floor/ceil mapping to libm functions to better vectorization. However, with `-O3 -march=native`, the performance gap between GCC 14 and LLVM 22 becomes negligible, indicating that with sufficient ISA extensions enabled, both converge to similar implementations. This also suggests GCC 14's SSE code generation has deficiencies: perhaps it's not that GCC 14 cannot vectorize (since it does so with `-O3 -march=native`), but rather it doesn't know how to express vectorized code with SSE after attempting vectorization, so it falls back to scalar.

### 737.gmsh_r

737.gmsh_r is a 3D CAD meshing software with seven workloads:

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

Workload runtimes are 17.1s, 11.8s, 11.2s, 16.9s, 9.2s, 13.4s, and 12.8s, totaling 92.2s, reftime 459s, corresponding to 4.98 points. Both `-O3 -ffast-math` and `-O3 -march=native` yield minimal benefit; LLVM 22 is actually slower than GCC 14, so detailed comparison is omitted.

When compiling with `-O3 -march=native`, if CC is set to just `gcc` without passing `-std=c18`, the 4. gasdis workload enters an infinite loop, continuously reporting: `Info    : Symbolic perturbation failed (2 superposed vertices ?)`. The difference is whether FMA contraction occurs: with `-O3 -std=c18 -march=native`, contraction doesn't happen; with `-O3 -march=native` or `-O3 -std=gnu18 -march=native`, it does (see [Godbolt](https://godbolt.org/z/58fTP5fnG)). In other programs FMA contraction improves performance, but here it unfortunately causes an infinite loop. This relates to [`-fp-contract`](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html):

```
-ffp-contract=style

    -ffp-contract=off disables floating-point expression contraction. -ffp-contract=fast enables floating-point expression contraction such as forming of fused multiply-add operations if the target has native support for them. -ffp-contract=on enables floating-point expression contraction if allowed by the language standard. This is implemented for C and C++, where it enables contraction within one expression, but not across different statements.

    The default is -ffp-contract=off for C in a standards compliant mode (-std=c11 or similar), -ffp-contract=fast otherwise.
```

This only affects C code, not C++, so in practice only 737.gmsh_r is affected. Although 709.cactus_r also has C code, its main computation is in C++.

Per-workload hotspot analysis follows.

#### 1. choi

Hotspot functions:

- `netgen::ADTree6::GetIntersecting` from `src/gmsh/contrib/Netgen/libsrc/gprim/adtree.cpp`: 18.40%, implements a 6-dimensional KD-Tree search algorithm. Main bottleneck is the data-dependent branch `if (node->pi != -1)` with high misprediction rate;
- `__ieee754_atan2_fma` from libm: 6.64%;
- `reparamMeshVertexOnFace` from `src/gmsh/src/geo/MVertex.cpp`: 6.03%, enters different `if-else` branches based on vertex dimension, with significant mispredictions.

Although floating-point is used, the computation pattern doesn't lend itself to vectorization. KD-Tree search naturally has high MPKI. Executed 204.7B instructions with 744.3M mispredictions, MPKI = `744.3M/204.7B*1000=3.64`, second highest in SPEC FP 2026 Rate. The highest, 731.astcenc_r, is essentially due to GCC's poor implementation as discussed above; it could be optimized to around LLVM 22's 1.3, which would make 737.gmsh_r first.

#### 2. mediterranean

Hotspot functions:

- `meshGEdgeProcessing` from `src/gmsh/src/mesh/meshGEdge.cpp`: 36.55%, main bottleneck is Gauss-Seidel iteration in a loop, where scalar division and comparisons take considerable time;
- `KDTreeSingleIndexAdaptor::searchLevel` from `src/gmsh/src/numeric/nanoflann.hpp`: 33.50%, another classic KD-Tree search, recursing into left or right subtrees based on input value;
- `InterpolateCurve` from `src/gmsh/src/geo/GeoInterpolation.cpp`: 6.53%, recursive interpolation computation.

Although floating-point is involved, the computation pattern is not vectorization-friendly because intermediate results feed into if-branches, with additional floating-point computation inside the branches.

#### 3. projection

Hotspot functions:

- `laplaceSmoothing` from `src/gmsh/src/mesh/meshGFaceOptimize.cpp`: 11.73%, main bottleneck is `std::set` operations (which is backed by `std::map`), hence the `std::map` functions below;
- `std::map::_M_get_insert_unique_pos` from libstdc++: 7.49%, `std::map` insertion algorithm;
- `__ieee754_atan2_fma` from libm: 7.21%;
- `reparamMeshVertexOnFace`: 6.66%, see above;
- `std::map::_M_get_insert_unique` from libstdc++: 6.09%, `std::map` insertion;
- `SetRotationMatrix` from `src/gmsh/src/geo/Geo.cpp`: 5.01%, multi-layer loops suitable for vectorization, and the compiler does vectorize, though time share is low.

The main bottleneck in this workload is `std::map` operations.

#### 4. gasdis

Hotspot functions:

- `MakeHybridHexTetMeshConformalThroughTriHedron` from `src/gmsh/src/mesh/meshCombine3D.cpp`: 30.18%, main bottleneck is `std::map` searches in a loop;
- `parallelDelaunay3D` from `src/gmsh/contrib/hxt/tetMesh/src/hxt_tetDelaunay.c`: 9.05%, Delaunay triangulation algorithm;
- `hxtRefineTetrahedra` from `src/gmsh/contrib/hxt/tetMesh/src/hxt_tetRefine.c`: 5.18%, loop with floating-point computation including add/sub, mul/div, and sqrt.

Bottleneck is mainly `std::map`.

#### 5. Torus, 6. spec, and 7. p19

The last three workloads have the same hotspot functions as 4. gasdis.

#### Summary

Per-workload data:

| Workload         | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) | Mispred (M) | MPKI |
|------------------|----------|-----------|----------|-----------|------------|---------------|---------------|-------------|------|
| 1. choi          | 17.0     | 204.7     | 59.3     | 25.6      | 39.4       | 22.1          | 0.3           | 744.3       | 3.64 |
| 2. mediterranean | 11.7     | 190.7     | 57.4     | 23.2      | 24.0       | 28.5          | 2.4           | 71.0        | 0.37 |
| 3. projection    | 11.1     | 109.0     | 29.1     | 14.4      | 20.3       | 13.3          | 2.2           | 183.0       | 1.68 |
| 4. gasdis        | 16.9     | 157.8     | 46.3     | 17.8      | 27.6       | 19.6          | 0.2           | 689.9       | 4.37 |
| 5. Torus         | 9.2      | 77.3      | 21.9     | 8.2       | 13.4       | 9.4           | 0.5           | 380.4       | 4.92 |
| 6. spec          | 13.3     | 101.4     | 30.2     | 10.8      | 18.1       | 10.9          | 0.2           | 546.1       | 5.39 |
| 7. p10           | 12.7     | 96.3      | 28.8     | 10.2      | 17.2       | 10.4          | 0.1           | 529.3       | 5.50 |

Overall MPKI is high, largely attributable to KD-Tree queries and `std::map` queries/insertions, although the tree keys are single-precision floats. Based on the analysis, the code indeed isn't suitable for vectorization, and FMA contraction is disabled since it would cause non-convergence.

### 748.flightdm_r

flightdm is a flight dynamics simulator with eight workloads:

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

Workload runtimes are 5.9s, 14.7s, 10.9s, 11.3s, 24.8s, 8.0s, 9.8s, and 8.4s, totaling 93.9s, reftime 716s, corresponding to 7.63 points. `-O3 -march=native` only gives 2% improvement; `-O3 -ljemalloc` provides 4%; `-O3 -flto` gives 11%. LLVM 22 is slower than GCC 14.

#### 1. weather

Hotspot functions:

- `__sincos_fma` from libm: 6.75%;
- `__ieee754_atan2_fma` from libm: 6.41%;
- `__strncmp_avx2` from libc: 5.04%;
- `parse_path` from `src/JSB-FlightSim/src/simgear/props/props.cxx`: 4.43%, path string parsing, splitting into components;
- `__ieee754_pow_fma` from libm: 4.05%.

The hotspots are quite unusual: mostly libm/libc functions, and flightdm's own most time-consuming function is a path parser. Various optimization flags having no effect is unsurprising.

#### 2. B747

Hotspot functions:

- `SGPropertyNode::getDoubleValue` from `src/JSB-FlightSim/src/simgear/props/props.cxx`: 5.65%, appears to be parsing configuration files and extracting floating-point values;
- `__ieee754_atan2_fma` from libm: 5.42%;
- `__sincos_fma` from libm: 5.25%.

Nothing interesting to analyze.

#### 3. x153 and 4. c3104

Same hotspot functions as 2. B747.

#### 5. ah1s

Hotspot functions:

- `SGPropertyNode::getDoubleValue` from `src/JSB-FlightSim/src/simgear/props/props.cxx`: 8.45%, see above;
- `JSBSim::aFunc::getValue` from `src/JSB-FlightSim/src/math/FGFunction.cpp`: 7.20%, a memoized `std::function`-like container;
- `__sincos_fma` from libm: 6.04%;
- `__ieee754_atan2_fma` from libm: 5.35%;
- `JSBSim::FGPropertyValue::getValue` from `src/JSB-FlightSim/src/math/FGPropertyValue.cpp`: 5.11%, calls `getDoubleValue` above.

The overall impression: either calling libm for transcendental functions or extracting configuration file contents.

#### 6. orbit_torque

Hotspot functions:

- `__ieee754_atan2_fma` from libm: 7.52%;
- `__sincos_fma` from libm: 6.82%;
- `__strncmp_avx2` from libc: 6.57%;
- `parse_path` from `src/JSB-FlightSim/src/simgear/props/props.cxx`: 6.12%, path string parsing, splitting into components;
- `SGPropertyNode::getChild` from `src/JSB-FlightSim/src/simgear/props/props.cxx`: 4.05%, traverses child nodes via string comparison to find matching children.

#### 7. orbit_torque2 and 8. orbit

Same hotspot functions as 6. orbit_torque.

#### Summary

748.flightdm_r is an uninteresting benchmark. Much time is spent in libm and libc functions, while its own code just traverses configuration files. I'd call it a libm benchmark. Beyond that, it behaves more like a SPEC INT 2026 Rate workload: string operations, memory allocation, many small functions and lambdas, suitable for `-O3 -flto` optimization. Per-workload data under `-O3`:

| Workload         | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) | Mispred (M) | MPKI |
|------------------|----------|-----------|----------|-----------|------------|---------------|---------------|-------------|------|
| 1. weather       | 5.9      | 106.1     | 30.8     | 15.4      | 19.5       | 12.9          | 0.6           | 11.6        | 0.11 |
| 2. B747          | 14.8     | 260.1     | 80.0     | 38.7      | 49.4       | 28.4          | 1.7           | 25.6        | 0.10 |
| 3. x153          | 10.8     | 193.3     | 59.1     | 28.7      | 37.3       | 20.0          | 1.0           | 20.9        | 0.11 |
| 4. c3104         | 11.4     | 194.6     | 58.9     | 29.1      | 35.7       | 23.9          | 1.3           | 18.2        | 0.09 |
| 5. ah1s          | 24.7     | 407.3     | 130.0    | 61.3      | 77.9       | 46.4          | 1.6           | 49.3        | 0.12 |
| 6. orbit_torque  | 7.9      | 152.8     | 41.9     | 22.7      | 28.3       | 16.3          | 1.1           | 24.2        | 0.16 |
| 7. orbit_torque2 | 9.9      | 191.4     | 52.5     | 28.4      | 35.3       | 21.0          | 1.2           | 17.1        | 0.09 |
| 8. orbit         | 8.4      | 161.6     | 44.3     | 23.9      | 30.0       | 17.2          | 1.0           | 16.3        | 0.10 |

Unremarkable.

### 749.fotonik3d_r

Finally, a familiar face from SPEC FP 2017 Rate (previously 549.fotonik3d_r). fotonik3d solves Maxwell's equations in 3D space. Another physics-based benchmark; 3D PDE solvers invariably involve Stencil, and let's see if this holds. Single workload:

```shell
fotonik3d_r
```

reftime is 1156s. Performance under different flags:

| Compiler + Flags                       | Time (s) | Score | Improvement over GCC 14 `-O3` (%) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) |
|----------------------------------------|----------|-------|-----------------------------------|-----------|----------|-----------|------------|---------------|---------------|
| GCC 14 `-O3`                           | 131.1    | 8.82  | 0                                 | 1408.5    | 375.1    | 120.7     | 30.9       | 5.4           | 527.2         |
| GCC 14 `-O3 -march=native`             | 114.9    | 10.1  | 14                                | 670.1     | 274.1    | 82.4      | 27.1       | 5.5           | 249.4         |
| GCC 14 `-O3 -ffast-math`               | 116.7    | 9.91  | 12                                | 1117.6    | 378.4    | 120.8     | 30.7       | 4.8           | 396.2         |
| GCC 14 `-O3 -ffast-math -march=native` | 108.5    | 10.65 | 21                                | 599.5     | 276.3    | 82.3      | 26.9       | 4.8           | 204.8         |

LLVM 22 performs similarly to GCC 14 and is omitted. Both `-O3 -march=native` and `-O3 -ffast-math` provide solid improvements. Hotspot analysis:

- `power_dft` from `src/power.F90`: 30.92%, performs DFT (Discrete Fourier Transform), bottleneck is double-precision floating-point multiply-add in loops, compiled to SSE vector instructions by GCC 14;
- `UPML_updateE_simple` from `src/UPML.F90`: 24.73%, 3D Stencil computation, SSE vector instructions;
- `UPML_updateH` from `src/UPML.F90`: 23.26%, 3D Stencil computation, SSE vector instructions;
- `mat_updateE` from `src/material.F90`: 11.04%, Stencil computation, SSE vector instructions;
- `updateH` from `src/update.F90`: 9.78%, Stencil computation, SSE vector instructions.

Besides `power_dft`, most time is spent on Stencil computation. This time the Stencil pattern is purer since GCC can vectorize well with SSE. Based on earlier experience, such programs benefit greatly from `-O3 -march=native`, `-O3 -ffast-math`, and their combination.

With `-march=native`, wider AVX2 vectors bring higher parallelism, plus FMA instructions like [`vfmaddsub231pd`](https://www.felixcloutier.com/x86/vfmaddsub132pd:vfmaddsub213pd:vfmaddsub231pd).

With `-O3 -ffast-math`, the core computation in `power_dft` is essentially complex multiplied by real, then added to complex, as shown in this Fortran code:

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

Under `-O3`, GCC 14 faithfully implements complex multiplication. However, Efield1 and Efield2 are real numbers, so the converted complex has zero imaginary part. With `-O3 -ffast-math`, this simplifies to directly multiplying the real part into expfuncE's real and imaginary components. With `-O3 -ffast-math -march=native`, both optimizations combine: the AVX2 FMA instruction `vfmadd213pd` replaces the `vfmaddsub231pd` needed under `-O3 -march=native` (which simultaneously adds and subtracts; the subtraction comes from the complex multiplication definition, but subtracts zero here since Efield1/Efield2's imaginary part is zero). See [Godbolt](https://godbolt.org/z/v3W4e5xjP).

In summary, 749.fotonik3d_r is a classic floating-point application with heavy Stencil and vector floating-point operations, high parallelism, amenable to vectorization, and benefits from `-ffast-math` computation order optimization.

### 765.roms_r

Another returnee from SPEC FP 2017 Rate (previously 554.roms_r), implementing ocean simulation. Unsurprisingly, it's Stencil again. Single workload:

```shell
roms_r < roms_benchmark2.in.x
```

reftime is 1575s. Performance:

| Compiler + Flags            | Time (s) | Score | Improvement over GCC 14 `-O3` (%) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) |
|-----------------------------|----------|-------|-----------------------------------|-----------|----------|-----------|------------|---------------|---------------|
| GCC 14 `-O3`                | 169.8    | 9.28  | 0                                 | 2620.6    | 874.8    | 204.7     | 192.1      | 193.3         | 709.2         |
| GCC 14 `-O3 -march=native`  | 149.5    | 10.5  | 14                                | 1317.9    | 555.3    | 125.0     | 126.6      | 164.9         | 365.9         |
| GCC 14 `-O3 -ffast-math`    | 162.8    | 9.67  | 4                                 | 2518.6    | 854.5    | 204.0     | 178.5      | 134.0         | 711.7         |
| LLVM 22 `-O3`               | 165.6    | 9.51  | 3                                 | 2434.3    | 834.9    | 190.3     | 164.1      | 231.8         | 687.0         |
| LLVM 22 `-O3 -march=native` | 152.1    | 10.4  | 12                                | 1423.4    | 551.4    | 131.2     | 140.1      | 259.8         | 350.0         |

Heavy floating-point computation with high vectorizability; `-O3 -march=native` improvement is expected.

Hotspot functions:

- `step2d_tile` from `src/step2d_LF_AM3.h`: 20.37%, 2D Stencil computation, high vectorization;
- `pre_step3d` from `src/pre_step3d.F90`: 10.43%, floating-point computation in loops, high vectorization;
- `lmd_skpp` from `src/lmd_skpp.F90`: 8.91%, complex floating-point computation in loops, mainly scalar;
- `step3d_t_tile` from `src/step3d_t.F90`: 7.04%, 3D Stencil computation, high vectorization;
- `rhs3d` from `src/rhs3d.F90`: 6.04%, 2D Stencil computation, high vectorization;
- `t3dmix2` from `src/t3dmix2_geo.h`: 5.86%, 3D Stencil computation, high vectorization;
- `step3d_uv_tile` from `src/step3d_uv.F90`: 5.85%, 3D Stencil computation, high vectorization;
- `_ZGVbN2v_exp_sse4` from libmvec: 4.66%, vectorized exp.

Typical Stencil computation with high vectorization. With `-O3 -march=native`, wider vectors plus FMA naturally bring solid improvements.

### 766.femflow_r

femflow is a fluid dynamics solver for Navier-Stokes equations. Single workload:

```shell
femflow_r refrate.prm
```

reftime is 1467s. Performance:

| Compiler + Flags            | Time (s) | Score | Improvement over GCC 14 `-O3` (%) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) |
|-----------------------------|----------|-------|-----------------------------------|-----------|----------|-----------|------------|---------------|---------------|
| GCC 14 `-O3`                | 188.7    | 7.77  | 0                                 | 3862.4    | 1358.5   | 797.6     | 117.5      | 562.2         | 676.0         |
| GCC 14 `-O3 -march=native`  | 95.1     | 15.4  | 98                                | 1736.9    | 619.3    | 356.0     | 65.2       | 286.8         | 445.4         |
| GCC 16 `-O3`                | 153.6    | 9.55  | 23                                | 3178.6    | 1109.3   | 673.3     | 127.2      | 56.3          | 930.9         |
| GCC 16 `-O3 -march=native`  | 83.5     | 17.57 | 126                               | 1457.0    | 501.1    | 281.4     | 61.1       | 47.2          | 545.7         |
| LLVM 22 `-O3`               | 124.7    | 11.8  | 51                                | 2703.0    | 857.3    | 475.5     | 60.6       | 40.8          | 930.3         |
| LLVM 22 `-O3 -march=native` | 88.7     | 16.5  | 113                               | 1392.9    | 495.7    | 269.4     | 42.9       | 41.8          | 471.1         |

LLVM 22 provides significant improvement over GCC 14, and `-O3 -march=native` brings even more dramatic gains. This is the second-highest `-O3 -march=native` improvement in SPEC FP 2026 Rate (first is 772.marian_r below). GCC 16 also improves notably over GCC 14, overtaking LLVM 22 with `-O3 -march=native`.

There are many hotspot functions, mostly single-digit percentage each, mainly computational operators:

- `Laplace::LaplaceOperator::local_apply_quadratic_geo` from `src/laplace_operator.h`: 5.49%, heavy floating-point vector computation with high parallelism;
- `operator *(const dealii::VectorizedArray &, const dealii::VectorizedArray &)` from `src/dealii/include/deal.ll/base/vectorization.h`: 5.36%, element-wise vector multiplication.

Other functions include dealii::Tensor computations, including `dealii::internal::even_odd_apply` from `src/dealii/include/deal.ll/matrix_free/tensor_product_kernels.h`, implementing Tensor double-precision floating-point multiplication. The "even-odd" refers to exploiting data symmetry by splitting into even and odd parts, reducing computation count while being vectorization-friendly. For such workloads, `-O3 -march=native` provides better floating-point performance through wider vectors plus FMA.

LLVM 22's advantage over GCC 14 comes from vectorizing more code: comparing instruction counts, LLVM 22 executes fewer FP scalar instructions and more FP vector instructions. GCC 16 shows a similar pattern, approaching LLVM 22's vectorization level.

### 767.nest_r

nest is a spiking neural network simulator. This benchmark has three workloads:

```shell
# 1. cuba
nest_r cuba_stdp.sli
# 2. structural
nest_r structural_plasticity_benchmark
# 3. Artificial
nest_r ArtificialSynchrony
```

`-O3 -march=native` gives only 3% improvement; LLVM 22 is slower than GCC 14. Per-workload data under GCC 14 `-O3`:

| Workload      | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) |
|---------------|----------|-----------|----------|-----------|------------|---------------|---------------|
| 1. cuba       | 14.1     | 176.3     | 54.5     | 21.6      | 22.4       | 29.2          | 0.0           |
| 2. structural | 24.6     | 413.3     | 136.3    | 42.8      | 52.5       | 93.2          | 0.0           |
| 3. Artificial | 48.6     | 1125.4    | 392.6    | 150.5     | 160.5      | 163.6         | 0.0           |

Total time 87.4s, reftime 793s, corresponding to 9.07 points.

#### 1. cuba

Hotspot functions:

- `nest::iaf_psc_exp::handle` from `src/nest-simulator/models/iaf_psc_exp.cpp`: 25.75%, processes incoming spikes and updates internal state. Main bottleneck is indirect memory access, writing spike weights to corresponding input buffers;
- `__ieee754_pow_fma` from libm: 11.96%, called by `nest::Connector::send` below;
- `spec::poisson_distribution::operator()` from `src/specrand-distributions/spec_random_distributions.cpp`: 9.87%, random number generation for input spike generation;
- `nest::Connector::send` from `src/nest-simulator/nestkernel/connector_base.h`: 8.29%, spike propagation through synapses with STDP. Main bottleneck is indirect memory access, plus inlined weight computation with pow and exp calls;
- `nest::iaf_psc_exp::update` from `src/nest-simulator/models/iaf_psc_exp.cpp`: 6.91%, neuron state update at each timestep, mainly scalar floating-point.

A classic SNN simulation with STDP. Main bottlenecks are spike propagation and STDP synaptic weight updates, with very low vectorization and indirect memory access.

#### 2. structural

Hotspot functions:

- `spec::poisson_distribution::operator()` from `src/specrand-distributions/spec_random_distributions.cpp`: 24.26%, see above;
- `nest::iaf_psc_alpha::update` from `src/nest-simulator/models/iaf_psc_alpha.cpp`: 13.71%, similar to `nest::iaf_psc_exp::update` but different neuron model;
- `__ieee754_pow_fma` from libm: 13.37%, see above;
- `nest::GrowthCurveGaussian::update` from `src/nest-simulator/nestkernel/growth_curve.cpp`: 6.60%, numerical ODE solving with frequent exp and pow calls;
- `nest::iaf_psc_alpha::handle` from `src/nest-simulator/models/iaf_psc_alpha.cpp`: 25.75%, similar to `nest::iaf_psc_exp::handle`;
- `nest::Connector::send` from `src/nest-simulator/nestkernel/connector_base.h`: 6.60%, see above, but without STDP this time (static weights);
- `exp` from `libm`: 5.39%.

Compared to 1. cuba, different neuron model without STDP. The main bottleneck shifts to Poisson distribution random generation; the rest is typical SNN simulation.

#### 3. Artificial

Hotspot functions:

- `nest::iaf_psc_alpha_ps::update` from `src/nest-simulator/models/iaf_psc_alpha_ps.cpp`: 13.26%, neuron state update;
- `nest::iaf_psc_alpha::update` from `src/iaf_psc_alpha.cpp`: 12.37%, see above;
- `nest::Connector::send` from `src/nest-simulator/nestkernel/connector_base.h`: 7.19%, see above, still no STDP (static weights);
- `nest::SimulationManager::update_` from `src/nest-simulator/nestkernel/simulation_manager.cpp`: 5.66%, core SNN simulation loop calling the above functions;
- `__ieee754_pow_fma` from libm: 5.17%, see above.

#### Summary

nest is a flexible SNN simulator, but single-threaded performance is mediocre since most effort goes into multi-core/multi-thread optimization. Unsurprisingly, nest's neuron update code isn't vectorized, while spike propagation and STDP are inherently hard to optimize. This is a floating-point application that's difficult to vectorize; as the counters show, zero vector floating-point instructions are executed.

### 772.marian_r

marian_r is a neural-network-based translator. Another neural network inference workload, meaning `-O3 -march=native` should have a large advantage. If dedicated hardware acceleration instructions are available (like in 706.stockfish_r), performance will far exceed `-O3`. Two workloads:

```shell
# 1. TildeMODEL
marian-decoder --cpu-threads 1 -m model.alphas.npz -v vocab.spm vocab.spm --beam-size 1 --mini-batch 32 --maxi-batch 100 --maxi-batch-sort src -w 512 --skip-cost --gemm-type intgemm8 --intgemm-options precomputed-alpha standard-only --quiet --quiet-translation -i TildeMODEL-spec.en --log TildeMODEL-spec.log --log-level off -o TildeMODEL-spec.out
# 2. EuroPat
marian-decoder --cpu-threads 1 -m model.alphas.npz -v vocab.spm vocab.spm --beam-size 1 --mini-batch 32 --maxi-batch 100 --maxi-batch-sort src -w 512 --skip-cost --gemm-type intgemm8 --intgemm-options precomputed-alpha standard-only --quiet --quiet-translation -i EuroPat-spec.en --log EuroPat-spec.log --log-level off -o EuroPat-spec.out
```

reftime is 1579s. Compiler and flag comparison:

| Compiler + Flags           | Time (s) | Score | Improvement over GCC 14 `-O3` (%) | 1. TildeMODEL (s) | 2. EuroPat (s) |
|----------------------------|----------|-------|-----------------------------------|-------------------|----------------|
| GCC 14 `-O3`               | 235.2    | 6.71  | 0                                 | 88.8              | 146.4          |
| GCC 14 `-O3 -march=native` | 78.4     | 20.14 | 200                               | 28.2              | 50.3           |
| GCC 15 `-O3`               | 150.1    | 10.52 | 57                                | 56.0              | 94.8           |
| GCC 15 `-O3 -march=native` | 77.5     | 20.37 | 203                               | 27.8              | 49.7           |

`-O3 -march=native` provides a massive 200% improvement. On Apple M1 it's 47%, on Apple M2 it reaches 92%. This level of improvement was previously only seen in 706.stockfish_r. GCC 15 also significantly improves over GCC 14 under `-O3`.

#### 1. TildeMODEL

Hotspot functions:

- `marian::cpu::integer::affineOrDotTyped` from `src/marian/tensors/cpu/intgemm_interface.h`: 82.28%, mainly in `tiled_gemm`, performing integer matrix multiplication: uint8_t matrix A multiplied by int8_t matrix B, accumulated to int32_t, finally converted to float and added to float matrix C;
- `marian::cpu::ProdBatched` from `src/marian/tensors/cpu/prod.cpp`: 10.30%, core is sgemm (actual floating-point matrix operations), compiled to scalar SSE floating-point rather than vector, but given its time share, this is tolerable.

The main hotspot has the same computation pattern as 706.stockfish_r's NNUE. With `-O3 -march=native`, AVX-VNNI's vpdpbusd instruction optimizes it (see [Godbolt](https://godbolt.org/z/PTxK1evK3)). Similarly, GCC 15 performs better than GCC 14 due to its superior unsigned extension implementation. For detailed discussion, see the 706.stockfish_r section in the [INT Rate article](./spec-cpu-2026-workload-analysis-int-rate-en.md).

Performance counter comparison:

| Compiler + Flags           | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) | 128-bit Int Vec (B) | 256-bit Int Vec (B) |
|----------------------------|----------|-----------|----------|-----------|------------|---------------|---------------|---------------------|---------------------|
| GCC 14 `-O3`               | 88.2     | 2038.9    | 217.8    | 57.8      | 53.2       | 58.7          | 2.1           | 514.6               | 0.0                 |
| GCC 14 `-O3 -march=native` | 27.6     | 423.0     | 131.5    | 25.1      | 47.4       | 59.8          | 1.1           | 12.8                | 47.4                |
| GCC 15 `-O3`               | 55.6     | 1353.5    | 173.9    | 22.1      | 53.2       | 58.7          | 2.1           | 184.7               | 0.0                 |
| GCC 15 `-O3 -march=native` | 27.3     | 415.1     | 128.9    | 23.5      | 47.5       | 59.8          | 1.1           | 12.8                | 47.4                |

128-bit integer vector from `int_vec_retired.128bit` counter, 256-bit from `int_vec_retired.256bit`.

#### 2. EuroPat

Hotspot functions:

- `marian::cpu::integer::affineOrDotTyped`: 78.96%, see above;
- `marian::cpu::ProdBatched`: 14.25%, see above.

Identical hotspots to 1. TildeMODEL; the same analysis applies. Performance counters:

| Compiler + Flags           | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) | 128-bit Int Vec (B) | 256-bit Int Vec (B) |
|----------------------------|----------|-----------|----------|-----------|------------|---------------|---------------|---------------------|---------------------|
| GCC 14 `-O3`               | 145.6    | 3352.7    | 370.4    | 89.7      | 98.8       | 123.8         | 3.6           | 815.0               | 0.0                 |
| GCC 14 `-O3 -march=native` | 49.7     | 777.2     | 228.7    | 36.6      | 88.3       | 123.9         | 1.7           | 19.9                | 72.6                |
| GCC 15 `-O3`               | 94.2     | 2268.5    | 301.7    | 33.1      | 98.8       | 123.8         | 3.6           | 293.6               | 0.0                 |
| GCC 15 `-O3 -march=native` | 49.0     | 765.3     | 225.2    | 34.3      | 88.3       | 123.9         | 1.7           | 19.9                | 72.6                |

#### Summary

772.marian_r is essentially a 706.stockfish_r NNUE clone. The hotspot is int8_t times uint8_t accumulated to int32_t matrix multiplication, with more integer vector instructions than floating-point. It probably should be expelled from SPEC FP 2026 Rate.

### 782.lbm_r

lbm stands for Lattice Boltzmann Method, another fluid dynamics application, still Stencil. Single workload:

```shell
lbm_r 900 reference.dat 0 0 200_200_130_ldc.of
```

reftime is 573s. Performance comparison:

| Compiler + Flags           | Time (s) | Score | Improvement over GCC 14 `-O3` (%) | Insns (B) | Load (B) | Store (B) | Branch (B) | FP Scalar (B) | FP Vector (B) |
|----------------------------|----------|-------|-----------------------------------|-----------|----------|-----------|------------|---------------|---------------|
| GCC 14 `-O3`               | 105.8    | 5.42  | 0                                 | 2232.2    | 473.3    | 242.4     | 14.5       | 1108.2        | 0.0           |
| GCC 14 `-O3 -ffast-math`   | 95.8     | 5.98  | 10                                | 1892.4    | 419.2    | 192.8     | 14.5       | 1009.5        | 0.0           |
| GCC 14 `-O3 -march=native` | 131.0    | 4.37  | -19                               | 1669.6    | 550.3    | 309.8     | 14.5       | 1228.8        | 0.0           |
| GCC 15 `-O3`               | 105.2    | 5.45  | 0.6                               | 2218.9    | 468.9    | 242.4     | 14.5       | 1108.2        | 0.0           |
| GCC 15 `-O3 -march=native` | 111.0    | 5.16  | -5                                | 1777.3    | 509.8    | 282.9     | 14.5       | 1108.2        | 0.0           |
| GCC 16 `-O3`               | 105.4    | 5.44  | 0.4                               | 2218.9    | 468.9    | 242.4     | 14.5       | 1108.2        | 0.0           |
| GCC 16 `-O3 -march=native` | 110.6    | 5.18  | -4                                | 1777.3    | 509.8    | 282.9     | 14.5       | 1108.2        | 0.0           |

The sole hotspot function is `LBM_performStreamCollideTRT` from `src/lbm.c`, accounting for 99.35% of time. Its structure is: read from current-round Grid, heavy floating-point computation, write to next-round Grid, with conditional branches in between. Memory access is strided, making vectorization difficult; all generated instructions are SSE scalar. For such scalar-compute-intensive cases, `-O3 -ffast-math` typically helps by reordering computations and reusing intermediate results.

`-O3 -march=native` actually regresses performance. GCC 14 regresses worst (-19%); GCC 15/16 regress less but still underperform `-O3`. Assembly analysis suggests increased stack memory access instructions offset the FMA instruction count reduction benefit (see [Godbolt](https://godbolt.org/z/5Ynsjn5o8)). Note that FMA instructions are counted twice in the FP scalar column but only once in total instruction count.

## Discussion

### Compiler Flags Comparison

Overall, compiler flags have significant impact on SPEC FP 2026 Rate performance:

- `-march=native` provides solid improvement for many benchmarks. AVX2 not only widens vectors compared to SSE but also adds many useful instructions that reduce instruction count, plus AVX-VNNI specifically benefits 772.marian_r;
- `-ffast-math` also helps notably, especially since SPEC FP 2026 Rate has substantial floating-point computation. Strictly following source code computation order is often slower than optimized ordering. However, `-ffast-math` may produce results not conforming to IEEE 754;
- `-flto` and `-ljemalloc` have minimal effect on most SPEC FP 2026 Rate benchmarks, though they slightly help 748.flightdm_r.

Other common flags like `-static` and `-fomit-frame-pointer` haven't been extensively tested yet.

### Branch Prediction

Only 731.astcenc_r and 737.gmsh_r have notably high MPKI in SPEC FP 2026 Rate; others peak at 767.nest_r's 0.87. 731.astcenc_r's high MPKI is entirely due to GCC 14's poor compilation. Switching to LLVM 22 immediately normalizes it. Hopefully GCC will address this.

## Conclusion

This article provides in-depth analysis of SPEC CPU 2026 FP Rate workloads, for reference by compiler and processor designers. From a compiler perspective, combining the strengths of both GCC and LLVM can further improve performance. From a processor perspective, optimizing for program bottlenecks can further increase scores.
