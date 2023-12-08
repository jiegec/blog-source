---
layout: post
date: 2023-12-08
tags: [cpu,paging,vipt,cache]
categories:
    - hardware
---

# VIPT 与缓存大小和页表大小的关系

VIPT（Virtual Index Physical Tag）是 L1 数据缓存常用的技术，利用了虚拟地址和物理地址的 Index 相同的特性，得以优化 L1 数据缓存的读取。但是 VIPT 的使用，与页表大小和 L1 数据缓存大小都有关系。这篇博客探讨一下，VIPT 技术背后的一些问题。

<!-- more -->

## VIPT 是什么

以防读者不记得 VIPT 是什么，这里再复习一下缓存的原理。首先，把数据的物理地址划分为三段：

1. Tag
2. Index
3. Offset

缓存组织成多路，每一路有若干个项，每项里面是一个缓存行。查询时，首先根据 Index 作为下标，去索引缓存，得到多路的缓存行；然后再用 Tag 和多路缓存行进行比较，如果有匹配，则说明是命中；否则就是缓存缺失。

可以看到，这个过程是先用 Index，后用 Tag，因此如果可以先得到 Index，就可以提前完成第一步。回顾一下物理地址和虚拟地址的转换：物理地址和虚拟地址的页内偏移是相同的，只会修改页号。那么，如果把 Index 放在页内偏移的部分，那就可以在虚实地址转换之前，直接从虚拟地址获取到 Index，并且这个 Index 一定是物理地址的 Index，毕竟虚实地址转换不会修改 Index。这就是 VIPT。

所以很明显，VIPT 是一种优化方法，利用虚实转换中页内偏移不变的特性，实现更快的数据缓存读取。

## VIPT 的局限性

但同时，VIPT 也给 L1 数据缓存带来了局限性。前面提到，VIPT 要求 Index 被包含在页内偏移中，那么可以来算一算，Index 最大是多少：

假如页大小是 $P$，每个缓存行大小是 $C$，为了让 Index 包含在页内偏移中，Index 的个数（也叫做 Sets）$I$ 需要满足 $I * C \le P$。

此时考虑一下数据缓存的总大小：每个 Index 有 Way 路缓存行，所以总大小是 $I * C * W$，其中 $W$ 指的是路数。此时你会发现，数据缓存的总大小不大于 $W * P$，也就是路数乘以页的大小。

换句话说，L1 数据缓存大小，受限于路数乘以页的大小。如果你去查看一些处理器，你会发现它们都取到了这个最大值：

1. i9-13900K: L1 数据缓存 48KB，$W=12, P=4096$
2. i9-10980XE: L1 数据缓存 32KB，$W=8, P=4096$
3. EPYC 7551: L1 数据缓存 32KB，$W=8, P=4096$
3. 3A6000: L1 数据缓存 64KB，$W=4, P=16384$

毕竟比较大的 L1 数据缓存对性能是有帮助的，当然了，太大了也会导致 Load To Use 延迟增加，可能得不偿失。

当然了，L2 L3 等缓存就没有这个限制了，毕竟通常是采用物理地址，不涉及 VIPT。

这时候你可能要说了，等等！为啥有一些处理器不符合这个规则：

1. Kunpeng-920: L1 数据缓存 64KB，$W=4, P=4096$

此时 $W * P$ 只有 16KB，为什么能够实现 64KB 的数据缓存？实际上，前面的讨论都基于一个假设：页表大小是固定的。要是页表大小不唯一呢？

## 多变的页表大小

现在一些处理器，特别是非 x86 的处理器，通常会支持多种页表大小：4KB、16KB 和 64KB，由操作系统决定使用哪一种。例如上面的例子中，Kunpeng-920 就支持多种页表大小，如果你用数据缓存大小倒推，会得到页表是 16KB 的结论。那么问题来了，如果要支持多种页表大小，VIPT 还能正常工作吗？

假设有一个 CPU，数据缓存大小是 64KB，4 路，缓存行大小是 64 字节。那么，根据这些信息，可以计算出缓存有 256 个 Set，也就是 Index 可以取 0 到 255，占用地址的 8 个位。缓存行大小是 64 字节，行内便宜占用地址的 6 位。也就是说，Index 对应的是地址的 `[13:6]` 位。接下来对页表大小进行分类讨论：

假如页表大小是 64 KB，那么页内偏移就是地址的第 `[15:0]` 位，那么物理地址和虚拟地址的 `[15:0]` 位相等，自然 Index 对应的 `[13:6]` 位也相等，VIPT 不会遇到问题。

假如页表大小是 16 KB，那么页内偏移就是地址的第 `[13:0]` 位，那么物理地址和虚拟地址的 `[13:0]` 位相等，自然 Index 对应的 `[13:6]` 位也相等，VIPT 不会遇到问题。

假如页表大小是 4 KB，那么页内偏移就是地址的第 `[11:0]` 位，那么物理地址和虚拟地址的 `[11:0]` 位相等，但是 Index 对应的 `[13:6]` 位就不一定相等了。这时候会出现什么问题呢？

