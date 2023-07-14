---
layout: post
date: 2021-03-18
tags: [openwrt,linksys,e8450,wifi,80211ax]
categories:
    - hardware
---

# Linksys E8450 OpenWRT 配置 w/ 802.11ax

## 背景

之前用的 newifi 路由器（Lenovo y1s）无线网总是出问题，于是换了一个新的支持 802.11ax 的路由器 Linksys E8450，目前在 openwrt snapshot 支持。Openwrt 的支持页面：[Linksys E8450](https://openwrt.org/toh/linksys/linksys_e8450)。

## 过程

按照支持页面，下载固件：

```shell
$ wget https://downloads.openwrt.org/snapshots/targets/mediatek/mt7622/openwrt-mediatek-mt7622-linksys_e8450-squashfs-sysupgrade.bin
```

更新（2023-02-27）：固件已经从 snapshot 进入正式版，下载链接为 <https://downloads.openwrt.org/releases/22.03.3/targets/mediatek/mt7622/openwrt-22.03.3-mediatek-mt7622-linksys_e8450-squashfs-sysupgrade.bin>。如果已经替换为 UBI，则使用 <https://downloads.openwrt.org/releases/22.03.3/targets/mediatek/mt7622/openwrt-22.03.3-mediatek-mt7622-linksys_e8450-ubi-squashfs-sysupgrade.itb> 固件。

然后访问固件升级页面：http://192.168.1.1/config-admin-firmware.html#firmware，选择下载的 bin 文件。点击“开始升级”，然后等待。一段时间后，ssh 到路由器：

```shell
$ ssh root@192.168.1.1
The authenticity of host '192.168.1.1 (192.168.1.1)' can't be established.
ED25519 key fingerprint is SHA256:REDACTED.
No matching host key fingerprint found in DNS.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '192.168.1.1' (ED25519) to the list of known hosts.


BusyBox v1.33.0 () built-in shell (ash)

  _______                     ________        __
 |       |.-----.-----.-----.|  |  |  |.----.|  |_
 |   -   ||  _  |  -__|     ||  |  |  ||   _||   _|
 |_______||   __|_____|__|__||________||__|  |____|
          |__| W I R E L E S S   F R E E D O M
 -----------------------------------------------------
 OpenWrt SNAPSHOT, r16242-41af8735d4
 -----------------------------------------------------
=== WARNING! =====================================
There is no root password defined on this device!
Use the "passwd" command to set up a new password
in order to prevent unauthorized SSH logins.
--------------------------------------------------
root@OpenWrt:~# uname -a
Linux OpenWrt 5.10.23 #0 SMP Wed Mar 17 19:55:38 2021 aarch64 GNU/Linux
```

配置 luci:

```shell
$ opkg update
$ opkg install luci
```

然后就可以网页访问看到 luci 了：Powered by LuCI Master (git-21.060.51374-cd06e70) / OpenWrt SNAPSHOT r16242-41af8735d4。

由于目前 luci 不支持 802.11ax 的配置，可以直接修改 uci 配置来达到效果：

```shell
root@OpenWrt:/# uci show wireless
root@OpenWrt:/# uci set wireless.radio1.htmode='HE80'
root@OpenWrt:/# /etc/init.d/network restart
'radio0' is disabled
```

注：实际上设置为 HE 开头的字符串即可，见 [mac80211.sh](https://github.com/openwrt/openwrt/blob/8019c54d8a191cfb90c3bf06ff367f601f872fd1/package/kernel/mac80211/files/lib/netifd/wireless/mac80211.sh#L334)。

再连接上 Wi-Fi 的时候就可以看到是 802.11ax 模式了。也在 [OpenWRT 论坛](https://forum.openwrt.org/t/got-802-11ax-working-in-linksys-e8450/91533) 上分享了一下这个方案。

更新（2021-07-31）：目前最新的 luci 版本已经可以在网页上配置 802.11ax 模式了。