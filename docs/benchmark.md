---
layout: page
date: 1970-01-01
permalink: /benchmark/
---

# 性能测试

## SPEC INT 2017 Rate-1

下面贴出自己测的数据（SPECint2017，Estimated，rate，base，1 copy），不保证满足 SPEC 的要求，仅供参考。总运行时间（秒）基本和分数成反比，乘积按 5e4 估算。

### 数据总览

![](./data/int2017_rate1_score.svg)

??? note "分数/GHz"

    ![](./data/int2017_rate1_score_per_ghz.svg)

??? note "每项分数"

    ![](./data/int2017_rate1_ratio.svg)

??? note "IPC"

    ![](./data/int2017_rate1_ipc.svg)

??? note "分支预测 MPKI"

    ![](./data/int2017_rate1_mpki.svg)

??? note "分支预测错误率"

    ![](./data/int2017_rate1_mispred.svg)

??? note "频率"

    ![](./data/int2017_rate1_freq.svg)

### 原始数据

桌面平台（`-march=native` + LTO + Jemalloc）：

- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3 -march=native -flto -ljemalloc`）: [9.43](./data/int2017_rate1/Qualcomm_X1E80100_O3-march=native-flto-ljemalloc_001.txt)

桌面平台（LTO + Jemalloc）：

- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3 -flto -ljemalloc`）: [12.9](./data/int2017_rate1/AMD_Ryzen_9_9950X_O3-flto-ljemalloc_001.txt)
- Intel Core i9-14900K @ 6.0 GHz Raptor Lake（`-O3 -flto -ljemalloc`）: [12.1](./data/int2017_rate1/Intel_Core_i9-14900K_O3-flto-ljemalloc_001.txt)
- Intel Core i9-12900KS @ 5.5 GHz Alder Lake（`-O3 -flto -ljemalloc`）: [10.4](./data/int2017_rate1/Intel_Core_i9-12900KS_O3-flto-ljemalloc_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3 -flto -ljemalloc`）: [9.25](./data/int2017_rate1/Qualcomm_X1E80100_O3-flto-ljemalloc_001.txt)
- Loongson 3A6000 @ 2.5 GHz LA664（`-O3 -flto -ljemalloc`）: [4.86](./data/int2017_rate1/Loongson_3A6000_O3-flto-ljemalloc_001.txt)

桌面平台（LTO）：

- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3 -flto`）: [11.7](./data/int2017_rate1/AMD_Ryzen_9_9950X_O3-flto_001.txt)
- Intel Core i9-14900K @ 6.0 GHz Raptor Lake（`-O3 -flto`）: [11.7](./data/int2017_rate1/Intel_Core_i9-14900K_O3-flto_001.txt) [11.7](./data/int2017_rate1/Intel_Core_i9-14900K_O3-flto_002.txt)
- Intel Core i9-12900KS @ 5.5 GHz Alder Lake（`-O3 -flto`）: [9.97](./data/int2017_rate1/Intel_Core_i9-12900KS_O3-flto_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3 -flto`）: [8.62](./data/int2017_rate1/Qualcomm_X1E80100_O3-flto_001.txt)

桌面平台：

- Intel Core i9-14900K @ 6.0 GHz Raptor Lake（`-O3`）: [11.3](./data/int2017_rate1/Intel_Core_i9-14900K_O3_001.txt)
- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3`）: [11.2](./data/int2017_rate1/AMD_Ryzen_9_9950X_O3_001.txt)
- Intel Core i9-12900KS @ 5.5 GHz Alder Lake（`-O3`）: [9.62](./data/int2017_rate1/Intel_Core_i9-12900KS_O3_001.txt)
- AMD Ryzen 5 7500F @ 5.0 GHz Zen 4（`-O3`）: [9.51](./data/int2017_rate1/AMD_Ryzen_5_7500F_O3_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3`）: [8.31](./data/int2017_rate1/Qualcomm_X1E80100_O3_001.txt)
- AMD Ryzen 7 5700X @ 4.7 GHz Zen 3（`-O3`）: [7.87](./data/int2017_rate1/AMD_Ryzen_7_5700X_O3_001.txt)
- Apple M1 @ 3.1 GHz Firestorm（`-O3`）: [7.77](./data/int2017_rate1/Apple_M1_O3_001.txt)
- Intel Core i9-10980XE @ 4.8 GHz Cascade Lake（`-O3`）: [6.24](./data/int2017_rate1/Intel_Core_i9-10980XE_O3_001.txt)
- Qualcomm 8cx Gen3 P Core @ 3.0 GHz Cortex-X1C（`-O3`）: [5.73](./data/int2017_rate1/Qualcomm_8cx_Gen3_P_Core_O3_001.txt)
- Loongson 3A6000 @ 2.5 GHz LA664（`-O3`）: [4.35](./data/int2017_rate1/Loongson_3A6000_O3_001.txt)
- Qualcomm 8cx Gen3 E Core @ 2.4 GHz Cortex-A78C（`-O3`）: [4.11](./data/int2017_rate1/Qualcomm_8cx_Gen3_E_Core_O3_001.txt)

服务器平台（`-march=native` + LTO + Jemalloc）：

- Loongson 3C6000 @ 2.2 GHz LA664（`-O3 -march=native -flto -ljemalloc`）: [4.65](./data/int2017_rate1/Loongson_3C6000_O3-march=native-flto-ljemalloc_001.txt)

服务器平台（LTO + Jemalloc）：

- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3 -flto -ljemalloc`）: [7.48](./data/int2017_rate1/AWS_Graviton_4_O3-flto-ljemalloc_001.txt)
- AWS Graviton 3E @ 2.6 GHz Neoverse V1（`-O3 -flto -ljemalloc`）: [6.17](./data/int2017_rate1/AWS_Graviton_3E_O3-flto-ljemalloc_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3 -flto -ljemalloc`）: [5.33](./data/int2017_rate1/AMD_EPYC_7742_O3-flto-ljemalloc_001.txt)

服务器平台（LTO）：

- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3 -flto`）: [4.99](./data/int2017_rate1/AMD_EPYC_7742_O3-flto_001.txt)

服务器平台：

- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3`）: [6.80](./data/int2017_rate1/AWS_Graviton_4_O3_001.txt) [7.00](./data/int2017_rate1/AWS_Graviton_4_O3_002.txt)
- AMD EPYC 9R14 @ 3.7 GHz Zen 4（`-O3`）: [6.57](./data/int2017_rate1/AMD_EPYC_9R14_O3_001.txt)
- T-Head Yitian 710 @ 3.0 GHz Neoverse N2（`-O3`）: [5.79](./data/int2017_rate1/T-Head_Yitian_710_O3_001.txt)
- Intel Xeon Platinum 8576C Emerald Rapids（`-O3`）: [5.72](./data/int2017_rate1/Intel_Xeon_Platinum_8576C_O3_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Ice Lake（`-O3`）: [5.66](./data/int2017_rate1/Intel_Xeon_Platinum_8358P_O3_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3`）: [5.39](./data/int2017_rate1/Kunpeng_920_HuaweiCloud_kc2_O3_001.txt)
- AMD EPYC 9754 @ 3.1 GHz Zen 4c（`-O3`）: [5.32](./data/int2017_rate1/AMD_EPYC_9754_O3_001.txt)
- AMD EPYC 7K83 Zen 3（`-O3`）: [5.18](./data/int2017_rate1/AMD_EPYC_7K83_O3_001.txt)
- AWS Graviton 3E @ 2.6 GHz Neoverse V1（`-O3`）: [5.53](./data/int2017_rate1/AWS_Graviton_3E_O3_001.txt)
- AWS Graviton 3 @ 2.6 GHz Neoverse V1（`-O3`）: [5.10](./data/int2017_rate1/AWS_Graviton_3_O3_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3`）: [4.67](./data/int2017_rate1/AMD_EPYC_7742_O3_001.txt)
- Ampere Altra @ 3.0 GHz Neoverse N1（`-O3`）: [4.41](./data/int2017_rate1/Ampere_Altra_O3_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3`）: [4.35](./data/int2017_rate1/Intel_Xeon_E5-2680_v4_O3_001.txt)
- AMD EPYC 7H12 @ 3.3 GHz Zen 2（`-O3`）: [4.23](./data/int2017_rate1/AMD_EPYC_7H12_O3_001.txt)
- Loongson 3C6000 @ 2.2 GHz LA664（`-O3`）: [4.18](./data/int2017_rate1/Loongson_3C6000_O3_001.txt)
- Intel Xeon E5-2680 v3 @ 3.0 GHz Haswell（`-O3`）: [4.01](./data/int2017_rate1/Intel_Xeon_E5-2680_v3_O3_001.txt)
- Intel Xeon D-2146NT @ 2.9 GHz Skylake（`-O3`）: [3.96](./data/int2017_rate1/Intel_Xeon_D-2146NT_O3_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3`）: [3.10](./data/int2017_rate1/Kunpeng_920_O3_001.txt)
- Kunpeng 920 HuaweiCloud kc1 @ 2.6 GHz（`-O3`）: [3.03](./data/int2017_rate1/Kunpeng_920_HuaweiCloud_kc1_O3_001.txt)
- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3`）: [3.06](./data/int2017_rate1/AMD_EPYC_7551_O3_001.txt)
- Intel Xeon E5-2603 v4 @ 1.7 GHz Broadwell（`-O3`）: [2.48](./data/int2017_rate1/Intel_Xeon_E5-2603_v4_O3_001.txt)
- Loongson 3C5000 @ 2.2 GHz LA464（`-O3`）: [2.20](./data/int2017_rate1/Loongson_3C5000_O3_001.txt)

注：

1. SPEC INT 2017 Rate-1 结果受 `-flto`（分数 +4%）和 `-ljemalloc`（分数 +4-10%）影响很明显。`-Ofast` 和 `-O3` 区别很小，`-march=native` 影响很小。
2. 在部分处理器上，Linux 不能保证程序被调度到性能最高的核心上，例如：
      1. Qualcomm X1E80100 上，负载不一定会调度到有 Boost 的核上，因此需要手动绑核。没有 Boost 的核心会跑在 3.4 GHz，Boost 的核心最高可以达到 4.0 GHz，对应 14% 的性能提升。具体地讲，它有三个 Cluster，0-3 是没有 Boost 的 Cluster，4-7 和 8-11 每个 Cluster 中可以有一个核心 Boost 到 4.0 GHz，也就是说，最多有两个核达到 4.0 GHz，这两个核需要分别位于 4-7 和 8-11 两个 Cluster 当中。如果一个 Cluster 有两个或者以上的核有负载，那么他们都只有 3.4 GHz。
      2. AMD Ryzen 9 9950X 不同核能够达到的最大频率不同，目前 Linux（6.11）的调度算法不一定可以保证跑到最大频率 5.75 GHz 上，可能会飘到频率低一些（5.45 GHz 左右）的核心上，损失 4% 的性能，因此需要绑核心，详见 [Linux 大小核的调度算法探究](./blog/posts/software/linux-core-scheduling.md) 以及 [谈谈 Linux 与 ITMT 调度器与多簇处理器](https://blog.hjc.im/thoughts-on-linux-preferred-cores-and-multi-ccx.html)。
3. 对于服务器 CPU，默认设置可能没有打开 C6 State，此时单核不一定能 Boost 到宣称的最高频率，需要进 BIOS 打开 C6 State，使得空闲的核心进入低功耗模式，才能发挥出最高的 Boost 频率。
4. 对于除了苹果以外的 ARM64 核心，内核的 branch-misses 计数器考虑了 speculative 而不只是 retired，因此数字会偏高，此时要用 r22 计数替代。

x86 平台的分支预测准确率（Average）由高到低：

1. Zen 5(9950X): MPKI=4.33 Mispred=2.45%
2. Zen 4 Server(9R14): MPKI=4.38 Mispred=2.48%
3. Zen 4c(9754): MPKI=4.51 Mispred=2.55%
4. Zen 4 Desktop(7500F)/Zen 3(5700X): MPKI=4.53 Mispred=2.57%
5. Zen 2(7742): MPKI=4.62 Mispred=2.62%
6. Ice Lake(8358P)/Alder Lake(12900KS)/Raptor Lake(14900K): MPKI=4.71 Mispred=2.68%
7. Skylake(D-2146NT)/Cascade Lake(10980XE): MPKI=5.34 Mispred=3.04%
8. Zen 1(7551): MPKI=5.72 Mispred=3.26%
9. Haswell(E5-2680 v3)/Broadwell(E5-2680 v4): MPKI=5.84 Mispred=3.27%

ARM64 平台的分支预测准确率（Average）由高到低：

1. Neoverse V2(Graviton 4): MPKI=4.34 Mispred=2.39%
2. Oryon(X1E80100): MPKI=4.56 Mispred=2.50%
3. Neoverse N2(Yitian 710): MPKI=4.66 Mispred=2.57%
4. Firestorm(M1): MPKI=4.67 Mispred=2.55%
5. Neoverse V1(Graviton 3)/Cortex X1C(8cx Gen3 P Core): MPKI=4.75 Mispred=2.62%
6. Neoverse N1(Ampere Altra)/Cortex A78C(8cx Gen3 E Core): MPKI=5.06 Mispred=2.79%
7. TSV110(Kunpeng 920): MPKI=6.36 Mispred=3.49%

### 网上的数据

[SPEC CPU 2017 by David Huang](https://blog.hjc.im/spec-cpu-2017):

- AMD Ryzen 9950X Zen 5: 12.6
- Apple M3 Pro: 11.8
- Intel Core 13900K Raptor Lake: 11.5
- Apple M2 Pro: 10.3
- Apple M2: 9.95
- AMD HX 370 Strix Point Zen 5: 9.64
- Intel Core Ultra 258V Lunar Lake Lion Cove+Skymont: 9.46
- Apple M1 Max Firestorm+Icestorm: 9.2
- AMD Ryzen 5950X Zen 3: 9.15
- Loongson 3A6000 LA664: 4.29

[高通 X Elite Oryon 微架构评测：走走停停 by JamesAslan](https://zhuanlan.zhihu.com/p/704707254):

- AMD Ryzen 7700X Zen 4: 10.35
- Intel Core 13700K Raptor Lake: 9.81
- Intel Core 12700K Alder Lake: 9.13
- AMD Ryzen 5950X Zen 3: 8.45
- Apple M2 Avalanche+Blizzard: 8.40
- Qualcomm X1E80100 Oryon: 8.19
- Apple M1 Firestorm+Icestorm: 7.40
- Qualcomm 8 Gen 2 Cortex-X3: 6.58

[Running SPEC CPU2017 on Chinese CPUs, and More](https://old.chipsandcheese.com/2024/10/18/running-spec-cpu2017-on-chinese-cpus-and-more/)

- AMD Ryzen 9 7950X3D Non-VCache: 10.5
- Intel Core Ultra 7 258V Lion Cove: 9.37
- Intel Core Ultra 7 115H Redwood Cove: 7.6
- Intel Core Ultra 7 258V Skymont: 5.92
- Intel Core Ultra 7 115H Crestmont: 5.88
- Intel Core i5-6600K Skylake: 5.65
- Loongson 3A6000: 4.27
- Mediatek Genio 1200 Cortex A78: 3.8
- AMD FX-8150: 3.5
- Intel Core Ultra 7 115H Low Power Crestmont: 3.32
- Loongson 3A5000: 2.93
- Intel Celeron J4125 Goldmont Plus: 2.43
- Zhaoxin KaiXian KX-6640MA: 2.07
- Amlogic S922X Cortex A73: 1.77
- Mediatek Genio 1200 Cortex A55: 1.19

[Running SPEC CPU2017 at Chips and Cheese?](https://old.chipsandcheese.com/2024/09/19/running-spec-cpu2017-at-chips-and-cheese/)

- AMD Ryzen 9 9950X: 11.9
- AMD Ryzen 9 7950X3D Non-VCache: 10.5
- AMD Ryzen 9 7950X3D VCache: 10.5
- Intel Core Ultra 7 115H Redwood Cove: 7.58
- Intel Core Ultra 7 115H Crestmont: 5.34
- AMD Ryzen 9 3950X 3.5GHz: 5.28
- Ampere Altra: 3.98
- AmpereOne: 3.94
- AMD FX-8159: 3.46

[The AMD Ryzen 9 9950X and Ryzen 9 9900X Review: Flagship Zen 5 Soars - and Stalls](https://www.anandtech.com/show/21524/the-amd-ryzen-9-9950x-and-ryzen-9-9900x-review/5)

- AMD Ryzen 9 9950X Zen 5: 10.95
- Intel Core i9-14900K Raptor Lake: 10.94
- AMD Ryzen 9 7950X Zen 4: 9.88

[Snapdragon X Elite Qualcomm Oryon CPU Design and Architecture Hot Chips 2024](https://www.servethehome.com/snapdragon-x-elite-qualcomm-oryon-cpu-design-and-architecture-hot-chips-2024-arm/)

- Qualcomm X Elite Oryon on Linux: 10.64
- Qualcomm X Elite Oryon on Windows: 9.70

[ARM Cortex X1 微架构评测（上）：向山进发](https://zhuanlan.zhihu.com/p/619033328)

- Zen 3 @ 4.95 GHz: 8.4
- Firestorm @ 3.0 GHz: 7.4
- Cortex X1 @ 3.0 GHz: 5.7
- Cortex A78 @ 2.4 GHz: 3.9

## SPEC FP 2017 Rate-1

下面贴出自己测的数据（SPECfp2017，Estimated，rate，base，1 copy），不保证满足 SPEC 的要求，仅供参考。总运行时间基本和分数成反比，乘积按 1e5 估算。

### 数据总览

![](./data/fp2017_rate1_score.svg)

??? note "分数/GHz"

    ![](./data/fp2017_rate1_score_per_ghz.svg)

??? note "每项分数"

    ![](./data/fp2017_rate1_ratio.svg)

??? note "IPC"

    ![](./data/fp2017_rate1_ipc.svg)

??? note "分支预测 MPKI"

    ![](./data/fp2017_rate1_mpki.svg)

??? note "分支预测错误率"

    ![](./data/fp2017_rate1_mispred.svg)

??? note "频率"

    ![](./data/fp2017_rate1_freq.svg)

### 原始数据

桌面平台（`-march=native`）：

- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3 -march=native`）: [17.6](./data/fp2017_rate1/AMD_Ryzen_9_9950X_O3-march=native_001.txt)
- Intel Core i9-14900K @ 6.0 GHz Raptor Lake（`-O3 -march=native`）: [16.6](./data/fp2017_rate1/Intel_Core_i9-14900K_O3-march=native_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3 -march=native`）: [14.4](./data/fp2017_rate1/Qualcomm_X1E80100_O3-march=native_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz (AVX-512 @ 4.0 GHz) Cascade Lake（`-O3 -march=native`）: [7.24](./data/fp2017_rate1/Intel_Core_i9-10980XE_O3-march=native_001.txt)

桌面平台：

- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3`）: [16.5](./data/fp2017_rate1/AMD_Ryzen_9_9950X_O3_001.txt)
- Intel Core i9-14900K @ 6.0 GHz Raptor Lake（`-O3`）: [16.1](./data/fp2017_rate1/Intel_Core_i9-14900K_O3_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3`）: [14.4](./data/fp2017_rate1/Qualcomm_X1E80100_O3_001.txt)
- Intel Core i9-12900KS @ 5.5 GHz Alder Lake（`-O3`）: [14.3](./data/fp2017_rate1/Intel_Core_i9-12900KS_O3_001.txt)
- AMD Ryzen 5 7500F Zen 4（`-O3`）: [11.6](./data/fp2017_rate1/AMD_Ryzen_5_7500F_O3_001.txt)
- Apple M1 @ 3.1 GHz Firestorm（`-O3`）: [11.5](./data/fp2017_rate1/Apple_M1_O3_001.txt)
- AMD Ryzen 7 5700X @ 4.7 GHz Zen 3（`-O3`）: [9.91](./data/fp2017_rate1/AMD_Ryzen_7_5700X_O3_001.txt)
- Qualcomm 8cx Gen3 P Core @ 3.0 GHz Cortex-X1C（`-O3`）: [8.07](./data/fp2017_rate1/Qualcomm_8cx_Gen3_P_Core_O3_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3`）: [6.91](./data/fp2017_rate1/Intel_Core_i9-10980XE_O3_001.txt)
- Qualcomm 8cx Gen3 E Core @ 2.4 GHz Cortex-A78C（`-O3`）: [5.99](./data/fp2017_rate1/Qualcomm_8cx_Gen3_E_Core_O3_001.txt)
- Loongson 3A6000 @ 2.5 GHz LA664（`-O3`）: [5.57](./data/fp2017_rate1/Loongson_3A6000_O3_001.txt)

服务器平台（`-march=native`）：

- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3 -march=native`）: [8.87](./data/fp2017_rate1/AWS_Graviton_4_O3-march=native_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Ice Lake（`-O3 -march=native`）: [7.60](./data/fp2017_rate1/Intel_Xeon_Platinum_8358P_O3-march=native_001.txt)
- Intel Xeon D-2146NT @ 2.9 GHz Skylake（`-O3 -march=native`）: [5.48](./data/fp2017_rate1/Intel_Xeon_D-2146NT_O3-march=native_001.txt)

服务器平台：

- AMD EPYC 9R14 @ 3.7 GHz Zen 4（`-O3`）: [9.03](./data/fp2017_rate1/AMD_EPYC_9R14_O3_001.txt)
- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3`）: [8.75](./data/fp2017_rate1/AWS_Graviton_4_O3_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3`）: [8.19](./data/fp2017_rate1/Kunpeng_920_HuaweiCloud_kc2_O3_001.txt)
- Intel Xeon Platinum 8576C Emerald Rapids（`-O3`）: [8.14](./data/fp2017_rate1/Intel_Xeon_Platinum_8576C_O3_001.txt)
- AWS Graviton 3E @ 2.6 GHz Neoverse V1（`-O3`）: [8.10](./data/fp2017_rate1/AWS_Graviton_3E_O3_001.txt)
- AWS Graviton 3 @ 2.6 GHz Neoverse V1（`-O3`）: [7.80](./data/fp2017_rate1/AWS_Graviton_3_O3_001.txt)
- AMD EPYC 7K83 Zen 3（`-O3`）: [7.63](./data/fp2017_rate1/AMD_EPYC_7K83_O3_001.txt)
- T-Head Yitian 710 @ 3.0 GHz Neoverse N2（`-O3`）: [7.63](./data/fp2017_rate1/T-Head_Yitian_710_O3_001.txt)
- AMD EPYC 9754 @ 3.1 GHz Zen 4c（`-O3`）: [7.53](./data/fp2017_rate1/AMD_EPYC_9754_O3_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3`）: [7.12](./data/fp2017_rate1/AMD_EPYC_7742_O3_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Ice Lake（`-O3`）: [7.12](./data/fp2017_rate1/Intel_Xeon_Platinum_8358P_O3_001.txt)
- AMD EPYC 7H12 @ 3.3 GHz Zen 2（`-O3`）: [6.61](./data/fp2017_rate1/AMD_EPYC_7H12_O3_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3`）: [5.44](./data/fp2017_rate1/Intel_Xeon_E5-2680_v4_O3_001.txt)
- Ampere Altra @ 3.0 GHz Neoverse N1（`-O3`）: [5.26](./data/fp2017_rate1/Ampere_Altra_O3_001.txt)
- Intel Xeon E5-2680 v3 @ 3.3 GHz Haswell（`-O3`）: [5.15](./data/fp2017_rate1/Intel_Xeon_E5-2680_v3_O3_001.txt)
- Intel Xeon D-2146NT @ 2.9 GHz Skylake（`-O3`）: [5.00](./data/fp2017_rate1/Intel_Xeon_D-2146NT_O3_001.txt)
- Loongson 3C6000 @ 2.2 GHz LA664（`-O3`）: [4.94](./data/fp2017_rate1/Loongson_3C6000_O3_001.txt)
- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3`）: [3.47](./data/fp2017_rate1/AMD_EPYC_7551_O3_001.txt)
- Kunpeng 920 HuaweiCloud kc1 @ 2.6 GHz（`-O3`）: [3.17](./data/fp2017_rate1/Kunpeng_920_HuaweiCloud_kc1_O3_001.txt)
- Intel Xeon E5-2603 v4 @ 1.7 GHz Broadwell（`-O3`）: [3.14](./data/fp2017_rate1/Intel_Xeon_E5-2603_v4_O3_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3`）: [3.13](./data/fp2017_rate1/Kunpeng_920_O3_001.txt)
- Loongson 3C5000 @ 2.2 GHz LA464（`-O3`）: [2.85](./data/fp2017_rate1/Loongson_3C5000_O3_001.txt)

注：

1. SPEC FP 2017 Rate-1 结果受 `-march=native` 影响很明显，特别是有 AVX-512 的平台，因为不开 `-march=native` 时，默认情况下 SIMD 最多用到 SSE。
2. 部分内核版本（大约 6.7-6.11，在 6.12/6.11.7 中修复）会显著影响 503.bwaves_r 和 507.cactuBSSN_r 项目的性能，详见 [Intel Spots A 3888.9% Performance Improvement In The Linux Kernel From One Line Of Code](https://www.phoronix.com/news/Intel-Linux-3888.9-Performance)、[mm, mmap: limit THP alignment of anonymous mappings to PMD-aligned sizes](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=d4148aeab412432bf928f311eca8a2ba52bb05df) 和 [kernel 6.10 THP causes abysmal performance drop](https://bugzilla.suse.com/show_bug.cgi?id=1229012)。

### 网上的数据

[高通 X Elite Oryon 微架构评测：走走停停 by JamesAslan](https://zhuanlan.zhihu.com/p/704707254):

- Intel Core 13700K Raptor Lake: 14.56
- Qualcomm X1E80100 Oryon: 14.20
- AMD Ryzen 7700X Zen 4: 13.97
- Intel Core 12700K Alder Lake: 13.70
- Apple M2 Avalanche+Blizzard: 12.64
- AMD Ryzen 5950X Zen 3: 11.86
- Apple M1 Firestorm+Icestorm: 11.20
- Qualcomm 8 Gen 2 Cortex-X3: 9.91

[Running SPEC CPU2017 on Chinese CPUs, and More](https://old.chipsandcheese.com/2024/10/18/running-spec-cpu2017-on-chinese-cpus-and-more/)

- AMD Ryzen 9 7950X3D Non-VCache: 15.4
- Intel Core Ultra 7 258V Lion Cove: 13.9
- Intel Core Ultra 7 115H Redwood Cove: 12
- Intel Core Ultra 7 258V Skymont: 7.94
- Intel Core i5-6600K Skylake: 7.92
- Intel Core Ultra 7 115H Crestmont: 6.86
- Loongson 3A6000: 5.49
- Mediatek Genio 1200 Cortex A78: 5.09
- Intel Core Ultra 7 115H Low Power Crestmont: 4.32
- AMD FX-8150: 3.63
- Loongson 3A5000: 3.38
- Intel Celeron J4125 Goldmont Plus: 2.45
- Amlogic S922X Cortex A73: 2.01
- Zhaoxin KaiXian KX-6640MA: 1.97
- Mediatek Genio 1200 Cortex A55: 1.01

[Running SPEC CPU2017 at Chips and Cheese?](https://old.chipsandcheese.com/2024/09/19/running-spec-cpu2017-at-chips-and-cheese/)

- AMD Ryzen 9 9950X: 19.8
- AMD Ryzen 9 7950X3D Non-VCache: 15.3
- AMD Ryzen 9 7950X3D VCache: 12.7
- Intel Core Ultra 7 115H Redwood Cove: 11.2
- AMD Ryzen 9 3950X 3.5GHz: 7.26
- Intel Core Ultra 7 115H Crestmont: 5.83
- Ampere Altra: 5.62
- AmpereOne: 4.29
- AMD FX-8159: 3.47

[The AMD Ryzen 9 9950X and Ryzen 9 9900X Review: Flagship Zen 5 Soars - and Stalls](https://www.anandtech.com/show/21524/the-amd-ryzen-9-9950x-and-ryzen-9-9900x-review/5)

- AMD Ryzen 9 9950X Zen 5: 17.72
- Intel Core i9-14900K Raptor Lake: 16.90
- AMD Ryzen 9 7950X Zen 4: 14.26

[Snapdragon X Elite Qualcomm Oryon CPU Design and Architecture Hot Chips 2024](https://www.servethehome.com/snapdragon-x-elite-qualcomm-oryon-cpu-design-and-architecture-hot-chips-2024-arm/)

- Qualcomm X Elite Oryon on Linux: 17.77
- Qualcomm X Elite Oryon on Windows: 16.66

[ARM Cortex X1 微架构评测（上）：向山进发](https://zhuanlan.zhihu.com/p/619033328)

- Zen 3 @ 4.95 GHz: 11.9
- Firestorm @ 3.0 GHz: 11.2
- Cortex X1 @ 3.0 GHz: 8.9
- Cortex A78 @ 2.4 GHz: 5.9


## SPEC INT 2006 Speed

因为 GCC 没有自动并行化，所以都是单核运行。运行时间基本和分数成反比，乘积按 400000 估算。

下面贴出自己测的数据（SPECint2006，Estimated，speed，base），不保证满足 SPEC 的要求，仅供参考。

- Intel Core i9-14900K Raptor Lake（`-O3`）: [91.9](./data/int2006_speed/Intel_Core_i9-14900K_O3_001.txt)
- Intel Core i9-14900K Raptor Lake（`-O2`）: [87.2](./data/int2006_speed/Intel_Core_i9-14900K_O2_001.txt)
- Intel Core i9-13900K Raptor Lake（`-Ofast -fomit-frame-pointer -march=native -mtune=native`）: 85.3 86.8
- Intel Core i9-13900K Raptor Lake（`-O2`）: 79.6
- Intel Core i9-12900KS Alder Lake（`-O2`）: 74.4
- Intel Core i9-10980XE Cascade Lake（`-O2`）: 43.9
- Intel Xeon E5-2680 v3 Haswell（`-O2`）: 33.2
- POWER8NVL（`-O2`）: 26.5
- Kunpeng 920 TaiShan V110（`-Ofast -fomit-frame-pointer -march=native -mtune=native`）: 24.5
- Kunpeng 920 TaiShan V110（`-O2`）: 23.3

### 网上的数据

只考虑单核，不考虑 ICC 的自动多线程并行化。

[Anandtech 的数据](https://www.anandtech.com/show/16084/intel-tiger-lake-review-deep-dive-core-11th-gen/8)：

- Intel Core i9-10900K Comet Lake: 58.76
- AMD Ryzen 3950X Zen 2: 50.02
- AMD Ryzen 4800U Zen 2: 37.10
- Amazon Graviton 2 Neoverse-N1: 29.99

[Anandtech 的数据](https://www.anandtech.com/show/16252/mac-mini-apple-m1-tested/4)：

- Apple M1 Firestorm+Icestorm: 69.40
- AMD Ryzen 5950X Zen 3: 68.53
- Apple A14 Firestorm+Icestorm: 63.34
- Intel Core i9-10900K Comet Lake: 58.58
- Apple A13 Lightning+Thunder: 52.83
- AMD Ryzen 3950X Zen 2: 50.10
- AMD Ryzen 2700X Zen+: 39.01

[Anandtech 的数据](https://www.anandtech.com/show/14694/amd-rome-epyc-2nd-gen/9)：

- AMD EPYC 7742 Zen 2: 39.25
- AMD EPYC 7601 Zen 1: 31.45

[Baikal 的数据](https://www.163.com/dy/article/IB0CL7PU0511838M.html):

- Baikal-S：19
- Kunpeng 920 TSV110: 26

[龙芯 3A6000 新闻](https://www.ithome.com/0/709/460.htm)：

- Loongson 3A6000 LA664: 43.1

[龙芯 3A6000](https://www.bilibili.com/video/BV1am4y1x71V/):

- Loongson 3A6000 LA664: 43.1
- Intel Core i3-10100 Comet Lake: 42.5
- Hygon 3250: 39
- Kirin 990: 26.4
- Zhaoxin KX6780A: 20.5
- Phytium FT-D2000: 15.4
- Pangu M900: 12.4

[在龙芯 3A5000 上测试 SPEC CPU 2006](https://zhuanlan.zhihu.com/p/393600027):

- Loongson 3A5000 LA464: 26.6

[龙芯、海光、飞腾、兆芯同桌对比性能力求公平](https://zhuanlan.zhihu.com/p/627627813):

- Intel Core i9-10850K Comet Lake: 62.5
- AMD Ryzen 5600G: 48.2 59.9
- AMD Ryzen 2600: 36.1 40.5
- Intel Core i5-6500 Skylake: 40.1
- Hygon C86 3250: 30.5
- Loongson 3A5000HV LA464: 26.5
- Zhaoxin KX-U6780A: 15.5
- Phytium D2000: 15.3


## SPEC INT 2006 Rate

TODO

### 网上的数据

[Kunpeng 920 官方数据](https://www.hisilicon.com/en/products/Kunpeng/Huawei-Kunpeng/Huawei-Kunpeng-920)：

- Kunpeng 920 TSV110 64 Cores: >930

[夏晶的数据](https://www.zhihu.com/question/308299017/answer/592860614)：

- AMD Zen 2 64 Cores: ~1200
- Intel Skylake 8180 v5 28 Cores: ~750
- Cavium TX2 32 Cores: ~750
- AMD EPYC 7601 Zen 1 32 Cores: ~700
- Qualcomm 2400 48 Cores: ~650
- Phytium FT2000 64 Cores: ~600
- Intel 6148 Skylake 20 Cores: ~550

[龙芯 3A6000 新闻](https://www.ithome.com/0/709/460.htm)：

- Loongson 3A6000 LA664 4C 8T: 155

[龙芯、海光、飞腾、兆芯同桌对比性能力求公平](https://zhuanlan.zhihu.com/p/627627813):

- Intel Core i9-10850K Comet Lake 10C 20T: 328 349
- AMD Ryzen 5600G 6C 12T: 192 232 235 278
- AMD Ryzen 2600 6C 12T: 166 179 192 199
- Hygon C86 3250 8C 16T: 173 197
- Intel Core i5-6500 Skylake 4C: 113
- Phytium D2000 8C: 90.2
- Zhaoxin KX-U6780A 8C: 82.9
- Loongson 3A5000HV 4C: 81.2

## SPEC INT 2017 Speed

下面贴出自己测的数据（SPECint2017，Estimated，speed，base，单线程），不保证满足 SPEC 的要求，仅供参考。

运行时间基本和分数成反比，乘积按 1e5 估算。

- Intel Core i9-14900K Raptor Lake（`-O3`）: [12.1](./data/int2017_speed/Intel_Core_i9-14900K_O3_001.txt)
- Intel Core i9-12900KS Alder Lake（`-O3`）: [10.5](./data/int2017_speed/Intel_Core_i9-12900KS_O3_001.txt) [10.9](./data/int2017_speed/Intel_Core_i9-12900KS_O3_002.txt)
- Qualcomm X1E80100 X Elite（`-O3`）: [7.99](./data/int2017_speed/Qualcomm_X1E80100_O3_001.txt)
- Intel Core i9-10980XE Cascade Lake（`-O3`）: [7.18](./data/int2017_speed/Intel_Core_i9-10980XE_O3_001.txt)
- AMD EPYC 7742 Zen 2（`-O3`）: [5.55](./data/int2017_speed/AMD_EPYC_7742_O3_001.txt)
- Kunpeng 920 TaiShan V110（`-O3`）: [3.65](./data/int2017_speed/Kunpeng_920_O3_001.txt) [3.62](./data/int2017_speed/Kunpeng_920_O3_002.txt)

注：SPEC INT 2017 单线程 OpenMP 下 speed 测试按理说约等于 rate-1，前者虽然启用了 OpenMP，但仅允许单线程。不过实测下来还是不太一样。

## SPEC FP 2017 Speed

下面贴出自己测的数据（SPECfp2017，Estimated，speed，base，单线程），不保证满足 SPEC 的要求，仅供参考。

运行时间基本和分数成反比，乘积按 5e5 估算。

- Intel Core i9-14900K Raptor Lake（`-O3`）: [12.8](./data/fp2017_speed/Intel_Core_i9-14900K_O3_001.txt)
- Intel Core i9-12900KS Alder Lake（`-O3`）: [13.1](./data/fp2017_speed/Intel_Core_i9-12900KS_O3_001.txt)
- AMD EPYC 7742 Zen 2（`-O3`）: [6.99](./data/fp2017_speed/AMD_EPYC_7742_O3_001.txt)
- Intel Core i9-10980XE Cascade Lake（`-O3`）: [6.20](./data/fp2017_speed/Intel_Core_i9-10980XE_O3_001.txt)
- Kunpeng 920 TaiShan V110（`-O3`）: [2.57](./data/fp2017_speed/Kunpeng_920_O3_001.txt)

注：SPEC FP 2017 单线程 OpenMP 下 speed 测试不等价为 rate-1，因为跑的测试不同。

## SPEC 运行配置

### SPEC 2006

```
# match spec result standard
reportable = yes
# skip peak
basepeak = yes
# show live output
teeout = yes

# optimization flags for base
default=base=default=default:
COPTIMIZE = -O3 -fgnu89-inline -fcommon -fno-strict-aliasing
CXXOPTIMIZE = -O3 -fpermissive --std=c++98 -fno-strict-aliasing
FOPTIMIZE = -O3 -std=legacy -fno-strict-aliasing

# specify compilers
default=default=default=default:
CC = /usr/bin/gcc
CXX = /usr/bin/g++
FC = /usr/bin/gfortran

# fix compilation
default=base=default=default:
PORTABILITY = -DSPEC_CPU_LP64

400.perlbench=default=default=default:
CPORTABILITY = -DSPEC_CPU_LINUX_X64

462.libquantum=default=default=default:
CPORTABILITY = -DSPEC_CPU_LINUX

483.xalancbmk=default=default=default:
CXXPORTABILITY = -DSPEC_CPU_LINUX

481.wrf=default=default=default:
CPORTABILITY = -DSPEC_CPU_CASE_FLAG -DSPEC_CPU_LINUX
```

运行方式：

```shell
# int speed
cd /mnt && . ./shrc && runspec int
```

### SPEC 2017

```
# match spec result standard
reportable = yes
# skip peak
basepeak = yes
# show live output
teeout = yes
# speedup compilation
makeflags = --jobs=16

# compilers
default:
   preENV_LD_LIBRARY_PATH  = /usr/lib64:/usr/lib:/lib64
   SPECLANG                = /usr/bin/
   CC                      = $(SPECLANG)gcc -std=c99
   CXX                     = $(SPECLANG)g++
   FC                      = $(SPECLANG)gfortran
   # How to say "Show me your version, please"
   CC_VERSION_OPTION       = -v
   CXX_VERSION_OPTION      = -v
   FC_VERSION_OPTION       = -v

# perf: use runcpu --define perf=1 --noreportable to enable
%if %{perf} eq "1"
# override branch-misses counter if necessary
%ifndef %{branchmisses}
%define branchmisses branch-misses
%endif
default:
   command_add_redirect = 1
# bind to core if requested
%ifdef %{bindcore}
   monitor_wrapper = mkdir -p $[top]/result/perf.$lognum; echo "$command" > $[top]/result/perf.$lognum/$benchmark.cmd.$iter.\$\$; taskset -c %{bindcore} perf stat -x \\; -e instructions,cycles,branches,%{branchmisses},task-clock -o $[top]/result/perf.$lognum/$benchmark.perf.$iter.\$\$ $command
%else
   monitor_wrapper = mkdir -p $[top]/result/perf.$lognum; echo "$command" > $[top]/result/perf.$lognum/$benchmark.cmd.$iter.\$\$; perf stat -x \\; -e instructions,cycles,branches,%{branchmisses},task-clock -o $[top]/result/perf.$lognum/$benchmark.perf.$iter.\$\$ $command
%endif
%endif

# portability flags
default:
   EXTRA_PORTABILITY = -DSPEC_LP64
500.perlbench_r,600.perlbench_s:  #lang='C'
%if %{machine} eq "x86_64"
   PORTABILITY    = -DSPEC_LINUX_X64
%else
   PORTABILITY    = -DSPEC_LINUX_AARCH64
%endif

521.wrf_r,621.wrf_s:  #lang='F,C'
   CPORTABILITY  = -DSPEC_CASE_FLAG
   FPORTABILITY  = -fconvert=big-endian

523.xalancbmk_r,623.xalancbmk_s:  #lang='CXX'
   PORTABILITY   = -DSPEC_LINUX

526.blender_r:  #lang='CXX,C'
   PORTABILITY   = -funsigned-char -DSPEC_LINUX

527.cam4_r,627.cam4_s:  #lang='F,C'
   PORTABILITY   = -DSPEC_CASE_FLAG

628.pop2_s:  #lang='F,C'
   CPORTABILITY    = -DSPEC_CASE_FLAG
   FPORTABILITY    = -fconvert=big-endian

intspeed,fpspeed:
   EXTRA_OPTIMIZE = -fopenmp -DSPEC_OPENMP
fpspeed:
   #
   # 627.cam4 needs a big stack; the preENV will apply it to all
   # benchmarks in the set, as required by the rules.
   #
   preENV_OMP_STACKSIZE = 120M

default=base:         # flags for all base
%ifdef %{extralibs}
   EXTRA_LIBS     = %{extralibs}
%endif
%ifdef %{optflags}
   OPTIMIZE       = %{optflags}
%else
   OPTIMIZE       = -O3
%endif
   # -std=c++03 required for https://www.spec.org/cpu2017/Docs/benchmarks/510.parest_r.html
   CXXOPTIMIZE    = -std=c++03
   # -fallow-argument-mismatch required for https://www.spec.org/cpu2017/Docs/benchmarks/521.wrf_r.html
   FOPTIMIZE      = -fallow-argument-mismatch

intrate,intspeed=base: # flags for integer base
   EXTRA_COPTIMIZE = -fno-strict-aliasing -fno-unsafe-math-optimizations -fno-finite-math-only -fgnu89-inline -fcommon
# Notes about the above
#  - 500.perlbench_r/600.perlbench_s needs -fno-strict-aliasing, -fno-unsafe-math-optimizations and -fno-finite-math-only
#  - 502.gcc_r/602.gcc_s             needs -fgnu89-inline or -z muldefs
#  - 525.x264_r/625.x264_s           needs -fcommon
#  - For 'base', all benchmarks in a set must use the same options.
#  - Therefore, all base benchmarks get the above.  See:
#       https://www.spec.org/cpu2017/Docs/runrules.html#BaseFlags
#       https://www.spec.org/cpu2017/Docs/benchmarks/500.perlbench_r.html
#       https://www.spec.org/cpu2017/Docs/benchmarks/502.gcc_r.html
#       https://www.spec.org/cpu2017/Docs/benchmarks/525.x264_r.html

fprate,fpspeed=base: # flags for fp base
   EXTRA_COPTIMIZE = -Wno-error=implicit-int
# Notes about the above
#  - 527.cam4_r,627.cam4_s needs -Wno-error=implicit-int
```

运行方式：

```shell
# int speed
cd /mnt && . ./shrc && runcpu intspeed
# fp speed
ulimit -s unlimited && cd /mnt && . ./shrc && runcpu fpspeed
```

## 浮点峰值性能

| uArch              | DP FLOP/cycle | SP FLOP/cycle | ISA       |
|--------------------|---------------|---------------|-----------|
| AMD Zen 5          | 32            | 64            | AVX512F   |
| Intel Skylake Cove | 32            | 64            | AVX512F   |
| Intel Sunny Cove   | 32            | 64            | AVX512F   |
| AMD Zen 2          | 16            | 32            | FMA       |
| AMD Zen 3          | 16            | 32            | AVX512F   |
| AMD Zen 4          | 16            | 32            | AVX512F   |
| ARM Neoverse V1    | 16            | 32            | SVE(256b) |
| ARM Neoverse V2    | 16            | 32            | SVE(128b) |
| Apple Avalanche    | 16            | 32            | ASIMD     |
| Apple Firestorm    | 16            | 32            | ASIMD     |
| Intel Broadwell    | 16            | 32            | FMA       |
| Intel Golden Cove  | 16            | 32            | FMA       |
| Intel Haswell      | 16            | 32            | FMA       |
| Loongson LA464     | 16            | 32            | LASX      |
| Loongson LA664     | 16            | 32            | LASX      |
| Qualcomm Oryon     | 16            | 32            | ASIMD     |
| AMD Zen 1          | 8             | 16            | FMA       |
| ARM Cortex A78     | 8             | 16            | ASIMD     |
| ARM Cortex X1      | 8             | 16            | ASIMD     |
| ARM Icestorm       | 8             | 16            | ASIMD     |
| ARM Neoverse N1    | 8             | 16            | ASIMD     |
| ARM Neoverse N2    | 8             | 16            | SVE(128b) |
| Intel Gracemont    | 8             | 16            | FMA       |
| Hisilicon TSV110   | 4             | 16            | ASIMD     |

## 固定频率方法

可以尝试用 cpupower frequency-set 来固定频率，但是一些平台不支持，还可能有 Linux 内无法关闭的 Boost。设置频率后，用 `cpupower frequency-info` 验证：`current CPU frequency: 4.29 GHz (asserted by call to kernel)` 是否和预期频率一致并且不变。

对于 AMD CPU，在 Linux 下为了固定 CPU 的频率，需要通过 MSR 进行设置：[jiegec/ZenStates-Linux](https://github.com/jiegec/ZenStates-Linux)：

1. 关闭 Core performance boost
2. 读取当前的 pstate 设置
3. 修改当前 pstate 的 FID，也就修改了频率

## CPU 型号

下面给出测试的各 CPU 型号的官网链接：

- [AMD Ryzen 5 7500F](https://www.amd.com/en/products/processors/desktops/ryzen/7000-series/amd-ryzen-5-7500f.html): Max Boost Clock 5.0 GHz
- [AMD Ryzen 9 9950X](https://www.amd.com/en/products/processors/desktops/ryzen/9000-series/amd-ryzen-9-9950x.html): Max Boost Clock 5.7 GHz
- [AWS Gravition 2/3/3E/4](https://github.com/aws/aws-graviton-getting-started/blob/main/README.md)
- [Intel Core i9-10980XE](https://www.intel.com/content/www/us/en/products/sku/198017/intel-core-i910980xe-extreme-edition-processor-24-75m-cache-3-00-ghz/specifications.html): Max Boost Clock 4.8 GHz
- [Intel Core i9-12900KS](https://www.intel.com/content/www/us/en/products/sku/225916/intel-core-i912900ks-processor-30m-cache-up-to-5-50-ghz/specifications.html): Max Boost Clock 5.5 GHz
- [Intel Core i9-14900K](https://www.intel.com/content/www/us/en/products/sku/236773/intel-core-i9-processor-14900k-36m-cache-up-to-6-00-ghz/specifications.html): Max Boost Clock 6.0 GHz
- [Intel Xeon E5-2603 v4](https://www.intel.com/content/www/us/en/products/sku/92993/intel-xeon-processor-e52603-v4-15m-cache-1-70-ghz/specifications.html)
- [Qualcomm 8cx Gen3](https://www.qualcomm.com/products/mobile/snapdragon/laptops-and-tablets/snapdragon-mobile-compute-platforms/snapdragon-8cx-gen-3-compute-platform)
- [Qualcomm X Elite](https://www.qualcomm.com/products/mobile/snapdragon/laptops-and-tablets/snapdragon-x-elite)
