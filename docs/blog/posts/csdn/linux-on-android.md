---
layout: post
date: 2014-04-26
tags: [android,ubuntu,linuxonandroid]
categories:
    - csdn
title: Linux on Android 简单教程
---

迁移自本人在 CSDN 上的博客：https://blog.csdn.net/build7601/article/details/24544879

介绍：
Linux on Android，顾名思义，就是让你能在 Android 上跑 linux。。。。

步骤：
1.下载所需的文件：
项目主页为：tinyurl.com cn3lxgz
在这里举 Ubuntu 13.10 为例，下载 tinyurl.com lp7fqw4
Core 只有最基本的东西，没界面。。但是我的 sd 卡空间过小，只好用这个，
Small 就有界面了，Large 还有很多东东，具体看 tinyurl.com m5tdmkj 下面的 Readme

然后下载 Complete Linux Installer，这是用来启动 linux 的：
tinyurl.com mzsbud8

还要下载 VNCViewer（浏览 linux 桌面），终端模拟器

2.做好准备工作：
解压下载好的 zip，把里面的.img 解压出来。
安装好 Complete Linux Installer VNCViewer 终端模拟器到 android 上，把解压的.img 文件传到 sd 卡上，比如：
adb push ubuntu-13.10.CORE.ext2.img 你的 sd 卡路径

安装完是这个样子的：

![](/images/20140426171926125.png)

3.开始启动！
打开 Complete Linux Installer，
选择启动系统，点击右上角 Settings，选择添加：

![](/images/20140426172223984.png)

在名称输入你喜欢的名称，比如 ubuntu。
选择...，然后选择 sd 卡上的 img 文件。保存更改

选择你刚才创建的 ubuntu，点击启动 linux！

你会发现出现了一个终端模拟器有没有！！

![](/images/20140426172417015.png)

完成！你可以用 VNCViewer 去查看他的界面：
连接 localhost：5900。

![](/images/20140426172607765.png)

什么都没有，什么情况！？！？
因为我下载的是 Core 啊！什么都没有啊啊啊啊。。。。
如果下载的是别的，那估计已经有界面了。。

如果没法连接到，请在终端模拟器输入 vncserver 并回车，然后 VNC 连接 5901 端口即可！