---
layout: post
date: 2019-09-14
tags: [linux,efi,esp,macos,vmware]
categories:
    - software
---

# 在 macOS 上创建 ESP 镜像文件

最近 rCore 添加了 UEFI 支持，在 QEMU 里跑自然是没有问题，然后尝试放到 VMWare 虚拟机里跑，这时候问题就来了：需要一个带有 ESP 盘的 vmdk 虚拟盘。搜索了一下网络，找到了解决方案：

```shell
hdiutil create -fs fat32 -ov -size 60m -volname ESP -format UDTO -srcfolder esp uefi.cdr
```

其中 `60m ` `esp` 和 `uefi.cdr` 都可以按照实际情况修改。它会把 esp 目录下的文件放到 ESP 分区中，然后得到一个镜像文件：

```
uefi.cdr: DOS/MBR boot sector; partition 1 : ID=0xb, start-CHS (0x3ff,254,63), end-CHS (0x3ff,254,63), startsector 1, 122879 sectors, extended partition table (last)
```

接着转换为 vmdk：

```shell
qemu-img convert -O vmdk uefi.cdr uefi.vmdk
```

这样就可以了。