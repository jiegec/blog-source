---
layout: post
date: 2018-12-06
tags: [010editor,macos,parser,binary,hex,flv,h264,avc]
category: software
title: 编写 010 Editor 的 FLV Template
---

最近在做 FLV 和 H264 方面的研究，研究了很多标准和文档，然后用 010 Editor 对着文件进行分析。这个软件真的很好用，对研究二进制结构用处特别大。不过它自带的 FLV.bt 功能不是很好，我对它加上了 H264(AVC) 的部分支持，放在了 [myFLV.bt](https://github.com/jiegec/tools/blob/master/myFLV.bt) 里。我也写了 H264 的解析，不过效率不高，大文件要卡好一会。

除此之外，很多格式，010 editor 都有支持，特别好用，它的解析器语法也很好写。