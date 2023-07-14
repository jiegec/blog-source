---
layout: post
date: 2020-02-07
tags: [macos,mmap,catalina]
categories:
    - software
title: 在 macOS 上带执行权限 mmap 一个已删除文件遇到的问题和解决方案
---

## 背景

实验环境：macOS Catalina 10.15.2

最近在 [rcore-rs/zircon-rs](https://github.com/rcore-os/zircon-rs) 项目中遇到一个比较玄学的问题，首先需求是在 macOS 的用户进程里开辟一段地址空间，然后把这个地址空间多次映射（权限可能不同、同一块内存可能被映射到多个地址），通过 mmap 模拟虚拟地址的映射。采用的是如下的方案：

1. 在临时目录创建一个文件，把文件大小设为 16M（暂不考虑扩容）
2. 需要映射一个虚拟地址到物理地址的时候，就对这个文件的物理地址偏移进行 FIXED 映射，虚拟地址就是期望的虚拟地址。

这样的方案在 Linux 下运行地很好，但在 macOS 下总是以一定概率在第二部出现 EPERM。网上搜了很多，但也没搜到相关的信息，于是自己断断续续地研究了一下，现在有一个比较初步的结果。

## TL；DR

先说结论：调用一个带 PROT_EXEC 并且映射文件的 mmap 时，macOS 会进行安全检测，如果此时发现文件在文件系统上消失了，它会认为这可能是一个恶意软件行为，进行拦截，返回 EPERM。

而代码实际上在第一步和第二步之间，把临时目录删了：由于进程持有 fd，所以文件并不会真的删掉，当软件退出的时候文件自然会删除，这是临时文件的常见做法（见 tmpfile(3)）。

## 研究过程

### 查看 Console

在网上一番搜索未果后，就尝试在 Console 里面寻找信息。照着程序名字搜索，可以找到一些信息：

```
temporarySigning type=1 matchFlags=0x0 path=/path/to/executable
```

这是编译这个 executable 的时候出现的，好像也没啥问题。然后解除过滤，在这个信息前后按照 syspolicyd 寻找：

````
initiating malware scan (... info_path: /path/to/temp/file proc_path: /path/to/executable)
Unable (errno: 2) to read file at <private> for process path: <private> library path: <private>
Disallowing load of <private> in 50001, <private>
Library load (/path/to/temp/file) rejected: library load denied by system policy
````

这几条记录比较可疑，每次运行程序，如果跑挂了，就会出现这几条，如果没跑挂，就不会出现这一条。所以很大概率是被 macOS 拦截了。错误信息的用词是 library，所以大概率是被当成加载动态库了，但既然内容是空的，所以我想的是文件名触碰到了什么奇怪的规则，然后文件名又是随机的，随机导致 EPERM 是概率性出现的，这好像很有道理。于是我把 tmpfile 换成了固定的路径，忽然就好了。但固定的路径只能保证同时只有一个程序在跑，如果路径拼接上 pid，怎么删，谁来删又是一个问题。虽然可以放到 /tmp 下面然后随便搞，但 /tmp 的回收并不是那么积极，在临时目录下丢太多文件也会出现问题。

### 一丝曙光

这时候，@wangrunji0408 提供了一个方案：在 System Preferences -> Security & Privacy -> Privacy -> Developer Tools 中添加编译该 executable 的程序（如 iTerm、CLion）可以解决这个问题。那么问题应该比较明确了，就是 malware scan 的问题，如果信任了这个 App 为 Developer Tools，它产生的 executable 也是可信的，应该不是恶意软件。但在 tmux 环境下，它哪个 App 也不属于，没法继承，况且把这个权限开放出去也有潜在的安全问题。并且让每个开发者都要这么操作一遍很不方便。

### 回到 Console

今天刚好看到一个 [post](https://georgegarside.com/blog/macos/sierra-console-private/)，内容是如何在 macOS Catalina 中查看 log 中标记为 private 的内容。如果你注意到的话，上面的 log 中出现了几处 private，这并不是我改的，而是 macOS 自带的隐私机制（当然这种机制似乎并没有采用的很完全，一些消息源没有打上 private 的标签）。

然后按照上面的 post 的方法（[另一个 post](https://saagarjha.com/blog/2019/09/29/making-os-log-public-on-macos-catalina/)）开启了一下标记为 private 的内容，正好我的系统没有升级到 10.15.3 所以还能用。此时上面的第二条和第三条就出现了具体内容：

```
Unable (errno: 2) to read file at /path/to/temp/file for process path: /path/to/executable library path: /path/to/temp/file
Disallowing load of /path/to/temp/file in 61254, /path/to/executable
```

这个时候问题就很明显了：读取不到文件。这时候回想起 tmpfile 的工作原理，它会删除生成的文件，在删除文件之后，macOS 进行扫描，发现找不到文件，于是 disallow 了，mmap 就会返回 EPERM。

解决方案也很显然了：把删除目录延后，或者放在 /tmp 下等待清理等待。

我也写了一段 C 代码来验证这个现象：

```cpp
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>


int main() {
    int fd = open("mmap", O_RDWR | O_CREAT, 0777);
    uint64_t addr = 0x200000000;
    ftruncate(fd, 16*1024*1024);
    // might not work if unlink is put here (race condition)
    // you can use sleep to reproduce
    unlink("mmap");
    void * res = mmap((void *)addr, 16*1024*1024, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_SHARED | MAP_FIXED, fd, 0);
    // always works if unlink is put here
    // unlink("mmap");
    if (res == MAP_FAILED) {
        perror("mmap");
    } else {
        printf("good");
    }
    return 0;
}

```

