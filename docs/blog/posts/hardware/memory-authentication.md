---
layout: post
date: 2022-05-10
tags: [memory,bus,dram,auth,teaching]
categories:
    - hardware
---

# 「教学」内存认证算法

## 背景

之前 @松 给我讲过一些内存认证（Memory Authentication）算法的内容，受益匪浅，刚好今天某硬件群里又讨论到了这个话题，于是趁此机会再学习和整理一下相关的知识。

内存认证计算的背景是可信计算，比如要做一些涉及重要数据的处理，从软件上，希望即使系统被攻击非法进入了，也可以保证重要信息不会泄漏；从硬件上，希望即使系统可以被攻击者进行一些物理的操作（比如导出或者修改内存等等），也可以保证攻击者无法读取或者篡改数据。

下面的内容主要参考了 [Hardware Mechanisms for Memory Authentication: A Survey of Existing Techniques and Engines](https://link.springer.com/chapter/10.1007/978-3-642-01004-0_1) 这篇 2009 年的文章。

## 威胁模型

作为一个防御机制，首先要确定攻击方的能力。一个常见的威胁模型是认为，攻击者具有物理的控制，可以任意操控内存中的数据，但是无法读取或者修改 CPU 内部的数据。也就是说，只有 CPU 芯片内的数据是可信的，离开了芯片都是攻击者掌控的范围。一个简单的想法是让内存中保存的数据是加密的，那么怎样攻击者可以如何攻击加密的数据？下面是几个典型的攻击方法：

- Spoofing attack：把内存数据改成任意攻击者控制的数据；这种攻击可以通过签名来解决
- Splicing or relocation attack：把某一段内存数据挪到另一部分，这样数据的签名依然是正确的；所以计算签名时需要把地址考虑进来，这样地址变了，验证签名就会失败
- Replay attack：如果同一个地址的内存发生了改变，攻击者可以把旧的内存数据再写进去，这样签名和地址都是正确的；为了防止重放攻击，还需要引入计数器或者随机 nonce

## Authentication Primitives

为了防御上面几种攻击方法，上面提到的文章里提到了如下的思路：

一是 Hash Function，把内存分为很多个块，每一块计算一个密码学 Hash 保存在片内，那么读取数据的时候，把整块数据读取进来，计算一次 Hash，和片内保存的结果进行比对；写入数据的时候，重新计算一次修改后数据的 Hash，更新到片内的存储。这个方法的缺点是没有加密，攻击者可以看到内容，只不过一修改就会被 CPU 发现（除非 Hash 冲突），并且存储代价很大：比如 512-bit 的块，每一块计算一个 128-bit 的 Hash，那就浪费了 25% 的空间，而片内空间是十分宝贵的。

二是 MAC Function，也就是密码学的消息验证码，它需要一个 Key，保存在片内；由于攻击者不知道密码，根据 MAC 的性质，攻击者无法篡改数据，也无法伪造 MAC，所以可以直接把计算出来的 MAC 也保存到内存里。为了防御重放攻击，需要引入随机的 nonce，并且把 nonce 保存在片内，比如每 512-bit 的数据，保存 64-bit 的 nonce，这样片内需要保存 12.5% 的空间，依然不少。MAC 本身也不加密，所以如果不希望攻击者看到明文，还需要进行加密。

三是 Block-Level AREA，也就是在把明文和随机的 nonce 拼接起来，采用块加密算法，保存在内存中；解密的时候，验证最后的 nonce 和片内保存的一致。这个方法和 MAC 比较类似，同时做了加密的事情，也需要在片内保存每块数据对应的随机 nonce。

## Integrity Tree

但是上面几种方法开销都比较大，比如要保护 1GB 的内存，那么片内就要保存几百 MB 的数据，这对于片内存储来说太大了。这时候，可以采用区块链里常用的 Merkle Tree 或者类似的方法来用时间换空间。

这种方法的主要思路是，首先把内存划分为很多个块，这些块对应一颗树的叶子结点；自底向上构建一颗树，每个结点可以验证它的子结点的完整性，那么经过 log(n) 层的树，最后只会得到一个很小的根结点，只需要把根结点保存在片内。

为了验证某一个块的完整性，就从这一块对应的叶子结点开始，不断计算出一个值，和父亲结点比较；再递归向上，最后计算出根结点的值，和片内保存的值进行对比。这样验证的复杂度是 O(logn)，但是片内保存的数据变成了 O(1)，所以是以时间换空间。更新数据的时候，也是类似地从叶子结点一步一步计算，最后更新根结点的值。

这个方法浪费的空间，考虑所有非叶子结点保存的数据，如果是二叉树，总的大小就是数据的一半，但是好处是大部分都可以保存在内存里，所以是比较容易实现的。缺点是每次读取和写入都要进行 O(logn) 次的内存访问和计算，开销比较大。

上面提到的父结点的值的计算方法，如果采用密码学 Hash 函数，这棵树就是 Merkle Tree。它的验证过程是只读的，可以并行的，但是更新过程是串行的，因为要从子结点一步一步计算 Hash，父结点依赖子结点的 Hash 结果。

另一种设计是 Parallelizable Authentication Tree（PAT），它采用 MAC 而不是 Hash，每个结点保存了一个随机的 nonce 和计算出来的 MAC 值，最底层的 MAC 输入是实际的数据，其他层的 MAC 输入是子结点的 nonce，最后在片内保存最后一次 MAC 使用的 nonce 值。这样的好处是更新的时候，每一层都可以并行算，因为 MAC 的输入是 nonce 值，不涉及到子结点的 MAC 计算结果。缺点是要保存更多数据，即 MAC 和 nonce。

还有一种设计是 Tamper-Evident Counter Tree（TEC-Tree），计算的方法则是上面提到的 Block-level AREA。类似地，最底层是用数据和随机 nonce 拼起来做加密，而其他层是用子节点的随机 nonce 拼起来，再拼接上这一层的 nonce 做加密。验证的时候，首先对最底层进行解密，然后判断数据是否匹配，然后再解密上一层，判断 nonce 是否匹配，一直递归，最后解密到根的 nonce，和片内保存的进行匹配。更新的时候，也可以类似地一次性生产一系列的 nonce，然后并行地加密每一层的结果。

最后引用文章里的一个对比：

![](/images/memory_integrity.png)

可以看到，后两种算法可以并行地更新树的节点，同时也需要保存更多的数据。

## Cached Trees

从上面的 Integrity Tree 算法可以发现，每次读取或者写入都要访问内存 O(logn) 次，这个对性能影响是十分巨大的。一个简单的思路是，我把一些经常访问的树结点保存在片内的缓存，这样就可以减少一些内存访问次数；进一步地，如果认为攻击者无法篡改片内的缓存，那就可以直接认为片内的结点都是可信的，在验证和更新的时候，只需要从叶子结点遍历到缓存在片内的结点即可。

## The Bonsai Merkle Tree

为了进一步减少空间的占用，Bonsai Merkle Tree（BMT）的思路是，既然对每个内存块都生成一个比较长的（比如 64 位）的 nonce 比较耗费空间，那是否可以减少一下 nonce 的位数，当 nonce 出现重复的时候，换一个密钥重新加密呢？具体的做法是，每个内存块做一次 MAC 计算，输入是数据，地址和 counter：`M=MAC(C, addr, ctr)`。此时，地址和 `ctr` 充当了原来的 nonce 的作用，所以类似地，此时的 Merkle Tree 保护的是这些 counter，由于 counter 位数比较少，就可以进一步地减少空间的开销，而且树的层数也更少了。缺点是既然位数少了，如果 counter 出现了重复，就需要更换密钥，重新进行一次加密，这个比较耗费时间，所以还要尽量减少重新加密的次数。

具体来说，为了避免重放攻击，每次更新数据的时候，就让 counter 加一，这和原来采用一个足够长（比如 64-bit）的随机 nonce 是类似的。重新加密是很耗费时间的，因此为了把重新加密的范围局限到一个小的局部，又设计了一个两级的 counter：7-bit 的 local counter，每次更新数据加一；64-bit 的 global counter，当某一个 local counter 溢出的时候加一。这时候实际传入 MAC 计算的 counter 则是 global counter 拼接上 local counter。这样相当于是做了一个 counter 的共同前缀，在内存访问比较均匀的时候，比如每个 local counter 轮流加一，那么每次 local counter 溢出只需要重新加密一个小范围的内存，减少了开销。

文章后续还提到了一些相关的算法，这里就不继续翻译和总结了。

## Mountable Merkle Tree

再来看一下 [Scalable Memory Protection in the Penglai Enclave](https://www.usenix.org/system/files/osdi21-feng.pdf) 中提到的 Mountable Merkle Tree 设计。它主要考虑的是动态可变的保护内存区域，比如提到的微服务场景，并且被保护内存区域的访问有时间局部性，因此它的思路是，不去构造一个对应完整内存的 Merkle Tree，而是允许一些子树不存在。具体来说，它设计了一个 Sub-root nodes 的概念，对应了 Merkle Tree 中间的一层。这一层往上是预先分配好的，并且大部分保存在内存中，根结点保存在片内，这一层往下是动态分配的。比如应用创建了一个新的 enclave，需要新的一个被保护的内存区域，再动态分配若干个 Merkle Tree，接到 Sub-root nodes 层，成为新的子树。

![](/images/mountable_merkle_tree.png)

由于片内空间是有限的，所以这里采取了缓存的方式，只把一部分常用的树结点保存在片内；如果某一个子树一直没有被访问，就可以换出到内存里。如果删除了一个已有的 enclave，那么相应的子树就可以删掉，减少内存空间的占用。

## 参考文献

- [Hardware Mechanisms for Memory Authentication: A Survey of Existing Techniques and Engines](https://link.springer.com/chapter/10.1007/978-3-642-01004-0_1)
- [Scalable Memory Protection in the Penglai Enclave](https://www.usenix.org/system/files/osdi21-feng.pdf)