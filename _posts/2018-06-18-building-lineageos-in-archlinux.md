---
layout: post
date: 2018-06-18 05:47:00 +0800
tags: [lineageos,archlinux,python2,angler]
category: programming
title: 在 ArchLinux 上编译 LineageOS for Huawei Angler
---

实践了一下如何在 ArchLinux 上编译自己的 LineageOS 。本文主要根据[官方文档](https://wiki.lineageos.org/devices/angler/build) 进行编写。

```shell
$ mkdir -p ~/bin
$ mkdir -p ~/android/lineage
$ curl https://storage.googleapis.com/git-repo-downloads/repo > ~/bin/repo
$ chmod a+x ~/bin/repo
$ vim ~/.config/fish/config.fish
set -x PATH ~/bin $PATH
$ exec fish -l
$ cd ~/android/lineage
$ repo init -u https://github.com/LineageOS/android.git -b lineage-15.1
$ repo sync
$ bash
$ source build/envsetup.sh
$ breakfast angler
$ vim ~/.config/fish/config.fish
set -x USE_CCACHE=1
$ ccache -M 50G
$ cd ~/android/lineage/device/huawei/angler
$ ./extract-files.sh
# Plug in your Nexus 6P
$ cd ~/android/lineage
$ virtualenv2 venv
$ source venv/bin/activate
$ croot
$ brunch angler
```

然而，出现了 flex 版本不兼容的问题，正在研究解决中。。
