---
layout: post
date: 2023-07-22
tags: [cpp,stl,random,sampling]
categories:
    - programming
---

# libc++ 的 uniform_int_distribution 性能问题

## 背景

前段时间，@lwpie 发现一段 C++ 代码在 macOS 下，分别用自带的 Clang 编译和用 Homebrew 的 GCC 编译，性能差距接近一个数量级，下面是运行时间：

- GCC-13 Homebrew: 300
- Apple Clang: 2170

<!-- more -->

代码如下：

```c++
#include <algorithm>
#include <array>
#include <chrono>
#include <iostream>
#include <memory>
#include <random>

constexpr size_t FILE_N = 1e8;
constexpr size_t DATA_R = (1 << 23);

int main() {
  for (size_t i = 0; i < 4; ++i) {
    auto start = std::chrono::high_resolution_clock::now();
    std::random_device rd;
    std::mt19937_64 gen(rd());
    std::uniform_int_distribution<> dis(0, DATA_R);
    std::shared_ptr<std::array<size_t, FILE_N>> data(
        new std::array<size_t, FILE_N>());
    std::generate(data->begin(), data->end(),
                  [&dis, &gen]() { return dis(gen); });
    auto end = std::chrono::high_resolution_clock::now();
    std::cout << std::chrono::duration_cast<std::chrono::milliseconds>(end -
                                                                       start)
                     .count()
              << std::endl;
    auto mean = std::accumulate(data->begin(), data->end(), 0.0) / FILE_N;
    std::cout << mean << std::endl;
  }
  return 0;
}
```

首先上结论：GCC-13 Homebrew 用的是 libstdc++，而 Apple Clang 用的是 libc++；libstdc++ 优化了 uniform_int_distribution 的实现，而 libc++ 采用的是朴素的实现，同时参数的选取正好触发了朴素实现的最坏情况，因此性能差距巨大。

## 探究

从现象上来看，看起来是 GCC 和 Clang 的性能差异很大，但由于这里涉及到了 STL 的实现，因此控制变量很重要：经过测试，发现 Clang + libstdc++ 性能好，GCC + libstdc++ 性能好，Clang + libc++ 性能差。

因此问题大概可以定位在 libc++ 上。那么，就去找 libc++ 的 uniform_int_distribution 实现：

```c++
// https://github.com/llvm/llvm-project/blob/9b2dfff57a382b757c358b43ee1df7591cb480ee/libcxx/include/__random/uniform_int_distribution.h#L233-L257
typename uniform_int_distribution<_IntType>::result_type
uniform_int_distribution<_IntType>::operator()(_URNG& __g, const param_type& __p)
_LIBCPP_DISABLE_UBSAN_UNSIGNED_INTEGER_CHECK
{
    static_assert(__libcpp_random_is_valid_urng<_URNG>::value, "");
    typedef __conditional_t<sizeof(result_type) <= sizeof(uint32_t), uint32_t, __make_unsigned_t<result_type> >
        _UIntType;
    const _UIntType __rp = _UIntType(__p.b()) - _UIntType(__p.a()) + _UIntType(1);
    if (__rp == 1)
        return __p.a();
    const size_t __dt = numeric_limits<_UIntType>::digits;
    typedef __independent_bits_engine<_URNG, _UIntType> _Eng;
    if (__rp == 0)
        return static_cast<result_type>(_Eng(__g, __dt)());
    size_t __w = __dt - std::__countl_zero(__rp) - 1;
    if ((__rp & (numeric_limits<_UIntType>::max() >> (__dt - __w))) != 0)
        ++__w;
    _Eng __e(__g, __w);
    _UIntType __u;
    do
    {
        __u = __e();
    } while (__u >= __rp);
    return static_cast<result_type>(__u + __p.a());
}
```

可以看到，它的实现思路是，为了生成 `[a, b]` 之间的均匀整随机数，它先找一个比 `b-a` 大的二的幂，然后生成随机数，模这个二的幂，接着采用拒绝采样：如果采样得到的值大于 `b-a`，那就重新采样。

但是前面测试的代码中，正好区间的大小就是二的幂，那么向上取整到二的幂次的时候，相当于每次采样有一半的概率需要重试。这样需要重新生成随机数的次数很多，而且分支预测错误率也很高。@Harry-Chen 用 perf 测试得到的数据：

- branch-misses: 30% of all branches
- Top-down: 44.6% Bad Speculation

说明分支预测确实成为了瓶颈。那么 libstdc++ 是怎么实现的，为什么它没有这个问题？经过搜索，发现了一篇博客：[Doubling the speed of std::uniform_int_distribution in the GNU C++ library (libstdc++)](https://lemire.me/blog/2019/09/28/doubling-the-speed-of-stduniform_int_distribution-in-the-gnu-c-library/)：

论文 [Fast Random Integer Generation in an Interval](https://arxiv.org/abs/1805.10941) 提出了新的 uniform_int_distribution 实现，比原来的实现得到了两倍的性能提升，并且合并到了 [libstdc++ 的实现](https://gcc.gnu.org/git/?p=gcc.git;a=blobdiff;f=libstdc%2B%2B-v3/include/bits/uniform_int_dist.h;h=ecb8574864aee10b9ea164379fffef27c7bdb0df;hp=6e1e3d5fc5fe8f7f22e62a85b35dc8bfa4743372;hb=98c37d3bacbb2f8bbbe56ed53a9547d3be01b66b;hpb=6ce2cb116af6e0965ff0dd69e7fd1925cf5dc68c)当中。

所以到这里，问题就比较清晰了：libstdc++ 实现了更好的算法，同时 libc++ 的算法遇到了最坏情况，二者合起来，就观测到了巨大的性能差距。

如果把代码里 `DATA_R` 改成 `(1 << 23)-1`，那么 libc++ 算法的采样失败概率就会降到最小，此时的性能情况是：

- GCC-13 Homebrew: 253
- Apple Clang: 490

可见这里就是大概两倍的性能差距，这个差距就来源于 libstdc++ 实现的更好的采样算法。

解决方法就是，等 libc++ 也实现更好的算法，或者在需要用 uniform_int_distribution 的时候，避免链接 libc++，或者自己实现更好的算法。
