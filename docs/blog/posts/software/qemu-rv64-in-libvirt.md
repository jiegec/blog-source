---
layout: post
date: 2022-05-31
tags: [qemu,libvirt,virtmanager,debian,riscv,rv64]
categories:
    - software
title: 在 libvirt 中运行 RISC-V 虚拟机
---

## 背景

我在 libvirt 中跑了几个 KVM 加速的虚拟机，然后突发奇想，既然 libvirt 背后是 qemu，然后 qemu 是支持跨指令集的，那是否可以让 libvirt 来运行 RISC-V 架构的虚拟机？经过一番搜索，发现可以跑 ARM：[How To: Running Fedora-ARM under QEMU](https://fedoraproject.org/wiki/Architectures/ARM/HowToQemu#Using_QEMU_with_libvirt)，既然如此，我们也可以试试用 libvirt 来运行 RV64 虚拟机。

## 准备 rootfs

第一步是根据 Debian 的文档 [Creating a riscv64 chroot](https://wiki.debian.org/RISC-V#Creating_a_riscv64_chroot) 来创建 rootfs，然后再用 virt-make-fs 来打包。

首先是用 mmdebstrap 来生成一个 chroot：

```shell
$ sudo mkdir -p /tmp/riscv64-chroot
$ sudo apt install mmdebstrap qemu-user-static binfmt-support debian-ports-archive-keyring
$ sudo mmdebstrap --architectures=riscv64 --include="debian-ports-archive-keyring" sid /tmp/riscv64-chroot "deb http://deb.debian.org/debian-ports sid main" "deb http://deb.debian.org/debian-ports unreleased main"
```

进入 chroot 以后，进行一些配置：

```shell
$ sudo chroot /tmp/riscv64-chroot
$ apt update
$ apt install linux-image-riscv64 u-boot-menu vim
# set root password
$ passwd
```

然后修改 `/etc/default/u-boot` 文件，添加如下的配置：

```shell
# change ro to rw, set root device
U_BOOT_PARAMETERS="rw noquiet root=/dev/vda1"
# fdt is provided by qemu
U_BOOT_FDT_DIR="noexist"
```

然后运行 `u-boot-update` 生成配置文件 `/boot/extlinux/extlinux.conf`。

到这里，rootfs 已经准备完毕。

## 尝试在 QEMU 中启动

接下来，可以参考 [Setting up a riscv64 virtual machine](https://wiki.debian.org/RISC-V#Setting_up_a_riscv64_virtual_machine) 先启动一个 qemu 来测试一下是否可以正常工作：

首先制作一个 qcow2 格式的镜像：

```shell
$ sudo virt-make-fs --partition=gpt --type=ext4 --size=+10G --format=qcow2 /tmp/riscv64-chroot rootfs.qcow2
$ qemu-img info rootfs.qcow2
image: rootfs.qcow2
file format: qcow2
virtual size: 11.4 GiB (12231971328 bytes)
disk size: 1.33 GiB
cluster_size: 65536
Format specific information:
    compat: 1.1
    compression type: zlib
    lazy refcounts: false
    refcount bits: 16
    corrupt: false
    extended l2: false
```

然后启动 qemu，配置好 OpenSBI 和 U-Boot 的路径：

```shell
$ sudo apt install qemu-system-misc opensbi u-boot-qemu
$ sudo qemu-system-riscv64 -nographic -machine virt -m 8G \
    -bios /usr/lib/riscv64-linux-gnu/opensbi/generic/fw_jump.elf \
    -kernel /usr/lib/u-boot/qemu-riscv64_smode/uboot.elf \
    -object rng-random,filename=/dev/urandom,id=rng0 -device virtio-rng-device,rng=rng0 \
    -append "console=ttyS0 rw root=/dev/vda1" \
    -device virtio-blk-device,drive=hd0 -drive file=rootfs.qcow2,format=qcow2,id=hd0 \
    -device virtio-net-device,netdev=usernet -netdev user,id=usernet,hostfwd=tcp::22222-:22
```

如果系统可以正常工作，看到下面的输出，下一步就可以配置 libvirt 了。

```
[    6.285024] Run /init as init process
Loading, please wait...
Starting version 251.1-1
[    7.743714] virtio_ring: module verification failed: signature and/or required key missing - tainting kernel
[    8.071762] virtio_blk virtio1: [vda] 23838189 512-byte logical blocks (12.2 GB/11.4 GiB)
[    8.181210]  vda: vda1
Begin: Loading essential drivers ... done.
Begin: Running /scripts/init-premount ... done.
Begin: Mounting root file system ... Begin: Running /scripts/local-top ... done.
Begin: Running /scripts/local-premount ... done.
Warning: fsck not present, so skipping root file system
[    9.003143] EXT4-fs (vda1): mounted filesystem with ordered data mode. Quota mode: none.
done.
Begin: Running /scripts/local-bottom ... done.
Begin: Running /scripts/init-bottom ... done.
[    9.754151] Not activating Mandatory Access Control as /sbin/tomoyo-init does not exist.
[    9.808860] random: fast init done
[   10.651361] systemd[1]: Inserted module 'autofs4'
[   10.735574] systemd[1]: systemd 251.1-1 running in system mode (+PAM +AUDIT +SELINUX +APPARMOR +IMA +SMACK +SECCOMP +GCRYPT -GNUTLS +OPENSSL +ACL +BLKID +CURL +ELFUTILS +FIDO2 +IDN2 -IDN +IPTC +KMOD +LIBCRYPTSETUP +LIBFDISK +PCRE2 -PWQUALITY -P11KIT -QRENCODE +TPM2 +BZIP2 +LZ4 +XZ +ZLIB +ZSTD -BPF_FRAMEWORK -XKBCOMMON +UTMP +SYSVINIT default-hierarchy=unified)
[   10.736902] systemd[1]: Detected architecture riscv64.

Welcome to Debian GNU/Linux bookworm/sid!
```

## 配置 libvirt

首先，打开 virt-manager，在向导中，可以在下拉菜单选择自定义的架构，选择 riscv64 和 virt，然后选择 Import existing disk image，找到刚刚创建的 qcow2 文件。

创建好以后，我们还不能直接启动，因为此时还没有配置 OpenSBI 和 U-Boot。由于 virt-aa-helper 会[检查 OpenSBI 和 U-Boot 的路径，要求它们不能在 /usr/lib 路径下](https://github.com/wiedi/libvirt/blob/435b4ad22bf812d97f30e4d6b71e6b3a967f4f75/src/security/virt-aa-helper.c#L529)：

```cpp
/*
 * Don't allow access to special files or restricted paths such as /bin, /sbin,
 * /usr/bin, /usr/sbin and /etc. This is in an effort to prevent read/write
 * access to system files which could be used to elevate privileges. This is a
 * safety measure in case libvirtd is under a restrictive profile and is
 * subverted and trying to escape confinement.
 *
 * Note that we cannot exclude block devices because they are valid devices.
 * The TEMPLATE file can be adjusted to explicitly disallow these if needed.
 *
 * RETURN: -1 on error, 0 if ok, 1 if blocked
 */
    const char * const restricted[] = {
        "/bin/",
        "/etc/",
        "/lib",
        "/lost+found/",
        "/proc/",
        "/sbin/",
        "/selinux/",
        "/sys/",
        "/usr/bin/",
        "/usr/lib",
        "/usr/sbin/",
        "/usr/share/",
        "/usr/local/bin/",
        "/usr/local/etc/",
        "/usr/local/lib",
        "/usr/local/sbin/"
    };
```

所以，我手动把 U-Boot 和 OpenSBI 复制一份到 /var/lib 下：

```shell
$ sudo mkdir -p /var/lib/custom
$ cd /var/lib/custom
$ sudo cp -r /usr/lib/u-boot/qemu-riscv64_smode .
$ sudo cp -r /usr/lib/riscv64-linux-gnu .
```

此时，再去配置 libvirt 的 XML 配置文件：

```xml
  <os>
    <type arch='riscv64' machine='virt'>hvm</type>
    <loader type='rom'>/var/lib/custom/riscv64-linux-gnu/opensbi/generic/fw_jump.elf</loader>
    <kernel>/var/lib/custom/qemu-riscv64_smode/uboot.elf</kernel>
    <boot dev='hd'/>
  </os>
```

其余部分不用修改。在下面可以看到 virt-manager 已经设置好了 qemu-system-riscv64:

```XML
<devices>
  <emulator>/usr/bin/qemu-system-riscv64</emulator>
  <disk type='file' device='disk'>
    <driver name='qemu' type='qcow2'/>
    <source file='/path/to/rootfs.qcow2'/>
    <target dev='vda' bus='virtio'/>
    <address type='pci' domain='0x0000' bus='0x04' slot='0x00' function='0x0'/>
  </disk>
```

保存以后直接启动，就完成了在 libvirt 中运行 Debian RV64 虚拟机的目的。