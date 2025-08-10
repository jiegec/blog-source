# SPEC INT 2006 Speed

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

