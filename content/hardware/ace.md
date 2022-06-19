---
layout: post
date: 2022-05-16 00:34:00 +0800
tags: [axi,bus,cache,coherence,teaching]
category: hardware
title: 「教学」ACE 缓存一致性协议
---

## 背景

最近几天分析了 TileLink 的缓存一致性协议部分内容，见[TileLink 总线协议分析]({{< relref "tilelink.md" >}})，趁此机会研究一下之前尝试过研究，但是因为缺少一些基础知识而弃坑的 ACE 协议分析。

下面主要参考了 IHI0022E 的版本，也就是 AXI4 对应的 ACE 版本。

## 回顾

首先回顾一下一个缓存一致性协议需要支持哪些操作。对于较上一级 Cache 来说，它需要这么几件事情：

1. 读或写 miss 的时候，需要请求这个缓存行的数据，并且更新自己的状态，比如读取到 Shared，写入到 Modified 等。
2. 写入一个 valid && !dirty 的缓存行的时候，需要升级自己的状态，比如从 Shared 到 Modified。
3. 需要 evict 一个 valid && dirty 的缓存行的时候，需要把 dirty 数据写回，并且降级自己的状态，比如 Modified -> Shared/Invalid。如果需要 evict 一个 valid && !dirty 的缓存行，可以选择通知，也可以选择不通知下一级。
4. 收到 snoop 请求的时候，需要返回当前的缓存数据，并且更新状态。
5. 需要一个方法来通知下一级 Cache/Interconnect，告诉它第一和第二步完成了。

如果之前看过我的 TileLink 分析，那么上面的这些操作对应到 TileLink 就是：

1. 读或写 miss 的时候，需要请求这个缓存行的数据（发送 AcquireBlock，等待 GrantData），并且更新自己的状态，比如读取到 Shared，写入到 Modified 等。
2. 写入一个 valid && !dirty 的缓存行的时候，需要升级自己的状态（发送 AcquirePerm，等待 Grant），比如从 Shared 到 Modified。
3. 需要 evict 一个 valid && dirty 的缓存行的时候，需要把 dirty 数据写回（发送 ReleaseData，等待 ReleaseAck），并且降级自己的状态，比如 Modified -> Shared/Invalid。如果需要 evict 一个 valid && !dirty 的缓存行，可以选择通知（发送 Release，等待 ReleaseAck），也可以选择不通知下一级。
4. 收到 snoop 请求的时候（收到 Probe），需要返回当前的缓存数据（发送 ProbeAck/ProbeAckData），并且更新状态。
5. 需要一个方法（发送 GrantAck）来通知下一级 Cache/Interconnect，告诉它第一和第二步完成了。

秉承着这个思路，再往下看 ACE 的设计，就会觉得很自然了。

## Cache state model

首先来看一下 ACE 的缓存状态模型，我在之前的[缓存一致性协议分析]({{< relref "cache-coherency-protocol.md" >}})中也分析过，它有这么五种，就是 MOESI 的不同说法：

1. UniqueDirty: Modified
2. SharedDirty: Owned
3. UniqueClean: Exclusive
4. SharedClean: Shared
5. Invalid: Invalid

文档中的定义如下：

- Valid, Invalid: When valid, the cache line is present in the cache. When invalid, the cache line is not present in the cache.
- Unique, Shared: When unique, the cache line exists only in one cache. When shared, the cache line might exist in more than one cache, but this is not guaranteed.
- Clean, Dirty: When clean, the cache does not have responsibility for updating main memory. When dirty, the cache line has been modified with respect to main memory, and this cache must ensure that main memory is eventually updated.

大致理解的话，Unique 表示只有一个缓存有这个缓存行，Shared 表示有可能有多个缓存有这个缓存行；Clean 表示它不负责更新内存，Dirty 表示它负责更新内存。下面的很多操作都是围绕这些状态进行的。

文档中也说，它支持 MOESI 的不同子集：MESI, ESI, MEI, MOESI，所以也许在一个简化的系统里，一些状态可以不存在，实现会有所不同。

## Channel usage examples

到目前为止，我还没有介绍 ACE 的信号，但是我们可以尝试一下，如果我们是协议的设计者，我们要如何添加信号来完成这个事情。

首先考虑上面提到的第一件事情：读或写 miss 的时候，需要请求这个缓存行的数据，并且更新自己的状态，比如读取到 Shared，写入到 Modified 等。

我们知道，AXI 有 AR 和 R channel 用于读取数据，那么遇到读或者写 miss 的时候，可以在 AR channel 上捎带一些信息，让下一级的 Interconnect 知道自己的意图是读还是写，然后 Interconnect 就在 R channel 上返回数据。

那么，具体要捎带什么信息呢？我们“不妨”用这样一种命名方式：`操作+目的状态`，比如我读 miss 的时候，需要读取数据，进入 Shared 状态，那就叫 ReadShared；我写 miss 的时候，需要读取数据（通常写入缓存的只是一个缓存行的一部分，所以先要把完整的读进来），那就叫 ReadUnique。这个操作可以编码到一个信号中，传递给 Interconnect。

