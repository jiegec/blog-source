---
layout: post
date: 2018-07-12
tags: [debian,fcitx,googlepinyin,fbterm]
categories:
    - misc
title: 配置 fcitx-fbterm 实现在终端下显示和输入中文
---

参考网站：

[Ubuntu 使用 fbterm 无法打开 fb 设备的解决及 fcitx-fbterm 安装](https://www.linuxidc.com/Linux/2015-01/111976.htm)
[Fcitx - ArchWiki](https://wiki.archlinux.org/index.php/fcitx)
[完美中文 tty, fbterm+yong(小小输入法)](https://blog.csdn.net/guozhiyingguo/article/details/52852394)
[让 linux console 支持中文显示和 fcitx 输入法](http://www.voidcn.com/article/p-wrcgydjy-er.html)

考虑到 lemote yeeloong 机器的 cpu 运算性能，跑一个图形界面会非常卡，于是选择直接用 framebuffer。但是，显示中文又成了问题。于是，采用了 fbterm 和 fcitx 配合，加上 gdm 的方法，完成了终端下的中文输入。

首先，安装相关的包：
``` shell
$ sudo apt install gpm fcitx-fronend-fbterm dbus-x11 fbterm fonts-wqy-zenhei
```

接着，基于以上参考网站第一个，编写 zhterm 文件：
```shell
$ echo zhterm
#!/bin/bash
eval `dbus-launch --auto-syntax`
fcitx >/dev/null 2>&1
fbterm -i fcitx-fbterm
kill $DBUS_SESSION_BUS_PID
fcitx-remote -e
$ chmod +x zhterm
$ zhterm
# Use C-SPC to switch input source
```

另：找到一个[映射 Caps Lock 到 Escape 的方案](https://unix.stackexchange.com/a/7682/144358)：
```
$ sudo bash -c "dumpkeys | sed 's/CtrlL_Lock/Escape/' | loadkeys"
```
