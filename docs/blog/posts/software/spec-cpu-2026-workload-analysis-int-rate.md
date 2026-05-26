---
layout: post
date: 2026-05-22
tags: [benchmark,spec]
categories:
    - software
---

# SPEC CPU 2026 负载特性分析（INT Rate 篇）

## 背景

最近用 SPEC CPU 2026 跑了一些测试，打算结合[测试结果](../../../benchmark/spec-cpu-2026-rate.md)做一些深入的负载特性分析。本篇主要是分析 SPEC INT 2026 Rate 的负载特性，后续再更新 SPEC FP 2026 Rate。

<!-- more -->

本文测试环境：CPU 为 Intel i9-14900K P-Core @ 5.7 GHz，Linux 发行版为 Debian Trixie，编译器是 GCC 14.2.0，默认编译选项是 `-O3`。其实这款 CPU 最快能 Boost 到 6.0 GHz，但是时不时因为未知原因（防缩缸？）在只有单核负载的情况下也 Boost 不上去，现象是每跑一段时间负载，CPU 核心就会强制降频到 4.7 GHz，故退而求其次，选择在更容易稳定达到的 5.7 GHz 频率来跑，因为能跑 6.0 GHz 的就是那一个物理 P 核，其他的物理 P 核都能上 5.7 GHz，降频了只要换一个就好。6.0 GHz 下的性能可以参考之前的测试结果：[INT](../../../benchmark/data-trixie/int2026_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt) 和 [FP](../../../benchmark/data-trixie/fp2026_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt)，基本上，从 5.7 GHz 到 6.0 GHz，性能可以按频率线性放缩。本文所用的脚本已开源到 [jiegec/spec2026](https://github.com/jiegec/spec2026)。

推荐阅读：[Evaluating SPEC CPU2026](https://chipsandcheese.com/p/evaluating-spec-cpu2026) 和 [SPEC CPU2026: Characterization, Representativeness, and Cross-Suite Comparison](https://arxiv.org/abs/2605.03713v2)

## SPEC INT 2026 Rate 分析

### 706.stockfish_r

stockfish 是一个著名的国际象棋引擎，测试会用如下三种参数分别运行：

```shell
# 1. 1to6_classical
stockfish bench 1600 1 26 spec_ref_pos_1to6.fen depth classical
# 2. 1to6_nnue
stockfish bench 1600 1 26 spec_ref_pos_1to6.fen depth nnue
# 3. 7to11_nnue
stockfish bench 1600 1 26 spec_ref_pos_7to11.fen depth nnue
```

实测数据显示，三条命令耗费的时间分别是 47s、77s 和 72s，共计 196s。reftime 是 1260s，对应 6.4 分。开启 `-march=native` 后，1to6_classical 时间缩短 10% 到 43s，而 1to6_nnue 和 7to11_nnue 时间明显缩短到 32s 和 31s，总时间 105s，对应 12 分，分数提升显著。下面逐一分析这三条命令的性能特性。

#### 1. 1to6_classical

通过 `perf` 观察性能瓶颈，运行第一个命令 1to6_classical 时，这几个函数耗费的时间占比较多，百分比代表这个函数执行时间的占比，后续都用这个方法表示：

- `Stockfish::Eval::evaluate(const Position& pos)` 来自 `src/evaluate.cpp`: 19.16%，inline 了 `Evaluation<NO_TRACE>(pos).value()` 的调用，里面主要是对局面的评估，涉及比较多零散的访存和计算，没有特别集中的热点指令；
- `Stockfish::TranspositionTable::probe(const Key key, bool& found)` 来自 `src/tt.cpp`: 17.91%，主要的瓶颈来自于随机访存，在 `first_entry(key)` 当中有 `&table[mul_hi64(key, clusterCount)].entry[0]` 的代码，其中 `mul_hi64` 计算两个 64 位整数乘法结果的高 64 位，因此访存地址是根据参数计算得出；对于 `mul_hi64`，GCC 14 会忠实地按照源码把 64 位拆分成高低 32 位分别计算，而 LLVM 22 能够正确识别出这段代码的意图，并直接用 AMD64 的 mul 指令实现；事实上，Stockfish 原本的代码里会用 __int128，此时 GCC 14 也能生成高效的代码，只可惜因为用到了 C 语法扩展，被 SPEC 禁用了（汇编对比见 [Godbolt](https://godbolt.org/z/x3j89xqWP)）；
- `Stockfish::MovePicker::next_move(bool skipQuiets)` 来自 `src/movepick.cpp`: 10.36%，里面比较慢的是 `partial_insertion_sort`，找到插入位置后，还要把原来数组里靠后的元素往后挪，留出空间用于插入元素；
- `Stockfish::search(Position& pos, Stack* ss, Value alpha, Value beta, Depth depth, bool cutNode)` 来自 `src/search.cpp`: 9.49%，搜索逻辑主要在这里实现；
- `__popcountdi2`: 7.52%，被 `Stockfish::Eval::evaluate(const Position& pos)` 调用，用来判断局面上满足某种条件，内部实现就是位运算，有兴趣的读者可以阅读 Hacker's Delight 这本书。

开了 `-march=native` 后，能观察到 `__popcountdi2` 被内联为 `popcnt` 指令。经过测试，开了 `-mpopcnt` 后，时间即从 47s 降低到 44s，接近 `-march=native` 的性能，可见在开启 popcnt 指令集的前提下，内联 `__popcountdi2` 调用就可以明显减少时间。

`-O3` 编译选项下，1to6_classical 执行的指令数为 531.8B（`instructions` 性能计数器），其中 Load 指令有 135.7B 条（`mem_inst_retired.all_loads` 性能计数器），Store 有 59.7B 条（`mem_inst_retired.all_stores` 性能计数器），分支指令有 56.0B 条（`branch-instructions` 性能计数器），其中有 2.6B 次错误预测（`branch-misses` 性能计数器）。可见，1to6_classical 的 MPKI 还是比较高的：`2.6B/532.9B*1000=4.88`，即使是在 SPEC INT 2017 当中，也是比较高的，高于 531.deepsjeng_r 的 3.16 和 557.xz_r 的 3.49，低于 505.mcf_r 的 6.24 和 541.leela_r 的 7.71。

使用 `perf record -e branch-misses:pp`，观察到主要的分支错误预测来自于 `Stockfish::MovePicker::next_move()` 函数，贡献了 27.48% 的错误预测，主要是插入排序的部分，一是循环找到插入的位置，二是循环搬运数组内原有元素。其次是 `Stockfish::Eval::evalute()` 函数，贡献了 17.42% 的错误预测。再其次是 `Stockfish::search()` 函数，贡献了 13.06% 的错误预测。

开 `-O3 -mpopcnt` 后，指令数减少到 453.9B，其中 Load 有 124.2B 条，Store 有 53.1B 条，分支指令有 46.1B 条，错误预测还是 2.6B 次，所以光是内联了 `__popcountdi2` 的调用，就可以少掉 77.9B，原来的约 15% 的指令。`__popcountdi2` 本身的实现包括 21 条指令，此外还有 `__popcountdi2@plt` 里的一次 jmp，和 `call __popcountdi2@plt` 本身和前后保存和恢复寄存器的开销。

#### 2. 1to6_nnue

后两个命令的引擎从 classical 变为了 nnue，涉及神经网络，因此它的计算模式会不太一样。通过 `perf` 观察到 1to6_nnue 的主要耗时函数：

- `Stockfish::Eval::NNUE:evaluate(const Position& pos, bool adjusted)` 来自 `src/nnue/evaluate_nnue.cpp`：80.59%，主要耗时在 `affine_transform_non_ssse3` 的 `sum += weights[offset + j] * input[j]`，即神经网络的推理过程，它的计算过程是，进行 int8_t 乘 uint8_t，再累加到 int32_t 类型的结果，默认编译选项下，只能用基础的 SSE 指令如 pmaddwd/paddd，而不能用 AVX；
- `Stockfish::TranspositionTable::probe(const Key key, bool& found)` 来自 `src/tt.cpp`: 仅 4.81%，瓶颈和前面分析的一样是随机访存。

分析 `Stockfish::Eval::NNUE:evaluate` 的指令，可以看到，它为了实现上述逻辑，核心思路是采用 pmaddwd 指令，进行 4 次 16 位有符号的乘法计算，累加到 32 位的结果。但是，在这之前，需要先把输入的 8 位有符号 weights 和无符号 input 转换到 16 位有符号数。其中 8 位有符号 weights 转换比较简单，而 8 位无符号 input 的处理逻辑比较复杂。首先，它对 input 的每个元素加上 128，然后当成有符号数来看待，这相当于对每个元素减去了 128，把 uint8_t 映射到了 int8_t。这样，input 就可以用和 weights 相同的方法进行符号扩展。但是，这样会导致结果计算错误，为了纠正这个偏差，又减去了 128 倍的 weights 之和。汇编代码如下（[Godbolt](https://godbolt.org/z/ox7q63Er8)）：

```asm
1:
# 加载有符号 weights 的 16 个元素
movdqu (%rdx,%rcx,1),%xmm2
movdqa %xmm5,%xmm8
# 加载无符号 input 的 16 个元素
movdqa (%r12,%rcx,1),%xmm10
add $0x10,%rcx
# 对 weights 进行符号扩展
pcmpgtb %xmm2,%xmm8
movdqa %xmm2,%xmm9
# 每个 input 元素加上 128，即减去 128 转为有符号 int8_t
paddb %xmm6, %xmm10
# 符号扩展 weights
punpckhbw %xmm8,%xmm2
punpcklbw %xmm8,%xmm9
movdqa %xmm2,%xmm11
movdqa %xmm9,%xmm8
# 计算 weights 之和乘以 128
pmaddwd %xmm3,%xmm11
pmaddwd %xmm7,%xmm8
paddd %xmm11,%xmm0
paddd %xmm8,%xmm0
paddd %xmm11,%xmm0
movdqa %xmm5,%xmm11
# 对 input 进行符号扩展
pcmpgtb %xmm10,%xmm11
paddd %xmm8,%xmm0
movdqa %xmm10,%xmm8
punpckhbw %xmm11,%xmm10
punpcklbw %xmm11,%xmm8
# 计算 weights * input
pmaddwd %xmm10,%xmm2
pmaddwd %xmm8,%xmm9
# 结果累加
paddd %xmm2,%xmm0
paddd %xmm9,%xmm0
cmp $0x400,%rcx
jne 1b
```

经验告诉我们，对于这种适合 SIMD 的代码，在开了 `-march=native` 的情况下应当有明显的性能提升，实际测试也证明了这一点，开了 `-march=native` 后，时间从 77s 降低到 32s，`Stockfish::Eval::NNUE::evaluate` 时间占比降到 54.20%，此时主要的计算指令变为 [vpdpbusd (Multiply and Add Unsigned and Signed Bytes)](https://www.felixcloutier.com/x86/vpdpbusd)，即针对字节（weights 数组元素是 int8_t 类型，input 数组元素是 uint8_t 类型）元素的整数乘加融合指令，和的类型是 int32_t。核心循环如下（[Godbolt](https://godbolt.org/z/zoeqc4zch)）：

```asm
1:
# 加载无符号 input
vmovdpa (%r8,%rcx,1),%ymm0
# 加载有符号 weights 并计算 sum += weights[offset + j] * input[j]
{vex} vpdpbusd (%rdx,%rcx,1),%ymm0,%ymm2
add $0x20,%rcx
cmp $0x400,%rcx
jne 1b
```

需要注意的是，单纯开 `-mavx2` 仅能把时间从 77s 减少到 50s，距离 `-march=native` 的 32s 还有明显的差距，即使开启了 AVX（[Godbolt](https://godbolt.org/z/e9dPsqddh)），由于没有开 AVX-VNNI，不能用 vpdpbusd，还是需要先格式转换到 16 位，再用 32 位累加器的 16 位整数乘加指令。Stockfish 的 NNUE 这样的计算方式，就是奔着 vpdpbusd 这条指令去的。所以一些没有这种指令的 CPU，或者有但是编译器没用上，就会比较吃亏。

例如在 ARM64 下，对应的 [USDOT (Dot product with unsigned and signed integers (vector))](https://developer.arm.com/documentation/ddi0487/maa/-Part-C-The-AArch64-Instruction-Set/-Chapter-C7-A64-Advanced-SIMD-and-Floating-point-Instruction-Descriptions/-C7-2-Alphabetical-list-of-A64-Advanced-SIMD-and-floating-point-instructions/-C7-2-448-USDOT--vector-) 指令被包括在 i8mm 扩展当中，有这个扩展的话，`-march=native` 性能提升显著（[Godbolt](https://godbolt.org/z/MxY3YYTYo)），例如 Apple M2；而如果没有这个扩展，开不开 `-march=native` 就没什么区别，例如 Apple M1，此时就要回退到类似 AMD64 那样，先扩展到 16 位，再求和（[Godbolt](https://godbolt.org/z/TfdvW4f75)）。RISC-V Vector 指令集扩展则有 vwmulsu.vv 指令可以使用，得到 16 位乘法结果之后，再用 vwadd.wv 指令累加到 32 位（[Godbolt](https://godbolt.org/z/ha5oEb4hE)）。LoongArch 也有对应的 xvmulwev.h.b/xvmulwod.h.b 指令，得到 16 位乘法结果之后，用 xvhaddw.w.h 指令累加到 32 位（[Godbolt](https://godbolt.org/z/xxr5rovxW)）。

除了是否开启对应指令集扩展以外，还观察到 GCC 15 在 1to6_nnue 上相比 GCC 14 有明显的性能提升（编译选项为 `-O3`），时间从 77s 降低到了 49s。观察生成的指令，虽然它还是用的 SSE 指令，但指令序列更简洁（[Godbolt](https://godbolt.org/z/exKaP5jKb)）：

```asm
# %xmm5 初始化为全零
1:
# 加载有符号 weights 的 16 个元素
movdqu (%rdx,%rcx,1),%xmm4
movdqa %xmm5,%xmm8
# 加载无符号 input 的 16 个元素
movdqa (%r12,%rcx,1),%xmm2
add $0x10,%rcx
# 将 weights 和零比较，非负得 0，负数得 0xFF
pcmpgtb %xmm4,%xmm8
movdqa %xmm2,%xmm6
movdqa %xmm4,%xmm7
# 把 input 从 8 位无符号扩展到 16 位，保存到 %xmm2 和 %xmm6
punpckhbw %xmm5,%xmm2
punpcklbw %xmm5,%xmm6
# 结合前面的 pcmpgtb，把 weights 从 8 位有符号扩展到 16 位，保存到 %xmm4 和 %xmm7
punpckhbw %xmm8,%xmm4
punpcklbw %xmm8,%xmm7
# 每条 pmaddwd 指令进行 4 次 16-bit * 16-bit + 16-bit * 16-bit = 32-bit 的计算
# 两条 pmaddwd 共完成 8 次 16-bit 乘法和 8 次 32-bit 加法
pmaddwd %xmm4,%xmm2
pmaddwd %xmm7,%xmm6
# 每条 paddd 指令进行 4 次 32 bit 的累加
paddd %xmm2,%xmm0
paddd %xmm6,%xmm0
cmp $0x400,%rcx
jne 1b
```

可见，即使没有对口的 vpdpbusd 指令，仅用 SSE 还是有优化空间的，GCC 15 通过用 SSE 实现高效的有符号和无符号符号扩展，获得了介于 GCC 14 比较差的指令序列与专用 vpdpbusd 指令的性能。这在 [SPEC CPU2026: Characterization, Representativeness, and Cross-Suite Comparison](https://arxiv.org/abs/2605.03713v2) 论文中也有提及：`For example, gcc-15 reduces the instruction count of 706.stockfish_r by up to 3x`，不过这个数字是相比 GCC 13 的；相比 GCC 14 也有减少，不过没有那么明显，详情见论文中的 Figure 10 和 Figure 16，这里实测下来是从 GCC 14 的 1342B 条指令降低到 GCC 15 的 1015B。相比之下，LLVM 22 生成的 SSE（`-O3`，[Godbolt](https://godbolt.org/z/Tsd1YhrWe)）或 AVX（`-O3 -march=alderlake`，[Godbolt](https://godbolt.org/z/WM1xWjqc3)）指令都没有 GCC 15 高效。

`-O3` 编译选项下，1to6_nnue 执行的指令数为 1342.1B，其中 Load 指令有 182.2B 条，Store 指令有 61.8B 条，128 位整数向量指令（如 SSE）有 229.1B 条（`int_vec_retired.128bit` 性能计数器），分支指令有 77.6B 条，其中有 1.6B 次错误预测。它的 MPKI 只有 `1.6B/1342B*1000=1.19`，主要瓶颈还是在上述的神经网络推理当中。

GCC 15 用 `-O3` 编译选项下，1to6_nnue 执行的指令数减少到 1015.3B，其中 Load 指令有 175.0B 条，Store 指令有 57.8B 条，128 位整数向量指令只有 97.0B 条，分支指令有 77.4B 条，优化效果明显。

GCC 14 用 `-march=native` 编译选项下，1to6_nnue 执行的指令数锐减到 446.8B，只剩下三分之一的指令数了，其中 Load 指令有 119.6B 条，Store 指令有 44.4B 条，分支指令有 48.7B 条，256 位的 AVX VNNI 指令有 13.2B 条（`int_vec_retired.vnni_256` 性能计数器），优化效果明显。

#### 3. 7to11_nnue

7to11_nnue 的行为与 1to6_nnue 类似，瓶颈也是在 `Stockfish::Eval::NNUE:evaluate` 函数上。开启 `-march=native` 后，时间从 72s 降到了 31s。GCC 15 的性能提升也和 1to6_nnue 类似，从 72s 降低到 46s。

`-O3` 编译选项下，7to11_nnue 执行的指令数为 1253.2B，其中 Load 指令有 176.1B 条，Store 指令有 61.6B 条，128 位整数向量指令有 212.5B 条，分支指令有 75.4B 条，其中有 1.5B 次错误预测。它的 MPKI 只有 `1.5B/1253B*1000=1.20`，主要瓶颈还是在神经网络推理当中。

GCC 15 用 `-O3` 编译选项下，7to11_nnue 执行的指令数减少到 955.3B，其中 Load 指令有 169.4B 条，Store 指令有 57.8B 条，128 位整数向量指令只有 92.3B 条，分支指令有 75.2B 条，优化效果明显。

GCC 14 用 `-march=native` 编译选项下，7to11_nnue 执行的指令数锐减到 425.9B，只剩下三分之一的指令数了，其中 Load 指令有 115.1B 条，Store 指令有 43.7B 条，分支指令有 47.1B 条，256 位的 AVX VNNI 指令有 12.0B 条，优化效果明显。

#### 小结

| 子测试         | 编译器+选项            | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) |
|----------------|------------------------|----------|----------|----------|-----------|----------|
| 1to6_classical | GCC 14 `-O3`           | 47       | 531.8    | 135.7    | 59.7      | 56.0     |
| 1to6_classical | GCC 14 `-O3 -mpopcnt`  | 44       | 453.9    | 124.2    | 53.1      | 46.1     |
| 1to6_nnue      | GCC 14 `-O3`           | 77       | 1342.1   | 182.2    | 61.8      | 77.6     |
| 1to6_nnue      | GCC 15 `-O3`           | 49       | 1015.3   | 175.0    | 57.8      | 77.4     |
| 1to6_nnue      | GCC 14 `-march=native` | 32       | 446.8    | 119.6    | 44.4      | 48.7     |
| 7to11_nnue     | GCC 14 `-O3`           | 72       | 1253.2   | 176.1    | 61.6      | 75.4     |
| 7to11_nnue     | GCC 15 `-O3`           | 46       | 955.3    | 169.4    | 57.8      | 75.2     |
| 7to11_nnue     | GCC 14 `-march=native` | 31       | 425.9    | 115.1    | 43.7      | 47.1     |

1to6_classical 比较像传统的各种棋类引擎，有比较复杂的分支和访存，所以它的 MPKI=4.88 比较类似 SPEC CPU 2017 的 531.deepsjeng_r（MPKI=3.16），属于比较高的一类。而 1to6_nnue 和 7to11_nnue 的主要瓶颈在于 i8 的矩阵运算，能否用上硬件的加速指令（这里是 AVX-VNNI）对性能影响很大，分支预测瓶颈就明显小了。整体平均下来的 MPKI 是 1.85，并不算高。

### 707.ntest_r

ntest 是黑白棋的引擎，测试会用如下参数运行：

```shell
ntest_r Othello.154.ggf 20 16
```

实测数据显示，运行这条命令耗费的时间是 140s。reftime 是 592s，对应 4.2 分。开启各项优化编译选项，`-O3 -flto` 相比 `-O3` 能带来 4% 的性能提升，进一步 `-O3 -flto -march=native` 相比 `-O3 -flto` 还能带来 10% 的性能提升。下面分析它的具体负载特性。通过 `perf` 观察性能瓶颈，这几个函数耗费的时间占比较多：

- `flips(int sq, u64 mover, u64 enemy)` 来自 `src/flips.cpp`：34.80%，最主要的开销，根据棋盘状态，经过一系列的访存和位运算，判断下子以后是否出现翻转（黑白棋的规则是，只有翻转了对方的棋子才能下子，不然就要轮空），主要是一些数据依赖的访存，混合了一堆位运算；
- `solveNParity(int alpha, int beta, u64 mover, u64 enemy, u64 parity, EndgameSearch* search, bool hasPassed)` 来自 `src/solve.cpp`：14.21%，进行 alpha-beta 减枝的 minimax 算法，遍历棋盘上的空位置，首先找到那些满足 good parity 的位置（用 `bitSet()` 函数，汇编上是用 AMD64 的 `bt` 指令判断），调用上述 `flips()` 看看是否会出现翻转，如果会出现翻转就尝试下子并进行递归，之后再遍历一次，这次遍历 bad parity 的位置，流程相同，主要的瓶颈在访存以及依赖访存结果的分支；
- `__popcountdi2`：9.65%，因为没开 `-mpopcnt/-march=native`，故需要它来代替 popcnt 指令，用来计算场面上各颜色棋子的数量等等；
- `solveNFlipParity`：8.95%，与 solveNParity 配合完成 minimax 算法；
- `solve2`：5.38%，minimax 算法的一部分，处理棋盘只有两个空位的最终局面，此时判断最终胜败是比较容易的。

这也是个比较典型的棋类引擎的模式了，整个 minimax 算法占了 70%+ 的时间，为了搜索局面，有大量的位运算和访存，还有根据访存结果决定方向的分支。果不其然，执行 2688.3B 条指令，其中有 647.8B 条 Load 指令，255.2B 条 Store 指令，228.2B 条是分支指令，有 6.1B 次错误预测，MPKI 达到了 `6.1B/2688B*1000=2.27`。通过 `perf record -e branch-misses:pp`，看到 `solveNParity` 和 `solveNFlipParity` 一起贡献了 60.37% 的错误预测，主要就是上面说的，循环内对 good 还是 bad parity 的判断，以及链表插入时是否为 NULL 的判断，都是方向依赖数据的分支。

和 706.stockfish_r 类似，它也有不少的 popcnt 调用，那么打开 `-mpopcnt` 就会得到不错的性能提升：时间从 140s 降低到 126s，减少 11% 时间，指令数减少到 2286.9B，其中有 586.9B 条 Load 指令，206.7B 条 Store 指令，187.6B 条分支指令。而即使开 `-march=native`，性能也只是进一步降到 122s，只有少量的地方用到了 AVX2。

另一方面，LLVM 22 的性能在 707.ntest_r 上比 GCC 14 要快：同样是 `-O3` 的编译选项，运行时间从 GCC 14 的 140s 降低到 126s。深入研究汇编发现，LLVM 22 在没有开 `-mpopcnt` 的时候，它的行为是，直接把类似 libgcc 的 `__popcountdi2` 的代码内联到了程序当中，省去了 call libgcc 的开销，不过代价就是代码体积会增加，实际执行了 2416.9B 条指令，其中有 542.7B 条 Load 指令，202.9B 条 Store 指令，168.2B 条分支指令。类似地，706.stockfish_r 的 1to6_classical 也是 LLVM 22 比 GCC 14 快，从 47s 降低到 44s。

同时，GCC 15 相比 GCC 14 也有性能提升，运行时间从 140s 降低到了 130s。分析汇编，发现主要优化点在 `flips(int sq, u64 mover, u64 enemy)` 函数当中。性能区别有两点：

1. 首先是对 callee-saved 寄存器的使用，GCC 14 会在 epilogue/prologue 直接进行一系列的 push/pop，而 GCC 15 更加聪明，仅在 `if (neighbors[sq]&enemy)` 条件成立的情况下，需要执行复杂函数体，需要 callee-saved 寄存器时才会进行 push/pop，否则就直接 ret，因为检查条件的时候并没有用到 callee-saved 寄存器，避免了保存和恢复。
2. 自己编译的 GCC 15 默认是 -no-pie 模式，而发行版的 GCC 14 默认是 -pie，而 -no-pie 模式因为采用绝对地址，可以在 imul 等指令的操作数直接访问内存，节省寄存器，于是 callee-saved register 就都可以不用了，开启 -static 也能带来类似的效果。上面的第一条分析是手动给 GCC 15 开 -pie 后观察到的。不过主要的性能提升还是来自于减少 push/pop 的执行次数。

GCC 15 编译的 707.ntest_r，实际执行 2429.3B 条指令，其中有 610.9B 的 Load 指令，206.2B 的 Store 指令，224.7B 的分支指令。

| 子测试 | 编译器+选项           | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) |
|--------|-----------------------|----------|----------|----------|-----------|----------|
| ntest  | GCC 14 `-O3`          | 140      | 2688.3   | 647.8    | 255.2     | 228.2    |
| ntest  | GCC 14 `-O3 -mpopcnt` | 126      | 2286.9   | 586.9    | 206.7     | 187.6    |
| ntest  | LLVM 22 `-O3`         | 126      | 2416.9   | 542.7    | 202.9     | 168.2    |
| ntest  | GCC 15 `-O3`          | 130      | 2429.3   | 610.9    | 206.2     | 224.7    |

结合 706.stockfish_r 和 707.ntest_r，可以看到，popcnt 还是比较常用的，但可惜 AMD64 的基线并不提供这条指令，因此如果开了 x86-64-v2 或以上的编译优化选项，这类应用就可以获得性能提升，免去了 libgcc 的 __popcountdi2 开销，本来一条指令就能完成的事情，因为额外的 call 以及 PLT 开销，带来了可观的性能开销。期待一个优雅的解决方法。相比 AVX-VNNI，popcnt 的普及程度就要大得多了。

### 708.sqlite_r

sqlite 就是大名鼎鼎的数据库了，不必多介绍。测试中，又是包括三条命令：

```shell
# 1. main
sqlite_r --memdb --size 2000 --testset main --verify
# 2. cte
sqlite_r --memdb --size 2000 --testset cte --verify
# 3. fp
sqlite_r --memdb --size 1000 --testset fp --verify
```

实测数据显示，三条命令耗费的时间分别是 69s、12s 和 25s，共计 106s。reftime 是 528s，对应 5.0 分。开启 -flto/-ljemalloc 对性能影响很小，-march=native 甚至带来了负优化。下面逐一分析这三条命令的性能特性。

#### 1. main

通过 `perf` 观察性能瓶颈，这几个函数耗费的时间占比较多：

- `sqlite3BtreeMovetoUnpacked(BtCursor *pCur, UnpackedRecord *pIdxKey, i64 intKey, int biasRight, int *pRes)` 来自 `src/sqlite3.c`：24.66%，在 Btree 上进行搜索，根据 key，查找对应的 entry，中间一个比较耗时的部分是逐字节扫描 pCell 指向的内存，此外还会经常调用 `sqlite3GetVarint` 获取 pCell 保存的变长 int 来实现二分搜索；
- `sqlite3VdbeExec(Vdbe *p)` 来自 `src/sqlite3.c`：22.36%，用 Loop+Switch 实现的执行字节码的虚拟机，执行编译好的 SQL 语句，VDBE 是 SQLite 的执行引擎，全称是 Virtual Database Engine，模拟过程会维护一个 `pc`，从 `aOp` 数组里扫描字节码，每个字节码是一个 `struct VdbeOp` 结构体，根据它的 `opcode` 字段进行一个大的 switch-case，一共有 176 种不同的 Op；gcc 把这个巨大的 switch-case 编译成了跳转表，也就是把各个 case 的地址保存到一个数组当中，根据 `opcode` 计算出对应 case 的地址，再 `jmp *%rax` 过去，执行完 case 的代码后，再跳回 switch 开头，读取下一个 opcode，再跳转；目前有一些解释器会直接用 C 的扩展，用 computed goto label 的写法来帮助编译器做这个优化，或者更进一步直接在每个 case 的最后跳转到下一个 `opcode` 对应的 case，拓展阅读： [Android Runtime 解释器的实现探究](./android-runtime-interpreter.md)；
- `pcache1Fetch(sqlite3_pcache *p, unsigned int iKey, int createFlag)` 来自 `src/sqlite3.c`：8.26%，对应一个用哈希表维护的 Page Cache，用于在内存里缓存硬盘上的数据，主要瓶颈在 `pcache1FetchNoMutex` 里的 `pPage = pCache->apHash[iKey % pCache->nHash]; while( pPage && pPage->iKey!=iKey ){ pPage = pPage->pNext; }`，对哈希表的桶里的链表做一个扫描，随机访存比较多；
- `sqlite3GetVarint(const unsigned char *p, u64 *v)` 来自 `src/sqlite3.c`：3.70%，恢复内存中可变长度的整数，比如 `[0,127]` 范围的数字用一个字节保存，`[128,16383]` 范围的数字用两个字节保存，更大的数字则要更长，最多到九个字节，这种压缩表示还挺常见的，多数时候可以节省空间。

都是一些比较经典的数据结构和算法的应用，Btree，Loop+Switch 的解释执行，加哈希表查询。一段 Vdbe 指令序列的例子如下：

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

能看到它的实现方式是，扫描 test 表的每一行，读取 key 列，如果不等于 1，则直接进入下一行；如果等于 1，则把所有列读出来，加入到结果当中。

这个测例的主要瓶颈在内存上。执行了 896.3B 条指令，其中 252.4B 是 Load 指令，105.1B 是 Store 指令，178.0B 是分支指令，错误预测了 1.5B 次，MPKI 是 `1.5B/897.6B*1000=1.67`。

#### 2. cte

通过 `perf` 观察性能瓶颈，这几个函数耗费的时间占比较多：

- `sqlite3VdbeExec(Vdbe *p)` 来自 `src/sqlite3.c`：41.15%，主要时间花费在查询的执行，因为这个 cte 测例，其计算过程比较复杂，用 SQL 实现了数独（递归和非递归版本）、Mandelbrot，还测试了 EXCEPT SELECT 语法；
- `sqlite3VdbeRecordCompareWithSkip(int nKey1, const void *pKey1, UnpackedRecord *pPKey2, int bSkip)` 来自 `src/sqlite3.c`：7.37%，比较表里的两个行，会调用 `sqlite3VdbeSerialGet` 获取行内的数据，再根据数据类型进行对应的比较；
- `sqlite3VdbeSerialGet(const unsigned char *buf, u32 serial_type, Mem *pMem)` 来自 `src/sqlite3.c`：5.95%，反序列化，根据内存中保存的数据类型，解析对应的数据，比如整数或者浮点，它的 switch-case 也被 GCC 编译成了跳转表；
- `vdbeSorterSort(SortSubtask *pTask, SorterList *pList)` 来自 `src/sqlite3.c`：5.95%，实现归并排序，主要时间是在通过函数指针调用比较器函数，以及根据比较结果进行归并。

瓶颈主要在解释器上，和 CPython 这类解释型语言的解释器的行为模式类似。执行了 306.0B 条指令，其中 82.8B 是 Load 指令，39.6B 是 Store 指令，62.6B 是分支指令，错误预测了 40.9M 次，MPKI 是 `40.9M/30602B*1000=0.13`，处于很低的水平。

#### 3. fp

通过 `perf` 观察性能瓶颈，这几个函数耗费的时间占比较多：

- `sqlite3VdbeExec(Vdbe *p)` 来自 `src/sqlite3.c`：30.66%，主要时间花费在查询的执行，因为这个 fp 测例，其计算过程引入了不少浮点运算；
- `sqlite3AtoF(const char *z, double *pResult, int length, u8 enc)` 来自 `src/sqlite3.c`：19.18%，实现从字符串到浮点数的转换，因为 SQL 内有很多浮点字面量；
- `vdbeSorterSort(SortSubtask *pTask, SorterList *pList)` 来自 `src/sqlite3.c`：10.44%，描述见上；
- `sqlite3VdbeRecordCompareWithSkip(int nKey1, const void *pKey1, UnpackedRecord *pPKey2, int bSkip)` 来自 `src/sqlite3.c`：6.76%，描述见上。

瓶颈主要在解释器上，不过因为 SQL 语句的设计，有很多时间花在字符串转浮点数上。执行了 554.7B 条指令，其中 132.3B 是 Load 指令，61.3B 是 Store 指令，111.5B 是分支指令，错误预测了 392.6M 次，MPKI 是 `392.6M/554.7B*1000=0.71`。

#### 小结

| 子测试 | 编译器+选项  | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | MPKI |
|--------|--------------|----------|----------|----------|-----------|----------|------|
| main   | GCC 14 `-O3` | 69       | 896.3    | 252.4    | 105.1     | 178.0    | 1.67 |
| cte    | GCC 14 `-O3` | 12       | 306.0    | 82.8     | 39.6      | 62.6     | 0.13 |
| fp     | GCC 14 `-O3` | 25       | 554.7    | 132.3    | 61.3      | 111.5    | 0.71 |

通过上面的分析，可见 sqlite_r 确实是比较难优化的那一类，大量访存、计算和分支混合在一起，对内存子系统的负担比较重，难以向量化，开 `-march=native` 后运行时间从 106s 增加到 112s，产生了负优化。整体来看，执行了 1760B 条指令，其中有 353B 条是分支指令，MPKI 仅有 1.08，主要由 main 贡献。

### 710.omnetpp_r

SPEC INT 2017 就有的老面孔 520.omnetpp_r，不过跑的内容还是不太一样。520.omnetpp_r 做的是 10 Gbps 网络的模拟，而 710.omnetpp_r 有足足十项测试，负载的多样性有了明显的增强。十项测试的命令行参数如下：

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

实测数据显示，十条命令耗费的时间分别是 24.6s、7.8s、3.8s、4.6s、9.1s、3.7s、2.6s、9.4s、6.6s 和 14.0s，共计 86.2s。reftime 是 486s，对应 5.6 分。

#### 1. randomMesh

首先分析第一条命令的热点函数：

- `omnetpp::cTopology::calculateUnweightedSingleShortestPathsTo(Node *_target)` 来自 `src/simulator/sim/ctopology.c`：16.22%，实现了经典的单源最短路算法，且由于每条边的权重都是一，约等于 BFS，主要瓶颈来自于随机访存和计算距离的双精度浮点运算；
- `__do_dyncast` 和 `__dynamic_cast` 来自 libstdc++.so：4.73%+3.24%+2.22%+0.81%=11.0%，代码中有一些 dynamic_cast 的使用，如 `Routing::handleMessage`；
- `Routing::handleMessage(cMessage *msg)` 来自 `src/model/Routing.cc`：7.10%，模拟路由表的功能，主要逻辑是内联了一个 `std::map<int, int>` 的 `find` 操作（[Godbolt](https://godbolt.org/z/ne6oEb9Md)），在一个红黑树上进行查询，读取结点，比较 key，走左子树或右子树继续查询；
- `cEvent::shouldPrecede(const cEvent *other)` 来自 `src/simulator/sim/cevent.cc`：4.64%，一个 cEvent 结构体的多关键字比较函数。

整体来看，它的瓶颈分散在比较多的地方。执行了 306.4B 条指令，其中有 98.7B 条 Load 指令，50.2B 条 Store 指令，62.1B 条分支指令，错误预测 661.2M 次，MPKI 为 `661.2M/306.4B*1000=2.16`。开 `-O3 -flto` 后，指令数减少到 284.6B，其中有 91.3B 条 Load 指令，45.4B 条 Store 指令，55.7B 条分支指令。进一步开 `-O3 -flto -ljemalloc`，指令数进一步减少到 279.8B，其中有 90.3B 条 Load 指令，44.4B 条 Store 指令，54.3B 条分支指令。

| 编译器+选项                   | 指令 (B) | Load (B) | Store (B) | 分支 (B) |
|-------------------------------|----------|----------|-----------|----------|
| GCC 14 `-O3`                  | 306.4    | 98.7     | 50.2      | 62.1     |
| GCC 14 `-O3 -flto`            | 284.6    | 91.3     | 45.4      | 55.7     |
| GCC 14 `-O3 -flto -ljemalloc` | 279.8    | 90.3     | 44.4      | 54.3     |

#### 其余的 2-10 共 9 条 queuenet 命令

用 `perf` 观察，其余 9 条 queuenet 命令的瓶颈主要集中在这些函数：

- strcmp（`__strcmp_avx2`）
- dynamic_cast（`__do_dyncast` 和 `__dynamic_cast`）
- malloc、free 和 operator new
- printf（`__printf_buffer`）

还有些 omnetpp 自己的函数（如 `omnetpp::common::StringPool::obtain(const char *s)`，主要是对 `std::unordered_map<const char *,int,str_hash, str_eq> pool` 进行查询和修改操作），散落各处，每个函数都只占用不到 5% 的时间。对于这么大比例使用 libc/libstdc++ 中函数的情况，标准库和内存分配器的实现就很重要了。

#### 小结

针对上面的分析，尝试不同的编译选项：

- 开 `-O3 -ljemalloc` 后，十条命令的性能都有了一定的提升，总时间从 86.2s 降低到 80.6s，分数从 5.6 分提升到 6.0 分。
- 开 `-O3 -flto` 也能带来不错的提升，总时间从 86.2s 降低到 76.1s，分数从 5.6 分提升到 6.4 分。
- 开 `-O3 -flto -ljemalloc`，则总时间从 86.2s 降低到 69.7s，分数从 5.6 分提升到 7.0 分。

类似的现象在 SPEC INT 2017 已经出现了，`-O3 -flto` 比 `-O3` 快 3%，`-O3 -flto -ljemalloc` 比 `-O3 -flto` 快 20%。

`-O3` 下，执行的指令数是 1447B，其中 291B 是分支指令，MPKI 是 0.78。虽然 randomMesh 因为图计算，MPKI 比较高，但整体的 MPKI 被其余命令拉低了。相比之下，SPEC INT 2017 Rate 的 520.omnetpp_r 的 MPKI 足足有 4.33。虽然还是同一个框架，但是负载行为还是出现了明显的变化。

### 714.cpython_r

前面才提到过解释器，这就到 CPython 了。测试包含三条命令：

```shell
# 1. resnet
cpython_r -I -B coreml_pb.py -i 2 -a -m Resnet50Headless.mlmodel -d 10
# 2. mobilenet
cpython_r -I -B coreml_pb.py -i 5 -a -c -m MobileNetV2.mlmodel -d 20
# 3. dna
cpython_r -I -B dna_bench.py 600000
```

三条命令的运行时间分别为 31s、20s 和 20s，总时间 71s，reftime 是 479s，对应 6.7 分。开启 `-O3 -flto` 后，三条命令的运行时间分别为 29s、19s 和 18s，总时间 66s，对应 7.3 分。`-O3 -ljemalloc` 影响很小，`-O3 -march=native` 有负优化。下面具体分析三条命令的负载特性。

#### 1. resnet

还是用 `perf`，统计出热点函数：

- `_PyEval_EvalFrameDefault(PyThreadState *tstate, _PyInterpreterFrame *frame, int throwflag)` 来自 `src/cpython/Python/ceval.c`：24.09%，解释器中的 Loop + Switch 核心代码，对 Python 字节码进行解释执行，主要的瓶颈也是跳转表，根据 opcode 计算 case 地址然后 `jmp *%rax`；
- `PyUnicode_FromFormatV(const char *format, va_list vargs)` 来自 `src/cpython/Objects/unicodeobject.c`，4.51%，把结果写到 Python 字符串的 sprintf 版本，主要瓶颈是格式化字符串的解析，找 `%` 的位置；
- `_PyObject_Free(void *ctx, void *p)` 来自 `src/cpython/Objects/obmalloc.c`：3.48%，释放 PyObject，Python 有一个自己的针对 PyObject 的内存分配器，而不是直接使用 malloc/free；
- `_PyObject_Malloc(void *ctx, size_t nbytes)` 来自 `src/cpython/Objects/obmalloc.c`：3.15%，分配 PyObject。

剩下就比较零散了，主要还是围绕着解释器的循环。执行了 651.6B 条指令，其中有 180.4B 是 Load 指令，104.1B 是 Store 指令，136.6B 是分支指令，错误预测仅 7.9M 次，MPKI 等于 `7.9M/651.6B*1000=0.01` 可以忽略不计。开启 `-O3 -flto` 后，热点函数不变，指令数降低为 618.0B，其中 Load 有 176.6B，Store 有 93.9B，分支有 128.6B，错误预测 48.6M 次。

#### 2. mobilenet

统计出热点函数，发现前四依然是上面四个，且时间占比差不多。可能是因为，resnet 和 mobilenet 测例用的是同一个 .py 源码，只是用的模型不同。执行了 438.9B 条指令，其中有 121.4B 是 Load 指令，70.5B 是 Store 指令，91.6B 是分支指令，错误预测 9.1M 次，MPKI 等于 `9.1M/438.9B*1000=0.02` 可以忽略不计。开启 `-O3 -flto` 后，热点函数不变，指令数降低为 416.4B，其中 Load 指令有 119.0B，Store 指令有 63.8B，分支有 86.2B，错误预测 35.0M 次。

#### 3. dna

统计热点函数：

- `_PyEval_EvalFrameDefault(PyThreadState *tstate, _PyInterpreterFrame *frame, int throwflag)` 来自 `src/cpython/Python/ceval.c`：36.75%，描述见上；
- `_PyObject_Free(void *ctx, void *p)` 来自 `src/cpython/Objects/obmalloc.c`：5.31%，描述见上；
- `PyUnicode_Contains(PyObject *str, PyObject *substr)` 来自 `src/cpython/Objects/unicodeobject.c`，4.59%，Python 字符串的 contains 操作，对应 `data/all/input/knucleotide.py` 代码中的 `chat in "GATC"` 判断；
- `_PyObject_Malloc(void *ctx, size_t nbytes)` 来自 `src/cpython/Objects/obmalloc.c`：3.52%，描述见上。

主要热点还是解释执行，不过因为字符串的 contains 调用次数较多，所以 `PyUnicode_Contains` 时间占比有所上升。执行了 394.9B 条指令，其中有 113.3B 是 Load 指令，62.1B 是 Store 指令，77.1B 是分支指令，错误预测 228.1M 次，MPKI 等于 `228M/394B*1000=0.58` 也还是很低。开启 `-O3 -flto` 后，热点函数不变，指令数降低为 379.3B，其中 Load 有 113.4B，Store 有 58.5B，分支有 71.6B，错误预测 223.8M 次。

#### 小结

| 子测试    | 编译器+选项        | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 错误预测 (M) |
|-----------|--------------------|----------|----------|----------|-----------|----------|--------------|
| resnet    | GCC 14 `-O3`       | 31       | 651.6    | 180.4    | 104.1     | 136.6    | 7.9          |
| resnet    | GCC 14 `-O3 -flto` | 29       | 618.0    | 176.6    | 93.9      | 128.6    | 48.6         |
| mobilenet | GCC 14 `-O3`       | 20       | 438.9    | 121.4    | 70.5      | 91.6     | 9.1          |
| mobilenet | GCC 14 `-O3 -flto` | 19       | 416.4    | 119.0    | 63.8      | 86.2     | 35.0         |
| dna       | GCC 14 `-O3`       | 20       | 394.9    | 113.3    | 62.1      | 77.1     | 228.1        |
| dna       | GCC 14 `-O3 -flto` | 18       | 379.3    | 113.4    | 58.5      | 71.6     | 223.8        |

714.cpython_r 就是一个典型的基于字节码的解释器，在一个 Loop + Switch 结构当中完成解释执行。整体 MPKI 很低，只有 0.17，即使开了 `-O3 -flto`，虽然预测错误多了，总指令数少了，MPKI 会变大，但绝对数字也还是很小，只有 0.23。

### 721.gcc_r

又一个熟悉的面孔，之前是 SPEC INT 2017 的 502.gcc_r。之前是 GCC 4.5.0 版本，针对 gcc-pp.c、gcc-smaller.c 和 ref32.c 进行五次编译，这次 721.gcc_r 对着三个同名文件（其中 gcc-pp.c 内容更新了，其余两个不变）分别进行一次编译，基于 GCC 11.2.0 版本，命令行参数如下，相比 502.gcc_r 有所简化：

```shell
# 1. gcc-pp
cc1_r gcc-pp.c -O2 -fpic -o gcc-pp.c.opts-O2_-fpic.s
# 2. gcc-smaller
cc1_r gcc-smaller.c -O3 -fipa-pta -o gcc-smaller.c.opts-O3_-fipa-pta.s
# 3. ref32
cc1_r ref32.c -O3 -finline-limit=12000 -fno-tree-vrp -o ref32.c.opts-O3_-finline-limit_12000_-fno-tree-vrp.s
```

`-O3` 运行时间分别为 44s、21s 和 51s，总时间 116s，reftime 是 686s，对应 5.9 分。开了 `-O3 -flto` 后，时间略微降低到 115s，开 `-O3 -flto -ljemalloc` 后时间进一步降低到 111s，主要针对的是占用时间约 2% 的 malloc/free。开 `-march=native` 对性能几乎没有影响。

与 502.gcc_r 的行为类似（见 [The Alberta Workloads for the SPEC CPU® 2017 Benchmark Suite 的分析](https://webdocs.cs.ualberta.ca/~amaral/AlbertaWorkloadsForSPECCPU2017/reports/gcc_report.html)），721.gcc_r 的时间分布在大量函数，除了 ref32 花费了 10.76% 的时间在 `dominated_by_p`、5.92% 的时间在 `bitmap_set_bit` 以外，其他函数的占用时间基本都在 3% 以下，没有一个特别明显的热点函数。

其中 `bitmap_set_bit(bitmap head, int bit)` 函数来自 `src/gcc/bitmap.cc`，通过位运算，在 bitmap 里把一个 bit 设为一，比较特别的是，这个 bitmap 可以有二叉树（splay tree）和链表两种保存格式。从 `perf record -e branch-misses:pp` 来看，这个函数主要是在设置 bit 的时候出现了一些分支预测的错误：它首先读取 bitmap 原来的数值，判断该 bit 是否已经设置，只有之前没设置的情况下，才会更新 bitmap。这样的好处是，可以节省一些 Store 指令，但也带来了一些分支的错误预测。此外就是链表的插入逻辑，需要判断指针是否为空。

另外，`dominated_by_p(enum cdi_direction dir, const_basic_block bb1, const_basic_block bb2)` 函数来自 `src/gcc/dominance.cc`，做的是基本块的 dominance 查询，A dom B 代表从函数入口到 B 一定会经过 A，这是编译器中很常见的一个查询，由于查询次数很多，会预先通过两遍 dfs（一遍从上往下，一遍从下往上，上对应入口，下对应出口）找到基本块的拓扑顺序，然后根据拓扑排序的结果来判断是否有 A dom B 的关系：`DFS_Number_In(A) <= DFS_Number_In(B) && DFS_Number_Out (A) >= DFS_Number_Out(B)`，也就是从上往下遍历（In）的时候，先到达 A，然后从下往上遍历（Out）的时候，先到达 B。其实这个函数并不复杂，但是因为它把两次比较做成了一次 `cmp+jl` 和一次 `cmp+setle`，导致容易出现分支预测错误。从逻辑上来说，这里可以改成完成两次比较，再对结果取 AND，但由于代码里是 `&&` 有短路的性质，理论上第一个条件成立了，就不该进行第二个条件，更何况第二个条件里还涉及两次访存。这种实现确实可能省下一些访存，但分支预测也变难了。如果改写代码，先进行两次比较，再进行 `&&` 操作，就没有分支指令了，不过访存次数也确实变多了：[Godbolt](https://godbolt.org/z/qKaKzT6a1)。

三次运行的性能计数器如下：

1. gcc-pp: 执行 470.2B 条指令，其中有 125.6B 条 Load 指令，58.8B 条 Store 指令，99.9B 条分支指令，错误预测 2.2B 次，MPKI 等于 `2.2B/470.2B*1000=4.68`
2. gcc-smaller: 执行 243.4B 条指令，其中有 65.0B 条 Load 指令，30.3B 条 Store 指令，51.8B 条分支指令，错误预测 0.91B 次，MPKI 等于 `0.91B/243.4B*1000=3.74`
3. ref32: 执行 403.7B 条指令，其中有 118.9 条 Load 指令，45.8B 条 Store 指令，86.1B 条分支指令，错误预测 0.61B 次，MPKI 等于 `0.61B/403.7B*1000=1.51`

| 子测试      | 编译器+选项  | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 错误预测 (B) | MPKI |
|-------------|--------------|----------|----------|----------|-----------|----------|--------------|------|
| gcc-pp      | GCC 14 `-O3` | 44       | 470.2    | 125.6    | 58.8      | 99.9     | 2.2          | 4.68 |
| gcc-smaller | GCC 14 `-O3` | 21       | 243.2    | 65.0     | 30.3      | 51.8     | 0.91         | 3.74 |
| ref32       | GCC 14 `-O3` | 51       | 403.8    | 118.9    | 45.8      | 86.1     | 0.61         | 1.51 |

整体指令数是 1120B，其中有 238B 条分支指令，MPKI 等于 3.37，在 SPEC INT 2026 中属于比较高的了。在 SPEC INT 2017 Rate 当中，502.gcc_r 的 MPKI 是 3.13，变化不大。

意料之中的是，用 GCC 14 编译的 721.gcc_r，运行得比用 LLVM 22 编译的 721.gcc_r 更快。

### 723.llvm_r

随着 LLVM 的发展，SPEC CPU 2026 终于是把 LLVM 也加入了进来。和 721.gcc_r 类似，也是跑 LLVM 的优化器，只不过输入直接就是 .bc 中间代码文件，而不是 C 代码。它包括两条命令：

```shell
# 1. transformsplus
llvm-opt_r transformsplus.bc -S -O3 -mcpu=pwr9
# 2. codegen
llvm-opt_r codegen.bc -S -O3 -mcpu=pwr9
```

`-O3` 运行时间分别为 62s 和 53s，总时间 115s，reftime 是 507s，对应 4.4 分。开 `-O3 -flto` 性能反而变差，不过开 `-O3 -ljemalloc` 有明显性能提升，运行时间降低为 59s 和 47s，总时间 106s，分数提高到 4.8 分。开 `-march=native` 对性能几乎没有影响。

有意思的是，用 GCC 14 编译的 723.llvm_r，运行得比用 LLVM 22 编译的 723.llvm_r 更快，当然快得并不多。下面针对这两条命令进行具体的分析。

#### 1. transformsplus

使用 `perf` 观察热点函数：

- `llvm::InstCombinerImpl::foldIntegerTypedPHI(llvm::PHINode& PN)` 来自 `src/lib/Transforms/InstCombine/InstCombinePHI.cpp`: 4.06%，对 IR 中的 PHI 结点进行处理，这个函数还挺复杂的，主要瓶颈在内层循环，遍历 use 链表，有比较多的随机访存和通过分支来判断 LLVM 自制 RTTI 的类型；
- `_int_malloc/cfree/malloc`：2.38%+0.89%+0.82%=4.09%，大量的内存分配和释放，因此 `-ljemalloc` 能带来不错的性能提升；
- `llvm::DenseMapBase::FindAndConstruct()`: 1.69%，LLVM 自己用数组实现的哈希表，主要瓶颈在读取哈希桶内的 entry 并比较 key，随机访存比较慢。

其他有很多小的函数，占时间比例不高，和 721.gcc_r 类似，也是时间分散得比较开。执行指令数为 572.8B，其中 Load 指令有 137.7B，Store 指令有 78.6B，分支指令有 118.7B，错误预测有 3.5B 次，MPKI 等于 `3.5B/572.8B*1000=6.11`，挺高的。

从 `perf record -e branch-misses:pp` 来看，错误预测挺分散在很多个函数，每个函数比例也不高。从 Top down 来看，有 40% 都在 Frontend Bound，有 19.2% 在 Bad Speculation。更进一步分析，发现它的 L1 ICache 缺失次数为 12.6B（`L1-icache-load-misses` 性能计数器），对应的 L1IC MPKI 足足有 `12.6B/572.8B*1000=22.0`，可见主要问题是 723.llvm_r 的代码量太大了，L1IC 存不下，BTB 也够呛。

#### 2. codegen

使用 `perf` 观察热点函数：

- `llvm::InstCombinerImpl::foldIntegerTypedPHI(llvm::PHINode& PN)` 来自 `src/lib/Transforms/InstCombine/InstCombinePHI.cpp`: 20.85%，描述见上；
- `_int_malloc/cfree/malloc`：1.91%+0.72%+0.65%=3.28%，描述见上；
- `llvm::DenseMapBase::FindAndConstruct()`: 1.29%，描述见上。

整体的情况和 transformsplus 类似，只不过 `foldIntegerTypedPHI` 时间占比更高，其他还是有很多函数耗费很短的时间，分散得比较开。执行指令数为 415.9B，其中 Load 指令有 100.4B，Store 指令有 57.5B，分支指令有 86.0B，错误预测有 2.4B 次，MPKI 等于 `2.4B/415.9B*1000=5.77`，依然很高。

#### 小结

| 子测试         | 编译器+选项  | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 错误预测 (B) | MPKI |
|----------------|--------------|----------|----------|----------|-----------|----------|--------------|------|
| transformsplus | GCC 14 `-O3` | 62       | 572.8    | 137.7    | 78.6      | 118.7    | 3.5          | 6.11 |
| codegen        | GCC 14 `-O3` | 53       | 415.9    | 100.4    | 57.5      | 86.0     | 2.4          | 5.77 |

llvm 和 gcc 同为编译器的双子星，在负载特性上也有类似之处：有很多的内存分配和释放，受益于 `-ljemalloc`；时间分布在大量小函数当中，热点不明显；MPKI 较高，尤其是 723.llvm_r 直接一跃成为 SPEC INT 2026 Rate 中 MPKI 最高的一项测试，可能是因为它有大量数据依赖的分支。723.llvm_r 整体的指令数有 991B，其中有 205B 是分支指令，MPKI 达到 5.98，即使放在 SPEC INT 2017 Rate 里，也能紧跟在 505.mcf_r 和 541.leela_r 两位大哥身后，成为 MPKI 第三高的项目。

### 727.cppcheck_r

cppcheck 是一个 cpp 静态分析工具，输入 C++ 文件，提供代码的分析报告，汇报数组越界访问或变量未初始化等等问题。它会分析三个不同的代码，根据命名看，应该是从其他测例里找的。747 和 770 不在 SPEC CPU 2026 当中，应该没被选上，只有 738 diamond 以 838.diamond_s 保留了下来：

```shell
# 1. 738_diamond
cppcheck_r --force 738-diamond-record.cpp --checkers-report=738_report.txt --enable=all --output-file=738_bogey.txt
# 2. 747_dealii
cppcheck_r --force 747-dealii-data_out_base.cc --checkers-report=747_report.txt --enable=all --output-file=747_bogey.txt
# 3. 770_7z
cppcheck_r --force 770-7z-SystemPage.cpp --checkers-report=770_report.txt --output-file=770_bogey.txt
```

三条指令的运行时间分别为 27s、22s 和 33s，共 82s，reftime 是 359s，对应 4.4 分。开 `-O3 -flto` 或 `-O3 -march=native` 仅能略微提升 1% 的性能，但 `-O3 -ljemalloc` 能显著提升性能，运行时间缩短到 24s、18s 和 29s，总时间 71s，对应 5.1 分。

下面对这三条命令进行深入的分析。

#### 1. 738_diamond

热点函数如下：

- `multiCompareImpl(const Token *tok, const char *haystack, nonneg int varid)` 来自 `src/lib/token.cpp`：40.82%，字符串匹配函数，比如用 abc|def 去匹配一个 token，主要时间用在找 NUL、空格或 `|` 等字符；
- `Token::Match(const Token *tok, const char pattern[], nonneg int varid)` 来自 `src/lib/token.cpp`：12.08%，也是类似的字符串匹配函数，语法有些不同，类似自研正则表达式子集，它会调用上面的 `multiCompareImpl` 函数来做部分匹配；
- `ScopeInfo3::findScope(const std::string & scope)` 来自 `src/lib/tokenize.cpp`：5.49%，循环，从当前作用域开始寻找对应的符号，如果没有，则检查更高一级的作用域，一般用于从变量名找到作用域里定义的符号，主要时间花在对 `std::list` 的遍历以及 `std::string` 的比较；
- `Tokenizer::simplifyUsing()`：3.57%，把 `using N::x;` 变为 `using x = N::x`，里面就会用到上面说的 `Token::Match`，参数如 `"using ::| %name% ::"`，来做一些模式的匹配并进行相应的简化；
- `cfree/malloc/_int_malloc`：0.47%+0.33%+0.45%=1.25%，内存分配相关。

可以看到，主要的瓶颈是字符串匹配上，它的实现就是一个循环，用指针去扫描字符串，没有做数据结构上的优化。执行了 399.9B 条指令，其中有 81.2B 条 Load 指令，25.5B 条 Store 指令，108.9B 条分支指令，错误预测 173.2M 次，MPKI 等于 `173M/399.9B*1000=0.43` 不算高。

#### 2. 747_dealii

热点函数类似：

- `multiCompareImpl(const Token *tok, const char *haystack, nonneg int varid)` 来自 `src/lib/token.cpp`：27.42%，描述见上；
- `Token::Match(const Token *tok, const char pattern[], nonneg int varid)` 来自 `src/lib/token.cpp`：14.55%，描述见上；
- `cfree/malloc/_int_malloc`：2.14%+1.57%+0.53%=4.24%，内存分配的比例更高；
- `Token::simpleMatch(const Token *tok, const char pattern[], size_t pattern_len)` 来自 `src/lib/token.cpp`：3.88%，又一个字符串匹配函数，换了种格式，比如 `"abc def"` 代表匹配 `abc` 或 `def`，这次的瓶颈是 `strncmp` 和 `memchr`；
- `TemplateSimplifier::addInstantiation(Token *token, const std::string &scope)` 来自 `src/lib/templatesimplifier.cpp`：2.98%，在 token 级别上做一些代码简化的变换，主要的耗时在对 `std::list` 的遍历；
- `isAliasOf(const Token* tok, const Token* expr, int* indirect, bool* inconclusive)` 来自 `src/lib/astutils.cpp`：2.55%，判断两个变量是否 alias。

依然有大量的字符串匹配，不知道为啥还要搞好几种语法，实现好几个字符串匹配函数。执行了 303.9B 条指令，其中有 67.3B 条 Load 指令，31.5B 条 Store 指令，82.5B 条分支指令，错误预测 298.9M 次，MPKI 等于 `298.9M/303.9B*1000=0.98` 也不算高。

#### 3. 770_7z

热点如下：

- `multiCompareImpl(const Token *tok, const char *haystack, nonneg int varid)` 来自 `src/lib/token.cpp`：32.25%，描述见上；
- `Token::Match(const Token *tok, const char pattern[], nonneg int varid)` 来自 `src/lib/token.cpp`：18.82%，描述见上；
- `__memcmp_avx2_movbe`：8.99%，被用于字符串匹配；
- `std::map<std::string>::equal_range`：7.34%，红黑树上的查询，外加字符串匹配；
- `__strchr_avx2`：7.34%，被用于字符串匹配；
- `cfree/malloc/_int_malloc`：0.37%+0.27%+0.17%=0.81%，这次内存分配的比例较低。

依然是字符串匹配为主。执行了 505.2B 条指令，其中有 111.0B 条 Load 指令，43.8B 条 Store 指令，137.5B 条分支指令，错误预测 421.0M 次，MPKI 等于 `421M/505.2B*1000=0.83` 也不算高。

#### 小结

整体看下来，727.cppcheck_r 就是在不断地做字符串匹配。我就纳闷了，为啥不能直接过一遍 tokenizer，把 token 都转为数字呢，这样比较起来多快。在 token 级别上做各种变换，就在不停地对 token 进行字符串比较，导致最后的性能瓶颈，不是在 cppcheck 自己写的字符串比较，就是在 libc 的字符串比较里了。

| 子测试      | 编译器+选项  | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 错误预测 (M) | MPKI |
|-------------|--------------|----------|----------|----------|-----------|----------|--------------|------|
| 738_diamond | GCC 14 `-O3` | 27       | 399.9    | 81.2     | 25.5      | 108.9    | 173.2        | 0.43 |
| 747_dealii  | GCC 14 `-O3` | 22       | 303.9    | 67.3     | 31.5      | 82.5     | 298.9        | 0.98 |
| 770_7z      | GCC 14 `-O3` | 33       | 505.2    | 111.0    | 43.8      | 137.5    | 421.0        | 0.83 |

整体执行了 1211B 指令，其中有 329B 分支指令，分支指令的比例足足有 27%，傲视 SPEC INT 2026 Rate 全场，这都是拜字符串匹配所赐，读一点就比较一点。但同时，MPKI 仅为 0.71，在 SPEC INT 2026 Rate 中倒数第三，仅高于 714.cpython_r 的 0.17 和 750.sealcrypto_r 的 0.14，说明大部分字符串匹配的结果都是很好预测的，比如比较到第一个字节就对不上了。

### 729.abc_r

之前第一次看到 abc 还是在 yosys，它是一个 EDA 软件，和后面的 734.vpr_r 都是开源 EDA 工具里的重量级人物，分别实现了逻辑综合以及布局布线。测试包括 6 条命令：

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

六个命令运行时间都不长，分别是 6.3s、10.1s、13.5s、32.3s、13.6s 和 17.0s，总时间 92.8s，reftime 是 459s，对应 4.9 分。

开 -flto/-march=native/-ljemalloc 都没有什么提升，性能差距在 1% 之内，属于是油盐不进了。下面进行具体热点分析。

#### 1. twoexact

主要的热点函数：

- `sat_solver_propagate(sat_solver* s)` 来自 `src/berkeley-abc/src/sat/bsat/satSolver.c`：75.33%，应该是 SAT Solver 中的 Unit Propagation，寻找那些只剩下一个变量还没确定的语句，给它进行赋值，然后传播到其他语句；
- `sat_solver_analyze(sat_solver* s, int h, veci* learnt)` 来自 `src/berkeley-abc/src/sat/bsat/satSolver`：15.85%，应该是针对出现冲突的语句进行分析，属于 CDCL（Conflict Driven Clause Learning） 的一部分；
- `sat_solver_solve_internal(sat_solver* s)` 来自 `src/berkeley-abc/src/sat/bsat/satSolver.c`：3.80%，是 SAT Solver 的入口函数。

很少能见到这种瓶颈如此高度集中的情况了，不过确实，SAT Solver 大部分时间都在做 Unit Propagation，出现冲突了就做 CDCL。唤起了很久以前在《软件分析与验证》课上写 DPLL SAT Solver 的[回忆](https://github.com/jiegec/dpll)，当然了，abc 的实现肯定比我那课程作业要更加复杂和高级。主要的瓶颈就是一堆访存以及依赖内存结果的分支，在 SAT 问题的解空间内进行搜索。

指令数 53.2B，其中 Load 指令 13.8B，Store 指令 3.2B，分支指令 8.4B，错误预测 606.2M，MPKI 等于 `606.2M/53.2B*1000=11.43`，非常的高，接近 SPEC INT 2017 的 541.leela_r 大帝。

通过 `perf record -e branch-misses:pp`，可以看到主要的分支预测错误来自 `sat_solver_propagate` 的几处变量取值的判断逻辑，都是依赖数据的分支，难以预测。

#### 2. beem6

主要的热点函数：

- `Cec4_ManPackAddPatterns(Gia_Man_t * p, int iBit, Vec_Int_t * vLits)` 来自 `src/proof/cec/cecSatG2.c`：54.65%，CEC 指的是 Combinational Equivalence Checking，函数的用途没仔细研究，不过它就是一个两层循环，对数组元素进行访存和位运算；
- `Cec4_ManGeneratePatterns_rec(Gia_Man_t * p, Gia_Obj_t * pObj, int Value, Vec_Int_t * vPat, Vec_Int_t * vVisit)` 来自 `src/proof/cec/cecSatG2.c`：29.01%，看起来也是一堆复杂的访存和逻辑运算混合。

热点依然很集中，不过因为缺少领域知识，不太明白它在跑什么。运行 255.5B 条指令，其中 Load 有 57.2B，Store 有 7.3B，分支有 40.3B，错误预测 192.0M 次，MPKI 等于 `192.0M/255.5B*1000=0.75`，相比 SAT 来说低了很多。

#### 3. mem

热点函数依然是 sat solver 相关，相比 twoexact，`sat_solver_canceluntil` 时间占比高了一些，达到了 8.46%，不过整体的特性基本是一样的。运行 151.0B 条指令，其中 Load 指令有 43.4B，Store 指令有 15.4B，分支有 24.2B，错误预测 1213.7M，MPKI 等于 `1213.7M/151.0B*1000=8.03`，非常高。

#### 4. vga

热点函数依然是 sat solver，整体特性一致。运行 490.0B 条指令，Load 指令有 143.9B，Store 指令有 54.4B，分支有 76.9B，错误预测 2092.8M 次，MPKI 等于 `2092.8M/490B*1000=4.27`，还是很高。

#### 5. mcml

热点函数终于有了新面孔：

- `Abc_ObjDeleteFanin(Abc_Obj_t * pObj, Abc_Obj_t * pFanin)` 来自 `src/base/abc/abcFanio.c`：12.57%，逻辑很简单，就是调用 `Vec_IntRemove` 从数组里删除一个元素，遍历数组，找到匹配的元素，把后面的元素都往前挪，这个遍历匹配逻辑是主要的瓶颈，其次就是移动数据；
- `Gia_ManSwiSimulate(Gia_Man_t * pAig, Gia_ParSwi_t * pPars)` 来自 `src/aig/gia/giaSwitch.c`：8.87%，依然看不懂在干啥，不过似乎是一些比较适合 SIMD 的循环，在 `-O3` 下能看到一些 SSE 指令，还有一个自己实现的 popcount 函数 `Gia_WordCountOnes`，它没有被识别并转化为 popcnt 指令，而是用 SSE 去向量化软件 popcount 实现；
- `Abc_AigAndLookup(Abc_Aig_t * pMan, Abc_Obj_t * p0, Abc_Obj_t * p1)` 来自 `src/base/abc/abcAig.c`：7.03%，主要时间是在内部一个循环当中，访存加位运算，不知道在实现什么功能，瓶颈在一些间接访存上，一路指针访问 `pObj->pNtk->vObjs->pArray`；
- `If_ObjPerformMappingAnd(If_Man_t * p, If_Obj_t * pObj, int Mode, int fPreprocess, int fFirst)` 来自 `src/map/if/ifMap.c`：6.72%，又是一堆不知道在干啥的复杂位运算；
- `Lpk_NodeCutsOneFilter(Lpk_Cut_t * pCuts, int nCuts, Lpk_Cut_t * pCutNew)` 来自 `src/berkeley-abc/src/opt/lpk/lpkCut.c`：5.47%，主要时间在循环里，不知道在实现什么，瓶颈在一些数据依赖的分支上。

运行 208.0B 条指令，其中 50.1B 条 Load 指令，15.4B 条 Store 指令，39.8B 条分支指令，错误预测 534.8M 次，MPKI 等于 `534.8M/208.0B*1000=2.57`，不低。

#### 6. des

再次出现了新的热点函数：

- `__strcmp_avx2` 来自 libc：22.04%，没想到瓶颈居然又出现在了 strcmp 上；
- `Nm_ManTableLookupId(Nm_Man_t * p, int ObjId)` 来自 `src/misc/nm/nmTable.c`：21.56%，遍历一个哈希表，哈希表的每个桶是个链表，遍历链表中的元素，寻找匹配，主要瓶颈也是这个访问链表和匹配；
- `Nm_ManTableAdd(Nm_Man_t * p, Nm_Entry_t * pEntry)` 来自 `src/misc/nm/nmTable.c`：12.19%，经典的哈希表插入算法，把新元素插入到对应桶的链表当中，主要瓶颈在判断哈希表中是否已经有相同 key 的元素；
- `Nm_ManTableLookupName(Nm_Man_t * p, char * pName, int Type)` 来自 `src/misc/nm/nmTable.c`：5.78%，同样是遍历哈希表查询，只不过这次用的是字符串匹配，解释了为啥 strcmp 调用次数那么多，其实是在找哈希表的字符串匹配；
- `Gia_ManSwiSimulate` 来自 `src/aig/gia/giaSwitch.c`：5.49%，描述见上；
- `spec_qsort`：3.98%，好久不见的熟悉面孔，在 SPEC INT 2017 年代，在 505.mcf_r 中有出色表现（指瓶颈在 qsort 上，且很大一部分开销来自于调用 comparator 函数指针，开 -flto 后因为把函数指针调用内联，性能直接提升 13%）。

这次又是经典数据结构哈希表了，而且还混入了大量的字符串匹配，最后瓶颈都在查哈希表上了，然后对链表的访问的空间局部性也很差。

运行 135.7B 条指令，其中有 29.7B 是 Load 指令，11.5B 是 Store 指令，23.3B 是分支指令，错误预测 372.9M 次，MPKI 等于 `372.9M/135.7B*1000=2.75`，依然不低，从 `perf record -e branch-misses:pp` 来看，错误预测主要出自 `__strcmp_avx2` 和 `spec_qsort`。

#### 小结

| 子测试   | 编译器+选项  | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 错误预测 (M) | MPKI  |
|----------|--------------|----------|----------|----------|-----------|----------|--------------|-------|
| twoexact | GCC 14 `-O3` | 6.3      | 53.2     | 13.8     | 3.2       | 8.4      | 606.2        | 11.43 |
| beem6    | GCC 14 `-O3` | 10.1     | 255.5    | 57.2     | 7.3       | 40.3     | 192.0        | 0.75  |
| mem      | GCC 14 `-O3` | 13.5     | 151.0    | 43.4     | 15.4      | 24.2     | 1213.7       | 8.03  |
| vga      | GCC 14 `-O3` | 32.3     | 490.0    | 143.9    | 54.4      | 76.9     | 2092.8       | 4.27  |
| mcml     | GCC 14 `-O3` | 13.6     | 208.0    | 50.1     | 15.4      | 39.8     | 534.8        | 2.57  |
| des      | GCC 14 `-O3` | 17.0     | 135.7    | 29.7     | 11.5      | 23.3     | 372.9        | 2.75  |

综合以上六条命令，可以看到它触碰了 abc 不同地方的代码，所以热点不尽相同，有 SAT，有看不懂的一些 EDA 相关逻辑，还有带字符串匹配的哈希表查询，其中 SAT 的占比是最大的。由于 SAT 的存在，最终的 MPKI 足足有 3.87，在 SPEC INT 2026 Rate 当中仅次于 723.llvm_r，超过了 721.gcc_r 和 777.zstd_r。

### 734.vpr_r

接下来就到了 EDA 的下一步，逻辑综合后，进行布局（place）布线（route），这就是 vpr_r 干的活。测试分为四条命令：

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

这里的 Stratix IV 是经典的 Altera FPGA，时代的眼泪了。四条命令的运行时间分别是 21s、29s、18s 和 19s，总时间 87s，reftime 是 461s，对应 5.3 分。开 `-O3 -flto` 后，时间降低到 19s、25s、17s 和 17s，总时间 78s，对应 5.9 分，提升显著。如果进一步开到 `-O3 -flto -ljemalloc`，时间进一步降低到 17s、24s、15s 和 16s，总时间 72s，对应 6.4 分，相比 `-O3` 提升了 20%。开 `-march=native` 只能带来不到 1% 的提升。

下面进行具体分析。

#### jpeg_place 和 smithwaterman_place

因为这两条命令都是做的布局（place），所以就放在一起分析了。它们的热点函数是类似的：

- `get_non_updateable_bb(ClusterNetId net_id, t_bb* bb_coord_new)` 来自 `src/vtr-vpr/vpr/src/place/place.cpp`：jpeg_place 占比 13.98%，smithwaterman_place 占比 18.26%，遍历 pin，根据它的 x 和 y 坐标，找到 bounding box，即 xmin/xmax/ymin/ymax，主要时间花在读取 x 和 y 上；
- `try_swap(...)` 来自 `src/vtr-vpr/vpr/src/place/place.cpp`：jpeg_place 占比 12.39%，smithwaterman_place 占比 11.46%，里面做的事情还挺复杂的，看不太懂，大概功能是尝试把一个块从一个地方挪到另一个地方；
- `physical_tile_type(ClusterBlockId blk)` 来自 `src/vtr-vpr/vpr/src/util/vpr_utils.cpp`：jpeg_place 占比 7.59%，smithwaterman_place 占比 7.75%，看起来是一些间接索引访存，先读取 `block_loc` 里的坐标，再从 `grid` 读取对应坐标的 type，这个函数会在 `get_non_updateable_bb` 和 `get_bb_from_scratch` 等地方被频繁调用；
- `get_bb_from_scratch(ClusterNetId net_id, t_bb* coords, t_bb* num_on_edges)` 来自 `src/vtr-vpr/vpr/src/place/place.cpp`：jpeg_place 占比 6.73%，smithwaterman_place 占比 2.78%，和 `get_non_updateable_bb` 类似，也是求 bounding box；
- `malloc/_int_mallloc/cfree` 来自 libc：jpeg_place 占比 1.62%+1.26%+1.06%=3.94%，smithwaterman_place 占比 1.76%+1.42%+1.11%=4.29%。

开 `-O3 -flto` 后，能看到的是 `physical_tile_type` 被内联了进去，节省了频繁调用函数的开销。考虑到这个内存分配和释放的时间占比，`-O3 -ljemalloc` 提升性能并不意外。

`-O3` 下，jpeg_place 执行了 273.7B 条指令，其中 Load 有 84.5B 条，Store 有 26.9B 条，分支有 51.9B 条，错误预测 781.0M 次，MPKI 等于 `781.0M/273.7B*1000=2.85`，不低。smithwaterman_place 执行了 245.0B 条指令，其中 Load 有 76.4B 条，Store 有 24.7B 条，分支有 45.4B 条，错误预测 661.9M 次，MPKI 等于 `661.9M/245.0B*1000=2.70`。在 bounding box 计算 min/max 过程中，能看到一些 cmov 指令的使用，因此实际上已经少了一些容易预测错误的分支了。在一些没有 cmov 指令的 ISA 下，可能 MPKI 还会更高。

#### jpeg_route 和 smithwaterman_route

到了布线，热点函数出现了一些不同：

- `ConnectionRouter<BinaryHeap>::evaluate_timing_driven_node_costs(...)` 来自 `src/vtr-vpr/vpr/src/route/connection_router.cpp`：jpeg_route 占比 9.35%，smithwaterman_route 占比 6.91%，有一些浮点运算，不知道具体在算什么；
- `ConnectionRouter<BinaryHeap>::timing_driven_add_to_heap(...)` 来自 `src/vtr-vpr/vpr/src/route/connection_router.cpp`：jpeg_route 占比 9.34%，smithwaterman_route 占比 6.82%，会调用 `evaluate_timing_driven_node_costs` 计算 cost，然后插入到 Binary Heap 当中；
- `ConnectionRouter<BinaryHeap>::timing_driven_expand_neighbours(...)` 来自 `src/vtr-vpr/vpr/src/route/connection_router.cpp`：jpeg_route 占比 8.14%，smithwaterman_route 占比 4.00%，不确定在干啥，看起来在遍历邻居结点，符合一定条件后，调用 `timing_driven_add_to_heap`；
- `ClassicLookahead::get_expected_delay_and_cong(...)` 来自 `src/vtr-vpr/vpr/src/route/router_lookahead.cpp`：jpeg_route 占比 7.86%，smithwaterman_route 占比 5.14%，看起来也是在进行一些延迟的计算，涉及到很多浮点数；
- `BinaryHeap::get_heap_head()` 来自 `src/vtr-vpr/vpr/src/route/binary_heap.cpp`：jpeg_route 占比 3.14%，smithwaterman_route 占比 1.64%，就是经典的最小二叉堆的实现，获取最小值，用的是浮点数做比较；
- `malloc/_int_mallloc/cfree` 来自 libc：jpeg_route 占比 1.10%+1.02%+0.78%=2.90%，smithwaterman_route 占比 1.62%+1.49%+1.08%=4.19%。

虽然不清楚具体算法，但看起来，就像是在做一些 cost 计算，然后通过 BinaryHeap 选择最小的 cost 去做一些扩展，有点类似搜索算法。

开 `-O3 -flto` 后，能看到的是 `evaluate_timing_driven_node_costs` 和 `timing_driven_add_to_heap` 被内联进 `timing_driven_expand_neighbours`，节省了频繁调用函数的开销，这个函数的时间占比提升到 jpeg_route 的 21.40% 和 smithwaterman_route 的 12.48%，类似的事情应该也发生在 `get_expected_delay_and_cong` 身上。考虑到这个内存分配和释放的时间占比，`-O3 -ljemalloc` 提升性能并不意外。

`-O3` 下，jpeg_route 执行了 424.1B 条指令，其中 Load 有 130.6B，Store 有 50.6B，分支有 79.0B 条，错误预测 1094.2M 次，MPKI 等于 `1094.2M/424.1B*1000=2.58`，不低。smithwaterman_route 执行了 305.8B 条指令，其中 Load 有 91.0B 条，Store 有 36.0B 条，分支有 59.4B 条，错误预测 609.3M 次，MPKI 等于 `609.3M/305.8B*1000=1.99`。

#### 小结

| 子测试              | 编译器+选项  | 时间 (s) | 指令 (B) | Load (B) | Store (B) | 分支 (B) | 错误预测 (M) | MPKI  |
|---------------------|--------------|----------|----------|----------|-----------|----------|--------------|-------|
| jpeg_place          | GCC 14 `-O3` | 21       | 273.7    | 84.5     | 26.9      | 521.9    | 781.0        | 2.85  |
| jpeg_route          | GCC 14 `-O3` | 29       | 424.1    | 130.6    | 50.6      | 79.0     | 1094.2       | 2.58  |
| smithwaterman_place | GCC 14 `-O3` | 18       | 245.0    | 76.4     | 24.7      | 45.4     | 661.9        | 2.70  |
| smithwaterman_route | GCC 14 `-O3` | 19       | 305.8    | 91.0     | 36.0      | 59.4     | 609.3        | 21.99 |

734.vpr_r 的负载分为两部分，place 和 route，其中 place 主要在做 bounding box 的计算，route 主要在做搜索和优化。开 `-flto` 和 `-ljemalloc` 后有明显的性能提升，主要是靠内联了热点函数以及更快的性能分配。整体指令数为 1254B，分支指令数 237B，MPKI 是 2.51，处于中游偏高的水平。

### 735.gem5_r

gem5 是大家很熟悉的模拟器了，在 GEM5 里跑 SPEC CPU 2017 养活了很多博士生，这下终于完成闭环，在 GEM5 里跑 SPEC INT 2026 的 GEM5，自己跑自己。当然，735.gem5_r 的 workload 就不是 SPEC CPU 2026 了，没有继续套娃，而是跑的 RISC-V Linux 内核，以及生成访存序列对内存子系统进行测试。这也是唯一一个看到函数名就知道函数来自哪个文件的项目了，实在太熟悉了。包括如下四条命令：

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

运行时间分别为 16s、21s、21s 和 31s，总时间 89s，reftime 是 487s，对应 5.4 分。各种编译选项的优化效果：

- 开 `-O3 -flto` 后运行时间降为 15s、20s、20s 和 29s，共 84s，对应 5.8 分，相比 `-O3` 提升 6%。对四条命令都有加速效果。
- 开 `-O3 -flto -ljemalloc` 后降为 14s、18s、16s 和 26s，共 74s，对应 6.6 分，相比 `-O3` 提升 20%。对四条命令都有比较显著的加速效果。
- 开 `-O3 -march=native -flto -ljemalloc` 后 12s、18s、16s 和 26s，共 72s，对应 6.8 分，相比 `-O3` 提升 24%。仅对第一条命令有加速效果。

看到这个性能提升的幅度，结合前面的经验，已经可以预估一下后面会见到的瓶颈大概是什么类型了。

#### o3

第一个测例是用 O3 CPU 模拟 RISC-V Linux 内核启动，热点函数如下：

- `malloc/_int_malloc/cfree/_int_free_chunk/operator new` 来自 libc/libstdc++：4.78%+3.46%+3.29%+1.35%+1.16%=13.29%，这个比例无敌了，不过确实，Gem5 有大量的动态内存分配，比如各种内存请求，都要 new 一个 Packet 出来
- `gem5::TimeBuffer<*>::advance()` 来自 `src/gem5/cpu/timebuf.hh`：3.05%+2.43%+2.39%+2.28+1.98%=12.13%，用于在各流水线级之间传递数据，维护一个滚动的时间窗口，主要的时间花在了 rep stos 对内存进行初始化，还有调用构造/析构函数，涉及到一些引用计数的更新
- `gem5::o3::IEW::tick()` 来自 `src/gem5/cpu/o3/iew.cc`：3.32%，IEW 代表 Issue Execute Writeback，后端各执行单元的时序在这里模拟

其他就是很多零散的函数了，每个函数的耗时都不高。开启 `-O3 -flto` 后，热点函数变为：

- `std::_Function_handler<void (), gem5::o3::CPU::CPU(gem5::BaseO3CPUParams const&)::{lambda()#1}>::_M_invoke(std::_Any_data const&)`：20.80% 实际上是 `tickEvent([this]{ tick(); }, "O3CPU tick", false, Event::CPU_Tick_Pri)` 当中调用 `tick()` 的 lambda，就是整个 O3 CPU 各种组件的单步模拟被融合到了一个巨大的函数里，仔细看里面的热点指令，其实还是 `gem5::TimeBuffer<*>::advance()` 相关的比较多
- `gem5::o3::IEW::tick()` 来自 `src/gem5/cpu/o3/iew.cc`：8.58%，描述见上
- `malloc/_int_malloc/cfree/_int_free_chunk/operator new` 来自 libc/libstdc++：5.55%+3.88%+3.72%+1.45%+1.22%=15.83%，随着其余部分被优化，内存分配的瓶颈更加明显了

进一步开启 `-O3 -flto -ljemalloc` 后，内存分配时间减少，热点函数：

- `std::_Function_handler<void (), gem5::o3::CPU::CPU(gem5::BaseO3CPUParams const&)::{lambda()#1}>::_M_invoke(std::_Any_data const&)`：23.20%，描述见上
- `gem5::o3::IEW::tick()` 来自 `src/gem5/cpu/o3/iew.cc`：9.19%，描述见上
- `gem5::o3::Commit::commit()` 来自 `src/gem5/cpu/o3/commit.cc`：4.56%，模拟 CPU 的 Commit 阶段
- `malloc/_int_malloc/cfree/_int_free_chunk/operator new/operator delete` 来自 libjemalloc：3.12%+1.02%+0.53%=4.67%，明显变少

开启 `-O3 -march=native` 带来的效果是，用 memset 调用取代了之前的 rep stos，进而可以用更加高效的 AVX2 版本的 memset 来进行初始化，优化了 `gem5::TimeBuffer<*>::advance()` 的性能。

`-O3` 下，执行 212B 条指令，其中有 43B 条分支指令，错误预测 176M 次，MPKI 等于 `176M/212B*1000=0.83`，比较低。

#### timing

第二个测例则是把 O3 换成了 TimingSimpleCPU，相比 O3 模拟的复杂度低很多，此时主要的瓶颈挪到了 RISC-V 架构相关的代码、缓存模拟，以及内存分配上：

- `cfree/malloc/operator new` 来自 libc：5.92%+4.56%+1.55%=12.03%，依然有很多内存分配的瓶颈
- `gem5::RiscvISA::Decoder::decode(ExtMachInst mach_inst, Addr addr)` 来自 `src/gem5/arch/riscv/decoder.cc`：8.97%，实现 RISC-V 指令集的 Decode，有很大一部分实现是自动生成的，在 `src/gem5/arch/riscv/generated/decode-method.cc.inc` 文件里
- `gem5::BaseTags::findBlock(Addr addr, bool is_secure)` 来自 `src/gem5/mem/cache/tags/base.cc`：5.19%，用来实现组相连的 tag 比较，就是一个循环比较 tag 找匹配的算法
- `gem5::PMAChecker::check(const RequestPtr &req)` 来自 `src/gem5/arch/riscv/pma_checker.cc`：4.86%，实现 RISC-V 的 PMA 检查，属于 MMU 的一部分，逻辑很简单，就是判断一下是否 Uncacheable，如果是，就标记 STRICT_ORDER，避免重排
- `gem5::RiscvISA::ISA::readMiscReg(RegIndex idx)` 来自 `src/gem5/arch/riscv/isa.cc`：3.34%，用于读取 RISC-V 的 CSR
- `gem5::BaseCache::access(PacketPtr pkt, CacheBlk *&blk, Cycles &lat, PacketList &writebacks)` 来自 `src/gem5/mem/cache/base.cc`：2.84%，用于模拟缓存的访问
- `gem5::PMP::pmpCheck(const RequestPtr &req, BaseMMU::Mode mode, RiscvISA::PrivilegeMode pmode, ThreadContext *tc, Addr vaddr)` 来自 `src/gem5/arch/riscv/pmp.cc`：2.66%，实现 RISC-V 的 PMP 检查，属于 MMU 的一部分，扫描 PMP 配置，逐个判断是否匹配

开 `-O3 -flto` 后，`readMiscReg` 被内联。开 `-O3 -flto -ljemalloc` 后，内存分配的开销降低到 4.48%+1.34%=5.82%。`-march=native` 影响比较小。

`-O3` 下，执行 334B 条指令，其中有 69.8B 条分支指令，错误预测 207.8M 次，MPKI 等于 `207.8M/334B*1000=0.62`，比较低。

#### traffic_21

热点函数：

- `cfree/malloc/operator new` 来自 libc：6.01%+4.62%+1.44%+1.40%=13.47%，依然有很多内存分配的瓶颈
- `gem5::SnoopFilter::lookupRequest(const Packet* cpkt, const ResponsePort& cpu_side_port)` 来自 `src/gem5/mem/snoop_filter.c`：5.93%，在总线上对 Snoop 请求进行 Filter，减少缓存一致性开销；此外它还有一个 `std::map`，查询和更新也耗费了不少时间
- `gem5::AddrRange::removeIntlvBits(Addr a)` 来自 `src/gem5/base/addr_range.hh`：3.39%，针对地址的 interleaving，进行一系列位运算，把 interleaving 的那部分比特去掉，保留其他的，具体实现方法是，找到要去掉的比特的位置，从小到大进行排序，然后把要保留的比特分段插入到结果当中
- `gem5::BaseTags::findBlock(Addr addr, bool is_secure)` 来自 `src/gem5/mem/cache/tags/base.cc`：3.18%，描述见上

开启 `-O3 -flto` 后，热点函数中 `removeIntlvBits` 消失，时间转移到了 `gem5::memory::DRAMInterface::decodePacket` 和 `gem5::memory::DRAMInterface::chooseNextFRFCFS`。开 `-O3 -flto -ljemalloc` 后，内存分配的开销降低到 4.08%+1.39%=5.47%。`-march=native` 影响比较小。

`-O3` 下，执行 226.5B 条指令，其中有 50.8B 条分支指令，错误预测 760.5M 次，MPKI 等于 `760.5M/226.5B*1000=3.35`，明显变高。

#### traffic_74_ruby

相比 traffic_21，traffic_74_ruby 开启了 ruby（不是那个 ruby 编程语言），因此瓶颈来到了 `gem5::ruby` 相关：

- `cfree/malloc/operator new` 来自 libc：4.43%+3.52%+1.29%+0.98%=10.22%，依然有很多内存分配的瓶颈
- `gem5::ruby::Cache_Controller::processNextState(Cache_TBE*& m_tbe_ptr, Cache_CacheEntry*& m_cache_entry_ptr, Addr addr)` 来自 `src/gem5/mem/ruby/protocol/Cache_Controller.cc`：4.44%，维护缓存的状态机，还挺复杂的
- `gem5::ruby::NetDest::intersectionIsNotEmpty(const NetDest& other_netDest)` 来自 `src/gem5/mem/ruby/common/NetDest.cc`：4.03%，做的是一些 std::bitset 的与操作
- `gem5::ruby::MessageBuffer::isReady(Tick current_time)` 来自 `src/gem5/mem/ruby/network/MessageBuffer.cc`：3.94%，维护了消息队列，判断当前时间是否有 ready 的消息
- `gem5::ruby::Cache_Controller::getDirEntry(const Addr& param_addr)` 来自 `src/gem5/mem/ruby/protocol/Cache_Controller.cc`：3.80%，根据地址找到 cache 对应的 entry，实现类似 `gem5::BaseTags::findBlock`

开启 `-O3 -flto` 后，`gem5::ruby::NetDest::intersectionIsNotEmpty` 被内联到 `gem5::ruby::WeightBased::route` 函数里，成为占时间最多的函数，占 6.45%。开启 `-O3 -flto -ljemalloc` 后，内存分配开销降低到 3.01%+0.83%=3.84%。`-march=native` 影响比较小。

`-O3` 下，执行 391.8B 条指令，其中有 82.1B 条分支指令，错误预测 1.25B 次，MPKI 等于 `1.25B/391.8B*1000=3.19`，依然较高。

#### 小结

735.gem5_r 四个测试跑的是挺不一样的代码路径，第一个 o3 的主要瓶颈就是 O3CPU，第二个 timing 的主要瓶颈是 RISC-V 指令集相关的代码，第三个 traffic_21 主要是缓存和内存控制器，而 traffic_74_ruby 主要是用 ruby 模拟的内存子系统。由于 gem5 高度模块化，有些时候一些可以 inline 函数没有被 inline，所以 `-flto` 可以带来不错的性能提升。此外，gem5 很喜欢动态分配内存，运行过程中有很多动态产生的对象，比如 Packet 等等，所以用 `-ljemalloc` 能带来不错的提升。`-march=native` 确实不太有用武之地。

整体下来，执行 1164B 条指令，其中有 246B 条分支指令，MPKI 等于 2.05，不算高，主要由后两个 traffic 测例贡献。

### 750.sealcrypto_r

sealcrypto 做的是同态加密，只有一条命令做测试：

```shell
sealcrypto_r refrate ecuador_province_capitals_refrate.csv Galapagos
```

运行时间 108s，reftime 是 536s，对应 5.0 分。

很奇特的是，开 `-O3 -flto` 性能倒退，`-O3 -flto -ljemalloc` 性能没啥变化，开 `-O3 -march=native -flto -ljemalloc` 性能进一步倒退。但是，LLVM 22 异军突起，以接近两倍的性能超越了 GCC 和 LLVM 的其他版本，仅用 50.5s 跑完，对应 10.6 分。可以说，完全就靠 750.sealcrypto_r，才让 LLVM 22 在 SPEC INT 2026 整体性能上超越了 GCC 14。下面就来看看是怎么一回事。

首先还是对 `-O3` 的 GCC 14 进行热点分析：

- `seal::util::DWTHandler::transform_to_rev(ValueType *values, int log_n, const RootType *roots, const ScalarType *scalar = nullptr)` 来自 `src/seal/util/dwthandler.h`：25.65%，这里 DWT 是离散小波变换 Discrete Wavelet Transform，上一次看到小波变换还是 Ghost Hunter，没想到在这里又遇到了，具体到指令上，就是一堆 imul/add/shr/shl 的运算指令
- `seal::util::DWTHandler::transform_from_rev(ValueType *values, int log_n, const RootType *roots, const ScalarType *scalar = nullptr)` 来自 `src/seal/util/DWTHandler.h`：16.58%，应该是 DWT 的逆过程，计算模式基本一样
- `seal::util::multiply_uint64_generic(T operand1, S operand2, unsigned long long *result128)` 来自 `src/seal/util/uintarith.h`：11.60%，实现了 64 位乘以 64 位得到 128 位结果的乘法，也是一堆乘法、加法和位运算
- `seal::util::dot_product_mod(const uint64_t *operand1, const uint64_t *operand2, size_t count, const Modulus &modulus)` 来自 `src/seal/util/uintarithsmallmod.cpp`：11.48%，实现的是点乘后取模的操作，调用 `multiply_accumulate_uint64` 函数进行乘法和累加，最后用 `barrett_reduce_128` 进行取模
- `seal::util::dyadic_product_coeffmod(ConstCoeffIter operand1, ConstCoeffIter operand2, size_t coeff_count, const Modulus &modulus, CoeffIter result)` 来自 `src/seal/util/polyarithsmallmod.cpp`：9.08%，实现的是 element wise 的模乘
- `seal::util::BaseConverter::fast_convert_array(ConstRNSIter in, RNSIter out, MemoryPoolHandle pool)` 来自 `src/seal/util/rns.cpp`：5.88%，这里的 RNS 应该是 Residue Number System 的缩写，指令上还是大量的 imul/add 等运算
- `seal::util::RNSTool::sm_mrq(ConstRNSIter input, RNSIter destination, MemoryPoolHandle pool)` 来自 `src/seal/util/rns.cpp`：5.40%，不确定在做什么，也是大量的运算

总而言之，既然是密码学，就会有大量的整数运算，其中有不少的乘法和位运算，在素数域下做各种操作。执行指令数足足有 3113.4B，其中有 79B 条分支指令，386B 条 Load，161B 条 Store，错误预测 449M 次，MPKI 只有 0.14，全场最低，甚至低于 714.cpython_r，同时 IPC 全场最高，达到了 5.09。从 Top down 分析来看，80.7% 属于 Retiring，13.5% 属于 Backend Bound，说明处理器基本在全速跑指令。

开了 `-O3 -march=native` 后，确实生成了不少 AVX2 指令，但看下来，生成的指令序列还是挺复杂的，有大量的 vpunpcklqdq/vpunpckhqdq/vpermq/vpblendvb/vperm2i128 等指令，并没有在进行的计算，而是在不断地倒腾向量寄存器里数据的位置。虽然指令数减少了，但 IPC 降低更多，最后性能反而倒退，实际从 108s 增加到 116s。原来的 `-O3` 版本虽然每次只处理一个元素，但指令的并行度更高，IPC 弥补了指令数多的劣势。

那么，LLVM 22 做了什么优化呢？执行的指令数直接降低到 1214B，分支只有 57.2B。以 `seal::util::DWTHandler::transform_to_rev` 为例，可以看到：seal 为了实现 64 位乘 64 位到 128 位的乘法，它自己实现了这个过程，不仅在 `seal::util::multiply_uint64_generic` 中有实现，实际上也内联到了 `seal::util::DWTHandler::transform_to_rev` 当中；GCC 14 忠实地实现了这个算法，因此指令数很多（见 [Godbolt](https://godbolt.org/z/KKTa1aMP8)）；但其实，AMD64 的 mul 指令本来就是一个 64 位乘 64 位得到 128 位的乘法，所以 LLVM 22 直接识别出这段代码做的事情，然后编译成了 mul 指令（见 [Godbolt](https://godbolt.org/z/bc6xPjEMc)，甚至如果开了 BMI2 扩展，还有 [mulx](https://www.felixcloutier.com/x86/mulx) 指令可以用），而且这种 64 位乘法保留高位的指令在各种 ISA 都挺常见的，比如 ARM64 的 umulh，RISC-V 的 mulhu，LoongArch 的 mulh.du。当然，seal 的源码其实已经考虑了这个问题，在编译器支持的情况下，直接用 __int128 来完成[这件事情](https://github.com/microsoft/SEAL/blob/e3476fad1d5bb5e5222c51a551b5a4d7e2cb4f91/native/src/seal/util/gcc.h#L44)。然而，这类依赖编译器行为或具体指令集扩展的代码，由于 SPEC CPU 2026 的编译器中立性，都被去掉了，都会回落到最通用的写法上。此时，就只能依赖编译器去自己识别和优化了。

但是，这样某种意义上也无法反映真实场景中的应用优化情况了，因为很多应用已经实际上和处理器的指令集扩展/编译器扩展共进化，实现的时候，脑子里是默认有这些东西，再去做的调优，甚至会写一些指令集相关的优化，用一些 intrinsics，比如原版 stockfish 就有针对 AVX512/AVX2/SSSE3/NEON_DOTPROD/LASX/LSX 的[优化](https://github.com/official-stockfish/Stockfish/blob/77a8f6ccf31846d63452f79e143fbc6dc62ae3a8/src/nnue/layers/affine_transform.h#L201)。到最后，就是编译器又实现各种 pass，识别程序里的 fallback generic 代码，再映射回高效的实现。其实类似的事情之前就出现过，网上用来证明编译器很聪明的一个例子，就是说识别 popcount 的循环，直接翻译成 popcnt 指令，然而很多程序直接用 `__builtin_popcount` 而不会真的去手写，这次只不过是换了个 pattern 罢了。当然，好消息是，C++20 引入了 std::popcount，可以一定程度避免类似的情况发生，只是来得太晚了。

相比之下，Geekbench 对这类指令集扩展的优化就比较持开放态度，愿意针对指令集扩展进行针对性的优化，比如经典引入 AMX/SME 对分数的巨大影响，当然这也让它被人骂 AppleBench，只能说见仁见智了。

### 753.ns3_r

753.ns3_r 和 710.omnetpp_r 做的事情类似，也是网络中的离散事件模拟器。它包括这些命令：

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

六条命令的耗时分别为 18s、15s、3s、19s、23s 和 14s，一共 92s，reftime 是 613s，对应 6.7 分。各编译选项对性能影响：

- `-O3 -flto`：时间降到 16s、14s、3s、17s、19s 和 13s，一共 82s，对应 7.5 分，相比 `-O3` 提升 12% 的性能
- `-O3 -flto -ljemalloc`：时间进一步降到 14s、12s、3s、13s、18s 和 11s，一共 71s，对应 8.6 分，相比 `-O3 -flto` 又提升 15% 性能

都有巨大提升，只有 `-march=native` 影响很小，仅 0.5%。下面来进行具体的分析。

#### mobile

热点分析：

- `cfree/malloc/_int_malloc/_int_free_chunk/operator new` 来自 libc/libstdc++：6.99%+5.66%+4.15%+1.83%+1.81%=20.44%，又是内存分配密集型应用
- `ns3::LteMiErrorModel::GetTbDecodificationStats(const SpectrumValue& sinr, const std::vector<int>& map, uint16_t size, uint8_t mcs, HarqProcessInfoList_t miHistory)` 来自 `src/ns-3.38/src/lte/model/lte-mi-error-model.cc`：9.57%，首先是一个循环，带有一些浮点运算，做一些累加和乘加操作，然后是一段二分查找，看起来主要瓶颈是在二分查找上面，此外在函数开头还会调用下面的 `Mib` 函数
- `ns3::LteMiErrorModel::Mib(const SpectrumValue& sinr, const std::vector<int>& map, uint8_t mcs)` 来自 `src/ns-3.38/src/lte/model/lte-mi-error-model.cc`：4.39%，又是一些浮点运算，不知道在算什么
- `ns3::LteMiErrorModel::MappingMiBler(double mib, uint8_t ecrId, uint16_t cbSize)` 来自 `src/ns-3.38/src/lte/model/lte-mi-error-model.cc`：3.53%，主要的开销是调用 erf 函数和做一些查表，`__erf` 函数占了总时间的 1.63%
- `ns3::MapScheduler::Insert(const Event& ev)` 来自 `src/ns-3.38/src/core/model/map-scheduler.cc`：2.66%，对 `std::map` 红黑树的插入

首先能看到的是，又是一个内存分配密集型应用。开了 `-O3 -flto` 后，`GetTbDecodificationStats` 把 `Mib` 内联了进去，时间占比提升到 12.68%，但还是内存分配占了最多的时间：7.82%+6.22%+4.51%+1.90%=20.45%。进一步开 `-O3 -flto -ljemalloc`，内存分配的时间占比终于降低到 6.23%+1.78%=8.01%，其实还是挺高的。

比较少见的是，作为 SPEC INT 2026 Rate 的一员，mobile 涉及不少浮点运算，还包括一些对 libm 的调用，比如 erf/atan2/pow/log，但实际瓶颈又是内存分配，属于是半步踏入了 SPEC FP 2026，又被 libc 退了回来。

`-O3` 下，执行指令 257B，其中分支指令有 54B，错误预测 627M，MPKI 等于 `627M/257B*1000=2.43`，并不低。

#### tcp

第二条命令测的又是不一样的代码了，这次的热点函数：

- `cfree/malloc/_int_malloc/_int_free_chunk/operator new` 来自 libc/libstdc++：7.02%+5.20%+3.68%+2.29%+1.56%=19.75%，又是内存分配密集型应用
- `ns3::TcpTxBuffer::NextSeg(SequenceNumber32* seq, SequenceNumber32* seqHigh, bool isRecovery)` 来自 `src/ns-3.38/src/internet/model/tcp-tx-buffer.cc`：4.35%，是一个 TCP 协议栈实现，这里做的是 RFC 6675 SACK 的部分，想起来之前设计的 [TCP 实验](https://lab.cs.tsinghua.edu.cn/tcp/doc/)，这里主要的瓶颈是循环里对 sequence number 的更新
- `ns3::MapScheduler::Insert(const Event& ev)` 来自 `src/ns-3.38/src/core/model/map-scheduler.cc`：4.05%，描述见上
- `__do_dyncast/__dynamic_cast` 来自 libstdc++：1.80%+1.55%=3.35%

`-O3` 下，执行指令 205B，其中分支指令有 45B，错误预测 148M，MPKI 等于 `148M/205B*1000=0.72`，比较低。

#### lena

第三条命令测的又是不一样的代码了，这次的热点函数：

- `cfree/malloc/_int_malloc/_int_free_chunk/operator new` 来自 libc/libstdc++：7.78%+6.13%+3.13%+2.08%+1.52%=20.64%，又是内存分配密集型应用
- `ns3::MapScheduler::Insert(const Event& ev)` 来自 `src/ns-3.38/src/core/model/map-scheduler.cc`：2.41%，描述见上
- `__do_dyncast/__dynamic_cast` 来自 libstdc++：1.73%+0.82%=2.55%

`-O3` 下，执行指令 467B，其中分支指令有 10B，错误预测 52M，MPKI 等于 `52M/467B*1000=0.11`，非常低。

#### dctcp

第四条命令测的又是不一样的代码了，这次的热点函数：

- `cfree/malloc/_int_malloc/_int_free_chunk/operator new` 来自 libc/libstdc++：6.30%+5.56%+4.03%+1.53%+1.43%+1.12%=40.61%，又是内存分配密集型应用
- `ns3::MapScheduler::Insert(const Event& ev)` 来自 `src/ns-3.38/src/core/model/map-scheduler.cc`：6.94%，描述见上

`-O3` 下，执行指令 225B，其中分支指令有 52B，错误预测 295M，MPKI 等于 `295M/225B*1000=1.31`，略高一点。

#### wifi_mixed

热点函数就不列举了，基本还是内存分配，外加 `ns3::TcpTxBuffer::NextSeg`。`-O3` 下，执行指令 292B，其中分支指令有 67B，错误预测 202M，MPKI 等于 `202M/292B*1000=0.69`，不高。

#### wifi_eht

热点函数除了内存分配，多了 `ns3::InterferenceHelper::AppendEvent` 和 `ns3::WifiSpectrumValueHelper::GetBandPowerW`。`-O3` 下，执行指令 194B，其中分支指令有 44B，错误预测 371M，MPKI 等于 `371M/194B*1000=1.91`，略高。

#### 小结

与 727.cppcheck_r 类似，753.ns3_r 又是一个内存分配器 benchmark，大量时间花在 malloc/free 上了，此外还有不少 std::map 或 libm 的调用。`-O3` 下，执行指令 1221B，分支指令 273B，MPKI 是 1.39。

### 777.zstd_r

作为 SPEC INT 2026 中唯一一个压缩算法，把 SPEC INT 2017 的 557.xz_r 替换掉了，也能见到压缩算法的变迁。从没有被选中的 770.7z_r 来看，zstd 也是成功杀出重围，被认为是更加重要的压缩算法。它一共包括八条命令，但其实压缩的都是同一个文件，不像 557.xz_r 那样会压缩不同的输入文件，只是在代码里对输入数据做了随机修改：

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

这里的 `-b` 代表 compression level 下界，`-e` 代表 compression level 上界，都相等，其实就是每次只测一种 compression level 的意思。8 条命令的运行时间：11.0s、14.5s、13.0s、11.6s、24.5s、10.9s、20.1s 和 25.5s，一共是 131.2s，reftime 是 644s，对应 4.9 分。

开 `-O3 -flto` 或 `-O3 -ljemalloc` 没有什么性能提升，但 `-O3 -march=native` 提升不错，运行时间降低到 10.5s、13.7s、12.6s、11.4s、23.4s、10.3s、18.6s 和 23.5s，一共是 124.0s，对应 5.2 分，提升 6%。

以第一条命令 b3 为例，热点函数：

- `ZSTD_compressBlock_doubleFast_noDict_generic` 来自 `src/zstd-1.5.6/lib/compress/zstd_double_fast.c`：56.82%，主要在对数据计算哈希，寻找匹配，进而用于压缩，具体算法没有仔细看
- `ZSTD_decompressBlock_internal.part.0` 来自 `src/zstd-1.5.6/lib/decompress/zstd_decompress_block.c`：16.63%，解压缩的主要逻辑，会调用 `ZSTD_decompressSequences`，挺复杂的
- `ZSTD_encodeSequences` 来自 `src/zstd-1.5.6/lib/compress/zstd_compress_sequences.c`：10.91%，分为 bmi2 和 generic 版本，不出意外 bmi2 版本也被 SPEC 禁用了，只能用 generic 版本，逻辑也挺复杂的，没有仔细看

`-O3` 下，b3 执行 183B 条指令，其中有 19B 分支指令，错误预测 546M 次，MPKI 等于 `546M/183B*1000=2.98`，属于比较高的。

第二条命令 b5 的热点函数：

- `ZSTD_RowFindBestMatch.constprop.0` 来自 `src/zstd-1.5.6/lib/compress/zstd_lazy.c`：67.91%，对数组进行循环，找到匹配最长的一项
- `ZSTD_compressBlock_lazy_generic.constprop.0` 来自 `src/zstd-1.5.6/lib/compress/zstd_lazy.c`：9.12%，也是比较复杂的匹配算法
- `ZSTD_decompressBlock_internal.part.0` 来自 `src/zstd-1.5.6/lib/decompress/zstd_decompress_block.c`：7.80%，描述见上

`-O3` 下，b5 执行 274B 条指令，其中有 28B 分支指令，错误预测 563M 次，MPKI 等于 `563M/274B*1000=2.05`，属于比较高的。

第五条命令 b14 的热点函数：

- `ZSTD_DUBT_findBestMatch` 来自 `src/zstd-1.5.6/lib/compress/zstd_lazy.c`：85.74%，也是在循环中做最长匹配
- `ZSTD_searchMax.constprop.0` 来自 `src/zstd-1.5.6/lib/compress/zstd_lazy.c`：9.04%，根据 dict mode 派发到不同的实现，实现也挺复杂

`-O3` 下，b14 执行 198B 条指令，其中有 29B 分支指令，错误预测 1608M 次，MPKI 等于 `1608M/198B*1000=8.12`，属于特别高的。

第六条命令 b16 的热点函数：

- `ZSTD_insertBtAndGetAllMatches` 来自 `src/zstd-1.5.6/lib/compress/zstd_opt.c`：38.62%，这里 Bt 代表的是 binary tree 二叉树
- `ZSTD_insertBt1` 来自 `src/zstd-1.5.6/lib/compress/zstd_opt.c`：35.15%
- `ZSTD_compressBlock_opt_generic.constprop.1` 来自 `src/zstd-1.5.6/lib/compress/zstd_opt.c`：16.50%

`-O3` 下，b16 执行 129B 条指令，其中有 18B 分支指令，错误预测 652M 次，MPKI 等于 `652M/129B*1000=5.05`，属于特别高的。

第三/四条命令 b7/b10 的热点与第二条命令 b5 类似；第七/八条命令 b18/b19 的热点函数和第六条命令 b16 类似，就不重复了。可见 zstd 会根据 compression level 选择不同路径，从而在压缩率和性能之间做出权衡。

那么开 `-march=native` 以后，发生了什么？能看到的是，由于 BMI 指令的引入，一些位运算的指令数变少了，比如 [bzhi](https://www.felixcloutier.com/x86/bzhi) 和 [tzcnt](https://www.felixcloutier.com/x86/tzcnt)，还有一些是三操作数且不影响 flags 的运算，如 [shrx](https://www.felixcloutier.com/x86/bzhi)，有点类似一些 RISC 指令集（如 RISC-V）的对应指令。

整体来看，`-O3` 下 777.zstd_r 执行 1827B 指令，其中 232B 是分支指令，但 MPKI 有 3.58，仅次于 729.abc_r 和 723.llvm_r。

## 讨论

### 编译器选项对比

综合下来，编译选项对 SPEC INT 2026 Rate 的性能影响还是不小的，比如：

- `-flto` 对 707.ntest_r、710.omnetpp_r、714.cpython_r、734.vpr_r、735.gem5_r、753.ns3_r 都有一定的性能提升，凡是热点分散在多个函数，且很多函数都很小的时候，开 LTO 能一定程度上带来优化，本质上就是挽回了因可读性而拆分文件带来的性能开销
- `-ljemalloc` 对 710.omnetpp_r、721.gcc_r、723.llvm_r、727.cppcheck_r、734.vpr_r、735.gem5_r、753.ns3_r 有性能提升，只能说这些软件做了太多的动态内存分配，有一些 benchmark 直接就是内存分配器 benchmark 了，此时替换 glibc 为 jemalloc/mimalloc 都有不错的性能提升，不过最新 glibc 也在改进 malloc 性能，不知道改进得怎样了？
- `-march=native` 对 706.stockfish_r、707.ntest_r、735.gem5_r、777.zstd_r 有不错的提升，一方面是诸如 AVX 等 SIMD 指令，另一方面就是一些位运算指令，比如 popcnt 和 BMI 扩展；事实上，现在很多软件在实现的时候，就已经考虑了硬件的加速指令，实际编译的时候，往往会直接用对应的 intrinsics，但 SPEC 禁用了这些 intrinsics，退而使用它的 generic 版本，此时就非常依赖 -march=native，以及需要编译器正确识别并翻译为对应的优化指令

还有一些常用的编译参数，比如 `-static`、`-fomit-frame-pointer`、`-Ofast`、`-ffast-math` 等等，目前没有做太多测试，以后说不定会加上。

### 编译器版本对比

本测试的主要编译器是 GCC 14.2.0，因为它是 Debian Trixie 的编译器版本。有意思的是，即使在 2026 年，随着编译器版本更新，硬件不变的情况下软件性能还在持续增长。GCC 15 能给 706.stockfish_r 生成更快的 SSE/AVX 指令序列，LLVM 22 能识别出 750.sealcrypto_r 的 64 位乘法模式，这些都是很好的例子。此外 LLVM 默认内联 popcount 的优化实现，而 GCC 会转化为对 libgcc 的 popcount 调用，前者代码体积膨胀，后者有额外的 call 开销，这些都会带来可观的性能差距。这些优化其实很具体，完全可以互相移植。在 SPEC INT 2017 时代，基本是 GCC 性能压制 LLVM，而目前 LLVM 凭借 750.sealcrypto_r 的优化相比 GCC 14 扳回一城，又被 GCC 15/16 反超。随着对 SPEC CPU 2026 的研究深入，未来还会编译出更快的程序。

### 分支预测

SPEC INT 2026 Rate 中 MPKI 较高的有：

- 723.llvm_r MPKI=5.98
- 729.abc_r MPKI=3.87
- 777.zstd_r MPKI=3.58
- 721.gcc_r MPKI=3.37
- 734.vpr_r MPKI=2.52
- 707.ntest_r MPKI=2.27
- 735.gem5_r MPKI=2.05

作为对比，SPEC INT 2017 Rate 的情况：

- 505.mcf_r MPKI=14.39
- 541.leela_r MPKI=12.62
- 557.xz_r MPKI=5.29
- 531.deepsjeng_r MPKI=4.40
- 520.omnetpp_r MPKI=4.33
- 502.gcc_r MPKI=3.13

SPEC INT 2026 Rate 整体低了不少。当然，这是每个 benchmark 的平均值，个别子命令可能更高。但无论如何，终于不用和 505.mcf_r 的 `spec_qsort` 以及 541.leela_r 的 `if(randint(2) == 0)` 搏斗了。

### 局限性

目前的测试仅限于 Intel i9-14900K P-Core，还需要在 ARM64/RISC-V/LoongArch 上做类似的分析。指令集不同，结论应该也会不一样。此外，目前的分析集中在 perf 统计的热点函数上，还可以做更细粒度的分析，比如统计各类指令的使用比例，以及 POPCNT/BMI/AVX 等指令扩展的使用情况。

本文只跑了 Rate 1（单副本）。多副本下内存带宽和缓存竞争会更激烈，MPKI、IPC 等指标可能会有较大差异。此外，分析集中在指令级和分支预测层面，缺少微架构级的深入分析，例如 L1/L2/LLC 的缓存缺失率、TLB miss 等，这些对处理器设计者来说更直接。功耗数据也未纳入考量，综合能效比还需要用 RAPL 等工具进一步测量。最后，PGO（`-fprofile-generate` / `-fprofile-use`）也没有尝试，PGO 或许能带来不错的性能提升。

## 总结

本文深入分析了 SPEC CPU 2026 中 INT Rate 的负载，供编译器和处理器的设计者参考。从编译器的角度来说，可以集 GCC 和 LLVM 之长，进一步提升性能；从处理器的角度来说，针对程序的瓶颈进行优化，也能进一步提高分数。
