---
layout: page
date: 1970-01-01
permalink: /benchmark/
---

# 性能测试

## 测试环境

测试环境如下：

1. 大部分测试：Debian Bookworm, GCC 12.2.0
2. LoongArch 测试：Debian Trixie, GCC 14.2.0，因为 Debian Bookworm 并不支持 LoongArch
3. HarmonyOS NEXT 测试：HarmonyOS NEXT 5，Clang 15.0.4 + Flang 20.1.7，详见 [jiegec/SPECCPU2017Harmony](https://github.com/jiegec/SPECCPU2017Harmony/tree/master/results)；X90 带有 VM 的代表是在 Linux 虚拟机中测试
4. 此外有针对不同编译器和编译器版本对比的测试，相关测试结果都进行了标注

预计等 Debian Trixie 发布后，尽量重跑一遍测试。经过测试，GCC 14 相比 GCC 12 对 SPEC 没有太多的性能影响，所以大体是可以比较的。而 GCC 15 则会对测试结果产生显著的差异。

## 注意事项

注意事项如下：

1. 分数只有在控制变量时（即一般所说的“用相同二进制测得”，此外还有一些影响性能的变量见下）可以用来比较**相同指令集**的不同处理器的性能，即通过测试结果比较：
      1. AMD64 指令集的 Intel 和 AMD 处理器的性能
      2. ARM64 指令集的 Apple、ARM、Huawei 和 Qualcomm 处理器的性能
      3. LoongArch 指令集的不同处理器的性能
2. 用分数来进行**不同指令集**的处理器之间的性能比较，则说服力较弱
3. 即使是相同硬件，如下因素都可能对测试结果产生**显著的影响**：
      1. 不同编译器（例如同等编译选项下 GCC 通常比 Clang 快）
      2. 不同编译器版本（通常新版本比旧版本快，但也有反例）
      3. 不同编译选项（例如是否开 LTO，是否设置 -march=native）
      4. 不同的内存分配器实现（libc 自带 malloc 或 jemalloc）
      5. 不同的标准库实现（比如 glibc 还是 musl）
      6. 不同的调频、调度或绑核策略（比如不当的绑核让频率从 4.0GHz 降到 3.4GHz）
      7. 不同的内核版本（比如部分内核版本会明显劣化性能）

简而言之，不给完整测试环境信息的前提下给出的分数，都是不靠谱的。

如果您需要引用本文的测试结果，请一定要列出该测试结果所使用的测试环境，并保证您对以上注意事项有充分的理解。

## SPEC INT 2017 Rate-1

下面贴出自己测的数据（SPECint2017，Estimated，rate，base，1 copy），不保证满足 SPEC 的要求，仅供参考。总运行时间（秒）基本和分数成反比，乘积按 5e4 估算。

### 数据总览

![](./data/int2017_rate1_score.svg)

![](./data/int2017_rate1_table.svg)

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

??? note "指令数"

    ![](./data/int2017_rate1_inst.svg)

### 原始数据

桌面平台（LTO + Jemalloc）：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3 -flto -ljemalloc`）: [9.13](./data/int2017_rate1/AMD_Ryzen_7_5700X_O3-flto-ljemalloc_001.txt)
- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3 -flto -ljemalloc`）: [12.9](./data/int2017_rate1/AMD_Ryzen_9_9950X_O3-flto-ljemalloc_001.txt)
- Apple M1 @ 3.2 GHz Firestorm（`-O3 -flto -ljemalloc`）: [8.93](./data/int2017_rate1/Apple_M1_O3-flto-ljemalloc_001.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3 -flto -ljemalloc`）: [3.52](./data/int2017_rate1/Apple_M1_E-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i9-10980XE @ 4.8 GHz Cascade Lake（`-O3 -flto -ljemalloc`）: [6.70](./data/int2017_rate1/Intel_Core_i9-10980XE_O3-flto-ljemalloc_001.txt)
- Intel Core i9-12900KS @ 5.5 GHz Golden Cove（`-O3 -flto -ljemalloc`）: [10.7](./data/int2017_rate1/Intel_Core_i9-12900KS_O3-flto-ljemalloc_001.txt)
- Intel Core i9-14900K @ 6.0 GHz Raptor Cove（`-O3 -flto -ljemalloc`）: [12.1](./data/int2017_rate1/Intel_Core_i9-14900K_O3-flto-ljemalloc_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3 -flto -ljemalloc`）: [8.71](./data/int2017_rate1/Intel_Xeon_w9-3595X_O3-flto-ljemalloc_001.txt)
- Loongson 3A6000 @ 2.5 GHz LA664（`-O3 -flto -ljemalloc`）: [4.86](./data/int2017_rate1/Loongson_3A6000_O3-flto-ljemalloc_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3 -flto -ljemalloc`）: [9.25](./data/int2017_rate1/Qualcomm_X1E80100_O3-flto-ljemalloc_001.txt)

桌面平台（LTO）：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3 -flto`）: [8.44](./data/int2017_rate1/AMD_Ryzen_7_5700X_O3-flto_001.txt)
- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3 -flto`）: [11.7](./data/int2017_rate1/AMD_Ryzen_9_9950X_O3-flto_001.txt)
- Apple M1 @ 3.2 GHz Firestorm（`-O3 -flto`）: [8.24](./data/int2017_rate1/Apple_M1_O3-flto_001.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3 -flto`）: [3.29](./data/int2017_rate1/Apple_M1_E-Core_O3-flto_001.txt)
- Huawei Kirin X90 E-Core @ 2.0 GHz（`-O3 -flto`）: [4.28](./data/int2017_rate1/Huawei_Kirin_X90_E-Core_O3-flto_001.txt)
- Huawei Kirin X90 P-Core @ 2.3 GHz（`-O3 -flto`）: [4.87](./data/int2017_rate1/Huawei_Kirin_X90_P-Core_O3-flto_001.txt)
- Intel Core i9-10980XE @ 4.8 GHz Cascade Lake（`-O3 -flto`）: [6.37](./data/int2017_rate1/Intel_Core_i9-10980XE_O3-flto_001.txt)
- Intel Core i9-12900KS @ 5.5 GHz Golden Cove（`-O3 -flto`）: [9.97](./data/int2017_rate1/Intel_Core_i9-12900KS_O3-flto_001.txt)
- Intel Core i9-14900K @ 6.0 GHz Raptor Cove（`-O3 -flto`）: [11.7](./data/int2017_rate1/Intel_Core_i9-14900K_O3-flto_001.txt) [11.7](./data/int2017_rate1/Intel_Core_i9-14900K_O3-flto_002.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3 -flto`）: [8.30](./data/int2017_rate1/Intel_Xeon_w9-3595X_O3-flto_001.txt)
- Loongson 3A6000 @ 2.5 GHz LA664（`-O3 -flto`）: [4.56](./data/int2017_rate1/Loongson_3A6000_O3-flto_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3 -flto`）: [8.62](./data/int2017_rate1/Qualcomm_X1E80100_O3-flto_001.txt)

桌面平台：

- AMD Ryzen 5 7500F @ 5.0 GHz Zen 4（`-O3`）: [9.51](./data/int2017_rate1/AMD_Ryzen_5_7500F_O3_001.txt)
- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3`）: [7.87](./data/int2017_rate1/AMD_Ryzen_7_5700X_O3_001.txt)
- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3`）: [11.2](./data/int2017_rate1/AMD_Ryzen_9_9950X_O3_001.txt) [11.3](./data/int2017_rate1/AMD_Ryzen_9_9950X_O3_002.txt)
- Apple M1 @ 3.2 GHz Firestorm（`-O3`）: [7.85](./data/int2017_rate1/Apple_M1_O3_001.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3`）: [3.15](./data/int2017_rate1/Apple_M1_E-Core_O3_001.txt)
- Huawei Kirin X90 VM P-Core @ 2.3 GHz（`-O3`）: [4.07](./data/int2017_rate1/Huawei_Kirin_X90_VM_P-Core_O3_001.txt)
- Intel Core i9-10980XE @ 4.8 GHz Cascade Lake（`-O3`）: [6.24](./data/int2017_rate1/Intel_Core_i9-10980XE_O3_001.txt)
- Intel Core i9-12900KS @ 5.5 GHz Golden Cove（`-O3`）: [9.62](./data/int2017_rate1/Intel_Core_i9-12900KS_O3_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3`）: [6.08](./data/int2017_rate1/Intel_Core_i9-12900KS_E-Core_O3_001.txt)
- Intel Core i9-14900K @ 6.0 GHz Raptor Cove（`-O3`）: [11.3](./data/int2017_rate1/Intel_Core_i9-14900K_O3_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3`）: [7.03](./data/int2017_rate1/Intel_Core_i9-14900K_E-Core_O3_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3`）: [8.05](./data/int2017_rate1/Intel_Xeon_w9-3595X_O3_001.txt)
- Loongson 3A6000 @ 2.5 GHz LA664（`-O3`）: [4.35](./data/int2017_rate1/Loongson_3A6000_O3_001.txt) [4.39](./data/int2017_rate1/Loongson_3A6000_O3_002.txt)
- Qualcomm 8cx Gen3 @ 3.0 GHz Cortex-X1C（`-O3`）: [5.73](./data/int2017_rate1/Qualcomm_8cx_Gen3_O3_001.txt)
- Qualcomm 8cx Gen3 E-Core @ 2.4 GHz Cortex-A78C（`-O3`）: [4.11](./data/int2017_rate1/Qualcomm_8cx_Gen3_E-Core_O3_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3`）: [8.31](./data/int2017_rate1/Qualcomm_X1E80100_O3_001.txt)

服务器平台（LTO + Jemalloc）：

- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3 -flto -ljemalloc`）: [5.33](./data/int2017_rate1/AMD_EPYC_7742_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9754 @ 3.1 GHz Zen 4c（`-O3 -flto -ljemalloc`）: [5.79](./data/int2017_rate1/AMD_EPYC_9754_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9755 @ 4.1 GHz Zen 5（`-O3 -flto -ljemalloc`）: [9.66](./data/int2017_rate1/AMD_EPYC_9755_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9K85 @ 4.1 GHz Zen 5（`-O3 -flto -ljemalloc`）: [9.48](./data/int2017_rate1/AMD_EPYC_9K85_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9K65 @ 3.7 GHz Zen 5c（`-O3 -flto -ljemalloc`）: [8.19](./data/int2017_rate1/AMD_EPYC_9K65_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9R14 @ 3.7 GHz Zen 4（`-O3 -flto -ljemalloc`）: [7.21](./data/int2017_rate1/AMD_EPYC_9R14_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9T24 @ 3.7 GHz Zen 4（`-O3 -flto -ljemalloc`）: [7.62](./data/int2017_rate1/AMD_EPYC_9T24_O3-flto-ljemalloc_001.txt)
- AWS Graviton 3 @ 2.6 GHz Neoverse V1（`-O3 -flto -ljemalloc`）: [5.24](./data/int2017_rate1/AWS_Graviton_3_O3-flto-ljemalloc_001.txt)
- AWS Graviton 3E @ 2.6 GHz Neoverse V1（`-O3 -flto -ljemalloc`）: [6.17](./data/int2017_rate1/AWS_Graviton_3E_O3-flto-ljemalloc_001.txt)
- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3 -flto -ljemalloc`）: [7.64](./data/int2017_rate1/AWS_Graviton_4_O3-flto-ljemalloc_001.txt) [7.41](./data/int2017_rate1/AWS_Graviton_4_O3-flto-ljemalloc_002.txt)
- Hygon C86 7390（`-O3 -flto -ljemalloc`）: [3.29](./data/int2017_rate1/Hygon_C86_7390_O3-flto-ljemalloc_001.txt)
- IBM POWER8NVL @ 4.0 GHz POWER8（`-O3 -flto -ljemalloc`）: [4.02](./data/int2017_rate1/IBM_POWER8NVL_O3-flto-ljemalloc_001.txt)
- Intel Xeon 6981E Crestmont（`-O3 -flto -ljemalloc`）: [4.79](./data/int2017_rate1/Intel_Xeon_6981E_O3-flto-ljemalloc_001.txt)
- Intel Xeon 6982P-C @ 3.6 GHz Redwood Cove（`-O3 -flto -ljemalloc`）: [7.22](./data/int2017_rate1/Intel_Xeon_6982P-C_O3-flto-ljemalloc_001.txt)
- Intel Xeon Platinum 8581C @ 3.4 GHz Raptor Cove（`-O3 -flto -ljemalloc`）: [6.87](./data/int2017_rate1/Intel_Xeon_Platinum_8581C_O3-flto-ljemalloc_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3 -flto -ljemalloc`）: [3.57](./data/int2017_rate1/Kunpeng_920_O3-flto-ljemalloc_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3 -flto -ljemalloc`）: [6.03](./data/int2017_rate1/Kunpeng_920_HuaweiCloud_kc2_O3-flto-ljemalloc_001.txt)
- Loongson 3C6000 @ 2.2 GHz LA664（`-O3 -flto -ljemalloc`）: [4.54](./data/int2017_rate1/Loongson_3C6000_O3-flto-ljemalloc_001.txt)

服务器平台（LTO）：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3 -flto`）: [3.19](./data/int2017_rate1/AMD_EPYC_7551_O3-flto_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3 -flto`）: [5.02](./data/int2017_rate1/AMD_EPYC_7742_O3-flto_001.txt)
- AMD EPYC 9754 @ 3.1 GHz Zen 4c（`-O3 -flto`）: [5.48](./data/int2017_rate1/AMD_EPYC_9754_O3-flto_001.txt)
- AMD EPYC 9755 @ 4.1 GHz Zen 5（`-O3 -flto`）: [8.97](./data/int2017_rate1/AMD_EPYC_9755_O3-flto_001.txt)
- AMD EPYC 9K65 @ 3.7 GHz Zen 5c（`-O3 -flto`）: [7.78](./data/int2017_rate1/AMD_EPYC_9K65_O3-flto_001.txt)
- AMD EPYC 9K85 @ 4.1 GHz Zen 5（`-O3 -flto`）: [8.83](./data/int2017_rate1/AMD_EPYC_9K85_O3-flto_001.txt)
- AMD EPYC 9R14 @ 3.7 GHz Zen 4（`-O3 -flto`）: [6.62](./data/int2017_rate1/AMD_EPYC_9R14_O3-flto_001.txt)
- AMD EPYC 9T24 @ 3.7 GHz Zen 4（`-O3 -flto`）: [7.14](./data/int2017_rate1/AMD_EPYC_9T24_O3-flto_001.txt)
- AWS Graviton 3 @ 2.6 GHz Neoverse V1（`-O3 -flto`）: [5.68](./data/int2017_rate1/AWS_Graviton_3_O3-flto_001.txt)
- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3 -flto`）: [7.14](./data/int2017_rate1/AWS_Graviton_4_O3-flto_001.txt) [6.53](./data/int2017_rate1/AWS_Graviton_4_O3-flto_002.txt) [6.51](./data/int2017_rate1/AWS_Graviton_4_O3-flto_003.txt)
- Hygon C86 7390（`-O3 -flto`）: [3.09](./data/int2017_rate1/Hygon_C86_7390_O3-flto_001.txt)
- Intel Xeon 6981E Crestmont（`-O3 -flto`）: [4.62](./data/int2017_rate1/Intel_Xeon_6981E_O3-flto_001.txt)
- Intel Xeon 6982P-C @ 3.6 GHz Redwood Cove（`-O3 -flto`）: [6.90](./data/int2017_rate1/Intel_Xeon_6982P-C_O3-flto_001.txt)
- Intel Xeon Platinum 8581C @ 3.4 GHz Raptor Cove（`-O3 -flto`）: [6.67](./data/int2017_rate1/Intel_Xeon_Platinum_8581C_O3-flto_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3 -flto`）: [3.26](./data/int2017_rate1/Kunpeng_920_O3-flto_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3 -flto`）: [5.71](./data/int2017_rate1/Kunpeng_920_HuaweiCloud_kc2_O3-flto_001.txt)
- Loongson 3C6000 @ 2.2 GHz LA664（`-O3 -flto`）: [4.39](./data/int2017_rate1/Loongson_3C6000_O3-flto_001.txt) [4.37](./data/int2017_rate1/Loongson_3C6000_O3-flto_002.txt)

服务器平台：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3`）: [3.07](./data/int2017_rate1/AMD_EPYC_7551_O3_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3`）: [4.73](./data/int2017_rate1/AMD_EPYC_7742_O3_001.txt)
- AMD EPYC 7H12 @ 3.3 GHz Zen 2（`-O3`）: [4.23](./data/int2017_rate1/AMD_EPYC_7H12_O3_001.txt)
- AMD EPYC 7K83 Zen 3（`-O3`）: [5.18](./data/int2017_rate1/AMD_EPYC_7K83_O3_001.txt)
- AMD EPYC 9754 @ 3.1 GHz Zen 4c（`-O3`）: [5.33](./data/int2017_rate1/AMD_EPYC_9754_O3_001.txt)
- AMD EPYC 9755 @ 4.1 GHz Zen 5（`-O3`）: [8.57](./data/int2017_rate1/AMD_EPYC_9755_O3_001.txt)
- AMD EPYC 9K65 @ 3.7 GHz Zen 5c（`-O3`）: [7.47](./data/int2017_rate1/AMD_EPYC_9K65_O3_001.txt)
- AMD EPYC 9K85 @ 4.1 GHz Zen 5（`-O3`）: [8.44](./data/int2017_rate1/AMD_EPYC_9K85_O3_001.txt)
- AMD EPYC 9R14 @ 3.7 GHz Zen 4（`-O3`）: [6.57](./data/int2017_rate1/AMD_EPYC_9R14_O3_001.txt) [6.41](./data/int2017_rate1/AMD_EPYC_9R14_O3_002.txt)
- AMD EPYC 9T24 @ 3.7 GHz Zen 4（`-O3`）: [6.94](./data/int2017_rate1/AMD_EPYC_9T24_O3_001.txt)
- AWS Graviton 3 @ 2.6 GHz Neoverse V1（`-O3`）: [5.43](./data/int2017_rate1/AWS_Graviton_3_O3_001.txt)
- AWS Graviton 3E @ 2.6 GHz Neoverse V1（`-O3`）: [5.53](./data/int2017_rate1/AWS_Graviton_3E_O3_001.txt)
- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3`）: [7.00](./data/int2017_rate1/AWS_Graviton_4_O3_001.txt) [6.85](./data/int2017_rate1/AWS_Graviton_4_O3_002.txt)
- Ampere Altra @ 3.0 GHz Neoverse N1（`-O3`）: [4.41](./data/int2017_rate1/Ampere_Altra_O3_001.txt)
- Hygon C86 7390（`-O3`）: [2.97](./data/int2017_rate1/Hygon_C86_7390_O3_001.txt)
- IBM POWER8NVL @ 4.0 GHz POWER8（`-O3`）: [3.54](./data/int2017_rate1/IBM_POWER8NVL_O3_001.txt)
- Intel Xeon 6982P-C @ 3.6 GHz Redwood Cove（`-O3`）: [6.68](./data/int2017_rate1/Intel_Xeon_6982P-C_O3_001.txt)
- Intel Xeon 6981E Crestmont（`-O3`）: [4.48](./data/int2017_rate1/Intel_Xeon_6981E_O3_001.txt)
- Intel Xeon D-2146NT @ 2.9 GHz Skylake（`-O3`）: [3.96](./data/int2017_rate1/Intel_Xeon_D-2146NT_O3_001.txt)
- Intel Xeon E5-2603 v4 @ 1.7 GHz Broadwell（`-O3`）: [2.48](./data/int2017_rate1/Intel_Xeon_E5-2603_v4_O3_001.txt)
- Intel Xeon E5-2680 v3 @ 3.0 GHz Haswell（`-O3`）: [4.01](./data/int2017_rate1/Intel_Xeon_E5-2680_v3_O3_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3`）: [4.35](./data/int2017_rate1/Intel_Xeon_E5-2680_v4_O3_001.txt)
- Intel Xeon E5-4610 v2 @ 2.7 GHz Ivy Bridge EP（`-O3`）: [3.06](./data/int2017_rate1/Intel_Xeon_E5-4610_v2_O3_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Sunny Cove（`-O3`）: [5.66](./data/int2017_rate1/Intel_Xeon_Platinum_8358P_O3_001.txt)
- Intel Xeon Platinum 8576C Raptor Cove（`-O3`）: [5.72](./data/int2017_rate1/Intel_Xeon_Platinum_8576C_O3_001.txt)
- Intel Xeon Platinum 8581C @ 3.4 GHz Raptor Cove（`-O3`）: [6.52](./data/int2017_rate1/Intel_Xeon_Platinum_8581C_O3_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3`）: [3.10](./data/int2017_rate1/Kunpeng_920_O3_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3`）: [5.53](./data/int2017_rate1/Kunpeng_920_HuaweiCloud_kc2_O3_001.txt)
- Loongson 3C5000 @ 2.2 GHz LA464（`-O3`）: [2.63](./data/int2017_rate1/Loongson_3C5000_O3_001.txt)
- Loongson 3C6000 @ 2.2 GHz LA664（`-O3`）: [4.19](./data/int2017_rate1/Loongson_3C6000_O3_001.txt) [4.14](./data/int2017_rate1/Loongson_3C6000_O3_002.txt)
- T-Head Yitian 710 @ 3.0 GHz Neoverse N2（`-O3`）: [5.79](./data/int2017_rate1/T-Head_Yitian_710_O3_001.txt)

手机平台（LTO）：

- Huawei Kirin 9010 E-Core Full @ 2.2 GHz（`-O3 -flto`）: [3.21](./data/int2017_rate1/Huawei_Kirin_9010_E-Core_Full_O3-flto_001.txt)
- Huawei Kirin 9010 P-Core Best @ 2.3 GHz（`-O3 -flto`）: [4.18](./data/int2017_rate1/Huawei_Kirin_9010_P-Core_Best_O3-flto_001.txt)
- Huawei Kirin 9010 P-Core Full @ 2.3 GHz（`-O3 -flto`）: [3.96](./data/int2017_rate1/Huawei_Kirin_9010_P-Core_Full_O3-flto_001.txt)

注：

1. SPEC INT 2017 Rate-1 结果受 `-flto`（分数 +4%，主要优化 mcf/deepsjeng）和 `-ljemalloc`（分数 +4-10%，主要优化 omnetpp/xalancbmk）影响很明显。`-Ofast` 和 `-O3` 区别很小，`-march=native` 影响很小。
2. 在部分处理器上，Linux 不能保证程序被调度到性能最高的核心上，例如：
      1. Qualcomm X1E80100 上，负载不一定会调度到有 Boost 的核上，因此需要手动绑核。没有 Boost 的核心会跑在 3.4 GHz，Boost 的核心最高可以达到 4.0 GHz，对应 14% 的性能提升。具体地讲，它有三个 Cluster，0-3 是没有 Boost 的 Cluster，4-7 和 8-11 每个 Cluster 中可以有一个核心 Boost 到 4.0 GHz，也就是说，最多有两个核达到 4.0 GHz，这两个核需要分别位于 4-7 和 8-11 两个 Cluster 当中。如果一个 Cluster 有两个或者以上的核有负载，那么他们都只有 3.4 GHz。
      2. AMD Ryzen 9 9950X 不同核能够达到的最大频率不同，目前 Linux（6.11）的调度算法不一定可以保证跑到最大频率 5.75 GHz 上，可能会飘到频率低一些（5.45 GHz 左右）的核心上，损失 4% 的性能，因此需要绑核心，详见 [Linux 大小核的调度算法探究](./blog/posts/software/linux-core-scheduling.md) 以及 [谈谈 Linux 与 ITMT 调度器与多簇处理器](https://blog.hjc.im/thoughts-on-linux-preferred-cores-and-multi-ccx.html)。这个问题已经有 Patch 进行修复。
3. 对于服务器 CPU，默认设置可能没有打开 C6 State，此时单核不一定能 Boost 到宣称的最高频率，需要进 BIOS 打开 C6 State，使得空闲的核心进入低功耗模式，才能发挥出最高的 Boost 频率。
4. 对于除了苹果以外的 ARM64 核心，内核的 branch-misses 计数器考虑了 speculative 而不只是 retired，因此数字会偏高，此时要用 r22 计数替代。
5. Google Cloud 只有部分机型（如 C4 和 C4A）支持 PMU，并且需要手动开启（参考 [Enable the PMU in VMs](https://cloud.google.com/compute/docs/enable-pmu-in-vms)）：

      ```shell
      $ gcloud compute instances export VM_NAME \
          --destination=YAML_FILE \
          --zone=ZONE
      $ vim YAML_FILE
      # append the following lines
      advancedMachineFeatures:
        performanceMonitoringUnit: STANDARD
      $ gcloud compute instances update-from-file VM_NAME \
          --most-disruptive-allowed-action=RESTART \
          --source=YAML_FILE \
          --zone=ZONE
      ```
6. 华为云的 kc2 实例的 PMU 默认不开启，需要通过工单申请，步骤如下：
      1. 创建一个私有镜像（可以先用公共镜像起一个虚拟机，再从虚拟机创建私有镜像）
      2. 创建工单申请，申请给私有镜像启用 PMU
      3. 用私有镜像创建新的虚拟机，在这个虚拟机内就可以使用 PMU：
            ```shell
            root@kc2 ~# dmesg | grep PMU
            [    1.196145] hw perfevents: enabled with armv8_pmuv3_0 PMU driver, 9 counters available
            ```
7. Kirin 9010 因为散热问题，单独跑测试，和顺着跑一遍测试，结果差距比较大。因此提供了两组数据：Best（每一项单独跑，取最短时间，散热影响比较小）和 Full（按照顺序跑一次，散热影响比较大）。

### 分支预测器比较

x86 平台的分支预测准确率（Average）由高到低（`-O3`）：

1. Zen 5(AMD 9950X/AMD 9755/AMD 9K85): MPKI=4.48 Mispred=2.52%
2. Zen 5c(AMD 9K65): MPKI=4.51 Mispred=2.54%
3. Zen 4(AMD 9T24/9R14): MPKI=4.57 Mispred=2.57%
4. Zen 4c(AMD 9754): MPKI=4.66 Mispred=2.63%
5. Zen 4(AMD 7500F): MPKI=4.68 Mispred=2.64%
6. Zen 3(AMD 5700X): MPKI=4.68 Mispred=2.64%
7. Zen 2(AMD 7742): MPKI=4.77 Mispred=2.69%
8. Redwood Cove(Intel 6982P-C): MPKI=4.77 Mispred=2.71%
9. Sunny Cove(Intel 8358P)/Golden Cove(Intel 12900KS)/Raptor Cove(Intel 14900K/Intel 8581C): MPKI=4.86 Mispred=2.75%
10. Gracemont(Intel 12900KS/Intel 14900K): MPKI=5.15 Mispred=2.92%
11. Skylake(Intel D-2146NT)/Cascade Lake(Intel 10980XE): MPKI=5.50 Mispred=3.13%
12. Zen 1(AMD 7551): MPKI=5.82 Mispred=3.31%
13. Haswell(Intel E5-2680 v3)/Broadwell(Intel E5-2680 v4): MPKI=5.98 Mispred=3.34%

x86 平台的分支预测准确率（Average）由高到低（`-O3 -flto`）：

1. Zen 5(AMD 9950X/AMD 9755): MPKI=5.35 Mispred=3.07%
2. Zen 5c(AMD 9K65)/Zen 5(AMD 9K85): MPKI=5.42 Mispred=3.10%
3. Zen 2(AMD 7742): MPKI=5.52 Mispred=3.17%
4. Zen 3(AMD 5700X): MPKI=5.55 Mispred=3.19%
5. Zen 4(AMD 9T24/AMD 9R14): MPKI=5.57 Mispred=3.19%
6. Redwood Cove(Intel 6982P-C): MPKI=5.70 Mispred=3.29%
7. Golden Cove(Intel 12900KS)/Raptor Cove(Intel 14900K/Intel 8581C): MPKI=5.81 Mispred=3.37%
8. Cascade Lake(Intel 10980XE): MPKI=6.55 Mispred=3.83%
9. Zen 1(AMD 7551): MPKI=6.86 Mispred=4.02%

ARM64 平台的分支预测准确率（Average）由高到低（`-O3`）：

1. Neoverse V2(AWS Graviton 4): MPKI=4.50 Mispred=2.47%
2. Oryon(Qualcomm X1E80100): MPKI=4.71 Mispred=2.58%
3. Neoverse N2(Aliyun Yitian 710): MPKI=4.80 Mispred=2.64%
4. Firestorm(Apple M1): MPKI=4.81 Mispred=2.62%
5. Neoverse V1(AWS Graviton 3/AWS Graviton 3E)/Cortex X1C(Qualcomm 8cx Gen3): MPKI=4.91 Mispred=2.69%
6. HuaweiCloud kc2: MPKI=5.17 Mispred=2.85%
7. Neoverse N1(Ampere Altra)/Cortex A78C(Qualcomm 8cx Gen3 E-Core): MPKI=5.21 Mispred=2.87%
8. Icestorm(Apple M1 E-Core): MPKI=5.41 Mispred=2.99%
9. TSV110(Hisilicon Kunpeng 920): MPKI=6.54 Mispred=3.58%

ARM64 平台的分支预测准确率（Average）由高到低（`-O3 -flto`）：

1. Neoverse V2(AWS Graviton 4): MPKI=5.19 Mispred=3.03%
2. Oryon(Qualcomm X1E80100): MPKI=5.41 Mispred=3.13%
3. Firestorm(Apple M1): MPKI=5.45 Mispred=3.14%
4. Neoverse V1(AWS Graviton 3): MPKI=5.64 Mispred=3.27%
5. HuaweiCloud kc2: MPKI=6.00 Mispred=3.50%
6. Icestorm(Apple M1 E-Core): MPKI=6.10 Mispred=3.56%
7. TSV110(Hisilicon Kunpeng 920): MPKI=6.74 Mispred=3.98%

LoongArch64 平台的分支预测准确率（Average）由高到低（`-O3`）：

1. LA664(3A6000/3C6000): MPKI=5.01 Mispred=2.79%
2. LA464(3C5000): MPKI=8.39 Mispred=4.21%

### 网上的数据

[SPEC CPU 2017 by David Huang](https://blog.hjc.im/spec-cpu-2017):

- Apple M4 Pro: 13.7
- AMD Ryzen 9950X Zen 5: 12.6
- Apple M3 Pro: 11.8
- Intel Core 13900K Raptor Cove: 11.5
- Intel Core Ultra 7 265K Arrow Lake Lion Cove+Skymont: 11.1
- AMD AI Max+ 395 Zen 5: 10.6
- Apple M2 Pro: 10.3
- Apple M2: 9.95
- AMD HX 370 Strix Point Zen 5: 9.64
- Intel Core Ultra 258V Lunar Lake Lion Cove+Skymont: 9.46
- Apple M1 Max Firestorm: 9.2
- AMD Ryzen 5950X Zen 3: 9.15
- Kunpeng 920 TSV120: 6.00
- Loongson 3A6000 LA664: 4.29
- Phytium D3000 FTC862: 4.24
- Loongson 3A5000 LA464: 3.04

[高通 X Elite Oryon 微架构评测：走走停停 by JamesAslan](https://zhuanlan.zhihu.com/p/704707254):

- AMD Ryzen 7700X Zen 4: 10.35
- Intel Core 13700K Raptor Cove: 9.81
- Intel Core 12700K Golden Cove: 9.13
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
- Loongson 3A6000 LA664: 4.27
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
- Intel Core i9-14900K Raptor Cove: 10.94
- AMD Ryzen 9 7950X Zen 4: 9.88

[Snapdragon X Elite Qualcomm Oryon CPU Design and Architecture Hot Chips 2024](https://www.servethehome.com/snapdragon-x-elite-qualcomm-oryon-cpu-design-and-architecture-hot-chips-2024-arm/)

- Qualcomm X Elite Oryon on Linux: 10.64
- Qualcomm X Elite Oryon on Windows: 9.70

[ARM Cortex X1 微架构评测（上）：向山进发](https://zhuanlan.zhihu.com/p/619033328)

- Zen 3 @ 4.95 GHz: 8.4
- Firestorm @ 3.0 GHz: 7.4
- Cortex X1 @ 3.0 GHz: 5.7
- Cortex A78 @ 2.4 GHz: 3.9

[极客湾•麒麟 9010，测评汇总：IPC 性能，巨幅提升！CPU 能效全频段领先，麒麟 9000S！](https://www.bilibili.com/opus/925502754370093090)

- Huawei Kirin 9010: 4.54
- HUawei Kirin 9000s: 4.06

### 多版本 GCC 和 LLVM 性能比较

在 Intel i9-14900K @ 5.7 GHz 上用 -O3 测试几种编译器组合的性能：

| Benchmark       | GCC 15 | GCC 14 | GCC 13 | GCC 12 | GCC 11 | LLVM 19 | LLVM 18 | LLVM 17 | LLVM 20 | LLVM 20 w/ -fwrapv |
|-----------------|--------|--------|--------|--------|--------|---------|---------|---------|---------|--------------------|
| 500.perlbench_r | 12.0   | 11.8   | 12.0   | 12.3   | 12.3   | 10.9    | 10.9    | 10.8    | 10.8    | 10.9               |
| 502.gcc_r       | 14.0   | 13.7   | 13.7   | 13.6   | 13.5   | 13.5    | 13.5    | 13.5    | 13.5    | 13.5               |
| 505.mcf_r       | 9.34   | 9.48   | 9.19   | 9.32   | 9.38   | 8.32    | 8.40    | 8.76    | 8.27    | 8.26               |
| 520.omnetpp_r   | 9.39   | 9.07   | 8.87   | 9.17   | 9.17   | 8.78    | 8.80    | 8.77    | 8.74    | 8.73               |
| 523.xalancbmk_r | 8.91   | 8.91   | 8.95   | 8.85   | 9.11   | 8.88    | 8.86    | 8.85    | 8.86    | 8.83               |
| 525.x264_r      | 23.7   | 19.7   | 18.6   | 18.5   | 19.4   | 19.5    | 18.8    | 18.5    | 19.9    | 20.0               |
| 531.deepsjeng_r | 7.43   | 7.36   | 7.36   | 7.24   | 6.95   | 7.18    | 7.27    | 7.22    | 7.17    | 7.29               |
| 541.leela_r     | 7.20   | 7.06   | 7.13   | 7.16   | 7.00   | 7.45    | 7.39    | 7.36    | 7.41    | 7.19               |
| 548.exchange2_r | 32.5   | 29.9   | 28.8   | 28.2   | 16.2   | 14.4    | 14.4    | 12.9    | 10.9    | 14.4               |
| 557.xz_r        | 5.69   | 5.62   | 5.59   | 5.62   | 5.55   | 5.71    | 5.69    | 5.70    | 5.69    | 5.66               |
| geomean         | 11.2   | 10.8   | 10.7   | 10.7   | 10.1   | 9.80    | 9.78    | 9.68    | 9.52    | 9.78               |

完整数据：

- [GCC 11.3.0](./data/others/SPEC_INT_2017_Intel_i9-14900K_O3_GCC_11.txt)
- [GCC 12.2.0](./data/others/SPEC_INT_2017_Intel_i9-14900K_O3_GCC_12.txt)
- [GCC 13.3.0](./data/others/SPEC_INT_2017_Intel_i9-14900K_O3_GCC_13.txt)
- [GCC 14.2.0](./data/others/SPEC_INT_2017_Intel_i9-14900K_O3_GCC_14.txt)
- [GCC 15.1.0](./data/others/SPEC_INT_2017_Intel_i9-14900K_O3_GCC_15.txt)
- [LLVM 19.1.4](./data/others/SPEC_INT_2017_Intel_i9-14900K_O3_LLVM_19.txt)
- [LLVM 18.1.8](./data/others/SPEC_INT_2017_Intel_i9-14900K_O3_LLVM_18.txt)
- [LLVM 17.0.6](./data/others/SPEC_INT_2017_Intel_i9-14900K_O3_LLVM_17.txt)
- [LLVM 20.1.5](./data/others/SPEC_INT_2017_Intel_i9-14900K_O3_LLVM_20.txt)

LLVM 20 的 548.exchange2_r 性能下降可以通过添加 `-fwrapv` 选项来解决，见 [548.exchange2_r of SPEC CPU 2017 has 30% performance regression between LLVM 18/19 and LLVM 20 on amd64](https://github.com/llvm/llvm-project/issues/139274)：

- [LLVM 20.1.5 with -fwrapv](./data/others/SPEC_INT_2017_Intel_i9-14900K_O3_LLVM_20_fwrapv.txt)

注：GCC 指 GCC + GFortran，LLVM 指 Clang + Flang-new

### LA664 不同编译器版本和编译选项下的测试结果

鉴于网上针对 LA664 的 SPEC INT 2017 Rate-1 性能测试有一些争议：

- [龙芯 3A6000、华为鲲鹏 920B 与 Intel 各代 CPU GCC14 Spec 2017 性能比对评测](https://zhuanlan.zhihu.com/p/711617301)
- [开源软件环境下龙芯 3A6000 的性能](https://zhuanlan.zhihu.com/p/7264671348)
- [是什么原因导致 guee 测试 3C6000 同编译参数同编译器下会有两份差异较大的 Spec2017 测试报告？](https://www.zhihu.com/question/9063557412)

小结一下上面的文章里的结果：

- [3A6000 GCC 15.0.0 -O3 -march=native -flto by guee: 5.11, 2.04/GHz](https://gitee.com/guee/CPU-benchmarks/blob/master/2024-11/3A6000/SPEC%20CPU%202017/intrate-1%20(OpenKylin%20%2B%20GCC15%2Bglibc2.40%20NUC%E5%8F%8C%E9%80%9A%E9%81%93%E5%86%85%E5%AD%98)/CPU2017.019.intrate.txt)
- [3A6000 GCC 14.0.1 -Ofast -march=native -flto -ljemalloc by Matterhorn: 4.73, 1.89/GHz](https://gitee.com/matter2024/CPU/blob/master/Spec2017/Ofast%2Bflto%2Bnative%2Bjemalloc/3A6000%E6%96%B0%E4%B8%96%E7%95%8C/CPU2017.008.intrate.txt)
- [3A6000 GCC 14.0.1 -Ofast -march=native -flto by Matterhorn: 4.69, 1.88/GHz](https://gitee.com/matter2024/CPU/blob/master/Spec2017/Ofast%2Bflto%2Bnative/3A6000%E6%96%B0%E4%B8%96%E7%95%8C/CPU2017.003.intrate.txt)
- [3A6000 GCC 14.0.1 -O3 -msimd=lasx by Matterhorn: 4.50, 1.80/GHz](https://gitee.com/matter2024/CPU/blob/master/Spec2017/O3/3A6000%E6%96%B0%E4%B8%96%E7%95%8C/CPU2017.004.intrate.txt)
- [3A6000 GCC 14.0.1 -O3 by Matterhorn: 4.17, 1.67/GHz](https://gitee.com/matter2024/CPU/blob/master/Spec2017/O3/3A6000%E6%96%B0%E4%B8%96%E7%95%8C/CPU2017.010.intrate.txt)

可见主要的分歧是在 GCC 版本和编译选项上。

下面贴出本人测试的结果：

- [3C6000 GCC 15.1.0 -O3 -msimd=lasx -flto -ljemalloc: 4.92, 2.24/GHz](./data/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3-msimd=lasx-flto-ljemalloc.txt)
- [3C6000 GCC 15.1.0 -O3 -flto -ljemalloc: 4.90, 2.23/GHz](./data/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3-flto-ljemalloc.txt)
- [3A6000 GCC 14.2.0 -O3 -flto -ljemalloc: 4.86, 1.94/GHz](./data/int2017_rate1/Loongson_3A6000_O3-flto-ljemalloc_001.txt)
- [3C6000 GCC 15.1.0 -O3 -march=native -flto -ljemalloc: 4.82, 2.20/GHz](./data/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3-march=native-flto-ljemalloc.txt)
- [3C6000 GCC 15.1.0 -O3 -flto: 4.67, 2.12/GHz](./data/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3-flto.txt)
- [3A6000 GCC 14.2.0 -O3 -flto: 4.56, 1.82/GHz](./data/int2017_rate1/Loongson_3A6000_O3-flto_001.txt)
- [3C6000 GCC 14.2.0 -O3 -flto -ljemalloc: 4.54, 2.06/GHz](./data/int2017_rate1/Loongson_3C6000_O3-flto-ljemalloc_001.txt)
- [3C6000 GCC 15.1.0 -O3: 4.49, 2.04/GHz](./data/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3.txt)
- [3C6000 GCC 15.1.0 -O3 -march=la464: 4.49, 2.04/GHz](./data/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3-march=la464.txt)
- [3C6000 GCC 15.1.0 -O3 -march=la664: 4.40, 2.04/GHz](./data/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3-march=la664.txt)
- [3C6000 GCC 14.2.0 -O3 -flto: 4.39, 2.00/GHz](./data/int2017_rate1/Loongson_3C6000_O3-flto_001.txt)
- [3A6000 GCC 14.2.0 -O3: 4.35, 1.74/GHz](./data/int2017_rate1/Loongson_3A6000_O3_001.txt)
- [3C6000 GCC 14.2.0 -O3: 4.19, 1.90/GHz](./data/int2017_rate1/Loongson_3C6000_O3_001.txt)

注：3A6000 频率是 2.5 GHz，3C6000 频率是 2.2 GHz。

结论：性能受编译器版本和编译选项影响很大，如果对不上，那么性能的差距可能会影响和其他处理器比较的结论。在上面的例子里，这些编译器版本和编译选项带来的优化：

1. `-flto`：约 5% 提升，`4.39/4.19=1.05`, `4.56/4.35=1.05`
2. `-march=native`（仅 GCC 14）或 `-msimd=lasx`: 约 8% 提升，`4.50/4.17=1.08`
3. GCC 15.1.0 vs GCC 14.2.0: 约 7% 提升，`4.49/4.19=1.07`
3. `-ljemalloc`: 约 3-7% 提升，`4.90/4.63=1.06`, `4.86/4.56=1.07`, `4.54/4.39=1.03`

## SPEC FP 2017 Rate-1

下面贴出自己测的数据（SPECfp2017，Estimated，rate，base，1 copy），不保证满足 SPEC 的要求，仅供参考。总运行时间基本和分数成反比，乘积按 1e5 估算。

### 数据总览

![](./data/fp2017_rate1_score.svg)

![](./data/fp2017_rate1_table.svg)

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

??? note "指令数"

    ![](./data/fp2017_rate1_inst.svg)

### 原始数据

桌面平台（`-march=native`）：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3 -march=native`）: [11.4](./data/fp2017_rate1/AMD_Ryzen_7_5700X_O3-march=native_001.txt)
- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3 -march=native`）: [17.6](./data/fp2017_rate1/AMD_Ryzen_9_9950X_O3-march=native_001.txt)
- Apple M1 @ 3.1 GHz Firestorm（`-O3 -march=native`）: [11.6](./data/fp2017_rate1/Apple_M1_O3-march=native_001.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3 -march=native`）: [3.89](./data/fp2017_rate1/Apple_M1_E-Core_O3-march=native_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz (AVX-512 @ 4.0 GHz) Cascade Lake（`-O3 -march=native`）: [7.24](./data/fp2017_rate1/Intel_Core_i9-10980XE_O3-march=native_001.txt)
- Intel Core i9-14900K @ 6.0 GHz Raptor Cove（`-O3 -march=native`）: [16.6](./data/fp2017_rate1/Intel_Core_i9-14900K_O3-march=native_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3 -march=native`）: [11.0](./data/fp2017_rate1/Intel_Xeon_w9-3595X_O3-march=native_001.txt)
- Loongson 3A6000 @ 2.5 GHz LA664（`-O3 -march=native`）: [5.73](./data/fp2017_rate1/Loongson_3A6000_O3-march=native_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3 -march=native`）: [14.4](./data/fp2017_rate1/Qualcomm_X1E80100_O3-march=native_001.txt)

桌面平台（LTO）：

- Huawei Kirin X90 E-Core @ 2.0 GHz（`-O3 -flto`）: [6.52](./data/fp2017_rate1/Huawei_Kirin_X90_E-Core_O3-flto_001.txt)
- Huawei Kirin X90 P-Core @ 2.3 GHz（`-O3 -flto`）: [7.42](./data/fp2017_rate1/Huawei_Kirin_X90_P-Core_O3-flto_001.txt)


桌面平台：

- AMD Ryzen 5 7500F Zen 4（`-O3`）: [11.6](./data/fp2017_rate1/AMD_Ryzen_5_7500F_O3_001.txt)
- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3`）: [9.91](./data/fp2017_rate1/AMD_Ryzen_7_5700X_O3_001.txt)
- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3`）: [16.3](./data/fp2017_rate1/AMD_Ryzen_9_9950X_O3_001.txt) [16.6](./data/fp2017_rate1/AMD_Ryzen_9_9950X_O3_002.txt)
- Apple M1 @ 3.1 GHz Firestorm（`-O3`）: [11.6](./data/fp2017_rate1/Apple_M1_O3_001.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3`）: [3.89](./data/fp2017_rate1/Apple_M1_E-Core_O3_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3`）: [6.91](./data/fp2017_rate1/Intel_Core_i9-10980XE_O3_001.txt)
- Intel Core i9-12900KS @ 5.5 GHz Golden Cove（`-O3`）: [14.3](./data/fp2017_rate1/Intel_Core_i9-12900KS_O3_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3`）: [6.90](./data/fp2017_rate1/Intel_Core_i9-12900KS_E-Core_O3_001.txt)
- Intel Core i9-14900K @ 6.0 GHz Raptor Cove（`-O3`）: [16.1](./data/fp2017_rate1/Intel_Core_i9-14900K_O3_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3`）: [7.31](./data/fp2017_rate1/Intel_Core_i9-14900K_E-Core_O3_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3`）: [10.6](./data/fp2017_rate1/Intel_Xeon_w9-3595X_O3_001.txt)
- Loongson 3A6000 @ 2.5 GHz LA664（`-O3`）: [5.56](./data/fp2017_rate1/Loongson_3A6000_O3_001.txt)
- Qualcomm 8cx Gen3 E-Core @ 2.4 GHz Cortex-A78C（`-O3`）: [6.08](./data/fp2017_rate1/Qualcomm_8cx_Gen3_E-Core_O3_001.txt)
- Qualcomm 8cx Gen3 @ 3.0 GHz Cortex-X1C（`-O3`）: [8.07](./data/fp2017_rate1/Qualcomm_8cx_Gen3_O3_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3`）: [14.4](./data/fp2017_rate1/Qualcomm_X1E80100_O3_001.txt)

服务器平台（`-march=native`）：

- AMD EPYC 9754 @ 3.1 GHz Zen 4c（`-O3 -march=native`）: [8.42](./data/fp2017_rate1/AMD_EPYC_9754_O3-march=native_001.txt)
- AMD EPYC 9755 @ 4.1 GHz Zen 5（`-O3 -march=native`）: [14.4](./data/fp2017_rate1/AMD_EPYC_9755_O3-march=native_001.txt)
- AMD EPYC 9K65 @ 3.7 GHz Zen 5c（`-O3 -march=native`）: [12.7](./data/fp2017_rate1/AMD_EPYC_9K65_O3-march=native_001.txt)
- AMD EPYC 9K85 @ 4.1 GHz Zen 5（`-O3 -march=native`）: [14.2](./data/fp2017_rate1/AMD_EPYC_9K85_O3-march=native_001.txt)
- AMD EPYC 9R14 @ 3.7 GHz Zen 4（`-O3 -march=native`）: [10.1](./data/fp2017_rate1/AMD_EPYC_9R14_O3-march=native_001.txt)
- AMD EPYC 9T24 @ 3.7 GHz Zen 4（`-O3 -march=native`）: [10.1](./data/fp2017_rate1/AMD_EPYC_9T24_O3-march=native_001.txt)
- AWS Graviton 3 @ 2.6 GHz Neoverse V1（`-O3 -march=native`）: [7.73](./data/fp2017_rate1/AWS_Graviton_3_O3-march=native_001.txt)
- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3 -march=native`）: [9.29](./data/fp2017_rate1/AWS_Graviton_4_O3-march=native_001.txt) [9.35](./data/fp2017_rate1/AWS_Graviton_4_O3-march=native_002.txt)
- Intel Xeon 6981E Crestmont（`-O3 -march=native`）: [4.77](./data/fp2017_rate1/Intel_Xeon_6981E_O3-march=native_001.txt)
- Intel Xeon 6982P-C @ 3.6 GHz Redwood Cove（`-O3 -march=native`）: [9.50](./data/fp2017_rate1/Intel_Xeon_6982P-C_O3-march=native_001.txt)
- Intel Xeon D-2146NT @ 2.9 GHz Skylake（`-O3 -march=native`）: [5.48](./data/fp2017_rate1/Intel_Xeon_D-2146NT_O3-march=native_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Sunny Cove（`-O3 -march=native`）: [7.60](./data/fp2017_rate1/Intel_Xeon_Platinum_8358P_O3-march=native_001.txt)
- Intel Xeon Platinum 8581C @ 3.4 GHz Raptor Cove（`-O3 -march=native`）: [8.60](./data/fp2017_rate1/Intel_Xeon_Platinum_8581C_O3-march=native_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3 -march=native`）: [3.17](./data/fp2017_rate1/Kunpeng_920_O3-march=native_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3 -march=native`）: [8.01](./data/fp2017_rate1/Kunpeng_920_HuaweiCloud_kc2_O3-march=native_001.txt)
- Loongson 3C5000 @ 2.2 GHz LA464（`-O3 -march=native`）: [3.09](./data/fp2017_rate1/Loongson_3C5000_O3-march=native_001.txt)
- Loongson 3C6000 @ 2.2 GHz LA664（`-O3 -march=native`）: [4.93](./data/fp2017_rate1/Loongson_3C6000_O3-march=native_001.txt)

服务器平台：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3`）: [4.05](./data/fp2017_rate1/AMD_EPYC_7551_O3_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3`）: [7.12](./data/fp2017_rate1/AMD_EPYC_7742_O3_001.txt)
- AMD EPYC 7H12 @ 3.3 GHz Zen 2（`-O3`）: [6.61](./data/fp2017_rate1/AMD_EPYC_7H12_O3_001.txt)
- AMD EPYC 7K83 Zen 3（`-O3`）: [7.63](./data/fp2017_rate1/AMD_EPYC_7K83_O3_001.txt)
- AMD EPYC 9754 @ 3.1 GHz Zen 4c（`-O3`）: [7.64](./data/fp2017_rate1/AMD_EPYC_9754_O3_001.txt)
- AMD EPYC 9755 @ 4.1 GHz Zen 5（`-O3`）: [13.2](./data/fp2017_rate1/AMD_EPYC_9755_O3_001.txt)
- AMD EPYC 9K65 @ 3.7 GHz Zen 5c（`-O3`）: [11.7](./data/fp2017_rate1/AMD_EPYC_9K65_O3_001.txt)
- AMD EPYC 9K85 @ 4.1 GHz Zen 5（`-O3`）: [13.0](./data/fp2017_rate1/AMD_EPYC_9K85_O3_001.txt)
- AMD EPYC 9R14 @ 3.7 GHz Zen 4（`-O3`）: [9.26](./data/fp2017_rate1/AMD_EPYC_9R14_O3_001.txt)
- AMD EPYC 9T24 @ 3.7 GHz Zen 4（`-O3`）: [9.23](./data/fp2017_rate1/AMD_EPYC_9T24_O3_001.txt)
- AWS Graviton 3 @ 2.6 GHz Neoverse V1（`-O3`）: [7.80](./data/fp2017_rate1/AWS_Graviton_3_O3_001.txt)
- AWS Graviton 3E @ 2.6 GHz Neoverse V1（`-O3`）: [8.10](./data/fp2017_rate1/AWS_Graviton_3E_O3_001.txt)
- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3`）: [9.36](./data/fp2017_rate1/AWS_Graviton_4_O3_001.txt) [9.39](./data/fp2017_rate1/AWS_Graviton_4_O3_002.txt)
- Ampere Altra @ 3.0 GHz Neoverse N1（`-O3`）: [5.26](./data/fp2017_rate1/Ampere_Altra_O3_001.txt)
- Hygon C86 7390（`-O3`）: [3.95](./data/fp2017_rate1/Hygon_C86_7390_O3_001.txt)
- IBM POWER8NVL @ 4.0 GHz POWER8（`-O3`）: [4.10](./data/fp2017_rate1/IBM_POWER8NVL_O3_001.txt)
- Intel Xeon 6982P-C @ 3.6 GHz Redwood Cove（`-O3`）: [9.50](./data/fp2017_rate1/Intel_Xeon_6982P-C_O3_001.txt)
- Intel Xeon D-2146NT @ 2.9 GHz Skylake（`-O3`）: [5.00](./data/fp2017_rate1/Intel_Xeon_D-2146NT_O3_001.txt)
- Intel Xeon E5-2603 v4 @ 1.7 GHz Broadwell（`-O3`）: [3.14](./data/fp2017_rate1/Intel_Xeon_E5-2603_v4_O3_001.txt)
- Intel Xeon E5-2680 v3 @ 3.3 GHz Haswell（`-O3`）: [5.15](./data/fp2017_rate1/Intel_Xeon_E5-2680_v3_O3_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3`）: [5.44](./data/fp2017_rate1/Intel_Xeon_E5-2680_v4_O3_001.txt)
- Intel Xeon E5-4610 v2 @ 2.7 GHz Ivy Bridge EP（`-O3`）: [3.74](./data/fp2017_rate1/Intel_Xeon_E5-4610_v2_O3_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Sunny Cove（`-O3`）: [7.12](./data/fp2017_rate1/Intel_Xeon_Platinum_8358P_O3_001.txt)
- Intel Xeon Platinum 8576C Raptor Cove（`-O3`）: [8.14](./data/fp2017_rate1/Intel_Xeon_Platinum_8576C_O3_001.txt)
- Intel Xeon Platinum 8581C @ 3.4 GHz Raptor Cove（`-O3`）: [8.42](./data/fp2017_rate1/Intel_Xeon_Platinum_8581C_O3_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3`）: [3.13](./data/fp2017_rate1/Kunpeng_920_O3_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3`）: [8.17](./data/fp2017_rate1/Kunpeng_920_HuaweiCloud_kc2_O3_001.txt)
- Loongson 3C5000 @ 2.2 GHz LA464（`-O3`）: [3.00](./data/fp2017_rate1/Loongson_3C5000_O3_001.txt)
- Loongson 3C6000 @ 2.2 GHz LA664（`-O3`）: [4.75](./data/fp2017_rate1/Loongson_3C6000_O3_001.txt) [4.77](./data/fp2017_rate1/Loongson_3C6000_O3_002.txt) [4.75](./data/fp2017_rate1/Loongson_3C6000_O3_003.txt)
- T-Head Yitian 710 @ 3.0 GHz Neoverse N2（`-O3`）: [7.63](./data/fp2017_rate1/T-Head_Yitian_710_O3_001.txt)

手机平台（LTO）：

- Huawei Kirin 9010 E-Core Full @ 2.2 GHz（`-O3 -flto`）: [4.72](./data/fp2017_rate1/Huawei_Kirin_9010_E-Core_Full_O3-flto_001.txt)
- Huawei Kirin 9010 P-Core Best @ 2.3 GHz（`-O3 -flto`）: [6.22](./data/fp2017_rate1/Huawei_Kirin_9010_P-Core_Best_O3-flto_001.txt)
- Huawei Kirin 9010 P-Core Full @ 2.3 GHz（`-O3 -flto`）: [5.86](./data/fp2017_rate1/Huawei_Kirin_9010_P-Core_Full_O3-flto_001.txt)

注：

1. SPEC FP 2017 Rate-1 结果在 AMD64 平台下受 `-march=native` 影响很明显，特别是有 AVX-512 的平台，因为不开 `-march=native` 时，默认情况下 SIMD 最多用到 SSE。ARM64 平台下 `-march=native` 没有什么影响，甚至有一定的劣化。
2. 部分内核版本（大约 6.7-6.11，在 6.12/6.11.7 中修复）会显著影响 503.bwaves_r 和 507.cactuBSSN_r 项目的性能，详见 [Intel Spots A 3888.9% Performance Improvement In The Linux Kernel From One Line Of Code](https://www.phoronix.com/news/Intel-Linux-3888.9-Performance)、[mm, mmap: limit THP alignment of anonymous mappings to PMD-aligned sizes](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=d4148aeab412432bf928f311eca8a2ba52bb05df) 和 [kernel 6.10 THP causes abysmal performance drop](https://bugzilla.suse.com/show_bug.cgi?id=1229012)。
3. Qualcomm 8cx Gen3 在跑测试的时候，会因为过热降频，导致达不到最佳性能，三轮测试一轮比一轮慢。
4. 在华为云 kc2 实例上用 Debian Bookworm 带 `-march=native` 编译代码会报错，是 binutils 2.40 版本的问题；解决办法是手动安装一个 binutils 2.42：

      ```shell
      # Fix error building 511.povray_r:
      # /usr/bin/gcc -std=c99 -c -o image_validator/ImageValidator.o -DSPEC -DNDEBUG -Ifrontend -Ibase -I. -Ispec_qsort -DSPEC_AUTO_SUPPRESS_OPENMP  -O3 -march=native            -Wno-error=implicit-int   -DSPEC_LP64  image_validator/ImageValidator.c
      # /tmp/cc0E80QY.s: Assembler messages:
      # /tmp/cc0E80QY.s:2340: Error: selected processor does not support `bcax v22.16b,v22.16b,v11.16b,v22.16b'
      # /tmp/cc0E80QY.s:2425: Error: selected processor does not support `bcax v8.16b,v8.16b,v16.16b,v8.16b'
      # /tmp/cc0E80QY.s:2502: Error: selected processor does not support `bcax v3.16b,v3.16b,v5.16b,v3.16b'
      apt update
      apt install -y texinfo
      wget https://mirrors.tuna.tsinghua.edu.cn/gnu/binutils/binutils-2.42.tar.xz
      tar xvf binutils-2.42.tar.xz
      cd binutils-2.42
      mkdir build
      cd build/
      ../configure
      make all -j4
      make install -j4
      ```
5. Kirin 9010 因为散热问题，单独跑测试，和顺着跑一遍测试，结果差距比较大。因此提供了两组数据：Best（每一项单独跑，取最短时间，散热影响比较小）和 Full（按照顺序跑一次，散热影响比较大）。

### 网上的数据

[高通 X Elite Oryon 微架构评测：走走停停 by JamesAslan](https://zhuanlan.zhihu.com/p/704707254):

- Intel Core 13700K Raptor Cove: 14.56
- Qualcomm X1E80100 Oryon: 14.20
- AMD Ryzen 7700X Zen 4: 13.97
- Intel Core 12700K Golden Cove: 13.70
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
- Loongson 3A6000 LA664: 5.49
- Mediatek Genio 1200 Cortex A78: 5.09
- Intel Core Ultra 7 115H Low Power Crestmont: 4.32
- AMD FX-8150: 3.63
- Loongson 3A5000 LA464: 3.38
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
- Intel Core i9-14900K Raptor Cove: 16.90
- AMD Ryzen 9 7950X Zen 4: 14.26

[Snapdragon X Elite Qualcomm Oryon CPU Design and Architecture Hot Chips 2024](https://www.servethehome.com/snapdragon-x-elite-qualcomm-oryon-cpu-design-and-architecture-hot-chips-2024-arm/)

- Qualcomm X Elite Oryon on Linux: 17.77
- Qualcomm X Elite Oryon on Windows: 16.66

[ARM Cortex X1 微架构评测（上）：向山进发](https://zhuanlan.zhihu.com/p/619033328)

- Zen 3 @ 4.95 GHz: 11.9
- Firestorm @ 3.0 GHz: 11.2
- Cortex X1 @ 3.0 GHz: 8.9
- Cortex A78 @ 2.4 GHz: 5.9

[极客湾•麒麟 9010，测评汇总：IPC 性能，巨幅提升！CPU 能效全频段领先，麒麟 9000S！](https://www.bilibili.com/opus/925502754370093090)

- Huawei Kirin 9010: 7.77
- HUawei Kirin 9000s: 7.12

### 多版本 GCC 和 LLVM 性能比较

在 Intel i9-14900K @ 5.7 GHz 上用 -O3 测试几种编译器组合的性能：

| Benchmark       | GCC 12 | LLVM 20 | LLVM 19 | LLVM 18 |
|-----------------|--------|---------|---------|---------|
| 503.bwaves_r    | 75.1   | 70.9    | 73.1    | 73.2    |
| 507.cactuBSSN_r | 14.4   | 13.3    | 13.6    | 13.6    |
| 508.namd_r      | 9.24   | 10.5    | 10.6    | 10.5    |
| 510.parest_r    | 14.6   | 14.6    | 14.6    | 14.4    |
| 511.povray_r    | 14.6   | 13.7    | 13.7    | 13.7    |
| 519.lbm_r       | 12.1   | 11.2    | 11.2    | 11.2    |
| 521.wrf_r       | 13.5   | 14.0    | 13.3    | 13.3    |
| 526.blender_r   | 12.0   | 11.8    | 11.9    | 11.9    |
| 527.cam4_r      | 15.4   | 13.2    | 12.9    | 12.9    |
| 538.imagick_r   | 10.2   | 11.8    | 11.9    | 12.3    |
| 544.nab_r       | 12.6   | 8.47    | 8.22    | 8.22    |
| 549.fotonik3d_r | 24.5   | 24.0    | 21.0    | 21.2    |
| 554.roms_r      | 14.1   | 14.3    | 13.7    | 13.7    |
| geomean         | 15.4   | 14.8    | 14.6    | 14.6    |

完整数据：

- [GCC 12.2.0](./data/others/SPEC_FP_2017_Intel_i9-14900K_O3_GCC_12.txt)
- [LLVM 18.1.8](./data/others/SPEC_FP_2017_Intel_i9-14900K_O3_LLVM_18.txt)
- [LLVM 19.1.4](./data/others/SPEC_FP_2017_Intel_i9-14900K_O3_LLVM_19.txt)
- [LLVM 20.1.5](./data/others/SPEC_FP_2017_Intel_i9-14900K_O3_LLVM_20.txt)

注：GCC 指 GCC + GFortran，LLVM 指 Clang + Flang-new

## SPEC INT 2006 Speed

因为 GCC 没有自动并行化，所以都是单核运行。运行时间基本和分数成反比，乘积按 400000 估算。

下面贴出自己测的数据（SPECint2006，Estimated，speed，base），不保证满足 SPEC 的要求，仅供参考。

- Intel Core i9-14900K Raptor Cove（`-O3`）: [91.9](./data/int2006_speed/Intel_Core_i9-14900K_O3_001.txt)
- Intel Core i9-14900K Raptor Cove（`-O2`）: [87.2](./data/int2006_speed/Intel_Core_i9-14900K_O2_001.txt)
- Intel Core i9-13900K Raptor Cove（`-Ofast -fomit-frame-pointer -march=native -mtune=native`）: 85.3 86.8
- Intel Core i9-13900K Raptor Cove（`-O2`）: 79.6
- Intel Core i9-12900KS Golden Cove（`-O2`）: 74.4
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

不打算跑

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

- Intel Core i9-14900K Raptor Cove（`-O3`）: [12.1](./data/int2017_speed/Intel_Core_i9-14900K_O3_001.txt)
- Intel Core i9-12900KS Golden Cove（`-O3`）: [10.5](./data/int2017_speed/Intel_Core_i9-12900KS_O3_001.txt) [10.9](./data/int2017_speed/Intel_Core_i9-12900KS_O3_002.txt)
- Qualcomm X1E80100 X Elite（`-O3`）: [7.99](./data/int2017_speed/Qualcomm_X1E80100_O3_001.txt)
- Intel Core i9-10980XE Cascade Lake（`-O3`）: [7.18](./data/int2017_speed/Intel_Core_i9-10980XE_O3_001.txt)
- AMD EPYC 7742 Zen 2（`-O3`）: [5.55](./data/int2017_speed/AMD_EPYC_7742_O3_001.txt)
- Kunpeng 920 TaiShan V110（`-O3`）: [3.65](./data/int2017_speed/Kunpeng_920_O3_001.txt) [3.62](./data/int2017_speed/Kunpeng_920_O3_002.txt)

注：SPEC INT 2017 单线程 OpenMP 下 speed 测试按理说约等于 rate-1，前者虽然启用了 OpenMP，但仅允许单线程。不过实测下来还是不太一样。

## SPEC FP 2017 Speed

下面贴出自己测的数据（SPECfp2017，Estimated，speed，base，单线程），不保证满足 SPEC 的要求，仅供参考。

运行时间基本和分数成反比，乘积按 5e5 估算。

- Intel Core i9-14900K Raptor Cove（`-O3`）: [12.8](./data/fp2017_speed/Intel_Core_i9-14900K_O3_001.txt)
- Intel Core i9-12900KS Golden Cove（`-O3`）: [13.1](./data/fp2017_speed/Intel_Core_i9-12900KS_O3_001.txt)
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
makeflags = --jobs=%{nproc}

# compilers
default:
   preENV_LD_LIBRARY_PATH  = /usr/lib64:/usr/lib:/lib64
   SPECLANG                = /usr/bin/
%if %{clang} eq "1"
   CC                      = $(SPECLANG)clang -std=c99
   CXX                     = $(SPECLANG)clang++
%else
   CC                      = $(SPECLANG)gcc -std=c99
   CXX                     = $(SPECLANG)g++
%endif
%if %{flang} eq "1"
   FC                      = $(SPECLANG)flang-new
%else
   FC                      = $(SPECLANG)gfortran
%endif
# allow to override compilers
%ifdef %{override-cc}
   CC                      = %{override-cc} -std=c99
%endif
%ifdef %{override-cxx}
   CXX                     = %{override-cxx}
%endif
%ifdef %{override-fc}
   FC                      = %{override-fc}
%endif
   # How to say "Show me your version, please"
   CC_VERSION_OPTION       = -v
   CXX_VERSION_OPTION      = -v
   FC_VERSION_OPTION       = -v

# perf: use runcpu --define perf=1 --noreportable to enable
%if %{perf} eq "1"
# override branch-misses counter if necessary
# e.g. on ARMv8 PMUv3, use r22 for branch misses
# e.g. on Apple M1, use rcb for branch misses
%ifndef %{perf-branchmisses}
%define perf-branchmisses branch-misses
%endif
# override branches counter if necessary
# e.g. on Apple M1, use r8d for branches
%ifndef %{perf-branches}
%define perf-branches branches
%endif
default:
   command_add_redirect = 1
# bind to core if requested
%ifdef %{bindcore}
   monitor_wrapper = mkdir -p $[top]/result/perf.$lognum; echo "$command" > $[top]/result/perf.$lognum/$benchmark.cmd.$iter.\$\$; taskset -c %{bindcore} perf stat -x \\; -e instructions,cycles,%{perf-branches},%{perf-branchmisses},task-clock -o $[top]/result/perf.$lognum/$benchmark.perf.$iter.\$\$ $command
%else
   monitor_wrapper = mkdir -p $[top]/result/perf.$lognum; echo "$command" > $[top]/result/perf.$lognum/$benchmark.cmd.$iter.\$\$; perf stat -x \\; -e instructions,cycles,%{perf-branches},%{perf-branchmisses},task-clock -o $[top]/result/perf.$lognum/$benchmark.perf.$iter.\$\$ $command
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
%if %{clang} eq "1"
# from config/Example-aocc-linux-x86.cfg
   CXXPORTABILITY = -D__BOOL_DEFINED
%endif

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
%if %{flang} ne "1"
   # -fallow-argument-mismatch required for https://www.spec.org/cpu2017/Docs/benchmarks/521.wrf_r.html
   FOPTIMIZE      = -fallow-argument-mismatch
%endif

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

%if %{clang} eq "1"
# https://github.com/llvm/llvm-project/issues/96859
# 523.xalancbmk_r
   EXTRA_CXXOPTIMIZE = -fdelayed-template-parsing
%endif

%if %{gcc15} eq "1"
# https://gcc.gnu.org/bugzilla/show_bug.cgi?id=116064
# 523.xalamcbmk_r
   EXTRA_CXXOPTIMIZE += -Wno-error=template-body
%endif

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

| uArch             | DP FLOP/cycle | SP FLOP/cycle | ISA       |
|-------------------|---------------|---------------|-----------|
| AMD Zen 5         | 32            | 64            | AVX512F   |
| Intel Skylake     | 32            | 64            | AVX512F   |
| Intel Sunny Cove  | 32            | 64            | AVX512F   |
| AMD Zen 2         | 16            | 32            | FMA       |
| AMD Zen 3         | 16            | 32            | AVX512F   |
| AMD Zen 4         | 16            | 32            | AVX512F   |
| ARM Neoverse V1   | 16            | 32            | SVE(256b) |
| ARM Neoverse V2   | 16            | 32            | SVE(128b) |
| Apple Avalanche   | 16            | 32            | ASIMD     |
| Apple Firestorm   | 16            | 32            | ASIMD     |
| Intel Broadwell   | 16            | 32            | FMA       |
| Intel Golden Cove | 16            | 32            | FMA       |
| Intel Haswell     | 16            | 32            | FMA       |
| Loongson LA464    | 16            | 32            | LASX      |
| Loongson LA664    | 16            | 32            | LASX      |
| Qualcomm Oryon    | 16            | 32            | ASIMD     |
| AMD Zen 1         | 8             | 16            | FMA       |
| ARM Cortex A78    | 8             | 16            | ASIMD     |
| ARM Cortex X1     | 8             | 16            | ASIMD     |
| ARM Icestorm      | 8             | 16            | ASIMD     |
| ARM Neoverse N1   | 8             | 16            | ASIMD     |
| ARM Neoverse N2   | 8             | 16            | SVE(128b) |
| Intel Gracemont   | 8             | 16            | FMA       |
| Hisilicon TSV110  | 4             | 16            | ASIMD     |

## 固定频率方法

可以尝试用 cpupower frequency-set 来固定频率，但是一些平台不支持，还可能有 Linux 内无法关闭的 Boost。设置频率后，用 `cpupower frequency-info` 验证：`current CPU frequency: 4.29 GHz (asserted by call to kernel)` 是否和预期频率一致并且不变。

对于 AMD CPU，在 Linux 下为了固定 CPU 的频率，需要通过 MSR 进行设置：[jiegec/ZenStates-Linux](https://github.com/jiegec/ZenStates-Linux)：

1. 关闭 Core performance boost
2. 读取当前的 pstate 设置
3. 修改当前 pstate 的 FID，也就修改了频率

## 测试环境

参与测试的机型如下，除了括号中表明为云服务虚拟机的，其他都是物理机：

- AMD EPYC 7551: Zen 1, Naples
- AMD EPYC 7742: Zen 2, Rome
- AMD EPYC 7H12: Zen 2, Rome
- AMD EPYC 7K83(TencentCloud sa3.medium4, 2C 4G): Zen 3, Milan, w/o PMU
- AMD EPYC 9754(TencentCloud sa5.large8, 4C 8G): Zen 4c, Bergamo
- AMD EPYC 9755: Zen 5, Turin
- AMD EPYC 9K65(TencentCloud sa9.large8, 4C 8G): Zen 5c, Turin Dense
- AMD EPYC 9K85(TencentCloud sa9e.large8, 4C 8G): Zen 5, Turin
- AMD EPYC 9R14(AWS c7a.xlarge, 4C 8G): Zen 4, Genoa
- AMD EPYC 9T24(Aliyun g8a.xlarge, 4C 16G): Zen 4, Genoa
- AMD Ryzen 5 7500F: Zen 4, Raphael
- AMD Ryzen 7 5700X: Zen 3, Vermeer
- AMD Ryzen 9 9950X: Zen 5, Granite Ridge
- AWS Gravition 3(AWS c7g.large, 2C 4G): Neoverse V1
- AWS Gravition 3E(AWS c7gn.medium, 1C 2G): Neoverse V1
- AWS Gravition 4(AWS c8g.large, 2C 4G): Neoverse V2
- Ampere Altra(Aliyun c6r.large, 2C 4G): Neoverse N1
- Apple M1: Firestorm + Icestorm
- Huawei Kirin 9010
- Hygon C86 7390(Aliyun g7h.large, 2C 8G): w/o PMU
- IBM POWER8NVL
- Intel Core i9-10980XE: Cascade Lake
- Intel Core i9-12900KS: Golden Cove + Gracemont, Alder Lake
- Intel Core i9-14900K: Raptor Cove + Gracemont, Raptor Lake
- Intel Xeon 6981E(TencentCloud s9.large8, 4C 8G): Crestmont, Sierra Forest, w/o PMU
- Intel Xeon 6982P-C(Aliyun g9i.xlarge, 4C 16G): Redwood Cove, Granite Rapids
- Intel Xeon D-2146NT: Skylake
- Intel Xeon E5-2603 v4: Broadwell
- Intel Xeon E5-2680 v3: Haswell
- Intel Xeon E5-2680 v4: Broadwell
- Intel Xeon E5-4610 v2: Ivy Bridge EP
- Intel Xeon Platinum 8358P: Sunny Cove, Ice Lake
- Intel Xeon Platinum 8576C(TencentCloud s8.medium8, 2C 8G): Raptor Cove, Emerald Rapids, w/o PMU
- Intel Xeon Platinum 8581C(GCP c4-standard-2, 2C 7G): Raptor Cove, Emerald Rapids
- Intel Xeon w9-3595X: Golden Cove, Sapphire Rapids
- Kunpeng 920 HuaweiCloud kc2(HuaweiCloud kc2.xlarge.2, 4C 8G)
- Kunpeng 920: TaiShan V110
- Loongson 3A6000: LA664
- Loongson 3C5000: LA464
- Loongson 3C6000: LA664
- Qualcomm 8cx Gen3: Cortex-X1C + Cortex-A78C
- Qualcomm X1E80100: Oryon
- T-Head Yitian 710(Aliyun c8y.large, 2C 4G): Neoverse N2

由于云服务的特性，建议至少用 4C 的实例来测试，否则性能波动会比较大。

## 更新历史

- 2025.07.11:
      - 测试 Intel Xeon w9-3595X 的性能
- 2025.06.11:
      - 测试 Huawei Kirin X90 在虚拟机中的性能
- 2025.06.06:
      - 测试 Huawei Kirin X90 的性能
- 2025.05.26:
      - 测试 Loongson 3C6000 的性能
      - 在阿里云 g8a.xlarge 实例上测试 AMD EPYC 9T24 的性能
      - 在阿里云 g9i.xlarge 实例上测试 Intel Xeon 6982P-C 的性能
- 2025.05.16:
      - 在华为云 kc2.xlarge.2 实例上测试 HuaweiCloud Kunpeng 920 kc2 的性能
      - 在 AWS c7a.xlarge 实例上测试 AMD EPYC 9R14 的性能
      - 测试 Apple M1 的性能
      - 在腾讯云 sa9.large8 实例上测试 AMD EPYC 9K65 的性能
      - 在腾讯云 sa5.large8 实例上测试 AMD EPYC 9754 的性能
      - 在腾讯云 sa9e.large8 实例上测试 AMD EPYC 9K85 的性能
      - 在腾讯云 s9.large8 实例上测试 Intel Xeon 6981E 的性能
- 2025.05.15:
      - 测试 AMD EPYC 9755 的性能
      - 在华为云 kc2.large.2 实例上测试 HuaweiCloud Kunpeng 920 kc2 的性能
      - 在 AWS c7g.large 实例上测试 AWS Graviton 3 的性能
- 2025.05.07:
      - 在 AWS c8g.large 实例上测试 AWS Graviton 4 的性能
      - 测试 Loongson 3C6000 的性能
      - 测试不同编译器在 Intel Core i9-14900K 上的性能
- 2025.04.22:
      - 在 GCP c4-standard-2 实例上测试 Intel Xeon Platinum 8581C 的性能
      - 在阿里云 g7h.large 实例上测试 Hygon C86 7390 的性能
      - 在阿里云 g8a.large 实例上测试 AMD EPYC 9T24 的性能
      - 在阿里云 g9i.large 实例上测试 Intel Xeon 6982P-C 的性能
- 2025.04.19:
      - 测试 Loongson 3C6000 的性能
- 2025.04.18:
      - 测试 AMD EPYC 7551 的性能
      - 测试 AMD Ryzen 7 5700X 的性能
      - 测试 Apple M1 的性能
      - 测试 Huawei Kunpeng 920 的性能
      - 测试 Intel Core i9-10980XE 的性能
      - 测试 Loongson 3A6000 的性能
- 2025.04.11:
      - 在华为云 kc2.xlarge.4 实例上测试 HuaweiCloud Kunpeng 920 kc2 的性能
- 2025.03.26:
      - 测试 AMD Ryzen 9 9950X 的性能
      - 测试 Intel Xeon E5-4610 v2 的性能
- 2025.01.12:
      - 测试 Intel Core i9-12900KS E-Core 的性能
      - 测试 Intel Core i9-14900K E-Core 的性能
- 2024.12.31:
      - 测试 Huawei Kirin 9010 的性能
- 2024.12.16:
      - 测试 Huawei Kirin 9010 的性能
- 2024.12.05:
      - 测试 Loongson 3A6000 的性能
      - 测试 IBM POWER8NVL 的性能
- 2024.11.20:
      - 在 AWS c7gn.medium 实例上测试 AWS Graviton 3E 的性能
      - 在 AWS r8g.medium 实例上测试 AWS Graviton 4 的性能
      - 在华为云 kc1.large.2 实例上测试 HuaweiCloud Kunpeng 920 kc1 的性能
      - 在华为云 kc2.large.2 实例上测试 HuaweiCloud Kunpeng 920 kc2 的性能
      - 测试 AMD EPYC 7742 的性能
      - 测试 AMD EPYC 7H12 的性能
      - 测试 AMD Ryzen 7 5700X 的性能
      - 测试 Intel Xeon E5-2603 v4 的性能
      - 测试 Loongson 3A6000 的性能
      - 测试 Loongson 3C5000 的性能
      - 测试 Loongson 3C6000 的性能
      - 测试 Qualcomm X1E80100 的性能
- 2024.11.18:
      - 测试 Intel Core i9-14900K 的性能
      - 测试 Intel Core i9-12900KS 的性能
      - 测试 Qualcomm X1E80100 的性能
      - 测试 AMD Ryzen 9 9950X 的性能
- 2024.11.07:
      - 测试 Qualcomm 8cx Gen3 的性能
- 2024.11.02:
      - 在阿里云 c6r.large 实例上测试 Ampere Altra 的性能
      - 在阿里云 c8y.large 实例上测试 T-Head Yitian 710 的性能
      - 在 AWS r8g.medium 实例上测试 AWS Graviton 4 的性能
      - 在 AWS c7g.medium 实例上测试 AWS Graviton 3 的性能
- 2024.11.01:
      - 测试 Apple M1 的性能
      - 测试 Qualcomm X1E80100 的性能
- 2024.10.30:
      - 在 AWS c7a.medium 实例上测试 AMD EPYC 9R14 的性能
      - 在腾讯云 s8.medium8 实例上测试 Intel Xeon Platinum 8576C 的性能
      - 在腾讯云 sa3.medium4 实例上测试 AMD EPYC 7K83 的性能
      - 在腾讯云 sa5.medium2 实例上测试 AMD EPYC 9754 的性能
