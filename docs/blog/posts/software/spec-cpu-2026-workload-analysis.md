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

stockfish 是一个著名的国际象棋引擎，测试会用如下三种参数分别运行：

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

`-O3` 编译选项下，1to6_classical 执行的指令数为 532.9B，其中分支指令有 56.1B 次，其中有 2.6B 次错误预测。可见，1to6_classical 的 MPKI 还是比较高的：`2.6B/532.9B*1000=4.88`，即使是在 SPEC INT 2017 当中，也是比较高的，高于 531.deepsjeng_r 的 3.16 和 557.xz_r 的 3.49，低于 505.mcf_r 的 6.24 和 541.leela_r 的 7.71。

#### 1to6_nnue

后两个命令的引擎从 classical 变为了 nnue，涉及神经网络，因此它的计算模式会不太一样。通过 `perf` 观察到 1to6_nnue 的主要耗时函数：

- `Stockfish::Eval::NNUE:evaluate(const Position& pos, bool adjusted)` 来自 `src/nnue/evaluate_nnue.cpp`：80.26%，主要耗时在 `affine_transform_non_ssse3` 的 `sum += weights[offset + j] * input[j]`，即神经网络的推理过程，它的计算过程是，进行 int8_t 乘 uint8_t，再累加到 int32_t 类型的结果，默认编译选项下，只能用基础的 SSE 指令如 pmaddwd/paddd，而不能用 AVX
- `Stockfish::TranspositionTable::probe(const Key key, bool& found)` 来自 `src/tt.cpp`: 仅 5.27%，瓶颈和前面分析的一样是随机访存

