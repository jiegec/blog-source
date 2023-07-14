---
layout: post
date: 2023-04-09 12:47:00 +0800
tags: [aix,unix]
category: system
title: AIX 7.2 虚拟机安装
---

## 安装过程

宿主机环境是 Debian bookworm，不需要像其他教程那样自己编译 qemu，直接 apt install 即可。

通过 google 可以搜索到 AIX 7.2 的 ISO，下载第一个 ISO 到本地，然后在 QEMU 中启动安装镜像：

```bash
qemu-img create -f qcow2 aix-hdd.qcow2 20G
qemu-system-ppc64 -cpu POWER8 -machine pseries -m 16384 -serial mon:stdio -drive file=aix-hdd.qcow2,if=none,id=drive-virtio-disk0 -device virtio-scsi-pci,id=scsi -device scsi-hd,drive=drive-virtio-disk0 -cdrom aix_7200-04-02-2027_1of2_072020.iso -prom-env boot-command='boot cdrom:\ppc\chrp\bootfile.exe' -display none
```

进去以后，耐心等待，直到进入安装界面，按照提示进行安装，建议安装上 SSH Server，关掉图形界面，这样安装会比较快。安装需要几十分钟，安装完成后会进入 bootloop，关掉 QEMU。接着，准备好网络：

```bash
sudo ip tuntap add tap0 mode tap
sudo ip link set tap0 up
sudo ip a add 10.0.2.15/24 dev tap0
```

再启动虚拟机，注意启动选项修改了，并且多了网络的配置：

```bash
qemu-system-ppc64 -cpu POWER8 -machine pseries -m 16384 -serial mon:stdio -drive file=aix-hdd.qcow2,if=none,id=drive-virtio-disk0 -device virtio-scsi-pci,id=scsi -device scsi-hd,drive=drive-virtio-disk0 -cdrom aix_7200-04-02-2027_1of2_072020.iso -prom-env boot-command='boot disk:' -display none -net nic -net tap,script=no,ifname=tap0
```

第一次启动系统时，会进入配置界面，修改好 root 密码，然后配置网络：

```bash
chdev -l en0 -a netaddr=10.0.2.16 -a netmask=255.255.255.0 -a state=up
```

到这里了以后，就可以通过 ssh 访问虚拟机：

```bash
ssh root@10.0.2.16
```

## KVM

另外测试了一下，在 powerpc64 机器上，可以开启 KVM 来加速 QEMU，但是需要首先关掉 SMT。另外在使用过程中出现了玄学问题，最后还是在 x86 上跑了虚拟机。

## 安装软件

接下来，可以从 [AIX Toolbox for Open Source Software](https://www.ibm.com/support/pages/node/882892) 安装软件：

```shell
# in aix
chfs -a size=+200M /home
chfs -a size=+400M /opt
chfs -a size=+400M /tmp
# setup default gateway
route add 0 10.0.2.15 -if en0
# edit /etc/resolv.conf
echo "nameserver 1.1.1.1" > /etc/resolv.conf
# in host
wget https://public.dhe.ibm.com/aix/freeSoftware/aixtoolbox/ezinstall/ppc/dnf_aixtoolbox.sh
scp dnf_aixtoolbox.sh root@10.0.2.16:/
# in aix
rpm --rebuilddb
ksh /dnf_aixtoolbox.sh -y
/opt/freeware/bin/dnf update
/opt/freeware/bin/dnf install gcc
```

安装好的包会放到 /opt/freeware 路径下。

安装过程中可能需要继续扩大各个 fs 的大小。

dnf 如果提示缺少 `libssl.a`，参考 <https://www.ibm.com/support/pages/resolving-rpm-libssla-and-libcryptoa-errors> 进行解决：

1. 访问 <https://www.ibm.com/resources/mrs/assets?source=aixbp&S_PKG=openssl> 下载安装包，例如 `openssl-1.1.2.2000.tar.Z`。

2. scp 到 AXI 上安装：

```shell
uncompress openssl-1.1.2.2000.tar.Z
tar -xvf openssl-1.1.2.2000.tar
# install openssl.base using smitty
```

为了方便，可以修改 `/etc/environment` 文件，把 `/opt/freeware/bin` 目录加到 PATH 目录中。

## 参考文档

本博客参考了以下文档中的命令：

- <https://aix4admins.blogspot.com/2020/04/qemu-aix-on-x86-qemu-quick-emulator-is.html>
- <https://virtuallyfun.com/2019/04/22/installing-aix-on-qemu/>
- <https://www.ibm.com/support/pages/resolving-rpm-libssla-and-libcryptoa-errors>