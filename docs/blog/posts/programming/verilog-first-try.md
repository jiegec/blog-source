---
layout: post
date: 2018-06-21
tags: [fpga,verilog,verilator,cpu]
categories:
    - programming
title: Verilog 初体验
---

自己以前一直对硬件方面没有接触，但是大二大三很快就要接触相关知识，所以自己就先预习一下 Verilog HDL，以便以后造计算机。听学长们推荐了一本书叫《自己动手写 CPU》，由于自己手中只有很老的 Spartan-3 板子，手上没有可以用来试验的 FPGA，所以选择用 Verilog + Verilator 进行模拟。既然是模拟，自然是会有一定的问题，不过这个以后再说。

然后就是模仿着这本书的例子，写了指令的获取和指令的解码两部分很少很少的代码，只能解码 ori (or with immidiate) 这一个指令。然后，通过 verilator 跑模拟，输出 vcd 文件，再用 gtkwave 显示波形，终于能够看到我想要的结果了。能够看到，前一个时钟周期获取指令，下一个时钟周期进行解码，出现了流水线的结果。这让我十分开心。

接下来就是实现一些基本的算术指令，然后讲计算的结果写入到相应的寄存器中。这样做完之后，就可以做一个基于 verilator 的简易 A+B 程序了。

我的代码发布在[jiegec/learn_verilog](https://github.com/jiegec/learn_verilog)中。最近马上到考试周，可能到暑假会更频繁地更新吧。
