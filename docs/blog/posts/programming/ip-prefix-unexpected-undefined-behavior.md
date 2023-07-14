---
layout: post
date: 2019-06-21
tags: [c,cpp,ip,cidr,ub]
category: programming
title: IP 前缀转换上意外遇到的 Undefined Behavior
---

最近发现了两个很神奇的 Undefined Behavior，出现在 Prefix Len 和 Netmask 的转换的问题下。一个简单思路可能是：

```c++
#define PREFIX_BIN2DEC(bin) (32 - __builtin_ctz((bin)))
#define PREFIX_DEC2BIN(hex) (((~0) >> (32 - (hex))) << (32 - (hex))
```

乍一看，似乎没有什么问题。但是，在一些平台下，可能会出现这样的结果：

```
PREFIX_BIN2DEC(0x00000000) = 33
PREFIX_DEC2BIN(0) = 0xFFFFFFFF
```

而且只能在一些平台上不确定地复现，最后发现其实是 Undefined Behavior，在 C 的标准中：

```
In any case, the behavior is undefined if rhs is negative or is greater or equal the number of bits in the promoted lhs.
```

意味着， `0xFFFFFFFF >> 32` 是一个 UB，所以出现了上面的问题。

另外，`__builtin_ctz` 有这样的说明：

```
Returns the number of trailing 0-bits in x, starting at the least significant bit position. If x is 0, the result is undefined.
```

意味着，`__builtin_ctz(0)` 也是一个 UB，所以得到了错误的结果。

解决方案也很简单，下面提供一个参考的解决方法：

```cpp
#define PREFIX_BIN2DEC(bin) ((bin) ? (32 - __builtin_ctz((bin))) : 0)
#define PREFIX_DEC2BIN(hex) (((uint64_t)0xFFFFFFFF << (32 - (hex))) & 0xFFFFFFFF)
```

Quagga 的实现：

```c
/* Convert masklen into IP address's netmask (network byte order). */
void
masklen2ip (const int masklen, struct in_addr *netmask)
{
  assert (masklen >= 0 && masklen <= IPV4_MAX_BITLEN);

  /* left shift is only defined for less than the size of the type.
   * we unconditionally use long long in case the target platform
   * has defined behaviour for << 32 (or has a 64-bit left shift) */

  if (sizeof(unsigned long long) > 4)
    netmask->s_addr = htonl(0xffffffffULL << (32 - masklen));
  else
    netmask->s_addr = htonl(masklen ? 0xffffffffU << (32 - masklen) : 0);
}

/* Convert IP address's netmask into integer. We assume netmask is
   sequential one. Argument netmask should be network byte order. */
u_char
ip_masklen (struct in_addr netmask)
{
  uint32_t tmp = ~ntohl(netmask.s_addr);
  if (tmp)
    /* clz: count leading zeroes. sadly, the behaviour of this builtin
     * is undefined for a 0 argument, even though most CPUs give 32 */
    return __builtin_clz(tmp);
  else
    return 32;
}
```

BIRD 的解决方法：

```c
/**
 * u32_mkmask - create a bit mask
 * @n: number of bits
 *
 * u32_mkmask() returns an unsigned 32-bit integer which binary
 * representation consists of @n ones followed by zeroes.
 */
u32
u32_mkmask(uint n)
{
  return n ? ~((1 << (32 - n)) - 1) : 0;
}

/**
 * u32_masklen - calculate length of a bit mask
 * @x: bit mask
 *
 * This function checks whether the given integer @x represents
 * a valid bit mask (binary representation contains first ones, then
 * zeroes) and returns the number of ones or 255 if the mask is invalid.
 */
uint
u32_masklen(u32 x)
{
  int l = 0;
  u32 n = ~x;

  if (n & (n+1)) return 255;
  if (x & 0x0000ffff) { x &= 0x0000ffff; l += 16; }
  if (x & 0x00ff00ff) { x &= 0x00ff00ff; l += 8; }
  if (x & 0x0f0f0f0f) { x &= 0x0f0f0f0f; l += 4; }
  if (x & 0x33333333) { x &= 0x33333333; l += 2; }
  if (x & 0x55555555) l++;
  if (x & 0xaaaaaaaa) l++;
  return l;
}
```

