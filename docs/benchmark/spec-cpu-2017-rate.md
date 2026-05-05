# SPEC CPU 2017 Rate

## SPEC INT 2017 Rate-1

下面贴出自己测的数据（SPECint2017，Estimated，rate，base，1 copy），不保证满足 SPEC 的要求，仅供参考。总运行时间（秒）基本和分数成反比，乘积按 5e4 估算。

### 数据总览

#### Debian Trixie

![](./data-trixie/int2017_rate1_score.svg)

![](./data-trixie/int2017_rate1_table.svg)

??? note "分数/GHz"

    ![](./data-trixie/int2017_rate1_score_per_ghz.svg)

??? note "每项分数"

    ![](./data-trixie/int2017_rate1_ratio.svg)

??? note "IPC"

    ![](./data-trixie/int2017_rate1_ipc.svg)

??? note "分支预测 MPKI"

    ![](./data-trixie/int2017_rate1_mpki.svg)

??? note "分支预测错误率"

    ![](./data-trixie/int2017_rate1_mispred.svg)

??? note "频率"

    ![](./data-trixie/int2017_rate1_freq.svg)

??? note "指令数"

    ![](./data-trixie/int2017_rate1_inst.svg)


#### Debian Bookworm

![](./data-bookworm/int2017_rate1_score.svg)

![](./data-bookworm/int2017_rate1_table.svg)

??? note "分数/GHz"

    ![](./data-bookworm/int2017_rate1_score_per_ghz.svg)

??? note "每项分数"

    ![](./data-bookworm/int2017_rate1_ratio.svg)

??? note "IPC"

    ![](./data-bookworm/int2017_rate1_ipc.svg)

??? note "分支预测 MPKI"

    ![](./data-bookworm/int2017_rate1_mpki.svg)

??? note "分支预测错误率"

    ![](./data-bookworm/int2017_rate1_mispred.svg)

??? note "频率"

    ![](./data-bookworm/int2017_rate1_freq.svg)

??? note "指令数"

    ![](./data-bookworm/int2017_rate1_inst.svg)

#### HarmonyOS

![](./data-harmonyos/int2017_rate1_score.svg)

![](./data-harmonyos/int2017_rate1_table.svg)

??? note "每项分数"

    ![](./data-harmonyos/int2017_rate1_ratio.svg)

### 原始数据

#### Debian Trixie

