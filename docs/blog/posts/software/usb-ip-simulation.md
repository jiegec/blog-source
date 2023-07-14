---
layout: post
date: 2020-05-15 20:20:00 +0800
tags: [linux,usbip]
category: software
title: USB/IP 模拟 USB 设备
---

## 背景

2018 年的时候发过一篇博客，讲如何用 USB/IP 协议在两台 Linux 电脑之间共享 USB 设备。最近刚好有一个需求，就是针对一个现成的 USB device 的代码，通过 USB/IP 模拟出一个 USB 设备，然后进行调试。

## USB/IP 协议

USB/IP 只有一个简略的[文档](https://github.com/realthunder/usbip/blob/master/usbip_protocol.txt)，为数不多的使用 USB/IP 的代码，所以有一些细节没有说的很清楚，只能一点点去尝试。

首先，USB/IP 基于 TCP，端口号 3240。客户端向服务端发送请求，服务端向客户端进行回应。

请求的类型：OP_REQ_DEVLIST OP_REQ_IMPORT USBIP_CMD_SUBMIT 和 USBIP_CMD_UNLINK

回应的类型：OP_REP_DEVLIST OP_REP_IMPORT USBIP_RET_SUBMIT USBIP_RET_UNLINK

工作的过程大概如下：

1. OP_REQ_DEVLIST 请求获取设备列表
2. OP_REP_DEVLIST 返回设备列表
3. OP_REQ_IMPORT 请求 USB 设备
4. OP_REP_IMPORT 返回 USB 设备
5. USBIP_CMD_SUBMIT 发送 URB
6. USBIP_RET_SUBMIT 返回 URB

（先不考虑 CMD_UNLINK 和 RET_UNLINK）

其中前面四个比较简单清晰，所需要的字段也都是 Descriptor 中对应的字段。后面两个就相对复杂一些：URB data 的长度需要根据 endpoint 类型和 direction 共同决定。URB 实际上是 Linux 内核里的一个数据结构。

## USB 协议

那么，USB 协议的几种 transfer 怎么对应到 URB 的数据呢？首先看最常见的三种（[ref](https://www.beyondlogic.org/usbnutshell/usb4.shtml）：

1. Control Transfer
   1. 第一种是 Control IN，一共有三个阶段，第一个阶段是 Setup，Host 发送给 Device 一个八字节的 Setup Packet；第二个阶段是 Data，Device 发送给 Host 一段数据；第三个阶段是 Status，Host 发送给 Device 一个 Zero Length Packet。此时 Setup Packet 对应 urb 中的 setup，Data 就对应 RET_SUBMIT 里面的 URB data 了，自然 CMD_SUBMIT 中是没有 URB data 的
   2. 第二种是 Control OUT，一共有三个阶段，第一个阶段是 Setup，Host 发送给 Device 一个吧字节的 Setup Packet；第二个阶段是 Data，Host 给 Device 发送一段数据；第三个阶段是 Status，Device 给 Host 发送一个 Zero Length Packet。此时 Setup Packet 对应 urb 中的 setup，Data 对应 CMD_SUBMIT 末尾的 URB data，长度由 transfer_buffer_length 指定。返回的 RET_SUBMIT 不带 URB data，但依然需要有 RET_SUBMIT。
2. Interrupt/Bulk Transfer
   1. 第一种是 Interrupt/Bulk IN，由 Device 给 Host 发送一段数据，附在 RET_SUBMIT 中。
   2. 第二种是 Interrupt/Bulk OUT，由 Host 给 Device 发送一段数据，中 CMD_SUBMIT 的 URB data 中。返回的 RET_SUBMIT 不带 URB data，但不能不发 RET_SUBMIT。



可见，Interrupt 和 Bulk 是比较简单的，而 Control 和 Isochronous（没有提到）则比较复杂。

## 回到 USB/IP 协议

其实补充了这些信息以后，就可以实现一个 USB/IP 协议的服务器了。