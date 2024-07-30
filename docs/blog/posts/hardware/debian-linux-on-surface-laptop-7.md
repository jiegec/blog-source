---
layout: post
date: 2024-07-30
tags: [surface,linux,qcom,qualcomm,xelite,aarch64,debian]
categories:
    - hardware
---

# 在 Surface Laptop 7 上运行 Debian Linux

## 背景

最近借到一台 Surface Laptop 7 可以拿来折腾，它用的是高通 Snapdragon X Elite 处理器，跑的是 Windows on Arm 系统。但作为 Linux 用户，肯定不满足于 WSL，而要裸机上安装 Linux。由于这个机器太新，所以安装的过程遇到了很多坎坷。

<!-- more -->

## 上游进展

目前 X Elite 处理器的上游支持已经逐步完善，但是还是需要很新的内核，也就是最近才合并了 X Elite 的两个笔记本的 device tree 支持进内核。我用的是 v6.11-rc1-43-g94ede2a3e913 版本的内核，目前可以正常显示，Wi-Fi 正常，USB Type-C 口正常工作（键盘，鼠标，有线网都可以通过 USB 接到电脑上），内置的键盘、触摸板和触摸屏不工作。希望后续可以获得更好的硬件支持。

## 折腾过程

高通和 Linaro 在去年的时候推出了一个实验性的 Debian Installer Image：https://git.codelinaro.org/linaro/qcomlt/demos/debian-12-installer-image，它针对的设备是高通自己的 CRD 设备，和 Surface Laptop 7 不同。自然，把这个 image 写到 U 盘里并启动是不行的。

需要注意的是，Surface Laptop 7 默认安装了 Windows，并且开启了安全启动，而我们自己编译的 Linux 内核自然是过不了安全启动的，所以要去固件关闭安全启动。由于 Windows 的 Bitlocker 默认是打开的，请先保证你可以获取 Bitlocker recovery key，不然之后可能进不去 Windows 系统了。安装双系统前，记得在 Windows 里准备好分区表，空间不够的话，可以在线缩小 NTFS。

进入固件的方法：按住音量上键开机。开机后，可以看到 Surface UEFI 的界面，可以调启动顺序，也可以关闭安全启动。为了安装方便，建议把 USB Storage 放到第一个。

接着就开始启动 U 盘里的 Debian Installer Image 了。启动以后，可以看到进入了 grub shell，目测是 grub 找不到自己的配置文件，可以在 (hd1,msdos1)/boot/grub 下面找到。但是这个 image 的 device tree 和 kernel 都比较老，直接启动会发现，Debian Install 进去了，但是内置键盘和外置 USB 键盘都不工作，于是没法进行进一步的安装。

这时候，在网上搜索了一下已有的在 X Elite 上运行 Linux 的尝试，发现有人在 ASUS 的 X Elite 笔记本上装好了（[来源](https://matrix.org/_matrix/media/v3/download/matrix.org/hrxnkHBVEacnUGKSnHPMUHRX/1000004724.jpg)），我就试着用 ASUS 对应型号笔记本的 device tree 去启动，依然不行，经过了解后（感谢 @imbushuo），得知 Surface 的内置键盘等外设需要通过 SAM 访问，需要额外的配置，目前不确定能否通过 device tree 启用。

但很快也发现有人在 Surface Laptop 7 上跑起来了（[来源](https://x.com/merckhung/status/1804972131182354604)），我发邮件问了这个作者，作者说他用的是外置的键盘，内置的键盘也不工作。放大观察作者录的视频，发现用的是最新的 master 分支的 Linux 内核，并且用的就是 CRD 的 device tree。到这里就比较有思路了：自己编译一个内核，然后用 x1e80100-crd.dtb 作为 device tree。

于是魔改了 Debian Installer Image：替换掉 linux 内核，换成自己编译的最新版，解开 initrd，把里面的 kernel modules 也换成新内核的版本，再把新的 x1e80100-crd.dtb 复制上去，再用 grub 启动新内核 + 新 initrd + 新 Device Tree，发现 USB 外接键盘工作了！虽然只有 Type-C 工作，但是也足够完成剩下的工作了。

不过在安装 Debian 的时候，还遇到了小插曲：glibc 版本不够新，估计是 Linaro 的 Image 太老了。于是我从新的 debian arm64 里复制了 libc.so.6 和 ld-linux-aarch64.so.1，覆盖掉 initrd 里的旧版本，这样就好了。

安装完以后，安装的系统里的内核是 debian 的最新内核，但是不够新，于是又老传统：手动 arch-chroot 进新的 sysroot，安装新的内核。也可以像 Linaro 仓库里指出的那样，直接替换 Debian Installer Image 里的 deb，但是我发现我打的 deb 太大了（毕竟 defconfig），放不进文件系统，只好最后自己手动装。

最后在 grub 配置里添加 devicetree 加载命令，再从 Debian Installer Image 的 grub 配置偷 linux cmdline，最终是 grub 配置是这个样子：

```shell
devicetree /boot/x1e80100-crd.dtb
echo    'Loading Linux 6.11.0-rc1-00043-g94ede2a3e913 ...'
linux   /boot/vmlinuz-6.11.0-rc1-00043-g94ede2a3e913 root=UUID=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee ro efi=novamap pd_ignore_unused clk_ignore_unused fw_devlink=off cma=128M quiet
echo    'Loading initial ramdisk ...'
initrd  /boot/initrd.img-6.11.0-rc1-00043-g94ede2a3e913
```

这样搞完，Debian 系统就正常起来了！
