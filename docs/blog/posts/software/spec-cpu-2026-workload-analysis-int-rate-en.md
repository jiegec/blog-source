---
layout: post
date: 2026-05-22
tags: [benchmark,spec,speccpu2026]
categories:
    - software
---

# SPEC CPU 2026 Workload Analysis (INT Rate)

[中文版本](spec-cpu-2026-workload-analysis-int-rate.md)

## Background

I've been running some benchmarks with SPEC CPU 2026 recently, and plan to do in-depth workload analysis combined with the [test results](../../../benchmark/spec-cpu-2026-rate.md). This article focuses on SPEC INT 2026 Rate workload characteristics. For SPEC FP 2026 Rate analysis, see the [FP Rate article](./spec-cpu-2026-workload-analysis-fp-rate.md).

<!-- more -->

Test environment: CPU is Intel i9-14900K P-Core @ 5.7 GHz, Linux distribution is Debian Trixie, compiler is GCC 14.2.0, default compilation flags are `-O3`. This CPU can actually boost up to 6.0 GHz, but occasionally fails to boost under single-core workloads for unknown reasons (degradation protection?), specifically manifesting as the CPU core being forced down to 4.7 GHz after running for a while. So I opted for the more reliably achievable 5.7 GHz. Only one physical P-core can stably run at 6.0 GHz; other P-cores can all reach 5.7 GHz, and switching to another core when throttling occurs is sufficient. Performance at 6.0 GHz can be referenced from previous test results: [INT](../../../benchmark/data-trixie/int2026_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt) and [FP](../../../benchmark/data-trixie/fp2026_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt), basically, from 5.7 GHz to 6.0 GHz, performance scales linearly with frequency. This article may give multiple different runtimes for the same workload, which could be due to performance variance across multiple runs or because some numbers include `perf record` overhead, but the errors are small enough for reliable comparison. The scripts used in this article are open-sourced at [jiegec/spec2026](https://github.com/jiegec/spec2026).

Recommended reading: [Evaluating SPEC CPU2026](https://chipsandcheese.com/p/evaluating-spec-cpu2026) and [SPEC CPU2026: Characterization, Representativeness, and Cross-Suite Comparison](https://arxiv.org/abs/2605.03713v2)

## SPEC INT 2026 Rate Analysis

### 706.stockfish_r

Stockfish is a well-known chess engine. This benchmark includes three workloads:

```shell
# 1. 1to6_classical
stockfish bench 1600 1 26 spec_ref_pos_1to6.fen depth classical
# 2. 1to6_nnue
stockfish bench 1600 1 26 spec_ref_pos_1to6.fen depth nnue
# 3. 7to11_nnue
stockfish bench 1600 1 26 spec_ref_pos_7to11.fen depth nnue
```

Measured data shows the three workloads take 47s, 77s, and 72s respectively, totaling 196s. The reftime is 1260s, corresponding to 6.4 points. With `-march=native` enabled, 1to6_classical time decreases by 10% to 43s, while 1to6_nnue and 7to11_nnue significantly decrease to 32s and 31s, total time 105s, corresponding to 12 points, a significant score improvement. Below is a per-workload performance analysis.

#### 1. 1to6_classical

Using `perf` to observe performance bottlenecks, the major hotspot functions for 1to6_classical and their time shares are listed below (subsequent benchmarks use the same representation):

- `Stockfish::Eval::evaluate(const Position& pos)` from `src/evaluate.cpp`: 19.16%, inlines the `Evaluation<NO_TRACE>(pos).value()` call, mainly evaluating board positions with scattered memory accesses and computations, no particularly concentrated hotspot instructions;
- `Stockfish::TranspositionTable::probe(const Key key, bool& found)` from `src/tt.cpp`: 17.91%, the main bottleneck is random memory access in `first_entry(key)` which contains `&table[mul_hi64(key, clusterCount)].entry[0]`, where `mul_hi64` computes the upper 64 bits of a 64-bit integer multiplication, so the memory address is computed from the argument; for `mul_hi64`, GCC 14 faithfully splits the 64-bit values into high and low 32-bit halves, while LLVM 22 correctly recognizes the code's intent and uses AMD64's mul instruction directly. This was implemented in [PR #168396](https://github.com/llvm/llvm-project/pull/168396), with `mul_hi64` corresponding to "Ladder" in the PR description; in fact, Stockfish's original code uses __int128 which GCC 14 can also compile efficiently, but unfortunately this C syntax extension was disabled by SPEC (assembly comparison at [Godbolt](https://godbolt.org/z/x3j89xqWP));
- `Stockfish::MovePicker::next_move(bool skipQuiets)` from `src/movepick.cpp`: 10.36%, the slow part is `partial_insertion_sort`: after finding the insertion position, the subsequent array elements must be shifted to make room;
- `Stockfish::search(Position& pos, Stack* ss, Value alpha, Value beta, Depth depth, bool cutNode)` from `src/search.cpp`: 9.49%, the main search logic is implemented here;
- `__popcountdi2` from libgcc: 7.52%, called by `Stockfish::Eval::evaluate(const Position& pos)` to determine board conditions using bit operations. Interested readers can refer to Hacker's Delight.

With `-march=native` enabled, [`__popcountdi2`](https://github.com/gcc-mirror/gcc/blob/32bbd8849a550ad6f936636476c3ab9be8a58807/libgcc/libgcc2.c#L846) is inlined as a `popcnt` instruction. Testing shows that enabling `-mpopcnt` alone reduces time from 47s to 44s, close to `-march=native` performance. Simply enabling the popcnt ISA extension and eliminating the `__popcountdi2` function call overhead brings noticeable performance improvement.

Under `-O3`, 1to6_classical executes 531.8B instructions (`instructions` perf counter), with 135.7B Load instructions (`mem_inst_retired.all_loads` counter), 59.7B Stores (`mem_inst_retired.all_stores` counter), 56.0B branch instructions (`branch-instructions` counter), of which 2622.8M are mispredicted (`branch-misses` counter). The MPKI is quite high: `2622.8M/531.8B*1000=4.93`. Even among SPEC INT 2017 benchmarks, this is higher than 531.deepsjeng_r's 3.16 and 557.xz_r's 3.49, but lower than 505.mcf_r's 6.24 and 541.leela_r's 7.71.

Using `perf record -e branch-misses:pp`, the main branch mispredictions come from `Stockfish::MovePicker::next_move()` contributing 27.48%, mainly from the insertion sort, i.e., finding the insertion position and shifting existing elements. Next is `Stockfish::Eval::evaluate()` at 17.42%, then `Stockfish::search()` at 13.06%.

With `-O3 -mpopcnt`, instruction count drops to 453.9B, with 124.2B Loads, 53.1B Stores, 46.1B branch instructions, and still 2.6B mispredictions. Just inlining the `__popcountdi2` call saves 77.9B instructions, about 15% of the original. `__popcountdi2` itself is 21 instructions, plus one jmp in `__popcountdi2@plt`, plus the `call __popcountdi2@plt` itself and register save/restore overhead.

#### 2. 1to6_nnue

The latter two workloads switch from classical to nnue engine (involving neural networks), so the computation pattern is different. `perf` shows the main time-consuming functions for 1to6_nnue:

- `Stockfish::Eval::NNUE:evaluate(const Position& pos, bool adjusted)` from `src/nnue/evaluate_nnue.cpp`: 80.59%, main time spent in `affine_transform_non_ssse3`'s `sum += weights[offset + j] * input[j]`, i.e., neural network inference. It computes int8_t multiplied by uint8_t, accumulated into int32_t result. Under default flags, only basic SSE instructions like pmaddwd/paddd can be used, not AVX;
- `Stockfish::TranspositionTable::probe(const Key key, bool& found)` from `src/tt.cpp`: only 4.81%, same random memory access bottleneck as before.

Analyzing the `Stockfish::Eval::NNUE:evaluate` instructions: to implement the above logic, the core approach uses the pmaddwd instruction for 4 signed 16-bit multiplications accumulated into 32-bit results. But first, the 8-bit signed weights and unsigned input must be extended to signed 16-bit. Signed 8-bit weights extension is straightforward, while unsigned 8-bit input handling is complex. First, it adds 128 to each input element, then treats it as signed, effectively subtracting 128, mapping uint8_t to int8_t. This allows input to use the same sign extension method as weights. However, this introduces error in the result, so to correct the bias, 128 times the sum of weights is subtracted. Assembly code ([Godbolt](https://godbolt.org/z/ox7q63Er8)):

```asm
1:
# Load 16 signed weights elements
movdqu (%rdx,%rcx,1),%xmm2
movdqa %xmm5,%xmm8
# Load 16 unsigned input elements
movdqa (%r12,%rcx,1),%xmm10
add $0x10,%rcx
# Sign-extend weights
pcmpgtb %xmm2,%xmm8
movdqa %xmm2,%xmm9
# Add 128 to each input element, i.e., subtract 128 to convert to signed int8_t
paddb %xmm6, %xmm10
# Sign-extend weights
punpckhbw %xmm8,%xmm2
punpcklbw %xmm8,%xmm9
movdqa %xmm2,%xmm11
movdqa %xmm9,%xmm8
# Compute weights sum times 128
pmaddwd %xmm3,%xmm11
pmaddwd %xmm7,%xmm8
paddd %xmm11,%xmm0
paddd %xmm8,%xmm0
paddd %xmm11,%xmm0
movdqa %xmm5,%xmm11
# Sign-extend input
pcmpgtb %xmm10,%xmm11
paddd %xmm8,%xmm0
movdqa %xmm10,%xmm8
punpckhbw %xmm11,%xmm10
punpcklbw %xmm11,%xmm8
# Compute weights * input
pmaddwd %xmm10,%xmm2
pmaddwd %xmm8,%xmm9
# Accumulate results
paddd %xmm2,%xmm0
paddd %xmm9,%xmm0
cmp $0x400,%rcx
jne 1b
```

For SIMD-friendly code like this, `-march=native` typically brings significant improvement, as confirmed by testing: time drops from 77s to 32s, `Stockfish::Eval::NNUE::evaluate` share drops to 54.20%, with the main computation instruction becoming the AVX-VNNI extension's [vpdpbusd (Multiply and Add Unsigned and Signed Bytes)](https://www.felixcloutier.com/x86/vpdpbusd), a fused integer multiply-add for byte elements (weights are int8_t, input are uint8_t), with int32_t accumulator. Core loop ([Godbolt](https://godbolt.org/z/zoeqc4zch)):

```asm
1:
# Load unsigned input
vmovdpa (%r8,%rcx,1),%ymm0
# Load signed weights and compute sum += weights[offset + j] * input[j]
{vex} vpdpbusd (%rdx,%rcx,1),%ymm0,%ymm2
add $0x20,%rcx
cmp $0x400,%rcx
jne 1b
```

If the CPU supports AVX512-VNNI, this can be further widened to 512-bit: `vpdpbusd (%rdx,%rax), %zmm1, %zmm0`. Note that simply enabling `-mavx2` only reduces time from 77s to 50s, still far from `-march=native`'s 32s: even with AVX enabled ([Godbolt](https://godbolt.org/z/e9dPsqddh)), without AVX-VNNI the vpdpbusd instruction is unavailable, requiring format conversion to 16-bit followed by 16-bit integer multiply-add with 32-bit accumulator. Stockfish's NNUE computation is designed around the vpdpbusd instruction. CPUs lacking this instruction, or where the compiler doesn't utilize it, will see significantly lower performance.

On ARM64, the corresponding [USDOT (Dot product with unsigned and signed integers (vector))](https://developer.arm.com/documentation/ddi0487/maa/-Part-C-The-AArch64-Instruction-Set/-Chapter-C7-A64-Advanced-SIMD-and-Floating-point-Instruction-Descriptions/-C7-2-Alphabetical-list-of-A64-Advanced-SIMD-and-floating-point-instructions/-C7-2-448-USDOT--vector-) instruction is part of the i8mm extension. With this extension, `-march=native` provides significant improvement ([Godbolt](https://godbolt.org/z/MxY3YYTYo)), e.g., Apple M2; without it, `-march=native` makes no difference, e.g., Apple M1, falling back to extend-to-16-bit-then-sum like AMD64 ([Godbolt](https://godbolt.org/z/TfdvW4f75)). RISC-V Vector extension has the vwmulsu.vv instruction, yielding 16-bit multiplication results, then vwadd.wv to accumulate to 32-bit ([Godbolt](https://godbolt.org/z/ha5oEb4hE)). LoongArch also has corresponding xvmulwev.h.b/xvmulwod.h.b instructions yielding 16-bit results, then xvhaddw.w.h to accumulate to 32-bit ([Godbolt](https://godbolt.org/z/xxr5rovxW)), which can be further optimized using [xvmulwev.h.bu.b](https://github.com/loongson-community/discussions/issues/119), and the optimized transform function is 37% faster than GCC 16.

Beyond ISA extension enablement, GCC 15 shows notable performance improvement over GCC 14 on 1to6_nnue (with `-O3`), from 77s to 49s. Examining the generated instructions: although still using SSE, the instruction sequence is more concise ([Godbolt](https://godbolt.org/z/exKaP5jKb)):

```asm
# %xmm5 initialized to all zeros
1:
# Load 16 signed weights elements
movdqu (%rdx,%rcx,1),%xmm4
movdqa %xmm5,%xmm8
# Load 16 unsigned input elements
movdqa (%r12,%rcx,1),%xmm2
add $0x10,%rcx
# Compare weights with zero: non-negative gives 0, negative gives 0xFF
pcmpgtb %xmm4,%xmm8
movdqa %xmm2,%xmm6
movdqa %xmm4,%xmm7
# Zero-extend input from 8-bit unsigned to 16-bit, saved in %xmm2 and %xmm6
punpckhbw %xmm5,%xmm2
punpcklbw %xmm5,%xmm6
# Combined with pcmpgtb above, sign-extend weights from 8-bit signed to 16-bit, saved in %xmm4 and %xmm7
punpckhbw %xmm8,%xmm4
punpcklbw %xmm8,%xmm7
# Each pmaddwd performs 4 times 16-bit * 16-bit + 16-bit * 16-bit = 32-bit
# Two pmaddwd together complete 8 16-bit multiplications and 8 32-bit additions
pmaddwd %xmm4,%xmm2
pmaddwd %xmm7,%xmm6
# Each paddd performs 4 32-bit accumulations
paddd %xmm2,%xmm0
paddd %xmm6,%xmm0
cmp $0x400,%rcx
jne 1b
```

Even without the dedicated vpdpbusd instruction, SSE-only optimization space remains. GCC 15 efficiently implements signed and unsigned sign extension via SSE, achieving performance between GCC 14's suboptimal instruction sequence and the dedicated vpdpbusd instruction. This is also mentioned in [SPEC CPU2026: Characterization, Representativeness, and Cross-Suite Comparison](https://arxiv.org/abs/2605.03713v2): `For example, gcc-15 reduces the instruction count of 706.stockfish_r by up to 3x`, though that number is relative to GCC 13; the reduction vs. GCC 14 is less dramatic (see Figure 10 and Figure 16 in the paper). Measured here: from GCC 14's 1342B instructions down to GCC 15's 1015B. In comparison, LLVM 22's SSE (`-O3`, [Godbolt](https://godbolt.org/z/Tsd1YhrWe)) or AVX (`-O3 -march=alderlake`, [Godbolt](https://godbolt.org/z/WM1xWjqc3)) sequences are less efficient than GCC 15.

Under `-O3`, 1to6_nnue executes 1342.1B instructions, with 182.2B Loads, 61.8B Stores, 229.1B 128-bit integer vector instructions (e.g., SSE, `int_vec_retired.128bit` counter), 77.6B branch instructions, with 1612.9M mispredictions. Its MPKI is only `1612.9M/1342.1B*1000=1.20`; the main bottleneck is the neural network inference above.

GCC 15 under `-O3`: 1to6_nnue instruction count drops to 1015.3B, with 175.0B Loads, 57.8B Stores, only 97.0B 128-bit integer vector instructions, 77.4B branch instructions, showing significant optimization.

GCC 14 under `-march=native`: 1to6_nnue instruction count plummets to 446.8B (only one-third of the original), with 119.6B Loads, 44.4B Stores, 48.7B branch instructions, 13.2B 256-bit AVX VNNI instructions (`int_vec_retired.vnni_256` counter), showing significant optimization.

#### 3. 7to11_nnue

7to11_nnue behaves similarly to 1to6_nnue, with the bottleneck also in `Stockfish::Eval::NNUE:evaluate`. Enabling `-march=native` reduces time from 72s to 31s. GCC 15's improvement is also similar to 1to6_nnue, from 72s to 46s.

Under `-O3`, 7to11_nnue executes 1253.2B instructions, with 176.1B Loads, 61.6B Stores, 212.5B 128-bit integer vector instructions, 75.4B branch instructions, with 1547.5M mispredictions. Its MPKI is only `1547.5M/1253.2B*1000=1.23`; the main bottleneck remains neural network inference.

GCC 15 under `-O3`: 7to11_nnue instruction count drops to 955.3B, with 169.4B Loads, 57.8B Stores, only 92.3B 128-bit integer vector instructions, 75.2B branch instructions, showing significant optimization.

GCC 14 under `-march=native`: 7to11_nnue instruction count plummets to 425.9B (only one-third), with 115.1B Loads, 43.7B Stores, 47.1B branch instructions, 12.0B 256-bit AVX VNNI instructions, showing significant optimization.

#### Summary

Performance under different compilation options:

| Workload          | Compiler + Flags         | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | Mispredictions (M) | MPKI | 128-bit Int Vec (B) | 256-bit Int Vec (B) |
|-------------------|--------------------------|----------|----------|----------|-----------|----------|------------------|------|--------------------|---------------------|
| 1. 1to6_classical | GCC 14 `-O3`           | 47       | 531.8    | 135.7    | 59.7      | 56.0     | 2622.8           | 4.93 | 0.13               | 0.00                |
| 1. 1to6_classical | GCC 14 `-O3 -mpopcnt`  | 44       | 453.9    | 124.2    | 53.1      | 46.1     | 2639.3           | 5.81 | 0.13               | 0.00                |
| 2. 1to6_nnue      | GCC 14 `-O3`           | 77       | 1342.1   | 182.2    | 61.8      | 77.6     | 1612.9           | 1.20 | 229.1              | 0.00                |
| 2. 1to6_nnue      | GCC 15 `-O3`           | 49       | 1015.3   | 175.0    | 57.8      | 77.4     | 1258.2           | 1.24 | 97.0               | 0.00                |
| 2. 1to6_nnue      | GCC 14 `-march=native` | 32       | 446.8    | 119.6    | 44.4      | 48.7     | 953.8            | 2.13 | 5.1                | 36.3                |
| 3. 7to11_nnue     | GCC 14 `-O3`           | 72       | 1253.2   | 176.1    | 61.6      | 75.4     | 1547.5           | 1.23 | 212.5              | 0.00                |
| 3. 7to11_nnue     | GCC 15 `-O3`           | 46       | 955.3    | 169.4    | 57.8      | 75.2     | 1224.7           | 1.28 | 92.3               | 0.00                |
| 3. 7to11_nnue     | GCC 14 `-march=native` | 31       | 425.9    | 115.1    | 43.7      | 47.1     | 922.9            | 2.17 | 4.6                | 35.0                |

1to6_classical resembles a traditional chess engine with complex branching and memory access, so its MPKI=4.93 is similar to SPEC CPU 2017's 531.deepsjeng_r (MPKI=3.16), falling in the higher category. Meanwhile, 1to6_nnue and 7to11_nnue are mainly bottlenecked by i8 matrix operations; whether hardware acceleration instructions (here AVX-VNNI) are available has a major performance impact, with branch prediction becoming much less significant. The overall average MPKI is 1.85, not particularly high.

### 707.ntest_r

ntest is an Othello (Reversi) engine. The benchmark includes:

```shell
ntest_r Othello.154.ggf 20 16
```

Measured runtime is 140s. The reftime is 592s, corresponding to 4.2 points. With various optimized flags: `-O3 -flto` vs. `-O3` brings 4% improvement; further `-O3 -flto -march=native` vs. `-O3 -flto` brings another 10%. Below is detailed workload analysis. Othello rules are simple: you can only place a piece at an empty position if it flips at least one opponent's piece, otherwise you pass. The flipping rule: along all 8 directions (horizontal, vertical, diagonal), if all pieces between the new piece and another of your own pieces are opponent's pieces, they all get flipped. `perf` shows these high-time-share functions:

- `flips(int sq, u64 mover, u64 enemy)` from `src/flips.cpp`: 34.80%, the main cost. Based on board state, through memory accesses and bit operations, it first checks `neighbors[sq]&enemy` for adjacent enemy pieces (none means cannot play), then computes which pieces get flipped. Mainly data-dependent memory accesses mixed with bit operations;
- `solveNParity(int alpha, int beta, u64 mover, u64 enemy, u64 parity, EndgameSearch* search, bool hasPassed)` from `src/solve.cpp`: 14.21%, alpha-beta pruning minimax (negamax variant), iterating over empty positions. It first finds those with good parity (using `bitSet()` which uses AMD64's `bt` instruction, since in Othello the player making the last move gains an advantage, so it prioritizes positions giving the last move), calling `flips()` to check for flips, recursing if flips occur, then iterating again for bad parity positions. Main bottleneck is memory access and data-dependent branches;
- `__popcountdi2`: 9.65%, without `-mpopcnt/-march=native`, needed for counting pieces of each color, etc.;
- `solveNFlipParity`: 8.95%, works with solveNParity to complete the minimax algorithm;
- `solve2`: 5.38%, part of the minimax algorithm, handling the final position with only two empty squares, where determining the winner is straightforward without further recursion.

This is a typical chess engine pattern: the entire minimax algorithm takes 70%+ of the time, with extensive bit operations and memory accesses for position searching, plus data-dependent branches. Indeed: 2688.3B instructions executed, with 647.8B Loads, 255.2B Stores, 228.2B branches, 6.1B mispredictions, MPKI reaching `6.1B/2688B*1000=2.27`. Via `perf record -e branch-misses:pp`, `solveNParity` and `solveNFlipParity` together contribute 60.37% of mispredictions, mainly from the loop's good/bad parity checks and linked list insertion NULL checks, all data-dependent branches.

Similar to 706.stockfish_r, it has significant popcnt calls, so enabling `-mpopcnt` gives nice improvement: time drops from 140s to 126s (11% reduction), instructions reduce to 2286.9B with 586.9B Loads, 206.7B Stores, 187.6B branches. Even with `-march=native`, performance only further drops to 122s, with minimal AVX2 usage.

On the other hand, LLVM 22 is faster than GCC 14 on 707.ntest_r: with the same `-O3` flags, runtime drops from GCC 14's 140s to 126s. Investigating the assembly reveals that LLVM 22, without `-mpopcnt`, directly inlines code similar to libgcc's `__popcountdi2` into the program, saving the libgcc call overhead at the cost of larger code size, executing 2416.9B instructions with 542.7B Loads, 202.9B Stores, 168.2B branches. Similarly, 706.stockfish_r's 1to6_classical is also faster with LLVM 22 vs. GCC 14, from 47s to 44s.

Meanwhile, GCC 15 also improves over GCC 14, from 140s to 130s. Assembly analysis reveals the main optimization in `flips(int sq, u64 mover, u64 enemy)`. Two performance differences:

1. Callee-saved register usage: GCC 14 performs a series of push/pop in prologue/epilogue unconditionally, while GCC 15 is smarter, only performing push/pop when `if (neighbors[sq]&enemy)` is true and the complex function body requiring callee-saved registers is needed, otherwise returning directly, since the condition check doesn't use callee-saved registers.
2. The self-compiled GCC 15 defaults to -no-pie mode while the distro's GCC 14 defaults to -pie. In -no-pie mode, absolute addresses allow memory operands directly in imul etc., saving registers and eliminating the need for callee-saved registers, removing push/pop overhead entirely. `-static` provides similar benefit. The first point was observed after manually adding -pie to GCC 15. The main performance gain comes from reducing push/pop execution count.

GCC 15's 707.ntest_r executes 2429.3B instructions with 610.9B Loads, 206.2B Stores, 224.7B branches. Results under different compilers and flags:

| Compiler + Flags             | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) |
|------------------------------|----------|----------|----------|-----------|----------|
| GCC 14 `-O3`               | 140      | 2688.3   | 647.8    | 255.2     | 228.2    |
| GCC 14 `-O3 -flto`         | 134      | 2656.3   | 623.4    | 251.3     | 200.9    |
| GCC 14 `-O3 -mpopcnt`      | 126      | 2286.9   | 586.9    | 206.7     | 187.6    |
| GCC 14 `-O3 -march=native` | 122      | 2230.0   | 588.2    | 206.4     | 185.2    |
| LLVM 22 `-O3`              | 126      | 2416.9   | 542.7    | 202.9     | 168.2    |
| GCC 15 `-O3`               | 130      | 2429.3   | 610.9    | 206.2     | 224.7    |

Combining 706.stockfish_r and 707.ntest_r shows that popcnt is quite commonly used. Unfortunately, the AMD64 baseline doesn't provide this instruction, so with x86-64-v2 or higher optimization flags, such applications can use a single popcnt instruction to eliminate the libgcc `__popcountdi2` call overhead. Compared to AVX-VNNI, popcnt is far more widely available.

### 708.sqlite_r

sqlite is the famous database and needs no introduction. The benchmark includes three workloads:

```shell
# 1. main
sqlite_r --memdb --size 2000 --testset main --verify
# 2. cte
sqlite_r --memdb --size 2000 --testset cte --verify
# 3. fp
sqlite_r --memdb --size 1000 --testset fp --verify
```

Measured times: 69s, 12s, and 25s respectively, totaling 106s. The reftime is 528s, corresponding to 5.0 points. Enabling `-flto`/`-ljemalloc` has minimal impact; `-march=native` even causes regression. Below is per-workload analysis.

#### 1. main

`perf` hotspot functions:

- `sqlite3BtreeMovetoUnpacked(BtCursor *pCur, UnpackedRecord *pIdxKey, i64 intKey, int biasRight, int *pRes)` from `src/sqlite3.c`: 24.66%, B-tree search for entries by key. A time-consuming part is byte-by-byte scanning of pCell memory, plus frequent `sqlite3GetVarint` calls to read variable-length ints for binary search;
- `sqlite3VdbeExec(Vdbe *p)` from `src/sqlite3.c`: 22.36%, a Loop+Switch bytecode VM executing compiled SQL statements. VDBE (Virtual Database Engine) is SQLite's execution engine, maintaining a `pc` scanning bytecodes from the `aOp` array. Each bytecode is a `struct VdbeOp`; based on the `opcode` field, a large switch-case (176 different Ops) is performed. GCC compiles this into a jump table, storing each case's address in an array, computing the target from `opcode`, then `jmp *%rax`. Some interpreters use C extensions with computed goto labels, or further jump directly to the next opcode's case at each case's end. Further reading: [Android Runtime Interpreter Implementation](./android-runtime-interpreter.md);
- `pcache1Fetch(sqlite3_pcache *p, unsigned int iKey, int createFlag)` from `src/sqlite3.c`: 8.26%, a hash table Page Cache for caching disk data in memory, with main bottleneck in `pcache1FetchNoMutex`'s `pPage = pCache->apHash[iKey % pCache->nHash]; while( pPage && pPage->iKey!=iKey ){ pPage = pPage->pNext; }`, scanning linked list in hash buckets with frequent random accesses;
- `sqlite3GetVarint(const unsigned char *p, u64 *v)` from `src/sqlite3.c`: 3.70%, recovering variable-length integers from memory (e.g., `[0,127]` uses one byte, `[128,16383]` uses two bytes, up to nine bytes). This encoding is quite common and usually saves space.

Classic data structures: B-tree, Loop+Switch interpretation, and hash table lookup. An example VDBE instruction sequence:

```sql
sqlite> CREATE TABLE test(key INT, value INT);
sqlite> EXPLAIN SELECT * FROM test WHERE key = 1;
addr  opcode         p1    p2    p3    p4             p5  comment
----  -------------  ----  ----  ----  -------------  --  -------------
0     Init           0     10    0                    0   Start at 10
1     OpenRead       0     2     0     2              0   root=2 iDb=0; test
2     Rewind         0     9     0                    0
3       Column         0     0     1                    0   r[1]= cursor 0 column 0
4       Ne             2     8     1     BINARY-8       84  if r[1]!=r[2] goto 8
5       Column         0     0     3                    0   r[3]= cursor 0 column 0
6       Column         0     1     4                    0   r[4]= cursor 0 column 1
7       ResultRow      3     2     0                    0   output=r[3..4]
8     Next           0     3     0                    1
9     Halt           0     0     0                    0
10    Transaction    0     0     1     0              1   usesStmtJournal=0
11    Integer        1     2     0                    0   r[2]=1
12    Goto           0     1     0                    0
```

It scans every row of the test table, reads the key column, skips to the next row if not equal to 1; if equal, reads all columns and adds to results.

Main bottleneck is memory. 896.3B instructions executed, with 252.4B Loads, 105.1B Stores, 178.0B branches, 1.5B mispredictions, MPKI = `1.5B/896.3B*1000=1.67`.

#### 2. cte

`perf` hotspot functions:

- `sqlite3VdbeExec(Vdbe *p)` from `src/sqlite3.c`: 41.15%, most time in query execution, since this cte workload has complex computations, implementing Sudoku (recursive and non-recursive), Mandelbrot, and testing EXCEPT SELECT syntax via SQL;
- `sqlite3VdbeRecordCompareWithSkip(int nKey1, const void *pKey1, UnpackedRecord *pPKey2, int bSkip)` from `src/sqlite3.c`: 7.37%, comparing two rows, calling `sqlite3VdbeSerialGet` to retrieve data then comparing by type;
- `sqlite3VdbeSerialGet(const unsigned char *buf, u32 serial_type, Mem *pMem)` from `src/sqlite3.c`: 5.95%, deserialization based on stored data type (integer or float), its switch-case also compiled into a jump table;
- `vdbeSorterSort(SortSubtask *pTask, SorterList *pList)` from `src/sqlite3.c`: 5.95%, merge sort implementation, with main time in function pointer comparator calls and merging based on comparison results.

Bottleneck is mainly the interpreter, similar to CPython. 306.0B instructions, with 82.8B Loads, 39.6B Stores, 62.6B branches, 40.9M mispredictions, MPKI = `40.9M/306.0B*1000=0.13`, very low.

#### 3. fp

`perf` hotspot functions:

- `sqlite3VdbeExec(Vdbe *p)` from `src/sqlite3.c`: 30.66%, query execution with significant floating-point operations in this fp workload;
- `sqlite3AtoF(const char *z, double *pResult, int length, u8 enc)` from `src/sqlite3.c`: 19.18%, string-to-float conversion since the SQL contains many float literals;
- `vdbeSorterSort(SortSubtask *pTask, SorterList *pList)` from `src/sqlite3.c`: 10.44%, see above;
- `sqlite3VdbeRecordCompareWithSkip(int nKey1, const void *pKey1, UnpackedRecord *pPKey2, int bSkip)` from `src/sqlite3.c`: 6.76%, see above.

Bottleneck is mainly the interpreter, with significant time on string-to-float conversion due to SQL design. 554.7B instructions, 132.3B Loads, 61.3B Stores, 111.5B branches, 392.6M mispredictions, MPKI = `392.6M/554.7B*1000=0.71`.

#### Summary

Results under different flags:

| Workload | Compiler + Flags           | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | MPKI |
|----------|----------------------------|----------|----------|----------|-----------|----------|------|
| 1. main  | GCC 14 `-O3`               | 69       | 896.3    | 252.4    | 105.1     | 178.0    | 1.67 |
| 1. main  | GCC 14 `-O3 -march=native` | 73       | 905.3    | 273.7    | 109.9     | 177.2    | 1.62 |
| 2. cte   | GCC 14 `-O3`               | 12       | 306.0    | 82.8     | 39.6      | 62.6     | 0.13 |
| 2. cte   | GCC 14 `-O3 -march=native` | 13       | 303.6    | 88.9     | 40.0      | 62.6     | 0.13 |
| 3. fp    | GCC 14 `-O3`               | 25       | 554.7    | 132.3    | 61.3      | 111.5    | 0.71 |
| 3. fp    | GCC 14 `-O3 -march=native` | 27       | 555.8    | 142.7    | 62.6      | 111.6    | 0.69 |

As shown, sqlite_r is one of those hard-to-optimize benchmarks: heavy memory access, computation, and branching interleaved, heavy on the memory subsystem, hard to vectorize. `-O3 -march=native` actually increases runtime from 106s to 113s, a regression. Overall: 1760B instructions, 353B branches, MPKI only 1.08, mainly from main.

### 710.omnetpp_r

The familiar 520.omnetpp_r from SPEC INT 2017, but with different workloads. 520.omnetpp_r simulated a 10 Gbps network; 710.omnetpp_r has ten workloads, significantly more diverse:

```shell
omnetpp_r -f randomMesh.ini -c General
omnetpp_r -f queuenet.ini -c OneFifo
omnetpp_r -f queuenet.ini -c TandemFifos
omnetpp_r -f queuenet.ini -c SmallCQN
omnetpp_r -f queuenet.ini -c Ring
omnetpp_r -f queuenet.ini -c Terminal
omnetpp_r -f queuenet.ini -c CallCenter
omnetpp_r -f queuenet.ini -c ForkJoin
omnetpp_r -f queuenet.ini -c ResourceAllocation
omnetpp_r -f queuenet.ini -c AllocDealloc
```

Measured times: 24.6s, 7.8s, 3.8s, 4.6s, 9.1s, 3.7s, 2.6s, 9.4s, 6.6s, and 14.0s, totaling 86.2s. The reftime is 486s, corresponding to 5.6 points.

#### 1. randomMesh

Hotspot functions:

- `omnetpp::cTopology::calculateUnweightedSingleShortestPathsTo(Node *_target)` from `src/simulator/sim/ctopology.c`: 16.22%, classic single-source shortest path (effectively BFS since all edges have unit weight), with bottleneck from random memory access and double-precision floating-point distance computation;
- `__do_dyncast` and `__dynamic_cast` from libstdc++.so: 4.73%+3.24%+2.22%+0.81%=11.0%, some dynamic_cast usage, e.g., `Routing::handleMessage`;
- `Routing::handleMessage(cMessage *msg)` from `src/model/Routing.cc`: 7.10%, simulating routing table, where main logic inlines a `std::map<int, int>` `find` operation ([Godbolt](https://godbolt.org/z/ne6oEb9Md)), querying a red-black tree;
- `cEvent::shouldPrecede(const cEvent *other)` from `src/simulator/sim/cevent.cc`: 4.64%, multi-key comparison of cEvent structs.

Overall, bottlenecks are spread across many locations. 306.4B instructions, 98.7B Loads, 50.2B Stores, 62.1B branches, 661.2M mispredictions, MPKI = `661.2M/306.4B*1000=2.16`. With `-O3 -flto`, instructions drop to 284.6B (91.3B Loads, 45.4B Stores, 55.7B branches). Further with `-O3 -flto -ljemalloc`, instructions drop to 279.8B (90.3B Loads, 44.4B Stores, 54.3B branches).

randomMesh under different flags:

| Compiler + Flags              | Insns (B) | Load (B) | Store (B) | Branch (B) |
|-------------------------------|----------|----------|-----------|----------|
| GCC 14 `-O3`                  | 306.4    | 98.7     | 50.2      | 62.1     |
| GCC 14 `-O3 -flto`            | 284.6    | 91.3     | 45.4      | 55.7     |
| GCC 14 `-O3 -flto -ljemalloc` | 279.8    | 90.3     | 44.4      | 54.3     |

#### Remaining 2-10: 9 queuenet workloads

`perf` shows the remaining 9 queuenet workloads' bottlenecks concentrated in:

- strcmp (`__strcmp_avx2`)
- dynamic_cast (`__do_dyncast` and `__dynamic_cast`)
- malloc, free, and operator new
- printf (`__printf_buffer`)

Plus some omnetpp functions (e.g., `omnetpp::common::StringPool::obtain(const char *s)`, mainly querying and modifying `std::unordered_map<const char *,int,str_hash, str_eq> pool`), scattered around with each under 5%. With such heavy libc/libstdc++ usage, standard library and memory allocator implementations become critical.

#### Summary

Based on the above analysis, different compiler flags were tested:

- `-O3 -ljemalloc`: all ten workloads improve, total from 86.2s to 80.6s, score from 5.6 to 6.0.
- `-O3 -flto`: total from 86.2s to 76.1s, score from 5.6 to 6.4.
- `-O3 -flto -ljemalloc`: total from 86.2s to 69.7s, score from 5.6 to 7.0.

Similar patterns appeared in SPEC INT 2017: `-O3 -flto` was 3% faster than `-O3`; `-O3 -flto -ljemalloc` was 20% faster than `-O3 -flto`.

Under `-O3`, total instructions are 1447B, with 291B branches, MPKI = 0.78. Although randomMesh has high MPKI due to graph computation, the overall MPKI is dragged down by other workloads. In comparison, SPEC INT 2017 Rate's 520.omnetpp_r had MPKI of 4.33. Same framework, but workload behavior has changed significantly.

### 714.cpython_r

We just mentioned interpreters, and here comes CPython. The benchmark contains three workloads:

```shell
# 1. resnet
cpython_r -I -B coreml_pb.py -i 2 -a -m Resnet50Headless.mlmodel -d 10
# 2. mobilenet
cpython_r -I -B coreml_pb.py -i 5 -a -c -m MobileNetV2.mlmodel -d 20
# 3. dna
cpython_r -I -B dna_bench.py 600000
```

Runtimes: 31s, 20s, and 20s, total 71s, reftime 479s, corresponding to 6.7 points. With `-O3 -flto`: 29s, 19s, and 18s, total 66s, 7.3 points. `-O3 -ljemalloc` has minimal impact; `-O3 -march=native` causes regression. Detailed analysis follows.

#### 1. resnet

Hotspot functions via `perf`:

- `_PyEval_EvalFrameDefault(PyThreadState *tstate, _PyInterpreterFrame *frame, int throwflag)` from `src/cpython/Python/ceval.c`: 24.09%, the interpreter's Loop + Switch core, interpreting Python bytecode. Main bottleneck is the jump table (`jmp *%rax` based on opcode);
- `PyUnicode_FromFormatV(const char *format, va_list vargs)` from `src/cpython/Objects/unicodeobject.c`: 4.51%, sprintf into Python string, with bottleneck in format string parsing, finding `%` positions;
- `_PyObject_Free(void *ctx, void *p)` from `src/cpython/Objects/obmalloc.c`: 3.48%, freeing PyObject. Python has its own allocator for PyObjects rather than using malloc/free directly;
- `_PyObject_Malloc(void *ctx, size_t nbytes)` from `src/cpython/Objects/obmalloc.c`: 3.15%, allocating PyObject.

The rest is scattered, mainly around the interpreter loop. 651.6B instructions, 180.4B Loads, 104.1B Stores, 136.6B branches, only 7.9M mispredictions, MPKI = `7.9M/651.6B*1000=0.01`, negligible. With `-O3 -flto`: same hotspots, instructions drop to 618.0B (176.6B Loads, 93.9B Stores, 128.6B branches, 48.6M mispredictions).

#### 2. mobilenet

Same top-four hotspots with similar proportions, likely because resnet and mobilenet use the same .py source, just different models. 438.9B instructions, 121.4B Loads, 70.5B Stores, 91.6B branches, 9.1M mispredictions, MPKI = `9.1M/438.9B*1000=0.02`, negligible. With `-O3 -flto`: instructions drop to 416.4B (119.0B Loads, 63.8B Stores, 86.2B branches, 35.0M mispredictions).

#### 3. dna

Hotspot functions:

- `_PyEval_EvalFrameDefault(...)`: 36.75%, see above;
- `_PyObject_Free(...)`: 5.31%, see above;
- `PyUnicode_Contains(PyObject *str, PyObject *substr)` from `src/cpython/Objects/unicodeobject.c`: 4.59%, Python string contains operation, corresponding to `char in "GATC"` in `data/all/input/knucleotide.py`;
- `_PyObject_Malloc(...)`: 3.52%, see above.

Main hotspot remains interpretation, though `PyUnicode_Contains` is higher due to frequent string contains calls. 394.9B instructions, 113.3B Loads, 62.1B Stores, 77.1B branches, 228.1M mispredictions, MPKI = `228M/394B*1000=0.58`, still very low. With `-O3 -flto`: 379.3B instructions (113.4B Loads, 58.5B Stores, 71.6B branches, 223.8M mispredictions).

#### Summary

Results under different flags:

| Workload     | Compiler + Flags   | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | Mispredictions (M) |
|--------------|--------------------|----------|----------|----------|-----------|----------|--------------|
| 1. resnet    | GCC 14 `-O3`       | 31       | 651.6    | 180.4    | 104.1     | 136.6    | 7.9          |
| 1. resnet    | GCC 14 `-O3 -flto` | 29       | 618.0    | 176.6    | 93.9      | 128.6    | 48.6         |
| 2. mobilenet | GCC 14 `-O3`       | 20       | 438.9    | 121.4    | 70.5      | 91.6     | 9.1          |
| 2. mobilenet | GCC 14 `-O3 -flto` | 19       | 416.4    | 119.0    | 63.8      | 86.2     | 35.0         |
| 3. dna       | GCC 14 `-O3`       | 20       | 394.9    | 113.3    | 62.1      | 77.1     | 228.1        |
| 3. dna       | GCC 14 `-O3 -flto` | 18       | 379.3    | 113.4    | 58.5      | 71.6     | 223.8        |

714.cpython_r is a typical bytecode interpreter with Loop + Switch structure. Overall MPKI is very low at 0.17; even with `-O3 -flto` (more mispredictions but fewer total instructions, higher MPKI), the absolute number is still tiny at 0.23.

### 721.gcc_r

502.gcc_r existed in SPEC INT 2017 (based on GCC 4.5.0, compiling gcc-pp.c, gcc-smaller.c, and ref32.c five times each). This time, 721.gcc_r compiles the same three files once each (gcc-pp.c content updated, others unchanged), based on GCC 11.2.0, with simplified command lines:

```shell
# 1. gcc-pp
cc1_r gcc-pp.c -O2 -fpic -o gcc-pp.c.opts-O2_-fpic.s
# 2. gcc-smaller
cc1_r gcc-smaller.c -O3 -fipa-pta -o gcc-smaller.c.opts-O3_-fipa-pta.s
# 3. ref32
cc1_r ref32.c -O3 -finline-limit=12000 -fno-tree-vrp -o ref32.c.opts-O3_-finline-limit_12000_-fno-tree-vrp.s
```

`-O3` runtimes: 44s, 21s, and 51s, total 116s, reftime 686s, corresponding to 5.9 points. `-O3 -flto` slightly reduces to 115s; `-O3 -flto -ljemalloc` further reduces to 111s, mainly targeting the ~2% time spent in malloc/free. `-march=native` has almost no impact.

Similar to 502.gcc_r (see [The Alberta Workloads for the SPEC CPU 2017 Benchmark Suite analysis](https://webdocs.cs.ualberta.ca/~amaral/AlbertaWorkloadsForSPECCPU2017/reports/gcc_report.html)), 721.gcc_r's time is distributed across many functions. Except ref32 spending 10.76% in `dominated_by_p` and 5.92% in `bitmap_set_bit`, other functions are mostly under 3%, with no single dominant hotspot.

`bitmap_set_bit(bitmap head, int bit)` from `src/gcc/bitmap.cc` sets a bit in a bitmap using bit operations. Notably, this bitmap can be stored as either a splay tree or linked list. From `perf record -e branch-misses:pp`, this function's mispredictions mainly come from checking whether the bit is already set before writing. This saves some Store instructions but introduces branch mispredictions. Plus linked list insertion with NULL pointer checks.

`dominated_by_p(enum cdi_direction dir, const_basic_block bb1, const_basic_block bb2)` from `src/gcc/dominance.cc` performs basic block dominance queries (A dom B means all paths from entry to B pass through A), which is common in compilers. Due to frequent queries, two DFS passes precompute topological order, then dominance is checked via: `DFS_Number_In(A) <= DFS_Number_In(B) && DFS_Number_Out(A) >= DFS_Number_Out(B)`. The function is simple with precomputed DFS results, but combining two comparisons into `cmp+jl` and `cmp+setle` causes branch mispredictions. The `&&` short-circuit means the second condition (with two memory accesses) theoretically shouldn't execute if the first fails. Rewriting to perform both comparisons then AND would eliminate branches but increase memory accesses: [Godbolt](https://godbolt.org/z/qKaKzT6a1).

Performance counters for the three workloads:

1. gcc-pp: 470.2B instructions, 125.6B Loads, 58.8B Stores, 99.9B branches, 2.2B mispredictions, MPKI = `2.2B/470.2B*1000=4.68`
2. gcc-smaller: 243.4B instructions, 65.0B Loads, 30.3B Stores, 51.8B branches, 0.91B mispredictions, MPKI = `0.91B/243.4B*1000=3.74`
3. ref32: 403.7B instructions, 118.9B Loads, 45.8B Stores, 86.1B branches, 0.61B mispredictions, MPKI = `0.61B/403.7B*1000=1.51`

Results:

| Workload       | Compiler + Flags        | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | Mispred (B) | MPKI |
|----------------|-------------------------|----------|----------|----------|-----------|----------|--------------|------|
| 1. gcc-pp      | GCC 14 `-O3`            | 44       | 470.2    | 125.6    | 58.8      | 99.9     | 2.2          | 4.68 |
| 1. gcc-pp      | GCC 14 `-O3 -ljemalloc` | 42       | 467.2    | 125.2    | 58.7      | 98.5     | 2.2          | 4.71 |
| 2. gcc-smaller | GCC 14 `-O3`            | 21       | 243.2    | 65.0     | 30.3      | 51.8     | 0.91         | 3.74 |
| 2. gcc-smaller | GCC 14 `-O3 -ljemalloc` | 21       | 242.1    | 64.7     | 30.2      | 51.2     | 0.90         | 3.72 |
| 3. ref32       | GCC 14 `-O3`            | 51       | 403.8    | 118.9    | 45.8      | 86.1     | 0.61         | 1.51 |
| 3. ref32       | GCC 14 `-O3 -ljemalloc` | 49       | 405.2    | 119.4    | 46.2      | 85.8     | 0.61         | 1.51 |

Overall 1120B instructions, 238B branches, MPKI = 3.37, quite high for SPEC INT 2026. For comparison, SPEC INT 2017 Rate's 502.gcc_r had MPKI of 3.13, not much different.

Unsurprisingly, 721.gcc_r compiled with GCC 14 runs faster than when compiled with LLVM 22.

### 723.llvm_r

With LLVM's growth, SPEC CPU 2026 finally includes it. Similar to 721.gcc_r, it runs the LLVM optimizer but with .bc IR files as input rather than C source. Two workloads:

```shell
# 1. transformsplus
llvm-opt_r transformsplus.bc -S -O3 -mcpu=pwr9
# 2. codegen
llvm-opt_r codegen.bc -S -O3 -mcpu=pwr9
```

`-O3` runtimes: 62s and 53s, total 115s, reftime 507s, corresponding to 4.4 points. `-O3 -flto` actually regresses, but `-O3 -ljemalloc` gives significant improvement: 59s and 47s, total 106s, 4.8 points. `-march=native` has almost no impact.

Interestingly, 723.llvm_r compiled with GCC 14 runs faster than with LLVM 22, though the advantage is small. Detailed analysis follows.

#### 1. transformsplus

`perf` hotspots:

- `llvm::InstCombinerImpl::foldIntegerTypedPHI(llvm::PHINode& PN)` from `src/lib/Transforms/InstCombine/InstCombinePHI.cpp`: 4.06%, processing PHI nodes in IR, with main bottleneck in inner loop traversing use chains with random memory access and LLVM's custom RTTI type checks via branches;
- `_int_malloc/cfree/malloc`: 2.38%+0.89%+0.82%=4.09%, heavy allocation/deallocation, hence `-ljemalloc` helps;
- `llvm::DenseMapBase::FindAndConstruct()`: 1.69%, LLVM's array-based hash table, with bottleneck in reading hash bucket entries and comparing keys (random access). Recently [LLVM has been optimizing this](https://maskray.me/blog/2026-06-07-recent-llvm-hash-table-improvements).

Many other small functions with low individual share; time is spread widely like 721.gcc_r. 572.8B instructions, 137.7B Loads, 78.6B Stores, 118.7B branches, 3.5B mispredictions, MPKI = `3.5B/572.8B*1000=6.11`, quite high.

From `perf record -e branch-misses:pp`, mispredictions are spread across many functions. Top-down analysis shows 40% Frontend Bound, 19.2% Bad Speculation. Further analysis reveals L1 ICache misses at 12.6B (`L1-icache-load-misses` counter), giving L1IC MPKI of `12.6B/572.8B*1000=22.0`. The main issue is 723.llvm_r's code size being too large for L1IC, and BTB is likely also strained.

#### 2. codegen

`perf` hotspots:

- `llvm::InstCombinerImpl::foldIntegerTypedPHI(llvm::PHINode& PN)`: 20.85%, see above;
- `_int_malloc/cfree/malloc`: 1.91%+0.72%+0.65%=3.28%, see above;
- `llvm::DenseMapBase::FindAndConstruct()`: 1.29%, see above.

Overall similar to transformsplus, with `foldIntegerTypedPHI` taking a larger share. 415.9B instructions, 100.4B Loads, 57.5B Stores, 86.0B branches, 2.4B mispredictions, MPKI = `2.4B/415.9B*1000=5.77`, still high.

#### Summary

Results:

| Workload          | Compiler + Flags        | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | Mispred (B) | MPKI |
|-------------------|-------------------------|----------|----------|----------|-----------|----------|--------------|------|
| 1. transformsplus | GCC 14 `-O3`            | 62       | 572.8    | 137.7    | 78.6      | 118.7    | 3.5          | 6.11 |
| 1. transformsplus | GCC 14 `-O3 -ljemalloc` | 59       | 563.2    | 135.7    | 77.2      | 115.2    | 3.3          | 5.86 |
| 2. codegen        | GCC 14 `-O3`            | 53       | 415.9    | 100.4    | 57.5      | 86.0     | 2.4          | 5.77 |
| 2. codegen        | GCC 14 `-O3 -ljemalloc` | 47       | 411.0    | 99.3     | 56.6      | 84.1     | 2.3          | 5.60 |

LLVM and GCC, twin stars of the compiler world, share similar workload characteristics: heavy memory allocation/deallocation benefiting from `-ljemalloc`; time spread across many small functions with no dominant hotspot; high MPKI. 723.llvm_r becomes the highest-MPKI benchmark in SPEC INT 2026 Rate at 5.98, likely due to its many data-dependent branches. Overall 991B instructions, 205B branches. Even in SPEC INT 2017 Rate, it would follow closely behind 505.mcf_r and 541.leela_r as the third-highest MPKI.

### 727.cppcheck_r

cppcheck is a C++ static analysis tool that reports issues like array out-of-bounds or uninitialized variables. It analyzes three different codes, seemingly sourced from other benchmarks. 747.dealii (became part of 766.femflow_r) and 770.7z aren't in SPEC CPU 2026 (not selected); only 738 diamond remains as 838.diamond_s:

```shell
# 1. 738_diamond
cppcheck_r --force 738-diamond-record.cpp --checkers-report=738_report.txt --enable=all --output-file=738_bogey.txt
# 2. 747_dealii
cppcheck_r --force 747-dealii-data_out_base.cc --checkers-report=747_report.txt --enable=all --output-file=747_bogey.txt
# 3. 770_7z
cppcheck_r --force 770-7z-SystemPage.cpp --checkers-report=770_report.txt --output-file=770_bogey.txt
```

Runtimes: 27s, 22s, and 33s, total 82s, reftime 359s, corresponding to 4.4 points. `-O3 -flto` or `-O3 -march=native` only improve ~1%, but `-O3 -ljemalloc` significantly improves to 24s, 18s, and 29s, total 71s, 5.1 points.

#### 1. 738_diamond

Hotspot functions:

- `multiCompareImpl(const Token *tok, const char *haystack, nonneg int varid)` from `src/lib/token.cpp`: 40.82%, string matching, matching a token against `abc|def` by comparing characters, skipping to next `|` when no match;
- `Token::Match(const Token *tok, const char pattern[], nonneg int varid)` from `src/lib/token.cpp`: 12.08%, similar string matching with different syntax (like a custom regex subset), calling `multiCompareImpl` for partial matching;
- `ScopeInfo3::findScope(const std::string & scope)` from `src/lib/tokenize.cpp`: 5.49%, searching for symbols starting from current scope upward, with main time in `std::list` traversal and `std::string` comparison;
- `Tokenizer::simplifyUsing()`: 3.57%, transforms `using N::x;` to `using x = N::x` using `Token::Match` with patterns like `"using ::| %name% ::"`;
- `cfree/malloc/_int_malloc`: 0.47%+0.33%+0.45%=1.25%.

Main bottleneck is string matching with a simple loop-based implementation, no data structure optimization. 399.9B instructions, 81.2B Loads, 35.5B Stores, 108.9B branches, 173.2M mispredictions, MPKI = `173M/399.9B*1000=0.43`, not high.

#### 2. 747_dealii

Similar hotspots:

- `multiCompareImpl(...)`: 27.42%;
- `Token::Match(...)`: 14.55%;
- `cfree/malloc/_int_malloc`: 2.14%+1.57%+0.53%=4.24%, higher allocation share;
- `Token::simpleMatch(const Token *tok, const char pattern[], size_t pattern_len)` from `src/lib/token.cpp`: 3.88%, another string matching function with different format (e.g., `"abc def"` means match `abc` or `def`), bottleneck in `strncmp` and `memchr`;
- `TemplateSimplifier::addInstantiation(Token *token, const std::string &scope)` from `src/lib/templatesimplifier.cpp`: 2.98%, token-level code transformations, main time in `std::list` traversal;
- `isAliasOf(const Token* tok, const Token* expr, int* indirect, bool* inconclusive)` from `src/lib/astutils.cpp`: 2.55%, alias checking.

Lots of string matching with multiple syntax variants and separate implementations; unclear why. 303.9B instructions, 67.3B Loads, 31.5B Stores, 82.5B branches, 298.9M mispredictions, MPKI = `298.9M/303.9B*1000=0.98`.

#### 3. 770_7z

Hotspots:

- `multiCompareImpl(...)`: 32.25%;
- `Token::Match(...)`: 18.82%;
- `__memcmp_avx2_movbe`: 8.99%, used for string matching;
- `std::map<std::string>::equal_range`: 7.34%, red-black tree queries plus string matching;
- `__strchr_avx2`: 7.34%, used for string matching;
- `cfree/malloc/_int_malloc`: 0.37%+0.27%+0.17%=0.81%.

Still string-matching dominated. 505.2B instructions, 111.0B Loads, 43.8B Stores, 137.5B branches, 421.0M mispredictions, MPKI = `421M/505.2B*1000=0.83`.

#### Summary

Overall, 727.cppcheck_r is constantly doing string matching. A question worth pondering: why not tokenize into numeric IDs for faster comparison? Operating at the token level with string comparisons means the bottleneck is either in cppcheck's own string comparison or libc's.

Results:

| Workload       | Compiler + Flags        | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | Mispred (M) | MPKI |
|----------------|-------------------------|----------|----------|----------|-----------|----------|--------------|------|
| 1. 738_diamond | GCC 14 `-O3`            | 27       | 399.9    | 81.2     | 35.5      | 108.9    | 173.2        | 0.43 |
| 1. 738_diamond | GCC 14 `-O3 -ljemalloc` | 24       | 395.0    | 80.2     | 34.7      | 107.5    | 171.8        | 0.43 |
| 2. 747_dealii  | GCC 14 `-O3`            | 22       | 303.9    | 67.3     | 31.5      | 82.5     | 298.9        | 0.98 |
| 2. 747_dealii  | GCC 14 `-O3 -ljemalloc` | 18       | 291.0    | 64.5     | 29.2      | 79.0     | 287.3        | 0.99 |
| 3. 770_7z      | GCC 14 `-O3`            | 33       | 505.2    | 111.0    | 43.8      | 137.5    | 421.0        | 0.83 |
| 3. 770_7z      | GCC 14 `-O3 -ljemalloc` | 29       | 501.5    | 110.1    | 43.2      | 136.6    | 409.8        | 0.82 |

Overall 1211B instructions, 329B branches; branches account for 27%, the highest in SPEC INT 2026 Rate, all thanks to string matching (read a bit, compare a bit). Yet MPKI is only 0.71, third-lowest in SPEC INT 2026 Rate (above only 714.cpython_r's 0.17 and 750.sealcrypto_r's 0.14), meaning most string matching results are highly predictable (e.g., mismatch at the first byte).

### 729.abc_r

abc is an EDA tool (first encountered through yosys), along with 734.vpr_r, both heavyweight open-source EDA tools implementing logic synthesis and place-and-route respectively. Six workloads:

```shell
# 1. twoexact
./abc_r -F twoexact.in
# 2. beem6
./abc_r -F beem6-fraig.in
# 3. mem
./abc_r -F mem_ctrl.in
# 4. vga
./abc_r -F vga_lcd_miter.in
# 5. mcml
./abc_r -F mcml.in
# 6. des
./abc_r -F des_system90.in
```

Runtimes: 6.3s, 10.1s, 13.5s, 32.3s, 13.6s, and 17.0s, total 92.8s, reftime 459s, corresponding to 4.9 points.

Enabling `-flto`, `-march=native`, or `-ljemalloc` provides negligible improvement (within 1%), impervious to all optimizations. Detailed analysis follows.

#### 1. twoexact

Hotspot functions:

- `sat_solver_propagate(sat_solver* s)` from `src/berkeley-abc/src/sat/bsat/satSolver.c`: 75.33%, SAT Solver's Unit Propagation, finding clauses with only one undetermined variable, assigning it, then propagating;
- `sat_solver_analyze(sat_solver* s, int h, veci* learnt)` from `src/berkeley-abc/src/sat/bsat/satSolver`: 15.85%, conflict analysis as part of CDCL (Conflict Driven Clause Learning);
- `sat_solver_solve_internal(sat_solver* s)` from `src/berkeley-abc/src/sat/bsat/satSolver.c`: 3.80%, SAT Solver entry point.

Rarely see such concentrated bottlenecks, but indeed, SAT Solvers spend most time in Unit Propagation and CDCL on conflicts. Reminds me of writing a [DPLL SAT Solver](https://github.com/jiegec/dpll) for a Software Analysis and Verification course long ago. Main bottleneck: memory accesses and data-dependent branches searching the SAT problem's solution space.

53.2B instructions, 13.8B Loads, 3.2B Stores, 8.4B branches, 606.2M mispredictions, MPKI = `606.2M/53.2B*1000=11.39`, very high, approaching SPEC INT 2017's 541.leela_r.

Via `perf record -e branch-misses:pp`, main mispredictions come from `sat_solver_propagate`'s variable value checks, all data-dependent and hard to predict.

#### 2. beem6

Hotspot functions:

- `Cec4_ManPackAddPatterns(Gia_Man_t * p, int iBit, Vec_Int_t * vLits)` from `src/berkeley-abc/src/proof/cec/cecSatG2.c`: 54.65%, CEC (Combinational Equivalence Checking), inner loop iterating vLits entries, updating `p->vSims` via bit operations;
- `Cec4_ManGeneratePatterns_rec(Gia_Man_t * p, Gia_Obj_t * pObj, int Value, Vec_Int_t * vPat, Vec_Int_t * vVisit)` from `src/berkeley-abc/src/proof/cec/cecSatG2.c`: 29.01%, recursive processing by pObj type.

Still concentrated hotspots. 255.5B instructions, 57.2B Loads, 7.3B Stores, 40.3B branches, 192.0M mispredictions, MPKI = `192.0M/255.5B*1000=0.75`, much lower than SAT.

#### 3. mem

Hotspots are still SAT solver-related. Compared to twoexact, `sat_solver_canceluntil` is higher at 8.46%, but overall characteristics are the same. 151.0B instructions, 43.4B Loads, 15.4B Stores, 24.2B branches, 1213.7M mispredictions, MPKI = `1213.7M/151.0B*1000=8.03`, very high.

#### 4. vga

Still SAT solver dominated. 490.0B instructions, 143.9B Loads, 54.4B Stores, 76.9B branches, 2092.8M mispredictions, MPKI = `2092.8M/490B*1000=4.27`, still high.

#### 5. mcml

New hotspot functions appear:

- `Abc_ObjDeleteFanin(Abc_Obj_t * pObj, Abc_Obj_t * pFanin)` from `src/berkeley-abc/src/base/abc/abcFanio.c`: 12.57%, calls `Vec_IntRemove` to delete an element by scanning the array and shifting subsequent elements;
- `Gia_ManSwiSimulate(Gia_Man_t * pAig, Gia_ParSwi_t * pPars)` from `src/berkeley-abc/src/aig/gia/giaSwitch.c`: 8.87%, simulation with significant time in a custom popcount function `Gia_WordCountOnes` (not recognized as popcnt, using SSE vector software popcount);
- `Abc_AigAndLookup(Abc_Aig_t * pMan, Abc_Obj_t * p0, Abc_Obj_t * p1)` from `src/berkeley-abc/src/base/abc/abcAig.c`: 7.03%, computing p0 AND p1 with special cases, then hash table linked list traversal with multi-level pointer access: `pObj->pNtk->vObjs->pArray`;
- `If_ObjPerformMappingAnd(If_Man_t * p, If_Obj_t * pObj, int Mode, int fPreprocess, int fFirst)` from `src/map/if/ifMap.c`: 6.72%, also significant time in software popcount `If_WordCountOnes`;
- `Lpk_NodeCutsOneFilter(Lpk_Cut_t * pCuts, int nCuts, Lpk_Cut_t * pCutNew)` from `src/berkeley-abc/src/opt/lpk/lpkCut.c`: 5.47%, bottleneck in data-dependent comparison branches.

208.0B instructions, 50.1B Loads, 15.4B Stores, 39.8B branches, 534.8M mispredictions, MPKI = `534.8M/208.0B*1000=2.57`.

#### 6. des

New hotspot functions again:

- `__strcmp_avx2` from libc: 22.04%, unexpectedly bottlenecked on strcmp again;
- `Nm_ManTableLookupId(Nm_Man_t * p, int ObjId)` from `src/misc/nm/nmTable.c`: 21.56%, traversing a hash table with chained linked lists;
- `Nm_ManTableAdd(Nm_Man_t * p, Nm_Entry_t * pEntry)` from `src/misc/nm/nmTable.c`: 12.19%, classic hash table insertion;
- `Nm_ManTableLookupName(Nm_Man_t * p, char * pName, int Type)` from `src/misc/nm/nmTable.c`: 5.78%, hash table lookup using string matching, explaining the high strcmp count;
- `Gia_ManSwiSimulate` from `src/aig/gia/giaSwitch.c`: 5.49%, see above;
- `spec_qsort`: 3.98%, familiar from SPEC INT 2017's 505.mcf_r (where qsort bottleneck came from function pointer comparator calls; `-flto` inlining the pointer gave 13% improvement).

Classic hash table with string matching; bottleneck in hash table queries with poor spatial locality for linked list access.

135.7B instructions, 29.7B Loads, 11.5B Stores, 23.3B branches, 372.9M mispredictions, MPKI = `372.9M/135.7B*1000=2.75`. Mispredictions mainly from `__strcmp_avx2` and `spec_qsort`.

#### Summary

Results:

| Workload    | Compiler + Flags | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | Mispred (M) | MPKI  |
|-------------|------------------|----------|----------|----------|-----------|----------|--------------|-------|
| 1. twoexact | GCC 14 `-O3`    | 6.3      | 53.2     | 13.8     | 3.2       | 8.4      | 606.2        | 11.39 |
| 2. beem6    | GCC 14 `-O3`    | 10.1     | 255.5    | 57.2     | 7.3       | 40.3     | 192.0        | 0.75  |
| 3. mem      | GCC 14 `-O3`    | 13.5     | 151.0    | 43.4     | 15.4      | 24.2     | 1213.7       | 8.03  |
| 4. vga      | GCC 14 `-O3`    | 32.3     | 490.0    | 143.9    | 54.4      | 76.9     | 2092.8       | 4.27  |
| 5. mcml     | GCC 14 `-O3`    | 13.6     | 208.0    | 50.1     | 15.4      | 39.8     | 534.8        | 2.57  |
| 6. des      | GCC 14 `-O3`    | 17.0     | 135.7    | 29.7     | 11.5      | 23.3     | 372.9        | 2.75  |

The six workloads touch different abc code paths: SAT, various EDA logic, and hash table lookups with string matching. SAT dominates the weight, giving overall MPKI of 3.87, second only to 723.llvm_r in SPEC INT 2026 Rate, exceeding 721.gcc_r and 777.zstd_r.

### 734.vpr_r

Next comes EDA's next step: after logic synthesis, place-and-route, which is what vpr_r does. Four workloads:

```shell
# 1. jpeg_place
vpr stratixiv_arch.timing.xml JPEG_stratixiv_arch_timing.blif --RL_agent_placement off --place_algorithm bounding_box --max_criticality 0.0 --init_t 512 --alpha_t 0.75 --exit_t 1 --router_initial_timing all_critical --routing_failure_predictor off --route_chan_width 300 --max_router_iterations 20 --router_lookahead classic --initial_pres_fac 1.0 --pres_fac_mult 2.0 --astar_fac 1.5 --router_profiler_astar_fac 1.5 --seed 3 --sdc_file JPEG_stratixiv_arch_timing.sdc --pack_verbosity 0 --netlist_verbosity 0 --base_cost_type demand_only --inner_num 4 --read_initial_place_file ref_JPEG_stratixiv_arch_timing.init.place --place
# 2. jpeg_route
vpr stratixiv_arch.timing.xml JPEG_stratixiv_arch_timing.blif --place_algorithm bounding_box --place_static_notiming_move_prob 50 25 25 --max_criticality 0.0 --router_initial_timing all_critical --routing_failure_predictor off --route_chan_width 300 --max_router_iterations 20 --router_lookahead classic --initial_pres_fac 1.0 --pres_fac_mult 2.0 --astar_fac 1.5 --router_profiler_astar_fac 1.5 --seed 3 --sdc_file JPEG_stratixiv_arch_timing.sdc --pack_verbosity 0 --netlist_verbosity 0 --base_cost_type demand_only --place_file ref_JPEG_stratixiv_arch_timing.place --analysis --route
# 3. smithwaterman_place
vpr stratixiv_arch.timing.xml smithwaterman_stratixiv_arch_timing.blif --RL_agent_placement off --place_algorithm bounding_box --max_criticality 0.0 --init_t 512 --alpha_t 0.75 --exit_t 1 --router_initial_timing all_critical --routing_failure_predictor off --route_chan_width 300 --max_router_iterations 20 --router_lookahead classic --initial_pres_fac 1.0 --pres_fac_mult 2.0 --astar_fac 1.5 --router_profiler_astar_fac 1.5 --seed 3 --sdc_file smithwaterman_stratixiv_arch_timing.sdc --pack_verbosity 0 --netlist_verbosity 0 --base_cost_type demand_only --inner_num 1.8 --read_initial_place_file ref_smithwaterman_stratixiv_arch_timing.init.place --place
# 4. smithwaterman_route
vpr stratixiv_arch.timing.xml smithwaterman_stratixiv_arch_timing.blif --place_algorithm bounding_box --place_static_notiming_move_prob 50 25 25 --max_criticality 0.0 --router_initial_timing all_critical --routing_failure_predictor off --route_chan_width 300 --max_router_iterations 20 --router_lookahead classic --initial_pres_fac 1.0 --pres_fac_mult 2.0 --astar_fac 1.5 --router_profiler_astar_fac 1.5 --seed 3 --sdc_file smithwaterman_stratixiv_arch_timing.sdc --pack_verbosity 0 --netlist_verbosity 0 --base_cost_type demand_only --place_file ref_smithwaterman_stratixiv_arch_timing.place --analysis --route
```

The Stratix IV here is the classic Altera FPGA, now a relic of its era. Runtimes: 21s, 29s, 18s, and 19s, total 87s, reftime 461s, 5.3 points. With `-O3 -flto`: 19s, 25s, 17s, 17s, total 78s, 5.9 points, significant. Further with `-O3 -flto -ljemalloc`: 17s, 24s, 15s, 16s, total 72s, 6.4 points, 20% over `-O3`. `-march=native` adds less than 1%.

#### 1. jpeg_place and 3. smithwaterman_place

Both perform placement, analyzed together. Similar hotspots:

- `get_non_updateable_bb(ClusterNetId net_id, t_bb* bb_coord_new)` from `src/vtr-vpr/vpr/src/place/place.cpp`: jpeg_place 13.98%, smithwaterman_place 18.26%, iterating pins to find bounding box (xmin/xmax/ymin/ymax) by reading x and y coordinates;
- `try_swap(...)` from `src/vtr-vpr/vpr/src/place/place.cpp`: jpeg_place 12.39%, smithwaterman_place 11.46%, selecting a block to move to an empty position or swap with another, evaluating cost;
- `physical_tile_type(ClusterBlockId blk)` from `src/vtr-vpr/vpr/src/util/vpr_utils.cpp`: jpeg_place 7.59%, smithwaterman_place 7.75%, indirect indexed memory access, reading coordinates from `block_loc`, then reading type from `grid`;
- `get_bb_from_scratch(ClusterNetId net_id, t_bb* coords, t_bb* num_on_edges)` from `src/vtr-vpr/vpr/src/place/place.cpp`: jpeg_place 6.73%, smithwaterman_place 2.78%, similar bounding box computation;
- `malloc/_int_malloc/cfree`: jpeg_place 3.94%, smithwaterman_place 4.29%.

With `-O3 -flto`, `physical_tile_type` gets inlined, saving frequent function call overhead. Given the memory allocation share, `-O3 -ljemalloc` improvement is expected.

Under `-O3`: jpeg_place executes 273.7B instructions (84.5B Loads, 26.9B Stores, 51.9B branches, 781.0M mispredictions, MPKI=2.85). smithwaterman_place: 245.0B instructions (76.4B Loads, 24.7B Stores, 45.4B branches, 661.9M mispredictions, MPKI=2.70). Some cmov instructions visible in bounding box min/max computation; on ISAs without cmov, MPKI could be even higher.

#### 2. jpeg_route and 4. smithwaterman_route

Routing hotspots differ:

- `ConnectionRouter<BinaryHeap>::evaluate_timing_driven_node_costs(...)`: jpeg_route 9.35%, smithwaterman_route 6.91%, computing cost with floating-point;
- `ConnectionRouter<BinaryHeap>::timing_driven_add_to_heap(...)`: jpeg_route 9.34%, smithwaterman_route 6.82%, computing cost then inserting into Binary Heap;
- `ConnectionRouter<BinaryHeap>::timing_driven_expand_neighbours(...)`: jpeg_route 8.14%, smithwaterman_route 4.00%, expanding neighbor nodes into heap;
- `ClassicLookahead::get_expected_delay_and_cong(...)`: jpeg_route 7.86%, smithwaterman_route 5.14%, delay and congestion estimation with floating-point;
- `BinaryHeap::get_heap_head()`: jpeg_route 3.14%, smithwaterman_route 1.64%, classic min binary heap with float comparison;
- `malloc/_int_malloc/cfree`: jpeg_route 2.90%, smithwaterman_route 4.19%.

Looks like cost computation with BinaryHeap selecting minimum cost for expansion, similar to search algorithms.

With `-O3 -flto`, `evaluate_timing_driven_node_costs` and `timing_driven_add_to_heap` are inlined into `timing_driven_expand_neighbours`. Given the allocation share, `-O3 -ljemalloc` improvement is expected.

Under `-O3`: jpeg_route executes 424.1B instructions (130.6B Loads, 50.6B Stores, 79.0B branches, 1094.2M mispredictions, MPKI=2.58). smithwaterman_route: 305.8B instructions (91.0B Loads, 36.0B Stores, 59.4B branches, 609.3M mispredictions, MPKI=1.99).

#### Summary

Results:

| Workload               | Compiler + Flags        | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | Mispred (M) | MPKI |
|------------------------|-------------------------|----------|----------|----------|-----------|----------|--------------|------|
| 1. jpeg_place          | GCC 14 `-O3`            | 21       | 273.7    | 84.5     | 26.9      | 51.9     | 781.0        | 2.85 |
| 1. jpeg_place          | GCC 14 `-O3 -flto`      | 19       | 247.0    | 69.2     | 22.2      | 47.8     | 774.2        | 3.13 |
| 1. jpeg_place          | GCC 14 `-O3 -ljemalloc` | 19       | 261.5    | 81.9     | 25.1      | 47.9     | 764.5        | 2.92 |
| 2. jpeg_route          | GCC 14 `-O3`            | 29       | 424.1    | 130.6    | 50.6      | 79.0     | 1094.2       | 2.58 |
| 2. jpeg_route          | GCC 14 `-O3 -flto`      | 26       | 356.6    | 103.2    | 33.5      | 66.3     | 1075.5       | 3.02 |
| 2. jpeg_route          | GCC 14 `-O3 -ljemalloc` | 28       | 411.5    | 127.9    | 48.8      | 74.9     | 1080.0       | 2.62 |
| 3. smithwaterman_place | GCC 14 `-O3`            | 18       | 245.0    | 76.4     | 24.7      | 45.4     | 661.9        | 2.70 |
| 3. smithwaterman_place | GCC 14 `-O3 -flto`      | 17       | 222.1    | 63.1     | 20.8      | 21.8     | 662.7        | 2.98 |
| 3. smithwaterman_place | GCC 14 `-O3 -ljemalloc` | 17       | 232.9    | 73.8     | 23.0      | 41.4     | 648.7        | 2.78 |
| 4. smithwaterman_route | GCC 14 `-O3`            | 19       | 305.8    | 91.0     | 36.0      | 59.4     | 609.3        | 1.99 |
| 4. smithwaterman_route | GCC 14 `-O3 -flto`      | 17       | 264.3    | 72.9     | 25.5      | 51.5     | 590.9        | 2.24 |
| 4. smithwaterman_route | GCC 14 `-O3 -ljemalloc` | 18       | 293.6    | 88.4     | 34.2      | 55.3     | 594.7        | 2.03 |

734.vpr_r splits into place (bounding box computation) and route (search and optimization). `-flto` and `-ljemalloc` provide significant gains via inlining hotspots and faster allocation. Overall 1254B instructions, 237B branches, MPKI = 2.51, in the upper-middle range.

### 735.gem5_r

gem5 is the well-known simulator; running SPEC CPU 2017 in GEM5 sustained many PhDs. Now the loop is complete: running SPEC INT 2026's GEM5 inside GEM5. Of course, 735.gem5_r's workload isn't SPEC CPU 2026 (no turtles all the way down), but RISC-V Linux kernel boot and memory access sequence generation. Four workloads:

```shell
# 1. o3
gem5sim --stats-file=run_riscv_boot.py_o3_10_--max-ticks_10_000_000_000_stats.stats.txt run_riscv_boot.py o3 10 --max-ticks 10_000_000_000
# 2. timing
gem5sim --stats-file=run_riscv_boot.py_timing_4_--max-ticks_20_000_000_000.stats.txt run_riscv_boot.py timing 4 --max-ticks 20_000_000_000
# 3. traffic_21
gem5sim --stats-file=synthetic_traffic.py_LinearGenerator_21.stats.txt synthetic_traffic.py LinearGenerator 21
# 4. traffic_74_ruby
gem5sim --stats-file=synthetic_traffic.py_LinearGenerator_74_--ruby.stats.txt synthetic_traffic.py LinearGenerator 74 --ruby
```

Runtimes: 16s, 21s, 21s, and 31s, total 89s, reftime 487s, 5.4 points. Optimization effects:

- `-O3 -flto`: 15s, 20s, 20s, 29s, total 84s, 5.8 points (+6%).
- `-O3 -flto -ljemalloc`: 14s, 18s, 16s, 26s, total 74s, 6.6 points (+20%).
- `-O3 -march=native -flto -ljemalloc`: 12s, 18s, 16s, 26s, total 72s, 6.8 points (+24%). Only the first workload benefits from `-march=native`.

Given these improvements, we can already guess what bottlenecks we'll find.

#### 1. o3

First workload simulates RISC-V Linux boot with O3 CPU. Hotspots:

- `malloc/_int_malloc/cfree/_int_free_chunk/operator new`: 4.78%+3.46%+3.29%+1.35%+1.16%=13.29%, an incredible ratio, but gem5 indeed allocates heavily (e.g., Packet objects);
- `gem5::TimeBuffer<*>::advance()` from `src/gem5/cpu/timebuf.hh`: 3.05%+2.43%+2.39%+2.28%+1.98%=12.13%, passing data between pipeline stages via rolling time windows, with main time in `rep stos` or SSE `movups` memory initialization, plus constructor/destructor with reference counting;
- `gem5::o3::IEW::tick()` from `src/gem5/cpu/o3/iew.cc`: 3.32%, Issue-Execute-Writeback timing simulation, bottleneck mainly `rep stos` for data initialization.

Many other scattered small functions. With `-O3 -flto`, hotspots become one large fused function at 20.80% (the `tick()` lambda). With `-O3 -flto -ljemalloc`, allocation drops to 4.67%. `-march=native` replaces `rep stos` with AVX2 memset, optimizing `TimeBuffer::advance()`.

Under `-O3`: 211.1B instructions, 69.9B Loads, 31.7B Stores, 43.2B branches, 175.5M mispredictions, MPKI = `175.5M/211.1B*1000=0.83`.

#### 2. timing

Second workload uses TimingSimpleCPU (much less complex than O3). Bottleneck shifts to RISC-V architecture code, cache simulation, and allocation:

- `cfree/malloc/operator new`: 12.03%;
- `gem5::RiscvISA::Decoder::decode(...)`: 8.97%, RISC-V instruction decode (partially auto-generated) with `std::map`-based decode cache;
- `gem5::BaseTags::findBlock(...)`: 5.19%, set-associative tag comparison;
- `gem5::PMAChecker::check(...)`: 4.86%, RISC-V PMA check;
- `gem5::RiscvISA::ISA::readMiscReg(...)`: 3.34%, CSR read;
- `gem5::BaseCache::access(...)`: 2.84%, cache access simulation;
- `gem5::PMP::pmpCheck(...)`: 2.66%, RISC-V PMP check.

With `-O3 -flto`, `readMiscReg` is inlined. With `-O3 -flto -ljemalloc`, allocation drops to 5.82%.

Under `-O3`: 333.9B instructions, 113.9B Loads, 57.8B Stores, 69.8B branches, 202.9M mispredictions, MPKI = `202.9M/333.9B*1000=0.61`.

#### 3. traffic_21

Hotspots:

- `cfree/malloc/operator new`: 13.47%;
- `gem5::SnoopFilter::lookupRequest(...)`: 5.93%, snoop filtering on bus using `std::map`;
- `gem5::AddrRange::removeIntlvBits(...)`: 3.39%, address interleaving bit removal, with bottleneck in `ctz64()` (GCC 14 generates loop, GCC 15 generates `rep bsfq`, with `-mbmi` generates `tzcnt`, [Godbolt](https://godbolt.org/z/PjxbhnqPK));
- `gem5::BaseTags::findBlock(...)`: 3.18%.

With `-O3 -flto`, `removeIntlvBits` disappears; with `-ljemalloc`, allocation drops to 5.47%.

Under `-O3`: 226.4B instructions, 65.5B Loads, 31.3B Stores, 50.8B branches, 749.3M mispredictions, MPKI = `749.3M/226.4B*1000=3.31`, noticeably higher.

#### 4. traffic_74_ruby

With ruby enabled, bottlenecks shift to `gem5::ruby` components:

- `cfree/malloc/operator new`: 10.22%;
- `gem5::ruby::Cache_Controller::processNextState(...)`: 4.44%, cache state machine;
- `gem5::ruby::NetDest::intersectionIsNotEmpty(...)`: 4.03%, bitset AND operations;
- `gem5::ruby::MessageBuffer::isReady(...)`: 3.94%, message queue;
- `gem5::ruby::Cache_Controller::getDirEntry(...)`: 3.80%, `std::map` lookup.

With `-O3 -flto`, `intersectionIsNotEmpty` inlined into `route` (6.45%). With `-ljemalloc`, allocation drops to 3.84%.

Under `-O3`: 391.5B instructions, 103.2B Loads, 54.4B Stores, 82.1B branches, 1246.0M mispredictions, MPKI = `1246.0M/391.5B*1000=3.18`, still high.

#### Summary

Results:

| Workload           | Compiler + Flags        | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | Mispred (M) | MPKI |
|--------------------|-------------------------|----------|----------|----------|-----------|----------|--------------|------|
| 1. o3              | GCC 14 `-O3`            | 16       | 211.1    | 69.9     | 31.7      | 43.2     | 175.5        | 0.83 |
| 1. o3              | GCC 14 `-O3 -ljemalloc` | 15       | 189.5    | 65.0     | 28.0      | 37.0     | 204.8        | 1.08 |
| 1. o3              | GCC 14 `-O3 -flto`      | 15       | 193.8    | 65.0     | 27.4      | 39.6     | 163.5        | 0.84 |
| 2. timing          | GCC 14 `-O3`            | 21       | 333.9    | 113.9    | 57.8      | 69.8     | 202.9        | 0.61 |
| 2. timing          | GCC 14 `-O3 -ljemalloc` | 19       | 301.8    | 106.9    | 51.8      | 60.5     | 202.9        | 0.67 |
| 2. timing          | GCC 14 `-O3 -flto`      | 21       | 324.4    | 111.6    | 56.2      | 67.0     | 194.7        | 0.60 |
| 3. traffic_21      | GCC 14 `-O3`            | 21       | 226.4    | 65.5     | 31.3      | 50.8     | 749.3        | 3.31 |
| 3. traffic_21      | GCC 14 `-O3 -ljemalloc` | 18       | 198.0    | 59.2     | 26.1      | 42.7     | 723.3        | 3.65 |
| 3. traffic_21      | GCC 14 `-O3 -flto`      | 20       | 216.1    | 62.8     | 29.2      | 48.1     | 745.4        | 3.45 |
| 4. traffic_74_ruby | GCC 14 `-O3`            | 31       | 391.5    | 103.2    | 54.4      | 82.1     | 1246.0       | 3.18 |
| 4. traffic_74_ruby | GCC 14 `-O3 -ljemalloc` | 28       | 363.6    | 97.1     | 49.5      | 74.1     | 1200.3       | 3.30 |
| 4. traffic_74_ruby | GCC 14 `-O3 -flto`      | 29       | 361.3    | 96.7     | 48.6      | 75.5     | 1204.0       | 3.33 |

735.gem5_r's four tests exercise very different code paths. Due to gem5's high modularity, `-flto` helps inline functions that could benefit from it. Additionally, gem5 heavily allocates dynamic objects (e.g., Packets), making `-ljemalloc` effective. `-march=native` has limited applicability.

Overall: 1164B instructions, 246B branches, MPKI = 2.05, not high, mainly contributed by the two traffic workloads.

### 750.sealcrypto_r

sealcrypto performs homomorphic encryption, with one workload:

```shell
sealcrypto_r refrate ecuador_province_capitals_refrate.csv Galapagos
```

Runtime 108s, reftime 536s, 5.0 points.

Oddly, `-O3 -flto` regresses; `-O3 -flto -ljemalloc` has no effect; `-O3 -march=native -flto -ljemalloc` regresses further. But LLVM 22 dominates with nearly 2x performance, only 50.5s, 10.6 points. It's essentially 750.sealcrypto_r alone that lets LLVM 22 surpass GCC 14 overall on SPEC INT 2026. Let's see why.

First, GCC 14 `-O3` hotspot analysis:

- `seal::util::DWTHandler::transform_to_rev(...)` from `src/seal/util/dwthandler.h`: 25.65%, DWT (Discrete Wavelet Transform), instruction-level: lots of imul/add/shr/shl;
- `seal::util::DWTHandler::transform_from_rev(...)` from `src/seal/util/DWTHandler.h`: 16.58%, inverse DWT, same computation pattern;
- `seal::util::multiply_uint64_generic(T operand1, S operand2, unsigned long long *result128)` from `src/seal/util/uintarith.h`: 11.60%, 64-bit * 64-bit = 128-bit multiplication via arithmetic and bit operations;
- `seal::util::dot_product_mod(...)` from `src/seal/util/uintarithsmallmod.cpp`: 11.48%, dot product with modular reduction using `multiply_accumulate_uint64` and `barrett_reduce_128`;
- `seal::util::dyadic_product_coeffmod(...)` from `src/seal/util/polyarithsmallmod.cpp`: 9.08%, element-wise modular multiplication;
- `seal::util::BaseConverter::fast_convert_array(...)` from `src/seal/util/rns.cpp`: 5.88%, RNS (Residue Number System) conversion;
- `seal::util::RNSTool::sm_mrq(...)` from `src/seal/util/rns.cpp`: 5.40%.

Being cryptography, there's massive integer computation with multiplication and bit operations in prime fields. 3113.4B instructions, 385.7B Loads, 161.3B Stores, 78.5B branches, 450.0M mispredictions, MPKI = `450.0M/3113.4B*1000=0.14`, the lowest overall, even below 714.cpython_r. IPC is the highest at 5.09. Top-down: 80.7% Retiring, 13.5% Backend Bound, meaning the processor is running at nearly full throughput.

With `-O3 -march=native`, AVX2 instructions appear, but the sequences are complex with heavy data shuffling (vpunpcklqdq/vpunpckhqdq/vpermq/vpblendvb/vperm2i128), see [Godbolt](https://godbolt.org/z/z3oEs4hnd). Instructions drop to 2757.7B but IPC drops more, resulting in regression from 108s to 116s. The original `-O3` version processes one element at a time but with higher ILP, compensating via IPC. GCC 16's `-march=native` is much better, with fewer shuffles, mostly vpaddq/vpsubq/vpmuludq/vpsllq/vpsrlq compute instructions, see [Godbolt](https://godbolt.org/z/Pqrhj9ebE).

What did LLVM 22 do? Instructions plummet to 1213.6B (302.8B Loads, 109.2B Stores, 57.2B branches, 1093.9M mispredictions, MPKI=0.90). Taking `DWTHandler::transform_to_rev` as example: seal implements 64*64=128 multiplication generically in `multiply_uint64_generic` and inlines it; GCC 14 faithfully implements the algorithm with many instructions ([Godbolt](https://godbolt.org/z/KKTa1aMP8)); but AMD64's mul instruction already does 64*64=128, so LLVM 22 recognizes the pattern and compiles to mul ([Godbolt](https://godbolt.org/z/bc6xPjEMc), with BMI2 even [mulx](https://www.felixcloutier.com/x86/mulx)). Such 64-bit multiply-high instructions exist across ISAs: ARM64's umulh, RISC-V's mulhu, LoongArch's mulh.du. Of course, seal's source already handles this with __int128 when [supported](https://github.com/microsoft/SEAL/blob/e3476fad1d5bb5e5222c51a551b5a4d7e2cb4f91/native/src/seal/util/gcc.h#L44). Similar to 706.stockfish_r's 1to6_classical. However, SPEC CPU 2026's compiler neutrality removes such compiler/ISA-dependent code, falling back to the most generic implementation. Only compiler recognition and optimization remains.

This somewhat fails to reflect real-world optimization, since many applications have co-evolved with ISA extensions/compiler extensions, even writing intrinsics (e.g., original stockfish has [optimizations](https://github.com/official-stockfish/Stockfish/blob/77a8f6ccf31846d63452f79e143fbc6dc62ae3a8/src/nnue/layers/affine_transform.h#L201) for AVX512/AVX2/SSSE3/NEON_DOTPROD/LASX/LSX). Compilers then implement passes to recognize generic fallback code and map back to efficient implementations. Similar to the well-known "compiler recognizes popcount loop and emits popcnt instruction" example; programs often use `__builtin_popcount` directly. C++20's std::popcount partially addresses this, but came too late.

In contrast, Geekbench is more open to ISA extension optimization (e.g., AMX/SME's dramatic score impact), though this earns it the "AppleBench" moniker.

Meanwhile, LLVM 22 generates significantly more mispredictions. Via `perf record -e branch-misses:pp`, 46.81% come from `sm_mrq`, specifically the inlined `multiply_uint_mod` from `src/seal/util/uintarithsmallmod.h`, which has a final step: if result >= p, subtract p: `SEAL_COND_SELECT(tmp2 >= p, tmp2 - p, tmp2)` (familiar from Montgomery Multiplication; Barrett Reduction here, same principle). The `SEAL_COND_SELECT` macro (with `SEAL_AVOID_BRANCHING` undefined, using the ternary operator):

```c
#ifndef SEAL_AVOID_BRANCHING
#define SEAL_COND_SELECT(cond, if_true, if_false) (cond ? if_true : if_false)
#else
#define SEAL_COND_SELECT(cond, if_true, if_false) \
    ((if_false) ^ ((~static_cast<uint64_t>(cond) + 1) & ((if_true) ^ (if_false))))
#endif
```

LLVM 22 uses a branch:

```asm
# Initialize rax = 0
mov $0x0,%eax
# Compare tmp2(rcx) with p(r10)
cmp %r10,%rcx
# If p > tmp2, jump to label:
jb label
# rax = r10, i.e., rax = p
mov %r10,%rax
label:
# Compute tmp2 - rax
sub %rax,%rcx
```

Less computation but high branch misprediction rate, unless hardware implements Short Forward Branch to Predication (see [Brief Introduction to OoO CPUs (Part 3: Frontend)](../hardware/brief-into-ooo-3.md)). GCC 14's approach:

```asm
# tmp2 in rax, p in rdx
# rcx = rax, i.e., rcx = tmp2
mov %rax,%rcx
# rcx -= rdx, i.e., rcx = tmp2 - p
sub %rdx,%rcx
# Compare tmp2 and p
cmp %rdx,%rax
# If tmp2 >= p, rax = rcx = tmp2 - p; otherwise rax keeps original tmp2
cmovae %rcx,%rax
```

GCC 14 avoids massive mispredictions via cmov. This difference alone creates LLVM 22's much higher MPKI. If LLVM 22 used cmov here, performance could improve further. LLVM 22 does use cmov in many places, but why it ultimately chose not to in this specific case requires further investigation.

LLVM 22 with `-O3 -march=native` improves mispredictions from 1093.9M to 612.7M (MPKI=0.54). The improvement isn't in `sm_mrq` (still uses branch, not cmov) but in `DWTHandler::transform_from_rev` and `RNSTool::fastbconv_sk`. These functions also have `SEAL_COND_SELECT`, but now `cond ? if_true : if_false` compiles to `vpcmpgtq` + `vblendvpd`, a vectorized cmov equivalent. LLVM 22 refuses cmov for scalar but implements it for vectorization.

750.sealcrypto_r under different compilers and flags:

| Compiler + Flags            | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | Mispred (M) | MPKI |
|-----------------------------|----------|----------|----------|-----------|----------|--------------|------|
| GCC 14 `-O3`                | 108      | 3113.4   | 385.7    | 161.3     | 78.5     | 450.0        | 0.14 |
| GCC 14 `-O3 -march=native`  | 116      | 2757.7   | 370.0    | 126.7     | 76.1     | 431.0        | 0.16 |
| GCC 15 `-O3`                | 106.4    | 3071.3   | 379.1    | 161.4     | 80.0     | 416.1        | 0.14 |
| GCC 15 `-O3 -march=native`  | 117.7    | 2701.9   | 379.4    | 130.6     | 77.6     | 406.9        | 0.15 |
| GCC 16 `-O3`                | 105.9    | 3020.1   | 381.1    | 158.5     | 80.7     | 430.3        | 0.14 |
| GCC 16 `-O3 -march=native`  | 99.3     | 2492.3   | 328.0    | 123.2     | 81.8     | 433.3        | 0.17 |
| LLVM 22 `-O3`               | 50.5     | 1213.6   | 302.8    | 109.2     | 57.2     | 1093.9       | 0.90 |
| LLVM 22 `-O3 -march=native` | 48.2     | 1126.0   | 299.2    | 108.7     | 53.4     | 612.7        | 0.54 |

### 753.ns3_r

753.ns3_r is similar to 710.omnetpp_r, also a network discrete event simulator. Workloads:

```shell
# 1. mobile
ns3_r mobile-scenario --simTimeMinutes=3 --RngSeed=1 --RngRun=1
# 2. tcp
ns3_r tcp-pacing --simulationEndTime=500 --useEcn=false --RngSeed=1 --RngRun=1
# 3. lena
ns3_r lena-radio-link-failure --numberOfEnbs=2 --interSiteDistance=800 --simTime=200 --RngSeed=1 --RngRun=1
# 4. dctcp
ns3_r dctcp-example --enableSwitchEcn=true --flowStartupWindow=0.4 --convergenceTime=0.4 --measurementWindow=0.4 --RngSeed=1 --RngRun=1
# 5. wifi_mixed
ns3_r wifi-mixed-network --isUdp=0 --payloadSize=3072 --simulationTime=25 --RngSeed=1 --RngRun=1
# 6. wifi_eht
ns3_r wifi-eht-network --simulationTime=0.2 --frequency=5 --useRts=1 --minExpectedThroughput=6 --maxExpectedThroughput=547 --RngSeed=1 --RngRun=1
```

Runtimes: 18s, 15s, 3s, 19s, 23s, and 14s, total 92s, reftime 613s, 6.7 points. Optimization effects:

- `-O3 -flto`: 16s, 14s, 3s, 17s, 19s, 13s, total 82s, 7.5 points (+12%);
- `-O3 -flto -ljemalloc`: 14s, 12s, 3s, 13s, 18s, 11s, total 71s, 8.6 points (+15% over `-flto`).

Massive improvements; only `-march=native` has minimal impact (0.5%).

#### 1. mobile

Hotspots:

- `cfree/malloc/_int_malloc/_int_free_chunk/operator new`: 6.99%+5.66%+4.15%+1.83%+1.81%=20.44%, allocation-intensive;
- `ns3::LteMiErrorModel::GetTbDecodificationStats(...)`: 9.57%, floating-point accumulation and binary search;
- `ns3::LteMiErrorModel::Mib(...)`: 4.39%, floating-point computation;
- `ns3::LteMiErrorModel::MappingMiBler(...)`: 3.53%, floating-point, erf function calls, table lookups;
- `ns3::MapScheduler::Insert(const Event& ev)`: 2.66%, `std::map` red-black tree insertion.

Allocation-intensive. With `-O3 -flto`, `Mib` inlined into `GetTbDecodificationStats`. With `-ljemalloc`, allocation drops to 8.01%.

Unusually for SPEC INT 2026, mobile involves significant floating-point and libm calls (erf/atan2/pow/log), half-stepping into SPEC FP territory but pulled back by heavy libc calls.

Under `-O3`: 257.2B instructions, 66.6B Loads, 35.4B Stores, 54.4B branches, 631.1M mispredictions, MPKI = `631.1M/257.2B*1000=2.45`. Mispredictions mainly from allocator and `std::map` insertion.

#### 2. tcp

Hotspots:

- `cfree/malloc/_int_malloc/_int_free_chunk/operator new`: 19.75%;
- `ns3::TcpTxBuffer::NextSeg(...)`: 4.35%, TCP stack implementing RFC 6675 SACK;
- `ns3::MapScheduler::Insert(...)`: 4.05%;
- `__do_dyncast/__dynamic_cast`: 3.35%.

Under `-O3`: 204.8B instructions, 63.5B Loads, 41.4B Stores, 45.4B branches, 148.1M mispredictions, MPKI = `148.1M/204.8B*1000=0.72`.

#### 3. lena

Hotspots: allocation 20.64%, `MapScheduler::Insert` 2.41%, dynamic_cast 2.55%.

Under `-O3`: 46.6B instructions, 14.2B Loads, 9.6B Stores, 10.4B branches, 53.4M mispredictions, MPKI = `53.4M/46.6B*1000=1.15`.

#### 4. dctcp

Hotspots: allocation 40.61%, `MapScheduler::Insert` 6.94%.

Under `-O3`: 225.3B instructions, 71.1B Loads, 43.9B Stores, 52.3B branches, 295.8M mispredictions, MPKI = `295.8M/225.3B*1000=1.31`.

#### 5. wifi_mixed

Same pattern: allocation + `TcpTxBuffer::NextSeg`. Under `-O3`: 291.8B instructions, 88.8B Loads, 52.7B Stores, 66.5B branches, 201.9M mispredictions, MPKI = `201.9M/291.8B*1000=0.69`.

#### 6. wifi_eht

Hotspots include `InterferenceHelper::AppendEvent` and `WifiSpectrumValueHelper::GetBandPowerW`. Under `-O3`: 194.3B instructions, 58.1B Loads, 32.6B Stores, 44.0B branches, 372.0M mispredictions, MPKI = `372.0M/194.3B*1000=1.91`. Mispredictions mainly from `std::map` queries inlined in `InterferenceHelper::AppendEvent`.

#### Summary

Results:

| Workload      | Compiler + Flags | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | Mispred (M) | MPKI |
|---------------|------------------|----------|----------|----------|-----------|----------|--------------|------|
| 1. mobile     | GCC 14 `-O3`    | 18       | 257.2    | 66.6     | 35.4      | 54.4     | 631.1        | 2.45 |
| 2. tcp        | GCC 14 `-O3`    | 15       | 204.8    | 63.5     | 41.4      | 45.4     | 148.1        | 0.72 |
| 3. lena       | GCC 14 `-O3`    | 3        | 46.6     | 14.2     | 9.6       | 10.4     | 53.4         | 1.15 |
| 4. dctcp      | GCC 14 `-O3`    | 19       | 225.3    | 71.1     | 43.9      | 52.3     | 295.8        | 1.31 |
| 5. wifi_mixed | GCC 14 `-O3`    | 23       | 291.8    | 88.8     | 52.7      | 66.5     | 201.9        | 0.69 |
| 6. wifi_eht   | GCC 14 `-O3`    | 14       | 194.3    | 58.1     | 32.6      | 44.0     | 372.0        | 1.91 |

Similar to 727.cppcheck_r, 753.ns3_r is essentially a memory allocator benchmark, with much time in malloc/free, plus std::map and libm calls. Under `-O3`: 1221B instructions, 273B branches, MPKI = 1.39.

### 777.zstd_r

The sole compression algorithm in SPEC INT 2026, replacing SPEC INT 2017's 557.xz_r, reflecting compression algorithm evolution. Eight workloads compressing the same file with different compression levels:

```shell
# 1. b3
zstd -b3 -e3 --verbose -i40 cld.tar
# 2. b5
zstd -b5 -e5 --verbose -i25 cld.tar
# 3. b7
zstd -b7 -e7 --verbose -i12 cld.tar
# 4. b10
zstd -b10 -e10 --verbose -i6 cld.tar
# 5. b14
zstd -b14 -e14 --verbose -i4 cld.tar
# 6. b16
zstd -b16 -e16 --verbose -i1 cld.tar
# 7. b18
zstd -b18 -e18 --verbose -i1 cld.tar
# 8. b19
zstd -b19 -e19 --verbose -i1 cld.tar
```

Here `-b` is compression level lower bound, `-e` is upper bound (both equal = test one level). Runtimes: 11.0s, 14.5s, 13.0s, 11.6s, 24.5s, 10.9s, 20.1s, 25.5s, total 131.2s, reftime 644s, 4.9 points.

`-O3 -flto` or `-O3 -ljemalloc` have no improvement, but `-O3 -march=native` gives a nice 6% boost (total 124.0s, 5.2 points).

Taking b3 as example, hotspots:

- `ZSTD_compressBlock_doubleFast_noDict_generic` from `src/zstd-1.5.6/lib/compress/zstd_double_fast.c`: 56.82%, hashing data and finding matches for compression;
- `ZSTD_decompressBlock_internal.part.0` from `src/zstd-1.5.6/lib/decompress/zstd_decompress_block.c`: 16.63%, decompression logic;
- `ZSTD_encodeSequences` from `src/zstd-1.5.6/lib/compress/zstd_compress_sequences.c`: 10.91%, bmi2 version disabled by SPEC, using generic version.

Under `-O3`, b3: 181.4B instructions, 49.9B Loads, 17.7B Stores, 19.1B branches, 543.9M mispredictions, MPKI = `543.9M/181.4B*1000=3.00`. 78.98% mispredictions from `ZSTD_compressBlock_doubleFast_noDict_generic` (e.g., `if (MEM_read64(matchl0) == MEM_read64(ip))`).

b5 hotspots: `ZSTD_RowFindBestMatch` 67.91%, `ZSTD_compressBlock_lazy_generic` 9.12%. Under `-O3`: 273.6B instructions, MPKI = 2.06.

b14 hotspots: `ZSTD_DUBT_findBestMatch` 85.74%. Under `-O3`: 197.6B instructions, MPKI = `1609.6M/197.6B*1000=8.15`, extremely high.

b16 hotspots: `ZSTD_insertBtAndGetAllMatches` 38.62%, `ZSTD_insertBt1` 35.15%. Under `-O3`: 129.1B instructions, MPKI = 5.05.

b7/b10 are similar to b5; b18/b19 are similar to b16. zstd uses different paths based on compression level, trading compression ratio for speed.

With `-march=native`: BMI instructions (bzhi, tzcnt) and three-operand non-flag-affecting operations (shrx) reduce instruction counts, similar to corresponding RISC-V instructions. Results before and after:

| Workload | Compiler + Flags           | Time (s) | Insns (B) | Load (B) | Store (B) | Branch (B) | Mispred (M) | MPKI |
|----------|----------------------------|----------|----------|----------|-----------|----------|--------------|------|
| 1. b3    | GCC 14 `-O3`               | 11.0     | 181.4    | 49.9     | 17.7      | 19.1     | 543.9        | 3.00 |
| 1. b3    | GCC 14 `-O3 -march=native` | 10.5     | 170.4    | 49.9     | 18.3      | 18.9     | 543.8        | 3.19 |
| 2. b5    | GCC 14 `-O3`               | 14.5     | 273.6    | 61.3     | 35.1      | 28.4     | 562.4        | 2.06 |
| 2. b5    | GCC 14 `-O3 -march=native` | 14.0     | 250.5    | 59.7     | 35.4      | 28.3     | 559.1        | 2.23 |
| 3. b7    | GCC 14 `-O3`               | 13.0     | 228.5    | 48.9     | 25.8      | 29.8     | 599.3        | 2.62 |
| 3. b7    | GCC 14 `-O3 -march=native` | 12.7     | 207.4    | 46.6     | 26.0      | 29.8     | 596.7        | 2.88 |
| 4. b10   | GCC 14 `-O3`               | 11.6     | 207.2    | 41.5     | 17.6      | 32.6     | 516.3        | 2.49 |
| 4. b10   | GCC 14 `-O3 -march=native` | 11.5     | 184.0    | 37.8     | 17.8      | 32.6     | 569.6        | 3.10 |
| 5. b14   | GCC 14 `-O3`               | 24.5     | 197.6    | 48.8     | 16.5      | 29.1     | 1609.6       | 8.15 |
| 5. b14   | GCC 14 `-O3 -march=native` | 23.7     | 190.1    | 46.7     | 15.9      | 27.8     | 1612.5       | 8.48 |
| 6. b16   | GCC 14 `-O3`               | 10.9     | 129.1    | 29.9     | 11.2      | 18.0     | 652.1        | 5.05 |
| 6. b16   | GCC 14 `-O3 -march=native` | 10.2     | 124.7    | 30.7     | 12.0      | 17.3     | 646.5        | 5.18 |
| 7. b18   | GCC 14 `-O3`               | 20.1     | 265.8    | 57.0     | 17.0      | 32.6     | 987.7        | 3.72 |
| 7. b18   | GCC 14 `-O3 -march=native` | 18.4     | 259.2    | 57.0     | 17.2      | 31.4     | 980.7        | 3.78 |
| 8. b19   | GCC 14 `-O3`               | 25.5     | 342.0    | 72.9     | 19.1      | 41.8     | 1060.6       | 3.10 |
| 8. b19   | GCC 14 `-O3 -march=native` | 23.4     | 332.8    | 72.7     | 19.1      | 40.1     | 1050.2       | 3.16 |

Overall under `-O3`: 1827B instructions, 232B branches, MPKI = 3.58, third-highest after 729.abc_r and 723.llvm_r.

## Discussion

### Compiler Flags Comparison

Compilation flags significantly impact SPEC INT 2026 Rate performance:

- `-flto` helps 707.ntest_r, 710.omnetpp_r, 714.cpython_r, 734.vpr_r, 735.gem5_r, 753.ns3_r. When hotspots are spread across many small functions, LTO essentially recovers performance lost to file-splitting for readability;
- `-ljemalloc` helps 710.omnetpp_r, 721.gcc_r, 723.llvm_r, 727.cppcheck_r, 734.vpr_r, 735.gem5_r, 753.ns3_r. These programs do too much dynamic allocation, some benchmarks are essentially allocator benchmarks, where replacing glibc with jemalloc/mimalloc provides nice improvement (latest glibc is also improving malloc, unclear how much);
- `-march=native` helps 706.stockfish_r, 707.ntest_r, 735.gem5_r, 777.zstd_r. Partially SIMD (for ARM64, e.g., Apple M2, it's the USDOT instruction giving 706.stockfish_r +33%; without i8mm extension, `-march=native` has no effect), partially bit manipulation instructions (popcnt, BMI). Many real-world programs already account for hardware acceleration, often using intrinsics directly, but SPEC disables these, falling back to generic versions that depend heavily on `-march=native` and compiler pattern recognition.

Other common flags like `-static`, `-fomit-frame-pointer`, `-Ofast`, `-ffast-math` haven't been extensively tested yet.

### Compiler Version Comparison

The primary compiler is GCC 14.2.0 (Debian Trixie's version). Interestingly, even in 2026, with hardware unchanged, software performance continues growing with compiler updates. GCC 15 generates faster SSE/AVX sequences for 706.stockfish_r; LLVM 22 recognizes 750.sealcrypto_r's 64-bit multiplication pattern. Additionally, LLVM defaults to inlining popcount's optimized implementation while GCC calls libgcc's popcount; the former bloats code, the latter adds call overhead. These specific optimizations can be cross-ported. In SPEC INT 2017 era, GCC dominated LLVM; now LLVM gains ground via 750.sealcrypto_r, then gets overtaken again by GCC 15/16. As SPEC CPU 2026 research deepens, faster programs will be compiled.

### Branch Prediction

SPEC INT 2026 Rate benchmarks with high MPKI:

- 723.llvm_r MPKI=5.98
- 729.abc_r MPKI=3.87
- 777.zstd_r MPKI=3.58
- 721.gcc_r MPKI=3.37
- 734.vpr_r MPKI=2.52
- 707.ntest_r MPKI=2.27
- 735.gem5_r MPKI=2.05

For comparison, SPEC INT 2017 Rate:

- 505.mcf_r MPKI=14.39
- 541.leela_r MPKI=12.62
- 557.xz_r MPKI=5.29
- 531.deepsjeng_r MPKI=4.40
- 520.omnetpp_r MPKI=4.33
- 502.gcc_r MPKI=3.13

SPEC INT 2026 Rate is significantly lower overall. Of course, these are per-benchmark averages; individual workloads may be higher. But regardless, no more battling 505.mcf_r's `spec_qsort` and 541.leela_r's `if(randint(2) == 0)`. That said, SPEC INT 2026 Rate still has many MPKI contributions from `std::map` red-black trees and other data structures with data-dependent branches, not necessarily easy to optimize in hardware. Applications are becoming aware of branch prediction, using ternary operators to hint compilers to generate cmov instructions.

### Limitations

Current testing is limited to Intel i9-14900K P-Core; similar analysis is needed on ARM64/RISC-V/LoongArch. Different ISAs likely lead to different conclusions. Additionally, analysis focuses on perf-reported hotspot functions; finer-grained analysis (instruction type distributions, POPCNT/BMI/AVX usage) would be valuable.

Only Rate 1 (single copy) was tested. Multi-copy runs would stress memory bandwidth and cache contention more, potentially changing MPKI, IPC, etc. significantly. Analysis focuses on instruction-level and branch prediction, lacking microarchitecture-level deep analysis (L1/L2/LLC miss rates, TLB misses) more directly useful for processor designers. Power data wasn't considered; energy efficiency ratio needs RAPL measurement. Finally, PGO (`-fprofile-generate` / `-fprofile-use`) wasn't attempted and could potentially bring nice improvements.

## Conclusion

This article provides in-depth analysis of SPEC CPU 2026 INT Rate workloads, for reference by compiler and processor designers. From the compiler perspective, combining the best of GCC and LLVM can further improve performance; from the processor perspective, optimizing for program bottlenecks can further improve scores.