如果虚拟地址和物理地址都是一一对应，那么即使映射时修改了 `[13:12]` 位，Index 变了，也没问题，只要保存的 Tag 是完整的 `[VALEN-1:12]` 位，数据依然可以精确地找到，不会访问到错误的数据。但是，在实际使用的时候，有可能出现多个虚拟地址对应同一个物理地址，例如共享内存等等。举一个例子：

1. 第一个虚拟页到物理页的映射：0x80000000 -> 0x00000000
2. 第二个虚拟页到物理页的映射：0x80001000 -> 0x00000000

这两个虚拟页对应同一个物理页，但是这两个虚拟页的 Index 却不相同，因为它们的第 `[13:12]` 位不相等。回顾 L1 数据缓存访问的流程，第一步就是用 Index 作为下标去访问，既然两个虚拟页的访问时下标就不一样，自然也没法访问到同样的数据，往第一个虚拟页写数据，从第二个虚拟页却读不出来，这就坏事了。这个现象叫做 virtual aliasing。

这个问题怎么解决呢？阅读 [Cache and TLB Flushing Under Linux](https://www.kernel.org/doc/Documentation/cachetlb.txt)，里面有一段话：

```
Is your port susceptible to virtual aliasing in its D-cache?
Well, if your D-cache is virtually indexed, is larger in size than
PAGE_SIZE, and does not prevent multiple cache lines for the same
physical address from existing at once, you have this problem.

If your D-cache has this problem, first define asm/shmparam.h SHMLBA
properly, it should essentially be the size of your virtually
addressed D-cache (or if the size is variable, the largest possible
size).  This setting will force the SYSv IPC layer to only allow user
processes to mmap shared memory at address which are a multiple of
this value.
```

翻译成中文，意思就是，假如数据缓存的 VIPT 是基于一个比较大的页（上面的例子是 16KB），比实际的页表大小更大（4KB），并且没有防止同一个物理地址的缓存行出现多次，就会遇到问题。为了解决这个问题，需要在 Linux 里设置 `SHMLBA` 参数，它的大小应该是 VIPT 对应的页大小（16KB）。它会要求共享内存的基地址一定是 `SHMLBA` 的倍数。

这就解决了前面的问题：出现多个虚拟地址映射同一个物理地址时，既然 Index 不一致会有问题，那就软件上去保证 Index 一致，而保证 Index 一致，其实就是对齐到 `SHMLBA` 的倍数。回顾上面的例子：

1. 第一个虚拟页到物理页的映射：0x80000000 -> 0x00000000
2. 第二个虚拟页到物理页的映射：0x80001000 -> 0x00000000

第二个页就没有对齐到 `SHMLBA`，也就是 16KB 的边界上。假如映射的时候，就保证第二个页对齐到 16KB 的边界上，就变成了：

1. 第一个虚拟页到物理页的映射：0x80000000 -> 0x00000000
2. 第二个虚拟页到物理页的映射：0x80004000 -> 0x00000000

此时这两个页的虚拟地址的 `[13:12]` 位就相同了，不会出现 virtual aliasing 的问题。这个方法也叫 Page Coloring（的一种），额外要求共享内存中虚拟地址和物理地址的第 `[13:12]` 位相同。

因此，在使用共享内存的时候，不要忘记了对齐到 `SHMLBA`，它不一定是页表的大小。

这是软件做法，有没有硬件做法呢？答案是，有，可以参考 [What problem does cache coloring solve?](https://cs.stackexchange.com/a/32302) 和 [Designing a Virtual Memory System for the SHMAC Research Infrastructure](https://ntnuopen.ntnu.no/ntnu-xmlui/handle/11250/2467634) 第 3.7 节。这里列出来几种比较好理解的方法：

1. 缓存缺失的时候，去其他 set 里寻找匹配，如果发现了，就把数据挪到当前的 virtual index 对应的位置。这个方法复杂点在于需要去其他 set 里寻找可能的匹配。
2. 在 L2 缓存中记录缓存行对应的 virtual index，缓存缺失的时候，去询问 L2，L2 发现有 alias 的情况，告诉 L1 缓存，让他去指定的 set 里寻找数据，并且迁移。这个方法的好处是不需要像第一种方法那样去寻找可能的匹配，而是让 L2 去记录信息。缺点就是需要记录更多信息，另外要求 L2 缓存需要是 inclusive 的。见 [XiangShan Cache 别名问题](https://xiangshan-doc.readthedocs.io/zh-cn/latest/huancun/cache_alias/)

此外还有一些比较复杂的方法，建议阅读上面的参考论文。

因此 VIPT 也可以不受实际的页大小的限制，但是为了解决 aliasing 的问题，需要在软件上或者硬件上找补。

## 参考

- [Page Colouring on ARMv6 (and a bit on ARMv7)](https://community.arm.com/arm-community-blogs/b/architectures-and-processors-blog/posts/page-colouring-on-armv6-and-a-bit-on-armv7)
- 推荐阅读：[浅谈现代处理器实现超大 L1 Cache 的方式](https://blog.cyyself.name/why-the-big-l1-cache-is-so-hard/)