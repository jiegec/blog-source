---
layout: post
date: 2021-03-08 00:03:00 +0800
tags: [pcb,lceda,schematic,footprint,circuit]
category: hardware
title: PCB 笔记
---

记录一下在学习画板子过程中学到的心得。

## 工具

目前使用过 [KiCad](https://kicad.org/) 和 [lceda](https://lceda.cn/)：

- KiCad: 开源软件，跨平台。
- lceda：在线编辑，不需要安装，和 lcsc 有深度集成。

项目 [jiegec/HT42B534USB2UART](https://github.com/jiegec/HT42B534USB2UART) 采用的是 KiCad 5 编写的。目前正在做的另一个项目采用 lceda

## 流程

1. 选择所需要使用的芯片，查找芯片的 datasheet。
2. 寻找采用了芯片的一些设计，特别是看 schematic。
3. 按照 datasheet 里面推荐的电路，或者是其他人的设计，画自己需要的 schematic。
4. 设置好各个元件的 footprint，然后转到 PCB 设计。
5. 在 PCB 里面布线，生成 Gerber 等文件。
6. 把 Gerber 给到生产商（比如 jlc），交付生产。
7. 如果是自己焊接，则需要购买元件，比如从 lcsc 购买。
8. 收到 PCB 和元件后，自己按照 BOM 和 schematic 焊接各个元件。

## 笔记

1. 对于一些连接很多元件的信号，比如 GND，可以留作铺铜解决。也就是说，先不管 GND，把其他所有的信号都接好以后，再在顶层铺铜；如果还是有没有连接上的 GND，可以通过过孔（Via）走到底层，在底层再铺一层铜。
2. 对于外部供电的 VCC 和 GND，在 KiCad 中需要用 PWR_FLAG 标记一下。
3. 在 KiCad 中设计 PCB 前，要把生产商的工艺参数设置好，不然画了也要重画。
4. lceda 在选择元件的时候，可以直接从 lcsc 里选择，这样可以保证封装和商品可以对得上，不需要手动进行匹配。
5. 如果要用 jlc 的 SMT 贴片，先在 [SMT 元件列表](https://www.jlc.com/portal/smtComponentList.html) 里搜索所需要的元件；推荐用基本库，如果用其他库，则要加钱；选好元件以后，用元件编号去 lceda 里搜索并添加到 schematic。
6. 对于涉及模拟信号的设计，比如音频，需要特别注意模拟信号的电和地都是单独的：`AVCC` 和 `AGND`。所以要特别注意 datasheet 里面不同的地的表示方法。最后，再用磁珠把 `VCC` 和 `AVCC`、`GND` 和 `AGND` 分别连接起来就可以了。可以参考 [DE2 板子中第 19 页的音频部分设计](https://wiki.bu.ost.ch/infoportal/_media/fpga/cyclone_iv/de2_115_schematic.pdf) 和 [Staying well grounded](https://www.analog.com/en/analog-dialogue/articles/staying-well-grounded.html)。
7. 在 schematic 里经常会出现在电源附近的电容，那么，在 PCB 中，也尽量把这些电容放在对应的电源的旁边。
8. 耳机插座里面，一般分三种组成部件：Tip，Ring，Sleeve。只有两段的是 TS，三段的是 TRS，四段的是 TRRS。TS 是单声道，T 是声音，S 是地。TRS 是双声道，T 是左声道（或者单声道），R 是右声道，S 是地。TRRS 则是双声道加录音。一般来说，LINE IN 是双声道，MIC IN 是单声道，它们的阻抗也不同；LINE OUT 和 HEADPHONE OUT 都是双声道，但 HEADPHONE OUT 经过了额外的放大器。
9. 遇到一个 SPI 协议没有 `SPI_MISO` 引脚的芯片，可能说明它是 write-only 的。
10. 手焊的基本元件，一般用 0603 加一些 Padding 的封装；SMT 的话，则建议用 0402 封装。
11. I2C 的信号线一般需要加一个几 K 欧姆的上拉电阻到 VCC。

未完待续。