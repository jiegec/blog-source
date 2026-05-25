---
layout: post
date: 2026-05-21
tags: [benchmark,spec]
draft: true
categories:
    - software
---

# SPEC CPU 2026 负载特性分析（INT Rate 篇）

## 背景

最近用 SPEC CPU 2026 跑了一些测试，打算结合[测试结果](../../../benchmark/spec-cpu-2026-rate.md)做一些深入的负载特性分析。本篇主要是分析 SPEC INT 2026 Rate 的负载特性。

<!-- more -->

本文测试环境：CPU 为 Intel i9-14900K P-Core @ 5.7 GHz，Linux 发行版为 Debian Trixie，编译器是 GCC 14.2.0，默认编译选项是 `-O3`。其实这款 CPU 最快能 Boost 到 6.0 GHz，但是时不时因为未知原因（防缩缸？）在只有单核负载的情况下也 Boost 不上去，现象是每跑一段时间负载，CPU 核心就会强制降频到 4.7 GHz，故退而求其次，选择在更容易稳定达到的 5.7 GHz 频率来跑，因为能跑 6.0 GHz 的就是那一个物理 P 核，其他的物理 P 核都能上 5.7 GHz，降频了只要换一个就好。6.0 GHz 下的性能可以参考之前的测试结果：[INT](../../../benchmark/data-trixie/int2026_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt) 和 [FP](../../../benchmark/data-trixie/fp2026_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt)，基本上，从 5.7 GHz 到 6.0 GHz，性能可以按频率线性放缩。

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

实测数据显示，三条命令耗费的时间分别是 47s、77s 和 72s，共计 196s。reftime 是 1260s，对应 6.4 分。开启 `-march=native` 后，1to6_classical 时间缩短 10% 到 43s，而 1to6_nnue 和 7to11_nnue 时间明显缩短到 32s 和 31s，总时间 105s，对应 12 分，分数提升显著。下面分别分析这三条命令的具体性能特性。

#### 1to6_classical

通过 `perf` 观察性能瓶颈，运行第一个命令 1to6_classical 时，这几个函数耗费的时间占比较多，百分比代表这个函数执行时间的占比，后续都用这个方法表示：

- `Stockfish::TranspositionTable::probe(const Key key, bool& found)` 来自 `src/tt.cpp`: 19.26%，主要的瓶颈来自于随机访存，在 `first_entry(key)` 当中有 `&table[mul_hi64(key, clusterCount)].entry[0]`，其中 mul_hi64 计算两个 64 位整数乘法结果的高 64 位，因此访存地址是根据参数计算得出
- `Stockfish::Eval::evaluate(const Position& pos)` 来自 `src/evaluate.cpp`: 17.23%，inline 了 `Evaluation<NO_TRACE>(pos).value()` 的调用，里面主要是对局面的评估，涉及比较多零散的访存和计算
- `Stockfish::MovePicker::next_move(bool skipQuiets)` 来自 `src/movepick.cpp`: 10.43%，里面比较慢的是 `partial_insertion_sort`
- `Stockfish::search(Position& pos, Stack* ss, Value alpha, Value beta, Depth depth, bool cutNode)` 来自 `src/search.cpp`: 9.52%，搜索逻辑主要在这里实现
- `__popcountdi2`: 7.60%，被 `Stockfish::Eval::evaluate(const Position& pos)` 调用，用来判断局面上满足某种条件

开了 `-march=native` 后，能观察到 `__popcountdi2` 被内联为 `popcnt` 指令。经过测试，开了 `-mpopcnt` 后，时间即从 47s 降低到 44s，接近 `-march=native` 的性能，可见在开启 popcnt 指令集的前提下，内联 `__popcountdi2` 调用就可以明显减少时间。

`-O3` 编译选项下，1to6_classical 执行的指令数为 532.9B，其中分支指令有 56.1B 次，其中有 2.6B 次错误预测。可见，1to6_classical 的 MPKI 还是比较高的：`2.6B/532.9B*1000=4.88`，即使是在 SPEC INT 2017 当中，也是比较高的，高于 531.deepsjeng_r 的 3.16 和 557.xz_r 的 3.49，低于 505.mcf_r 的 6.24 和 541.leela_r 的 7.71。

#### 1to6_nnue

后两个命令的引擎从 classical 变为了 nnue，涉及神经网络，因此它的计算模式会不太一样。通过 `perf` 观察到 1to6_nnue 的主要耗时函数：

- `Stockfish::Eval::NNUE:evaluate(const Position& pos, bool adjusted)` 来自 `src/nnue/evaluate_nnue.cpp`：80.59%，主要耗时在 `affine_transform_non_ssse3` 的 `sum += weights[offset + j] * input[j]`，即神经网络的推理过程，它的计算过程是，进行 int8_t 乘 uint8_t，再累加到 int32_t 类型的结果，默认编译选项下，只能用基础的 SSE 指令如 pmaddwd/paddd，而不能用 AVX
- `Stockfish::TranspositionTable::probe(const Key key, bool& found)` 来自 `src/tt.cpp`: 仅 4.81%，瓶颈和前面分析的一样是随机访存

