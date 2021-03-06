---
layout: post
date: 2020-12-27 08:46:00 +0800
tags: [ethernet,ieee,fiber,sfp,qsfp,gigabitethernet,rgmii,sgmii,qsgmii]
category: hardware
title: 以太网的物理接口
---

## 背景

最近逐渐接触到了一些高速的以太网的接口，被一大堆的名字搞得有点懵，所以特意学习了一下并整理成这篇博客。

更新：经 @z4yx 指出，还可以看[华为的介绍文档](https://support.huawei.com/hedex/hdx.do?docid=EDOC1100156553&id=ZH-CN_TOPIC_0250303640&lang=zh)

### 几几 BASE 杠什么是什么意思

在下文里，经常可以看到类似 100BASE-TX 这种写法，它表示的意思是：

1. BASE 前面的数字表示速率，比如 10，100，1000，10G等等
2. BASE 之后的第一个字母，常见的 T 表示双绞线，S 表示 850nm 光纤，L 表示 1310nm 光纤，C 表示同轴电缆
3. 之后可能还有别的字母，比如 X 表示 8b/10b 或者 4b/5b（FE） 的编码，R 表示 64b/66b 的编码
4. 之后可能还有别的数字，如果是 LAN PHY 表示的是所使用的 lane 数量；如果是 WAN PHY 表示的是传输的公里数

详见[Wikipedia - Ethernet Physical Layer # Naming Conventions](https://en.wikipedia.org/wiki/Ethernet_physical_layer#Naming_conventions)。

### 各个速率对应的英文单词是什么

- Fast Ethernet: 100Mbps
- Gigabit Ethernet: 1Gbps
- Multi Gigabit Ethernet: 2.5Gbps
- Ten Gigabit Ethernet: 10Gbps
- Forty Gigabit Ethernet: 40Gbps
- Hundred Gigabit Ethernet: 100Gbps

### 常见的连接器

连接器（connector）一般来说指的就是线缆和网络设备之间的物理接口了。常见的有：

- [8P8C](https://en.wikipedia.org/wiki/Modular_connector#8P8C)：一般我们会称之为 RJ45，关于它们俩的关系，可以看 Wikipedia 上面的说明，不过在日常生活中，这两个混用其实也没有什么大问题
- [LC](https://en.wikipedia.org/wiki/Optical_fiber_connector#LC)：一种光纤的接口，有两个突出来的插到 SFP 光模块中的突起，比较常见
- [SFP+ DAC](https://en.wikipedia.org/wiki/Twinaxial_cabling#SFP+_Direct-Attach_Copper_(10GSFP+Cu))：一般是 DAC（Direct Attatched Cable） 线，线的两端直接就是 SFP+ 的接口，直接插到 SFP+ 笼子中，不需要光模块；更高速率的也有 DAC 线

对于光纤的接口，注意购买的时候要和光模块对应，不然可能插不进去。常见的有 LC-LC，SC-LC，SC-SC 等等，表示线的两端分别是什么接口。

### MDI 和 MDI-X

这其实就是大家常见的 RJ45 里面 8 根线对应的信号，在十兆和百兆的时候，需要区分 MDI 和 MDI-X，在同种类型的端口之间用交叉线，在不同类型的端口之间用直通线。在后来，有了 Auto MDI-X，也就是会按照实际情况自动检测并且匹配。从千兆开始，设备都支持 Auto MDI-X 了，所以线本身是交叉还是直通就无所谓了。

### 各种 SFP

[SFP](https://en.wikipedia.org/wiki/Small_form-factor_pluggable_transceiver) 是很常见的，特别是在高速的网络之中。而它又分为几种，对应不同的速率：

- SFP：1Gbps/100Mbps
- SFP+：10Gbps
- SFP28：25Gbps
- SFP56：50Gbps
- QSFP：4Gbps
- QSFP+：40Gbps
- QSFP28: 100Gbps/50Gbps
- QSFP56：200Gbps
- QSFP-DD：400Gbps

可以看到，名字前面加了个 Q（Quad），速率就翻了 4 倍，同时物理接口的尺寸也变大了。所以，不带 Q 的 SFP 的物理尺寸都一样，带 Q 的 SFP 物理尺寸都一样大，但后者比前者大一些。

通常，网络设备也会支持把一个 QSFP 接口拆成多个 SFP 接口来使用，比如有的线，一边是 QSFP28，另一边是 4xSFP28，只要设备支持即可，目的是节省空间。

[SFP 标准](https://members.snia.org/document/dl/26184) 规定了 [20 根信号线](https://en.wikipedia.org/wiki/Small_form-factor_pluggable_transceiver#Signals)，正反面各 10 根，重要的是下面的这些（括号里写得是 Pin 的编号）：

1. Mod_ABS（6）：模块是否插入
2. RD+（13）、RD-（12）：接受数据的差分对
3. TD+（18）、TD-（19）：传输数据的差分对
4. SDA（4）、SCL（5）：模块的 I2C
5. Tx_Fault（2）、Tx_Disable（3）、Rx_LOS（8）：一些状态信号

可以看到，收和发各有一个差分对共 4 条数据线。相对应的，QSFP 收和发各有四对差分对共 16 条数据线，一共 38 根线。并且有一些信号是复用了同样的 pin，这样的设计可以节省一些 pin，是很常见的。

### MII

有时候，还会遇到各种 [MII](https://en.wikipedia.org/wiki/Media-independent_interface) 接口，也就是 MAC 和 PHY 之间的接口。有时候，还会伴随着 MDIO 接口，来进行控制信息的传输。它又分不同的类型：

- Standard MII：速率是 100Mbps（25MHz\*4）或者 10Mbps（2.5Mhz\*4），TX 7 根线，RX 7+2 根线，加上 MDIO 2 根线共 18 根线
- RMII：速率是 100Mbps 或者 10Mbps，频率都是 50MHz，一共 10 根线，数据线是 TX 和 RX 各 2 根
- GMII：速率是 1000Mbps（125MHz\*8），数据线是 TX 和 RX 各 8 根；也支持速率 100Mbps（25MHz）和 10Mbps（2.5MHz）
- RGMII：速率是 1000Mbps（125MHz\*4\*2，DDR），数据线是 TX 和 RX 各 4 根；也支持速率 100Mbps（25MHz\*4）和 10Mbps（2.5MHz\*4），一共是 5+5+2 根线
- SGMII：速率是 1000Mbps（625MHz\*2\*8/10），采用 625MHz DDR 差分对 SerDes，采用 8b/10b 的编码

有的时候，MAC 和 PHY 是独立的，比如很多常见的 FPGA 开发板，在使用千兆网的时候，在板子上是 PHY 芯片，从 FPGA 到 PHY 通过 RGMII 连接，然后 PHY 再连接到 8P8C（RJ45）的连接器上。一般还会把 MDIO 也接到 FPGA 上面。如果有多个 PHY，就会吧 MDIO 通过总线的方式合并起来，给每个 PHY 配置不同的地址（一般是在指定的 PIN 上设置上拉/下拉电阻实现），就可以保证不冲突的访问。

扩展阅读：[KXZ9031RNX Datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/00002117F.pdf)
