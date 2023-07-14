---
layout: post
date: 2019-05-30
tags: [ip,udp,checksum]
category: networking
title: IP 和 UDP Checksum 的增量更新问题
---

之前在写 IP Checksum 的增量更新，就是当 TTL -= 1 的时候，Checksum 应该增加 0x0100，但是这样会有问题，在于，如果按照原来的 IP Checksum 计算方法，是不会出现 0xFFFF 的（求和，进位，然后取反写入），这种加法就有可能出现 0xFFFF。于是翻阅了相关的 RFC：

首先是 RFC 1141 相关部分：

```c++
unsigned long sum;
ipptr->ttl--;                  /* decrement ttl */
sum = ipptr->Checksum + 0x100;  /* increment checksum high byte*/
ipptr->Checksum = (sum + (sum>>16)) /* add carry */
```

这也是比较直接能想到的一种方法，但是会出现刚才提到的问题。于是 RFC 1624 纠正了这个问题：

```
  Although this equation appears to work, there are boundary conditions
   under which it produces a result which differs from the one obtained
   by checksum computation from scratch.  This is due to the way zero is
   handled in one's complement arithmetic.

   In one's complement, there are two representations of zero: the all
   zero and the all one bit values, often referred to as +0 and -0.
   One's complement addition of non-zero inputs can produce -0 as a
   result, but never +0.  Since there is guaranteed to be at least one



Rijsinghani                                                     [Page 2]
 
RFC 1624             Incremental Internet Checksum              May 1994


   non-zero field in the IP header, and the checksum field in the
   protocol header is the complement of the sum, the checksum field can
   never contain ~(+0), which is -0 (0xFFFF).  It can, however, contain
   ~(-0), which is +0 (0x0000).

   RFC 1141 yields an updated header checksum of -0 when it should be
   +0.  This is because it assumed that one's complement has a
   distributive property, which does not hold when the result is 0 (see
   derivation of [Eqn. 2]).

   The problem is avoided by not assuming this property.  The correct
   equation is given below:

          HC' = ~(C + (-m) + m')    --    [Eqn. 3]
              = ~(~HC + ~m + m')
```

只要把代码简单修改一下就可以了，或者遇到 0xFFFF 时设为 0，这时候就解决了这个问题。

但是，仔细研究了一下发现，UDP Checksum 又是这么定义的（RFC 768）:

```
If the computed  checksum  is zero,  it is transmitted  as all ones (the
equivalent  in one's complement  arithmetic).   An all zero  transmitted
checksum  value means that the transmitter  generated  no checksum  (for
debugging or for higher level protocols that don't care).
```

刚好和 IP Checksum 相反，这就很有意思了。