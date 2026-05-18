# SPEC CPU 2026 Rate

可通过[交互式图表](./viewer.html)查看和筛选本文的测试数据。

## SPEC INT 2026 Rate-1

下面贴出自己测的数据（SPECint2026，Estimated，rate，base，1 copy），不保证满足 SPEC 的要求，仅供参考。

### 原始数据

#### Debian Trixie

桌面平台：

- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3`）: [5.27](./data-trixie/int2026_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt)
桌面平台（LTO）：

- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3 -flto`）: [5.39](./data-trixie/int2026_rate1/Intel_Core_i9-14900K_P-Core_O3-flto_001.txt)
桌面平台（LTO + Jemalloc）：

- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3 -flto -ljemalloc`）: [5.63](./data-trixie/int2026_rate1/Intel_Core_i9-14900K_P-Core_O3-flto-ljemalloc_001.txt)


#### 备注

### 网上的数据

来自 SPEC 官网：

| Machine                                                                                             | Score | Compilation Flags                                                         |
|-----------------------------------------------------------------------------------------------------|-------|---------------------------------------------------------------------------|
| [Ampere eMAG 8180](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260210-00003.html)      | 1.00  | -O3 -ffast-math -mcpu=native -flto=16 -ljemalloc                          |
| [AMD Ryzen AI 9 HX 370](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260210-00018.html) | 5.00  | -O3 -ffast-math -march=native -flto=full                                  |
| [NVIDIA GB10](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260210-00020.html)           | 5.97  | -fuse-ld=lld -O3 -ffast-math -mcpu=native -flto=thin -fomit-frame-pointer |
| [Apple M5 Pro](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260422-00243.html)          | 7.64  | -O3                                                                       |

## SPEC FP 2026 Rate-1

下面贴出自己测的数据（SPECfp2026，Estimated，rate，base，1 copy），不保证满足 SPEC 的要求，仅供参考。

### 原始数据

#### Debian Trixie

桌面平台（`-march=native`）：

- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3 -march=native`）: [8.92](./data-trixie/fp2026_rate1/Intel_Core_i9-14900K_P-Core_O3-march=native_001.txt)

桌面平台：

- Intel Core i9-14900K P-Core @ 6.0 GHz Raptor Cove（`-O3`）: [7.02](./data-trixie/fp2026_rate1/Intel_Core_i9-14900K_P-Core_O3_001.txt)


#### 备注


### 网上的数据

来自 SPEC 官网：

| Machine                                                                                             | Score | Compilation Flags                                                         |
|-----------------------------------------------------------------------------------------------------|-------|---------------------------------------------------------------------------|
| [Ampere eMAG 8180](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260210-00001.html)      | 1.00  | -O3 -ffast-math -mcpu=native -flto=16 -ljemalloc                          |
| [AMD Ryzen AI 9 HX 370](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260210-00017.html) | 8.59  | -O3 -ffast-math -march=native -flto=full                                  |
| [NVIDIA GB10](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260210-00019.html)           | 9.70  | -fuse-ld=lld -O3 -ffast-math -mcpu=native -flto=thin -fomit-frame-pointer |
| [Apple M5 Pro](https://www.spec.org/cpu2026/results/res2026q2/cpu2026-20260422-00245.html)          | 10.9  | -O3                                                                       |
