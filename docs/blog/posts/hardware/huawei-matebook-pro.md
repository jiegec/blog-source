---
layout: post
date: 2025-06-06
tags: [huawei,arm64,matebook,matebookpro,harmonyos]
categories:
    - hardware
---

# 鸿蒙电脑 MateBook Pro 开箱体验

## 购买

2025.6.6 号正式开卖，当华为线上商城显示没货的时候，果断去线下门店买了一台回来。购买的是 32GB 内存，1TB SSD 存储，加柔光屏的版本，型号 HAD-W32，原价 9999，国补后 7999。

<!-- more -->

## 开箱

由于用了国补，需要当面激活，就在店里直接激活了，所以没有体验到鸿蒙系统的扫码激活功能，有点可惜。激活前的第一次开机需要插电，直接按电源键是没有反应的。激活过程也很简单，联网，创建用户，登录华为账号，输入指纹，就可以了。包装盒里还有 140W 单口 Type-C 电源适配器，体积挺小的。此外附赠了一条 Type-C to Type-C 的线，还有一个 Type-C 有线耳机，外加一个 Type-A 母口加 Type-C 公口的线，可以用来接 Type-A 公口的外设。此外还有快速指南和一个超纤抛光布。店家还贴心地提供了一个虚拟机的安装教程。

外形上，就是 MateBook X Pro 加了一个 HarmonyOS 的标识，上手很轻，不愧是不到一公斤的笔记本，对于习惯用 MacBookAir 轻薄本的我来说，是很大的一个亮点。不像 MacBookAir，这台鸿蒙电脑有风扇，有点小小的不习惯，但还算安静。

## 系统体验

预装的版本是 HarmonyOS 5.0.1.305，有更新 5.0.1.310 SP9，首先更新了一下系统。这是我的第一台支持触屏的笔记本，所以用起来还有点新奇。这个柔光屏用起来触感不错，和之前买的柔光屏 MatePad 的触感类似。

底部状态栏的颜色会随着情况变化，比如在桌面的时候，默认壁纸是黑色的，状态栏也就是黑色的。如果打开了设置，设置是白色的，状态栏也就是白色的。之后可以多测试一下它具体的变色逻辑。

系统里预装了 WPS Office，迅雷，亿图，中望 CAD，剪映，好压，抖音等，面向的客户群体很显然了。虽然预装，但都可以卸载。

内置了控制手机屏幕的功能，有略微的不跟手，但由于电脑本身也是触屏，所以体验还是和手机很接近的。下方是经典的三个按钮。这个协同，可以电脑和手机同时操作，还是挺好的，不会说电脑控制了手机，手机就不能用的情况。手机界面左上角会提示协同中。键鼠共享功能不错，可以把手机当屏幕，然后用电脑的键盘和触摸板控制，外接的鼠标也可以。

触摸板手势方面，可以在设置里修改，比如菜单弹出改成双指点按或轻点。触摸板的手感比苹果还是有一定的差距，但是屏幕触摸弥补了这个问题。没有找到三指拖拽的手势，它用的是类似 Windows 的轻点两次，第二次不抬起的做法。

## 应用体验

目前（2025 年 6 月 6 日）应用商城有这些软件：

- Bilibili
- 飞书
- 钉钉
- QQ（在应用尝鲜内）
- CodeArts IDE（在应用尝鲜内，需要开发者模式）

暂时还没有微信，可以通过操控手机来发微信，但是在消息栏里按回车是换行，没找到发送按钮对应的电脑按键，需要手动操。但是居然有企业微信。

支持应用接续，在手机上播放的 B 站视频，可以在电脑上接续继续看。

期待一个功能，当电脑上出现需要扫的二维码的时候，可以通过协同功能，不用操作手机，让手机直接扫电脑的屏幕。不过反过来，如果电脑上有需要输入手机短信验证码的场景，就已经很方便了。

## 开发者模式

开发者模式的打开方式和手机上一样，在设置里狂点软件版本。自带了一个 Terminal App，会提示你如何打开开发者模式。

打开以后就可以访问终端了。shell 是用的 toybox。df 如下：

```shell
$ df -h
Filesystem                                            Size  Used Avail Use% Mounted on
tmpfs                                                  16G   52K   16G   1% /
tmpfs                                                  16G     0   16G   0% /storage/hmdfs
/dev/block/dm-4                                       5.7M  5.7M     0 100% /cust
/dev/block/dm-6                                       3.1G  3.1G     0 100% /preload
/dev/block/dm-0                                       3.0G  3.0G     0 100% /system/variant
/dev/block/dm-5                                       8.0K  8.0K     0 100% /version
/dev/block/platform/b0000000.hi_pcie/by-name/userdata 928G   59G  869G   7% /data/service/hnp
tmpfs                                                  16G     0   16G   0% /module_update
/dev/block/dm-2                                       9.3G  8.1G  1.1G  88% /sys_prod
devfs                                                  15G  104M   15G   1% /dev
/data/service/el2/100/hmdfs/non_account               928G   59G  869G   7% /mnt/hmdfs/100/non_account
/dev/block/loop0                                      114M  112M     0 100% /module_update/ArkWebCore
tmpfs                                                 1.0G  608K  0.9G   1% /dev/shm
```

查看 [`/proc/cpuinfo`](./huawei-matebook-pro-cpuinfo.txt)。四个 0xd42，八个 0xd43，八个 0xd03，共 20 个逻辑核。

试了一下 CodeArts IDE，显示支持 Java 和 Python 开发，UI 上有点像 JetBrains，但应该是基于 VSCode 做的二次开发。实际测了一下，用它创建 Python 项目后，可以在 CodeArts IDE 的命令行里用 Python3：

```shell
$ pwd
/storage/Users/currentUser/IDEProjects/pythonProject
$ python3 main.py
Hello World!
$ which python3
/storage/Users/currentUser/IDEProjects/pythonProject/venv/bin/python3o
$ /data/app/bin/python --version
Python 3.12.5
```

看了看 `/data/app/bin` 目录，下面有 git，python，unzip, vi，rg，java（bisheng jdk 8/17），ssh，electron（用来跑 LSP！）等等。

试了试 pip，也是工作的：

```shell
(venv) $ python3 -m pip install requests
(venv) $ python3
Python 3.12.5 (main, Aug 28 2024, 01:18:17) [Clang 15.0.4 (llvm-project 81cdec3cd117b1e6e3a9f1ebc4695d790c978463)] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import requests
>>> requests.get("https://github.com").status_code
200
>>> 
```

## 外设

把 Type-C Hub 接到 MateBook Pro 上，显示器，键盘鼠标都正常工作了。

## 未完待续