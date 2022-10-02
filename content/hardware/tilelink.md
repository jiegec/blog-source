---
layout: post
date: 2022-05-09 16:15:00 +0800
tags: [tilelink,bus,cache,coherence]
category: hardware
title: TileLink 总线协议分析
---

## 背景

最近在研究一些支持缓存一致性的缓存的实现，比如 rocket-chip 的实现和 sifive 的实现，因此需要研究一些 TileLink 协议。本文讨论的时候默认读者具有一定的 AXI 知识，因此很多内容会直接参考 AXI。

## 信号

根据 [TileLink Spec 1.8.0](https://github.com/chipsalliance/omnixtend/blob/master/OmniXtend-1.0.3/spec/TileLink-1.8.0.pdf)，TileLink 分为以下三种：

- TL-UL: 只支持读写，不支持 burst，类比 AXI-Lite
- TL-UH：支持读写，原子指令，预取，支持 burst，类比 AXI+ATOP（AXI5 引入的原子操作）
- TL-C：在 TL-UH 基础上支持缓存一致性协议，类比 AXI+ACE/CHI

## TileLink Uncached

TileLink Uncached(TL-UL 和 TL-UH) 包括了两个 channel：

- A channel: M->S 发送请求，类比 AXI 的 AR/AW/W
- D channel: S->M 发送响应，类比 AXI 的 R/W

因此 TileLink 每个周期只能发送读或者写的请求，而 AXI 可以同时在 AR 和 AW channel 上发送请求。

一些请求的例子：

- 读：M->S 在 A channel 上发送 Get，S->M 在 D channel 上发送 AccessAckData
- 写：M->S 在 A channel 上发送 PutFullData/PutPartialData，S->M 在 D channel 是发送 AccessAck
- 原子操作：M->S 在 A channel 上发送 ArithmeticData/LogicalData，S->M 在 D channel 上发送 AccessAckData
- 预取操作：M->S 在 A channel 上发送 Intent，S->M 在 D channel 上发送 AccessAck

## AXI4ToTL

针对 [AXI4ToTL](https://github.com/chipsalliance/rocket-chip/blob/850e1d5d56989f031fe3e7939a15afa1ec165d64/src/main/scala/amba/axi4/ToTL.scala#L59) 模块的例子，来分析一下如何把一个 AXI4 Master 转换为 TileLink。

首先考虑一下 AXI4 和 TileLink 的区别：一个是读写 channel 合并了，所以这里需要一个 Arbiter；其次 AXI4 中 AW 和 W 是分开的，这里也需要进行合并。这个模块并不考虑 Burst 的情况，而是由 [AXI4Fragmenter](https://github.com/chipsalliance/rocket-chip/blob/850e1d5d56989f031fe3e7939a15afa1ec165d64/src/main/scala/amba/axi4/Fragmenter.scala#L14=) 来进行拆分，即添加若干个 AW beat，和 W 进行配对。

具体到代码实现上，首先把 AR channel [对应到](https://github.com/chipsalliance/rocket-chip/blob/850e1d5d56989f031fe3e7939a15afa1ec165d64/src/main/scala/amba/axi4/ToTL.scala#L86=) 到 A channel 上：

```scala
val r_out = Wire(out.a)
r_out.valid := in.ar.valid
r_out.bits :<= edgeOut.Get(r_id, r_addr, r_size)._2
```

然后 AW+W channel 也[连接](https://github.com/chipsalliance/rocket-chip/blob/850e1d5d56989f031fe3e7939a15afa1ec165d64/src/main/scala/amba/axi4/ToTL.scala#L119=) 到 A channel，由于不用考虑 burst 的情况，这里在 aw 和 w 同时 valid 的时候才认为有请求。

```scala
val w_out = Wire(out.a)
in.aw.ready := w_out.ready && in.w.valid && in.w.bits.last
in.w.ready  := w_out.ready && in.aw.valid
w_out.valid := in.aw.valid && in.w.valid
w_out.bits :<= edgeOut.Put(w_id, w_addr, w_size, in.w.bits.data, in.w.bits.strb)._2
```

比较有意思的是读写的 id 增加了若干位，最低位 0 表示读，1 表示写，剩下几位是请求编号，这样发出去的是不同 id 的多个请求。

然后，把读和写的 A channel [连接](https://github.com/chipsalliance/rocket-chip/blob/850e1d5d56989f031fe3e7939a15afa1ec165d64/src/main/scala/amba/axi4/ToTL.scala#L155=)到 Arbiter 上：

```scala
TLArbiter(TLArbiter.roundRobin)(out.a, (UInt(0), r_out), (in.aw.bits.len, w_out))
```

其余的部分则是对 D channel 进行判断，有数据的转给 R channel，没有数据的转给 B channel：

```scala
out.d.ready := Mux(d_hasData, ok_r.ready, ok_b.ready)
ok_r.valid := out.d.valid && d_hasData
ok_b.valid := out.d.valid && !d_hasData
```

最后处理了一下 TileLink 和 AXI4 对写请求返回确认的区别：TileLink 中，可以在第一个 burst beat 就返回确认，而 AXI4 需要在最后一个 burst beat 之后返回确认。

## TLToAXI4

再来看一下反过来的转换，从 TileLink Master 到 AXI。由于 TileLink 同时只能进行读或者写，所以它首先做了一个虚构的 arw channel，可以理解为合并了 ar 和 aw channel 的 AXI4，这个设计在 SpinalHDL 的代码中也能看到。然后再根据是否是写入，分别[连接](https://github.com/chipsalliance/rocket-chip/blob/850e1d5d56989f031fe3e7939a15afa1ec165d64/src/main/scala/tilelink/ToAXI4.scala#L153=)到 ar 和 aw channel：

```scala
val queue_arw = Queue.irrevocable(out_arw, entries=depth, flow=combinational)
out.ar.bits := queue_arw.bits
out.aw.bits := queue_arw.bits
out.ar.valid := queue_arw.valid && !queue_arw.bits.wen
out.aw.valid := queue_arw.valid &&  queue_arw.bits.wen
queue_arw.ready := Mux(queue_arw.bits.wen, out.aw.ready, out.ar.ready)
```

[这里](https://github.com/chipsalliance/rocket-chip/blob/850e1d5d56989f031fe3e7939a15afa1ec165d64/src/main/scala/tilelink/ToAXI4.scala#L197=)处理了 aw 和 w 的 valid 信号：

```scala
in.a.ready := !stall && Mux(a_isPut, (doneAW || out_arw.ready) && out_w.ready, out_arw.ready)
out_arw.valid := !stall && in.a.valid && Mux(a_isPut, !doneAW && out_w.ready, Bool(true))
out_w.valid := !stall && in.a.valid && a_isPut && (doneAW || out_arw.ready)
```

这样做的原因是，在 TileLink 中，每个 burst 都是一个 a channel 上的请求，而 AXI4 中，只有第一个 burst 有 aw 请求，所有 burst 都有 w 请求，因此这里用 doneAW 信号来进行区分。

接着，要把 b 和 r channel 上的结果连接到 d channel，根据上面的经验，[这里](https://github.com/chipsalliance/rocket-chip/blob/850e1d5d56989f031fe3e7939a15afa1ec165d64/src/main/scala/tilelink/ToAXI4.scala#L205=) 又是一个 arbitration：

```scala
val r_wins = (out.r.valid && b_delay =/= UInt(7)) || r_holds_d
out.r.ready := in.d.ready && r_wins
out.b.ready := in.d.ready && !r_wins
in.d.valid := Mux(r_wins, out.r.valid, out.b.valid)
```

最后还处理了一下请求和结果顺序的问题。

## TileLink Cached

上面说的两个模块都是 TileLink Uncached，那么它如何支持缓存一致性呢？首先，它引入了三个 channel：C、D 和 E，支持三种操作：

- Acquire：M->S 在 A channel 上发送 Acquire，S->M 在 D channel 上发送 Grant，然后 M->S 在 E channel 上发送 GrantAck；功能是获取一个 copy，可以看到这个和 Get 是类似的，都是在 A channel 上发送请求，在 D channel 上接受响应，只不过额外需要在 E channel 上发送 GrantAck。
- Release：M->S 在 C channel 上发送 Release，S->M 在 D channel 上发送 ReleaseAck；功能是删除自己的 copy，一般是缓存行要被换出的时候，发送 ReleaseData 来写回 Dirty 数据
- Probe：S->M 在 B channel 上发送 Probe，M->S 在 C channel 上发送 ProbeAck；功能是要求 M 删除自己的 copy，通常是有某一个缓存发送了 Acquire，导致其他缓存需要降低权限

可以看到，A C E 三个 channel 是 M->S，B D 两个 channel 是 S->M。

假如一个缓存（Master A）要写入一块只读数据，或者读取一块 miss 的缓存行，如果是广播式的缓存一致性协议，那么需要经历如下的过程：

- Master A -> Slave: Acquire
- Slave -> Master B: Probe
- Master B -> Slave: ProbeAck
- Slave -> Master A: Grant
- Master A -> Slave: GrantAck

首先 Master A 发出 Acquire 请求，然后 Slave 向其他 Master 广播 Probe，等到其他 Master 返回 ProbeAck 后，再向 Master A 返回 Grant，最后 Master A 发送 GrantAck 给 Slave。这样 Master A 就获得了这个缓存行的一份拷贝，并且让 Master B 的缓存行失效或者状态变成只读。

TileLink 的缓存行有三个状态：None，Branch 和 Trunk(Tip)。基本对应 MSI 模型：None->Invalid，Branch->Shared 和 Trunk->Modified。Rocket Chip 代码中 [ClientStates](https://github.com/chipsalliance/rocket-chip/blob/850e1d5d56989f031fe3e7939a15afa1ec165d64/src/main/scala/tilelink/Metadata.scala#L10=) 还定义了 Dirty 状态，大致对应 MESI 模型：None->Invalid，Branch->Shared，Trunk->Exclusive，Dirty->Modified。

此外，标准还说可以在 B 和 C channel 上进行 TL-UH 的操作。标准这么设计的意图是可以让 Slave 转发操作到拥有缓存数据的 Master 上。比如 Master A 在 A channel 上发送 Put 请求，那么 Slave 向 Master B 的 B channel 上发送 Put 请求，Master B 在 C channel 上发送 AccessAck 响应，Slave 再把响应转回 Master A 的 D channel。这就像是一个片上的网络，Slave 负责在 Master 之间路由请求。

## Broadcast

接下来看看 Rocket Chip 自带的基于广播的缓存一致性协议实现。核心实现是 [TLBroadcast](https://github.com/chipsalliance/rocket-chip/blob/850e1d5d56989f031fe3e7939a15afa1ec165d64/src/main/scala/tilelink/Broadcast.scala)，核心的逻辑就是，如果一个 Master A 发送了 Acquire，那么 TLBroadcast 需要发送 Probe 到其他的 Master，当其他的 Master 都响应了 ProbeAck 后，再返回 Grant 到 Master A。

首先来看 B channel 上的 Probe [逻辑](https://github.com/chipsalliance/rocket-chip/blob/850e1d5d56989f031fe3e7939a15afa1ec165d64/src/main/scala/tilelink/Broadcast.scala#L214=)。它记录了一个 todo bitmask，表示哪些 Master 需要发送 Probe，这里采用了 Probe Filter 来减少发送 Probe 的次数，因为只需要向拥有这个缓存行的 Master 发送 Probe：

```scala
val probe_todo = RegInit(0.U(max(1, caches.size).W))
val probe_line = Reg(UInt())
val probe_perms = Reg(UInt(2.W))
val probe_next = probe_todo & ~(leftOR(probe_todo) << 1)
val probe_busy = probe_todo.orR()
val probe_target = if (caches.size == 0) 0.U else Mux1H(probe_next, cache_targets)

// Probe whatever the FSM wants to do next
in.b.valid := probe_busy
if (caches.size != 0) {
	in.b.bits := edgeIn.Probe(probe_line << lineShift, probe_target, lineShift.U, probe_perms)._2
}
when (in.b.fire()) { probe_todo := probe_todo & ~probe_next }
```

这里 `probe_next` 就是被 probe 的那个 Master 对应的 bitmask，`probe_target` 就是 Master 的 Id。这个 Probe FSM 的输入就是 Probe Filter，它会[给出](https://github.com/chipsalliance/rocket-chip/blob/850e1d5d56989f031fe3e7939a15afa1ec165d64/src/main/scala/tilelink/Broadcast.scala#L256=)哪些 Cache 拥有当前的缓存行的信息：

```scala
val leaveB = !filter.io.response.bits.needT && !filter.io.response.bits.gaveT
val others = filter.io.response.bits.cacheOH & ~filter.io.response.bits.allocOH
val todo = Mux(leaveB, 0.U, others)
filter.io.response.ready := !probe_busy
when (filter.io.response.fire()) {
	probe_todo  := todo
	probe_line  := filter.io.response.bits.address >> lineShift
	probe_perms := Mux(filter.io.response.bits.needT, TLPermissions.toN, TLPermissions.toB)
}
```

这里又区分两种情况：如果 Acquire 需要进入 Trunk 状态（比如是个写入操作），意味着其他 Master 需要进入 None 状态，所以这里要发送 toN；如果 Acquire 不需要进入 Trunk 状态（比如是个读取操作），那么只需要其他 Master 进入 Branch 状态，所以这里要发送 toB。

在 B channel 发送 Probe 的同时，也要[处理](https://github.com/chipsalliance/rocket-chip/blob/850e1d5d56989f031fe3e7939a15afa1ec165d64/src/main/scala/tilelink/Broadcast.scala#L152=) C channel 上的 ProbeAck 和 ProbeAckData：

```scala
// Incoming C can be:
// ProbeAck     => decrement tracker, drop 
// ProbeAckData => decrement tracker, send out A as PutFull(DROP)
// ReleaseData  =>                    send out A as PutFull(TRANSFORM)
// Release      => send out D as ReleaseAck
```

由于这里采用的是 invalidation based，所以如果某个 Master 之前处于 Dirty 状态，那么它会发送 ProbeAckData，此时需要把数据写回，所以需要用 PutFull 把数据写出去。

## Serialization

下面来讨论一下 TileLink 对各组信号的一些要求。

### Flow Control Rules

首先是 Flow Control Rules，讨论的是 ready 和 valid 信号的关系，目的是防止死锁。首先是两个比较常规的要求：

- If ready is LOW, the receiver must not process the beat and the sender must not consider the beat processed.
- If valid is LOW, the receiver must not expect the control or data signals to be a syntactically correct TileLink beat.

第一个说的就是 valid & ready 的时候才认为是一个 beat 处理了，第二个就是如果 valid=LOW，那么信号可能是随机的、不合法的。

- valid must never depend on ready. If a sender wishes to send a beat, it must assert valid independently of whether the receiver signals that it is ready.
- As a consequence, there must be no combinational path from ready to valid or any of the control and data signals.

这里是为了防止组合逻辑出现环路，如果 valid 依赖 ready，ready 依赖 valid，就会出现问题，所以这里规定，valid 不能依赖 ready，反过来只能 ready 依赖 valid。类似地，其他的数据和控制信号也不可以依赖 ready。简单理解就是 sender 要主动提供数据，而 receiver 决定了是否接受。

- A low priority valid may not combinationally depend on a high priority valid. In other words, the decision to send a request may not be based on receiving a response in the same cycle.
- A high priority ready may not combinationally depend on a low priority ready. In other words, acceptance of a response may not be made contingent upon a request being accepted the same cycle.

这两条的意思是，同一个周期内，我设置发送的请求的 valid，不能依赖于同一个周期内接受到的响应的 valid，比如 A 的 valid 不能组合依赖于 D 的 valid。另一方面，我设置的响应的 ready 不能依赖于同一个周期内的请求，比如 D 的 ready 不能组和依赖于 A 的 ready。

那么，有这么几种用法是可以的：

- It is acceptable for a receiver to drive ready in response to valid or any of the control and data signals. For example, an arbiter may lower ready if a valid request is made for an address which is busy. However, whenever possible, it is recommended that ready be driven independently so as to reduce the handshaking circuit depth. 接收方可以让 ready 依赖于 valid 或者其他的控制和数据信号，不过这样会让组合逻辑比较长。
- A channel may change valid and all control and data signals based on the value of ready in the prior cycle. For example, after a request has been accepted (ready HIGH), a new request may be presented. Only a same-cycle dependency of valid on ready is forbidden. 可以让当前周期的 valid 依赖于上一个周期的 ready 信号，只是不能有同周期的 valid 对 ready 的依赖。
- A device may legally drive valid for a response based on valid of a request in the same cycle. For example, a combinational ROM which answers immediately. In this case, presumably ready for the request will likewise be driven by ready for the response. The converse relationship is forbidden. 设备可以让响应的 valid 依赖请求的 valid，比如一个组合的 ROM，它的 D channel 的 valid 可以组合依赖于 A channel 的 valid，同时 A channel 的 ready 组合依赖于 D channel 的 ready。这样就简化了设备的设计，并且可以无延迟地进行访问。

和 AXI 不同的一点在于，TileLink 不要求 irrevocable，也就是说如果一个周期内 valid=HIGH 但是 ready=LOW，那么下一个周期 Master 可以修改控制和数据信号，也可以让 valid=LOW。

	Note that a sender may raise valid and then lower it on the following
	cycle, even if the message was not accepted on the previous cycle. For example,
	the sender might have some other higher priority task to perform on the
	following cycle, instead of trying to send the rejected message again.
	Furthermore, the sender may change the contents of the control and data signals
	when a message was not accepted.

TileLink 的 burst 请求是通过比 bus 更宽的 size 的多个 beat 组成的。一旦第一个 beat fire 了，后续只能发送同一个 burst 的数据，不可以交错。

### Request-Response Message Ordering

这里讨论的是请求和响应的顺序关系。TileLink 规定，响应的第一个 beat 不早于第一个请求的 beat，比如：

- 对于 Get 请求，如果响应需要多个 beat，那么第一个 beat 不早于请求的那一个周期，这个比较常规，意思是可以组合返回响应。
- 对于 Put 请求，如果请求需要多个 beat，那么响应可以在第一个请求的 beat 的周期，这个比较特别，意思是对于多个 beat 的请求，可以立即返回响应，不需要等到所有请求的 beat 完成。
- 对于 ArithmeticData 请求，响应和请求都可能有多个 beat，那么响应的第一个 beat 不早于请求的第一个 beat 即可，其他没有顺序要求。

### Deadlock Freedom

那么多规则，一个很重要的目的是要防止死锁。为了防止死锁，有这样三条：

1. The agent graph (Section 5.3) contains no cycles
2. Agents must eventually present all beats of a received message
3. Unless they have a higher priority message in flight or unanswered
    1. Agents must eventually accept a presented beat
    2. Agents must eventually answer a received request message

大概意思是，beat 不能无限推迟，无论是发送方还是接受方。对于每个请求，它的响应不能无限推迟。

TileLink 定义了各个 channel 的优先级，从低到高是 `A<B<C<D<E`。对于同一个 channel，A C E 上是 master/sender 优先级更高，B D 上是 slave/receiver 优先级更高。

TileLink 的设计里保证了，每个请求的响应都比请求优先级更高。比如 A channel 的请求（Get/Put/AcquireBlock）的响应在 D channel（AccessAckData/AccessAck/Grant），B channel 的请求（Probe）的响应在 C channel（ProbeAck），C channel 的请求（Release）的响应在 D channel（ReleaseAck），D channel 的请求（Grant）的响应在 E channel（GrantAck）。

## 参考文档

- [TileLink spec](https://github.com/chipsalliance/omnixtend/blob/master/OmniXtend-1.0.3/spec/TileLink-1.8.0.pdf)
- [rocket-chip](https://github.com/chipsalliance/rocket-chip)
