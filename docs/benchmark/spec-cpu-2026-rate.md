# SPEC CPU 2026 Rate

可通过[交互式图表](./viewer.html)查看和筛选本文的测试数据。

## SPEC INT 2026 Rate-1

下面贴出自己测的数据（SPECint2026，Estimated，rate，base，1 copy），不保证满足 SPEC 的要求，仅供参考。

### 原始数据

#### Debian Forky

服务器平台（LTO + Jemalloc）：

- Loongson 3C6000D @ 2.1 GHz LA664（`-O3 -flto -ljemalloc`）: [1.74](./data-forky/int2026_rate1/Loongson_3C6000D_O3-flto-ljemalloc_001.txt)

服务器平台（LTO）：

- Loongson 3C6000D @ 2.1 GHz LA664（`-O3 -flto`）: [1.66](./data-forky/int2026_rate1/Loongson_3C6000D_O3-flto_001.txt)

服务器平台：

- Loongson 3C6000D @ 2.1 GHz LA664（`-O3`）: [1.61](./data-forky/int2026_rate1/Loongson_3C6000D_O3_001.txt)

#### Debian Trixie

桌面平台（`-march=native` + LTO + Jemalloc）：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3 -march=native -flto -ljemalloc`）: [3.97](./data-trixie/int2026_rate1/AMD_Ryzen_7_5700X_O3-march=native-flto-ljemalloc_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3 -march=native -flto -ljemalloc`）: [4.31](./data-trixie/int2026_rate1/Apple_M1_P-Core_O3-march=native-flto-ljemalloc_001.txt)
- Apple M2 P-Core @ 3.5 GHz Avalanche（`-O3 -march=native -flto -ljemalloc`）: [5.20](./data-trixie/int2026_rate1/Apple_M2_P-Core_O3-march=native-flto-ljemalloc_001.txt)
- Huawei Kirin X90 VM P-Core @ 2.3 GHz（`-O3 -march=native -flto -ljemalloc`）: [2.82](./data-trixie/int2026_rate1/Huawei_Kirin_X90_VM_P-Core_O3-march=native-flto-ljemalloc_001.txt)
- Intel Core i7-13700K P-Core @ 5.4 GHz Raptor Cove（`-O3 -march=native -flto -ljemalloc`）: [5.56](./data-trixie/int2026_rate1/Intel_Core_i7-13700K_P-Core_O3-march=native-flto-ljemalloc_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3 -march=native -flto -ljemalloc`）: [5.55](./data-trixie/int2026_rate1/Intel_Core_i9-12900KS_P-Core_O3-march=native-flto-ljemalloc_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3 -march=native -flto -ljemalloc`）: [6.26](./data-trixie/int2026_rate1/Intel_Core_i9-14900K_P-Core_O3-march=native-flto-ljemalloc_001.txt)

桌面平台（LTO + Jemalloc）：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3 -flto -ljemalloc`）: [3.87](./data-trixie/int2026_rate1/AMD_Ryzen_7_5700X_O3-flto-ljemalloc_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3 -flto -ljemalloc`）: [4.31](./data-trixie/int2026_rate1/Apple_M1_P-Core_O3-flto-ljemalloc_001.txt)
- Apple M2 P-Core @ 3.5 GHz Avalanche（`-O3 -flto -ljemalloc`）: [5.10](./data-trixie/int2026_rate1/Apple_M2_P-Core_O3-flto-ljemalloc_001.txt)
- Huawei Kirin X90 VM P-Core @ 2.3 GHz（`-O3 -flto -ljemalloc`）: [2.80](./data-trixie/int2026_rate1/Huawei_Kirin_X90_VM_P-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i7-13700K P-Core @ 5.4 GHz Raptor Cove（`-O3 -flto -ljemalloc`）: [5.36](./data-trixie/int2026_rate1/Intel_Core_i7-13700K_P-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3 -flto -ljemalloc`）: [3.17](./data-trixie/int2026_rate1/Intel_Core_i9-10980XE_O3-flto-ljemalloc_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3 -flto -ljemalloc`）: [2.96](./data-trixie/int2026_rate1/Intel_Core_i9-12900KS_E-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3 -flto -ljemalloc`）: [5.37](./data-trixie/int2026_rate1/Intel_Core_i9-12900KS_P-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3 -flto -ljemalloc`）: [3.28](./data-trixie/int2026_rate1/Intel_Core_i9-14900K_E-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3 -flto -ljemalloc`）: [6.03](./data-trixie/int2026_rate1/Intel_Core_i9-14900K_P-Core_O3-flto-ljemalloc_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3 -flto -ljemalloc`）: [4.45](./data-trixie/int2026_rate1/Intel_Xeon_w9-3595X_O3-flto-ljemalloc_001.txt)

桌面平台（LTO）：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3 -flto`）: [3.66](./data-trixie/int2026_rate1/AMD_Ryzen_7_5700X_O3-flto_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3 -flto`）: [4.10](./data-trixie/int2026_rate1/Apple_M1_P-Core_O3-flto_001.txt)
- Apple M2 P-Core @ 3.5 GHz Avalanche（`-O3 -flto`）: [4.91](./data-trixie/int2026_rate1/Apple_M2_P-Core_O3-flto_001.txt)
- Huawei Kirin X90 VM P-Core @ 2.3 GHz（`-O3 -flto`）: [2.63](./data-trixie/int2026_rate1/Huawei_Kirin_X90_VM_P-Core_O3-flto_001.txt)
- Intel Core i7-13700K P-Core @ 5.4 GHz Raptor Cove（`-O3 -flto`）: [5.07](./data-trixie/int2026_rate1/Intel_Core_i7-13700K_P-Core_O3-flto_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3 -flto`）: [2.97](./data-trixie/int2026_rate1/Intel_Core_i9-10980XE_O3-flto_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3 -flto`）: [2.78](./data-trixie/int2026_rate1/Intel_Core_i9-12900KS_E-Core_O3-flto_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3 -flto`）: [5.05](./data-trixie/int2026_rate1/Intel_Core_i9-12900KS_P-Core_O3-flto_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3 -flto`）: [3.10](./data-trixie/int2026_rate1/Intel_Core_i9-14900K_E-Core_O3-flto_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3 -flto`）: [5.71](./data-trixie/int2026_rate1/Intel_Core_i9-14900K_P-Core_O3-flto_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3 -flto`）: [4.17](./data-trixie/int2026_rate1/Intel_Xeon_w9-3595X_O3-flto_001.txt)

桌面平台：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3`）: [3.53](./data-trixie/int2026_rate1/AMD_Ryzen_7_5700X_O3_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3`）: [4.02](./data-trixie/int2026_rate1/Apple_M1_P-Core_O3_001.txt)
- Apple M2 P-Core @ 3.5 GHz Avalanche（`-O3`）: [4.76](./data-trixie/int2026_rate1/Apple_M2_P-Core_O3_001.txt)
- Huawei Kirin X90 VM P-Core @ 2.3 GHz（`-O3`）: [2.54](./data-trixie/int2026_rate1/Huawei_Kirin_X90_VM_P-Core_O3_001.txt)
- Intel Core i7-13700K P-Core @ 5.4 GHz Raptor Cove（`-O3`）: [4.96](./data-trixie/int2026_rate1/Intel_Core_i7-13700K_P-Core_O3_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3`）: [2.90](./data-trixie/int2026_rate1/Intel_Core_i9-10980XE_O3_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3`）: [2.73](./data-trixie/int2026_rate1/Intel_Core_i9-12900KS_E-Core_O3_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3`）: [4.94](./data-trixie/int2026_rate1/Intel_Core_i9-12900KS_P-Core_O3_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3`）: [3.05](./data-trixie/int2026_rate1/Intel_Core_i9-14900K_E-Core_O3_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3`）: [5.59](./data-trixie/int2026_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3`）: [4.09](./data-trixie/int2026_rate1/Intel_Xeon_w9-3595X_O3_001.txt)

服务器平台（`-march=native` + LTO + Jemalloc）：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3 -march=native -flto -ljemalloc`）: [1.52](./data-trixie/int2026_rate1/AMD_EPYC_7551_O3-march=native-flto-ljemalloc_001.txt)
- AWS Graviton 5 @ 3.3 GHz Neoverse V3（`-O3 -march=native -flto -ljemalloc`）: [4.67](./data-trixie/int2026_rate1/AWS_Graviton_5_O3-march=native-flto-ljemalloc_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3 -march=native -flto -ljemalloc`）: [2.17](./data-trixie/int2026_rate1/Intel_Xeon_E5-2680_v4_O3-march=native-flto-ljemalloc_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3 -march=native -flto -ljemalloc`）: [1.59](./data-trixie/int2026_rate1/Kunpeng_920_O3-march=native-flto-ljemalloc_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3 -march=native -flto -ljemalloc`）: [2.68](./data-trixie/int2026_rate1/Kunpeng_920_HuaweiCloud_kc2_O3-march=native-flto-ljemalloc_001.txt)

服务器平台（LTO + Jemalloc）：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3 -flto -ljemalloc`）: [1.50](./data-trixie/int2026_rate1/AMD_EPYC_7551_O3-flto-ljemalloc_001.txt)
- AWS Graviton 5 @ 3.3 GHz Neoverse V3（`-O3 -flto -ljemalloc`）: [4.56](./data-trixie/int2026_rate1/AWS_Graviton_5_O3-flto-ljemalloc_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3 -flto -ljemalloc`）: [2.14](./data-trixie/int2026_rate1/Intel_Xeon_E5-2680_v4_O3-flto-ljemalloc_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3 -flto -ljemalloc`）: [1.59](./data-trixie/int2026_rate1/Kunpeng_920_O3-flto-ljemalloc_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3 -flto -ljemalloc`）: [2.65](./data-trixie/int2026_rate1/Kunpeng_920_HuaweiCloud_kc2_O3-flto-ljemalloc_001.txt)

服务器平台（LTO）：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3 -flto`）: [1.42](./data-trixie/int2026_rate1/AMD_EPYC_7551_O3-flto_001.txt)
- AWS Graviton 5 @ 3.3 GHz Neoverse V3（`-O3 -flto`）: [4.27](./data-trixie/int2026_rate1/AWS_Graviton_5_O3-flto_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3 -flto`）: [2.06](./data-trixie/int2026_rate1/Intel_Xeon_E5-2680_v4_O3-flto_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3 -flto`）: [1.51](./data-trixie/int2026_rate1/Kunpeng_920_O3-flto_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3 -flto`）: [2.51](./data-trixie/int2026_rate1/Kunpeng_920_HuaweiCloud_kc2_O3-flto_001.txt)

服务器平台：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3`）: [1.37](./data-trixie/int2026_rate1/AMD_EPYC_7551_O3_001.txt)
- AWS Graviton 5 @ 3.3 GHz Neoverse V3（`-O3`）: [4.21](./data-trixie/int2026_rate1/AWS_Graviton_5_O3_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3`）: [2.01](./data-trixie/int2026_rate1/Intel_Xeon_E5-2680_v4_O3_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3`）: [1.46](./data-trixie/int2026_rate1/Kunpeng_920_O3_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3`）: [2.42](./data-trixie/int2026_rate1/Kunpeng_920_HuaweiCloud_kc2_O3_001.txt)

#### 备注

1. 对于除了苹果以外的 ARM64 核心，内核的 branch-misses 计数器考虑了 speculative 而不只是 retired，因此数字会偏高，此时要用 r22 计数替代。

### 分支预测器比较

#### Debian Trixie

x86 平台的分支预测准确率（Average）由高到低（`-O3`）：

1. Golden Cove(Intel 12900KS P-Core)/Raptor Cove(Intel 13700K P-Core/Intel 14900K P-Core): MPKI=2.13
2. Gracemont(Intel 12900KS E-Core/Intel 14900K E-Core): MPKI=2.44
3. Cascade Lake(Intel 10980XE): MPKI=2.70
4. Broadwell(Intel E5-2680 v4): MPKI=2.94
5. Zen 1(AMD 7551): MPKI=3.73

ARM64 平台的分支预测准确率（Average）由高到低（`-O3`）：

1. Neoverse V3(AWS Graviton 5): MPKI=1.83
2. Avalanche(Apple M2 P-Core): MPKI=2.04
3. Firestorm(Apple M1 P-Core): MPKI=2.80
4. TSV110(Hisilicon Kunpeng 920): MPKI=4.07

### 网上的数据

来自 SPEC 官网：

| Machine                                                                                             | Score | Compilation Flags                                                         |
|-----------------------------------------------------------------------------------------------------|-------|---------------------------------------------------------------------------|
| [Ampere eMAG 8180](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260210-00003.html)      | 1.00  | -O3 -ffast-math -mcpu=native -flto=16 -ljemalloc                          |
| [AMD Ryzen AI 9 HX 370](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260210-00018.html) | 5.00  | -O3 -ffast-math -march=native -flto=full                                  |
| [NVIDIA GB10](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260210-00020.html)           | 5.97  | -fuse-ld=lld -O3 -ffast-math -mcpu=native -flto=thin -fomit-frame-pointer |
| [Apple M5 Pro](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260422-00243.html)          | 7.64  | -O3                                                                       |

另见 [David Huang](https://benchview.hjc.im)、[Chips and Cheese](https://chipsandcheese.com/p/evaluating-spec-cpu2026)。

### 多版本 GCC 和 LLVM 性能比较

在 Intel i9-12900KS @ 5.5 GHz 上用 -O3 测试几种编译器组合的 SPEC INT 2026 Rate-1 性能：

| Benchmark        | GCC 16   | GCC 15   | GCC 14 | LLVM 22  | LLVM 21 | LLVM 20 | LLVM 19 |
|------------------|----------|----------|--------|----------|---------|---------|---------|
| 706.stockfish_r  | 8.37     | **8.45** | 6.13   | 6.12     | 6.11    | 6.07    | 5.82    |
| 707.ntest_r      | 4.37     | 4.38     | 4.03   | **4.52** | 4.49    | 4.49    | 4.49    |
| 708.sqlite_r     | **4.53** | 4.35     | 4.52   | 4.33     | 4.26    | 4.30    | 4.18    |
| 710.omnetpp_r    | **5.47** | 5.43     | 5.34   | 4.98     | 4.99    | 4.97    | 4.96    |
| 714.cpython_r    | 6.53     | **6.62** | 6.40   | 5.74     | 5.78    | 5.72    | 5.72    |
| 721.gcc_r        | **5.53** | 5.52     | 5.43   | 5.31     | 5.30    | 5.28    | 5.28    |
| 723.llvm_r       | **4.18** | 4.14     | 4.09   | 4.05     | 4.05    | 4.03    | 4.01    |
| 727.cppcheck_r   | 3.80     | **3.93** | 3.83   | 3.78     | 3.90    | 3.89    | 3.71    |
| 729.abc_r        | 4.54     | **4.57** | 4.51   | 4.45     | 4.43    | 4.41    | 4.40    |
| 734.vpr_r        | **5.02** | 5.01     | 4.90   | 4.85     | 4.86    | 4.83    | 4.71    |
| 735.gem5_r       | **5.52** | 5.33     | 5.24   | 5.27     | 5.25    | 5.14    | 5.18    |
| 750.sealcrypto_r | 4.86     | 4.88     | 4.82   | **10.2** | 4.99    | 4.98    | 4.93    |
| 753.ns3_r        | 6.56     | **6.59** | 6.38   | 6.30     | 6.36    | 6.30    | 6.25    |
| 777.zstd_r       | **4.69** | 4.42     | 4.41   | 4.30     | 4.27    | 4.29    | 4.26    |
| geomean          | **5.17** | 5.14     | 4.94   | 5.13     | 4.88    | 4.86    | 4.80    |

完整数据：

- [GCC 14.2.0](./data-trixie/others/SPEC_INT_2026_Intel_i9-12900KS_O3_GCC_14.txt)
- [GCC 15.2.0](./data-trixie/others/SPEC_INT_2026_Intel_i9-12900KS_O3_GCC_15.txt)
- [GCC 16.1.0](./data-trixie/others/SPEC_INT_2026_Intel_i9-12900KS_O3_GCC_16.txt)
- [LLVM 19.1.7](./data-trixie/others/SPEC_INT_2026_Intel_i9-12900KS_O3_LLVM_19.txt)
- [LLVM 20.1.8](./data-trixie/others/SPEC_INT_2026_Intel_i9-12900KS_O3_LLVM_20.txt)
- [LLVM 21.1.8](./data-trixie/others/SPEC_INT_2026_Intel_i9-12900KS_O3_LLVM_21.txt)
- [LLVM 22.1.6](./data-trixie/others/SPEC_INT_2026_Intel_i9-12900KS_O3_LLVM_22.txt)

## SPEC FP 2026 Rate-1

下面贴出自己测的数据（SPECfp2026，Estimated，rate，base，1 copy），不保证满足 SPEC 的要求，仅供参考。

### 原始数据

#### Debian Trixie

桌面平台（`-march=native`）：

- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3 -march=native`）: [5.97](./data-trixie/fp2026_rate1/Apple_M1_P-Core_O3-march=native_001.txt)
- Apple M2 P-Core @ 3.5 GHz Avalanche（`-O3 -march=native`）: [6.73](./data-trixie/fp2026_rate1/Apple_M2_P-Core_O3-march=native_001.txt)
- Huawei Kirin X90 VM P-Core @ 2.3 GHz（`-O3 -march=native`）: [3.95](./data-trixie/fp2026_rate1/Huawei_Kirin_X90_VM_P-Core_O3-march=native_001.txt)
- Intel Core i7-13700K P-Core @ 5.4 GHz Raptor Cove（`-O3 -march=native`）: [7.96](./data-trixie/fp2026_rate1/Intel_Core_i7-13700K_P-Core_O3-march=native_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz (AVX-512 @ 4.0 GHz) Cascade Lake（`-O3 -march=native`）: [4.22](./data-trixie/fp2026_rate1/Intel_Core_i9-10980XE_O3-march=native_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3 -march=native`）: [3.97](./data-trixie/fp2026_rate1/Intel_Core_i9-12900KS_E-Core_O3-march=native_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3 -march=native`）: [8.09](./data-trixie/fp2026_rate1/Intel_Core_i9-12900KS_P-Core_O3-march=native_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3 -march=native`）: [4.19](./data-trixie/fp2026_rate1/Intel_Core_i9-14900K_E-Core_O3-march=native_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3 -march=native`）: [9.36](./data-trixie/fp2026_rate1/Intel_Core_i9-14900K_P-Core_O3-march=native_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3 -march=native`）: [6.34](./data-trixie/fp2026_rate1/Intel_Xeon_w9-3595X_O3-march=native_001.txt)

桌面平台：

- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3`）: [5.80](./data-trixie/fp2026_rate1/Apple_M1_P-Core_O3_001.txt)
- Apple M2 P-Core @ 3.5 GHz Avalanche（`-O3`）: [6.38](./data-trixie/fp2026_rate1/Apple_M2_P-Core_O3_001.txt)
- Huawei Kirin X90 VM P-Core @ 2.3 GHz（`-O3`）: [3.76](./data-trixie/fp2026_rate1/Huawei_Kirin_X90_VM_P-Core_O3_001.txt)
- Intel Core i7-13700K P-Core @ 5.4 GHz Raptor Cove（`-O3`）: [6.32](./data-trixie/fp2026_rate1/Intel_Core_i7-13700K_P-Core_O3_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3`）: [3.55](./data-trixie/fp2026_rate1/Intel_Core_i9-10980XE_O3_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3`）: [3.46](./data-trixie/fp2026_rate1/Intel_Core_i9-12900KS_E-Core_O3_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3`）: [6.56](./data-trixie/fp2026_rate1/Intel_Core_i9-12900KS_P-Core_O3_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3`）: [3.66](./data-trixie/fp2026_rate1/Intel_Core_i9-14900K_E-Core_O3_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3`）: [7.44](./data-trixie/fp2026_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3`）: [5.01](./data-trixie/fp2026_rate1/Intel_Xeon_w9-3595X_O3_001.txt)

服务器平台（`-march=native`）：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3 -march=native`）: [2.04](./data-trixie/fp2026_rate1/AMD_EPYC_7551_O3-march=native_001.txt)
- AWS Graviton 5 @ 3.3 GHz Neoverse V3（`-O3 -march=native`）: [6.10](./data-trixie/fp2026_rate1/AWS_Graviton_5_O3-march=native_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3 -march=native`）: [2.74](./data-trixie/fp2026_rate1/Intel_Xeon_E5-2680_v4_O3-march=native_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3 -march=native`）: [1.62](./data-trixie/fp2026_rate1/Kunpeng_920_O3-march=native_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3 -march=native`）: [3.69](./data-trixie/fp2026_rate1/Kunpeng_920_HuaweiCloud_kc2_O3-march=native_001.txt)

服务器平台：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3`）: [1.86](./data-trixie/fp2026_rate1/AMD_EPYC_7551_O3_001.txt)
- AWS Graviton 5 @ 3.3 GHz Neoverse V3（`-O3`）: [5.67](./data-trixie/fp2026_rate1/AWS_Graviton_5_O3_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3`）: [2.43](./data-trixie/fp2026_rate1/Intel_Xeon_E5-2680_v4_O3_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3`）: [1.54](./data-trixie/fp2026_rate1/Kunpeng_920_O3_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3`）: [3.78](./data-trixie/fp2026_rate1/Kunpeng_920_HuaweiCloud_kc2_O3_001.txt)

#### 备注

1. 对于除了苹果以外的 ARM64 核心，内核的 branch-misses 计数器考虑了 speculative 而不只是 retired，因此数字会偏高，此时要用 r22 计数替代。

### 网上的数据

来自 SPEC 官网：

| Machine                                                                                             | Score | Compilation Flags                                                         |
|-----------------------------------------------------------------------------------------------------|-------|---------------------------------------------------------------------------|
| [Ampere eMAG 8180](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260210-00001.html)      | 1.00  | -O3 -ffast-math -mcpu=native -flto=16 -ljemalloc                          |
| [AMD Ryzen AI 9 HX 370](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260210-00017.html) | 8.59  | -O3 -ffast-math -march=native -flto=full                                  |
| [NVIDIA GB10](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260210-00019.html)           | 9.70  | -fuse-ld=lld -O3 -ffast-math -mcpu=native -flto=thin -fomit-frame-pointer |
| [Apple M5 Pro](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260422-00245.html)          | 10.9  | -O3                                                                       |

另见 [David Huang](https://benchview.hjc.im)、[Chips and Cheese](https://chipsandcheese.com/p/evaluating-spec-cpu2026)。

### 多版本 GCC 和 LLVM 性能比较

在 Intel i9-12900KS @ 5.5 GHz 上用 -O3 测试几种编译器组合的 SPEC FP 2026 Rate-1 性能：

| Benchmark       | GCC 16   | GCC 15   | GCC 14 | LLVM 22  | LLVM 21  | LLVM 20  |
|-----------------|----------|----------|--------|----------|----------|----------|
| 709.cactus_r    | 6.77     | 7.52     | 7.62   | 8.28     | **8.29** | 8.16     |
| 722.palm_r      | 7.79     | 7.81     | 7.88   | **9.20** | 9.00     | 8.44     |
| 731.astcenc_r   | 4.77     | 4.76     | 4.60   | 5.96     | 5.84     | **6.16** |
| 736.ocio_r      | 6.20     | 6.25     | 6.26   | 6.81     | **6.87** | 6.84     |
| 737.gmsh_r      | **4.55** | 4.53     | 4.50   | 4.40     | 4.38     | 4.40     |
| 748.flightdm_r  | **7.76** | 7.54     | 7.42   | 7.05     | 7.09     | 7.11     |
| 749.fotonik3d_r | 6.81     | 6.82     | 6.82   | 6.93     | **6.99** | 6.76     |
| 765.roms_r      | 7.50     | 7.39     | 7.40   | **7.52** | 7.51     | 7.38     |
| 766.femflow_r   | 9.92     | 7.97     | 8.16   | **12.1** | **12.1** | **12.1** |
| 767.nest_r      | 7.17     | **8.60** | 8.50   | 8.15     | 8.18     | 8.15     |
| 772.marian_r    | **10.3** | **10.3** | 6.58   | 4.78     | 4.78     | 4.78     |
| 782.lbm_r       | **4.81** | **4.81** | 4.80   | 4.49     | 4.49     | 4.47     |
| geomean         | 6.81     | **6.83** | 6.56   | 6.84     | **6.83** | 6.79     |

完整数据：

- [GCC 14.2.0](./data-trixie/others/SPEC_FP_2026_Intel_i9-12900KS_O3_GCC_14.txt)
- [GCC 15.2.0](./data-trixie/others/SPEC_FP_2026_Intel_i9-12900KS_O3_GCC_15.txt)
- [GCC 16.1.0](./data-trixie/others/SPEC_FP_2026_Intel_i9-12900KS_O3_GCC_16.txt)
- [LLVM 20.1.8](./data-trixie/others/SPEC_FP_2026_Intel_i9-12900KS_O3_LLVM_20.txt)
- [LLVM 21.1.8](./data-trixie/others/SPEC_FP_2026_Intel_i9-12900KS_O3_LLVM_21.txt)
- [LLVM 22.1.6](./data-trixie/others/SPEC_FP_2026_Intel_i9-12900KS_O3_LLVM_22.txt)
