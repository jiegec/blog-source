---
layout: post
date: 2017-10-17 16:46:40 +0800
tags: [vs,c,c++,cs]
category: programming
title: 关于scanf和scanf_s的问题
---

最近作为程设基础的小教员，收到很多同学的求助，关于`scanf`和`scanf_s`的问题已经遇到了两次，特此写一篇博文来叙述一下这个问题。

一开始，有同学问我，
```
char a;
scanf("%c",&a);
```
为什么会报错？我说，vs默认强制要求使用scanf_s函数，于是我建议这位同学把这个错误信息关掉了。嗯。经过百度，这位同学的问题解决了。

后来，又有一位同学问我，
```
char a;
scanf_s("%c",&a);
```
程序为什么会崩溃？我想了想，如果scanf_s和scanf是一样的行为，这段代码是没问题的。但scanf_s既然安全，必然是在字符串方面做了处理。这里的char*勉强也算一个？网上一查，果然，应该写成`scanf_s("%c",&a,1);`，字符串则要写成`scanf_s("%s",str,sizeof(str))`，来保证缓冲区不会溢出。

但是，这样解决这个问题又面临着不同的选择：

1. 学习`scanf_s`和`scanf`的不同，把所有`scanf`换成`scanf_s`并做相应的修改。
   这样当然符合了语言进化的潮流，也会让vs闭嘴。但是，scanf_s只有在C11标准中有，而且，根据[cpprefrence.com上关于scanf的描述](http://en.cppreference.com/w/c/io/fscanf)，只有在`__STDC_LIB_EXT1__`被定义且在`#include<stdio.h>`之前`#define __STDC_WANT_LIB_EXT1__`才能确保使用`scanf_s`能使用，当然在vs较新版本中是默认可以使用的。但是，程设基础的作业是要丢到oj上的，而oj上的编译器不一定支持这些，所以这个选项不行。
2. 坚持用`scanf`，自己按照题目要求保证缓冲区不溢出，同时让vs闭嘴。
   网上已有[教程](https://www.cnblogs.com/wangduo/p/5554465.html)，已经讲的很全面了，大家可以根据这个教程把vs教训一顿。为了能在oj里跑，建议用里面的方法五到八。（个人最推荐在文件头添加`#define _CRT_SECURE_NO_WARNINGS`）

以后再遇到这个问题，我就丢这个连接上来就好了咯。yeah！
