# SPEC FP 2017 Speed

下面贴出自己测的数据（SPECfp2017，Estimated，speed，base，单线程），不保证满足 SPEC 的要求，仅供参考。

运行时间基本和分数成反比，乘积按 5e5 估算。

- Intel Core i9-14900K Raptor Cove（`-O3`）: [12.8](./data/fp2017_speed/Intel_Core_i9-14900K_O3_001.txt)
- Intel Core i9-12900KS Golden Cove（`-O3`）: [13.1](./data/fp2017_speed/Intel_Core_i9-12900KS_O3_001.txt)
- AMD EPYC 7742 Zen 2（`-O3`）: [6.99](./data/fp2017_speed/AMD_EPYC_7742_O3_001.txt)
- Intel Core i9-10980XE Cascade Lake（`-O3`）: [6.20](./data/fp2017_speed/Intel_Core_i9-10980XE_O3_001.txt)
- Kunpeng 920 TaiShan V110（`-O3`）: [2.57](./data/fp2017_speed/Kunpeng_920_O3_001.txt)

注：SPEC FP 2017 单线程 OpenMP 下 speed 测试不等价为 rate-1，因为跑的测试不同。

