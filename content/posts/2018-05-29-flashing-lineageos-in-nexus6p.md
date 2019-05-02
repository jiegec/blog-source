---
layout: post
date: 2018-05-29 07:18:00 +0800
tags: [android,nexus6p,huawei,angler,lineageos]
category: phone
title: 向 Nexus 6P 中刷入 LineageOS 实践
---

Nexus 6P 自带的系统没有允许 Root ，所以需要自己解锁 bootloader 并且刷上别的系统。我选择了 LineageOS 。Nexus 6P 的代号为 angler， 首先可以找到官方的[安装教程](https://wiki.lineageos.org/devices/angler/install)。

我们需要下载的东西：

```shell
$ wget https://mirrorbits.lineageos.org/full/angler/20180521/lineage-15.1-20180521-nightly-angler-signed.zip
$ wget https://mirrorbits.lineageos.org/full/angler/20180521/lineage-15.1-20180521-nightly-angler-signed.zip?sha256 -O lineage-15.1-20180521-nightly-angler-signed.zip.sha256
$ wget https://mirrorbits.lineageos.org/su/addonsu-15.1-arm64-signed.zip
$ wget https://mirrorbits.lineageos.org/su/addonsu-15.1-arm64-signed.zip?sha256 -O addonsu-15.1-arm64-signed.zip
$ wget https://github.com/opengapps/arm64/releases/download/20180527/open_gapps-arm64-8.1-full-20180527.zip
$ wget https://github.com/opengapps/arm64/releases/download/20180527/open_gapps-arm64-8.1-full-20180527.zip.md5
$ wget https://dl.twrp.me/angler/twrp-3.2.1-0-angler.img
$ wget https://dl.twrp.me/angler/twrp-3.2.1-0-angler.img.asc
$ wget https://dl.twrp.me/angler/twrp-3.2.1-0-angler.img.md5
$ gpg --verify *.asc
$ md5sum -c *.md5
$ sha256sum -c *.sha256
``` 

其中 Open GApps 可以自己考虑选择 full 还是其它的选择。

接下来，按照教程，先解锁 bootloader 。连接手机，进入 USB Debugging Mode ，重启进入 bootloader 并且解锁：

```shell
$ adb reboot bootloader
$ fastboot flashing unlock
# Confirm unlocking, and then the data should be wiped
```

接下来刷入 TWRP 。还是进入 bootloader ，然后刷入。

```
$ fastboot flash recovery twrp-3.2.1-0-angler.img
# Select recovery, and enter it
```

进入 TWRP 后，把我们刚刚下载的 zip 文件都 push 到手机上，并用 TWRP 安装：

```
# Select Wipe -> Advanced Wipe, Select Cache, System and Data and wipe then
# Install lineageos, opengapps, addonsu and follow on-screen instructions
# Reboot into system
```

经过一段时间的等待， LineageOS 就安装成功了。但是遇到了一些问题：

1. 开机时提示 vendor image 版本与打包 LineagesOS 时采用的版本不同。
    于是我下载了官方的 [factory image](https://dl.google.com/dl/android/aosp/angler-opm2.171019.029.a1-factory-bf17e552.zip)，找到其中的 vendor.img ，用 TWRP 刷到了 vendor 分区中。并且执行了 flash-bash.sh 更新 bootloader 和 radio 。重启的时候这个错误就解决了。2018-06-12 更新 注意：不要下载 Driver Binaries 里面的 vendor, 刷上去系统还是提示版本 mismatch，建议还是下载完整的factory 镜像。
2. 检测不到 SIM 卡。
    回到 bootloader 看 Barcode, 是有 IMEI 等信息的，说明分区没有被写坏。在网上搜索一段时间以后，发现禁用登录密码重启一次后即可使用，之后把密码加回来即可。


