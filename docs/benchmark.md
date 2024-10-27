---
layout: page
date: 1970-01-01
permalink: /benchmark/
---

# 性能测试

## SPEC INT 2017 Rate-1

下面贴出自己测的数据（SPECint2017，Estimated，rate，base，1 copy），不保证满足 SPEC 的要求，仅供参考。

运行时间（秒）基本和分数成反比，乘积按 5e4 估算。

![](./data/int2017_rate1_score.svg)

![](./data/int2017_rate1_score_per_ghz.svg)

![](./data/int2017_rate1_ratio.svg)

![](./data/int2017_rate1_mpki.svg)

![](./data/int2017_rate1_ipc.svg)

![](./data/int2017_rate1_mispred.svg)

![](./data/int2017_rate1_freq.svg)

- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3 -flto`）: [11.7](./data/int2017_rate1/AMD_Ryzen_9_9950X_O3-flto_001.txt)
- Intel Core i9-14900K @ 6.0 GHz Raptor Lake（`-O3 -flto`）: [11.7](./data/int2017_rate1/Intel_Core_i9-14900K_O3-flto_001.txt) [11.7](./data/int2017_rate1/Intel_Core_i9-14900K_O3-flto_002.txt)
- Intel Core i9-14900K @ 6.0 GHz Raptor Lake（`-O3`）: [11.3](./data/int2017_rate1/Intel_Core_i9-14900K_O3_001.txt)
- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3`）: [11.2](./data/int2017_rate1/AMD_Ryzen_9_9950X_O3_001.txt)
- Intel Core i9-12900KS @ 5.5 GHz Alder Lake（`-O3 -flto`）: [9.97](./data/int2017_rate1/Intel_Core_i9-12900KS_O3-flto_001.txt)
- Intel Core i9-12900KS @ 5.5 GHz Alder Lake（`-O3`）: [9.62](./data/int2017_rate1/Intel_Core_i9-12900KS_O3_001.txt)
- AMD Ryzen 5 7500F Zen 4（`-O3`）: [8.73](./data/int2017_rate1/AMD_Ryzen_5_7500F_O3_001.txt)
- Qualcomm X1E80100 Boost @ 4.0 GHz X Elite（`-O3`）: [8.60](./data/int2017_rate1/Qualcom_X1E80100_O3_001.txt)
- Qualcomm X1E80100 Non-boost @ 3.4 GHz X Elite（`-O3`）: [7.56](./data/int2017_rate1/Qualcom_X1E80100_O3_001.txt)
- Intel Core i9-10980XE @ 4.8 GHz Cascade Lake（`-O3`）: [6.24](./data/int2017_rate1/Intel_Core_i9-10980XE_O3_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Ice Lake（`-O3`）: [5.66](./data/int2017_rate1/Intel_Xeon_Platinum_8358P_O3_001.txt)
- AMD EPYC 7742 Zen 2（`-O3`）: [4.67](./data/int2017_rate1/AMD_EPYC_7742_O3_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3`）: [4.35](./data/int2017_rate1/Intel_Xeon_E5-2680_v4_O3_001.txt)
- Intel Xeon E5-2680 v3 @ 3.0 GHz Haswell（`-O3`）: [4.01](./data/int2017_rate1/Intel_Xeon_E5-2680_v3_O3_001.txt)
- Intel Xeon D-2146NT @ 2.9 GHz Skylake（`-O3`）: [3.96](./data/int2017_rate1/Intel_Xeon_D-2146NT_O3_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3`）: [3.18](./data/int2017_rate1/Kunpeng-920_O3_001.txt)
- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3`）: [3.06](./data/int2017_rate1/AMD_EPYC_7551_O3_001.txt)

注：

1. SPEC INT 2017 Rate-1 结果受 `-flto` 影响很明显。
2. 在部分处理器上，Linux 不能保证程序被调度到性能最高的核心上，例如：
      1. Qualcomm X1E80100 上，负载不一定会调度到有 Boost 的核上，因此需要手动绑核。没有 Boost 的核心会跑在 3.4 GHz，Boost 的核心最高可以达到 4.0 GHz，对应 14% 的性能提升。具体地讲，它有三个 Cluster，0-3 是没有 Boost 的 Cluster，4-7 和 8-11 每个 Cluster 中可以有一个核心 Boost 到 4.0 GHz，也就是说，最多有两个核达到 4.0 GHz，这两个核需要分别位于 4-7 和 8-11 两个 Cluster 当中。如果一个 Cluster 有两个或者以上的核有负载，那么他们都只有 3.4 GHz。
      2. AMD Ryzen 9 9950X 不同核能够达到的最大频率不同，目前 Linux（6.11）的调度算法不一定可以保证跑到最大频率 5.75 GHz 上，可能会飘到频率低一些（5.45 GHz 左右）的核心上，损失 4% 的性能，因此需要绑核心，详见 [Linux 大小核的调度算法探究](./blog/posts/software/linux-core-scheduling.md) 以及 [谈谈 Linux 与 ITMT 调度器与多簇处理器](https://blog.hjc.im/thoughts-on-linux-preferred-cores-and-multi-ccx.html)。
3. 对于服务器 CPU，默认设置可能没有打开 C6 State，此时单核不一定能 Boost 到宣称的最高频率，需要进 BIOS 打开 C6 State，使得空闲的核心进入低功耗模式，才能发挥出最高的 Boost 频率。

x86 平台的分支预测准确率（Average）由高到低：

1. Zen 5(9950X): MPKI=4.33 Mispred=2.45%
2. Zen 2(7742): MPKI=4.62 Mispred=2.62%
3. Ice Lake(8358P)/Alder Lake(12900KS)/Raptor Lake(14900K): MPKI=4.71 Mispred=2.68%
4. Skylake(D-2146NT)/Cascade Lake(10980XE): MPKI=5.34 Mispred=3.04%
5. Zen 1(7551): MPKI=5.72 Mispred=3.26%
6. Haswell(E5-2680 v3)/Broadwell(E5-2680 v4): MPKI=5.84 Mispred=3.27%

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
- Qualcomm X Elite Oryon on Windows: 10.64

## SPEC FP 2017 Rate-1

下面贴出自己测的数据（SPECfp2017，Estimated，rate，base，1 copy），不保证满足 SPEC 的要求，仅供参考。

运行时间基本和分数成反比，乘积按 1e5 估算。

![](./data/fp2017_rate1_score.svg)

![](./data/fp2017_rate1_score_per_ghz.svg)

![](./data/fp2017_rate1_ratio.svg)

![](./data/fp2017_rate1_mpki.svg)

![](./data/fp2017_rate1_ipc.svg)

![](./data/fp2017_rate1_mispred.svg)

![](./data/fp2017_rate1_freq.svg)

- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3 -march=native`）: [17.6](./data/fp2017_rate1/AMD_Ryzen_9_9950X_O3-march=native_001.txt)
- Intel Core i9-14900K @ 6.0 GHz Raptor Lake（`-O3 -march=native`）: [16.6](./data/fp2017_rate1/Intel_Core_i9-14900K_O3-march=native_001.txt)
- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3`）: [16.5](./data/fp2017_rate1/AMD_Ryzen_9_9950X_O3_001.txt)
- Intel Core i9-14900K @ 6.0 GHz Raptor Lake（`-O3`）: [16.1](./data/fp2017_rate1/Intel_Core_i9-14900K_O3_001.txt)
- Intel Core i9-12900KS @ 5.5 GHz Alder Lake（`-O3`）: [14.3](./data/fp2017_rate1/Intel_Core_i9-12900KS_O3_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3`）: [13.9](./data/fp2017_rate1/Qualcom_X1E80100_O3_001.txt)
- AMD Ryzen 5 7500F Zen 4（`-O3`）: [11.6](./data/fp2017_rate1/AMD_Ryzen_5_7500F_O3_001.txt)
- Intel Core i9-10980XE Cascade Lake（`-O3 -march=native`）: [7.24](./data/fp2017_rate1/Intel_Core_i9-10980XE_O3-march=native_001.txt)
- AMD EPYC 7742 Zen 2（`-O3`）: [7.14](./data/fp2017_rate1/AMD_EPYC_7742_O3_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Ice Lake（`-O3 -march=native`）: [7.60](./data/fp2017_rate1/Intel_Xeon_Platinum_8358P_O3-march=native_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Ice Lake（`-O3`）: [7.12](./data/fp2017_rate1/Intel_Xeon_Platinum_8358P_O3_001.txt)
- Intel Core i9-10980XE Cascade Lake（`-O3`）: [6.91](./data/fp2017_rate1/Intel_Core_i9-10980XE_O3_001.txt)
- Intel Xeon D-2146NT @ 2.9 GHz Skylake（`-O3 -march=native`）: [5.48](./data/fp2017_rate1/Intel_Xeon_D-2146NT_O3-march=native_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3`）: [5.44](./data/fp2017_rate1/Intel_Xeon_E5-2680_v4_O3_001.txt)
- Intel Xeon E5-2680 v3 @ 3.3 GHz Haswell（`-O3`）: [5.15](./data/fp2017_rate1/Intel_Xeon_E5-2680_v3_O3_001.txt)
- Intel Xeon D-2146NT @ 2.9 GHz Skylake（`-O3`）: [5.00](./data/fp2017_rate1/Intel_Xeon_D-2146NT_O3_001.txt)
- AMD EPYC 7551 Zen 1（`-O3`）: [4.05](./data/fp2017_rate1/AMD_EPYC_7551_O3_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3`）: [3.20](./data/fp2017_rate1/Kunpeng-920_O3_001.txt)

SPEC FP 2017 Rate-1 结果受 `-march=native` 影响很明显，特别是有 AVX-512 的平台，因为不开 `-march=native` 时，默认情况下 SIMD 最多用到 SSE。

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
- Qualcomm X1E80100 X Elite（`-O3`）: [7.99](./data/int2017_speed/Qualcom_X1E80100_O3_001.txt)
- Intel Core i9-10980XE Cascade Lake（`-O3`）: [7.18](./data/int2017_speed/Intel_Core_i9-10980XE_O3_001.txt)
- AMD EPYC 7742 Zen 2（`-O3`）: [5.55](./data/int2017_speed/AMD_EPYC_7742_O3_001.txt)
- Kunpeng 920 TaiShan V110（`-O3`）: [3.65](./data/int2017_speed/Kunpeng-920_O3_001.txt) [3.62](./data/int2017_speed/Kunpeng-920_O3_002.txt)

注：SPEC INT 2017 单线程 OpenMP 下 speed 测试按理说约等于 rate-1，前者虽然启用了 OpenMP，但仅允许单线程。不过实测下来还是不太一样。

## SPEC FP 2017 Speed

下面贴出自己测的数据（SPECfp2017，Estimated，speed，base，单线程），不保证满足 SPEC 的要求，仅供参考。

运行时间基本和分数成反比，乘积按 5e5 估算。

- Intel Core i9-14900K Raptor Lake（`-O3`）: [12.8](./data/fp2017_speed/Intel_Core_i9-14900K_O3_001.txt)
- Intel Core i9-12900KS Alder Lake（`-O3`）: [13.1](./data/fp2017_speed/Intel_Core_i9-12900KS_O3_001.txt)
- AMD EPYC 7742 Zen 2（`-O3`）: [6.99](./data/fp2017_speed/AMD_EPYC_7742_O3_001.txt)
- Intel Core i9-10980XE Cascade Lake（`-O3`）: [6.20](./data/fp2017_speed/Intel_Core_i9-10980XE_O3_001.txt)
- Kunpeng 920 TaiShan V110（`-O3`）: [2.57](./data/fp2017_speed/Kunpeng-920_O3_001.txt)

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
default:
   command_add_redirect = 1
# bind to core if requested
%ifdef %{bindcore}
   monitor_wrapper = mkdir -p $[top]/result/perf.$lognum; echo "$command" > $[top]/result/perf.$lognum/$benchmark.cmd.$iter.\$\$; taskset -c %{bindcore} perf stat -x \\; -e instructions,cycles,branches,branch-misses,task-clock -o $[top]/result/perf.$lognum/$benchmark.perf.$iter.\$\$ $command
%else
   monitor_wrapper = mkdir -p $[top]/result/perf.$lognum; echo "$command" > $[top]/result/perf.$lognum/$benchmark.cmd.$iter.\$\$; perf stat -x \\; -e instructions,cycles,branches,branch-misses,task-clock -o $[top]/result/perf.$lognum/$benchmark.perf.$iter.\$\$ $command
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
%if %{fast} eq "1"
   OPTIMIZE       = -Ofast
%else
   OPTIMIZE       = -O3
%endif
%if %{native} eq "1"
   OPTIMIZE       += -march=native
%endif
%if %{lto} eq "1"
   OPTIMIZE       += -flto
%endif
   # -std=c++13 required for https://www.spec.org/cpu2017/Docs/benchmarks/510.parest_r.html
   CXXOPTIMIZE    = -std=c++03
   # -fallow-argument-mismatch required for https://www.spec.org/cpu2017/Docs/benchmarks/521.wrf_r.html
   FOPTIMIZE      = -fallow-argument-mismatch

intrate,intspeed=base: # flags for integer base
   EXTRA_COPTIMIZE = -fno-strict-aliasing -fgnu89-inline -fcommon
# Notes about the above
#  - 500.perlbench_r/600.perlbench_s needs -fno-strict-aliasing
#  - 502.gcc_r/602.gcc_s             needs -fgnu89-inline or -z muldefs
#  - 525.x264_r/625.x264_s           needs -fcommon
#  - For 'base', all benchmarks in a set must use the same options.
#  - Therefore, all base benchmarks get the above.  See:
#       https://www.spec.org/cpu2017/Docs/runrules.html#BaseFlags
#       https://www.spec.org/cpu2017/Docs/benchmarks/500.perlbench_r.html
#       https://www.spec.org/cpu2017/Docs/benchmarks/502.gcc_r.html
#       https://www.spec.org/cpu2017/Docs/benchmarks/525.x264_r.html
```

运行方式：

```shell
# int speed
cd /mnt && . ./shrc && runcpu intspeed
# fp speed
ulimit -s unlimited && cd /mnt && . ./shrc && runcpu fpspeed
```

## 浮点峰值性能

| uArch                         | DP FLOP/cycle | SP FLOP/cycle | ISA     |
|-------------------------------|---------------|---------------|---------|
| Skylake/Ice Lake/Cascade Lake | 32            | 64            | AVX512F |
| Golden Cove                   | 16            | 32            | FMA     |
| Zen 2/3                       | 16            | 32            | FMA     |
| Haswell/Broadwell             | 16            | 32            | FMA     |
| Gracemont                     | 8             | 16            | FMA     |
| Zen 1                         | 8             | 16            | FMA     |
| TSV110                        | 4             | 16            | ASIMD   |

## 固定频率方法

可以尝试用 cpupower frequency-set 来固定频率，但是一些平台不支持，还可能有 Linux 内无法关闭的 Boost。设置频率后，用 `cpupower frequency-info` 验证：`current CPU frequency: 4.29 GHz (asserted by call to kernel)` 是否和预期频率一致并且不变。

对于 AMD CPU，在 Linux 下为了固定 CPU 的频率，需要通过 MSR 进行设置：[jiegec/ZenStates-Linux](https://github.com/jiegec/ZenStates-Linux)：

1. 关闭 Core performance boost
2. 读取当前的 pstate 设置
3. 修改当前 pstate 的 FID，也就修改了频率
