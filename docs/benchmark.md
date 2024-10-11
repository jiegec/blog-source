---
layout: page
date: 1970-01-01
permalink: /benchmark/
---

# 性能测试

## SPEC INT 2006 Speed

因为 GCC 没有自动并行化，所以都是单核运行。运行时间基本和分数成反比，乘积按 400000 估算。

实测在 -Ofast 编译选项下，SPECfp 里的 gamess 和 bwaves 会失败，改成 -O3/-O2/-O1 以后 gamess 依然失败，只有不开 -O 或者 -O0 才能跑通 gamess。所以就不测 SPECfp 了，只测 SPECint。

下面贴出自己测的数据（SPECint2006，Estimated，speed，base），不保证满足 SPEC 的要求，仅供参考。

- i9-14900K Raptor Lake（`-O3`）: 91.9
- i9-14900K Raptor Lake（`-O2`）: 87.2
- i9-13900K Raptor Lake（`-Ofast -fomit-frame-pointer -march=native -mtune=native`）: 85.3 86.8
- i9-13900K Raptor Lake（`-O2`）: 79.6
- i9-12900KS Alder Lake（`-O2`）: 74.4
- i9-10980XE Cascade Lake（`-O2`）: 43.9
- E5-2680 v3 Haswell（`-O2`）: 33.2
- POWER8NVL（`-O2`）: 26.5
- Kunpeng 920 TaiShan V110（`-Ofast -fomit-frame-pointer -march=native -mtune=native`）: 24.5
- Kunpeng 920 TaiShan V110（`-O2`）: 23.3

### 网上的数据

只考虑单核，不考虑 ICC 的自动多线程并行化。

