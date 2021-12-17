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