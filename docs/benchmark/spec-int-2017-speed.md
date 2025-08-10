# SPEC INT 2017 Speed

下面贴出自己测的数据（SPECint2017，Estimated，speed，base，单线程），不保证满足 SPEC 的要求，仅供参考。

运行时间基本和分数成反比，乘积按 1e5 估算。

- Intel Core i9-14900K Raptor Cove（`-O3`）: [12.1](./data/int2017_speed/Intel_Core_i9-14900K_O3_001.txt)
- Intel Core i9-12900KS Golden Cove（`-O3`）: [10.5](./data/int2017_speed/Intel_Core_i9-12900KS_O3_001.txt) [10.9](./data/int2017_speed/Intel_Core_i9-12900KS_O3_002.txt)
- Qualcomm X1E80100 X Elite（`-O3`）: [7.99](./data/int2017_speed/Qualcomm_X1E80100_O3_001.txt)
- Intel Core i9-10980XE Cascade Lake（`-O3`）: [7.18](./data/int2017_speed/Intel_Core_i9-10980XE_O3_001.txt)
- AMD EPYC 7742 Zen 2（`-O3`）: [5.55](./data/int2017_speed/AMD_EPYC_7742_O3_001.txt)
- Kunpeng 920 TaiShan V110（`-O3`）: [3.65](./data/int2017_speed/Kunpeng_920_O3_001.txt) [3.62](./data/int2017_speed/Kunpeng_920_O3_002.txt)

注：SPEC INT 2017 单线程 OpenMP 下 speed 测试按理说约等于 rate-1，前者虽然启用了 OpenMP，但仅允许单线程。不过实测下来还是不太一样。

