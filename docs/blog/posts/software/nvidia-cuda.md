---
layout: post
date: 2021-12-26
tags: [nvidia,cuda]
categories:
    - software
---

# NVIDIA 驱动和 CUDA 版本信息速查

## 背景

之前和 NVIDIA 驱动和 CUDA 搏斗比较多，因此记录一下一些常用信息，方便查询。

## 常用地址

- [CUDA Toolkit Downloads](https://developer.nvidia.com/cuda-downloads?target_os=Linux)
- [CUDA Toolkit - Release Notes](https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html)
- [NVIDIA Driver Installation Quickstart Guide](https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html)
- [NVIDIA Driver Downloads](https://www.nvidia.com/Download/index.aspx)
- [NVIDIA Docker Installation Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

## CUDA 版本与 NVIDIA 驱动兼容性

可以通过 apt show cuda-runtime-x-x 找到：

- cuda 13.0 >= 580 (Release Notes: 580)
- cuda 12.6 >= 560 (Release Notes: 525)
- cuda 12.5 >= 555 (Release Notes: 525)
- cuda 12.4 >= 550 (Release Notes: 525)
- cuda 12.3 >= 545 (Release Notes: 525)
- cuda 12.2 >= 535 (Release Notes: 525)
- cuda 12.1 >= 530 (Release Notes: 525)
- cuda 12.0 >= 525 (Release Notes: 525)
- cuda 11.8 >= 520 (Release Notes: 450)
- cuda 11.7 >= 515 (Release Notes: 450)
- cuda 11.6 >= 510 (Release Notes: 450)
- cuda 11.5 >= 495 (Release Notes: 450)
- cuda 11.4 >= 470 (Release Notes: 450)
- cuda 11.3 >= 465 (Release Notes: 450)
- cuda 11.2 >= 460 (Release Notes: 450)
- cuda 11.1 >= 455 (Release Notes: 450)
- cuda 11.0 >= 450 (Release Notes: 450)
- cuda 10.2 >= 440
- cuda 10.1 >= 418
- cuda 10.0 >= 410
- cuda 9.2 >= 396
- cuda 9.1 >= 390
- cuda 9.0 >= 384

使用 nvidia-smi 看到的 CUDA 版本，通常就是这个驱动在上表里对应的 CUDA 版本，例如内核驱动版本是 470 的话，看到的 CUDA 版本就是 11.4。

实际上兼容的驱动版本会比 APT 宣称的更多一些：[官方文档](https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html) 里面写了 CUDA 11.x 可以兼容 NVIDIA >= 450，CUDA 12.x 可以兼容 NVIDIA >= 525，CUDA 13.x 可以兼容 NVIDIA >= 580。

## CUDA 版本和 GCC/Clang 版本兼容性

可以在 cuda/include/crt/host_config.h 文件里找到：

- cuda 13.0: gcc <= 15, 3.2 < clang < 21
- cuda 12.8: gcc <= 14, 3.2 < clang < 20
- cuda 12.6: gcc <= 13, 3.2 < clang < 19
- cuda 12.3: gcc <= 12, 3.2 < clang < 16
- cuda 12.1: gcc <= 12, 3.2 < clang < 16
- cuda 12.0: gcc <= 12, 3.2 < clang < 15
- cuda 11.8: gcc <= 11, 3.2 < clang < 15
- cuda 11.5: gcc <= 11
- cuda 11.4: gcc <= 10
- cuda 11.3: gcc <= 10, 3.2 < clang < 12
- cuda 11.1: gcc <= 10, 3.2 < clang < 11
- cuda 11.0: gcc <= 9, 3.2 < clang < 10
- cuda 10.2: gcc <= 8, 3.2 < clang < 9
- cuda 10.1: gcc <= 8, 3.2 < clang < 9
- cuda 10.0: gcc <= 7
- cuda 9.1: gcc <= 6

## CUDA 版本与显卡兼容性

编译选项与显卡对应关系 https://arnon.dk/matching-sm-architectures-arch-and-gencode-for-various-nvidia-cards/

可以在 `nvcc --help` 搜索 gpu-architecture 找到：

- cuda 12.8 sm_50 to sm_120a
- cuda 12.3 sm_50 to sm_90a
- cuda 12.1 sm_50 to sm_90a
- cuda 12.0 sm_50 to sm_90a
- cuda 11.8 sm_35 to sm_90
- cuda 11.4 sm_35 to sm_87
- cuda 11.3 sm_35 to sm_86
- cuda 11.1 sm_35 to sm_86
- cuda 11.0 sm_35 to sm_80
- cuda 10.2 sm_30 to sm_75
- cuda 10.0 sm_30 to sm_75
- cuda 9.1 sm_30 to sm_72
- cuda 9.0 sm_30 to sm_70

显卡的 Compute Capability 可以在 https://developer.nvidia.com/cuda-gpus 找到：

- RTX 5090: 120
- B200: 100
- H100: 90
- RTX 4090: 89
- RTX 3090: 86
- A100: 80
- RTX 2080: 75
- V100: 70
- P100: 60

## 升级 NVIDIA 驱动

升级后，需要 rmmod 已有的，再 modprobe 新的：

```bash
sudo rmmod nvidia_uvm nvidia_drm nvidia_modeset nvidia && sudo modprobe nvidia
```

如果发现 rmmod 失败，可以 `lsof /dev/nvidiactl` 查看谁在占用。DGX OS 上需要停止：

```bash
sudo systemctl stop nvsm.service
sudo systemctl stop nvidia-dcgm.service 
```

除了 `/dev/nvidia*` 可能被占用以外，还需要用 lsof 检查 `/dev/dri/render*`。
