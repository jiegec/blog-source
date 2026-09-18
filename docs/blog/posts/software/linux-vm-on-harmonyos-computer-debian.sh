#!/bin/bash
# Run this script with root permissions
# Original version: https://www.bilibili.com/opus/1186292133496094724 by Revy
set -x
cd /

# install debootstrap
dnf install -y debootstrap

# create debian trixie rootfs
mkdir /newroot /oldroot
mount -t tmpfs tmpfs /newroot
debootstrap trixie /newroot https://mirror.bfsu.edu.cn/debian

# change your password here
chroot /newroot apt install -y sudo busybox-static
chroot /newroot bash -c 'echo root:1|chpasswd'
chroot /newroot groupadd wheel
# fake user
chroot /newroot useradd -m -s /bin/bash -G sudo user
chroot /newroot bash -c 'echo user:1|chpasswd'

cp /newroot/bin/busybox /busybox

# mov old files
/busybox mv afs bin sbin lib lib64 home opt root var usr oldroot/

# move /etc except hsl
/busybox mkdir -p oldroot/etc
for d in /etc/*; do
  [ "$d" = "/etc/hsl" ] && continue
  /busybox mv "$d" oldroot/etc/
done

cd /newroot

# copy from new root to real root
/busybox mv bin sbin lib lib64 boot home opt root var usr ../ 2>/dev/null

# merge /etc content
/busybox mv etc/* ../etc/

# copy files from old root
cd /
/busybox cp -r oldroot/usr/lib/modules usr/lib/modules

# profit!
