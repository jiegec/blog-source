---
layout: post
date: 2020-10-09 08:16:00 +0800
tags: [bmc,ipmi,power,ibm]
category: system
title: IBM Power S822LC(8335-GTB) BMC 升级
---

## 背景

最近拿到一台 IBM Power S822LC（8335-GTB） 机器的访问权限，这也是我第一次碰 ppc64le 指令集的服务器。然后发现，它的 BMC 版本比较老，我想连接 Remote Control 失败了，原因是 JViewer 不支持 macOS，我就想着能不能升级一下。

## 升级过程

首先，在网上找了一下文档，首先用 ipmitool 找一下机器型号：

```shell
$ sudo ipmitool fru print 3
 Chassis Type          : Unknown
 Chassis Part Number   : 8335-GTB
 Chassis Serial        : REDACTED
```

可以看到，这台机器是 8335-GTB 型号，按照这个型号在 [Fix Central](https://www.ibm.com/support/fixcentral) 上搜索，可以找到若干个版本的 firmware，其中最老的版本是 `OP8_v1.11_2.1`，对比了一下，和原来的版本一致：

```shell
$ sudo ipmitool fru print 47
 Product Name          : OpenPOWER Firmware
 Product Version       : IBM-garrison-ibm-OP8_v1.11_2.1
 Product Extra         :        op-build-da02863
 Product Extra         :        buildroot-81b8d98
 Product Extra         :        skiboot-5.3.6
 Product Extra         :        hostboot-1f6784d-3408af7
 Product Extra         :        linux-4.4.16-openpower1-bc83f92
 Product Extra         :        petitboot-v1.2.4-de6cda2
 Product Extra         :        garrison-xml-3db7b6e
 Product Extra         :        occ-69fb587
 Product Extra         :        hostboot-binar
```

于是，我下载了比较新的版本，一个 hpm 文件，然后在 BMC 网页上进行升级。第一次升级比较保守，选择了 2017年的版本：

```shell
$ sudo ipmitool fru print 47
Product Name          : OpenPOWER Firmware
 Product Version       : IBM-garrison-ibm-OP8_v1.12_2.72
 Product Extra         :        op-build-14a75d0
 Product Extra         :        buildroot-211bd05
 Product Extra         :        skiboot-5.4.3
 Product Extra         :        hostboot-2eb7706-69b1432
 Product Extra         :        linux-4.4.30-openpower1-084eb48
 Product Extra         :        petitboot-v1.3.2-d709207
 Product Extra         :        garrison-xml-19a5164
 Product Extra         :        occ-d7efe30-47b58cb
 Product Extra         :        hostb
```

这次升级比较顺利，没有遇到什么障碍。但是我发现，BMC 里面显示的 BIOS 版本和 hpm 对不上，它总是认为 BIOS 版本是落后的，需要更新，而 Firmware 部分（BOOT 和 APP）是更新后的版本。但 BIOS 版本和原来的版本也不一样。于是我重新升级了几次，都没有效果，怀疑是升级出了问题。后来仔细读文档才发现，确实是 BMC 软件的问题（[文档](https://ak-delivery04-mul.dhe.ibm.com/sar/CMA/SFA/08cu1/0/8335GTB_820.1923.20190613n.xhtml)）：

```
Note: BMC Dashboard shows an incorrect level for the BIOS caused by improper translation of the level subfields. The Bios number should reflect the PNOR level for the system of "IBM-garrison-ibm-OP8_v1.11_2.19". In this case, the BIOS version should be 1.11_2.19 but shows as 1.17.19 instead with the "11_2" converted into the "17".

The Firmware Revision for the BMC firmware shows correctly as "2.13.58".

Here is an example output of the Dashboard with an errant BIOS Version:

Dashboard gives the overall information about the status of the device and remote server.

Device Information

Firmware Revision: 2.13.58

Firmware Build Time: Oct 26 2016 11:40:55 CDT

BIOS Version: 1.17.19
```

一番捣鼓之后，不知道怎么了，BMC 就挂了，怎么访问都不通。只好物理断电，重新来过。按照同样的方法，升级到了 2019 年的版本：

```shell
 Product Name          : OpenPOWER Firmware
 Product Version       : IBM-garrison-OP8_v1.12_2.96
 Product Extra         :        op-build-v2.3-7-g99a6bc8
 Product Extra         :        buildroot-2019.02.1-16-ge01dcd0
 Product Extra         :        skiboot-v6.3.1
 Product Extra         :        hostboot-p8-c893515-pd6f049d
 Product Extra         :        occ-p8-a2856b7
 Product Extra         :        linux-5.0.7-openpower1-p8e31f00
 Product Extra         :        petitboot-v1.10.3
 Product Extra         :        machine-xml-c5c3
```

中途也遇到了几次奇怪的问题，多次通过 IPMI reset 之后就好了。

## 远程访问

但是，最新版的 BMC 固件中，JViewer 依然没有 macOS 支持。我也 SSH 进去确认了一下，确实没有对应的支持文件。只好在 Linux 机器上访问，安装 icedtea 以后，就可以打开 jnlp 文件，之后一切都很正常。

一个可能的替代方案：https://github.com/sciapp/nojava-ipmi-kvm