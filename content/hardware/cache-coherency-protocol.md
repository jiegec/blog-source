---
layout: post
date: 2021-12-17 07:39:00 +0800
tags: [cpu,cache,coherence,msi,mesi,moesi]
category: hardware
title: 缓存一致性协议分析
---

## 参考文档

- [Cache coherence](https://en.wikipedia.org/wiki/Cache_coherence)
- [MSI protocol](https://en.wikipedia.org/wiki/MSI_protocol)
- [Write-once (cache coherence)](https://en.wikipedia.org/wiki/Write-once_(cache_coherence))
- [MESI protocol](https://en.wikipedia.org/wiki/MESI_protocol)
- [MOESI protocol](https://en.wikipedia.org/wiki/MOESI_protocol)
- [A Strategy to Verify an AXI/ACE Compliant Interconnect (2 of 4)](https://blogs.synopsys.com/vip-central/2014/12/23/a-strategy-to-verify-an-axi-ace-compliant-interconnect-part-2-of-4/)
- [Directory-based cache coherence](https://en.wikipedia.org/wiki/Directory-based_cache_coherence)

## Write-invalidate 和 Write-update

最基础的缓存一致性思想有两种：

1. Write-invalidate：写入数据的时候，将其他 Cache 中这条 Cache Line 设为 Invalid
2. Write-update：写入数据的时候，把新的结果写入到有这条 Cache Line 的其他 Cache

## Write-once 协议

Write-once 协议定义了四个状态：

1. Invalid：表示这个块不合法
2. Valid：表示这个块合法，并可能是共享的，同时数据没有修改
3. Reserved：表示这个块合法，不是共享的，同时数据没有更改
4. Dirty：表示这个块合法，不是共享的，数据做了修改，和内存不同。

可见，当一个缓存状态在 R 或者 D，其他缓存只能是 I；而缓存状态是 V 的时候，可以有多个缓存在 V 状态。

Write-once 协议的特点是，第一次写的时候，会写入到内存（类似 Write-through），连续写入则只写到缓存中，类似 Write-back。

当 Read hit 的时候，状态不变。

	Read hit: The information is supplied by the current cache. No state change.

当 Read miss 的时候，会查看所有缓存，如果有其他缓存处于 Valid/Reserved/Dirty 状态，就从其他缓存处读取数据，然后设为 Valid，其他缓存也设为 Valid。如果其他缓存处于 Dirty 状态，还要把数据写入内存。

	Read miss: The data is read from main memory. The read is snooped by other caches; if any of them have the line in the Dirty state, the read is interrupted long enough to write the data back to memory before it is allowed to continue. Any copies in the Dirty or Reserved states are set to the Valid state.

当 Write hit 的时候，如果是 Valid 状态，首先写入内存，把其他 Cache 都设为 Invalid，进入 Reserved 状态，这意味着第一次写是 Write-through。如果是 Reserved/Dirty 状态，则不修改内存，进入 Dirty 状态，这表示后续的写入都是 Write-back。

	Write hit: If the information in the cache is in Dirty or Reserved state, the cache line is updated in place and its state is set to Dirty without updating memory. If the information is in Valid state, a write-through operation is executed updating the block and the memory and the block state is changed to Reserved. Other caches snoop the write and set their copies to Invalid.

当 Write miss 的时候，这个行为 Wikipedia 上和上课讲的不一样。按照 Wikipedia 的说法，首先按照 Read miss 处理，再按照 Write hit 处理，类似于 Write Allocate 的思路。如果是这样的话，那么首先从其他缓存或者内存读取数据，然后把其他缓存都设为 Invalid，把更新后的数据写入内存，进入 Reserved 状态。相当于 Write miss 的时候，也是按照 Write-through 实现。

	Write miss: A partial cache line write is handled as a read miss (if necessary to fetch the unwritten portion of the cache line) followed by a write hit. This leaves all other caches in the Invalid state, and the current cache in the Reserved state.

教材上则是 Write miss 的时候按照 Write-back 处理。如果其他缓存都是 Invalid 时，从内存里读取数据，然后写入到缓存中，进入 Dirty 状态。如果其他缓存是 Valid/Reserved/Dirty 状态，就从其他缓存里读取数据，让其他缓存都进入 Invalid 状态，然后更新自己的数据，进入 Dirty 状态。

## MSI 协议

MSI 协议比较简单，它定义了三个状态：

1. Modified：表示数据已经修改，和内存里不一致
2. Shared：数据和内存一致，可以有一到多个缓存同时处在 Shared 状态
3. Invalid：不在缓存中

当 Read hit 的时候，状态不变。

当 Read miss 的时候，检查其他缓存的状态，如果都是 Invalid，就从内存里读取，然后进入 Shared 状态。如果有 Shared，就从其他缓存处读取。如果有 Dirty，那就要把其他缓存的数据写入内存和本地缓存，然后进入 Shared 状态。

当 Write hit 的时候，如果现在是 Shared 状态，则要让其他的 Shared 缓存进入 Invalid 状态，然后更新数据，进入 Modified 状态。如果是 Modified 状态，那就修改数据，状态保持不变。

当 Write miss 的时候，如果有其他缓存处于 Modified/Shared 状态，那就从其他缓存处读取数据，并让其他缓存进入 Invalid 状态，然后修改本地数据，进入 Modified 状态。如果所有缓存都是 Invalid 状态，那就从内存读入，然后修改缓存数据，进入 Modified 状态。

## MESI 协议

MESI 协议定义了四种状态：

1. Modified：数据与内存不一致，并且只有一个缓存有数据
2. Exclusive：数据与内存一致，并且只有一个缓存有数据
3. Shared：数据与内存一致，可以有多个缓存同时有数据
4. Invalid：不在缓存中

当 Read hit 的时候，状态不变。

当 Read miss 的时候，首先会检查其他缓存的状态，如果有数据，就从其他缓存读取数据，并且都进入 Shared 状态，如果其他缓存处于 Modified 状态，还需要把数据写入内存；如果其他缓存都没有数据，就从内存里读取，然后进入 Exclusive 状态。

当 Write hit 的时候，进入 Modified 状态，同时让其他缓存进入 Invalid 状态。

当 Write miss 的时候，检查其他缓存的状态，如果有数据，就从其他缓存读取，否则从内存读取。然后，其他缓存都进入 Invalid 状态，本地缓存更新数据，进入 Modified 状态。

值得一提的是，Shared 状态不一定表示只有一个缓存有数据：比如本来有两个缓存都是 Shared 状态，然后其中一个因为缓存替换变成了 Invalid，那么另一个是不会受到通知变成 Exclusive 的。Exclusive 的设置是为了减少一些总线请求，比如当数据只有一个核心访问的时候，只有第一次 Read miss 会发送总线请求，之后一直在 Exclusive/Modified 状态中，不需要发送总线请求。

## MOESI 协议

MOESI 定义了五个状态：

1. Modified：数据经过修改，并且只有一个缓存有这个数据
2. Owned：同时有多个缓存有这个数据，但是只有这个缓存可以修改数据
3. Exclusive：数据没有修改，并且只有一个缓存有这个数据
4. Shared：同时有多个缓存有这个数据，但是不能修改数据
5. Invalid：不在缓存中

状态中，M 和 E 是独占的，所有缓存里只能有一个。此外，可以同时有多个 S，或者多个 S 加一个 O，但是不能同时有多个 O。

它的状态转移与 MESI 类似，区别在于：当核心写入 Owned 状态的缓存时，有两种方式：1）通知其他 Shared 的缓存更新数据；2）把其他 Shared 缓存设为 Invalid，然后本地缓存进入 Modified 状态。在 Read miss 的时候，则可以从 Owned 缓存读取数据，进入 Shared 状态，而不用写入内存。它相比 MESI 的好处是，减少了写回内存的次数。

AMD64 文档里采用的就是 MOESI 协议。AMBA ACE 协议其实也是 MOESI 协议，只不过换了一些名称，表示可以兼容 MEI/MESI/MOESI 中的一个协议。ACE 对应关系如下：

1. UniqueDirty: Modified
2. SharedDirty: Owned
3. UniqueClean: Exclusive
4. SharedClean: Shared
5. Invalid: Invalid

需要注意的是，SharedClean 并不代表它的数据和内存一致，比如说和 SharedDirty 缓存一致，它只是说缓存替换的时候，不需要写回内存。

## ACE 协议

ACE 协议在 AXI 的基础上，添加了三个 channel：

1. AC：Coherent address channel，Input to master：ACADDR，ACSNOOP，ACPROT
2. CR：Coherent response channel，Output from master：CRRESP
3. CD：Coherent data channel，Output from master：CDDATA，CDLAST

此外，已有的 Channel 也添加了信号：

1. ARSNOOP[3:0]/ARBAR[1:0]/ARDOMAIN[1:0]
2. AWSNOOP[3:0]/AWBAR[1:0]/AWDOMAIN[1:0]/AWUNIQUE
3. RRESP[3:2]
4. RACK/WACK

ACE-lite 只在已有 Channel 上添加了新信号，没有添加新的 Channel。因此它内部不能有 Cache，但是可以访问一致的缓存内容。

当 Read miss 的时候，首先 AXI master 发送 read transaction 给 Interconnect，Interconnect 向保存了这个缓存行的缓存发送 AC 请求，如果有其他 master 提供了数据，就向请求的 master 返回数据；如果没有其他 master 提供数据，则向内存发起读请求，并把结果返回给 master，最后 master 提供 RACK 信号。

当 Write miss 的时候，也是类似地，AXI master 发送 MakeUnique 请求给 Interconnect，Interconnect 向保存了该缓存行的缓存发送请求，要求其他 master 状态改为 Invalid；当所有 master 都已经 invalidate 成功，就向原 AXI master 返回结果。

## 基于目录的缓存一致性

上面的缓存一致性协议中，经常有这么一个操作：向所有有这个缓存行的缓存发送/接受消息。简单的方法是直接广播，然后接受端自己判断是否处理。但是这个方法在核心很多的时候会导致广播流量太大，因此需要先保存下来哪些缓存会有这个缓存的信息，然后对这些缓存点对点地发送。这样就可以节省一些网络流量。

那么，怎么记录这个信息呢？一个简单的办法（Full bit vector format）是，有一个全局的表，对每个缓存行，都记录一个大小为 N（N 为核心数）的位向量，1 表示对应的核心中有这个缓存行。但这个方法保存数据量太大：缓存行数正比于 N，还要再乘以一次 N，总容量是 O(N^2) 的。

一个稍微好一些的方法（Coarse bit vector format）是，我把核心分组，比如按照 NUMA 节点进行划分，此时每个缓存行都保存一个大小为 M（M 为 NUMA 数量）的位向量，只要这个 NUMA 节点里有这个缓存行，对应位就取 1。这样相当于是以牺牲一部分流量为代价（NUMA 节点内部广播），来节省一些目录的存储空间。

但实际上，通常情况下，一个缓存行通常只会在很少的核心中保存，所以这里有很大的优化空间。比如说，可以设置一个缓存行同时出现的缓存数量上限(Limited pointer format)，然后保存核心的下标而不是位向量，这样的存储空间就是 O(Nlog2N)。但是呢，这样限制了缓存行同时出现的次数，如果超过了上限，需要替换掉已有的缓存，可能在一些场景下性能会降低。

还有一种方式，就是链表(Chained directory format)。目录中保存最后一次访问的核心编号，然后每个核心的缓存里，保存了下一个保存了这个缓存行的核心编号，或者表示链表终止。这样存储空间也是 O(Nlog2N)，不过发送消息的延迟更长，因为要串行遍历一遍，而不能同时发送。类似地，可以用二叉树(Number-balanced binary tree format)来组织：每个缓存保存两个指针，指向左子树和右子树，然后分别遍历，目的还是加快遍历的速度，可以同时发送消息给多个核心。