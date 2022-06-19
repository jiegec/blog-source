---
layout: post
date: 2022-06-19 17:05:00 +0800
tags: [wishbone,bus]
category: hardware
title: Wishbone 总线协议
---

## 背景

最近在研究如何把 Wishbone 总线协议引入计算机组成原理课程，因此趁此机会学习了一下 Wishbone 的协议。

## 总线

总线是什么？总线通常用于连接 CPU 和外设，为了更好的兼容性和可复用性，会想到能否设计一个统一的协议，其中 CPU 实现的是发起请求的一方（又称为 master），外设实现的是接收请求的一方（又称为 slave），那么如果要添加外设、或者替换 CPU 实现，都会变得比较简单，减少了许多适配的工作量。

那么，我们来思考一下，一个总线协议需要包括哪些内容？对于 CPU 来说，程序会读写内存，读写内存就需要以下几个信号传输到内存：

1. 地址（`addr`）：例如 32 位处理器就是 32 位地址，或者按照内存的大小计算地址线的宽度
2. 数据（`w_data` 和 `r_data`）：分别是写数据和读数据，宽度通常为 32 位 或 64 位，也就是一个时钟周期可以传输的数据量
3. 读还是写（`we`）：高表示写，低表示读
4. 字节有效（`be`）：例如为了实现单字节写，虽然 `w_data` 可能是 32 位宽，但是实际写入的是其中的一个字节

除了请求的内容以外，为了表示 CPU 想要发送请求，还需要添加 `valid` 信号：高表示发送请求，低表示不发送请求。很多时候，外设的速度比较慢，可能无法保证每个周期都可以处理请求，因此外设可以提供一个 `ready` 信号：当 `valid=1 && ready=1` 的时候，发送并处理请求；当 `valid=1 && ready=0` 的时候，表示外设还没有准备好，此时 CPU 需要一直保持 `valid=1` 不变，等到外设准备好后，`valid=1 && ready=1` 请求生效。

简单总结一下上面的需求，可以得到 master 和 slave 端分别的信号列表。这次，我们在命名的时候用 `_o` 表示输出、`_i` 表示输入，可以得到 master 端（CPU 端）的信号：

1. `clock_i`：时钟输入
2. `valid_o`：高表示 master 想要发送请求
3. `ready_i`：高表示 slave 准备好处理请求
4. `addr_o`：master 想要读写的地址
5. `we_o`：master 想要读还是写
6. `data_o`：master 想要写入的数据
7. `be_o`：master 读写的字节使能，用于实现单字节写等
8. `data_i`：slave 提供给 master 的读取的数据

除了时钟都是输入以外，把上面其余的信号输入、输出对称一下，就可以得到 slave 端（外设端）的信号：

1. `clock_i`：时钟输入
2. `valid_i`：高表示 master 想要发送请求
3. `ready_o`：高表示 slave 准备好处理请求
4. `addr_i`：master 想要读写的地址
5. `we_i`：master 想要读还是写
6. `data_i`：master 想要写入的数据
7. `be_i`：master 读写的字节使能，用于实现单字节写等
8. `data_o`：slave 提供给 master 的读取的数据

根据我们上面设计的自研总线，可以绘制出下面的波形图（以 master 的信号为例）：

<script type="WaveDrom">
{
  signal:
    [
      { name: "clock", wave: "p.........", node: ".abcdefgh"},
      { name: "valid_o", wave: "0101.01..0"},
      { name: "ready_i", wave: "010.101..0"},
      { name: "addr_o", wave: "x=x=.x===x", data: ["0x01", "0x02", "0x03", "0x01", "0x02"]},
      { name: "we_o", wave: "x1x0.x101x"},
      { name: "data_o", wave: "x=xxxx=x=x", data: ["0x12", "0x56", "0x9a"]},
      { name: "be_o", wave: "x=x=.x=x=x", data: ["0x1", "0x1", "0x1", "0x1"]},
      { name: "data_i", wave: "xxxx=xx=xx", data: ["0x34", "0x12"]},
    ]
}
</script>

