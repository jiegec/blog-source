---
layout: post
date: 2017-10-30
tags: [tyche,oj,cpu,cpuid]
categories:
    - others
title: 用 CPUID 获取评测机器的 CPU
---

受[用 CPUID 检测各大 OJ 测评机所用的 CPU（以及日常黑 BZOJ）](https://zhuanlan.zhihu.com/p/28322626)的启发，我决定去测试一下徐老师自己写的 OJ（名为 Tyche）所跑的机器是什么 CPU。于是我改造一下代码，用以下代码测评：

```cpp
#include <stdint.h>
#include <iostream>
#include <time.h>
#include <cpuid.h>
#include <sys/time.h>
static void cpuid(uint32_t func, uint32_t sub, uint32_t data[4]) {
    __cpuid_count(func, sub, data[0], data[1], data[2], data[3]);
}
int main() {
    uint32_t data[4];
    char str[48];
    for(int i = 0; i < 3; ++i) {
        cpuid(0x80000002 + i, 0, data);
        for(int j = 0; j < 4; ++j)
            reinterpret_cast<uint32_t*>(str)[i * 4 + j] = data[j];
    }

    struct timeval stop, start;
    gettimeofday(&start, NULL);
    while(1) {
        gettimeofday(&stop, NULL);
        if(stop.tv_usec - start.tv_usec > (str[##EDITME##] - 32) * 10000)
            break;
    }
}
```

经过测试，```usleep()```和```clock()```都被封杀，但是```gettimeofday()```存活了下来。然后我就不断地```C-a```上面的```###EDITME###```，根据评测出来的时间推算出字符串，然后得到以下结果：

```
0 ~ 7 : PADDING
8 73 I
9 110 n
10 116 t
11 101 e
12 108 l
13 40 (
14 82 R
15 41 )
16 32 SPC
17 67 C
18 111 o
19 114 r
20 101 e
21 40 (
22 84 T
23 77 M
24 41 )
25 32 SPC
26 105 i
27 51 3
28 45 -
29 50 2
30 49 1
31 50 2
32 48 0
33 32 SPC
34 67 C
35 80 P
36 85 U
37 32 SPC
38 64 @
39 32 SPC
40 51 3
41 46 .
42 51 3
43 48 0
44 71 G
45 72 H
46 122 z
```

连起来就是[这个 CPU](https://ark.intel.com/zh-cn/products/53426/Intel-Core-i3-2120-Processor-3M-Cache-3_30-GHz)：

```
Intel(R) Core(TM) i3-2120 CPU @ 3.30GHz
```

相比之下，还是比 BZOJ 好哈哈哈（又黑 BZOJ）。后来有大神在群里建议，可以用字符串比较的方式，对了就让题目 AC，不对就 WA。这个方法更加适合手里已经知道了一些常见 CPUID 的返回字符串，这里就是这样。
