---
layout: post
date: 2018-07-16
tags: [linux,initrd,initramfs]
categories:
    - os
---

# 构建简易的 initramfs

一直对 Linux 的启动很感兴趣，但对 initrd 和 initramfs 等概念不大了解，于是上网找了资料，自己成功地看到了现象。

参考资料：
[Build and boot a minimal Linux system with qemu](http://www.kaizou.org/2016/09/boot-minimal-linux-qemu/)
[Custom Initramfs](https://wiki.gentoo.org/wiki/Custom_Initramfs)
[initramfs vs initrd](https://dazdaztech.wordpress.com/2013/04/04/initrd-vs-initramfs/)
[ramfs, rootfs and initramfs](https://www.kernel.org/doc/Documentation/filesystems/ramfs-rootfs-initramfs.txt)
[The Kernel Newbie Corner: "initrd" and "initramfs"-- What's Up With That?](https://www.linux.com/learn/kernel-newbie-corner-initrd-and-initramfs-whats)

具体步骤：
```shell
$ cat hello.c
#include <stdio.h>
#include <unistd.h>

int main() {
    for (;;) {
        printf("Hello, world!\n");
    }
}
$ gcc -static hello.c -o init
$ echo init | cpio -o -H newc | gzip > initrd
$ qemu-system-x86_64 -kernel /boot/vmlinuz-linux -initrd initrd -nographic -append 'console=ttyS0'
# Use C-a c q u i t <Enter> to exit
```

可以看到过一会（三四秒？），可以看到满屏的 Hello world 在输出。
