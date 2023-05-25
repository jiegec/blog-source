---
layout: post
date: 2022-06-19 17:05:00 +0800
tags: [wishbone,bus,teaching]
category: hardware
title: 「教学」Wishbone 总线协议
---

本文的内容已经整合到[知识库](/kb/hardware/bus_protocol.html)中。

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
- `d` 周期：此时 `valid_o=1 && ready_i=1` 说明有请求发生，master 从地址 0x02（`addr_o=0x02`）读取数据（`we_o=0`），读取的数据为 0x34（`data_i=0x34`）
- `e` 周期：此时 `valid_o=0 && ready_i=0` 说明无事发生
- `f` 周期：此时 `valid_o=1 && ready_i=1` 说明有请求发生，master 向地址 0x03（`addr_o=0x03`）写入数据（`we_o=1`），写入的数据为 0x56（`data_i=0x56`）
- `g` 周期：此时 `valid_o=1 && ready_i=1` 说明有请求发生，master 从地址 0x01（`addr_o=0x01`）读取数据（`we_o=0`），读取的数据为 0x12（`data_i=0x12`）
- `h` 周期：此时 `valid_o=1 && ready_i=1` 说明有请求发生，master 向地址 0x02（`addr_o=0x02`）写入数据（`we_o=1`），写入的数据为 0x9a（`data_i=0x9a`）

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

把上面自研总线的波形图改成 Wishbone Classic Standard，就可以得到：

<script type="WaveDrom">
{
  signal:
    [
      { name: "CLK_I", wave: "p.........", node: ".abcdefgh"},
      { name: "CYC_O", wave: "0101.01..0"},
      { name: "STB_O", wave: "0101.01..0"},
      { name: "ACK_I", wave: "010.101..0"},
      { name: "ADR_O", wave: "x=x=.x===x", data: ["0x01", "0x02", "0x03", "0x01", "0x02"]},
      { name: "WE_O", wave: "x1x0.x101x"},
      { name: "DAT_O", wave: "x=xxxx=x=x", data: ["0x12", "0x56", "0x9a"]},
      { name: "SEL_O", wave: "x=x=.x=x=x", data: ["0x1", "0x1", "0x1", "0x1"]},
      { name: "DAT_I", wave: "xxxx=xx=xx", data: ["0x34", "0x12"]},
    ]
}
</script>

## Wishbone Classic Pipelined

上面的 Wishbone Classic Standard 协议非常简单，但是会遇到一个问题：假设实现的是一个 SRAM 控制器，它的读操作有一个周期的延迟，也就是说，在这个周期给出地址，需要在下一个周期才可以得到结果。在 Wishbone Classic Standard 中，就会出现下面的波形：

<script type="WaveDrom">
{
  signal:
    [
      { name: "CLK_I", wave: "p.....", node: ".abcd"},
      { name: "CYC_O", wave: "01...0"},
      { name: "STB_O", wave: "01...0"},
      { name: "ACK_I", wave: "0.1010"},
      { name: "ADR_O", wave: "x=.=.x", data: ["0x01", "0x02"]},
      { name: "WE_O", wave: "x0...x"},
      { name: "DAT_O", wave: "xxxxxx"},
      { name: "SEL_O", wave: "x=...x", data: ["0x1"]},
      { name: "DAT_I", wave: "xx=x=x", data: ["0x12", "0x34"]},
    ]
}
</script>

- `a` 周期：master 给出读地址 0x01，此时 SRAM 控制器开始读取，但是此时数据还没有读取回来，所以 `ACK_I=0`
- `b` 周期：此时 SRAM 完成了读取，把读取的数据 0x12 放在 `DAT_I` 并设置 `ACK_I=1`
- `c` 周期：master 给出下一个读地址 0x02，SRAM 要重新开始读取
- `d` 周期：此时 SRAM 完成了第二次读取，把读取的数据 0x34 放在 `DAT_I` 并设置 `ACK_I=1`

从波形来看，功能没有问题，但是每两个周期才能进行一次读操作，发挥不了最高的性能。那么怎么解决这个问题呢？我们在 `a` 周期给出第一个地址，在 `b` 周期得到第一个数据，那么如果能在 `b` 周期的时候给出第二个地址，就可以在 `c` 周期得到第二个数据。这样，就可以实现流水线式的每个周期进行一次读操作。但是，Wishbone Classic Standard 要求 `b` 周期时第一次请求还没有结束，因此我们需要修改协议，来实现流水线式的请求。

实现思路也很简单：既然 Wishbone Classic Standard 认为 `b` 周期时，第一次请求还没有结束，那就让第一次请求提前在 `a` 周期完成，只不过它的数据要等到 `b` 周期才能给出。实际上，这个时候的一次读操作，可以认为分成了两部分：首先是 master 向 slave 发送读请求，这个请求在 `a` 周期完成；然后是 slave 向 master 发送读的结果，这个结果在 `b` 周期完成。为了实现这个功能，我们进行如下修改：

- 添加 `STALL_I` 信号：`CYC_O=1 && STB_O=1 && STALL_I=0` 表示进行一次读请求
- 修改 `ACK_I` 信号含义：`CYC_O=1 && STB_O=1 && ACK_I=1` 表示一次读响应

进行如上修改以后，我们就得到了 Wishbone Classic Pipelined 总线协议。上面的两次连续读操作波形如下：

<script type="WaveDrom">
{
  signal:
    [
      { name: "CLK_I", wave: "p....", node: ".abcd"},
      { name: "CYC_O", wave: "01..0"},
      { name: "STB_O", wave: "01.0."},
      { name: "STALL_I", wave: "0...."},
      { name: "ACK_I", wave: "0.1.0"},
      { name: "ADR_O", wave: "x==xx", data: ["0x01", "0x02"]},
      { name: "WE_O", wave: "x0.xx"},
      { name: "DAT_O", wave: "xxxxx"},
      { name: "SEL_O", wave: "x=.xx", data: ["0x1"]},
      { name: "DAT_I", wave: "xx==x", data: ["0x12", "0x34"]},
    ]
}
</script>

- `a` 周期：master 请求读地址 0x01，slave 接收读请求（`STALL_O=0`）
- `b` 周期：slave 返回读请求结果 0x12，并设置 `ACK_I=1`；同时 master 请求读地址 0x02，slave 接收读请求（`STALL_O=0`）
- `c` 周期：slave 返回读请求结果 0x34，并设置 `ACK_I=1`；master 不再发起请求，设置 `STB_O=0`
- `d` 周期：所有请求完成，master 设置 `CYC_O=0`

这样我们就实现了一个每周期进行一次读操作的 slave。

## 参考文档

- [Wishbone Spec B4](https://cdn.opencores.org/downloads/wbspec_b4.pdf)