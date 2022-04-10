---
layout: post
date: 2014-07-06 16:34:44 +0800
tags: [java,android,libgdx,box2d]
category: csdn
title: 写了一个程序，分析各个源文件之间的include关系。
---

迁移自本人在 CSDN 上的博客：https://blog.csdn.net/build7601/article/details/37343993

![](/20140706162823328.png)

最左边是expat， 上面zlib，左下角mxml，中间最恶心的是lua，右边的是jpeg。

讲讲大概思路：

1.扫描源文件，这里判断最简单的#include，然后建立关系。

2.把这些作为一个个body加到box2d的世界里，让物理解决这一切！！

3.然后把有include关系的用一个distancejoint连接起来~你会发现他们就能保持一定距离了。但是！没有被连接的全都聚在一起，怎么办！

4.把距离近的，不和自己相连的（来个dfs）给个反方向的力！

5.好吧，这就是最终结果，有什么更好的方法？希望大家交流。

6.我不想开源，毕竟这还只是个半成品。。。。。做好了自然会开源的

7.像那个恶心的lua怎么解开？文件之间的依赖太多了，成环了。

8.使用java+libgdx+box2d写成，也就是说android也支持。

9.没啥了。。。。