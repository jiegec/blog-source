---
layout: page
date: 1970-01-01
permalink: /benchmark/
---

# 性能测试

## 测试环境

测试环境如下：

1. Debian Trixie 发布前的测试：Debian Bookworm, GCC 12.2.0
2. LoongArch 以及 Debian Trixie 发布后的测试：Debian Trixie, GCC 14.2.0
3. HarmonyOS NEXT 测试：HarmonyOS NEXT 5，Clang 15.0.4 + Flang 20.1.7，详见 [jiegec/SPECCPU2017Harmony](https://github.com/jiegec/SPECCPU2017Harmony/tree/master/results)；X90 带有 VM 的代表是在 Linux 虚拟机中测试
4. 此外有针对不同编译器和编译器版本对比的测试，相关测试结果都进行了标注

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

## 测试结果

要查看 SPEC CPU 不同版本以及测试项的测试结果，请点击对应链接：

- [SPEC CPU INT/FP 2026 Rate](./spec-cpu-2026-rate.md)
- [SPEC CPU INT/FP 2017 Rate](./spec-cpu-2017-rate.md)
- [SPEC CPU INT/FP 2017 Speed](./spec-cpu-2017-speed.md)
- [SPEC CPU INT/FP 2006 Rate/Speed](./spec-cpu-2006.md)

## SPEC 运行配置

### SPEC CPU 2006

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

### SPEC CPU 2017

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

此外，还需要注意 cpufreq governor（`cuupower frequency-info`），以及 boost 是否启用（`/sys/devices/system/cpu/cpufreq/boost`）。

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
- AMD EPYC 9R45(AWS m8a.xlarge, 4C 16G): Zen 5, Turin
- AMD EPYC 9T24(Aliyun g8a.xlarge, 4C 16G): Zen 4, Genoa
- AMD EPYC 9T95(Aliyun g9ae.xlarge, 4C 16G): Zen 5c, Turin Dense
- AMD Ryzen 5 7500F: Zen 4, Raphael
- AMD Ryzen 7 5700X: Zen 3, Vermeer
- AMD Ryzen 9 9950X: Zen 5, Granite Ridge
- AWS Gravition 3(AWS c7g.large, 2C 4G): Neoverse V1
- AWS Gravition 3E(AWS c7gn.medium, 1C 2G): Neoverse V1
- AWS Gravition 4(AWS c8g.large, 2C 4G): Neoverse V2
- Ampere Altra(Aliyun c6r.large, 2C 4G): Neoverse N1
- Apple M1: Firestorm + Icestorm
- Google Axion C4A(GCP c4a-standard-4, 4C 16G): Neoverse V2
- Google Axion N4A(GCP n4a-standard-4, 4C 16G): Neoverse N3
- Huawei Kirin 9010
- Hygon C86 7390(Aliyun g7h.large, 2C 8G): w/o PMU
- IBM POWER8NVL
- IBM POWER8(SMT8)
- IBM POWER9 3.2 GHz(SMT4, 4C16T)
- IBM POWER9 3.8 GHz(SMT4, 44C176T)
- Intel Core i5-1135G7: Willow Cove, Tiger Lake
- Intel Core i9-10980XE: Cascade Lake
- Intel Core i9-12900KS: Golden Cove + Gracemont, Alder Lake
- Intel Core i7-13700K: Raptor Cove + Gracemont, Raptor Lake
- Intel Core i9-14900K: Raptor Cove + Gracemont, Raptor Lake
- Intel Xeon 6975P-C(AWS m8i.xlarge, 4C 16G): Redwood Cove, Granite Rapids
- Intel Xeon 6981E(TencentCloud s9.large8, 4C 8G): Crestmont, Sierra Forest, w/o PMU
- Intel Xeon 6982P-C(Aliyun g9i.xlarge, 4C 16G): Redwood Cove, Granite Rapids
- Intel Xeon D-2146NT: Skylake
- Intel Xeon E5-2603 v4: Broadwell
- Intel Xeon E5-2680 v3: Haswell
- Intel Xeon E5-2680 v4: Broadwell
- Intel Xeon E5-4610 v2: Ivy Bridge EP
- Intel Xeon Gold 6430: Golden Cove, Sapphire Rapids
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

- 2026.05.02:
      - 测试 IBM POWER9 3.8 GHz (44C176T) 性能
      - 测试 Intel Core i5-1135G7 性能
- 2026.04.17:
      - 测试 Intel Core i7-13700K 性能
- 2026.02.23:
      - 测试 IBM POWER8 和 IBM POWER9 3.2 GHz (4C16T) 性能
- 2026.01.28:
      - 在 GCP n4a-standard-4 实例上测试 Google Axion N4A 的性能
      - 在 GCP c4a-standard-4 实例上测试 Google Axion C4A 的性能
      - 测试 Intel Xeon Platinum 8358P 的性能
- 2025.11.18:
      - 在 Aliyun g9ae.xlarge 实例上测试 AMD EPYC 9T95 的性能
- 2025.10.20:
      - 测试 Intel Xeon Gold 6430 的性能
- 2025.10.09:
      - 在 AWS m8i.xlarge 实例上测试 Intel Xeon 6975P-C 的性能
      - 在 AWS m8a.xlarge 实例上测试 AMD EPYC 9R45 的性能
      - 测试 Intel Core i9-12900KS 的性能
- 2025.08.10:
      - 开始在 Debian Trixie 上重复实验
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
