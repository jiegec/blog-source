---
layout: post
date: 2026-11-03
tags: [linux,xrdp,x11,forwarding,rdp]
categories:
    - software
---

# 用 XRDP + X11 转发实现带音频的图形界面转发

## 背景

最近遇到一个需求，在机器 A 上跑一个图形界面程序，但因为是远程访问，所以传统的办法就是开个 X11 Forwarding，或者跑个 VNC/RDP Server。但我有音频转发的需求，本地是 macOS，又不好在机器 A 上装 XRDP+桌面环境，于是在机器 B 上跑 XRDP Server，在机器 A 上通过 X11 Forwarding + Unix Socket Forwarding 实现图形界面和音频在机器 B 上的播放，再通过 RDP 客户端在 macOS 上实现带音频的图形界面浏览。

<!-- more -->

## 具体实现方法

具体实现方法不难，主要是在机器 B 上做一些配置：

1. 安装 XRDP，配置桌面环境，我用的是 Xfce4
2. 安装 pipewire-module-xrdp，关闭 pulseaudio 服务，改为 pipewire + pipewire-pulse + wireplumber
3. 带 X11 Forwarding 连接到机器 A，同时通过 Unix Socket 转发 pulseaudio 的 Unix Socket：`DISPLAY=XRDP_DESKTOP_HERE ssh -X -Y -R /run/user/UID_A_HERE/pulse/native:/run/user/UID_B_HERE/pulse/native host_a`

然后在 SSH Session 里跑带图形界面的程序即可，它就会通过 ssh 转发的 X11 在 XRDP 的 DISPLAY 上显示，再通过 pulse/native 的 Unix Socket 播放音频。

最后，通过 RDP Client（Windows App）连接到机器 B，就可以在看到图形界面的同时，也有正确的音频了。
