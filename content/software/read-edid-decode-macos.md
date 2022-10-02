---
layout: post
date: 2019-08-14 20:39:00 +0800
tags: [macos,edid]
category: software
title: macOS 下读取并解析 EDID
---

之前听说了 EDID 的存在，但是一直没有细究里面的格式和内容。今天了解了一下，发现其实非常简单，下面是方法：

首先获取所有显示器输出的 EDID：

```bash
ioreg -lw0 | grep IODisplayEDID
```

输出里会出现 "IODisplayEDID" = <00ffxxxxxxxxxxxxx> 的内容，尖括号内的就是 EDID 的内容。接着，我们采用 [edid-decode](https://git.linuxtv.org/edid-decode.git/) 进行解析：

```bash
git clone git://linuxtv.org/edid-decode.git
cd edid-decode
make
./edid-decode
<Paste EDID here>
```

就可以看到很详细的 EDID 数据解析了。

ref: https://gist.github.com/OneSadCookie/641549 https://www.avsforum.com/forum/115-htpc-mac-chat/1466910-ability-dump-display-s-edid-mac.html