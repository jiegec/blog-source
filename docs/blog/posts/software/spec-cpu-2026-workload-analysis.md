---
layout: post
date: 2026-05-21
tags: [benchmark,spec]
draft: true
categories:
    - software
---

# SPEC CPU 2026 负载特性分析

## 背景

最近用 SPEC CPU 2026 跑了一些测试，打算结合[测试结果](../../../benchmark/spec-cpu-2026-rate.md)做一些深入的负载特性分析。

<!-- more -->

本文测试环境：CPU 为 Intel i9-14900K P-Core @ 6.0 GHz，Linux 发行版为 Debian Trixie，编译器是 GCC 14.2.0。

推荐阅读：[Evaluating SPEC CPU2026](https://chipsandcheese.com/p/evaluating-spec-cpu2026)

## SPEC INT 2026 Rate

### 706.stockfish_r

测试会用如下三种参数分别运行：

```shell
# 1. 1to6_classical
stockfish bench 1600 1 26 spec_ref_pos_1to6.fen depth classical
# 2. 1to6_nnue
stockfish bench 1600 1 26 spec_ref_pos_1to6.fen depth nnue
# 3. 7to11_nnue
stockfish bench 1600 1 26 spec_ref_pos_7to11.fen depth nnue
```

实测数据显示，三条命令耗费的时间分别是 46s、73s 和 68s，共计 187s。reftime 是 1260s，对应 6.7 分。开启 `-march=native` 后，1to6_classical 时间缩短 10% 到 41s，而 1to6_nnue 和 7to11_nnue 时间缩短明显，时间直接砍半，整体下来分数提升约 60%。下面分别分析这三条命令的具体性能特性。

#### 1to6_classical

通过 `perf` 观察性能瓶颈，运行第一个命令 1to6_classical 时，这几个函数耗费的时间占比较多：

- `Stockfish::TranspositionTable::probe(const Key key, bool& found)` 来自 `src/tt.cpp`: 21.49%，主要的瓶颈来自于随机访存，在 `first_entry(key)` 当中有 `&table[mul_hi64(key, clusterCount)].entry[0]`，其中 mul_hi64 计算两个 64 位整数乘法结果的高 64 位，因此访存地址是根据参数计算得出
- `Stockfish::Eval::evaluate(const Position& pos)` 来自 `src/evaluate.cpp`: 18.15%，inline 了 `Evaluation<NO_TRACE>(pos).value()` 的调用，里面主要是对局面的评估，涉及比较多零散的访存和计算
- `Stockfish::MovePicker::next_move(bool skipQuiets)` 来自 `src/movepick.cpp`: 9.79%，里面比较慢的是 `partial_insertion_sort`
- `Stockfish::search(Position& pos, Stack* ss, Value alpha, Value beta, Depth depth, bool cutNode)` 来自 `src/search.cpp`: 9.08%，主要的搜索逻辑
- `__popcountdi2`: 7.19%，被 `Stockfish::Eval::evaluate(const Position& pos)` 调用，用来判断局面上满足某种条件

开了 `-march=native` 后，能观察到 `__popcountdi2` 被内联为 `popcnt` 指令。经过测试，开了 `-mpopcnt` 后，时间即从 46s 降低到 42s，接近 `-march=native` 的性能，可见在开启 popcnt 指令集的前提下，内联 `__popcountdi2` 调用就可以明显减少时间。

#### 1to6_nnue

后两个命令的引擎从 classical 变为了 nnue，涉及神经网络，因此它的计算模式会不太一样。通过 `perf` 观察到 1to6_nnue 的主要耗时函数：

- `Stockfish::Eval::NNUE:evaluate(const Position& pos, bool adjusted)` 来自 `src/nnue/evaluate_nnue.cpp`：80.26%，主要耗时在 `affine_transform_non_ssse3` 的 `weights[offset + j] * input[j]`，即神经网络的推理过程，它的计算过程是，进行 int8_t 乘 uint8_t，再累加到 int32_t 类型的结果，默认编译选项下，只能用最基础的 SSE 指令，而不能用 AVX
- `Stockfish::TranspositionTable::probe(const Key key, bool& found)` 来自 `src/tt.cpp`: 仅 5.27%，瓶颈和前面分析的一样是随机访存

由此可见，nnue 在开了 `-march=native` 的情况下应当有明显的性能提升，实际测试也证明了这一点，开了 `-march=native` 后，时间从 73s 降低到 30s，`Stockfish::Eval::NNUE::evaluate` 时间占比降到 53.84%，主要的计算指令变为 [vpdpbusd (Multiply and Add Unsigned and Signed Bytes)](https://www.felixcloutier.com/x86/vpdpbusd)，即针对字节（weight 数组元素是 int8_t 类型，input 数组元素是 uint8_t 类型）元素的整数乘加融合指令，和的类型是 int32_t。核心循环如下：

```asm
1:
vmovdpa (%r8,%rcx,1),%ymm0
{vex} vpdpbusd (%rdx,%rcx,1),%ymm0,%ymm2
add $0x20,%rcx
cmp $0x400,%rcx
jne 1b
```

需要注意的是，单纯开 `-mavx2` 还是需要执行 70s，即使用了 AVX，由于没有开 AVX-VNNI，不能用 vpdpbusd，还是需要先进行格式转换再用 32 位的整数乘加指令。可以说，Stockfish 的 NNUE 这样的计算方式，就是奔着 vpdpbusd 这条指令去的。所以一些没有这种计算的 ISA，就会比较吃亏。

例如在 ARM64 下，对应的 [USMMLA (Unsigned and signed 8-bit integer matrix multiply-accumulate to 32-bit integer (vector))](https://developer.arm.com/documentation/ddi0487/maa/-Part-C-The-AArch64-Instruction-Set/-Chapter-C7-A64-Advanced-SIMD-and-Floating-point-Instruction-Descriptions/-C7-2-Alphabetical-list-of-A64-Advanced-SIMD-and-floating-point-instructions/-C7-2-452-USMMLA--vector-) 指令被包括在 i8mm 扩展当中，有这个扩展的话，`-march=native` 性能提升显著，例如 Apple M2；而如果没有这个扩展，开不开 `-march=native` 就没什么区别，例如 Apple M1。

#### 7to11_nnue

7to11_nnue 的行为与 1to6_nnue 类似，瓶颈也是在 `Stockfish::Eval::NNUE:evaluate` 函数上。开启 `-march=native` 后，时间从 68s 降到了 30s。

#### 小结

1to6_classical 比较像传统的各种棋类引擎，有一些比较复杂的分支和访存性能，当然它的 MPKI 不算高，只有 1.84，低于 SPEC INT 2017 的 deepsjeng，可能是因为它的计算和访存过程更加复杂。


## SPEC FP 2026 Rate

TODO