分析 `Stockfish::Eval::NNUE:evalute` 的指令，可以看到，它为了实现上述逻辑，核心思路是采用 pmaddwd 指令，进行 4 次 16 位有符号的乘法计算，累加到 32 位的结果。但是，在这之前，需要先把输入的 8 位有符号 weights 和无符号 input 转换到 16 位有符号数。其中 8 位有符号 weights 转换比较简单，而 8 位无符号 weights 的处理逻辑比较复杂。首先，它对 input 的每个元素加上 128，然后当成有符号数来看待，这相当于对每个元素减去了 128，把 uint8_t 映射到了 int8_t。这样，input 就可以用和 weights 相同的方法进行符号扩展。但是，这样会导致结果计算错误，为了纠正这个偏差，又减去了 128 倍的 weights 之和。汇编代码如下（[Godbolt](https://godbolt.org/z/ox7q63Er8)）：

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

经验告诉我们，对于这种适合 SIMD 的代码，在开了 `-march=native` 的情况下应当有明显的性能提升，实际测试也证明了这一点，开了 `-march=native` 后，时间从 73s 降低到 32s，`Stockfish::Eval::NNUE::evaluate` 时间占比降到 54.20%，此时主要的计算指令变为 [vpdpbusd (Multiply and Add Unsigned and Signed Bytes)](https://www.felixcloutier.com/x86/vpdpbusd)，即针对字节（weights 数组元素是 int8_t 类型，input 数组元素是 uint8_t 类型）元素的整数乘加融合指令，和的类型是 int32_t。核心循环如下（[Godbolt](https://godbolt.org/z/zoeqc4zch)）：

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

需要注意的是，单纯开 `-mavx2` 仅能把时间从 77s 减少到 50s，距离 `-march=native` 的 32s 还有明显的差距，即使开启了 AVX（[Godbolt](https://godbolt.org/z/e9dPsqddh)），由于没有开 AVX-VNNI，不能用 vpdpbusd，还是需要先格式转换到 16 位，再用 32 位累加器的 16 位整数乘加指令。可以说，Stockfish 的 NNUE 这样的计算方式，就是奔着 vpdpbusd 这条指令去的。所以一些没有这种指令的 CPU，或者有但是编译器没用上，就会比较吃亏。

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

可见，即使没有对口的 vpdpbusd 指令，仅用 SSE 还是有优化空间的，GCC 15 通过用 SSE 实现高效的有符号和无符号符号扩展，获得了介于 GCC 14 比较差的指令序列与专用 vpdpbusd 指令的性能。这一点，在 [SPEC CPU2026: Characterization, Representativeness, and Cross-Suite Comparison](https://arxiv.org/abs/2605.03713v2) 论文中也有提及：`For example, gcc-15 reduces the instruction count of 706.stockfish_r by up to 3x`，不过这个数字是相比 GCC 13 的；相比 GCC 14 也有减少，不过没有那么明显，详情见论文中的 Figure 10 和 Figure 16，这里实测下来是从 GCC 14 的 1342B 条指令降低到 GCC 15 的 1015B。相比之下，LLVM 22 生成的 SSE（`-O3`，[Godbolt](https://godbolt.org/z/Tsd1YhrWe)）或 AVX（`-O3 -march=alderlake`，[Godbolt](https://godbolt.org/z/WM1xWjqc3)）指令都没有 GCC 15 高效。

`-O3` 编译选项下，1to6_nnue 执行的指令数为 1342B，其中分支指令有 77.6B 次，其中有 1.6B 次错误预测。它的 MPKI 只有 `1.6B/1342B*1000=1.19`，主要瓶颈还是在上述的神经网络推理当中。

#### 7to11_nnue

7to11_nnue 的行为与 1to6_nnue 类似，瓶颈也是在 `Stockfish::Eval::NNUE:evaluate` 函数上。开启 `-march=native` 后，时间从 72s 降到了 31s。GCC 15 的性能提升也和 1to6_nnue 类似。`-O3` 编译选项下，7to11_nnue 执行的指令数为 1253B，其中分支指令有 75.5B 次，其中有 1.5B 次错误预测。它的 MPKI 只有 `1.5B/1253B*1000=1.20`，主要瓶颈还是在神经网络推理当中。

#### 小结

1to6_classical 比较像传统的各种棋类引擎，有比较复杂的分支和访存，所以它的 MPKI=4.88 比较类似 SPEC CPU 2017 的 531.deepsjeng_r（MPKI=3.16），属于比较高的一类。而 1to6_nnue 和 7to11_nnue 的主要瓶颈在于 i8 的矩阵运算，能否使用硬件的加速指令则对性能至关重要，分支预测瓶颈就明显小了。整体平均下来的 MPKI 是 1.85，并不算高。

### 707.ntest_r

ntest 是黑白棋的引擎，测试会用如下参数运行：

```shell
ntest_r Othello.154.ggf 20 16
```

实测数据显示，运行这条命令耗费的时间是 140s。reftime 是 592s，对应 4.2 分。开启各项优化编译选项，`-O3 -flto` 相比 `-O3` 能带来 4% 的性能提升，进一步 `-O3 -flto -march=native` 相比 `-O3 -flto` 还能带来 10% 的性能提升。下面分析它的具体负载特性。通过 `perf` 观察性能瓶颈，这几个函数耗费的时间占比较多：

- `flips(int sq, u64 mover, u64 enemy)` 来自 `src/flips.cpp`：34.80%，最主要的开销，根据棋盘状态，经过一系列的访存和位运算，判断下子以后是否出现翻转，主要是一些数据依赖的访存
- `solveNParity(int alpha, int beta, u64 mover, u64 enemy, u64 parity, EndgameSearch* search, bool hasPassed)` 来自 `src/solve.cpp`：14.21%，进行 alpha-beta 减枝的 minimax 算法，遍历棋盘上的位置，如果可以下子，就尝试下子进行递归，主要的瓶颈在访存以及依赖访存结果的分支（如判断位置是否为空）
- `__popcountdi2`：9.65%，因为没开 `-march=native`，故需要它来代替 popcnt 指令，用来计算场面上各颜色棋子的数量等等
- `solveNFlipParity`：8.95%，与 solveNParity 配合完成 minimax 算法
- `solve2`：5.38%，minimax 算法的一部分，处理棋盘只有两个空位的最终局面

这也是个比较典型的棋类引擎的模式了，整个 minimax 算法占了 70%+ 的时间，为了搜索局面，有大量的位运算和访存，还有根据访存结果决定方向的分支。果不其然，执行 2688B 条指令，其中有 228B 条是分支指令，有 6.1B 次错误预测，MPKI 达到了 `6.1B/2688B*1000=2.27`。和 706.stockfish_r 类似，它也有不少的 popcnt 调用，那么打开 `-mpopcnt` 就会得到不错的性能提升：时间从 140s 降低到 126s，减少 11% 时间。而即使开 `-march=native`，性能也只是进一步降到 122s，只有少量的地方用到了 AVX2。

另一方面，LLVM 22 的性能在 707.ntest_r 上比 GCC 14 要快：同样是 `-O3` 的编译选项，运行时间从 GCC 14 的 140s 降低到 126s。深入研究汇编发现，LLVM 22 在没有开 `-mpopcnt` 的时候，它的行为是，直接把类似 libgcc 的 `__popcountdi2` 的代码内联到了程序当中，省去了 call libgcc 的开销，不过代价就是代码体积会增加。类似地，706.stockfish_r 的 1to6_classical 也是 LLVM 22 比 GCC 14 快，从 47s 降低到 44s。

同时，GCC 15 相比 GCC 14 也有性能提升，运行时间从 140s 降低到了 130s。分析汇编，发现主要优化点在 `flips(int sq, u64 mover, u64 enemy)` 函数当中。性能区别有两点：

1. 首先是对 callee-saved 寄存器的使用，GCC 14 会在 epilogue/prologue 直接进行一系列的 push/pop，而 GCC 15 更加聪明，仅在 `if (neighbors[sq]&enemy)` 条件成立的情况下，需要执行复杂函数体，需要 callee-saved 寄存器时才会进行 push/pop，否则就直接 ret，因为检查条件的时候并没有用到 callee-saved 寄存器，避免了保存和恢复。
2. 自己编译的 GCC 15 默认是 -no-pie 模式，而发行版的 GCC 14 默认是 -pie，而 -no-pie 模式因为采用绝对地址，可以在 imul 等指令的操作数直接访问内存，节省寄存器，于是 callee-saved register 就都可以不用了，开启 -static 也能带来类似的效果。上面的第一条分析是手动给 GCC 15 开 -pie 后观察到的。不过主要的性能提升还是来自于减少 push/pop 的执行次数。

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

实测数据显示，三条命令耗费的时间分别是 69s、12s 和 25s，共计 106s。reftime 是 528s，对应 5.0 分。开启 -flto/-ljemalloc 对性能影响很小，-march=native 甚至带来了负优化。下面分别分析这三条命令的具体性能特性。

#### main

通过 `perf` 观察性能瓶颈，这几个函数耗费的时间占比较多：

- `sqlite3BtreeMovetoUnpacked(BtCursor *pCur, UnpackedRecord *pIdxKey, i64 intKey, int biasRight, int *pRes)` 来自 `src/sqlite3.c`：24.66%，在 Btree 上进行搜索，根据 key，查找对应的 entry
- `sqlite3VdbeExec(Vdbe *p)` 来自 `src/sqlite3.c`：22.36%，用 Loop+Switch 实现的执行字节码的虚拟机，执行编译好的 SQL 语句，VDBE 是 SQLite 的执行引擎，全称是 Virtual Database Engine
- `pcache1Fetch(sqlite3_pcache *p, unsigned int iKey, int createFlag)` 来自 `src/sqlite3.c`：8.26%，对应一个用哈希表维护的 Page Cache，用于在内存里缓存硬盘上的数据
- `sqlite3GetVarint(const unsigned char *p, u64 *v)` 来自 `src/sqlite3.c`：3.70%，恢复内存中可变长度的整数

都是一些比较经典的数据结构和算法的应用，Btree，Loop+Switch 的解释执行，加哈希表查询。主要瓶颈在内存上。执行了 897.6B 条指令，其中 178.2B 是分支指令，错误预测了 1.5B 次，MPKI 是 `1.5B/897.6B*1000=1.67`。

#### cte

通过 `perf` 观察性能瓶颈，这几个函数耗费的时间占比较多：

- `sqlite3VdbeExec(Vdbe *p)` 来自 `src/sqlite3.c`：41.15%，主要时间花费在查询的执行，因为这个 cte 测例，其计算过程比较复杂，用 SQL 实现了数独（递归和非递归版本）、Mandelbrot，还测试了 EXCEPT SELECT 语法
- `sqlite3VdbeRecordCompareWithSkip(int nKey1, const void *pKey1, UnpackedRecord *pPKey2, int bSkip)` 来自 `src/sqlite3.c`：7.37%，比较表里的两个行
- `sqlite3VdbeSerialGet(const unsigned char *buf, u32 serial_type, Mem *pMem)` 来自 `src/sqlite3.c`：5.95%，反序列化，根据内存中保存的数据类型，解析对应的数据
- `vdbeSorterSort(SortSubtask *pTask, SorterList *pList)` 来自 `src/sqlite3.c`：5.95%，实现排序

瓶颈主要在解释器上，行为模式比较类似一些解释型语言的解释器，比如 CPython。执行了 307.2B 条指令，其中 62.8B 是分支指令，错误预测了 41M 次，MPKI 是 `41M/307.2B*1000=0.13`。

#### fp

通过 `perf` 观察性能瓶颈，这几个函数耗费的时间占比较多：

- `sqlite3VdbeExec(Vdbe *p)` 来自 `src/sqlite3.c`：30.66%，主要时间花费在查询的执行，因为这个 fp 测例，其计算过程引入了不少浮点运算
- `sqlite3AtoF(const char *z, double *pResult, int length, u8 enc)` 来自 `src/sqlite3.c`：19.18%，实现从字符串到浮点数的转换，因为 SQL 内有很多浮点字面量
- `vdbeSorterSort(SortSubtask *pTask, SorterList *pList)` 来自 `src/sqlite3.c`：10.44%，描述见上
- `sqlite3VdbeRecordCompareWithSkip(int nKey1, const void *pKey1, UnpackedRecord *pPKey2, int bSkip)` 来自 `src/sqlite3.c`：6.76%，描述见上

瓶颈主要在解释器上，不过因为 SQL 语句的设计，有很多时间花在字符串转浮点数上。执行了 555.5B 条指令，其中 111.7B 是分支指令，错误预测了 395M 次，MPKI 是 `395M/555.5B*1000=0.71`。

#### 小结

通过上面的分析，可见 sqlite_r 确实是比较难优化的那一类，大量访存、计算和分支混合在一起，对内存子系统的负担比较重，难以向量化，开 `-march=native` 后运行时间从 106s 增加到 112s。整体来看，执行了 1760B 条指令，其中有 353B 条是分支指令，MPKI 仅有 1.08，主要由 main 贡献。

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

#### randomMesh

首先分析第一条命令的热点函数：

- `omnetpp::cTopology::calculateUnweightedSingleShortestPathsTo(Node *_target)` 来自 `src/simulator/sim/ctopology.c`：16.22%，实现了经典的单源最短路算法，且每条边的权重都是一，所以就是 BFS
- `__do_dyncast` 和 `__dynamic_cast` 来自 libstdc++.so：4.73%+3.24%+2.22%+0.81%=11.0%，代码中有一些 dynamic_cast 的使用，如上面的 Routing::handleMessage
- `Routing::handleMessage(cMessage *msg)` 来自 `src/model/Routing.cc`：7.10%，模拟路由表的功能，主要逻辑是内联了一个 `std::map<int, int>` 的 `find` 操作（[Godbolt](https://godbolt.org/z/ne6oEb9Md)），在一个红黑树上进行查询
- `cEvent::shouldPrecede(const cEvent *other)` 来自 `src/simulator/sim/cevent.cc`：4.64%，一个 cEvent 结构体的比较函数

整体来看，它的瓶颈分散在比较多的地方。执行了 306B 条指令，其中有 62B 条是分支指令，错误预测 659M 次，MPKI 为 `659M/306B*1000=2.15`。

#### 其余的 9 条 queuenet 命令

用 `perf` 观察，其余 9 条 queuenet 命令的瓶颈主要集中在这些函数：

- strcmp（`__strcmp_avx2`）
- dynamic_cast（`__do_dyncast` 和 `__dynamic_cast`）
- malloc、free 和 operator new
- printf（`__printf_buffer`）

此外还有一些 omnetpp 自己的函数（如 `omnetpp::common::StringPool::obtain(const char *s)`，主要是对 `std::unordered_map<const char *,int,str_hash, str_eq> pool` 进行查询和修改操作），散落各处，每个函数都只占用不到 5% 的时间。对于这么大比例使用 libc/libstdc++ 中函数的情况，标准库和内存分配器的实现就很重要了。

#### 小结

针对上面的分析，尝试不同的编译选项：

- 开 `-O3 -ljemalloc` 后，十条命令的性能都有了一定的提升，总时间从 86.2s 降低到 80.6s，分数从 5.6 分提升到 6.0 分。
- 开 `-O3 -flto` 也能带来不错的提升，总时间从 86.2s 降低到 76.1s，分数从 5.6 分提升到 6.4 分。
- 开 `-O3 -flto -ljemalloc`，则总时间从 86.2s 降低到 69.7s，分数从 5.6 分提升到 7.0 分。

类似的现象在 SPEC INT 2017 已经出现了，`-O3 -flto` 比 `-O3` 快 3%，`-O3 -flto -ljemalloc` 比 `-O3 -flto` 快 20%。

`-O3` 下，执行的指令数是 1447B，其中 291B 是分支指令，MPKI 是 0.78。虽然 randomMesh 因为图计算，MPKI 比较高，但整体的 MPKI 被其余命令拉低了。相比之下，SPEC INT 2017 Rate 的 520.omnetpp_r 的 MPKI 足足有 4.33。虽然还是同一个框架，但是负载行为还是出现了明显的变化。

### 714.cpython_r

前面提到才提到过解释器，这就到 CPython 了。测试包含三条命令：

```shell
# 1. resnet
cpython_r -I -B coreml_pb.py -i 2 -a -m Resnet50Headless.mlmodel -d 10
# 2. mobilenet
cpython_r -I -B coreml_pb.py -i 5 -a -c -m MobileNetV2.mlmodel -d 20
# 3. dna
cpython_r -I -B dna_bench.py 600000
```

三条命令的运行时间分别为 31s、20s 和 20s，总时间 71s，reftime 是 479s，对应 6.7 分。开启 `-O3 -flto` 后，三条命令的运行时间分别为 29s、19s 和 18s，总时间 66s，对应 7.3 分。`-O3 -ljemalloc` 影响很小，`-O3 -march=native` 有负优化。下面具体分析三条命令的负载特性。

#### resnet

还是用 `perf`，统计出热点函数：

- `_PyEval_EvalFrameDefault(PyThreadState *tstate, _PyInterpreterFrame *frame, int throwflag)` 来自 `src/cpython/Python/ceval.c`：24.09%，解释器中的 Loop + Switch 核心代码，对 Python 字节码进行解释执行
- `PyUnicode_FromFormatV(const char *format, va_list vargs)` 来自 `src/cpython/Objects/unicodeobject.c`，4.51%，把结果写到 Python 字符串的 sprintf 版本
- `_PyObject_Free(void *ctx, void *p)` 来自 `src/cpython/Objects/obmalloc.c`：3.48%，释放 PyObject
- `_PyObject_Malloc(void *ctx, size_t nbytes)` 来自 `src/cpython/Objects/obmalloc.c`：3.15%，分配 PyObject

剩下就比较零散了，主要还是围绕着解释器的循环。执行了 653B 条指令，其中有 137B 是分支指令，错误预测 7.8M 次，MPKI 等于 `7.8M/653B*1000=0.01` 可以忽略不计。开启 `-O3 -flto` 后，热点函数不变，指令数降低为 618B，其中分支有 128B，错误预测 46M 次。

#### mobilenet

统计出热点函数，发现前四依然是上面四个，且时间占比差不多。可能是因为，resnet 和 mobilenet 测例用的是同一个 .py 源码，只是用的模型不同。执行了 439B 条指令，其中有 92B 是分支指令，错误预测 9.3M 次，MPKI 等于 `9.3M/439B*1000=0.02` 可以忽略不计。开启 `-O3 -flto` 后，热点函数不变，指令数降低为 417B，其中分支有 86B，错误预测 35M 次。

#### dna

统计热点函数：

- `_PyEval_EvalFrameDefault(PyThreadState *tstate, _PyInterpreterFrame *frame, int throwflag)` 来自 `src/cpython/Python/ceval.c`：36.75%，描述见上
- `_PyObject_Free(void *ctx, void *p)` 来自 `src/cpython/Objects/obmalloc.c`：5.31%，描述见上
- `PyUnicode_Contains(PyObject *str, PyObject *substr)` 来自 `src/cpython/Objects/unicodeobject.c`，4.59%，Python 字符串的 contains 操作，对应 `data/all/input/knucleotide.py` 代码中的 `chat in "GATC"` 判断
- `_PyObject_Malloc(void *ctx, size_t nbytes)` 来自 `src/cpython/Objects/obmalloc.c`：3.52%，描述见上

主要热点还是解释执行，不过因为字符串的 contains 调用次数较多，所以 `PyUnicode_Contains` 时间占比有所上升。执行了 394B 条指令，其中有 77B 是分支指令，错误预测 228M 次，MPKI 等于 `228M/394B*1000=0.58` 也还是很低。开启 `-O3 -flto` 后，热点函数不变，指令数降低为 380B，其中分支有 72B，错误预测 228M 次。

#### 小结

714.cpython_r 就是一个典型的字节码解释器，在一个 Loop + Switch 结构当中完成解释执行。整体 MPKI 很低，只有 0.17，即使开了 `-O3 -flto`，虽然预测错误多了，总指令数少了，MPKI 会变大，但绝对数字也还是很小，只有 0.23。

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

与 502.gcc_r 的行为类似（见 [The Alberta Workloads for the SPEC CPU® 2017 Benchmark Suite 的分析](https://webdocs.cs.ualberta.ca/~amaral/AlbertaWorkloadsForSPECCPU2017/reports/gcc_report.html)），721.gcc_r 的时间分布在大量函数，除了 ref32 花费了 10.76% 的时间在 dominated_by_p、5.92% 的时间在 bitmap_set_bit 以外，其他函数的占用时间基本都在 3% 以下，没有一个特别明显的热点函数。

三次运行的性能计数器如下：

1. gcc-pp: 执行 471B 条指令，其中有 100B 条分支指令，错误预测 2.2B 次，MPKI 等于 `2.2B/471B*1000=4.67`
2. gcc-smaller: 执行 244B 条指令，其中有 52B 条分支指令，错误预测 0.91B 次，MPKI 等于 `0.91B/244B*1000=3.72`
3. ref32: 执行 405B 条指令，其中有 86B 条分支指令，错误预测 0.61B 次，MPKI 等于 `0.61B/405B*1000=1.51`

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

#### transformsplus

使用 `perf` 观察热点函数：

- `llvm::InstCombinerImpl::foldIntegerTypedPHI(llvm::PHINode& PN)` 来自 `src/lib/Transforms/InstCombine/InstCombinePHI.cpp`: 4.06%，对 IR 中的 PHI 结点进行处理，这个函数还挺复杂的
- `_int_malloc/cfree/malloc`：2.38%+0.89%+0.82%=4.09%，大量的内存分配和释放，因此 `-ljemalloc` 能带来不错的性能提升
- `llvm::DenseMapBase::FindAndConstruct()`: 1.69%，LLVM 自己用数组实现的哈希表

其他用很多小的函数，占时间比例不高，和 721.gcc_r 类似，也是时间分散得比较开。执行指令数为 575B，其中分支指令有 119B，错误预测有 3.5B 次，MPKI 等于 `3.5B/575B*1000=6.09`，挺高的。

#### codegen

使用 `perf` 观察热点函数：

- `llvm::InstCombinerImpl::foldIntegerTypedPHI(llvm::PHINode& PN)` 来自 `src/lib/Transforms/InstCombine/InstCombinePHI.cpp`: 20.85%，描述见上
- `_int_malloc/cfree/malloc`：1.91%+0.72%+0.65%=3.28%，描述见上
- `llvm::DenseMapBase::FindAndConstruct()`: 1.29%，描述见上

整体的情况和 transformsplusplus 类似，只不过 `foldIntegerTypedPHI` 时间占比更高，其他还是有很多函数耗费很短的时间，分散得比较开。执行指令数为 417B，其中分支指令有 86B，错误预测有 2.4B 次，MPKI 等于 `2.4B/417B*1000=5.76`，依然挺很高。

#### 小结

llvm 和 gcc 同为编译器的双子星，在负载特性上也有类似之处：有很多的内存分配和释放，受益于 `-ljemalloc`；时间分布在大量小函数当中，热点不明显；MPKI 较高，尤其是 723.llvm_r 直接一跃成为 SPEC INT 2026 Rate 中 MPKI 最高的一项测试，可能是因为它有大量数据依赖的分支。723.llvm_r 整体的指令数有 991B，其中有 205B 是分支指令，MPKI 达到 5.98，即使是在人才济济的 SPEC INT 2017 Rate，也能紧紧地排在 505.mcf_r 和 541.leela_r 两位大哥身后成为第三大的 MPKI。

### 727.cppcheck_r

cppcheck 是一个 cpp 静态分析工具，输入 C++ 文件，提供代码的分析报告，汇报数组越界访问或变量未初始化等等问题。它会分析三个不同的代码，根据命名来看，应该是从其他测例里找的，而且还有 747 和 770 这种不在 SPEC CPU 2026 当中的测例，应该是没有被选上，只有 738 diamond 以 838.diamond_s 被保留了下来：

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

#### 738_diamond

热点函数如下：

- `multiCompareImpl(const Token *tok, const char *haystack, nonneg int varid)` 来自 `src/lib/token.cpp`：40.82%，字符串匹配函数，比如用 abc|def 去匹配一个 token
- `Token::Match(const Token *tok, const char pattern[], nonneg int varid)` 来自 `src/lib/token.cpp`：12.08%，也是类似的字符串匹配函数，语法有些不同，类似自研正则表达式子集
- `ScopeInfo3::findScope(const std::string & scope)` 来自 `src/lib/tokenize.cpp`：5.49%，循环，从当前作用域开始寻找对应的符号，如果没有，则检查更高一级的作用域，一般用于从变量名找到作用域里定义的符号
- `Tokenizer::simplifyUsing()`：3.57%，把 `using N::x;` 变为 `using x = N::x`，里面就会用到上面说的 `Token::Match`，参数是 `"using ::| %name% ::"`
- `cfree/malloc/_int_malloc`：0.47%+0.33%+0.45%=1.25%，内存分配相关

可以看到，主要的瓶颈是字符串匹配上，它的实现就是一个循环，用指针去扫描字符串，没有做数据结构上的优化。执行了 401B 条指令，其中有 109B 条分支指令，错误预测 174M 次，MPKI 等于 `174M/401B*1000=0.43` 不算高。

#### 747_dealii

热点函数类似：

- `multiCompareImpl(const Token *tok, const char *haystack, nonneg int varid)` 来自 `src/lib/token.cpp`：27.42%，描述见上
- `Token::Match(const Token *tok, const char pattern[], nonneg int varid)` 来自 `src/lib/token.cpp`：14.55%，描述见上
- `cfree/malloc/_int_malloc`：2.14%+1.57%+0.53%=4.24%，内存分配的比例更高
- `Token::simpleMatch(const Token *tok, const char pattern[], size_t pattern_len)` 来自 `src/lib/token.cpp`：3.88%，又一个字符串匹配函数，换了种格式，比如 `"abc def"` 代表匹配 `abc` 或 `def`
- `TemplateSimplifier::addInstantiation(Token *token, const std::string &scope)` 来自 `src/lib/templatesimplifier.cpp`：2.98%，在 token 级别上做一些代码简化的变换
- `isAliasOf(const Token* tok, const Token* expr, int* indirect, bool* inconclusive)` 来自 `src/lib/astutils.cpp`：2.55%，判断两个变量是否 alias

依然有大量的字符串匹配，不知道为啥还要搞好几种语法，实现好几个字符串匹配函数。执行了 304B 条指令，其中有 83B 条分支指令，错误预测 298M 次，MPKI 等于 `298M/304B*1000=0.98` 也不算高。

#### 770_7z

热点如下：

- `multiCompareImpl(const Token *tok, const char *haystack, nonneg int varid)` 来自 `src/lib/token.cpp`：32.25%，描述见上
- `Token::Match(const Token *tok, const char pattern[], nonneg int varid)` 来自 `src/lib/token.cpp`：18.82%，描述见上
- `__memcmp_avx2_movbe`：8.99%，被用于字符串匹配
- `std::map<std::string>::equal_range`：7.34%，红黑树上的字符串匹配
- `__strchr_avx2`：7.34%，被用于字符串匹配
- `cfree/malloc/_int_malloc`：0.37%+0.27%+0.17%=0.81%，内存分配的比例较低

依然是字符串匹配为主。执行了 506B 条指令，其中有 138B 条分支指令，错误预测 393M 次，MPKI 等于 `393M/506B*1000=0.78` 也不算高。

#### 小结

整体看下来，727.cppcheck_r 就是在不断地做字符串匹配。我就纳闷了，为啥不能直接过一遍 tokenizer，把 token 都转为数字呢，这样比较起来多快。在 token 级别上做各种变换，就在不停地对 token 进行字符串比较，导致最后的性能瓶颈，不是在 cppcheck 自己写的字符串比较，就是在 libc 的字符串比较里了。

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

#### twoexact

主要的热点函数：

- `sat_solver_propagate(sat_solver* s)` 来自 `src/berkeley-abc/src/sat/bsat/satSolver.c`：75.33%，应该是 SAT Solver 中的 Unit Propagation，寻找那些只剩下一个变量还没确定的语句，给它进行赋值，然后传播到其他语句
- `sat_solver_analyze(sat_solver* s, int h, veci* learnt)` 来自 `src/berkeley-abc/src/sat/bsat/satSolver`：15.85%，应该是针对出现冲突的语句进行分析，属于 CDCL（Conflict Driven Clause Learning） 的一部分
- `sat_solver_solve_internal(sat_solver* s)` 来自 `src/berkeley-abc/src/sat/bsat/satSolver.c`：3.80%，是 SAT Solver 的入口函数

很少能见到这种瓶颈如此高度集中的情况了，不过确实，SAT Solver 大部分时间都在做 Unit Propagation，出现冲突了就做 CDCL。唤起了很久以前在《软件分析与验证》课上写 DPLL SAT Solver 的[回忆](https://github.com/jiegec/dpll)，当然了，abc 的实现肯定比我那课程作业要更加复杂和高级。主要的瓶颈就是一堆访存以及依赖内存结果的分支，在 SAT 问题的解空间内进行搜索。

指令数 53B，其中分支指令 8.4B，错误预测 606M，MPKI 等于 `606M/53B*1000=11.43`，非常的高，接近 SPEC INT 2017 的 541.leela_r 大帝。

#### beem6

主要的热点函数：

- `Cec4_ManPackAddPatterns(Gia_Man_t * p, int iBit, Vec_Int_t * vLits)` 来自 `src/proof/cec/cecSatG2.c`：54.65%，CEC 指的是 Combinational Equivalence Checking，函数的用途没仔细研究，不过它就是一个两层循环，对数组元素进行访存和位运算
- `Cec4_ManGeneratePatterns_rec(Gia_Man_t * p, Gia_Obj_t * pObj, int Value, Vec_Int_t * vPat, Vec_Int_t * vVisit)` 来自 `src/proof/cec/cecSatG2.c`：29.01%，看起来也是一堆复杂的访存和逻辑运算混合

热点依然很集中，不过因为缺少领域知识，不太明白它在跑什么。运行 256B 条指令，其中分支有 40B，错误预测 192M 次，MPKI 等于 `192M/256B*1000=0.75`，相比 SAT 来说低了很多。

#### mem

热点函数依然是 sat solver 相关，相比 twoexact，`sat_solver_canceluntil` 时间占比高了一些，达到了 8.46%，不过整体的特性基本是一样的。运行 151B 条指令，其中分支有 24B，错误预测 1.2B，MPKI 等于 `1.2B/151B*1000=7.95`，非常高。

#### vga

热点函数依然是 sat solver，整体特性一致。运行 490B 条指令，分支有 77B，错误预测 2.1B 次，MPKI 等于 `2.1B/490B*1000=4.29`，还是很高。

#### mcml

热点函数终于有了新面孔：

- `Abc_ObjDeleteFanin(Abc_Obj_t * pObj, Abc_Obj_t * pFanin)` 来自 `src/base/abc/abcFanio.c`：12.57%，逻辑很简单，就是调用 `Vec_IntRemove` 从数组里删除一个元素，遍历数组，找到匹配的元素，把后面的元素都往前挪
- `Gia_ManSwiSimulate(Gia_Man_t * pAig, Gia_ParSwi_t * pPars)` 来自 `src/aig/gia/giaSwitch.c`：8.87%，依然看不懂在干啥，不过似乎是一些比较适合 SIMD 的循环，在 `-O3` 下能看到一些 SSE 指令
- `Abc_AigAndLookup(Abc_Aig_t * pMan, Abc_Obj_t * p0, Abc_Obj_t * p1)` 来自 `src/base/abc/abcAig.c`：7.03%，主要时间是在内部一个循环当中，访存加位运算，不知道在实现什么功能
- `If_ObjPerformMappingAnd(If_Man_t * p, If_Obj_t * pObj, int Mode, int fPreprocess, int fFirst)` 来自 `src/map/if/ifMap.c`：6.72%，又是一堆不知道在干啥的复杂位运算
- `Lpk_NodeCutsOneFilter(Lpk_Cut_t * pCuts, int nCuts, Lpk_Cut_t * pCutNew)` 来自 `src/berkeely-abc/src/opt/lpk/lpkCut.c`：5.47%，主要时间在循环里，不知道在实现什么

运行 209B 条指令，其中 40B 条分支指令，错误预测 535M 次，MPKI 等于 `535M/209B*1000=2.56`，不低。

#### des

再次出现了新的热点函数：

- `__strcmp_avx2` 来自 libc：22.04%，没想到瓶颈居然又出现在了 strcmp 上
- `Nm_ManTableLookupId(Nm_Man_t * p, int ObjId)` 来自 `src/misc/nm/nmTable.c`：21.56%，遍历一个哈希表，哈希表的每个桶是个链表，遍历链表中的元素，寻找匹配
- `Nm_ManTableAdd(Nm_Man_t * p, Nm_Entry_t * pEntry)` 来自 `src/misc/nm/nmTable.c`：12.19%，经典的哈希表插入算法，把新元素插入到对应桶的链表当中
- `Nm_ManTableLookupName(Nm_Man_t * p, char * pName, int Type)` 来自 `src/misc/nm/nmTable.c`：5.78%，同样是遍历哈希表查询，只不过这次用的是字符串匹配，解释了为啥 strcmp 调用次数那么多，其实是在找哈希表的字符串匹配
- `Gia_ManSwiSimulate` 来自 `src/aig/gia/giaSwitch.c`：5.49%，描述见上
- `spec_qsort`：3.98%，好久不见的熟悉面孔，在 SPEC INT 2017 年代，在 505.mcf_r 中有出色表现（指瓶颈在 qsort 上，且很大一部分开销来自于调用 comparator 函数指针，开 -flto 后因为把函数指针调用内联，性能直接提升 13%）

这次又是经典数据结构哈希表了，而且还混入了大量的字符串匹配，最后瓶颈都在查哈希表上了。

运行 137B 条指令，其中有 23.5B 是分支指令，错误预测 374M 次，MPKI 等于 `374M/137B*1000=2.73`，依然不低。

#### 小结

综合以上六条命令，可以看到它触碰了 abc 不同地方的代码，所以热点不尽相同，有 SAT，有看不懂的一些 EDA 相关逻辑，还有带字符串匹配的哈希表查询，其中 SAT 的占比是最大的。由于 SAT 的存在，最终的 MPKI 足足有 3.87，在 SPEC INT 2026 Rate 当中仅次于 723.llvm_r，超过了 721.gcc_r 和 777.zstd_r。共执行 1296B 条指令，其中有 213B 是分支指令，这个比例不算高，但预测错误率足够高。

### 734.vpr_r

接下来就到了 EDA 的下一步，逻辑综合后，就要进行布局（place）布线（route）了，这就是 vpr_r 干的活。测试分为四条命令：

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

- `get_non_updateable_bb(ClusterNetId net_id, t_bb* bb_coord_new)` 来自 `src/vtr-vpr/vpr/src/place/place.cpp`：jpeg_place 占比 13.98%，smithwaterman_place 占比 18.26%，遍历 pin，根据它的 x 和 y 坐标，找到 bounding box，即 xmin/xmax/ymin/ymax
- `try_swap(...)` 来自 `src/vtr-vpr/vpr/src/place/place.cpp`：jpeg_place 占比 12.39%，smithwaterman_place 占比 11.46%，里面做的事情还挺复杂的，看不太懂
- `physical_tile_type(ClusterBlockId blk)` 来自 `src/vtr-vpr/vpr/src/util/vpr_utils.cpp`：jpeg_place 占比 7.59%，smithwaterman_place 占比 7.75%，看起来就是比较简单的访存，这个函数会在 `get_non_updateable_bb` 和 `get_bb_from_scratch` 等地方被频繁调用
- `get_bb_from_scratch(ClusterNetId net_id, t_bb* coords, t_bb* num_on_edges)` 来自 `src/vtr-vpr/vpr/src/place/place.cpp`：jpeg_place 占比 6.73%，smithwaterman_place 占比 2.78%，和 `get_non_updateable_bb` 类似，也是求 bounding box
- `malloc/_int_mallloc/cfree` 来自 libc：jpeg_place 占比 1.62%+1.26%+1.06%=3.94%，smithwaterman_place 占比 1.76%+1.42%+1.11%=4.29%

开 `-O3 -flto` 后，能看到的是 `physical_tile_type` 被内联了进去，节省了频繁调用函数的开销。考虑到这个内存分配和释放的时间占比，`-O3 -ljemalloc` 提升性能并不意外。

`-O3` 下，jpeg_place 执行了 275B 条指令，其中分支有 52B 条，错误预测 785M 次，MPKI 等于 `785M/275B*1000=2.85`，不低。smithwaterman_place 执行了 247B 条指令，其中分支有 45.6B 条，错误预测 663M 次，MPKI 等于 `663M/247B*1000=2.68`。在 bounding box 计算 min/max 过程中，能看到一些 cmov 指令的使用，因此实际上已经少了一些容易预测错误的分支了。在一些没有 cmov 指令的 ISA 下，可能 MPKI 还会更高。

#### jpeg_route 和 smithwaterman_route

到了布线，热点函数出现了一些不同：

- `ConnectionRouter<BinaryHeap>::evaluate_timing_driven_node_costs(...)` 来自 `src/vtr-vpr/vpr/src/route/connection_router.cpp`：jpeg_route 占比 9.35%，smithwaterman_route 占比 6.91%，有一些浮点运算，不知道具体在算什么
- `ConnectionRouter<BinaryHeap>::timing_driven_add_to_heap(...)` 来自 `src/vtr-vpr/vpr/src/route/connection_router.cpp`：jpeg_route 占比 9.34%，smithwaterman_route 占比 6.82%，会调用 `evaluate_timing_driven_node_costs` 计算 cost，然后插入到 Binary Heap 当中
- `ConnectionRouter<BinaryHeap>::timing_driven_expand_neighbours(...)` 来自 `src/vtr-vpr/vpr/src/route/connection_router.cpp`：jpeg_route 占比 8.14%，smithwaterman_route 占比 4.00%，不确定在干啥，看起来在遍历邻居结点，符合一定条件后，调用 `timing_driven_add_to_heap`
- `ClassicLookahead::get_expected_delay_and_cong(...)` 来自 `src/vtr-vpr/vpr/src/route/router_lookahead.cpp`：jpeg_route 占比 7.86%，smithwaterman_route 占比 5.14%，看起来也是在进行一些延迟的计算，涉及到很多浮点数
- `BinaryHeap::get_heap_head()` 来自 `src/vtr-vpr/vpr/src/route/binary_heap.cpp`：jpeg_route 占比 3.14%，smithwaterman_route 占比 1.64%，就是经典的最小二叉堆的实现，获取最小值
- `malloc/_int_mallloc/cfree` 来自 libc：jpeg_route 占比 1.10%+1.02%+0.78%=2.90%，smithwaterman_route 占比 1.62%+1.49%+1.08%=4.19%

虽然不清楚具体算法，但看起来，就像是在做一些 cost 计算，然后通过 BinaryHeap 选择最小的 cost 去做一些扩展，有点类似搜索算法。

开 `-O3 -flto` 后，能看到的是 `evaluate_timing_driven_node_costs` 和 `timing_driven_add_to_heap` 被内联进 `timing_driven_expand_neighbours`，节省了频繁调用函数的开销，这个函数的时间占比提升到 jpeg_route 的 21.40% 和 smithwaterman_route 的 12.48%，类似的事情应该也发生在 `get_expected_delay_and_cong` 身上。考虑到这个内存分配和释放的时间占比，`-O3 -ljemalloc` 提升性能并不意外。

`-O3` 下，jpeg_route 执行了 425B 条指令，其中分支有 79B 条，错误预测 1.1B 次，MPKI 等于 `1.1B/425B*1000=2.59`，不低。smithwaterman_route 执行了 307B 条指令，其中分支有 59.6B 条，错误预测 613M 次，MPKI 等于 `613M/307B*1000=2.00`。

#### 小结

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

其他就是很多零散的函数了，每个函数的耗时都不高。开启 `-O3 lfto` 后，热点函数变为：

- `std::_Function_handler<void (), gem5::o3::CPU::CPU(gem5::BaseO3CPUParams const&)::{lambda()#1}>::_M_invoke(std::_Any_data const&)`：20.80% 实际上是 `tickEvent([this]{ tick(); }, "O3CPU tick", false, Event::CPU_Tick_Pri)` 当中调用 `tick()` 的 lambda，就是整个 O3 CPU 各种组件的单步模拟被融合到了一个巨大的函数里，仔细看里面的热点指令，其实还是 `gem5::TimeBuffer<*>::advance()` 相关的比较多
- `gem5::o3::IEW::tick()` 来自 `src/gem5/cpu/o3/iew.cc`：8.58%，描述见上
- `malloc/_int_malloc/cfree/_int_free_chunk/operator new` 来自 libc/libstdc++：5.55%+3.88%+3.72%+1.45%+1.22%=15.83%，随着其余部分被优化，内存分配的瓶颈更加明显了

进一步开启 `-O3 -lfto -ljemalloc` 后，内存分配时间减少，热点函数：

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
- `seal::util::BaseConverter::fast_convert_array(ConstRNSIter in, RNSIter out, MemoryPoolHandle pool)` 来自 `src/seal/util/rns.cpp`：5.88%，这里的 RNS 应该是 Residue Numebr System 的缩写，指令上还是大量的 imul/add 等运算
- `seal::util::RNSTool::sm_mrq(ConstRNSIter input, RNSIter destination, MemoryPoolHandle pool)` 来自 `src/seal/util/rns.cpp`：5.40%，不确定在做什么，也是大量的运算

总而言之，既然是密码学，就会有大量的整数运算，其中有不少的乘法，在素数域下做各种操作。执行指令数足足有 3113.8B，但分支只有 78.6B，MPKI 只有 0.14，全场最低，甚至低于 714.cpython_r，同时 IPC 全场最高，达到了 5.09。

开了 `-O3 -march=native` 后，确实生成了不少 AVX2 指令，但看下来，生成的指令序列还是挺复杂的，有大量的 vpunpcklqdq/vpunpckhqdq/vpermq/vpblendvb/vperm2i128 等指令，并没有在进行的计算，而是在不断地倒腾向量寄存器里数据的位置。虽然指令数减少了，但 IPC 降低更多，最后性能反而倒退，实际从 108s 增加到 116s。原来的 `-O3` 版本虽然每次只处理一个元素，但指令的并行度更高，IPC 弥补了指令数多的劣势。

那么，LLVM 22 做了什么优化呢？执行的指令数直接降低到 1214B，分支只有 57.2B。以 `seal::util::DWTHandler::transform_to_rev` 为例，可以看到：seal 为了实现 64 位乘 64 位到 128 位的乘法，它自己实现了这个过程，不仅在 `seal::util::multiply_uint64_generic` 中有实现，实际上也内联到了 `seal::util::DWTHandler::transform_to_rev` 当中；GCC 14 忠实地实现了这个算法，因此指令数很多（见 [Godbolt](https://godbolt.org/z/KKTa1aMP8)）；但其实，AMD64 的 mul 指令本来就是一个 64 位乘 64 位得到 128 位的乘法，所以 LLVM 12 直接识别出这段代码做的事情，然后编译成了 mul 指令（见 [Godbolt](https://godbolt.org/z/bc6xPjEMc)），而且这种 64 位乘法保留高位的指令在各种 ISA 都挺常见的，比如 ARM64 的 umulh，RISC-V 的 mulhu，LoongArch 的 mulh.du。当然，seal 的源码其实已经考虑了这个问题，在编译器支持的情况下，直接用 __int128 来完成[这件事情](https://github.com/microsoft/SEAL/blob/e3476fad1d5bb5e5222c51a551b5a4d7e2cb4f91/native/src/seal/util/gcc.h#L44)。然而，这类依赖编译器行为或具体指令集扩展的代码，由于 SPEC CPU 2026 的编译器中立性，都被去掉了，都会回落到最通用的写法上。此时，就只能依赖编译器去自己识别和优化了。

但是，这样某种意义也无法反映在真实场景中，应用的优化情况了，因为很多应用已经实际上和处理器的指令集扩展/编译器扩展共进化，实现的时候，脑子里是默认有这些东西，再去做的调优，甚至会写一些指令集相关的优化，用一些 intrinsics，比如原版 stockfish 就有针对 AVX512/AVX2/SSSE3/NEON_DOTPROD/LASX/LSX 的[优化](https://github.com/official-stockfish/Stockfish/blob/77a8f6ccf31846d63452f79e143fbc6dc62ae3a8/src/nnue/layers/affine_transform.h#L201)。到最后，就是编译器又实现各种 pass，识别程序里的 fallback generic 代码，再映射回高效的实现。其实类似的事情之前就出现过，网上用来证明编译器很聪明的一个例子，就是说识别 popcount 的循环，直接翻译成 popcnt 指令，然而很多程序直接用 `__builtin_popcount` 而不会真的去手写，这次只不过是换了个 pattern 罢了。当然，好消息是，C++20 引入了 std::popcount，可以一定程度避免类似的情况发生，只是来得太晚了。

相比之下，Geekbench 对这类指令集扩展的优化就比较持开放态度，愿意针对指令集扩展进行针对性的优化，比如经典引入 AMX/SME 对分数的巨大影响，当然这也让它被人骂 AppleBench，只能说见仁见智了。

## 总结

本文对 SPEC CPU 2026 中 INT Rate 的负载进行了深入的分析，以供编译器和处理器的设计者参考。从编译器的角度来说，可以集 GCC 和 LLVM 之长，进一步提升性能；从处理器的角度来说，针对程序的瓶颈进行优化，也能进一步提高分数。
