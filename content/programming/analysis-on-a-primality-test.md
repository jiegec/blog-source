---
layout: post
date: 2017-10-17 21:05:28 +0800
tags: [cs,prime,algorithm]
category: programming
title: 分析一个我第一次见的素数测试函数
---

今天逛到这个[连接](http://blog.csdn.net/l04205613/article/details/6025118)，发现其中的第四种素数判定方法很有意思：

```
#include<stdio.h>
#include<math.h>
int p[8]={4,2,4,2,4,6,2,6};
int prime(int n)
{
    int i=7,j,q;
    if(n==1)return 0;
    if(n==2||n==5||n==3)return 1;
    if(n%2==0||n%3==0||n%5==0)return 0;
    q=(int)sqrt(n);
    for(;i<=q;){
        for(j=0;j<8;j++){
            if(n%i==0)return 0;
            i+=p[j];
        }
        if(n%i==0)return 0;
    }
    return 1;
}
void main()
{
    int n;
    scanf("%d",&n);
    if(prime(n))puts("Yes");
    else puts("No");
}
```

仔细研究发现，这里利用的是这样的原理：

1. 判断是不是1, 2, 3, 5及其倍数
2. 从7开始，不断考虑其是否是素数，那么，这个p是什么回事呢？

首先把p的各个元素加起来，和为30，然后就可以发现一个规律：
7为质数，7+2=9不是质数，7+4=11为质数，11+2=13为质数，13+2=15为合数，15+2=17为质数，17+2=19为质数，19+2=21为合数，21+2=23为质数，23+2=25为合数，25+2=27为合数，27+2=29为质数，29+1=31为质数，31+2=33为合数，33+2=35为合数，35+2=37为质数。
观察以上所有的合数，都含有2或者3或者5的因子，而30又是2,3,5的公倍数，也就是说，后面的素数模30的余数不可能是上面这些合数，而剩下的素数才可能是真正的素数，于是跳过了很多素数的判断。

至于这个函数的性能如何，还需要进一步测试来进行判断。
