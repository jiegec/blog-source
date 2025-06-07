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

规格如下：

- 970g 重量
- 14.2 寸显示器
- 3120x2080 分辨率，120 Hz 刷新率
- 1.8mm 键程键盘
- 70 Wh 电池

## 系统体验

预装的版本是 HarmonyOS 5.0.1.305，有更新 5.0.1.310 SP9，首先更新了一下系统。这是我的第一台支持触屏的笔记本，所以用起来还有点新奇。这个柔光屏用起来触感不错，和之前买的柔光屏 MatePad 的触感类似。

底部状态栏的颜色会随着情况变化，比如在桌面的时候，默认壁纸是黑色的，状态栏也就是黑色的。如果打开了设置，设置是白色的，状态栏也就是白色的。之后可以多测试一下它具体的变色逻辑。

系统里预装了 WPS Office，迅雷，亿图，中望 CAD，剪映，好压，抖音等，面向的客户群体很显然了。虽然预装，但都可以卸载。

内置了控制手机屏幕的功能，有略微的不跟手，但由于电脑本身也是触屏，所以体验还是和手机很接近的。下方是经典的三个按钮。这个协同，可以电脑和手机同时操作，还是挺好的，不会说电脑控制了手机，手机就不能用的情况。手机界面左上角会提示协同中。键鼠共享功能不错，可以把手机当屏幕，然后用电脑的键盘和触摸板控制，外接的鼠标也可以。

触摸板手势方面，可以在设置里修改，比如菜单弹出改成双指点按或轻点。触摸板的手感比苹果还是有一定的差距，但是屏幕触摸弥补了这个问题。没有找到三指拖拽的手势，它用的是类似 Windows 的轻点两次，第二次不抬起的做法。

屏幕分辨率 2080 x 3120，14.2 英寸。

## 应用体验

目前（2025 年 6 月 6 日）应用商城有这些软件：

- Bilibili
- 飞书
- 钉钉
- 腾讯会议
- QQ（在应用尝鲜内）
- CodeArts IDE（在应用尝鲜内，需要开发者模式）

暂时还没有微信，可以通过操控手机来发微信，但是在消息栏里按回车是换行，没找到发送按钮对应的电脑按键，需要手动操。但是居然有企业微信。

支持应用接续，在手机上播放的 B 站视频，可以在电脑上接续继续看。

期待一个功能，当电脑上出现需要扫的二维码的时候，可以通过协同功能，不用操作手机，让手机直接扫电脑的屏幕。不过反过来，如果电脑上有需要输入手机短信验证码的场景，就已经很方便了。

试了一下腾讯会议，声音，视频，共享屏幕都是正常工作的。但是共享的屏幕只有笔记本自己的屏幕，还不能选取共享哪个屏幕的内容，也不能选取共享哪个窗口。

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

查看 [`/proc/cpuinfo`](./huawei-matebook-pro-cpuinfo.txt)。四个 0xd42（2.0 GHz），八个 0xd43（2.0 GHz），八个 0xd03（2.3 GHz），共 20 个逻辑核。从 part id 来看，0xd03 和 0xd42 对应麒麟 9010 的大核和中核，但 0xd43 是新的 part id。

使用 <https://github.com/jiegec/SPECCPU2017Harmony> 性能测试：

- X90 P-Core 2.3 GHz 0xd03 Full: INT 4.87 FP 7.42
- X90 E-Core 2.0 GHz 0xd43 Full: INT 4.28 FP 6.52
- X90 LPE-Core 2.0 GHz 0xd42 Full: INT 3.25 FP TODO
- 9010 P-Core 2.3 GHz 0xd03 Best: INT 4.18 FP 6.22
- 9010 P-Core 2.3 GHz 0xd03 Full: INT 3.96 FP 5.86
- 9010 E-Core 2.2 GHz 0xd42 Full: INT 3.21 FP 4.72

详细数据： <https://github.com/jiegec/SPECCPU2017Harmony/tree/master/results>。Best 代表每一项单独跑，散热条件好，Full 代表顺着跑一遍，散热条件差。由于编译器和编译选项不同，不能和在其他平台上跑的 SPEC CPU 2017 成绩直接对比，仅供参考。

大概性能排序：X90 P-Core > X90 E-Core > 9010 P-Core > X90 LPE-Core > 9010 E-Core > 9010 LPE-Core。

即使是同样的 2.3 GHz 0xd03 的核，X90 比 9010 快上 20%：可能是散热问题，或者缓存大小和内存带宽的问题，或许连微架构都是不一样的，这些都需要后续进一步测试。而 X90 的中核也比 9010 的大核要快。

### CodeArts IDE

试了一下从应用商城安装的 CodeArts IDE，显示支持 Java 和 Python 开发，UI 上有点像 JetBrains，但应该是基于 VSCode 做的二次开发。实际测了一下，用它创建 Python 项目后，可以在 CodeArts IDE 的命令行里用 Python3：

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

这里的 `/storage/Users/currentUser/` 就是 HOME 目录，对应文件管理器的个人目录。

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

需要 native 编译的库，比如 numpy 还不行，会提示找不到 make。

终端里的 ssh 是可以用的，实测 ssh 到远程的 linux 上是没问题的。

终端里的括号补全有一些问题，等待修复。CodeArts IDE 的 Python 单步调试功能也是工作的。

似乎没有安装 Remote 开发的插件，也没有安装插件的菜单。

既然可以跑 shell，意味着可以 execve 了，意味着可以做 termux 的类似物了。期待鸿蒙 5 上早日有 Termux 用，直接跑 Linux 发行版。实际测了一下，Popen 确实是工作的。

