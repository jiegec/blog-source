---
layout: post
date: 2018-01-30 16:05:33 +0800
tags: [VS,C,CS,C++]
category: programming
title: 再次吐槽 VS 关于 scanf 和 scanf_s 的问题
---

继[上次的吐槽](https://jiegec.github.io/programming/2017/10/17/on-scanf-and-scanf_s/)后，今天再次遇到同学因为 `scanf` 在 VS 下的 `deprecation error` 感到十分迷茫，在知乎上求助又因为拍照的原因被说，我就在此再次吐槽一下 VS 这对初学者很不友善很不友善的两点。

一点就是上面提到的这个，另一点就是程序结束后任意键以退出这一功能要做得更加醒目一点 。前者由于大多数新手在学习 `C/C++` 的时候都会跟着书上或者网上的代码敲一遍输入输出的代码，很容易就会撞到这个问题。后者则会让新手习惯性地以为程序闪退了，没有出结果，而不知道其实是程序执行结束后关闭而已。