分析 `Stockfish::Eval::NNUE:evalute` 的指令，可以看到，它为了实现上述逻辑，核心思路是采用 pmaddwd 指令，进行 4 次 16 位有符号的乘法计算，累加到 32 位的结果。但是，在这之前，需要先把输入的 8 位有符号 weights 和无符号 input 转换到 16 位有符号数。其中 8 位有符号 weights 转换比较简单，而 8 位无符号 weights 的处理逻辑比较复杂。首先，它对 input 的每个元素加上 128，然后当成有符号数来看待，这相当于对每个元素减去了 128，把 uint8_t 映射到了 int8_t。这样，input 就可以用和 weights 相同的方法进行符号扩展。但是，这样会导致结果计算错误，为了纠正这个偏差，又减去了 128 倍的 weights 之和。[汇编代码](https://godbolt.org/z/ox7q63Er8)如下：

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

经验告诉我们，对于这种适合 SIMD 的代码，在开了 `-march=native` 的情况下应当有明显的性能提升，实际测试也证明了这一点，开了 `-march=native` 后，时间从 73s 降低到 30s，`Stockfish::Eval::NNUE::evaluate` 时间占比降到 53.84%，此时主要的计算指令变为 [vpdpbusd (Multiply and Add Unsigned and Signed Bytes)](https://www.felixcloutier.com/x86/vpdpbusd)，即针对字节（weights 数组元素是 int8_t 类型，input 数组元素是 uint8_t 类型）元素的整数乘加融合指令，和的类型是 int32_t。[核心循环](https://godbolt.org/z/zoeqc4zch)如下：

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

需要注意的是，单纯开 `-mavx2` 还是需要执行 70s，即使开启了 AVX，由于没有开 AVX-VNNI，不能用 vpdpbusd，还是需要先格式转换到 16 位，再用 32 位累加器的 16 位整数乘加指令。可以说，Stockfish 的 NNUE 这样的计算方式，就是奔着 vpdpbusd 这条指令去的。所以一些没有这种计算的 ISA，就会比较吃亏。

例如在 ARM64 下，对应的 [USDOT (Dot product with unsigned and signed integers (vector))](https://developer.arm.com/documentation/ddi0487/maa/-Part-C-The-AArch64-Instruction-Set/-Chapter-C7-A64-Advanced-SIMD-and-Floating-point-Instruction-Descriptions/-C7-2-Alphabetical-list-of-A64-Advanced-SIMD-and-floating-point-instructions/-C7-2-448-USDOT--vector-) 指令被包括在 i8mm 扩展当中，[有这个扩展](https://godbolt.org/z/MxY3YYTYo)的话，`-march=native` 性能提升显著，例如 Apple M2；而如果[没有这个扩展](https://godbolt.org/z/TfdvW4f75)，开不开 `-march=native` 就没什么区别，例如 Apple M1，此时就要回退到类似 AMD64 那样，先扩展到 16 位，再求和。RISC-V Vector 指令集扩展则有 vwmulsu.vv 指令可以[使用](https://godbolt.org/z/ha5oEb4hE)，得到 16 位乘法结果之后，再用 vwadd.wv 指令累加到 32 位。LoongArch 也有对应的 xvmulwev.h.b/xvmulwod.h.b [指令](https://godbolt.org/z/xxr5rovxW)，得到 16 位乘法结果之后，用 xvhaddw.w.h 指令累加到 32 位。

除了是否开启对应指令集扩展以外，还观察到 GCC 15/16 在 1to6_nnue 上相比 GCC 14 有明显的性能提升（编译选项为 `-O3`），时间从 73s 降低到了 50s。观察生成的指令，虽然它还是用的 SSE 指令，但[指令序列](https://godbolt.org/z/exKaP5jKb)更简洁：

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

可见，即使没有对口的 vpdpbusd 指令，仅用 SSE 还是有优化空间的，通过用 SSE 实现高效的有符号和无符号符号扩展，获得了介于 GCC 14 比较差的指令序列与专用 vpdpbusd 指令的性能。

`-O3` 编译选项下，1to6_nnue 执行的指令数为 1342B，其中分支指令有 77.6B 次，其中有 1.6B 次错误预测。它的 MPKI 只有 `1.6B/1342B*1000=1.19`，主要瓶颈还是在上述的神经网络推理当中。

#### 7to11_nnue

7to11_nnue 的行为与 1to6_nnue 类似，瓶颈也是在 `Stockfish::Eval::NNUE:evaluate` 函数上。开启 `-march=native` 后，时间从 68s 降到了 30s。GCC 15/16 的性能提升也和 1to6_nnue 类似。`-O3` 编译选项下，7to11_nnue 执行的指令数为 1253B，其中分支指令有 75.5B 次，其中有 1.5B 次错误预测。它的 MPKI 只有 `1.5B/1253B*1000=1.20`，主要瓶颈还是在神经网络推理当中。

#### 小结

1to6_classical 比较像传统的各种棋类引擎，有比较复杂的分支和访存，所以它的 MPKI=4.88 比较类似 SPEC CPU 2017 的 531.deepsjeng_r（MPKI=3.16），属于比较高的一类。而 1to6_nnue 和 7to11_nnue 的主要瓶颈在于 i8 的矩阵运算，能否使用硬件的加速指令则对性能至关重要，分支预测瓶颈就明显小了。整体平均下来的 MPKI 是 1.85，并不算高。

### 707.ntest_r

ntest 是黑白棋的引擎，测试会用如下参数运行：

```shell
ntest Othello.154.ggf 20 16
```

实测数据显示，运行这条命令耗费的时间是 133s。reftime 是 592s，对应 4.5 分。开启各项优化编译选项，`-flto` 带来 4% 的性能提升，进一步开启 `-march=native` 带来 10% 的性能提升。下面分析它的具体负载特性。通过 `perf` 观察性能瓶颈，这几个函数耗费的时间占比较多：

- `flips(int sq, u64 mover, u64 enemy)` 来自 `src/flips.cpp`：34.73%，最主要的开销，根据棋盘状态，经过一系列的访存和位运算，判断下子以后是否出现翻转，主要是一些数据依赖的访存
- `solveNParity(int alpha, int beta, u64 mover, u64 enemy, u64 parity, EndgameSearch* search, bool hasPassed)` 来自 `src/solve.cpp`：14.29%，进行 alpha-beta 减枝的 minimax 算法，遍历棋盘上的位置，如果可以下子，就尝试下子进行递归，主要的瓶颈在访存以及依赖访存结果的分支（如判断位置是否为空）
- `__popcountdi2`：9.65%，因为没开 `-march=native`，故需要它来代替 popcnt 指令，用来计算场面上各颜色棋子的数量等等
- `solveNFlipParity`：9.00%，与 solveNParity 配合完成 minimax 算法
- `solve2`：5.42%，minimax 算法的一部分，处理棋盘只有两个空位的最终局面

这也是个比较典型的棋类引擎的模式了，整个 minimax 算法占了 70%+ 的时间，为了搜索局面，有大量的位运算和访存，还有根据访存结果决定方向的分支。果不其然，执行 2688B 条指令，其中有 228B 条是分支指令，有 6.1B 次错误预测，MPKI 达到了 `6.1B/2688B*1000=2.27`。和 706.stockfish_r 类似，它也有不少的 popcnt 调用，那么打开 `-mpopcnt` 就会得到不错的性能提升：时间从 133s 降低到 120s，减少 10% 时间。而即使开 `-march=native`，性能也只是进一步降到 116s，只有少量的地方用到了 AVX2。

另一方面，LLVM 22 的性能在 707.ntest_r 上比 GCC 14 要快：同样是 `-O3` 的编译选项，运行时间从 133s 降低到 120s。深入研究汇编发现，LLVM 22 在没有开 `-mpopcnt` 的时候，它的行为是，直接把类似 libgcc 的 `__popcountdi2` 的代码内联到了程序当中，省去了 call libgcc 的开销，不过代价就是代码体积会增加。

同时，GCC 15 相比 GCC 14 也有约 10% 的性能提升，运行时间从 133s 降低到了 123s。分析汇编，发现主要优化点在 `flips(int sq, u64 mover, u64 enemy)` 函数当中。性能区别有两点：

1. 首先是对 callee-saved 寄存器的使用，GCC 14 会在 epilogue/prologue 直接进行一系列的 push/pop，而 GCC 15 更加聪明，仅在 `if (neighbors[sq]&enemy)` 条件成立的情况下，需要执行复杂函数体，需要 callee-saved 寄存器时才会进行 push/pop，否则就直接 ret，因为检查条件的时候并没有用到 callee-saved 寄存器，避免了保存和恢复。
2. 自己编译的 GCC 15 默认是 -no-pie 模式，而发行版的 GCC 14 默认是 -pie，而 -no-pie 模式因为采用绝对地址，可以在 imul 等指令的操作数直接访问内存，节省寄存器，于是 callee-saved register 就都可以不用了，开启 -static 也能带来类似的效果。上面的第一条分析是手动给 GCC 15 开 -pie 后观察到的。不过主要的性能提升还是来自于减少 push/pop 的执行次数。

结合 706.stockfish_r 和 707.ntest_r，可以看到，popcnt 还是比较常用的，但可惜 AMD64 的基线并不提供这条指令，因此如果开了 x86-64-v2 或以上的编译优化选项，这类应用就可以获得性能提升，免去了 libgcc 的 __popcountdi2 开销，本来一条指令就能完成的事情，因为额外的 call 以及 PLT 开销，带来了可观的性能开销。期待一个优雅的解决方法。

### 708.sqlite_r

sqlite 就是大名鼎鼎的数据库了，不必多介绍。测试中，又是包括三条命令：

```shell
# 1. main
sqlite --memdb --size 2000 --testset main --verify
# 2. cte
sqlite --memdb --size 2000 --testset cte --verify
# 3. fp
sqlite --memdb --size 1000 --testset fp --verify
```

实测数据显示，三条命令耗费的时间分别是 65s、12s 和 24s，共计 101s。reftime 是 528s，对应 5.2 分。开启 -flto/-ljemalloc 对性能影响很小，-march=native 甚至带来了负优化。下面分别分析这三条命令的具体性能特性。

## SPEC FP 2026 Rate

TODO

## 总结

本文对 SPEC CPU 2026 的负载进行了深入的分析，以供编译器和处理器的设计者参考。从编译器的角度来说，可以集 GCC 和 LLVM 之长，进一步提升性能；从处理器的角度来说，针对程序的瓶颈进行优化，也能进一步提高分数。