再来考虑上面提到的第二件事情：写入一个 valid && !dirty 的缓存行的时候，需要升级自己的状态，比如从 Shared 到 Modified。

这个操作，需要让 Interconnect 把其他缓存中的这个缓存行数据清空，并且把自己升级到 Unique。根据上面的 `操作+目的状态` 的命名方式，我们可以命名为 CleanUnique，即把其他缓存都 Clean 掉，然后自己变成 Unique。

接下来考虑上面提到的第三件事情：需要 evict 一个 valid && dirty 的缓存行的时候，需要把 dirty 数据写回，并且降级自己的状态，比如 Modified -> Shared/Invalid。

按照前面的 `操作+目的状态` 命名法，可以命名为 WriteBackInvalid。ACE 实际采用的命名是 WriteBack。

终于到了第四件事情：收到 snoop 请求的时候，需要返回当前的缓存数据，并且更新状态。

既然 snoop 是从 Interconnect 发给 Master，在已有的 AR R AW W B channel 里没办法做这个事情，不然会打破已有的逻辑。那不得不添加一对 channel，比如我规定一个 AC channel 发送 snoop 请求，规定一个 C channel 让 master 发送响应，这样就可以了。这就相当于 TileLink 里面的 B channel（Probe 请求）和 C channel（ProbeAck 响应）。实际 ACE 和刚才设计的实际有一些区别，把 C channel 拆成了两个：CR 用于返回所有响应，CD 用于返回那些需要数据的响应。这就像 AW 和 W 的关系，一个传地址，一个传数据；类似地，CR 传状态，CD 传数据。

那么，接下来考虑一下 AC channel 上要发送什么请求呢？我们回顾一下上面已经用到的请求类型：需要 snoop 的有 ReadShared，ReadUnique 和 CleanUnique，不需要 snoop 的有 WriteBack。那我们直接通过 AC channel 把 ReadShared，ReadUnique 和 CleanUnique 这三种请求原样发送给需要 snoop 的 cache 那里就可以了。

Cache 在 AC channel 收到这些请求的时候，可以做相应的动作。由于 MOESI 协议下同样的请求可以有不同的响应方法，这里就不细说了。

这时候我们已经基本把 ACE 协议的信号和大题的工作流程推导出来了。哦，我们还忘了第五件事情：需要一个方法来通知下一级 Cache/Interconnect，告诉它第一和第二步完成了。TileLink 添加了一个额外的 E channel 来做这个事情，ACE 更加粗暴：直接用一对 RACK 和 WACK 信号来分别表示最后一次读和写已经完成。

关于 WACK 和 RACK 详见 [What's the purpose for WACK and RACK for ACE and what's the relationship with WVALID and RVALID?](https://community.arm.com/support-forums/f/soc-design-and-simulation-forum/9888/what-s-the-purpose-for-wack-and-rack-for-ace-and-what-s-the-relationship-with-wvalid-and-rvalid) 的讨论。

## 总结

到这里就暂时不继续分析了，其他的很多请求类型是服务于更多场景，比如一次写整个 Cache Line 的话，就不需要读取已有的数据了；或者一次性读取完就不管了，或者这是一个不带缓存的加速器，DMA 等，有一些针对性的优化或者简化的处理，比如对于不带缓存的 master，可以简化为 ACE-Lite，比如 ARM 的 CCI-400 支持两个 ACE master 和 三个 ACE-Lite Master，这些 Master 可以用来接 GPU 等外设。再简化一下 ACE-Lite，就得到了 ACP（Accelerator Coherency Port）。

最后我们再把文章开头的五件事对应到 ACE 上，作为一个前后的呼应：

1. 读或写 miss 的时候，需要请求这个缓存行的数据（AR 上发送 ReadShared/ReadUnique），并且更新自己的状态，比如读取到 Shared，写入到 Modified 等。
2. 写入一个 valid && !dirty 的缓存行的时候，需要升级自己的状态（AR 上发送 CleanUnique），比如从 Shared 到 Modified。
3. 需要 evict 一个 valid && dirty 的缓存行的时候，需要把 dirty 数据写回（AW 上发送 WriteBack），并且降级自己的状态，比如 Modified -> Shared/Invalid。如果需要 evict 一个 valid && !dirty 的缓存行，可以选择通知（AW 上发送 Evict），也可以选择不通知下一级。
4. 收到 snoop 请求的时候（AC 上收到 snoop 请求），需要返回当前的缓存数据（通过 CR 和 CD），并且更新状态。
5. 需要一个方法（读 RACK 写 WACK）来通知下一级 Cache/Interconnect，告诉它第一和第二步完成了。

## 参考文献

- [IHI0022E-AMBA AXI and ACE](https://developer.arm.com/documentation/ihi0022/e/)