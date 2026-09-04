---
layout: post
date: 2026-09-04
tags: [windows]
categories:
    - software
---

# 记一次 Windows 更新 0x800703F1 错误的修复

## 背景

最近在准备课堂展示，需要用到 Windows，于是翻出鸿蒙电脑，跑起了 Windows on ARM 虚拟机。结果 Windows 更新老是报 0x800703F1 错误，我做了不少自己都说不清的尝试，最后稀里糊涂地解决了。

<!-- more -->

## 现象

现象是，Windows 更新界面里所有更新一律失败，统一报错 0x800703F1。上网搜了一圈，网上信息基本都指向注册表损坏，例如运行下面这条命令时同样会报错：

```
reg load HKLM\COMPONENTS C:\Windows\System32\config\components
```

## 失败的尝试

参考了网上的大量资料（[[1]](https://gist.github.com/74Thirsty/18e2b9152c0ca3a2f5d76dcd1b5d6ff4)、[[2]](https://www.reddit.com/r/WindowsHelp/comments/1k6aktc/error_0x800703f1_code_how_to_fix/)），各种方法都试了一遍，无一成功：

- `sfc /scannow` 和 `DISM /Online /Cleanup-Image /RestoreHealth` 都跑过，修复时仍报同样的 0x800703F1 错误。
- `sysnative component scanner` 跑了一段输出后就卡住不动，不知道在干什么。
- 下载了新的 Windows 11 on ARM ISO，选择保留数据重装，结果还是报 0x800703F1。

## 成功的尝试

最后抱着试试看的心态，采用了 [Reddit](https://www.reddit.com/r/WindowsHelp/comments/1k6aktc/error_0x800703f1_code_how_to_fix/) 上这个方案：

```
-TekkieBoy-

Hi,

try the SequenceNumberChecker from there:

https://github.com/MOV-EDX/SequenceNumberChecker/releases/tag/1.0.1

Copy the drivers hive from the path:

C:\Windows\System32\config

on your desktop.

Create a copy from your drivers hive as backup and save it on a safe place.

Then drag and drop the damaged drivers hive on the SequenceNumberChecker tool.

The tool should then start and try’s to repair the hive.

When you see the message:

    Repairs have completed...press any key to exit

Do it and then copy the repaired hive back in the config folder.
```

我把其中的 drivers 换成 components（我的 drivers 没坏，坏的是 components），之后 Windows 更新忽然就恢复正常了。看了看这个程序的源码，就是强制把 sequence number 改了，但这真的是合理的修复吗，不会产生新的数据不一致问题吗？问题是没了，但是我并没有得到彻底解决问题的安全感。

## 感想

每次修 Windows，都让我觉得整个过程稀里糊涂。看到一个报错，搜索一番，得到一大堆可能的修复方法，只能一个个试：修不好不知道原因，修好了也不知道原因。Windows 是闭源的，我看不到源码，不知道背后到底发生了什么；要是在 Linux 上，我早就翻源码去调试了。而且我也没有在 Windows 里配置 Agent，没法让 AI 现场反编译 Windows 程序，搞清楚这个报错到底从哪来。说到底就是稀里糊涂，不想用 Windows。
