---
layout: post
date: 2018-06-18 05:47:00 +0800
tags: [lineageos,archlinux,python2,angler]
category: programming
title: 在 ArchLinux 上编译 LineageOS for Huawei Angler
---

实践了一下如何在 ArchLinux 上编译自己的 LineageOS 。本文主要根据[官方文档](https://wiki.lineageos.org/devices/angler/build) 进行编写。

```shell
$ # for py2 virtualenv and running x86 prebuilt binaries(e.g. bison)
$ sudo pacman -Sy python2-virtualenv lib32-gcc-libs 
$ mkdir -p ~/bin
$ mkdir -p ~/virtualenv
$ # build script is written in python 2
$ cd ~/virtualenv
$ virtualenv2 -p /usr/bin/python2 py2
$ mkdir -p ~/android/lineage
$ curl https://storage.googleapis.com/git-repo-downloads/repo > ~/bin/repo
$ chmod a+x ~/bin/repo
$ vim ~/.config/fish/config.fish
set -x PATH ~/bin $PATH
set -x USE_CCACHE=1
$ exec fish -l
$ cd ~/android/lineage
$ repo init -u https://github.com/LineageOS/android.git -b lineage-15.1
$ # alternatively, follow https://mirrors.tuna.tsinghua.edu.cn/help/lineageOS/
$ repo sync
$ source ~/virtualenv/py2/bin/activate
$ source build/envsetup.sh
$ breakfast angler
$ vim ~/.config/fish/config.fish
$ ccache -M 50G
$ cd ~/android/lineage/device/huawei/angler
$ ./extract-files.sh
# Plug in Nexus 6P, maybe over ssh, see my another post
$ cd ~/android/lineage
$ croot
$ brunch angler
$ # Endless waiting... (for me, more than 2 hrs)
```
