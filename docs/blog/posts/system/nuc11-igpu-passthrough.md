---
layout: post
date: 2022-05-05
tags: [windows,win11,esxi,vmware,gpu,igpu,passthrough]
category: system
title: NUC11 ESXi 中 iGPU 直通虚拟机
---

## 背景

之前在 NUC11PAKi5 上装了 ESXI 加几个虚拟机系统，但是自带的 iGPU Intel Iris Xe Graphics(Tiger Lake GT-2) 没用上，感觉有些浪费。因此想要给 Windows 直通。在直通到 Windows 后发现会无限重启，最后直通到 Linux 中。

## 步骤

第一步是到 esxi 的设备设置的地方，把 iGPU 的 Passthrough 打开，这时候会提示需要重启，但是如果重启，会发现还是处于 Needs reboot 状态。网上进行搜索，发现是 ESXi 自己占用了 iGPU 的输出，[解决方法](https://williamlam.com/2020/06/passthrough-of-integrated-gpu-igpu-for-standard-intel-nuc.html)如下：

```shell
$ esxcli system settings kernel set -s vga -v FALSE
```

这样设置以后就不会在显卡输出上显示 dcui 了，这是一个比较大的缺点，但是平时也不用自带的显示输出，就无所谓了。

第二步，重启以后，这时候看设备状态就是 Active。回到 Windows 虚拟机，添加 PCI device，然后启动。这时候，我遇到了这样的错误：

```
Module ‘DevicePowerOn’ power on failed
Failed to register the device pciPassthru0
```

搜索了一番，[解决方法](https://shuttletitan.com/vsphere/pci-passthrough-module-devicepoweron-power-on-failed/)是关掉 IOMMU。在虚拟机设计中关掉 IOMMU，就可以正常启动了。

第三步，进入 Windows，这时候就可以看到有一个新的未知设备了，VID=8086，PID=9a49；等待一段时间，Windows 自动安装好了驱动，就可以正常识别了。GPU-Z 中可以看到效果如下：

![](/images/igpu-passthrough.png)

不过关机重启的时候会蓝屏，可能还有一些问题，有人在[论坛](https://community.intel.com/t5/Graphics/SR-IOV-support-for-intel-Iris-Xe-Graphics-on-i7-1165G7/td-p/1293264)上也说 passthrough 之后会蓝屏。这个问题一直没有解决。

再尝试 Passthrough 到 Linux：

```shell
$ sudo dmesg | grep i915
[    2.173500] i915 0000:13:00.0: enabling device (0000 -> 0003)
[    2.180137] i915 0000:13:00.0: [drm] VT-d active for gfx access
[    2.182109] i915 0000:13:00.0: BAR 6: can't assign [??? 0x00000000 flags 0x20000000] (bogus alignment)
[    2.182110] i915 0000:13:00.0: [drm] Failed to find VBIOS tables (VBT)
[    2.182541] i915 0000:13:00.0: vgaarb: changed VGA decodes: olddecodes=io+mem,decodes=none:owns=none
[    2.197374] i915 0000:13:00.0: firmware: direct-loading firmware i915/tgl_dmc_ver2_08.bin
[    2.198037] i915 0000:13:00.0: [drm] Finished loading DMC firmware i915/tgl_dmc_ver2_08.bin (v2.8)
[    3.401676] i915 0000:13:00.0: [drm] failed to retrieve link info, disabling eDP
[    3.515822] [drm] Initialized i915 1.6.0 20200917 for 0000:13:00.0 on minor 0
[    3.516054] i915 0000:13:00.0: [drm] Cannot find any crtc or sizes
[    3.516144] i915 0000:13:00.0: [drm] Cannot find any crtc or sizes
```

OpenCL 也可以检测到：

```shell
$ sudo apt install intel-opencl-icd clinfo
Number of devices                                 1
  Device Name                                     Intel(R) Graphics Gen12LP [0x9a49]
  Device Vendor                                   Intel(R) Corporation
  Device Vendor ID                                0x8086
  Device Version                                  OpenCL 3.0 NEO
  Device Numeric Version                          0xc00000 (3.0.0)
  Driver Version                                  1.0.0
```

Vulkan：

```shell
$ vulkaninfo
Group 1:
        Properties:
                physicalDevices: count = 1
                        Intel(R) Xe Graphics (TGL GT2) (ID: 0)
                subsetAllocation = 0

        Present Capabilities:
                Intel(R) Xe Graphics (TGL GT2) (ID: 0):
                        Can present images from the following devices: count = 1
                                Intel(R) Xe Graphics (TGL GT2) (ID: 0)
                Present modes: count = 1
                        DEVICE_GROUP_PRESENT_MODE_LOCAL_BIT_KHR
```

不过目前还没找到显示输出的方法，只能用 VMware SVGA 或者远程桌面。

## 吐槽

需要吐槽的是，11 代的核显不再支持 Intel GVT-g，而是提供了 SR-IOV 的虚拟化。但是，Linux i915 驱动没有做相应的支持。

参考文档：

- [Passthrough of Integrated GPU (iGPU) for standard Intel NUC](https://williamlam.com/2020/06/passthrough-of-integrated-gpu-igpu-for-standard-intel-nuc.html)
- [PCI Passthrough – “Module ‘DevicePowerOn’ power on failed”](https://shuttletitan.com/vsphere/pci-passthrough-module-devicepoweron-power-on-failed/)