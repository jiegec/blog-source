---
layout: post
date: 2023-08-10
tags: [loongson,loongarch,cpu,machine,diy]
draft: true
categories:
    - hardware
---

# 组装一台采用龙芯 3A6000 CPU 的主机

## 背景

最近买到了龙芯 3A6000 以及配套主板，在此记录我组装台式机的过程，以及在其上的体验。

<!-- more -->

## 购买

组装的第一步是购买各个配件，我买了如下的配件：

1. 主板 + CPU：Loongson-3A6000-7A2000-1w-V0.1-EVB，暂未正式上市
2. 内存：Kingston HyperX HX426C16FB3/8 8GB，169 元
3. 显卡: AMD RADEON RX550 4G 379 元
4. 无线网卡: Intel AX200 79 元
5. 硬盘：致态 TiPlus5000 Gen3 1TB，369 元
6. 机箱：爱国者 A15 ATX，100 元
7. 电源：爱国者 DK 系列 500W，149 元

除了主板和 CPU 以外总价一千出头。目前主板和 CPU 还没有正式上市，按照 3A5000 现在的价格的估计的话大概也是一千多，加起来整机不到三千。当然了，现在 3A6000 才刚出来，所以我买的价格也比较高，但自己组装也能省下来不少钱。

实际上这里电源买的偏大了，不过 400W 和 500W 也只差 20 块钱，就愉快地加价了。

### 内存兼容性

我测试的内存条：

1. Kingston HyperX HX426C16FB3/8：支持
2. Kingston HyperX KF432C16BB/8：支持
3. 金百达（KingBank）长鑫颗粒 DDR4 3200MHz 16GB U-DIMM 1.35V CL 16：不支持
4. 紫光 SCC16GP02H1F1C-26V：不支持

网上找到的 3A6000 支持的内存型号：

1. 三星 M393A4G43AB3-CWEGY
2. 紫光 SCC16GU03H2F1C-32AA
3. 紫光 SCE08GU04APA-32

网上找到的 3A5000 支持的内存型号：

1. 紫光 SCC08GU03H3F1C-32AA
2. 紫光 SCC16GU03H4F1C-32AA

注：兼容性随 UEFI 固件版本和硬件版本不同可能不同，因此读者遇到不同的兼容性情况也是可能的。我目前使用的 UEFI 固件版本是 Loongson-UDK2018-V4.0.05420-stable202302。

## 显卡兼容性

我测试的显卡：

1. AMD RX550：可用
2. AMD RX6400：不可用，见不到 BIOS 界面

## Linux 发行版

目前查到的支持 LoongArch 的发行版有：

- AOSC OS: 有 LiveCD，但是还没有 DeployKit，可以用解压 base tarball 的方法安装
- LoongArchLinux：有安装 CD，可用
- Gentoo：没有安装 CD，需要借别的发行版的环境来安装
- Debian：没有官方安装 CD，有第三方的安装 CD
- UOS：没试过
- openEuler：没试过
- Loongnix：没试过
- Anolis OS：没试过

既然买的盘比较大，就预留了多个系统分区的空间，然后保留一个大的数据分区。目前装了 AOSC OS。

## VSCode Remote

VSCode Remote Server 是闭源的，但是理论上可以用 lat 来对 nodejs 做二进制翻译。只需要魔改 `~/.vscode/extensions/ms-vscode-remote.remote-ssh-0.102.0/out/extension.js`（版本号可能不同），把里面对 x86_64 架构的判断，加上 loongarch64，也就是把 loongarch64 当成 x86_64 去处理，那么 VSCode Remote 就会下载 x86_64 的 binary 并运行，此时用 lat 就可以跑 server 了。

按照这个方法实践了一下：QEMU 还没支持 LASX 指令（有 [patch](https://patchew.org/search?q=project%3AQEMU+LASX) 但是还没有合并），所以跑的时候会 SIGILL。真机 3A6000 上会在 lat 里面失败，怀疑是内核版本问题。

此外，code-server 也是可以用的，安装 node v16 和 npm，然后运行 code-server 安装脚本即可。
