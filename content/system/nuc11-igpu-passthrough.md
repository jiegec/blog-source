---
layout: post
date: 2022-05-05 10:24:00 +0800
tags: [windows,win11,esxi,vmware,gpu,igpu,passthrough]
category: system
title: NUC11 ESXi 中 iGPU 直通 Windows
---

## 背景

之前在 NUC11PAKi5 上装了 ESXI 加几个虚拟机系统，但是自带的 iGPU Intel Iris Xe Graphics(Tiger Lake GT-2) 没用上，感觉有些浪费。因此想要给 Windows 直通。途中遇到了一些问题，最后都解决了。

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

![](/igpu.png)


参考文档：

- [Passthrough of Integrated GPU (iGPU) for standard Intel NUC](https://williamlam.com/2020/06/passthrough-of-integrated-gpu-igpu-for-standard-intel-nuc.html)
- [PCI Passthrough – “Module ‘DevicePowerOn’ power on failed”](https://shuttletitan.com/vsphere/pci-passthrough-module-devicepoweron-power-on-failed/)