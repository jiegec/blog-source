---
layout: post
date: 2020-09-11 23:42:00 +0800
tags: [alpine,pxe,rpi,rpi4]
category: devops
title: 在 TKE 上配置不使用 LB 的 Nginx Ingress Controller
---

# 背景

需要给 rpi 配置一个 pxe 的最小环境，然后看到 alpine 有 rpi 的支持，所以尝试给 rpi4 配置 alpine 。

# PXE 设置

第一步是设置 rpi4 的启动模式，打开 BOOT UART 并且打开 网络启动：

```bash
> cd /lib/firmware/raspberrypi/bootloader/critical
> rpi-eeprom-config pieeprom-2020-04-16.bin > config.txt
$ cat config.txt
[all]
BOOT_UART=0
WAKE_ON_GPIO=1
POWER_OFF_ON_HALT=0
DHCP_TIMEOUT=45000
DHCP_REQ_TIMEOUT=4000
TFTP_FILE_TIMEOUT=30000
TFTP_IP=
TFTP_PREFIX=0
BOOT_ORDER=0x1
SD_BOOT_MAX_RETRIES=3
NET_BOOT_MAX_RETRIES=5
[none]
FREEZE_VERSION=0
> sed 's/BOOT_UART=0/BOOT_UART=1/;s/BOOT_ORDER=0x1/BOOR_ORDER=0x21/' config.txt > config-pxe.txt
> rpi-eeprom-config --out pieeprom-2020-04-16-pxe.bin --config config-pxe.txt pieeprom-2020-04-16.bin
> rpi-eeprom-update -d -f pieeprom-2020-04-16.pxe.bin
> reboot
```

重启以后，可以用 `vcgencmd bootloader_config` 查看当前的启动配置，看是否正确地更新了启动配置。

# 路由器配置

第二步，需要配置路由器，以 OpenWrt 为例：

```bash
> uci add_list dhcp.lan.dhcp_option="66,ip_address_of_tftp_server"
> uci commit dhcp
> /etc/init.d/dnsmasq restart
$ cat /etc/config/dhcp
...
config dhcp 'lan'
		...
    list dhcp_option '66,ip_address_of_tftp_server'
...
```

这样就配置完毕了。

# TFTP 服务器配置

下载 alpine linux 的 rpi boot，解压到指定目录：

```bash
> wget http://mirrors.tuna.tsinghua.edu.cn/alpine/v3.12/releases/aarch64/alpine-rpi-3.12.0-aarch64.tar.gz
> unar alpine-rpi-3.12.0-aarch64.tar.gz
> cd alpine-rpi-3.12.0-aarch64
```

修改 `cmdline.txt` ，把 `console=tty1` 改成 `console=ttyAMA0,115200`，并且去掉 `quiet`；修改 `usercfg.txt` 为：

```
dtoverlay=disable-bt
enable_uart=1
```

接着，启动 TFTP 服务器：

```bash
> sudo python3 -m py3tftp -p 69
```

# 树莓派启动

连接树莓派的串口，用 115200 Baudrate 打开，可以看到启动信息：

```
PM_RSTS: 0x00001000
RPi: BOOTLOADER release VERSION:a5e1b95f DATE: Apr 16 2020 TIME: 18:11:29 BOOTMODE: 0x00000006 part: 0 BUILD_TIMESTAMP=1587057086 0xa049cc2f 0x00c03111
uSD voltage 3.3V
... 
initramfs emergency recovery shell launched. Type 'exit' to continue boot
sh: can't access tty; job control turned off
/ #

```

然后，按照需要自定义 initramfs 即可。解压后，修改文件，然后运行：

```bash
> find . -print0 | cpio --null -ov --format=newc | gzip > ../initramfs-rpi4
```

把自带的 initramfs 替换掉。