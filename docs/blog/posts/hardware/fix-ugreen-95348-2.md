---
layout: post
date: 2026-11-13
tags: [ugreen,hdmi,capture]
categories:
    - hardware
---

# 修复绿联 UG307-95348 HDMI 采集卡颜色问题（二）

## 背景

经过 [上文](./fix-ugreen-95348.md) 的一系列修复，绿联 95348 终于是可以正确地还原 MateBook Pro 输出的 RGB 色彩了。但是，换到另一台运行 Windows 的笔记本上时，又出现了新的颜色问题，这篇博客就来探讨一下怎么解决新的问题。

<!-- more -->

## 颜色问题

### 现象

用着之前打过 patch、关闭 luma processing 和 chroma processing 的固件，给一台 Windows 机器采集的时候，出现了新的问题，颜色出现了新的偏差：

- 0,0,0 -> 16,16,16
- 255,0,0 -> 237,14,15
- 0,255,0 -> 13,236,12
- 0,0,255 -> 15,15,238
- 255,255,255 -> 234,234,234

在显卡软件里，可以看到这组偏差对应的是 YCbCr，用的是 Limited range。经过验算，这就是把 Limited range 的 YCbCr 当 Full range 来解析，导致的问题。

??? note "验算过程"

    这五个颜色对应的 YCbCr（BT.709 limited）和按 full range 解码的结果是：

    | 输入 RGB | YCbCr（limited） | 按 full 解码 | 实测 |
    | --- | --- | --- | --- |
    | 0,0,0 | 16,128,128 | 16,16,16 | 16,16,16 |
    | 255,0,0 | 63,102,240 | 239,15,15 | 237,14,15 |
    | 0,255,0 | 173,42,26 | 12,237,13 | 13,236,12 |
    | 0,0,255 | 32,240,118 | 16,16,240 | 15,15,238 |
    | 255,255,255 | 235,128,128 | 235,235,235 | 234,234,234 |

    按 full range 解码的公式是：

    - `R = Y + 1.5748 (Cr - 128)`
    - `G = Y - 0.1873 (Cb - 128) - 0.4681 (Cr - 128)`
    - `B = Y + 1.8556 (Cb - 128)`

    以红色 255,0,0 为例，对应的 YCbCr 是 (63,102,240)，代入：

    - `R = 63 + 1.5748 × (240 - 128) = 239.4 → 239`
    - `G = 63 - 0.1873 × (102 - 128) - 0.4681 × (240 - 128) = 15.44 → 15`
    - `B = 63 + 1.8556 × (102 - 128) = 14.75 → 15`

    得到 239,15,15，实测是 237,14,15，只差 1~2 个 LSB。

    如果按 limited range 解码，公式则是：

    - `R = 1.164 (Y - 16) + 1.793 (Cr - 128)`
    - `G = 1.164 (Y - 16) - 0.213 (Cb - 128) - 0.533 (Cr - 128)`
    - `B = 1.164 (Y - 16) + 2.112 (Cb - 128)`

    代入红色：

    - `R = 1.164 × (63 - 16) + 1.793 × (240 - 128) = 255.5 → 255`
    - `G = 1.164 × (63 - 16) - 0.213 × (102 - 128) - 0.533 × (240 - 128) = 0.6 → 1`
    - `B = 1.164 × (63 - 16) + 2.112 × (102 - 128) = -0.2 → 0`

    得到 255,1,0，基本就是正确的 255,0,0（1 个 LSB 的差来自 YCbCr 量化）。所以采集卡确实把 limited 的 YCbCr 当 full 来解了。

如果用显卡软件切换到 RGB 4:4:4 Limited range：

- 0,0,0 -> 16,16,16
- 255,0,0 -> 232,16,16
- 0,255,0 -> 15,234,13
- 0,0,255 -> 15,16,234
- 255,255,255 -> 233,233,233

RGB 的 limited range 则是把 0~255 线性压到 16~235：

`v_lim = 16 + 219 * v / 255`

比如 255 会变成 `16 + 219 × 255 / 255 = 235`，0 会变成 16。要还原回 full，需要 `v = (v_lim - 16) * 255 / 219`；采集卡没有做这一步，而是直接把 16~235 当成 0~255 用，所以纯色分量停在 232~234（理论值 235，差值来自采集卡内部的转换和舍入），另外两个分量是 16。

这也是类似的问题，只有把颜色切换到 RGB 4:4:4 Full range 才可以正确采集。