桌面平台（LTO + Jemalloc）：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3 -flto -ljemalloc`）: [9.31](./data-trixie/int2017_rate1/AMD_Ryzen_7_5700X_O3-flto-ljemalloc_001.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3 -flto -ljemalloc`）: [3.58](./data-trixie/int2017_rate1/Apple_M1_E-Core_O3-flto-ljemalloc_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3 -flto -ljemalloc`）: [9.14](./data-trixie/int2017_rate1/Apple_M1_P-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i5-1135G7 @ 4.2 GHz Willow Cove（`-O3 -flto -ljemalloc`）: [7.28](./data-trixie/int2017_rate1/Intel_Core_i5-1135G7_O3-flto-ljemalloc_001.txt)
- Intel Core i7-13700K E-Core @ 4.2 GHz Gracemont（`-O3 -flto -ljemalloc`）: [7.43](./data-trixie/int2017_rate1/Intel_Core_i7-13700K_E-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i7-13700K P-Core @ 5.2 GHz Raptor Cove（`-O3 -flto -ljemalloc`）: [10.9](./data-trixie/int2017_rate1/Intel_Core_i7-13700K_P-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3 -flto -ljemalloc`）: [6.96](./data-trixie/int2017_rate1/Intel_Core_i9-10980XE_O3-flto-ljemalloc_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3 -flto -ljemalloc`）: [6.63](./data-trixie/int2017_rate1/Intel_Core_i9-12900KS_E-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3 -flto -ljemalloc`）: [10.6](./data-trixie/int2017_rate1/Intel_Core_i9-12900KS_P-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3 -flto -ljemalloc`）: [7.90](./data-trixie/int2017_rate1/Intel_Core_i9-14900K_E-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3 -flto -ljemalloc`）: [12.6](./data-trixie/int2017_rate1/Intel_Core_i9-14900K_P-Core_O3-flto-ljemalloc_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3 -flto -ljemalloc`）: [8.96](./data-trixie/int2017_rate1/Intel_Xeon_w9-3595X_O3-flto-ljemalloc_001.txt)
- Loongson 3A6000 @ 2.5 GHz LA664（`-O3 -flto -ljemalloc`）: [4.86](./data-trixie/int2017_rate1/Loongson_3A6000_O3-flto-ljemalloc_001.txt)

桌面平台（LTO）：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3 -flto`）: [8.57](./data-trixie/int2017_rate1/AMD_Ryzen_7_5700X_O3-flto_001.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3 -flto`）: [3.34](./data-trixie/int2017_rate1/Apple_M1_E-Core_O3-flto_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3 -flto`）: [8.40](./data-trixie/int2017_rate1/Apple_M1_P-Core_O3-flto_001.txt)
- Intel Core i5-1135G7 @ 4.2 GHz Willow Cove（`-O3 -flto`）: [6.80](./data-trixie/int2017_rate1/Intel_Core_i5-1135G7_O3-flto_001.txt)
- Intel Core i7-13700K E-Core @ 4.2 GHz Gracemont（`-O3 -flto`）: [6.97](./data-trixie/int2017_rate1/Intel_Core_i7-13700K_E-Core_O3-flto_001.txt)
- Intel Core i7-13700K P-Core @ 5.2 GHz Raptor Cove（`-O3 -flto`）: [10.3](./data-trixie/int2017_rate1/Intel_Core_i7-13700K_P-Core_O3-flto_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3 -flto`）: [6.57](./data-trixie/int2017_rate1/Intel_Core_i9-10980XE_O3-flto_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3 -flto`）: [6.31](./data-trixie/int2017_rate1/Intel_Core_i9-12900KS_E-Core_O3-flto_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3 -flto`）: [10.0](./data-trixie/int2017_rate1/Intel_Core_i9-12900KS_P-Core_O3-flto_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3 -flto`）: [7.43](./data-trixie/int2017_rate1/Intel_Core_i9-14900K_E-Core_O3-flto_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3 -flto`）: [12.1](./data-trixie/int2017_rate1/Intel_Core_i9-14900K_P-Core_O3-flto_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3 -flto`）: [8.41](./data-trixie/int2017_rate1/Intel_Xeon_w9-3595X_O3-flto_001.txt)
- Loongson 3A6000 @ 2.5 GHz LA664（`-O3 -flto`）: [4.56](./data-trixie/int2017_rate1/Loongson_3A6000_O3-flto_001.txt)

桌面平台：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3`）: [8.19](./data-trixie/int2017_rate1/AMD_Ryzen_7_5700X_O3_001.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3`）: [3.20](./data-trixie/int2017_rate1/Apple_M1_E-Core_O3_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3`）: [7.97](./data-trixie/int2017_rate1/Apple_M1_P-Core_O3_001.txt)
- Intel Core i5-1135G7 @ 4.2 GHz Willow Cove（`-O3`）: [6.58](./data-trixie/int2017_rate1/Intel_Core_i5-1135G7_O3_001.txt)
- Intel Core i7-13700K E-Core @ 4.2 GHz Gracemont（`-O3`）: [6.72](./data-trixie/int2017_rate1/Intel_Core_i7-13700K_E-Core_O3_001.txt)
- Intel Core i7-13700K P-Core @ 5.2 GHz Raptor Cove（`-O3`）: [9.85](./data-trixie/int2017_rate1/Intel_Core_i7-13700K_P-Core_O3_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3`）: [6.31](./data-trixie/int2017_rate1/Intel_Core_i9-10980XE_O3_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3`）: [6.10](./data-trixie/int2017_rate1/Intel_Core_i9-12900KS_E-Core_O3_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3`）: [9.74](./data-trixie/int2017_rate1/Intel_Core_i9-12900KS_P-Core_O3_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3`）: [7.18](./data-trixie/int2017_rate1/Intel_Core_i9-14900K_E-Core_O3_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3`）: [11.6](./data-trixie/int2017_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3`）: [8.23](./data-trixie/int2017_rate1/Intel_Xeon_w9-3595X_O3_001.txt)
- Loongson 3A6000 @ 2.5 GHz LA664（`-O3`）: [4.35](./data-trixie/int2017_rate1/Loongson_3A6000_O3_001.txt) [4.39](./data-trixie/int2017_rate1/Loongson_3A6000_O3_002.txt)

服务器平台（LTO + Jemalloc）：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3 -flto -ljemalloc`）: [3.49](./data-trixie/int2017_rate1/AMD_EPYC_7551_O3-flto-ljemalloc_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3 -flto -ljemalloc`）: [5.48](./data-trixie/int2017_rate1/AMD_EPYC_7742_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9R45 @ 4.5 GHz Zen 5（`-O3 -flto -ljemalloc`）: [10.3](./data-trixie/int2017_rate1/AMD_EPYC_9R45_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9T95 @ 3.7 GHz Zen 5c（`-O3 -flto -ljemalloc`）: [8.80](./data-trixie/int2017_rate1/AMD_EPYC_9T95_O3-flto-ljemalloc_001.txt)
- Google Axion C4A @ Neoverse V2（`-O3 -flto -ljemalloc`）: [8.23](./data-trixie/int2017_rate1/Google_Axion_C4A_O3-flto-ljemalloc_001.txt)
- Google Axion N4A @ Neoverse N3（`-O3 -flto -ljemalloc`）: [7.97](./data-trixie/int2017_rate1/Google_Axion_N4A_O3-flto-ljemalloc_001.txt)
- IBM POWER8 @ 3.2 GHz POWER8（`-O3 -flto -ljemalloc`）: [3.63](./data-trixie/int2017_rate1/IBM_POWER8_O3-flto-ljemalloc_001.txt)
- IBM POWER9 3.2 GHz @ 3.2 GHz POWER9（`-O3 -flto -ljemalloc`）: [3.53](./data-trixie/int2017_rate1/IBM_POWER9_3.2_GHz_O3-flto-ljemalloc_001.txt)
- IBM POWER9 3.8 GHz @ 3.2 GHz POWER9（`-O3 -flto -ljemalloc`）: [4.81](./data-trixie/int2017_rate1/IBM_POWER9_3.8_GHz_O3-flto-ljemalloc_001.txt)
- Intel Xeon 6975P-C @ 3.9 GHz Redwood Cove（`-O3 -flto -ljemalloc`）: [8.03](./data-trixie/int2017_rate1/Intel_Xeon_6975P-C_O3-flto-ljemalloc_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3 -flto -ljemalloc`）: [4.95](./data-trixie/int2017_rate1/Intel_Xeon_E5-2680_v4_O3-flto-ljemalloc_001.txt)
- Intel Xeon Gold 6430 @ 2.6 GHz Golden Cove（`-O3 -flto -ljemalloc`）: [5.39](./data-trixie/int2017_rate1/Intel_Xeon_Gold_6430_O3-flto-ljemalloc_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Sunny Cove（`-O3 -flto -ljemalloc`）: [6.17](./data-trixie/int2017_rate1/Intel_Xeon_Platinum_8358P_O3-flto-ljemalloc_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3 -flto -ljemalloc`）: [3.65](./data-trixie/int2017_rate1/Kunpeng_920_O3-flto-ljemalloc_001.txt)
- Loongson 3C6000 @ 2.2 GHz LA664（`-O3 -flto -ljemalloc`）: [4.54](./data-trixie/int2017_rate1/Loongson_3C6000_O3-flto-ljemalloc_001.txt)

服务器平台（LTO）：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3 -flto`）: [3.28](./data-trixie/int2017_rate1/AMD_EPYC_7551_O3-flto_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3 -flto`）: [5.05](./data-trixie/int2017_rate1/AMD_EPYC_7742_O3-flto_001.txt)
- AMD EPYC 9R45 @ 4.5 GHz Zen 5（`-O3 -flto`）: [9.49](./data-trixie/int2017_rate1/AMD_EPYC_9R45_O3-flto_001.txt)
- AMD EPYC 9T95 @ 3.7 GHz Zen 5c（`-O3 -flto`）: [8.18](./data-trixie/int2017_rate1/AMD_EPYC_9T95_O3-flto_001.txt)
- Google Axion C4A @ Neoverse V2（`-O3 -flto`）: [7.68](./data-trixie/int2017_rate1/Google_Axion_C4A_O3-flto_001.txt)
- Google Axion N4A @ Neoverse N3（`-O3 -flto`）: [7.44](./data-trixie/int2017_rate1/Google_Axion_N4A_O3-flto_001.txt)
- IBM POWER8 @ 3.2 GHz POWER8（`-O3 -flto`）: [3.45](./data-trixie/int2017_rate1/IBM_POWER8_O3-flto_001.txt)
- IBM POWER9 3.2 GHz @ 3.2 GHz POWER9（`-O3 -flto`）: [3.30](./data-trixie/int2017_rate1/IBM_POWER9_3.2_GHz_O3-flto_001.txt)
- IBM POWER9 3.8 GHz @ 3.2 GHz POWER9（`-O3 -flto`）: [4.41](./data-trixie/int2017_rate1/IBM_POWER9_3.8_GHz_O3-flto_001.txt)
- Intel Xeon 6975P-C @ 3.9 GHz Redwood Cove（`-O3 -flto`）: [7.65](./data-trixie/int2017_rate1/Intel_Xeon_6975P-C_O3-flto_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3 -flto`）: [4.59](./data-trixie/int2017_rate1/Intel_Xeon_E5-2680_v4_O3-flto_001.txt)
- Intel Xeon Gold 6430 @ 2.6 GHz Golden Cove（`-O3 -flto`）: [5.16](./data-trixie/int2017_rate1/Intel_Xeon_Gold_6430_O3-flto_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Sunny Cove（`-O3 -flto`）: [5.91](./data-trixie/int2017_rate1/Intel_Xeon_Platinum_8358P_O3-flto_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3 -flto`）: [3.32](./data-trixie/int2017_rate1/Kunpeng_920_O3-flto_001.txt)
- Loongson 3C6000 @ 2.2 GHz LA664（`-O3 -flto`）: [4.39](./data-trixie/int2017_rate1/Loongson_3C6000_O3-flto_001.txt) [4.37](./data-trixie/int2017_rate1/Loongson_3C6000_O3-flto_002.txt)

服务器平台：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3`）: [3.12](./data-trixie/int2017_rate1/AMD_EPYC_7551_O3_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3`）: [4.78](./data-trixie/int2017_rate1/AMD_EPYC_7742_O3_001.txt)
- AMD EPYC 9R45 @ 4.5 GHz Zen 5（`-O3`）: [9.07](./data-trixie/int2017_rate1/AMD_EPYC_9R45_O3_001.txt)
- AMD EPYC 9T95 @ 3.7 GHz Zen 5c（`-O3`）: [7.83](./data-trixie/int2017_rate1/AMD_EPYC_9T95_O3_001.txt)
- Google Axion C4A @ Neoverse V2（`-O3`）: [7.25](./data-trixie/int2017_rate1/Google_Axion_C4A_O3_001.txt)
- Google Axion N4A @ Neoverse N3（`-O3`）: [7.16](./data-trixie/int2017_rate1/Google_Axion_N4A_O3_001.txt)
- IBM POWER8 @ 3.2 GHz POWER8（`-O3`）: [3.24](./data-trixie/int2017_rate1/IBM_POWER8_O3_001.txt)
- IBM POWER9 3.2 GHz @ 3.2 GHz POWER9（`-O3`）: [3.01](./data-trixie/int2017_rate1/IBM_POWER9_3.2_GHz_O3_001.txt)
- IBM POWER9 3.8 GHz @ 3.2 GHz POWER9（`-O3`）: [4.14](./data-trixie/int2017_rate1/IBM_POWER9_3.8_GHz_O3_001.txt)
- Intel Xeon 6975P-C @ 3.9 GHz Redwood Cove（`-O3`）: [7.38](./data-trixie/int2017_rate1/Intel_Xeon_6975P-C_O3_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3`）: [4.39](./data-trixie/int2017_rate1/Intel_Xeon_E5-2680_v4_O3_001.txt)
- Intel Xeon Gold 6430 @ 2.6 GHz Golden Cove（`-O3`）: [4.97](./data-trixie/int2017_rate1/Intel_Xeon_Gold_6430_O3_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Sunny Cove（`-O3`）: [5.66](./data-trixie/int2017_rate1/Intel_Xeon_Platinum_8358P_O3_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3`）: [3.17](./data-trixie/int2017_rate1/Kunpeng_920_O3_001.txt)
- Loongson 3C5000 @ 2.2 GHz LA464（`-O3`）: [2.63](./data-trixie/int2017_rate1/Loongson_3C5000_O3_001.txt)
- Loongson 3C6000 @ 2.2 GHz LA664（`-O3`）: [4.19](./data-trixie/int2017_rate1/Loongson_3C6000_O3_001.txt) [4.14](./data-trixie/int2017_rate1/Loongson_3C6000_O3_002.txt)

#### Debian Bookworm

桌面平台（LTO + Jemalloc）：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3 -flto -ljemalloc`）: [9.13](./data-bookworm/int2017_rate1/AMD_Ryzen_7_5700X_O3-flto-ljemalloc_001.txt)
- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3 -flto -ljemalloc`）: [12.9](./data-bookworm/int2017_rate1/AMD_Ryzen_9_9950X_O3-flto-ljemalloc_001.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3 -flto -ljemalloc`）: [3.52](./data-bookworm/int2017_rate1/Apple_M1_E-Core_O3-flto-ljemalloc_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3 -flto -ljemalloc`）: [8.93](./data-bookworm/int2017_rate1/Apple_M1_P-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3 -flto -ljemalloc`）: [6.70](./data-bookworm/int2017_rate1/Intel_Core_i9-10980XE_O3-flto-ljemalloc_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3 -flto -ljemalloc`）: [10.7](./data-bookworm/int2017_rate1/Intel_Core_i9-12900KS_P-Core_O3-flto-ljemalloc_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3 -flto -ljemalloc`）: [12.1](./data-bookworm/int2017_rate1/Intel_Core_i9-14900K_P-Core_O3-flto-ljemalloc_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3 -flto -ljemalloc`）: [8.71](./data-bookworm/int2017_rate1/Intel_Xeon_w9-3595X_O3-flto-ljemalloc_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3 -flto -ljemalloc`）: [9.25](./data-bookworm/int2017_rate1/Qualcomm_X1E80100_O3-flto-ljemalloc_001.txt)

桌面平台（LTO）：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3 -flto`）: [8.44](./data-bookworm/int2017_rate1/AMD_Ryzen_7_5700X_O3-flto_001.txt)
- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3 -flto`）: [11.7](./data-bookworm/int2017_rate1/AMD_Ryzen_9_9950X_O3-flto_001.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3 -flto`）: [3.29](./data-bookworm/int2017_rate1/Apple_M1_E-Core_O3-flto_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3 -flto`）: [8.24](./data-bookworm/int2017_rate1/Apple_M1_P-Core_O3-flto_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3 -flto`）: [6.37](./data-bookworm/int2017_rate1/Intel_Core_i9-10980XE_O3-flto_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3 -flto`）: [9.97](./data-bookworm/int2017_rate1/Intel_Core_i9-12900KS_P-Core_O3-flto_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3 -flto`）: [11.7](./data-bookworm/int2017_rate1/Intel_Core_i9-14900K_P-Core_O3-flto_001.txt) [11.7](./data-bookworm/int2017_rate1/Intel_Core_i9-14900K_P-Core_O3-flto_002.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3 -flto`）: [8.30](./data-bookworm/int2017_rate1/Intel_Xeon_w9-3595X_O3-flto_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3 -flto`）: [8.62](./data-bookworm/int2017_rate1/Qualcomm_X1E80100_O3-flto_001.txt)

桌面平台：

- AMD Ryzen 5 7500F @ 5.0 GHz Zen 4（`-O3`）: [9.51](./data-bookworm/int2017_rate1/AMD_Ryzen_5_7500F_O3_001.txt)
- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3`）: [7.87](./data-bookworm/int2017_rate1/AMD_Ryzen_7_5700X_O3_001.txt)
- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3`）: [11.2](./data-bookworm/int2017_rate1/AMD_Ryzen_9_9950X_O3_001.txt) [11.3](./data-bookworm/int2017_rate1/AMD_Ryzen_9_9950X_O3_002.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3`）: [3.15](./data-bookworm/int2017_rate1/Apple_M1_E-Core_O3_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3`）: [7.85](./data-bookworm/int2017_rate1/Apple_M1_P-Core_O3_001.txt)
- Huawei Kirin X90 VM P-Core @ 2.3 GHz（`-O3`）: [4.07](./data-bookworm/int2017_rate1/Huawei_Kirin_X90_VM_P-Core_O3_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3`）: [6.24](./data-bookworm/int2017_rate1/Intel_Core_i9-10980XE_O3_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3`）: [6.08](./data-bookworm/int2017_rate1/Intel_Core_i9-12900KS_E-Core_O3_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3`）: [9.62](./data-bookworm/int2017_rate1/Intel_Core_i9-12900KS_P-Core_O3_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3`）: [7.03](./data-bookworm/int2017_rate1/Intel_Core_i9-14900K_E-Core_O3_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3`）: [11.3](./data-bookworm/int2017_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3`）: [8.05](./data-bookworm/int2017_rate1/Intel_Xeon_w9-3595X_O3_001.txt)
- Qualcomm 8cx Gen3 E-Core @ 2.4 GHz Cortex-A78C（`-O3`）: [4.11](./data-bookworm/int2017_rate1/Qualcomm_8cx_Gen3_E-Core_O3_001.txt)
- Qualcomm 8cx Gen3 P-Core @ 3.0 GHz Cortex-X1C（`-O3`）: [5.73](./data-bookworm/int2017_rate1/Qualcomm_8cx_Gen3_P-Core_O3_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3`）: [8.31](./data-bookworm/int2017_rate1/Qualcomm_X1E80100_O3_001.txt)

服务器平台（LTO + Jemalloc）：

- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3 -flto -ljemalloc`）: [5.33](./data-bookworm/int2017_rate1/AMD_EPYC_7742_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9754 @ 3.1 GHz Zen 4c（`-O3 -flto -ljemalloc`）: [5.79](./data-bookworm/int2017_rate1/AMD_EPYC_9754_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9755 @ 4.1 GHz Zen 5（`-O3 -flto -ljemalloc`）: [9.66](./data-bookworm/int2017_rate1/AMD_EPYC_9755_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9K65 @ 3.7 GHz Zen 5c（`-O3 -flto -ljemalloc`）: [8.19](./data-bookworm/int2017_rate1/AMD_EPYC_9K65_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9K85 @ 4.1 GHz Zen 5（`-O3 -flto -ljemalloc`）: [9.48](./data-bookworm/int2017_rate1/AMD_EPYC_9K85_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9R14 @ 3.7 GHz Zen 4（`-O3 -flto -ljemalloc`）: [7.21](./data-bookworm/int2017_rate1/AMD_EPYC_9R14_O3-flto-ljemalloc_001.txt)
- AMD EPYC 9T24 @ 3.7 GHz Zen 4（`-O3 -flto -ljemalloc`）: [7.62](./data-bookworm/int2017_rate1/AMD_EPYC_9T24_O3-flto-ljemalloc_001.txt)
- AWS Graviton 3 @ 2.6 GHz Neoverse V1（`-O3 -flto -ljemalloc`）: [5.24](./data-bookworm/int2017_rate1/AWS_Graviton_3_O3-flto-ljemalloc_001.txt)
- AWS Graviton 3E @ 2.6 GHz Neoverse V1（`-O3 -flto -ljemalloc`）: [6.17](./data-bookworm/int2017_rate1/AWS_Graviton_3E_O3-flto-ljemalloc_001.txt)
- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3 -flto -ljemalloc`）: [7.64](./data-bookworm/int2017_rate1/AWS_Graviton_4_O3-flto-ljemalloc_001.txt) [7.41](./data-bookworm/int2017_rate1/AWS_Graviton_4_O3-flto-ljemalloc_002.txt)
- Hygon C86 7390（`-O3 -flto -ljemalloc`）: [3.29](./data-bookworm/int2017_rate1/Hygon_C86_7390_O3-flto-ljemalloc_001.txt)
- IBM POWER8NVL @ 4.0 GHz POWER8（`-O3 -flto -ljemalloc`）: [4.02](./data-bookworm/int2017_rate1/IBM_POWER8NVL_O3-flto-ljemalloc_001.txt)
- Intel Xeon 6981E Crestmont（`-O3 -flto -ljemalloc`）: [4.79](./data-bookworm/int2017_rate1/Intel_Xeon_6981E_O3-flto-ljemalloc_001.txt)
- Intel Xeon 6982P-C @ 3.6 GHz Redwood Cove（`-O3 -flto -ljemalloc`）: [7.22](./data-bookworm/int2017_rate1/Intel_Xeon_6982P-C_O3-flto-ljemalloc_001.txt)
- Intel Xeon Platinum 8581C @ 3.4 GHz Raptor Cove（`-O3 -flto -ljemalloc`）: [6.87](./data-bookworm/int2017_rate1/Intel_Xeon_Platinum_8581C_O3-flto-ljemalloc_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3 -flto -ljemalloc`）: [3.57](./data-bookworm/int2017_rate1/Kunpeng_920_O3-flto-ljemalloc_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3 -flto -ljemalloc`）: [6.03](./data-bookworm/int2017_rate1/Kunpeng_920_HuaweiCloud_kc2_O3-flto-ljemalloc_001.txt)

服务器平台（LTO）：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3 -flto`）: [3.19](./data-bookworm/int2017_rate1/AMD_EPYC_7551_O3-flto_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3 -flto`）: [5.02](./data-bookworm/int2017_rate1/AMD_EPYC_7742_O3-flto_001.txt)
- AMD EPYC 9754 @ 3.1 GHz Zen 4c（`-O3 -flto`）: [5.48](./data-bookworm/int2017_rate1/AMD_EPYC_9754_O3-flto_001.txt)
- AMD EPYC 9755 @ 4.1 GHz Zen 5（`-O3 -flto`）: [8.97](./data-bookworm/int2017_rate1/AMD_EPYC_9755_O3-flto_001.txt)
- AMD EPYC 9K65 @ 3.7 GHz Zen 5c（`-O3 -flto`）: [7.78](./data-bookworm/int2017_rate1/AMD_EPYC_9K65_O3-flto_001.txt)
- AMD EPYC 9K85 @ 4.1 GHz Zen 5（`-O3 -flto`）: [8.83](./data-bookworm/int2017_rate1/AMD_EPYC_9K85_O3-flto_001.txt)
- AMD EPYC 9R14 @ 3.7 GHz Zen 4（`-O3 -flto`）: [6.62](./data-bookworm/int2017_rate1/AMD_EPYC_9R14_O3-flto_001.txt)
- AMD EPYC 9T24 @ 3.7 GHz Zen 4（`-O3 -flto`）: [7.14](./data-bookworm/int2017_rate1/AMD_EPYC_9T24_O3-flto_001.txt)
- AWS Graviton 3 @ 2.6 GHz Neoverse V1（`-O3 -flto`）: [5.68](./data-bookworm/int2017_rate1/AWS_Graviton_3_O3-flto_001.txt)
- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3 -flto`）: [7.14](./data-bookworm/int2017_rate1/AWS_Graviton_4_O3-flto_001.txt) [6.53](./data-bookworm/int2017_rate1/AWS_Graviton_4_O3-flto_002.txt) [6.51](./data-bookworm/int2017_rate1/AWS_Graviton_4_O3-flto_003.txt)
- Hygon C86 7390（`-O3 -flto`）: [3.09](./data-bookworm/int2017_rate1/Hygon_C86_7390_O3-flto_001.txt)
- Intel Xeon 6981E Crestmont（`-O3 -flto`）: [4.62](./data-bookworm/int2017_rate1/Intel_Xeon_6981E_O3-flto_001.txt)
- Intel Xeon 6982P-C @ 3.6 GHz Redwood Cove（`-O3 -flto`）: [6.90](./data-bookworm/int2017_rate1/Intel_Xeon_6982P-C_O3-flto_001.txt)
- Intel Xeon Platinum 8581C @ 3.4 GHz Raptor Cove（`-O3 -flto`）: [6.67](./data-bookworm/int2017_rate1/Intel_Xeon_Platinum_8581C_O3-flto_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3 -flto`）: [3.26](./data-bookworm/int2017_rate1/Kunpeng_920_O3-flto_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3 -flto`）: [5.71](./data-bookworm/int2017_rate1/Kunpeng_920_HuaweiCloud_kc2_O3-flto_001.txt)

服务器平台：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3`）: [3.07](./data-bookworm/int2017_rate1/AMD_EPYC_7551_O3_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3`）: [4.73](./data-bookworm/int2017_rate1/AMD_EPYC_7742_O3_001.txt)
- AMD EPYC 7H12 @ 3.3 GHz Zen 2（`-O3`）: [4.23](./data-bookworm/int2017_rate1/AMD_EPYC_7H12_O3_001.txt)
- AMD EPYC 7K83 Zen 3（`-O3`）: [5.18](./data-bookworm/int2017_rate1/AMD_EPYC_7K83_O3_001.txt)
- AMD EPYC 9754 @ 3.1 GHz Zen 4c（`-O3`）: [5.33](./data-bookworm/int2017_rate1/AMD_EPYC_9754_O3_001.txt)
- AMD EPYC 9755 @ 4.1 GHz Zen 5（`-O3`）: [8.57](./data-bookworm/int2017_rate1/AMD_EPYC_9755_O3_001.txt)
- AMD EPYC 9K65 @ 3.7 GHz Zen 5c（`-O3`）: [7.47](./data-bookworm/int2017_rate1/AMD_EPYC_9K65_O3_001.txt)
- AMD EPYC 9K85 @ 4.1 GHz Zen 5（`-O3`）: [8.44](./data-bookworm/int2017_rate1/AMD_EPYC_9K85_O3_001.txt)
- AMD EPYC 9R14 @ 3.7 GHz Zen 4（`-O3`）: [6.57](./data-bookworm/int2017_rate1/AMD_EPYC_9R14_O3_001.txt) [6.41](./data-bookworm/int2017_rate1/AMD_EPYC_9R14_O3_002.txt)
- AMD EPYC 9T24 @ 3.7 GHz Zen 4（`-O3`）: [6.94](./data-bookworm/int2017_rate1/AMD_EPYC_9T24_O3_001.txt)
- AWS Graviton 3 @ 2.6 GHz Neoverse V1（`-O3`）: [5.43](./data-bookworm/int2017_rate1/AWS_Graviton_3_O3_001.txt)
- AWS Graviton 3E @ 2.6 GHz Neoverse V1（`-O3`）: [5.53](./data-bookworm/int2017_rate1/AWS_Graviton_3E_O3_001.txt)
- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3`）: [7.00](./data-bookworm/int2017_rate1/AWS_Graviton_4_O3_001.txt) [6.85](./data-bookworm/int2017_rate1/AWS_Graviton_4_O3_002.txt)
- Ampere Altra @ 3.0 GHz Neoverse N1（`-O3`）: [4.41](./data-bookworm/int2017_rate1/Ampere_Altra_O3_001.txt)
- Hygon C86 7390（`-O3`）: [2.97](./data-bookworm/int2017_rate1/Hygon_C86_7390_O3_001.txt)
- IBM POWER8NVL @ 4.0 GHz POWER8（`-O3`）: [3.54](./data-bookworm/int2017_rate1/IBM_POWER8NVL_O3_001.txt)
- Intel Xeon 6981E Crestmont（`-O3`）: [4.48](./data-bookworm/int2017_rate1/Intel_Xeon_6981E_O3_001.txt)
- Intel Xeon 6982P-C @ 3.6 GHz Redwood Cove（`-O3`）: [6.68](./data-bookworm/int2017_rate1/Intel_Xeon_6982P-C_O3_001.txt)
- Intel Xeon D-2146NT @ 2.9 GHz Skylake（`-O3`）: [3.96](./data-bookworm/int2017_rate1/Intel_Xeon_D-2146NT_O3_001.txt)
- Intel Xeon E5-2603 v4 @ 1.7 GHz Broadwell（`-O3`）: [2.48](./data-bookworm/int2017_rate1/Intel_Xeon_E5-2603_v4_O3_001.txt)
- Intel Xeon E5-2680 v3 @ 3.3 GHz Haswell（`-O3`）: [4.01](./data-bookworm/int2017_rate1/Intel_Xeon_E5-2680_v3_O3_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3`）: [4.35](./data-bookworm/int2017_rate1/Intel_Xeon_E5-2680_v4_O3_001.txt)
- Intel Xeon E5-4610 v2 @ 2.7 GHz Ivy Bridge EP（`-O3`）: [3.06](./data-bookworm/int2017_rate1/Intel_Xeon_E5-4610_v2_O3_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Sunny Cove（`-O3`）: [5.66](./data-bookworm/int2017_rate1/Intel_Xeon_Platinum_8358P_O3_001.txt)
- Intel Xeon Platinum 8576C Raptor Cove（`-O3`）: [5.72](./data-bookworm/int2017_rate1/Intel_Xeon_Platinum_8576C_O3_001.txt)
- Intel Xeon Platinum 8581C @ 3.4 GHz Raptor Cove（`-O3`）: [6.52](./data-bookworm/int2017_rate1/Intel_Xeon_Platinum_8581C_O3_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3`）: [3.10](./data-bookworm/int2017_rate1/Kunpeng_920_O3_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3`）: [5.53](./data-bookworm/int2017_rate1/Kunpeng_920_HuaweiCloud_kc2_O3_001.txt)
- T-Head Yitian 710 @ 3.0 GHz Neoverse N2（`-O3`）: [5.79](./data-bookworm/int2017_rate1/T-Head_Yitian_710_O3_001.txt)

#### HarmonyOS

桌面平台（LTO）：

- Huawei Kirin X90 E-Core @ 2.0 GHz（`-O3 -flto`）: [4.28](./data-harmonyos/int2017_rate1/Huawei_Kirin_X90_E-Core_O3-flto_001.txt)
- Huawei Kirin X90 P-Core @ 2.3 GHz（`-O3 -flto`）: [4.87](./data-harmonyos/int2017_rate1/Huawei_Kirin_X90_P-Core_O3-flto_001.txt)

手机平台（LTO）：

- Huawei Kirin 9010 E-Core Full @ 2.2 GHz（`-O3 -flto`）: [3.21](./data-harmonyos/int2017_rate1/Huawei_Kirin_9010_E-Core_Full_O3-flto_001.txt)
- Huawei Kirin 9010 P-Core Best @ 2.3 GHz（`-O3 -flto`）: [4.18](./data-harmonyos/int2017_rate1/Huawei_Kirin_9010_P-Core_Best_O3-flto_001.txt)
- Huawei Kirin 9010 P-Core Full @ 2.3 GHz（`-O3 -flto`）: [3.96](./data-harmonyos/int2017_rate1/Huawei_Kirin_9010_P-Core_Full_O3-flto_001.txt)

#### 备注

1. SPEC INT 2017 Rate-1 结果受 `-flto`（分数 +4%，主要优化 mcf/deepsjeng）和 `-ljemalloc`（分数 +4-10%，主要优化 omnetpp/xalancbmk）影响很明显。`-Ofast` 和 `-O3` 区别很小，`-march=native` 影响很小。
2. 在部分处理器上，Linux 不能保证程序被调度到性能最高的核心上，例如：
      1. Qualcomm X1E80100 上，负载不一定会调度到有 Boost 的核上，因此需要手动绑核。没有 Boost 的核心会跑在 3.4 GHz，Boost 的核心最高可以达到 4.0 GHz，对应 14% 的性能提升。具体地讲，它有三个 Cluster，0-3 是没有 Boost 的 Cluster，4-7 和 8-11 每个 Cluster 中可以有一个核心 Boost 到 4.0 GHz，也就是说，最多有两个核达到 4.0 GHz，这两个核需要分别位于 4-7 和 8-11 两个 Cluster 当中。如果一个 Cluster 有两个或者以上的核有负载，那么他们都只有 3.4 GHz。
      2. AMD Ryzen 9 9950X 不同核能够达到的最大频率不同，目前 Linux（6.11）的调度算法不一定可以保证跑到最大频率 5.75 GHz 上，可能会飘到频率低一些（5.45 GHz 左右）的核心上，损失 4% 的性能，因此需要绑核心，详见 [Linux 大小核的调度算法探究](../blog/posts/software/linux-core-scheduling.md) 以及 [谈谈 Linux 与 ITMT 调度器与多簇处理器](https://blog.hjc.im/thoughts-on-linux-preferred-cores-and-multi-ccx.html)。这个问题已经有 Patch 进行修复。
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

x86 平台的分支预测准确率（Average）由高到低（`-O3`，Debian Bookworm）：

1. Zen 5(AMD 9950X/AMD 9755/AMD 9K85): MPKI=4.48 Mispred=2.52%
2. Zen 5c(AMD 9K65): MPKI=4.51 Mispred=2.54%
3. Zen 4(AMD 9T24/9R14): MPKI=4.57 Mispred=2.57%
4. Zen 4c(AMD 9754): MPKI=4.66 Mispred=2.63%
5. Zen 4(AMD 7500F): MPKI=4.68 Mispred=2.64%
6. Zen 3(AMD 5700X): MPKI=4.68 Mispred=2.64%
7. Zen 2(AMD 7742): MPKI=4.77 Mispred=2.69%
8. Redwood Cove(Intel 6982P-C): MPKI=4.77 Mispred=2.71%
9. Sunny Cove(Intel 8358P)/Golden Cove(Intel 12900KS P-Core)/Raptor Cove(Intel 14900K P-Core/Intel 8581C): MPKI=4.86 Mispred=2.75%
10. Gracemont(Intel 12900KS P-Core/Intel 14900K P-Core): MPKI=5.15 Mispred=2.92%
11. Skylake(Intel D-2146NT)/Cascade Lake(Intel 10980XE): MPKI=5.50 Mispred=3.13%
12. Zen 1(AMD 7551): MPKI=5.82 Mispred=3.31%
13. Haswell(Intel E5-2680 v3)/Broadwell(Intel E5-2680 v4): MPKI=5.98 Mispred=3.34%

x86 平台的分支预测准确率（Average）由高到低（`-O3 -flto`，Debian Bookworm）：

1. Zen 5(AMD 9950X/AMD 9755): MPKI=5.35 Mispred=3.07%
2. Zen 5c(AMD 9K65)/Zen 5(AMD 9K85): MPKI=5.42 Mispred=3.10%
3. Zen 2(AMD 7742): MPKI=5.52 Mispred=3.17%
4. Zen 3(AMD 5700X): MPKI=5.55 Mispred=3.19%
5. Zen 4(AMD 9T24/AMD 9R14): MPKI=5.57 Mispred=3.19%
6. Redwood Cove(Intel 6982P-C): MPKI=5.70 Mispred=3.29%
7. Golden Cove(Intel 12900KS P-Core)/Raptor Cove(Intel 14900K P-Core/Intel 8581C): MPKI=5.81 Mispred=3.37%
8. Cascade Lake(Intel 10980XE): MPKI=6.55 Mispred=3.83%
9. Zen 1(AMD 7551): MPKI=6.86 Mispred=4.02%

ARM64 平台的分支预测准确率（Average）由高到低（`-O3`，Debian Bookworm）：

1. Neoverse V2(AWS Graviton 4): MPKI=4.50 Mispred=2.47%
2. Oryon(Qualcomm X1E80100): MPKI=4.71 Mispred=2.58%
3. Neoverse N2(Aliyun Yitian 710): MPKI=4.80 Mispred=2.64%
4. Firestorm(Apple M1 P-Core): MPKI=4.81 Mispred=2.62%
5. Neoverse V1(AWS Graviton 3/AWS Graviton 3E)/Cortex X1C(Qualcomm 8cx Gen3): MPKI=4.91 Mispred=2.69%
6. HuaweiCloud kc2: MPKI=5.17 Mispred=2.85%
7. Neoverse N1(Ampere Altra)/Cortex A78C(Qualcomm 8cx Gen3 E-Core): MPKI=5.21 Mispred=2.87%
8. Icestorm(Apple M1 E-Core): MPKI=5.41 Mispred=2.99%
9. TSV110(Hisilicon Kunpeng 920): MPKI=6.54 Mispred=3.58%

ARM64 平台的分支预测准确率（Average）由高到低（`-O3 -flto`，Debian Bookworm）：

1. Neoverse V2(AWS Graviton 4): MPKI=5.19 Mispred=3.03%
2. Oryon(Qualcomm X1E80100): MPKI=5.41 Mispred=3.13%
3. Firestorm(Apple M1 P-Core): MPKI=5.45 Mispred=3.14%
4. Neoverse V1(AWS Graviton 3): MPKI=5.64 Mispred=3.27%
5. HuaweiCloud kc2: MPKI=6.00 Mispred=3.50%
6. Icestorm(Apple M1 E-Core): MPKI=6.10 Mispred=3.56%
7. TSV110(Hisilicon Kunpeng 920): MPKI=6.74 Mispred=3.98%

LoongArch64 平台的分支预测准确率（Average）由高到低（`-O3`，Debian Trixie）：

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

- [GCC 11.3.0](./data-bookworm/others/SPEC_INT_2017_Intel_i9-14900K_O3_GCC_11.txt)
- [GCC 12.2.0](./data-bookworm/others/SPEC_INT_2017_Intel_i9-14900K_O3_GCC_12.txt)
- [GCC 13.3.0](./data-bookworm/others/SPEC_INT_2017_Intel_i9-14900K_O3_GCC_13.txt)
- [GCC 14.2.0](./data-bookworm/others/SPEC_INT_2017_Intel_i9-14900K_O3_GCC_14.txt)
- [GCC 15.1.0](./data-bookworm/others/SPEC_INT_2017_Intel_i9-14900K_O3_GCC_15.txt)
- [LLVM 19.1.4](./data-bookworm/others/SPEC_INT_2017_Intel_i9-14900K_O3_LLVM_19.txt)
- [LLVM 18.1.8](./data-bookworm/others/SPEC_INT_2017_Intel_i9-14900K_O3_LLVM_18.txt)
- [LLVM 17.0.6](./data-bookworm/others/SPEC_INT_2017_Intel_i9-14900K_O3_LLVM_17.txt)
- [LLVM 20.1.5](./data-bookworm/others/SPEC_INT_2017_Intel_i9-14900K_O3_LLVM_20.txt)

LLVM 20 的 548.exchange2_r 性能下降可以通过添加 `-fwrapv` 选项来解决，见 [548.exchange2_r of SPEC CPU 2017 has 30% performance regression between LLVM 18/19 and LLVM 20 on amd64](https://github.com/llvm/llvm-project/issues/139274)：

- [LLVM 20.1.5 with -fwrapv](./data-bookworm/others/SPEC_INT_2017_Intel_i9-14900K_O3_LLVM_20_fwrapv.txt)

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

- [3C6000 GCC 15.1.0 -O3 -msimd=lasx -flto -ljemalloc: 4.92, 2.24/GHz](./data-bookworm/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3-msimd=lasx-flto-ljemalloc.txt)
- [3C6000 GCC 15.1.0 -O3 -flto -ljemalloc: 4.90, 2.23/GHz](./data-bookworm/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3-flto-ljemalloc.txt)
- [3A6000 GCC 14.2.0 -O3 -flto -ljemalloc: 4.86, 1.94/GHz](./data-trixie/int2017_rate1/Loongson_3A6000_O3-flto-ljemalloc_001.txt)
- [3C6000 GCC 15.1.0 -O3 -march=native -flto -ljemalloc: 4.82, 2.20/GHz](./data-bookworm/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3-march=native-flto-ljemalloc.txt)
- [3C6000 GCC 15.1.0 -O3 -flto: 4.67, 2.12/GHz](./data-bookworm/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3-flto.txt)
- [3A6000 GCC 14.2.0 -O3 -flto: 4.56, 1.82/GHz](./data-trixie/int2017_rate1/Loongson_3A6000_O3-flto_001.txt)
- [3C6000 GCC 14.2.0 -O3 -flto -ljemalloc: 4.54, 2.06/GHz](./data-trixie/int2017_rate1/Loongson_3C6000_O3-flto-ljemalloc_001.txt)
- [3C6000 GCC 15.1.0 -O3: 4.49, 2.04/GHz](./data-bookworm/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3.txt)
- [3C6000 GCC 15.1.0 -O3 -march=la464: 4.49, 2.04/GHz](./data-bookworm/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3-march=la464.txt)
- [3C6000 GCC 15.1.0 -O3 -march=la664: 4.40, 2.04/GHz](./data-bookworm/others/SPEC_INT_2017_Loongson_3C6000_O3_GCC_15_O3-march=la664.txt)
- [3C6000 GCC 14.2.0 -O3 -flto: 4.39, 2.00/GHz](./data-trixie/int2017_rate1/Loongson_3C6000_O3-flto_001.txt)
- [3A6000 GCC 14.2.0 -O3: 4.35, 1.74/GHz](./data-trixie/int2017_rate1/Loongson_3A6000_O3_001.txt)
- [3C6000 GCC 14.2.0 -O3: 4.19, 1.90/GHz](./data-trixie/int2017_rate1/Loongson_3C6000_O3_001.txt)

注：3A6000 频率是 2.5 GHz，3C6000 频率是 2.2 GHz。

结论：性能受编译器版本和编译选项影响很大，如果对不上，那么性能的差距可能会影响和其他处理器比较的结论。在上面的例子里，这些编译器版本和编译选项带来的优化：

1. `-flto`：约 5% 提升，`4.39/4.19=1.05`, `4.56/4.35=1.05`
2. `-march=native`（仅 GCC 14）或 `-msimd=lasx`: 约 8% 提升，`4.50/4.17=1.08`
3. GCC 15.1.0 vs GCC 14.2.0: 约 7% 提升，`4.49/4.19=1.07`
3. `-ljemalloc`: 约 3-7% 提升，`4.90/4.63=1.06`, `4.86/4.56=1.07`, `4.54/4.39=1.03`

## SPEC FP 2017 Rate-1

下面贴出自己测的数据（SPECfp2017，Estimated，rate，base，1 copy），不保证满足 SPEC 的要求，仅供参考。总运行时间基本和分数成反比，乘积按 1e5 估算。

### 数据总览

#### Debian Bookworm

![](./data-bookworm/fp2017_rate1_score.svg)

![](./data-bookworm/fp2017_rate1_table.svg)

??? note "分数/GHz"

    ![](./data-bookworm/fp2017_rate1_score_per_ghz.svg)

??? note "每项分数"

    ![](./data-bookworm/fp2017_rate1_ratio.svg)

??? note "IPC"

    ![](./data-bookworm/fp2017_rate1_ipc.svg)

??? note "分支预测 MPKI"

    ![](./data-bookworm/fp2017_rate1_mpki.svg)

??? note "分支预测错误率"

    ![](./data-bookworm/fp2017_rate1_mispred.svg)

??? note "频率"

    ![](./data-bookworm/fp2017_rate1_freq.svg)

??? note "指令数"

    ![](./data-bookworm/fp2017_rate1_inst.svg)

#### Debian Trixie

![](./data-trixie/fp2017_rate1_score.svg)

![](./data-trixie/fp2017_rate1_table.svg)

??? note "分数/GHz"

    ![](./data-trixie/fp2017_rate1_score_per_ghz.svg)

??? note "每项分数"

    ![](./data-trixie/fp2017_rate1_ratio.svg)

??? note "IPC"

    ![](./data-trixie/fp2017_rate1_ipc.svg)

??? note "分支预测 MPKI"

    ![](./data-trixie/fp2017_rate1_mpki.svg)

??? note "分支预测错误率"

    ![](./data-trixie/fp2017_rate1_mispred.svg)

??? note "频率"

    ![](./data-trixie/fp2017_rate1_freq.svg)

??? note "指令数"

    ![](./data-trixie/fp2017_rate1_inst.svg)

#### HarmonyOS

![](./data-harmonyos/fp2017_rate1_score.svg)

![](./data-harmonyos/fp2017_rate1_table.svg)

??? note "每项分数"

    ![](./data-trixie/fp2017_rate1_ratio.svg)

### 原始数据

#### Debian Trixie

桌面平台（`-march=native`）：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3 -march=native`）: [11.7](./data-trixie/fp2017_rate1/AMD_Ryzen_7_5700X_O3-march=native_001.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3 -march=native`）: [3.93](./data-trixie/fp2017_rate1/Apple_M1_E-Core_O3-march=native_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3 -march=native`）: [12.2](./data-trixie/fp2017_rate1/Apple_M1_P-Core_O3-march=native_001.txt)
- Intel Core i5-1135G7 @ 4.2 GHz Willow Cove（`-O3 -march=native`）: [9.93](./data-trixie/fp2017_rate1/Intel_Core_i5-1135G7_O3-march=native_001.txt)
- Intel Core i7-13700K E-Core @ 4.2 GHz Gracemont（`-O3 -march=native`）: [7.22](./data-trixie/fp2017_rate1/Intel_Core_i7-13700K_E-Core_O3-march=native_001.txt)
- Intel Core i7-13700K P-Core @ 5.2 GHz Raptor Cove（`-O3 -march=native`）: [15.0](./data-trixie/fp2017_rate1/Intel_Core_i7-13700K_P-Core_O3-march=native_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz (AVX-512 @ 4.0 GHz) Cascade Lake（`-O3 -march=native`）: [7.85](./data-trixie/fp2017_rate1/Intel_Core_i9-10980XE_O3-march=native_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3 -march=native`）: [7.23](./data-trixie/fp2017_rate1/Intel_Core_i9-12900KS_E-Core_O3-march=native_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3 -march=native`）: [15.4](./data-trixie/fp2017_rate1/Intel_Core_i9-12900KS_P-Core_O3-march=native_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3 -march=native`）: [7.70](./data-trixie/fp2017_rate1/Intel_Core_i9-14900K_E-Core_O3-march=native_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3 -march=native`）: [18.0](./data-trixie/fp2017_rate1/Intel_Core_i9-14900K_P-Core_O3-march=native_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3 -march=native`）: [11.9](./data-trixie/fp2017_rate1/Intel_Xeon_w9-3595X_O3-march=native_001.txt)
- Loongson 3A6000 @ 2.5 GHz LA664（`-O3 -march=native`）: [5.73](./data-trixie/fp2017_rate1/Loongson_3A6000_O3-march=native_001.txt)

桌面平台：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3`）: [10.9](./data-trixie/fp2017_rate1/AMD_Ryzen_7_5700X_O3_001.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3`）: [3.93](./data-trixie/fp2017_rate1/Apple_M1_E-Core_O3_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3`）: [12.2](./data-trixie/fp2017_rate1/Apple_M1_P-Core_O3_001.txt)
- Intel Core i5-1135G7 @ 4.2 GHz Willow Cove（`-O3`）: [9.04](./data-trixie/fp2017_rate1/Intel_Core_i5-1135G7_O3_001.txt)
- Intel Core i7-13700K E-Core @ 4.2 GHz Gracemont（`-O3`）: [6.93](./data-trixie/fp2017_rate1/Intel_Core_i7-13700K_E-Core_O3_001.txt)
- Intel Core i7-13700K P-Core @ 5.2 GHz Raptor Cove（`-O3`）: [14.0](./data-trixie/fp2017_rate1/Intel_Core_i7-13700K_P-Core_O3_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3`）: [7.24](./data-trixie/fp2017_rate1/Intel_Core_i9-10980XE_O3_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3`）: [6.97](./data-trixie/fp2017_rate1/Intel_Core_i9-12900KS_E-Core_O3_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3`）: [14.4](./data-trixie/fp2017_rate1/Intel_Core_i9-12900KS_P-Core_O3_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3`）: [7.42](./data-trixie/fp2017_rate1/Intel_Core_i9-14900K_E-Core_O3_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3`）: [16.8](./data-trixie/fp2017_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3`）: [11.0](./data-trixie/fp2017_rate1/Intel_Xeon_w9-3595X_O3_001.txt)
- Loongson 3A6000 @ 2.5 GHz LA664（`-O3`）: [5.56](./data-trixie/fp2017_rate1/Loongson_3A6000_O3_001.txt)

服务器平台（`-march=native`）：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3 -march=native`）: [4.42](./data-trixie/fp2017_rate1/AMD_EPYC_7551_O3-march=native_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3 -march=native`）: [7.96](./data-trixie/fp2017_rate1/AMD_EPYC_7742_O3-march=native_001.txt)
- AMD EPYC 9R45 @ 4.5 GHz Zen 5（`-O3 -march=native`）: [16.2](./data-trixie/fp2017_rate1/AMD_EPYC_9R45_O3-march=native_001.txt)
- AMD EPYC 9T95 @ 3.7 GHz Zen 5c（`-O3 -march=native`）: [13.9](./data-trixie/fp2017_rate1/AMD_EPYC_9T95_O3-march=native_001.txt)
- Google Axion C4A @ Neoverse V2（`-O3 -march=native`）: [10.8](./data-trixie/fp2017_rate1/Google_Axion_C4A_O3-march=native_001.txt)
- Google Axion N4A @ Neoverse N3（`-O3 -march=native`）: [8.94](./data-trixie/fp2017_rate1/Google_Axion_N4A_O3-march=native_001.txt)
- Intel Xeon 6975P-C @ 3.9 GHz Redwood Cove（`-O3 -march=native`）: [11.0](./data-trixie/fp2017_rate1/Intel_Xeon_6975P-C_O3-march=native_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3 -march=native`）: [5.58](./data-trixie/fp2017_rate1/Intel_Xeon_E5-2680_v4_O3-march=native_001.txt)
- Intel Xeon Gold 6430 @ 2.6 GHz Golden Cove（`-O3 -march=native`）: [7.64](./data-trixie/fp2017_rate1/Intel_Xeon_Gold_6430_O3-march=native_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Sunny Cove（`-O3 -march=native`）: [8.03](./data-trixie/fp2017_rate1/Intel_Xeon_Platinum_8358P_O3-march=native_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3 -march=native`）: [3.19](./data-trixie/fp2017_rate1/Kunpeng_920_O3-march=native_001.txt)
- Loongson 3C5000 @ 2.2 GHz LA464（`-O3 -march=native`）: [3.09](./data-trixie/fp2017_rate1/Loongson_3C5000_O3-march=native_001.txt)
- Loongson 3C6000 @ 2.2 GHz LA664（`-O3 -march=native`）: [4.93](./data-trixie/fp2017_rate1/Loongson_3C6000_O3-march=native_001.txt)

服务器平台：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3`）: [4.15](./data-trixie/fp2017_rate1/AMD_EPYC_7551_O3_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3`）: [7.37](./data-trixie/fp2017_rate1/AMD_EPYC_7742_O3_001.txt)
- AMD EPYC 9R45 @ 4.5 GHz Zen 5（`-O3`）: [14.5](./data-trixie/fp2017_rate1/AMD_EPYC_9R45_O3_001.txt)
- AMD EPYC 9T95 @ 3.7 GHz Zen 5c（`-O3`）: [12.5](./data-trixie/fp2017_rate1/AMD_EPYC_9T95_O3_001.txt)
- Google Axion C4A @ Neoverse V2（`-O3`）: [10.8](./data-trixie/fp2017_rate1/Google_Axion_C4A_O3_001.txt)
- Google Axion N4A @ Neoverse N3（`-O3`）: [9.18](./data-trixie/fp2017_rate1/Google_Axion_N4A_O3_001.txt)
- IBM POWER8 @ 3.2 GHz POWER8（`-O3`）: [3.47](./data-trixie/fp2017_rate1/IBM_POWER8_O3_001.txt)
- IBM POWER9 3.2 GHz @ 3.2 GHz POWER9（`-O3`）: [3.84](./data-trixie/fp2017_rate1/IBM_POWER9_3.2_GHz_O3_001.txt)
- IBM POWER9 3.8 GHz @ 3.2 GHz POWER9（`-O3`）: [4.75](./data-trixie/fp2017_rate1/IBM_POWER9_3.8_GHz_O3_001.txt)
- Intel Xeon 6975P-C @ 3.9 GHz Redwood Cove（`-O3`）: [10.3](./data-trixie/fp2017_rate1/Intel_Xeon_6975P-C_O3_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3`）: [5.49](./data-trixie/fp2017_rate1/Intel_Xeon_E5-2680_v4_O3_001.txt)
- Intel Xeon Gold 6430 @ 2.6 GHz Golden Cove（`-O3`）: [7.01](./data-trixie/fp2017_rate1/Intel_Xeon_Gold_6430_O3_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Sunny Cove（`-O3`）: [7.24](./data-trixie/fp2017_rate1/Intel_Xeon_Platinum_8358P_O3_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3`）: [3.17](./data-trixie/fp2017_rate1/Kunpeng_920_O3_001.txt)
- Loongson 3C5000 @ 2.2 GHz LA464（`-O3`）: [3.00](./data-trixie/fp2017_rate1/Loongson_3C5000_O3_001.txt)
- Loongson 3C6000 @ 2.2 GHz LA664（`-O3`）: [4.75](./data-trixie/fp2017_rate1/Loongson_3C6000_O3_001.txt) [4.77](./data-trixie/fp2017_rate1/Loongson_3C6000_O3_002.txt) [4.75](./data-trixie/fp2017_rate1/Loongson_3C6000_O3_003.txt)

#### Debian Bookworm

桌面平台（`-march=native`）：

- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3 -march=native`）: [11.4](./data-bookworm/fp2017_rate1/AMD_Ryzen_7_5700X_O3-march=native_001.txt)
- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3 -march=native`）: [17.6](./data-bookworm/fp2017_rate1/AMD_Ryzen_9_9950X_O3-march=native_001.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3 -march=native`）: [3.89](./data-bookworm/fp2017_rate1/Apple_M1_E-Core_O3-march=native_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3 -march=native`）: [11.6](./data-bookworm/fp2017_rate1/Apple_M1_P-Core_O3-march=native_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz (AVX-512 @ 4.0 GHz) Cascade Lake（`-O3 -march=native`）: [7.24](./data-bookworm/fp2017_rate1/Intel_Core_i9-10980XE_O3-march=native_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3 -march=native`）: [16.6](./data-bookworm/fp2017_rate1/Intel_Core_i9-14900K_P-Core_O3-march=native_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3 -march=native`）: [11.0](./data-bookworm/fp2017_rate1/Intel_Xeon_w9-3595X_O3-march=native_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3 -march=native`）: [14.4](./data-bookworm/fp2017_rate1/Qualcomm_X1E80100_O3-march=native_001.txt)

桌面平台：

- AMD Ryzen 5 7500F @ 5.0 GHz Zen 4（`-O3`）: [11.6](./data-bookworm/fp2017_rate1/AMD_Ryzen_5_7500F_O3_001.txt)
- AMD Ryzen 7 5700X @ 4.65 GHz Zen 3（`-O3`）: [9.91](./data-bookworm/fp2017_rate1/AMD_Ryzen_7_5700X_O3_001.txt)
- AMD Ryzen 9 9950X @ 5.7 GHz Zen 5（`-O3`）: [16.3](./data-bookworm/fp2017_rate1/AMD_Ryzen_9_9950X_O3_001.txt) [16.6](./data-bookworm/fp2017_rate1/AMD_Ryzen_9_9950X_O3_002.txt)
- Apple M1 E-Core @ 2.1 GHz Icestorm（`-O3`）: [3.89](./data-bookworm/fp2017_rate1/Apple_M1_E-Core_O3_001.txt)
- Apple M1 P-Core @ 3.2 GHz Firestorm（`-O3`）: [11.6](./data-bookworm/fp2017_rate1/Apple_M1_P-Core_O3_001.txt)
- Intel Core i9-10980XE @ 4.7 GHz Cascade Lake（`-O3`）: [6.91](./data-bookworm/fp2017_rate1/Intel_Core_i9-10980XE_O3_001.txt)
- Intel Core i9-12900KS E-Core @ 4.1 GHz Gracemont（`-O3`）: [6.90](./data-bookworm/fp2017_rate1/Intel_Core_i9-12900KS_E-Core_O3_001.txt)
- Intel Core i9-12900KS P-Core @ 5.5 GHz Golden Cove（`-O3`）: [14.3](./data-bookworm/fp2017_rate1/Intel_Core_i9-12900KS_P-Core_O3_001.txt)
- Intel Core i9-14900K E-Core @ 4.4 GHz Gracemont（`-O3`）: [7.31](./data-bookworm/fp2017_rate1/Intel_Core_i9-14900K_E-Core_O3_001.txt)
- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3`）: [16.1](./data-bookworm/fp2017_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt)
- Intel Xeon w9-3595X @ 4.5 GHz Golden Cove（`-O3`）: [10.6](./data-bookworm/fp2017_rate1/Intel_Xeon_w9-3595X_O3_001.txt)
- Qualcomm 8cx Gen3 E-Core @ 2.4 GHz Cortex-A78C（`-O3`）: [6.08](./data-bookworm/fp2017_rate1/Qualcomm_8cx_Gen3_E-Core_O3_001.txt)
- Qualcomm 8cx Gen3 P-Core @ 3.0 GHz Cortex-X1C（`-O3`）: [8.07](./data-bookworm/fp2017_rate1/Qualcomm_8cx_Gen3_P-Core_O3_001.txt)
- Qualcomm X1E80100 @ 4.0 GHz X Elite（`-O3`）: [14.4](./data-bookworm/fp2017_rate1/Qualcomm_X1E80100_O3_001.txt)

服务器平台（`-march=native`）：

- AMD EPYC 9754 @ 3.1 GHz Zen 4c（`-O3 -march=native`）: [8.42](./data-bookworm/fp2017_rate1/AMD_EPYC_9754_O3-march=native_001.txt)
- AMD EPYC 9755 @ 4.1 GHz Zen 5（`-O3 -march=native`）: [14.4](./data-bookworm/fp2017_rate1/AMD_EPYC_9755_O3-march=native_001.txt)
- AMD EPYC 9K65 @ 3.7 GHz Zen 5c（`-O3 -march=native`）: [12.7](./data-bookworm/fp2017_rate1/AMD_EPYC_9K65_O3-march=native_001.txt)
- AMD EPYC 9K85 @ 4.1 GHz Zen 5（`-O3 -march=native`）: [14.2](./data-bookworm/fp2017_rate1/AMD_EPYC_9K85_O3-march=native_001.txt)
- AMD EPYC 9R14 @ 3.7 GHz Zen 4（`-O3 -march=native`）: [10.1](./data-bookworm/fp2017_rate1/AMD_EPYC_9R14_O3-march=native_001.txt)
- AMD EPYC 9T24 @ 3.7 GHz Zen 4（`-O3 -march=native`）: [10.1](./data-bookworm/fp2017_rate1/AMD_EPYC_9T24_O3-march=native_001.txt)
- AWS Graviton 3 @ 2.6 GHz Neoverse V1（`-O3 -march=native`）: [7.73](./data-bookworm/fp2017_rate1/AWS_Graviton_3_O3-march=native_001.txt)
- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3 -march=native`）: [9.29](./data-bookworm/fp2017_rate1/AWS_Graviton_4_O3-march=native_001.txt) [9.35](./data-bookworm/fp2017_rate1/AWS_Graviton_4_O3-march=native_002.txt)
- Intel Xeon 6981E Crestmont（`-O3 -march=native`）: [4.77](./data-bookworm/fp2017_rate1/Intel_Xeon_6981E_O3-march=native_001.txt)
- Intel Xeon 6982P-C @ 3.6 GHz Redwood Cove（`-O3 -march=native`）: [9.50](./data-bookworm/fp2017_rate1/Intel_Xeon_6982P-C_O3-march=native_001.txt)
- Intel Xeon D-2146NT @ 2.9 GHz Skylake（`-O3 -march=native`）: [5.48](./data-bookworm/fp2017_rate1/Intel_Xeon_D-2146NT_O3-march=native_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Sunny Cove（`-O3 -march=native`）: [7.60](./data-bookworm/fp2017_rate1/Intel_Xeon_Platinum_8358P_O3-march=native_001.txt)
- Intel Xeon Platinum 8581C @ 3.4 GHz Raptor Cove（`-O3 -march=native`）: [8.60](./data-bookworm/fp2017_rate1/Intel_Xeon_Platinum_8581C_O3-march=native_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3 -march=native`）: [3.17](./data-bookworm/fp2017_rate1/Kunpeng_920_O3-march=native_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3 -march=native`）: [8.01](./data-bookworm/fp2017_rate1/Kunpeng_920_HuaweiCloud_kc2_O3-march=native_001.txt)

服务器平台：

- AMD EPYC 7551 @ 2.5 GHz Zen 1（`-O3`）: [4.05](./data-bookworm/fp2017_rate1/AMD_EPYC_7551_O3_001.txt)
- AMD EPYC 7742 @ 3.4 GHz Zen 2（`-O3`）: [7.12](./data-bookworm/fp2017_rate1/AMD_EPYC_7742_O3_001.txt)
- AMD EPYC 7H12 @ 3.3 GHz Zen 2（`-O3`）: [6.61](./data-bookworm/fp2017_rate1/AMD_EPYC_7H12_O3_001.txt)
- AMD EPYC 7K83 Zen 3（`-O3`）: [7.63](./data-bookworm/fp2017_rate1/AMD_EPYC_7K83_O3_001.txt)
- AMD EPYC 9754 @ 3.1 GHz Zen 4c（`-O3`）: [7.64](./data-bookworm/fp2017_rate1/AMD_EPYC_9754_O3_001.txt)
- AMD EPYC 9755 @ 4.1 GHz Zen 5（`-O3`）: [13.2](./data-bookworm/fp2017_rate1/AMD_EPYC_9755_O3_001.txt)
- AMD EPYC 9K65 @ 3.7 GHz Zen 5c（`-O3`）: [11.7](./data-bookworm/fp2017_rate1/AMD_EPYC_9K65_O3_001.txt)
- AMD EPYC 9K85 @ 4.1 GHz Zen 5（`-O3`）: [13.0](./data-bookworm/fp2017_rate1/AMD_EPYC_9K85_O3_001.txt)
- AMD EPYC 9R14 @ 3.7 GHz Zen 4（`-O3`）: [9.26](./data-bookworm/fp2017_rate1/AMD_EPYC_9R14_O3_001.txt)
- AMD EPYC 9T24 @ 3.7 GHz Zen 4（`-O3`）: [9.23](./data-bookworm/fp2017_rate1/AMD_EPYC_9T24_O3_001.txt)
- AWS Graviton 3 @ 2.6 GHz Neoverse V1（`-O3`）: [7.80](./data-bookworm/fp2017_rate1/AWS_Graviton_3_O3_001.txt)
- AWS Graviton 3E @ 2.6 GHz Neoverse V1（`-O3`）: [8.10](./data-bookworm/fp2017_rate1/AWS_Graviton_3E_O3_001.txt)
- AWS Graviton 4 @ 2.8 GHz Neoverse V2（`-O3`）: [9.36](./data-bookworm/fp2017_rate1/AWS_Graviton_4_O3_001.txt) [9.39](./data-bookworm/fp2017_rate1/AWS_Graviton_4_O3_002.txt)
- Ampere Altra @ 3.0 GHz Neoverse N1（`-O3`）: [5.26](./data-bookworm/fp2017_rate1/Ampere_Altra_O3_001.txt)
- Hygon C86 7390（`-O3`）: [3.95](./data-bookworm/fp2017_rate1/Hygon_C86_7390_O3_001.txt)
- IBM POWER8NVL @ 4.0 GHz POWER8（`-O3`）: [4.10](./data-bookworm/fp2017_rate1/IBM_POWER8NVL_O3_001.txt)
- Intel Xeon 6981E Crestmont（`-O3`）: [4.80](./data-bookworm/fp2017_rate1/Intel_Xeon_6981E_O3_001.txt)
- Intel Xeon 6982P-C @ 3.6 GHz Redwood Cove（`-O3`）: [9.50](./data-bookworm/fp2017_rate1/Intel_Xeon_6982P-C_O3_001.txt)
- Intel Xeon D-2146NT @ 2.9 GHz Skylake（`-O3`）: [5.00](./data-bookworm/fp2017_rate1/Intel_Xeon_D-2146NT_O3_001.txt)
- Intel Xeon E5-2603 v4 @ 1.7 GHz Broadwell（`-O3`）: [3.14](./data-bookworm/fp2017_rate1/Intel_Xeon_E5-2603_v4_O3_001.txt)
- Intel Xeon E5-2680 v3 @ 3.3 GHz Haswell（`-O3`）: [5.15](./data-bookworm/fp2017_rate1/Intel_Xeon_E5-2680_v3_O3_001.txt)
- Intel Xeon E5-2680 v4 @ 3.3 GHz Broadwell（`-O3`）: [5.44](./data-bookworm/fp2017_rate1/Intel_Xeon_E5-2680_v4_O3_001.txt)
- Intel Xeon E5-4610 v2 @ 2.7 GHz Ivy Bridge EP（`-O3`）: [3.74](./data-bookworm/fp2017_rate1/Intel_Xeon_E5-4610_v2_O3_001.txt)
- Intel Xeon Platinum 8358P @ 3.4 GHz Sunny Cove（`-O3`）: [7.12](./data-bookworm/fp2017_rate1/Intel_Xeon_Platinum_8358P_O3_001.txt)
- Intel Xeon Platinum 8576C Raptor Cove（`-O3`）: [8.14](./data-bookworm/fp2017_rate1/Intel_Xeon_Platinum_8576C_O3_001.txt)
- Intel Xeon Platinum 8581C @ 3.4 GHz Raptor Cove（`-O3`）: [8.42](./data-bookworm/fp2017_rate1/Intel_Xeon_Platinum_8581C_O3_001.txt)
- Kunpeng 920 @ 2.6 GHz TaiShan V110（`-O3`）: [3.13](./data-bookworm/fp2017_rate1/Kunpeng_920_O3_001.txt)
- Kunpeng 920 HuaweiCloud kc2 @ 2.9 GHz（`-O3`）: [8.17](./data-bookworm/fp2017_rate1/Kunpeng_920_HuaweiCloud_kc2_O3_001.txt)
- T-Head Yitian 710 @ 3.0 GHz Neoverse N2（`-O3`）: [7.63](./data-bookworm/fp2017_rate1/T-Head_Yitian_710_O3_001.txt)

#### HarmonyOS

桌面平台（LTO）：

- Huawei Kirin X90 E-Core @ 2.0 GHz（`-O3 -flto`）: [6.52](./data-harmonyos/fp2017_rate1/Huawei_Kirin_X90_E-Core_O3-flto_001.txt)
- Huawei Kirin X90 P-Core @ 2.3 GHz（`-O3 -flto`）: [7.42](./data-harmonyos/fp2017_rate1/Huawei_Kirin_X90_P-Core_O3-flto_001.txt)

手机平台（LTO）：

- Huawei Kirin 9010 E-Core Full @ 2.2 GHz（`-O3 -flto`）: [4.72](./data-harmonyos/fp2017_rate1/Huawei_Kirin_9010_E-Core_Full_O3-flto_001.txt)
- Huawei Kirin 9010 P-Core Best @ 2.3 GHz（`-O3 -flto`）: [6.22](./data-harmonyos/fp2017_rate1/Huawei_Kirin_9010_P-Core_Best_O3-flto_001.txt)
- Huawei Kirin 9010 P-Core Full @ 2.3 GHz（`-O3 -flto`）: [5.86](./data-harmonyos/fp2017_rate1/Huawei_Kirin_9010_P-Core_Full_O3-flto_001.txt)

#### 备注

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

- [GCC 12.2.0](./data-bookworm/others/SPEC_FP_2017_Intel_i9-14900K_O3_GCC_12.txt)
- [LLVM 18.1.8](./data-bookworm/others/SPEC_FP_2017_Intel_i9-14900K_O3_LLVM_18.txt)
- [LLVM 19.1.4](./data-bookworm/others/SPEC_FP_2017_Intel_i9-14900K_O3_LLVM_19.txt)
- [LLVM 20.1.5](./data-bookworm/others/SPEC_FP_2017_Intel_i9-14900K_O3_LLVM_20.txt)

注：GCC 指 GCC + GFortran，LLVM 指 Clang + Flang-new