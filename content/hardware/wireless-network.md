---
layout: post
date: 2023-03-20 16:56:00 +0800
tags: [wireless,wifi,wlan,802.11]
category: system
title: 802.11 学习
---

## 背景

最近在学习 802.11，在博客上记录一下我的学习过程。

本文参考了 [802.11-1997](https://ieeexplore.ieee.org/document/654749) 并使用了标准中的图片。

## MAC 层帧格式

802.11 MAC 层的帧格式，如 802.11-1997 Figure 12：

![](/images/80211_mac.png)

前两个字节 Frame Control 的定义如 802.11-1997 Figure 13：

![](/images/80211_frame_control.png)

根据 Type 和 Subtype 字段决定了帧的类型，如管理（Management）帧，控制（Control）帧和数据（Data）帧。

无线路由器定期发送 Beacon frame，告诉客户端自己广播了哪些 SSID。客户端也可以主动发送 Probe Request frame 来询问有没有路由器有对应的 SSID，如果有，路由器回复一个 Probe Response frame。

## PHY

802.11 支持很多种 PHY，常见的有 802.11 b/g/n/ac/ax。

### 802.11b

首先看 [802.11b](https://ieeexplore.ieee.org/document/972833)，802.11b 是对 802.11 的补充，主要定义了第 18 章 `High Rate, direct sequence spread spectrum PHY specification`，缩写 HR-DSSS。

HR-DSSS 工作在 2.4 GHz 频段上，常用的是 13 个 channel，中心频率从 2412 MHz 到 2472 MHz 不等，呈等差数列，公差是 5 MHz。HR-DSSS 会占用 22MHz 的频谱，从中心频率减 11 MHz 到中心频率加 11 MHz，所以相邻 channel 会有干扰，见下图（取自 [Wikipedia](https://en.wikipedia.org/wiki/IEEE_802.11)）

![](/images/80211_channels.png)

这就是为什么通常会把 2.4GHz 无线路由器的 channel 固定为 1、6 或 11。

那么，HR-DSSS 如何把数据调制为 2.4GHz 上的信号呢？HR-DSSS 支持不同的速率，例如 1、2、5.5 和 11 Mbps，这些二进制的数据需要按照一定的方法调制到 2.4 GHz 的载波上。

首先是最简单的情况，例如在 channel 1 上传输 1 Mbps 的数据，802.11 采用的是 DSSS 的方法。简单来说，对于输入的每个位，扩展成 11 个 bit，这样就得到了一个 11 MHz 的基带信号，然后再把基带信号通过 DBPSK 调制到 2412 MHz 的载波信号上。

这个扩展过程是这样的：如果数据位是 0，那就输出 10110111000（Barker 码）；如果数据位是 1，那就输出 01001000111。实际上就是把 1 位的信息重复了 11 次再发出去，看起来很浪费，但很好地解决了干扰的问题，即使传输中出现了错误，接受方也很容易从 11 位的数据中恢复出原来的数据。

2 Mbps 的传输方式类似，只不过每个 symbol 传输两位的数据，所以采用 DQPSK 的调制方法，频率保持不变，实现了两倍的数据传输速率。

5.5 Mbps 和 11 Mbps 则采用了其他方法。由于上面的 1 比 11 的转换比例太浪费了，所以为了提升速度，5.5 Mbps 和 11 Mbps 时采用的是 CCK 编码方式，具体来说，5.5 Mbps 的时候，输入的 4 个 bit 会映射为 8 个 chip，类似地 11 Mbps 的时候，输入的 8 个 bit 也映射到 8 个 chip。每个 chip 都是复数，采用 DQPSK 进行调制。

可以看到，整个过程都是在冗余：速率低的时候，就冗余很多份；速率高的时候，冗余就比较少。实际上，5.5 Mbps 和 11 Mbps 还可以采用可选的 PBCC 进行编码，下面摘抄了 [About Data Modulation Format (802.11b/g DSSS/CCK/PBCC)](https://rfmw.em.keysight.com/wireless/helpfiles/89600b/webhelp/subsystems/wlan-dsss/content/dsss_about_datamodfmt.htm) 中 802.11b 不同速率和编码方式的表格：

| Data Modulation Formats | Spread Sequence Code scheme | Data Rate(Mbps) | Symbol Rate(Msps) | Chip Rate (Mcps) | Bits per Symbol | Modulation |
|-------------------------|-----------------------------|-----------------|-------------------|------------------|-----------------|------------|
| Barker 1                | 11 Chip Barker              |  1              |  1                | 11               | 1               | DBPSK      |
| Barker 2                | 11 Chip Barker              |  2              |  1                | 11               | 2               | DQPSK      |
| CCK 5.5                 | 8 chip CCK                  |  5.5            |  1.375            | 11               | 4               | DQPSK      |
| CCK 11                  | 8 chip CCK                  |  11             |  1.375            | 11               | 8               | DQPSK      |
| PBCC 5.5                | PBCC                        |  5.5            |  11               | N/A              | 0.5             | QPSK       |
| PBCC 11                 | PBCC                        |  11             |  11               | N/A              | 1               | QPSK       |
