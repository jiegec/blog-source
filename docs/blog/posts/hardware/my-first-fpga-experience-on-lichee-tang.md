---
layout: post
date: 2018-10-07
tags: [verilog,licheetang,fpga,uart]
categories:
    - hardware
title: 在荔枝糖（Lichee Tang）上初次体验 FPGA 
---

今天从张宇翔学长那拿到了 [荔枝糖（Lichee Tang）](http://tang.lichee.pro/) 的 FPGA 板子，于是立即开始把前段时间学到的 Verilog 应用上来。不过想到现在我手上没有多少外设，然后又必须远程到 Windows 电脑上去操作，于是先实现了一下 UART 通信。

在网上找到了 [ben-marshall/uart](https://github.com/ben-marshall/uart) 一个简易的实现，很快做到了一直在串口上打印 `A` 字符。接着我开始尝试实现一个简单的串口回显。一开始，我直接把 UART 读到的数据直接输出，果然可以了，但是一旦传输速率跟不上了，就会丢失数据。于是我添加了 FIFO IP 核，然后把读入的数据存入 FIFO，又从 FIFO 中读取数据写入到 UART 中去。不过发现了一个小 BUG：每次打印的是倒数第二次输入的字符，即丢失了第一个字符。在张宇翔学长的帮助下找到了问题：当 FIFO 的读使能信号为高时，其数据在下一个时钟周期才来，于是解决方案就是等到数据来的时候再向 UART 中写数据：

```verilog
always @ (posedge clk_in) begin
	uart_tx_en <= uart_fifo_re;
end
```

这样就解决了这个问题。完整代码在 [jiegec/learn_licheetang](https://github.com/jiegec/learn_licheetang) 中。
