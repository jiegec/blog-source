---
layout: post
date: 2021-12-29
tags: [linux,nvidia,xrdp,rdp]
categories:
    - software
title: XRDP 和 NVIDIA 显卡兼容性问题
---

## 背景

最近在尝试配置 XRDP，发现它在有 NVIDIA 的机器上启动远程桌面后会黑屏，查看错误信息可以看到：

```
xf86OpenConsole: Cannot open virtual console 1 (Permission denied)
```

## 解决方法

XRDP 作者在 [issue #2010](https://github.com/neutrinolabs/xrdp/issues/2010#issuecomment-942561105) 中提到了解决方法：

修改 /etc/xrdp/sesman.ini，在 `[Xorg]` 部分里加上下面的配置：

```
param=-configdir
param=/
```

实际上就是不让 Xorg 加载 nvidia xorg 驱动，这样就绕过了问题。