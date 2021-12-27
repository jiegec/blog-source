---
layout: post
date: 2021-12-26 16:03:00 +0800
tags: [nvidia,cuda]
category: software
title: NVIDIA 驱动和 CUDA 版本信息速查
---

## 背景

之前和 NVIDIA 驱动和 CUDA 搏斗比较多，因此记录一下一些常用信息，方便查询。

## 常用地址

- [CUDA Toolkit Downloads](https://developer.nvidia.com/cuda-downloads?target_os=Linux)
- [NVIDIA Driver Installation Quickstart Guide](https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html)
- [NVIDIA Driver Downloads](https://www.nvidia.com/Download/index.aspx)
- [NVIDIA Docker Installation Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

## CUDA 版本与 NVIDIA 驱动兼容性

可以通过 apt show cuda-runtime-x-x 找到：

- cuda 11.5 >= 495
- cuda 11.4 >= 470
- cuda 11.3 >= 465
- cuda 11.2 >= 460
- cuda 11.1 >= 455
- cuda 11.0 >= 450
- cuda 10.2 >= 440
- cuda 10.1 >= 418
- cuda 10.0 >= 410
- cuda 9.2 >= 396
- cuda 9.1 >= 387
- cuda 9.0 >= 384

使用 nvidia-smi 看到的 CUDA 版本通常就是这个驱动对应的 CUDA 版本。

## CUDA 版本和 GCC 版本兼容性

可以在 cuda/include/crt/host_config.h 文件里找到：

- cuda 11.5: gcc <= 11
- cuda 11.4: gcc <= 10
- cuda 11.0: gcc <= 9
- cuda 10.2: gcc <= 8
- cuda 10.1: gcc <= 8
- cuda 10.0: gcc <= 7
- cuda 9.1: gcc <= 6

## CUDA 版本与显卡兼容性

编译选项与显卡对应关系 https://arnon.dk/matching-sm-architectures-arch-and-gencode-for-various-nvidia-cards/

可以在 nvcc --help 搜索 gpu-architecture 找到：

- cuda 11.4 sm_35 to sm_87
- cuda 11.3 sm_35 to sm_86
- cuda 11.0 sm_35 to sm_80
- cuda 10.0 sm_30 to sm_75
- cuda 9.1 sm_30 to sm_72
- cuda 9.0 sm_30 to sm_70

显卡的 Compute Capability 可以在 https://developer.nvidia.com/cuda-gpus 找到：

- A100: 80
- V100: 70
- P100: 60

## 升级 NVIDIA 驱动

升级后，需要 rmmod 已有的，再 modprobe 新的：

```bash
sudo rmmod nvidia_uvm nvidia_drm nvidia_modeset nvidia && sudo modprobe nvidia
```

如果发现 rmmod 失败，可以 `lsof /dev/nvidiactl` 查看谁在占用。DGX 上需要停止：

```bash
sudo systemctl stop nvsm.service
sudo systemctl stop nvidia-dcgm.service 
```