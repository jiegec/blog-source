---
layout: post
date: 2019-03-08 18:07:00 +0800
tags: [rcore,rust,os,nginx,syscall,fs,sfs]
category: programming
title: 在 rCore 上运行 nginx
---

阿 西 吧 nginx 终于能在 rCore 上跑了 orrrrrrrz

通过这半个多月来的大量开发，我和王润基 @wangrunji0408 学长算是终于完成了第一个 milestone：跑起来一个 nginx 。遇到了很多困难，大概有这些：

1. syscall 实现不全。各种方面都缺，然后 nginx 在编译的时候又检测到比较新的 OS 版本，所以很多 syscall 都用了新的来替代老的，例如 readv/writev pread/pwrite accept4 等等，所以这方面做了一些工作。另外，还有很多新的 syscall 进来，太多了我就不细说了，基本上一个commit做一点一个commit做一点这个样子。
2. nginx 用到了 SSE 的寄存器 xmm ，但是之前是没有开的。所以把 sse 打开，然后切换上下文的时候把 sse 通过 fxsave 保存和 fxrstor 恢复（有意思的是，as居然不认这俩，只好手动写字节码），然后为了 16bit 的对齐又写了几行汇编代码。这块问题不大，今天一会就搞定了。但是如果要性能更高一些的话，可能需要在第一次使用 xmm 的时候再开始保存，大概就是加一个bit的事情。
3. 文件系统有点崩。实现还是有很多 BUG ，表现就是需要经常重新 mksfs 一下，再重启加载完好的 fs ，有时候强制关机一下就又崩了。
4. 内存管理做了一些改变。为了实现更加完整的 mmap mumap 和 mprotect ，又发现了一些新的 BUG 在里面，然后慢慢修复了。就是实现的有点粗暴。
5. 死锁问题。这个其实现在还会出现，只是还没调出来，也不会百分百出现。我们计划在锁上面做一些死锁检测，例如记住是谁上锁的，等等。现在就遇到一个很玄学的死锁问题。

然后代码也是一边在写一边在重构吧，很多地方现在都写得很粗暴，FIXME和TODO留了很多，很多地方也写得不够优雅。以后再慢慢重构+优化吧。

截图留念：

![](/assets/nginx.jpg)

再往前的话，还有很多小的问题，例如网卡的中断启用了但没有改 mask ，所以啥也没收到，靠 QEMU Tracing 找到问题。还有一个很有意思的现象，就是如果 elf 的 program header 没有 phdr 这个项的时候，我们发现，可以通过第一个load（如果加载了完整的 elf 头的话），我们可以从这里推断出 phdr 的地址（load的虚拟地址加偏移），然后丢到 auxv 里去让 musl 配置 tls。总之这些都解决了。也不用去考虑兼容 litc 了，已经全部向 linux 靠拢了，稳。