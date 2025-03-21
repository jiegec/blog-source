---
layout: post
date: 2014-09-20
tags: [math,wolframalpha]
categories:
    - csdn
---

# 用数学方法 + 数学软件去做一个物理题~

迁移自本人在 CSDN 上的博客：https://blog.csdn.net/build7601/article/details/39433177

经过测试，发现微信客户端登录 SDK 有一个 BUG。注：目前只在 iOS 上测试过，可以重现。

原题：

跳伞运动员在下落过程中，假定伞所受空气阻力大小跟下落速度的平方成正比，即 F= kv2，比例系数 k=20N·s2/m2，跳伞运动员与伞的总质量为 72 kg，起跳高度足够高，则：（g 取 10 m/s2） 

1. 跳伞运动员在空中做什么运动？收尾速度多大？ 
2. 当速度达到 4 m/s 时，下落加速度是多大？

做法：

我拿出我的数学大杀器，直接受力分析 + 牛顿第二定律得出 a=g-k/m*v*v.
我一看，这转化成数学不就是 f''(t)=10-5/18*f'(t)^2, f(0)=0, f'(0)=0，喜闻乐见的微分方程啊哈哈！

直接丢到各种数学软件，我用了[Wolfram|Alpha](http://www.wolframalpha.com/input/?i=f%27%27%28t%29%3D10-5%2F18*f%27%28t%29%5E2%2C+f%280%29%3D0%2C+f%27%280%29%3D0)

瞬间得到答案：
f(t) = -6/5 (5 t-3 log(e^(10 t/3)+1)+log(8))
yeah~

看看上面那个网址里面下面的函数图像，表示第一题可以秒杀~

好的，至于第二题，因为速度为 4，则可以写出：f'(t)=4 的方程，输入 d(-6/5 (5 t-3 log(e^(10 t/3)+1)+log(8)))/dt=4
解出
t = (3 log(5))/10
带入 f''(t)，输入 diff(diff(-6/5 (5 t-3 log(e^(10 t/3)+1)+log(8)),t),t),t=(3 log(5))/10，
得 a=5.5556.

大功造成~