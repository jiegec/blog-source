---
layout: post
date: 2018-05-11
tags: [linux,x11,display,xauthority,awk,perl]
category: programming
title: 在脚本中寻找 X11 的 DISPLAY 和 XAUTHORITY
---

之前在搞一个小工具，在里面需要访问 X11 server，但是访问 X11 server 我们需要两个东西：DISPLAY 和 XAUTHORITY 两个环境变量。但是，由于它们在不同的发型版和 Display Manager 下都有些不同，所以花了不少功夫才写了一些。

为了验证我们是否可以连上 X11 server，我们使用这一句：
```bash
DIMENSIONS=$(xdpyinfo | grep 'dimensions:' | awk '{print $2;exit}')
```

它尝试打开当前的 DISPLAY，并且输出它的分辨率。接下来，我对不同的一些发型版，综合网上的方法，尝试去找到正确的环境变量。

对于 Debian:
```bash
DISPLAY=$(w -hs | awk -v tty="$(cat /sys/class/tty/tty0/active)" '$2 == tty && $3 != "-" {print $3; exit}')
USER=$(w -hs | awk -v tty="$(cat /sys/class/tty/tty0/active)" '$2 == tty && $3 != "-" {print $1; exit}')
eval XAUTHORITY=~$USER/.Xauthority
export DISPLAY
export XAUTHORITY
DIMENSIONS=$(xdpyinfo | grep 'dimensions:' | awk '{print $2;exit}')
```

对于 Archlinux：
```bash
DISPLAY=$(w -hs | awk 'match($2, /:[0-9]+/) {print $2; exit}')
USER=$(w -hs | awk 'match($2, /:[0-9]+/) {print $1; exit}')
eval XAUTHORITY=/run/user/$(id -u $USER)/gdm/Xauthority
export DISPLAY
export XAUTHORITY
DIMENSIONS=$(xdpyinfo | grep 'dimensions:' | awk '{print $2;exit}')
```

最后一种情况很粗暴的，直接找进程拿：
```bash
XAUTHORITY=$(ps a | awk 'match($0, /Xorg/) {print $0; exit}' | perl -n -e '/Xorg.*\s-auth\s([^\s]+)\s/ && print $1')
PID=$(ps a | awk 'match($0, /Xorg/) {print $1; exit}')
DISPLAY=$(lsof -p $PID | awk 'match($9, /^\/tmp\/\.X11-unix\/X[0-9]+$/) {sub("/tmp/.X11-unix/X",":",$9); print $9; exit}')
export DISPLAY
export XAUTHORITY
DIMENSIONS=$(xdpyinfo | grep 'dimensions:' | awk '{print $2;exit}')
```

中间混用了大量的 awk perl 代码，就差 sed 了。牺牲了一点可读性，但是开发起来比较轻松。
