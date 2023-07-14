---
layout: post
date: 2021-12-06
tags: [cpu,manycore,intel,mic,a64fx]
categories:
    - hardware
---

# Manycore 处理器架构分析

## 参考文档

- [Intel® Many Integrated Core Architecture (Intel® MIC Architecture) - Advanced](https://www.intel.com/content/www/us/en/architecture-and-technology/many-integrated-core/intel-many-integrated-core-architecture.html)
- [Intel® Xeon Phi coprocessor (codename Knights Corner)](https://ieeexplore.ieee.org/abstract/document/7476487)
- [https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=7453080](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=7453080)
- [Knights Landing (KNL): 2nd Generation Intel® Xeon Phi™ Processor](https://www.alcf.anl.gov/files/HC27.25.710-Knights-Landing-Sodani-Intel.pdf)
- [Fujitsu A64FX](https://en.wikipedia.org/wiki/Fujitsu_A64FX)
- [Fujitsu Presents Post-K CPU Specifications](https://www.fujitsu.com/global/about/resources/news/press-releases/2018/0822-02.html)
- [Fujitsu High Performance CPU for the Post-K Computer](https://web.archive.org/web/20201205202434/https://hotchips.org/hc30/2conf/2.13_Fujitsu_HC30.Fujitsu.Yoshida.rev1.2.pdf)
- [SUPERCOMPUTER FUGAKU - SUPERCOMPUTER FUGAKU, A64FX 48C 2.2GHZ, TOFU INTERCONNECT D](https://www.top500.org/system/179807/)
- [Preliminary Performance Evaluation of the Fujitsu A64FX Using HPC Applications](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9229635)
- [FUJITSU Processor A64FX](https://www.fujitsu.com/downloads/SUPER/a64fx/a64fx_datasheet.pdf)
- [NVIDIA A100 Tensor Core GPU Architecture](https://images.nvidia.cn/aem-dam/en-zz/Solutions/data-center/nvidia-ampere-architecture-whitepaper.pdf)
- [NVIDIA TESLA V100 GPU ARCHITECTURE](https://images.nvidia.cn/content/volta-architecture/pdf/volta-architecture-whitepaper.pdf)
- [NVIDIA A100 TENSOR CORE GPU](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/nvidia-a100-datasheet-us-nvidia-1758950-r4-web.pdf)

## Xeon Phi - Intel MIC

MIC: Many Integrated Core Architecture

Knights Corner:

4 路 SMT，AVX512 指令，32 KB L1I，32 KB L1D，每核心 512KB L2，乱序执行，一条 512 位计算流水线，每个周期双精度性能 `512 / 64 * 2 = 16 FLOP/cycle`。61 核 1.053GHz 双精度性能是 `16 * 61 * 1.053 = 1028 GFLOPS`。

向量寄存器分为四组，每组 128 位，两个 DP/四个 SP。SP 和 DP 计算共享乘法器，来优化面积。

Knights Landing:

核心：4 路 SMT，AVX512 指令，乱序执行，两条 512 位计算流水线，每个周期双精度性能 `512 / 64 * 2 * 2 = 32 FLOP/cycle`，如果是 64 核 1.3 GHz，总双精度性能是 `32 * 64 * 1.3 = 2662 GFLOPS`。一共 36 个 Tile，每个 Tile 有 2 Core + 2 VPU/core + 1MB 16-way L2，最大 72 个核心。

内存：6-channel 384GB DDR4 2400 RAM（理论 `2400 * 6 * 8 = 115.2 GB/s`），8-16GB 3D MCDRAM（400+ GB/s）。

## Fujitsu A64FX

内存：4 组，每组 8GB HBM2，带宽 256 GB/s（`1024 bit * 2G`），总共 32GB HBM2，带宽 1TB/s。Cache Line 大小 256 B。

核心：4 个 NUMA Node（Core Memory Group），每个 NUMA Node 包括 12 计算核，有 8MB 16 路的 L2 Cache。总共 48 计算核，4 辅助核。

指令集：ARMv8.2+SVE，512 位向量宽度，乱序执行，两个浮点流水线和两个整数流水线，每个周期双精度性能 `512 / 64 * 2 * 2 = 32 FLOP/cycle`，主频 2.2 GHz，按主频算理论双精度浮点性能 `32 * 2.2 * 48 = 3.4 TFLOPS`。文档里写的是双精度浮点性能 2.7 TFLOPS，单精度 5.4 TFLOPS，半精度 10.8 TFLOPS，8 位整数 21.6 TOPS，应该是按照实际测出来的算。TOP 500 配置是 7630848 核，对应 `7630848 / 48 = 158976` 个节点，Rpeak 是 `537212 TFLOPS`，那么每个节点是 `537212 / 158976 = 3.38 TFLOPS`，和上面的 3.4 接近。Linpack 跑出来的 Rmax 是 442010 TFLOPS，每个节点是 `442010 / 158976 = 2.78 TFLOPS`，和文档里说的比较接近。

部分主要特性：

- Four-operand FMA: ARM FMA 指令只能是 `R0=R0+R1*R2`，A64FX 可以合并 `R0=R3,R0=R0+R1*R2` 两条为一条 `R0=R3+R1*R2` 指令
- Gather/Scatter: 非连续访存，同一个 128B 内连续的 lane 可以合并访问，如果数据有局部性的话，可以得到两倍带宽

## NVIDIA GPU

| 型号 | 工艺          | Peak DP(TFLOPS) | 功耗 (W) | 性能功耗比 (TFLOPS/W) |
| ---- | ------------- | --------------- | ------- | -------------------- |
| P100 | 16 nm FinFET+ | 4.7             | 250     | 0.019                |
| V100 | 12 nm FFN     | 7               | 250-300 | 0.023-0.028          |
| A100 | 7 nm N7       | 9.7             | 250-400 | 0.024-0.039          |

| 型号 | 内存容量 (GB) | 内存带宽 (GB/s) | 内存类型      | L2 缓存大小 | 寄存器堆大小 |
| ---- | ------------ | -------------- | ------------- | ----------- | ------------ |
| P100 | 12-16        | 549-732        | 4096 bit HBM2 | 4096 KB     | 14336 KB     |
| V100 | 16-32        | 900            | 4096 bit HBM2 | 6144 KB     | 20480 KB     |
| A100 | 40-80        | 1555-2039      | 5120 bit HBM2 | 40960 KB    | 27648 KB     |

| 型号 | SM 数量 | CUDA 核心数 | FP64 核心数 | SM 频率 (MHz) |
| ---- | ------- | ----------- | ----------- | ------------ |
| P100 | 56      | 3584        | 1792        | 1328         |
| V100 | 80      | 5120        | 2560        | 1380         |
| A100 | 108     | 6912        | 3456        | 1410         |

- CUDA 核心数 = SM 数量 * 64
- FP64 核心数 = SM 数量 * 32
- Peak DP = FP64 核心数 * SM 频率 * 2
- 寄存器堆大小 = SM 数量 * 256 KB