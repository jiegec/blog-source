---
layout: post
date: 2018-05-01
tags: [arch,boot,efi,fat32]
category: system
title: 在服务器上安装 Archlinux 记录
---

有一台服务器的 Ubuntu 挂了，我们想在上面重装一个 Archlinux。我们首先下载了 archlinux-2018.04.01 的 ISO, 直接 dd 到 U 盘上，但是遇到了问题。

首先遇到的问题是，一启动之后就会花屏。我们一开始怀疑是 NVIDIA 驱动的问题，于是想改 kernel param 但是发现，这个 ISO 是 hybrid 的，我们在 macOS 和 Windows 上都不能 mount 上这种类型的盘。于是我们选择自己搞分区表。我们把 U 盘插到电脑上，然后在 Linux 虚拟机内重新分区为 GPT，然后 mount 到 /mnt/usb，再重新下载 archlinux iso，不过此时刚好上游更新了 archlinux-2018.05.01 的影响。我们把 ISO 中根分区 mount 到 /mnt/iso 上来，然后 ```cp -a /mnt/iso/* /mnt/usb``` 。调整了 grub 中的内核参数，仍然无果。我们认为问题可能在显卡上，就把那张显卡拔下来了，果然显示就正常了，但是新的问题就来了。

一启动，fstab 尝试把 LABEL=ARCHISO_201805 挂在上来，但是失败。于是我们把 U 盘插到 mac 上，用 Disk Utility 给分区命了名，再插回去，然后这个 Live CD 的 Systemd 就成功起来了。接下来就是根据官方的 Installation Guide 进行安装各种东西。安装完后，在 /boot/EFI 的操作上也出现了一些问题，一开始忘记调用 `grub-mkconfig` ，导致重启以后进入 grub-rescue，所以又回到 Live CD 重新 `grub-mkconfig`  。同时对 systemd-networkd 也进行了相应的调整，这样开机以后可以配好网络。主要就是在网卡上配上两个 VLAN 和相应的 DHCP 和静态地址。

接下来对以前的东西进行迁移。主要就是按照十分详细的 Arch Wiki 进行相应的配置。由于空间所限，我们把原来的 home 目录直接 mount --bind 到 /home，但是不可避免地，会出现用户 id 不对应的问题。于是我们把需要用到的用户的 /etc/{passwd,group,shadow} 统统拷贝到新的系统的相应地方。然后是配置 winbind，就是按部就班地按照 Arch Wiki 和以前的配置进行更新，然后成功地把 AD 上的用户获取到。此时再次出现了 uid 不对应的问题，此时我们使用 `chown -R user:user /home/user` 的方法。

剩下的工作就是琐碎的安装各种常用软件。不必多说。

P.S. 我研究出了一个很好用的 mosh + tmux 的 fish function: (但是有时工作有时不工作，不明白什么回事)
``` 
function tmosh
    mosh $argv -- tmux new-session bash -c 'tmux set -g mouse on; tmux setw -g mode-keys vi; fish'
end
```
