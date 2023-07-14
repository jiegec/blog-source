---
layout: post
date: 2018-09-08
tags: [xcode,vim,xvim]
category: software
title: 在 Xcode 9 上启用 Vim 模拟（XVim 2） 
---

作为一个不用 vim 编辑会死星人，用 Xcode 总是止不住自己想 Escape 的心。于是找到了 [XVimProject/XVim2](https://github.com/XVimProject/XVim) 进行配置。

大致方法如下：

1. 按照 [Signing Xcode](https://github.com/XVimProject/XVim2/blob/master/SIGNING_Xcode.md) 对 Xcode 进行重签名。套路和对 GDB 进行签名一样。不过这次，签名完成的时间可长多了，毕竟 Xcode 这么大。
2. 接着按照项目的 README，首先 `git clone` 然后 `make` ，第一次打开 Xcode 的时候选择 `Load Bundle` 即可。

终于可以满足我 Escape Xcode 的欲望了。