---
layout: post
date: 2022-09-19
tags: [linux,fakeroot,mknod]
categories:
    - software
---

# Buildroot 2020.08 的 Fakeroot 版本过旧导致的兼容性问题

## 背景

最近在给之前的 Buildroot 2020.09 增加新的软件包，结果编译的时候报错：

```
mknod: ....../dev/console: Operation not permitted
```

还有一个背景是前段时间把系统升级到了 Ubuntu 22.04 LTS。

<!-- more -->

## 研究

跑的时候没有用 root，而是用 fakeroot 跑的，按理说在 fakeroot 里跑 mknod 是不会报错的，我直接运行系统的 fakeroot 是正常的：

```shell
fakeroot -- mknod -m 0622 test c 5 1
```

此时 fakeroot 会生成一个空文件，这是正常现象。那么为什么 Buildroot 里跑就不对了呢？

我仔细观察了一下，buildroot 用的是自己编译的 fakeroot，版本是 1.20.2，用这个版本跑就会报错：

```shell
$ ./output/host/bin/fakeroot -- mknod -m 0622 test c 5 1
mknod: test: Operation not permitted
```

果然就出问题了。

用 strace 观察下区别：

```shell
$ fakeroot -- strace mknod -m 0622 test c 5 1
newfstatat(AT_FDCWD, "test", {st_mode=S_IFREG|0644, st_size=0, ...}, AT_SYMLINK_NOFOLLOW) = 0
msgget(0x4b33194b, IPC_CREAT|0600)      = 32771
msgget(0x4b33194c, IPC_CREAT|0600)      = 32772
msgsnd(...) = 0
newfstatat(AT_FDCWD, "test", {st_mode=S_IFREG|0644, st_size=0, ...}, AT_SYMLINK_NOFOLLOW) = 0
msgsnd(...) = 0
openat(AT_FDCWD, "test", O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_PATH) = 3
newfstatat(3, "", {st_mode=S_IFREG|0644, st_size=0, ...}, AT_EMPTY_PATH) = 0
fchmodat(AT_FDCWD, "/proc/self/fd/3", 0622) = 0
$ ./output/host/bin/fakeroot -- strace mknod -m 0622 test c 5 1
umask(000)                              = 002
umask(002)                              = 000
mknodat(AT_FDCWD, "test", S_IFCHR|0622, makedev(0x5, 0x1)) = -1 EPERM (Operation not permitted)
```

可以看到，正常情况下，mknodat 系统调用被拦截，由 fakeroot 来创建空文件；而错误的 fakeroot 版本下，没有拦截成功，就出现了 EPERM。

## 解决

一个粗暴的解决办法是，直接修改 buildroot 源代码，让它用系统的 fakeroot：

```shell
        PATH=$$(BR_PATH) FAKEROOTDONTTRYCHOWN=1 /usr/bin/fakeroot -- $$(FAKEROOT_SCRIPT)
```

我还尝试重新编译 fakeroot 1.20.2，会出现编译错误，采用类似 [bug 69572 fakeroot failes to build: _STAT_VER undeclared](https://bugs.archlinux.org/task/69572) 的方法可以解决编译的问题，但是还是出现 EPERM。[Buildroot](https://github.com/buildroot/buildroot/commit/f45925a951318e9e53bead80b363e004301adc6f) 后来也引入了类似的修复。

于是在[源代码](https://salsa.debian.org/clint/fakeroot)历史中搜寻了一番，发现了一个疑似的修复 commit：[configure.ac: fix __xmknod{,at} pointer argument](https://salsa.debian.org/clint/fakeroot/-/commit/c3eebec293e35b997bb46c22fb5a4e114afb5e7f)，不过我并不能确定是不是这个问题。

进一步，我在 Docker 镜像中手动下载并编译 fakeroot 1.20.2、1.21 和 1.25.3，都可以复现这个问题，编译 1.29 版本则没有问题。用 git 克隆[仓库](https://salsa.debian.org/clint/fakeroot)，进一步定位到 upstream/1.26 和 upstream/1.27 版本都是正常的。而 upstream/1.25.2 会出错。进一步二分，找到修复的 commit 是 [libfakeroot.c: add wrappers for new glibc 2.33+ symbols](https://salsa.debian.org/clint/fakeroot/-/commit/feda578ca3608b7fc9a28a3a91293611c0ef47b7)，相关的代码如下：

```diff
+  int mknod(const char *pathname, mode_t mode, dev_t dev) {
+     return WRAP_MKNOD MKNOD_ARG(_STAT_VER, pathname, mode, &dev);
+  }
+
+  #if defined(HAVE_FSTATAT) && defined(HAVE_MKNODAT)
+    int mknodat(int dir_fd, const char *pathname, mode_t mode, dev_t dev) {
+       return WRAP_MKNODAT MKNODAT_ARG(_STAT_VER, dir_fd, pathname, mode, &dev);
+    }
+  #endif
+#endif /* GLIBC_PREREQ */
```

这说明在这个修复之前，不能正确地拦截 mknod 的调用。所以 glibc 2.33+ 要配合 fakeroot 1.26+ 版本才可以正确地运行 fakeroot。

结论：找个时间用新版的 Buildroot 重新构建一份。