[Anandtech 的数据](https://www.anandtech.com/show/16084/intel-tiger-lake-review-deep-dive-core-11th-gen/8)：

- i9-10900K Comet Lake: 58.76
- R9 3950X Zen 2: 50.02
- R7 4800U Zen 2: 37.10
- Amazon Graviton 2 Neoverse-N1: 29.99

[Anandtech 的数据](https://www.anandtech.com/show/16252/mac-mini-apple-m1-tested/4)：

- Apple M1: 69.40
- R9 5950X Zen 3: 68.53
- Apple A14: 63.34
- i9-10900K Comet Lake: 58.58
- Apple A13: 52.83
- R9 3950X Zen 2: 50.10
- R7 2700X Zen+: 39.01

[Anandtech 的数据](https://www.anandtech.com/show/14694/amd-rome-epyc-2nd-gen/9)：

- EPYC 7742 Zen 2: 39.25
- EPYC 7601 Zen 1: 31.45

[Baikal 的数据](https://www.163.com/dy/article/IB0CL7PU0511838M.html):

- Baikal-S：19
- Kunpeng 920: 26

[龙芯 3A6000 新闻](https://www.ithome.com/0/709/460.htm)：

- Loongson 3A6000: 43.1

[龙芯 3A6000](https://www.bilibili.com/video/BV1am4y1x71V/):

- Loongson 3A6000: 43.1
- Intel Core i3-10100: 42.5
- Hygon 3250: 39
- Kirin 990: 26.4
- Zhaoxin KX6780A: 20.5
- Phytium FT-D2000: 15.4
- Pangu M900: 12.4

[在龙芯 3A5000 上测试 SPEC CPU 2006](https://zhuanlan.zhihu.com/p/393600027):

- Loongson 3A5000: 26.6

[龙芯、海光、飞腾、兆芯同桌对比性能力求公平](https://zhuanlan.zhihu.com/p/627627813):

- Intel i9-10850K: 62.5
- AMD R5 5600G: 48.2 59.9
- AMD R5 2600: 36.1 40.5
- Intel i5-6500: 40.1
- Hygon C86 3250: 30.5
- Loongson 3A5000HV: 26.5
- Zhaoxin KX-U6780A: 15.5
- Phytium D2000: 15.3


## SPEC INT 2006 Rate

### 网上的数据

[Kunpeng 920 官方数据](https://www.hisilicon.com/en/products/Kunpeng/Huawei-Kunpeng/Huawei-Kunpeng-920)：

- Kunpeng 920 64 Cores: >930

[夏晶的数据](https://www.zhihu.com/question/308299017/answer/592860614)：

- AMD Zen 2 64 Cores: ~1200
- Intel Skylake 8180 v5 28 Cores: ~750
- Cavium TX2 32 Cores: ~750
- AMD Zen 1 7601 32 Cores: ~700
- Qualcomm 2400 48 Cores: ~650
- Phytium FT2000 64 Cores: ~600
- Intel Skylake 6148 v5 20 Cores: ~550

[龙芯 3A6000 新闻](https://www.ithome.com/0/709/460.htm)：

- Loongson 3A6000 4C 8T: 155

[龙芯、海光、飞腾、兆芯同桌对比性能力求公平](https://zhuanlan.zhihu.com/p/627627813):

- Intel i9-10850K 10C 20T: 328 349
- AMD R5 5600G 6C 12T: 192 232 235 278
- AMD R5 2600 6C 12T: 166 179 192 199
- Hygon C86 3250 8C 16T: 173 197
- Intel i5-6500 4C: 113
- Phytium D2000 8C: 90.2
- Zhaoxin KX-U6780A 8C: 82.9
- Loongson 3A5000HV 4C: 81.2

## SPEC INT 2017 Speed/Rate-1

下面贴出自己测的数据（SPECint2017，Estimated，speed，base，单线程），不保证满足 SPEC 的要求，仅供参考。运行时间基本和分数成反比，乘积按 100000 估算。

- i9-14900K Raptor Lake（`-O3`）: 12.1
- i9-12900KS Alder Lake（`-O3`）: 10.5 10.9
- X1E-80-100 X Elite（`-O3`）: 7.99
- i9-10980XE Cascade Lake（`-O3`）: 7.18
- 7742 Zen 2（`-O3`）: 5.55
- Kunpeng 920 TaiShan V110（`-O3`）: 3.65 3.62

注：SPEC INT 2017 不开 OpenMP 单线程 speed 测试等价为 rate-1。

### 网上的数据

[SPEC CPU 2017 by David Huang](https://blog.hjc.im/spec-cpu-2017):

- 9950X: 12.6
- M3 Pro: 11.8
- 13900K: 11.5
- M2 Pro: 10.3
- M2: 9.95
- HX 370: 9.64
- 258V: 9.46
- M1 Max: 9.2
- 5950X: 9.15
- 3A6000: 4.29

[高通 X Elite Oryon 微架构评测：走走停停 by JamesAslan](https://zhuanlan.zhihu.com/p/704707254):

- 7700X: 10.35
- 13700K: 9.81
- 12700K: 9.13
- 5950X: 8.45
- M2: 8.40
- Oryon: 8.19
- M1: 7.40
- 8 Gen 2: 6.58

## SPEC FP 2017 Speed/Rate-1

下面贴出自己测的数据（SPECfp2017，Estimated，speed，base，单线程），不保证满足 SPEC 的要求，仅供参考。运行时间基本和分数成反比，乘积按 500000 估算。

- i9-14900K Raptor Lake（`-O3`）: 12.8
- i9-12900KS Alder Lake（`-O3`）: 13.1

注：SPEC FP 2017 不开 OpenMP 单线程 speed 测试等价为 rate-1。

### 网上的数据

[高通 X Elite Oryon 微架构评测：走走停停 by JamesAslan](https://zhuanlan.zhihu.com/p/704707254):

- 13700K: 14.56
- Oryon: 14.20
- 7700X: 13.97
- 12700K: 13.70
- M2: 12.64
- 5950X: 11.86
- M1: 11.20
- 8 Gen 2: 9.91

## SPEC 运行配置

SPEC 2006:

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

SPEC 2017:

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
%ifndef %{gcc_dir}
%define gcc_dir /usr
%endif

default:
   preENV_LD_LIBRARY_PATH  = %{gcc_dir}/lib64/:%{gcc_dir}/lib/:/lib64
   SPECLANG                = %{gcc_dir}/bin/
   CC                      = $(SPECLANG)gcc -std=c99
   CXX                     = $(SPECLANG)g++
   FC                      = $(SPECLANG)gfortran
   # How to say "Show me your version, please"
   CC_VERSION_OPTION       = -v
   CXX_VERSION_OPTION      = -v
   FC_VERSION_OPTION       = -v

# portability flags
default:
   EXTRA_PORTABILITY = -DSPEC_LP64
500.perlbench_r,600.perlbench_s:  #lang='C'
   PORTABILITY    = -DSPEC_LINUX_X64

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
   OPTIMIZE       = -O3
   # -std=c++13 required for https://www.spec.org/cpu2017/Docs/benchmarks/510.parest_r.html
   CXXOPTIMIZE    = -std=c++03
   # -fallow-argument-mismatch required for https://www.spec.org/cpu2017/Docs/benchmarks/521.wrf_r.html
   FOPTIMIZE      = -fallow-argument-mismatch

intrate,intspeed=base: # flags for integer base
   EXTRA_COPTIMIZE = -fno-strict-aliasing
   LDCFLAGS        = -z muldefs
# Notes about the above
#  - 500.perlbench_r/600.perlbench_s needs -fno-strict-aliasing.
#  - 502.gcc_r/602.gcc_s             needs -fgnu89-inline or -z muldefs
#  - For 'base', all benchmarks in a set must use the same options.
#  - Therefore, all base benchmarks get the above.  See:
#       www.spec.org/cpu2017/Docs/runrules.html#BaseFlags
#       www.spec.org/cpu2017/Docs/benchmarks/500.perlbench_r.html
#       www.spec.org/cpu2017/Docs/benchmarks/502.gcc_r.html
```

如果在 ARM64 上，把 -DSPEC_LINUX_X64 替换为 -DSPEC_LINUX_AARCH64，其余内容不变。

运行方式：

```shell
# int speed
cd /mnt && . ./shrc && runcpu intspeed
# fp speed
ulimit -s unlimited && cd /mnt && . ./shrc && runcpu fpspeed
```

## 固定频率方法

可以尝试用 cpupower frequency-set 来固定频率，但是一些平台不支持，还可能有 Linux 内无法关闭的 Boost。

对于 AMD CPU，在 Linux 下无法很好地固定 CPU 的频率，而是要去 BIOS 中进行设置。以 [ASUS 为例](https://dlcdnets.asus.com.cn/pub/ASUS/mb/13MANUAL/PRIME_PROART_TUF_GAMING_AMD_AM5_Series_BIOS_EM_WEB_EN.pdf?model=PRIME%20X670-P%20WIFI-CSM)，需要的设置如下：

1. 进入 Ai Tweaker Menu
2. 修改 CPU Core Ratio，把 Auto 改成需要的频率倍数（例如 BCLK 100MHz，要 4.3 GHz 那么 Ratio 就是 43）
3. 关闭 Core Performance Boost

进入 Linux 后，用 `cpupower frequency-info` 验证：`current CPU frequency: 4.29 GHz (asserted by call to kernel)` 是否和预期频率一致并且不变
