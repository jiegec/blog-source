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

本文测试环境：CPU 为 Intel i9-14900K P-Core @ 5.7 GHz，Linux 发行版为 Debian Trixie，编译器是 GCC 14.2.0。其实这款 CPU 最快能 Boost 到 6.0 GHz，但是时不时因为未知原因（防缩缸？）在只有单核负载的情况下也 Boost 不上去，现象是每跑一段时间负载，CPU 核心就会强制降频到 4.7 GHz，故退而求其次，选择在更容易稳定达到的 5.7 GHz 频率来跑，因为能跑 6.0 GHz 的就是那一个物理 P 核，其他的物理 P 核都能上 5.7 GHz，降频了只要换一个就好。6.0 GHz 下的性能可以参考之前的测试结果：[INT](../../../benchmark/data-trixie/int2026_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt) 和 [FP](../../../benchmark/data-trixie/fp2026_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt)。

推荐阅读：[Evaluating SPEC CPU2026](https://chipsandcheese.com/p/evaluating-spec-cpu2026) 和 [SPEC CPU2026: Characterization, Representativeness, and Cross-Suite Comparison](https://arxiv.org/abs/2605.03713v2)

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

实测数据显示，三条命令耗费的时间分别是 47s、77s 和 72s，共计 196s。reftime 是 1260s，对应 6.4 分。开启 `-march=native` 后，1to6_classical 时间缩短 10% 到 43s，而 1to6_nnue 和 7to11_nnue 时间明显缩短到 32s 和 31s，总时间 105s，对应 12 分，分数提升显著。下面分别分析这三条命令的具体性能特性。

#### 1to6_classical

通过 `perf` 观察性能瓶颈，运行第一个命令 1to6_classical 时，这几个函数耗费的时间占比较多：

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
- `vdbeSorterSort(SortSubtask *pTask, SorterList *pList)` 来自 `src/sqlite3.c`：10.44%，实现排序
- `sqlite3VdbeRecordCompareWithSkip(int nKey1, const void *pKey1, UnpackedRecord *pPKey2, int bSkip)` 来自 `src/sqlite3.c`：6.76%，比较表里的两个行

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

- `_PyEval_EvalFrameDefault(PyThreadState *tstate, _PyInterpreterFrame *frame, int throwflag)` 来自 `src/cpython/Python/ceval.c`：36.75%，解释器中的 Loop + Switch 核心代码，对 Python 字节码进行解释执行
- `_PyObject_Free(void *ctx, void *p)` 来自 `src/cpython/Objects/obmalloc.c`：5.31%，释放 PyObject
- `PyUnicode_Contains(PyObject *str, PyObject *substr)` 来自 `src/cpython/Objects/unicodeobject.c`，4.59%，Python 字符串的 contains 操作，对应 `data/all/input/knucleotide.py` 代码中的 `chat in "GATC"` 判断
- `_PyObject_Malloc(void *ctx, size_t nbytes)` 来自 `src/cpython/Objects/obmalloc.c`：3.52%，分配 PyObject

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

`-O3` 运行时间分别为 62s 和 53s，总时间 115s，reftime 是 507s，对应 4.4 分。开 `-O3 -flto` 性能反而变差，不过开 `-O3 -ljemalloc` 有明显性能提升，运行时间降低为 59s 和 47s，总时间 106s，分数提高到 4.8 分。

有意思的是，用 GCC 14 编译的 723.llvm_r，运行得比用 LLVM 22 编译的 723.llvm_r 更快，当然快得并不多。下面针对这两条命令进行具体的分析。

#### transformsplus

使用 `perf` 观察热点函数：

- `llvm::InstCombinerImpl::foldIntegerTypedPHI(llvm::PHINode& PN)` 来自 `src/lib/Transforms/InstCombine/InstCombinePHI.cpp`: 4.06%，对 IR 中的 PHI 结点进行处理，这个函数还挺复杂的
- `_int_malloc/cfree/malloc`：2.38%+0.89%+0.82%=4.09%，大量的内存分配和释放，因此 `-ljemalloc` 能带来不错的性能提升
- `llvm::DenseMapBase::FindAndConstruct()`: 1.69%，LLVM 自己用数组实现的哈希表

其他用很多小的函数，占时间比例不高，和 721.gcc_r 类似，也是时间分散得比较开。执行指令数为 575B，其中分支指令有 119B，错误预测有 3.5B 次，MPKI 等于 `3.5B/575B*1000=6.09`，挺高的。

#### codegen

使用 `perf` 观察热点函数：

- `llvm::InstCombinerImpl::foldIntegerTypedPHI(llvm::PHINode& PN)` 来自 `src/lib/Transforms/InstCombine/InstCombinePHI.cpp`: 20.85%，对 IR 中的 PHI 结点进行处理
- `_int_malloc/cfree/malloc`：1.91%+0.72%+0.65%=3.28%，大量的内存分配和释放，因此 `-ljemalloc` 能带来不错的性能提升
- `llvm::DenseMapBase::FindAndConstruct()`: 1.29%，LLVM 自己用数组实现的哈希表

整体的情况和 transformsplusplus 类似，只不过 `foldIntegerTypedPHI` 时间占比更高，其他还是有很多函数耗费很短的时间，分散得比较开。执行指令数为 417B，其中分支指令有 86B，错误预测有 2.4B 次，MPKI 等于 `2.4B/417B*1000=5.76`，依然挺很高。

#### 小结

llvm 和 gcc 同为编译器的双子星，在负载特性上也有类似之处：有很多的内存分配和释放，受益于 `-ljemalloc`；时间分布在大量小函数当中，热点不明显；MPKI 较高，尤其是 723.llvm_r 直接一跃成为 SPEC INT 2026 Rate 中 MPKI 最高的一项测试，可能是因为它有大量数据依赖的分支。723.llvm_r 整体的指令数仅有 991B，但有 205B 的分支数，MPKI 达到 5.98，即使是在人才济济的 SPEC INT 2017 Rate，也能紧紧地排在 505.mcf_r 和 541.leela_r 两位大哥身后成为第三大的 MPKI。

## SPEC FP 2026 Rate

TODO

## 总结

本文对 SPEC CPU 2026 的负载进行了深入的分析，以供编译器和处理器的设计者参考。从编译器的角度来说，可以集 GCC 和 LLVM 之长，进一步提升性能；从处理器的角度来说，针对程序的瓶颈进行优化，也能进一步提高分数。