- `a` 周期：此时 `valid_o=1 && ready_i=1` 说明有请求发生，此时 `we_o=1` 说明是一个写操作，并且写入地址是 `addr_o=0x01`，写入的数据是 `data_o=0x12`
- `b` 周期：此时 `valid_o=0 && ready_i=0` 说明无事发生
- `c` 周期：此时 `valid_o=1 && ready_i=0` 说明 master 想要从地址 0x02（`addr_o=0x02`）读取数据（`we_o=0`），但是 slave 没有接受（`ready_i=0`）
- `d` 周期：此时 `valid_o=1 && ready_i=1` 说明有请求发生， master 从地址 0x02（`addr_o=0x02`）读取数据（`we_o=0`），读取的数据为 0x34（`data_i=0x34`）
- `e` 周期：此时 `valid_o=0 && ready_i=0` 说明无事发生
- `f` 周期：此时 `valid_o=1 && ready_i=1` 说明有请求发生， master 向地址 0x03（`addr_o=0x03`）写入数据（`we_o=1`），写入的数据为 0x56（`data_i=0x56`）
- `g` 周期：此时 `valid_o=1 && ready_i=1` 说明有请求发生， master 从地址 0x01（`addr_o=0x01`）读取数据（`we_o=0`），读取的数据为 0x12（`data_i=0x12`）
- `h` 周期：此时 `valid_o=1 && ready_i=1` 说明有请求发生， master 向地址 0x02（`addr_o=0x02`）写入数据（`we_o=1`），写入的数据为 0x9a（`data_i=0x9a`）

从上面的波形中，可以有几点观察：

1. master 想要发起请求的时候，就设置 `valid_o=1`；当 slave 可以接受请求的时候，就设置 `ready_i=1`；在 `valid_o=1 && ready_i=1` 时视为一次请求
2. 如果 master 发起请求，同时 slave 不能接收请求，即 `valid_o=1 && ready_i=0`，此时 master 要保持 `addr_o` `we_o` `data_o` 和 `be_o` 不变，直到请求结束
3. 当 master 不发起请求的时候，即 `valid_o=0`，此时总线上的信号都视为无效数据，不应该进行处理；对于读操作，只有在 `valid_o=1 && ready_i=1` 时 `data_i` 上的数据是有效的
4. 可以连续多个周期发生请求，即 `valid_o=1 && ready_i=1` 连续多个周期等于一，此时是理想情况，可以达到总线最高的传输速度

## Wishbone Classic Standard

首先我们来看最简单的 Wishbone 版本 Wishbone Classic Standard。其设计思路和上面的自研总线非常相似，让我们来看看它的信号，例如 master 端（CPU 端）的信号：

1. `CLK_I`: 时钟输入，即自研总线中的 `clock_i`
2. `STB_O`：高表示 master 要发送请求，即自研总线中的 `valid_o`
3. `ACK_I`：高表示 slave 处理请求，即自研总线中的 `ready_i`
4. `ADR_O`：master 想要读写的地址，即自研总线中的 `addr_o`
5. `WE_O`：master 想要读还是写，即自研总线中的 `we_o`
6. `DAT_O`：master 想要写入的数据，即自研总线中的 `data_o`
7. `SEL_O`：master 读写的字节使能，即自研总线中的 `be_o`
8. `DAT_I`：master 从 slave 读取的数据，即自研总线中的 `data_i`
9. `CYC_O`：总线的使能信号，无对应的自研总线信号

还有一些可选信号，这里就不赘述了。可以看到，除了最后一个 `CYC_O`，其他的信号其实就是我们刚刚设计的自研总线。`CYC_O` 的可以认为是 master 想要占用 slave 的总线接口，在常见的使用场景下，直接认为 `CYC_O=STB_O`。它的用途是：

1. 占用 slave 的总线接口，不允许其他 master 访问
2. 简化 interconnect 的实现

## 参考文档

- [Wishbone Spec B4](https://cdn.opencores.org/downloads/wbspec_b4.pdf)