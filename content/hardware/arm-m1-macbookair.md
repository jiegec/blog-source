---
layout: post
date: 2020-11-19 18:35:00 +0800
tags: [m1,macbookair,applesilicon,macos,arm,arm64]
category: hardware
title: ARM M1 MacBook Air 开箱
---

# 购买

我是 11.12 的时候在 Apple Store 上下单的，选的是 MacBookAir ，带 M1 芯片，8 核 CPU + 8 核 GPU，加了一些内存和硬盘。今天（11.19）的时候顺丰到货，比 Apple Store 上显示的预计到达时间 21-28 号要更早。另外，我也听朋友说现在一些线下的店也有货，也有朋友直接在京东上买到了 Mac mini，总之第一波 M1 的用户最近应该都可以拿到设备了。

现在这篇博客，就是在 ARM MBA 上编写的，使用的是 Intel 的 VSCode，毕竟 VSCode 的 ARM64 版不久后才正式发布。

# 开箱

从外观来看，一切都和 Intel MBA 一样，包装上也看不出区别，模具也是一样的。

![](/arm_mac_1.png)

进了系统才能看得出区别。预装的系统是 macOS Big Sur 11.0，之后手动更新到了目前最新的 11.0.1。

顺带 @FactorialN 同学提醒我在这里提一句：包装里有电源适配器，不太环保。

# 体验

## ARM64

首先自然是传统艺能，证明一下确实是 Apple Silicon：

```shell
$ uname -a
Darwin macbookair.lan 20.1.0 Darwin Kernel Version 20.1.0: Sat Oct 31 00:07:10 PDT 2020; root:xnu-7195.50.7~2/RELEASE_ARM64_T8101 x86_64
```

啊对不起我用错了，上面是在 Rosetta 里面跑的 shell 看到的结果。实际是这样子的：

```shell
$ uname -a
Darwin macbookair.lan 20.1.0 Darwin Kernel Version 20.1.0: Sat Oct 31 00:07:10 PDT 2020; root:xnu-7195.50.7~2/RELEASE_ARM64_T8101 arm64
```

货真价实的 ARM64 内核，系统的很多 binary 也都是 Universal 的：

```shell
$ file /bin/bash
/bin/bash: Mach-O universal binary with 2 architectures: [x86_64:Mach-O 64-bit executable x86_64] [arm64e:Mach-O 64-bit executable arm64e]
/bin/bash (for architecture x86_64):	Mach-O 64-bit executable x86_64
/bin/bash (for architecture arm64e):	Mach-O 64-bit executable arm64e
```

## Rosetta

接着，就是重头戏 Rosetta 了。第一次打开 Intel 的程序的时候，会弹出窗口安装 Rosetta，确定以后立马就装好了。接着常用的各种软件啥的，都没有什么问题。

唯一能看出区别的，就是在 Activity Monitor 可以看到架构的区别：

![](/arm_mac_2.png)

实际体验的时候，其实没有什么感觉。默认情况下，在 Terminal 下打开的是 ARM64 架构的，如果要切换的话，只需要：

```shell
$ uname -m
arm64
$ arch -arch x86_64 uname -m
x86_64
```

这样就可以了。如果开了一个 x86_64 的 shell，在 shell 里面执行的命令就都是 x86_64 架构的了。

## Homebrew

目前，Homebrew 的支持是这样子的，Intel 的 Homebrew 工作很正常，没有遇到任何问题。。ARM 的 Homebrew 目前还在进行移植，由于官方的 build farm 还没有支持 ARM，所以各种包都需要自己编译，试了几个常用的软件都没问题。

目前 Homebrew 推荐的方法是，在老地方 `/usr/local/Homebrew` 下面放 Intel 的 Homebrew，在 `/opt/homebrew` 下面放 ARM 的 Homebrew。虽然还是有很多警告，但目前来看基本使用都没有什么问题。Homebrew cask 也正常，毕竟基本就是一个下载器。

另外，试了一下用 ARM Homebrew 从源码编译 GCC，编译中途失败了。

## 其他软件

换到 ARM 上自然会想到，之前的那些软件还能不能跑。答案是，大多都可以，只是很多还是 Intel 版走翻译而已。

目前已经测试过正常使用的：VSCode、Google Chrome、Alacrity、iStat Menus、Alfred、Rectangle、Typora、Microsoft Office、Karabiner Elements、Jetbrains Toolbox、WeChat、CineBench、Dozer、Squirrel、Zoom、Tencent Meeting、Seafile、Skim、Mendeley、1 Password。

这些里面已经移植到 ARM64 的有 Alfred、iStat Menus、Karabiner Elements、Rectangle、Google Chrome。

这里有一部分是已经移植到 ARM64 的，有一些也很快就会移植过来。其中 iStat Menus 的电池健康显示有点 BUG，其他没发现问题。

另外，大家也知道 ARM Mac 很重要的一点是可以跑 iOS Apps，我们也确实跑了一些，不过都有一些问题：

- Doodle Jump：跑起来很正常，就是卡关了，别问为什么，没有加速度计，再怎么晃电脑也不会动
- Bilibili：部分内容可以加载出来，部分不可以，估计是什么组件没有配置好
- QQ Music：可以跑起来，但是在启动之后的引导页面，期望用户点一下屏幕，但怎么用鼠标点都没反应
- Weibo：毕竟正常，可以正常浏览啥都，就是 UI 有点错位，估计是因为显示窗口和实际都不大一样，小问题。
- Network Tools：很正常，各种网络信息都可以正常取出来。
- NFSee：没有 NFC 读卡功能，自然没法用。
- 彩云天气（ColorfulClouds Weather）：正常使用。

其他还有很多 App 还没有测试。

## 发热

大家也知道，这款 MBA 是没有风扇的。但我实际测试的过程中发现，确实不大需要。拿 stress 跑了一段时间 CPU 满载运行，也没感觉到电脑发热，只是在更新 macOS Big Sur 11.0.1 的时候稍微热了一点点，也只是一点点，距离烫手还有很长的距离。

续航方面目前来看也挺好的，捣鼓了一个下午，也没耗多少电。

## 总结

总的来说，还是挺香的。不错的性能，没有风扇的喧闹，没有烫手的键盘。可能有少部分软件还不能正常运行，然后很多程序还需要 Rosetta 翻译，但目前来看兼容性还是挺不错的，并且这些应该明年就都适配地差不多了吧。