---
layout: post
date: 2019-06-21 21:23:00 +0800
tags: [c,cpp,ip,cidr,ub]
category: programming
title: IP 前缀转换上意外遇到的 Undefined Behavior
---

最近发现了两个很神奇的 Undefined Behavior ，出现在 Prefix Len 和 Netmask 的转换的问题下。一个简单思路可能是：

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

意味着， `0xFFFFFFFF >> 32` 是一个 UB ，所以出现了上面的问题。

另外，`__builtin_ctz` 有这样的说明：

```
Returns the number of trailing 0-bits in x, starting at the least significant bit position. If x is 0, the result is undefined.
```

意味着，`__builtin_ctz(0)` 也是一个 UB ， 所以得到了错误的结果。

解决方案也很简单，下面提供一个参考的解决方法：

```cpp
#define PREFIX_BIN2DEC(bin) ((bin) ? (32 - __builtin_ctz((bin))) : 0)
#define PREFIX_DEC2BIN(hex) (((uint64_t)0xFFFFFFFF << (32 - (hex))) & 0xFFFFFFFF)
```

