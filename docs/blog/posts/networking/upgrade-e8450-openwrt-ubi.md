---
layout: post
date: 2022-01-03
tags: [openwrt,linksys,e8450,ubi,flash,router]
categories:
    - networking
---

# 升级 Linksys E8450 的 OpenWRT 系统到 UBI

## 背景

在 [OpenWRT Linksys E8450 页面](https://openwrt.org/toh/linksys/e8450) 中，如果要用新版的固件，需要转换到 UBI 格式的文件系统。之前用的是 non-UBI 格式的文件系统，直接在官方的分区下，覆盖掉其中一个启动分区。但是经常会报告 flash 出错，然后系统也不稳定，决定要按照文档更新到 UBI。

## 步骤

请注意：更换文件系统操作比较危险，请先备份好数据，并做好变砖的心理准备。本文仅记录了作者编写时可行的更新操作，不代表读者在阅读时，依然可以按照这个顺序进行，请按照 <https://github.com/dangowrt/owrt-ubi-installer> 的文档进行操作。

基本按照文档一步一步走。初始状态是一个 non-UBI 版本的 OpenWRT 固件：

1. 下载官方的 1.0 固件：https://downloads.linksys.com/support/assets/firmware/FW_E8450_1.0.01.101415_prod.img
2. 在 luci 中，刷入官方 1.0 固件，这时候进入了官方固件的系统
3. 登录官方固件网页，恢复出厂设置
4. 下载 openwrt ubi recovery [固件](https://github.com/dangowrt/linksys-e8450-openwrt-installer/releases/download/v0.6.1/openwrt-mediatek-mt7622-linksys_e8450-ubi-initramfs-recovery-installer.itb) 然后在官方固件里刷入
5. 这时候进入了 recovery 固件，下载 [ubi 固件](https://downloads.openwrt.org/snapshots/targets/mediatek/mt7622/openwrt-mediatek-mt7622-linksys_e8450-ubi-squashfs-sysupgrade.itb)，继续在网页里刷入
6. 这时候固件就更新完成了。ssh root@192.168.1.1，然后进去安装 luci 等软件，恢复配置即可。