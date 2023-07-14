---
layout: post
date: 2023-06-15 16:03:00 +0800
tags: [libvirtd,qemu,proxmoxve,pve]
category: software
title: 从 libvirtd 迁移到 Proxmox VE
---

## 背景

之前用 libvirtd + virt-manager 做 Linux 上的虚拟化，好处是比较轻量级，但是远程控制起来比较麻烦，要么通过 RDP 访问 virt-manager 的 UI，要么就用 cockpit 在网页里去配置虚拟机。此时就会比较怀念 VMware ESXi 的网页，但是 ESXi 装完以后，宿主机就很不自由了，很多东西没法自定义。最后就想到在 Debian 上装一个 Proxmox VE，希望得到一个比较好的中间态。

## Proxmox VE 安装

按照官方的 [Install Proxmox VE on Debian 11 Bullseye](https://pve.proxmox.com/wiki/Install_Proxmox_VE_on_Debian_11_Bullseye) 去安装即可。我的环境是 Debian Bookworm，把路径改成 Bookworm 的 pvetest 即可。安装的时候可能会遇到一些小问题，例如用 ifupdown2 替换 ifupdown 的时候会检查 config 是否正确等等。安装完以后重启，就可以用 root 用户访问 Proxmox VE 了。

## 迁移 libvirtd 虚拟机

下一步是迁移 libvirtd 虚拟机。在网上搜索，会看到提供的方法是，在 Proxmox VE 里创建一个同样大小的镜像，然后把原来的 qcow2 的数据复制一份，但是这样复制的时候得存两份数据，而且对稀疏 qcow2 的支持也不太好。

最后实际的解决办法是：在 Proxmox VE 里创建一个和 qcow2 大小一样的镜像，设置为 qcow2 格式，然后去 `/var/lib/vz/images` 路径下找到新建的 qcow2，直接用原来 libvirtd 创建的 qcow2 覆盖过去。目前来看，还没有遇到问题，毕竟 ProxmoxVE 用的也是 QEMU，和 libvirtd 一样。

## UEFI

在 Proxmox VE 创建虚拟机，如果选的是 UEFI，由于它会采用新的 EFI vars 镜像，所以原来的 UEFI vars 就丢失了，启动的时候，如果 grub 的 EFI 程序不在标准的路径下，可能会找不到 grub。

解决办法是，先删掉网卡，然后修改 boot order，把 ESP 分区所在的盘加上去，这样 UEFI 启动的时候直接进 shell，然后在 fs0 里找到 grub 的 EFI 程序再启动。

在启动 NixOS 的时候，还发现运行 systemd-boot 的 EFI 程序的时候会 Access Denied，查询了一下，是因为 Secure Boot。进入 UEFI Firmware Setup，把 Secure Boot 关掉再重启，就可以正常进入了。

## Windows

在创建虚拟机的时候，如果指定了 Windows 11，就会自动勾选上 TPM 相关的配置。但启动的时候，说 swtpm 报错无法启动，按照错误信息查询了一下，找到了 [Apparmor > swtpm: Could not open UnixIO socket: Permission denied](https://github.com/quickemu-project/quickemu/issues/487)：原因是 AppArmor 拦截了 swtpm 的操作，可以用命令来解除 AppArmor 的拦截：

```shell
sudo aa-complain /usr/bin/swtpm
sudo apparmor_parser -r /etc/apparmor.d/usr.bin.swtpm
```

这样处理以后就可以正常启动 Windows 了。
