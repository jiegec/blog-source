---
layout: post
date: 2022-11-23
tags: [mellanox,mlnx,nvidia,infiniband,firmware]
category: hardware
title: 升级 Mellanox 网卡固件
---

## 背景

最近发现有一台机器，插上 ConnectX-4 IB 网卡后，内核模块可以识别到设备，但是无法使用，现象是 `ibstat` 等命令都看不到设备。降级 OFED 从 5.8 到 5.4 以后问题消失，所以认为可能是新的 OFED 与比较旧的固件版本有兼容性问题，所以尝试升级网卡固件。升级以后，问题就消失了。

## 安装 MFT

首先，在 https://network.nvidia.com/products/adapter-software/firmware-tools/ 下载 MFT，按照指示解压，安装后，启动 mst 服务，就可以使用 `mlxfwmanager` 得到网卡的型号以及固件版本：

```
Device Type: ConnectX4
Description: Mellanox ConnectX-4 Single Port EDR PCIE Adapter LP
PSID:        DEL2180110032
Versions:    Current
  FW         12.20.1820
```

## 升级固件

从 PSID 可以看到，这是 DELL OEM 版本的网卡，可以在 https://network.nvidia.com/support/firmware/dell/ 处寻找最新固件，注意需要保证 PSID 一致，可以找到这个 PSID 的 DELL 固件地址：https://www.mellanox.com/downloads/firmware/fw-ConnectX4-rel-12_28_4512-06W1HY_0JJN39_Ax-FlexBoot-3.6.203.bin.zip。

下载以后，解压，然后就可以升级固件：

```shell
mlxfwmanager -u -i fw-ConnectX4-rel-12_28_4512-06W1HY_0JJN39_Ax-FlexBoot-3.6.203.bin
```

升级以后重启就工作了。

考虑到类似的情况之后还可能发生，顺便还升级了其他几台机器的网卡，下面是一个例子：

```
Device Type: ConnectX4
Description: ConnectX-4 VPI adapter card; FDR IB (56Gb/s) and 40GbE; dual-port QSFP28; PCIe3.0 x8; ROHS R6
PSID:        MT_2170110021
Versions:    Current
  FW         12.25.1020
```

注意这里的 PSID 是 MT_ 开头，说明是官方版本。这个型号可以在 https://network.nvidia.com/support/firmware/connectx4ib/ 找到最新的固件，注意 PSID 要正确，可以找到固件下载地址 https://www.mellanox.com/downloads/firmware/fw-ConnectX4-rel-12_28_2006-MCX454A-FCA_Ax-UEFI-14.21.17-FlexBoot-3.6.102.bin.zip。用同样的方法更新即可。

还有一个 ConnectX-3 的例子：

```
Device Type: ConnectX3
Description: ConnectX-3 VPI adapter card; single-port QSFP; FDR IB (56Gb/s) and 40GigE; PCIe3.0 x8 8GT/s; RoHS R6
PSID:        MT_1100120019
Versions:    Current
  FW         2.36.5150
```

ConnectX-3 系列的网卡固件可以在 https://network.nvidia.com/support/firmware/connectx3ib/ 找，根据 PSID，可以找到固件下载地址是 http://www.mellanox.com/downloads/firmware/fw-ConnectX3-rel-2_42_5000-MCX353A-FCB_A2-A5-FlexBoot-3.4.752.bin.zip。

## 小结

如果遇到 Mellanox 网卡能识别 PCIe，但是不能使用，可以考虑降级 OFED 或者升级网卡固件。

可以用 mlxfwmanager 查看 PSID 和更新固件。根据 PSID，判断是 OEM（DELL）版本还是官方版本。如果是 OEM 版本，要到对应 OEM 的固件下载地址找，例如 https://network.nvidia.com/support/firmware/dell/；如果是官方版，在 https://network.nvidia.com/support/firmware/firmware-downloads/ 找。