虽然可以通过手动指定 RGB 4:4:4 Full range 模式来解决颜色问题，但如果没有装对应的软件呢？又或者像鸿蒙和 macOS（macOS 其实有[私有 API 可以用](http://github.com/jiegec/mac-displayctl)）那样没有类似的设置入口呢？

于是就要看，显卡驱动都是怎么判断要选择什么模式的。

### EDID

答案就在 EDID 里面。按照 CEA-861 标准，显示器通过 EDID 告诉显卡，它支持哪些颜色模式，比如是否支持 YCbCr 4:4:4 等等，又具体支持哪些分辨率，哪些时序。

然后显卡驱动挑选一个时序，让显卡按照一定的波形来把显示输出通过 HDMI 发送给显示器。此时发送的内容，就有颜色（RGB/YCbCr）以及范围（Full/Limited）之分。那这是怎么决定的呢？

首先，CEA-861 标准规定了一个默认值：对于 CE Timing，默认是 Limited；对于 IT Timing，默认是 Full。什么是 CE Timing 呢？CEA-861 的定义是，出现在标准的 Table 1 表格里，且 VIC 大于 1 的时序，都是 CE Timing。这些 VIC 可以在 [这里](https://jia.je/kb/hardware/cta_vic.html) 找到。那非 CE 的 Timing，就是 IT。

所以当显卡驱动选择了一个时序以后，就根据它是 CE 还是 IT 来决定默认是 Limited 还是 Full。但同时，显卡软件也允许用户自己选择颜色 range。那显示器是怎么知道显卡发送的到底是 Full range 还是 Limited range 呢？

答案是，HDMI 里有传递元数据的 AVI InfoFrame。它里面可以指定，RGB 用的是 Full range 还是 Limited range；YCbCr 用的是 Full range 还是 Limited range。当显示器看到这个信息的时候，就知道不该用默认值去解析了。

但是，并不是所有显示器都支持这个。所以，它还得先在 EDID 里通过 VCDB 来声明，它的 RGB 或 YCbCr，是否允许通过 AVI InfoFrame 指定 range。

## 解决方法

根据这些信息，就能想到解决方法了：把固件里的 EDID 换掉，全用 IT timing（比如用 CVT-RB），这样默认就是 Full range 了。这样确实工作了。

但是，实践中，又遇到了新问题：我的[使用场景](../misc/classroom-routing.md)里，采集卡和教室的投影仪通过一个 HDMI Splitter 连到电脑上，此时就得兼顾采集卡的情况，而采集卡用的是 CE Timing，比如 VIC 97。结果就是电脑通过 HDMI Splitter 这么一通接了以后，又回到 Limited range 了。

那怎么办呢？如果采集卡能自己识别输入是 Full range 还是 Limited range，然后进行相对应的处理就好了。

怎么识别呢？刚才提到，AVI InfoFrame 里会携带这个信息。所以就修改 EDID，在 VCDB 里设置 QS=1，这样 AVI InfoFrame 里就会出现指定 Full range 还是 Limited range 的信息。然后经过逆向，发现 MS2130S 会在寄存器 0x3c4a 里记录这个信息，这样就可以自动检测了。

怎么处理呢？之前，我的做法是在 OBS 里去 Apply LUT，实现 Limited range 到 Full 的反向映射。但是，如果从 Limited range 的输入切换到 Full range，就得调整 OBS，很麻烦。

于是我就想到，利用已有的 luma processing 和 chroma processing 的 pipeline。根据之前的分析，已知这两个 pipeline 做的事情是：

- luma processing：`clip(clip(Y + fc90) * fc91/128)`
- chroma processing：`clip(rotate(ΔR, ΔB) * fc92/128)`

如果想要实现 Limited range 到 Full range 的映射，也就是 16-235 线性映射到 0-255，只需要：

- 0xfc90 设为 0xf0，对应 -16
- 0xfc91 设为 0x95，对应 255/219
- 0xfc92 设为 0x95，同样对应 255/219
- 最后把 0xfc8f 和 0xfc8e 都设为 0x00，打开 processing pipeline

最终的结果是，在 YCbCr 上的变换，对应到 RGB 上，正好就是 Limited range 到 Full range 的映射。这样就不用改 OBS 的 Filter，也可以达到一样的效果。

上面这些逻辑，如果写到固件里，当然是最好的，但还得避免 UVC brightness 等设置把这些寄存器的值覆盖掉；不过固件毕竟不是源码，大范围的汇编改动还是比较危险。

最后的解决办法是，写了一个程序，通过 hidapi 去轮询 0x3c4a 寄存器，根据它是 Full range 还是 Limited range 来调整内部的寄存器，这样无论输入是哪种 range，都可以采集到正确的颜色了。此外，我还在 EDID 里把 YCbCr 都去掉了，只保留了 RGB 的支持，这样就只需要考虑一种转换。

这样，无论是 MateBookPro，还是跑了 Windows 的机器，都可以准确地采集了。当然，还有一个遗留问题，就是苹果电脑，它依然会出现偏色的问题，具体的原因还没能找到。