UPDATE: 开了个坑：<https://github.com/jiegec/Termony>，目前已经能跑 busybox.static 了，虽然还有一些问题。

试了一下 HOME 目录，发现它里面不能有可执行的文件，所以可能还是得打包到一个 App 里面，通过 `/data/app/bin` 类似的路径来访问。

在 CodeArts IDE 里，可以访问 /data/storage/el1/bundle 目录，里面有一个 pc_entry.hap 文件，可以通过 `cat /data/storage/el1/bundle/pc_entry.hap | ssh hostname "cat - > pc_entry.hap"` 拷贝到其他机器上。这个文件有 1.9GB，可以看到在 `/data/app` 下面的各种文件，其实是来自于这个 `pc_entry.hap` 的 `hnp/arm64-v8a` 下面的一系列文件，例如 `git.hnp` 就是一个 zip 压缩包，里面就是 `/data/app/git.org/git_1.2` 目录的内容，这个东西叫做 `应用包内 Native 包（.hnp）`。这些文件在 module.json 里声明，对应 [hnpPackages 标签](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/module-configuration-file#hnppackages%E6%A0%87%E7%AD%BE)：

```json
{
  "module": {
    "hnpPackages": [
      {
        "package": "electron.hnp",
        "type": "private"
      },
      {
        "package": "huaweicloud-smartassist-java-ls.hnp",
        "type": "private"
      },
      {
        "package": "bishengjdk8.hnp",
        "type": "private"
      },
      {
        "package": "rg.hnp",
        "type": "private"
      },
      {
        "package": "unzip.hnp",
        "type": "private"
      },
      {
        "package": "git.hnp",
        "type": "private"
      },
      {
        "package": "bishengjdk17.hnp",
        "type": "private"
      },
      {
        "package": "python.hnp",
        "type": "private"
      }
    ],
    "name": "pc_entry",
    "packageName": "pc_entry"
  }
}
```

解压 `git.hnp` 后，里面的文件会被复制到 `/data/app/git.org/git_1.2` 目录下，然后有一个 `hnp.json` 指定了在 `/data/app/bin` 创建哪些文件的软连接，比如：

```json
{
    "install": {
        "links": [
            {
                "source": "bin/expr",
                "target": "expr"
            },
            {
                "source": "bin/git",
                "target": "git"
            }
        ]
    },
    "name": "git",
    "type": "hnp-config",
    "version": "1.2"
}
```

在 HarmonyOS SDK 里，有一个 hnpcli，可以用来生成 .hnp 文件。

除此之外，就是 VSCode 加各种插件了。

鸿蒙电脑上，可以访问各个 App 的内部目录了，无论是自带的文件浏览器，还是通过 DevEco Studio。这给调试带来了很多便利。

## 虚拟机

目前应用商城有两家虚拟机：Oseasy 和铠大师。两者都是提示安装 ARM64 版本的 Windows，尝试了一下给它一个 Debian 的安装 ISO，它不认。用的 unattended install，不需要进行什么操作。Oseasy 和铠大师的虚拟机不能同时开，但是可以一边安装完，再去安装另一边的 Windows。

试了试在虚拟机里装 WSL，说没有硬件虚拟化，大概是没有打开嵌套虚拟化的功能。

在 6 核虚拟机里运行 ARM64 Geekbench 6：[Single-Core 1436, Multi-Core 5296](https://browser.geekbench.com/v6/cpu/12309313)。8 核：[Single-Core 1462, Multi-Core 7043](https://browser.geekbench.com/v6/cpu/12309427)。算上剩下的 12 个逻辑核，考虑虚拟化的开销，多核分数达到网传的 11640 分，感觉是可能的。 

Oseasy 虚拟机只允许开到 8 个核心，估计是避免用到八个 0xD03 以外的核心吧，毕竟 Windows 的大小核调度不太好，但是这样剩下的核就测不出来性能了。

## 外设

把 Type-C Hub 接到 MateBook Pro 上，显示器，键盘鼠标都正常工作了。

## 侧载

打开开发者模式后，在设置里，可以打开 USB 调试：把电脑右边的 USB Type-C 接到另一台电脑上，就可以用 hdc 连接了。

然后给自己的项目加上 2in1 的 device type：

```
diff --git a/entry/build-profile.json5 b/entry/build-profile.json5
index 38bdcc9..ad6fd45 100644
--- a/entry/build-profile.json5
+++ b/entry/build-profile.json5
@@ -30,7 +30,13 @@
   ],
   "targets": [
     {
-      "name": "default"
+      "name": "default",
+      "config": {
+        "deviceType": [
+          "default",
+          "2in1"
+        ]
+      }
     },
     {
       "name": "ohosTest",
diff --git a/entry/src/main/module.json5 b/entry/src/main/module.json5
index 7b8532f..76c009c 100644
--- a/entry/src/main/module.json5
+++ b/entry/src/main/module.json5
@@ -5,7 +5,8 @@
     "description": "$string:module_desc",
     "mainElement": "EntryAbility",
     "deviceTypes": [
-      "default"
+      "default",
+      "2in1"
     ],
     "requestPermissions": [
       {
```

就可以在鸿蒙电脑上跑了。我编写的两个鸿蒙上的应用：<https://github.com/jiegec/SPECCPU2017Harmony> 和 <https://github.com/jiegec/NetworkToolsHarmony> 都能正常在 MateBook Pro 上运行。

测试的过程中，发现用 hdc 传文件到电脑比传手机更快：Pura 70 Pro+ 是 24 MB/s，MateBook Pro 是 31 MB/s。

开源的鸿蒙应用也可以编译+运行：

- <https://gitee.com/smdsbz/moonlight-ohos>

目前还没找到怎么让鸿蒙电脑自己调试自己。

## 未完待续
