---
layout: post
date: 2019-06-02
tags: [router,fpga,router-on-fpga]
categories:
    - hardware
---

# 在 FPGA 上实现路由器（3）

## 前言

又半个月过去了，在写了上篇系列[博文](router-on-fpga-2.md)之后也是做了很多新的更改。上次做的主要是关于性能方面的提升，怎么提高频率，从而达到比较大的流量，而这段时间做的则是功能，做实现 RIP 协议和转发表的动态更新。

## 软件部分

软件部分目前是用 C 代码写的，用 Xilinx SDK 提供的各个 AXI 外设的驱动和 PS 自己的驱动，实现了所需要的，RIP 协议的处理，转发表的更新和统计信息的读取。

实际上做的时候比较粗暴，主要是通过三种 AXI 外设与硬件部分进行交互：AXI Stream FIFO，AXI GPIO 和 AXI BRAM Controller。其中 AXI Stream FIFO 是用来接收和发送需要 CPU 处理的以太网帧的，AXI GPIO 则是用来读取统计的信息，AXI BRAM Controller 是用来读写转发表的。最后在顶层设计中把这些外设连接起来。

## 硬件部分

硬件部分还是继续之前的部分往下写，添加了统计信息，直接暴露出去，让 CPU 走 AXI GPIO 读，因为不需要很高的精确度；转发表本身，一开始想的是自己写一些接口转换，后来发现，直接用 True Dual Port RAM 然后把一个 port 暴露给 AXI BRAM Controller 即可，免去了各种麻烦，PS 可以直接进行修改，不需要额外的工作。

## 最终效果

为了测试这套东西是否正常工作，就开了两个 Arch Linux 的虚拟机，分别 Bridge 到两个千兆的 USB 网卡上，都连到 FPGA 上。然后在两边都配上了 BIRD，配置 RIP 和一些路由，确实能更新硬件的转发表，并两边的 RIP 可以学习到对方的路由。

