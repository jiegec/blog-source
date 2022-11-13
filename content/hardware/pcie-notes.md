---
layout: post
date: 2022-11-12 14:56:00 +0800
tags: [pcie,notes,learn]
category: hardware
title: PCIe 学习笔记
---

## 背景

最近在知乎上看到 [LogicJitterGibbs](https://www.zhihu.com/people/ljgibbs) 的 [资料整理：可以学习 1W 小时的 PCIe](https://zhuanlan.zhihu.com/p/447134701)，我跟着资料学习了一下，然后在这里记录一些我学习 PCIe 的笔记。

下面的图片主要来自 PCIe 3.0 标准以及 MindShare 的 PCIe 3.0 书本。

## 分层

PCIe 定义了三个层：Transaction Layer，Data Link Layer，Physical Layer，和 TCP/IP 四层模型很像。PCIe 也是基于 Packet 传输的。

![](/images/pcie_layer.png)

### Transaction Layer

Transaction Layer 的核心是 Transaction Layer Packet(TLP)。TLP 格式：

![](/images/pcie_tlp.png)

即可选的若干个 Prefix，一个 Header，可选的 Data Payload，可选的 Digest。

Prefix 和 Header 开头的一个字节是 `Fmt[2:0]` 和 `Type[4:0]` 字段。Fmt 决定了 header 的长度，有无数据，或者这是一个 Prefix。

它支持几类 Packet：

- Memory: MMIO
    - Read Request(MRd)/Completion(CplD)
    - Write Request(MWr): 注意只有 Request，没有 Completion
    - AtomicOp Request(FetchAdd/Swap/CAS)/Completion(CplD)
    - Locked Memory Read(MRdLk)/Completion(CplDLk): Legacy
- IO: Legacy
    - Read Request(IORd)/Completion(CplD)
    - Write Request(IOWr)/Completion(Cpl)
- Configuration: 访问配置空间
    - Read Request(CfgRd0/CfgRd1)/Completion(CplD)
    - Write Request(CfgWr0/CfgWr1)/Completion(Cpl)
- Message: 传输 event
    - Request(Msg/MsgD)

括号里的是 TLP Type，对应了它 Fmt 和 Type 字段的取值。如果 Completion 失败了，原来应该是 CplD/CplDLk 的 Completion 会变成不带数据的 Cpl/CplLk。


在 PCIe 3.0 标准的表 2-3 中列出了 TLP Type 以及对应的 Fmt 和 Type 编码。

TLP 路由有三个方法，决定了这个 TLP 目的地是哪里：

- Address-based: 32 位或 64 位地址，用于 Memory 和 IO 请求
- ID-based：lspci 看到的地址，也就是 Bus Device Function，用于 Configuration 请求
- Implicit：用于 Message 请求，路由方法：
    - Routed to Root Complex
    - Routed by Address: PCIe 3.0 标准中没有用这个路由方法的 Message
    - Routed by ID
    - Broadcast from Root Complex
    - Local - Terminate at Receiver
    - Gathered and router to Root Complex


### Data Link Layer

Data Link Layer 的主要功能是进行 TLP 的可靠传输。它在传输 TLP 的时候，会在开头加上一个两字节的 Sequence Number，最后加上一个四字节的 LCRC（Link CRC）。

![](/images/pcie_tlp_link.png)

除了传输 TLP，Data Link Layer 还会传输 Data Link Layer Packet(DLLP)，类型包括：

- Ack DLLP: 告诉对方自己已经成功收到了 TLP
- Nak DLLP：告诉对方自己接收 TLP 失败，请重试
- InitFC1/InitFC2/UpdateFC DLLPs：流量控制
- PM_Enter_L1/PM_Enter_L23/PM_Active_State_Request_L1/PM_Request_Ack：用于电源管理

Data Link Layer 收到上层要发送 TLP 时候，首先拼接 Sequence Number 和 LCRC，然后会保存在 retry buffer 中，通过 Physical Layer 发送。从 Physical Layer 收到新的 TLP/DLLP 时，会检查它的完整性（CRC），如果正确，就向发送方发送一个 Ack DLLP，并把 TLP 提交给 Transaction Layer；如果不正确，就向发送方发送一个 Nak DLLP。如果收到了 Ack DLLP，就可以把相应的 TLP 从 retry buffer 中删掉；如果收到了 Nak DLLP，则要重传。这样就实现了 TLP 的可靠传输。

需要注意的是，TLP 和 DLLP 的区别：TLP 就像 IP，目的地址可能会跨越多跳；而 DLLP 是点对点地工作，所以一个 TLP 在转发的每一跳中，接受方都会发送一次 Ack DLLP。

Data Link Layer 的流量是 Credit-based 的：接受方会告诉发送方自己的 Buffer 还有多少空间（Credit），然后发送方根据 Credit 来控制是否继续发送 TLP。

## 配置

接触 PCIe 的时候可能会有一个疑惑，就是这些 Bus Device Function 都是怎么分配的，分配完之后，访问请求又是怎么路由的。

首先回顾一下，上面提到了 TLP 的 Memory 和 IO 是根据地址路由，Configuration 是根据 Bus Device Function 路由，而 PCIe 大概是一个树形的结构，叶子结点就是 PCIe 设备，非叶子结点是桥或者交换机。回想一下，IP 的路由是按照最长前缀匹配，如果在 PCIe 中还这样做的话，又太过于复杂了，毕竟 PCIe 可以人为地设定每个设备的地址，让地址满足一定的连续性和局部性，这样路由选择就非常简单了。

观察 PCIe 标准中 7.3.3 Configuration Request Routing Rules，结合 MindShare 的书，看 Root Ports，Switches 和 Bridges 的要求，就知道 Configuration 请求是如何路由的：

- Configuration 请求只能由 Host Bridge 发起
- 如果 Configuration 请求是 Type0，那么这个请求的目的设备就是当前设备
- 如果 Configuration 请求是 Type1，
    - 如果请求的 Bus Number 等于某一个 Downstream Port 的 Secondary Bus Number，则把 Configuration 请求转换为 Type0，然后发给该 Downstream Port
    - 如果不等于，但是 Bus Number 属于某一个 Downstream Port 的 Secondary Bus Number 和 Subordinate Bus Number 之间，则不修改 Configuration 请求，发送给该 Downstream Port。

如果类比一下 IP，那么分组在中途路由器转发的时候就是 Type1，Type0 就是最后一跳。路由就是直接按照几个不重合的 Bus Number 区间进行判断，没有复杂的最长前缀匹配。但是又有一个问题，如果按照 Bus 路由，那同一个 Bus 下不同的 Device 咋办？这就像是以太网，最后一跳的时候，如果同一个链路上有多个设备，那么多个设备都能收到，每个设备根据自己的 Device 号判断是否是发给自己的。PCI（注意不是 PCIe）总线也类似。随着速度越来越高，通过交换机，以太网已经变成了点对点，所以很少见到一个链路上同时有多个设备的情况了。PCIe 也一样，所以根据 Bus 路由就足够了。至于 lspci 看到的那些 Device 不等于 0 的设备，要么是兼容 PCI 设备的，要么是虚拟的，在设备内部进行路由的，并不是真的有一个 PCIe link 连了多个物理设备。

所以简单理解一下，PCI 总线确实是一条总线，一条总线上很多设备。而 PCIe 实际上是一个网络，可以看作是很多个 PCI 总线连接在一起，可以把 Root Complex 或者 Switch 内部看成一个虚拟的有很多设备的 PCI 总线，而 PCIe Link 可以看成是只有一个设备的 PCI 总线。这样 PCIe 交换机可以看成若干个 PCI-PCI Bridge：

![](/images/pcie_bridge.png)

还有 MindShare 书中的图 3-5:

![](/images/pcie_system.png)

可以看到，这里的每一个 Bus 就是一个 PCI 总线，既有内部的虚拟 PCI 总线（Bus 0/2/6），也有 PCIe Link 充当的 PCI 总线（Bus 1/3/4/5/7/8/9）。在虚拟的 PCI 总线里，比如 PCIe Switch，一个 Device 对应一个 Downstream Port；而 PCIe Link 对应的 PCI 总线上就只有一个 Device。然后 PCIe Switch 的每个 Upstream Port 和 Downstream Port 里会记录三个 Bus Number：Primary(Pri)，Secondary(Sec) 和 Subordinate(Sub)。Primary 指的就是它上游直接连接的 PCI 总线编号，Sec 指的是下游直接连接的 PCI 总线编号，Sub 指的是它下游的最大 PCI 总线编号。

这样，收到 Type1 的时候，Switch 按照各个 Downstream Port 的 Sec 和 Sub 进行判断，如果目标 Bus Number 等于 Sec，就转换为 Type0 发出去；如果大于 Sec，但是小于或等于 Sub，就原样发出去。可以看到，从 Host Bridge 到每个设备都可以通过这样的方式一路转发。

既然 BDF 是把 Bus 划分为多个区间来路由的，那么 Memory 和 IO 请求也类似地可以对地址进行划分，变成多个区间，然后用类似的方法进行路由。

这些用于路由的区间上下界，可以在各个端口的 Type1 Configuration Space 中找到：

![](/images/pcie_type1.png)

- 路由 Type1 Configuration Request：Primary Bus Number, Secondary Bus Number, Subordinate Bus Number
    - `Request Bus Number == Secondary Bus Number`: Type1 -> Type0
    - `Secondary Bus Number < Request Bus Number <= Subordinate Bus Number`: Type1 -> Type1
- 路由 IO Request：`I/O Base <= IO Address <= I/O Limit`
- 路由 Prefetchable Memory Request：`Prefetchable Memory Base <= Memory Address <= Prefetchable Memory Limit`
- 路由 Non-Prefetchable Memory Request：`Memory Base <= Memory Address <= Memory Limit`

而具体到每一个设备上，设备会提供若干个 BAR（Base Address Register），在枚举设备的时候，会给 BAR 分配地址，然后把设备的地址进行合并，记录到 Switch 上的 Base 和 Limit，然后一直递归，一路更新到 Root Complex。这样，就完成了地址分配，以及请求的路由。