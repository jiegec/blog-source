---
layout: post
date: 2023-08-02
tags: [benchmark,spec]
categories:
    - software
---

# SPEC CPU 2006 性能测试

## 背景

最近在网上看到龙芯 3A6000 的 SPEC CPU 2006 性能评测数据，想着自己也可以在手上的一些平台上测一测，把测试的过程记录在本文。

<!-- more -->

## 安装

首先需要获取一份 cpu2006-1.2.iso 文件，md5 可以在 [官网](https://www.spec.org/md5sums.html) 上查到。在 Linux 环境下，mount 这个 iso 并运行里面的 install.sh：

```shell
mount cpu2006-1.2.iso /mnt
cd /mnt
./install.sh
```

按照提示输入安装路径，等待安装完成，然后按照提示进入环境：

```shell
cd /usr/cpu2006
source ./shrc
```

## 配置和运行

接着，需要按照 [SPEC CPU2006 Config Files](https://www.spec.org/cpu2006/Docs/config.html) 的文档编写配置文件。编辑 `config/default.cfg`，写一个基本的配置：

```config
# run one iteration
iterations = 1
# skip peak
basepeak = yes
# show live output
teeout = yes

# optimization flags for base
default=base=default=default:
COPTIMIZE = -O2
CXXOPTIMIZE = -O2
FOPTIMIZE = -O2
```

这样就会用单线程跑一个 `-O2` 优化的 401.bzip2 测例：

```shell
runspec bzip2
```

运行几分钟后，就可以在 result 目录下看到结果，可以看到 bzip2 单项的结果。接下来，尝试运行完整的 SPECint_base2006，修改 `config/default.cfg`：


```config
# match spec result standard
reportable = yes
# skip peak
basepeak = yes
# show live output
teeout = yes

# optimization flags for base
default=base=default=default:
COPTIMIZE = -O2
CXXOPTIMIZE = -O2
FOPTIMIZE = -O2
```

再运行：

```shell
runspec int
```

此时会遇到编译问题，下面来进行解决。

## 编译错误

编译错误实际上是因为现在用的系统太新了，在新系统上编译 2006 年前的代码，必然有各种问题。

### perlbench

遇到的第一个问题是 perlbench：

```shell
pp_sys.c:4489:42: error: invalid use of undefined type 'struct tm'
 4489 |                             dayname[tmbuf->tm_wday],
      |                                          ^~
```

这是因为没有 include time.h，阅读 perlbench 下面的 spec_config.h，可知需要给 perlbench 传单独的编译参数。修改 `config/default.cfg`，添加如下部分：

```
# fix compilation
int=default=default=default:
PORTABILITY = -DSPEC_CPU_LP64

400.perlbench=default=default=default:
CPORTABILITY = -DSPEC_CPU_LINUX_X64
```

表示给所有测例都加上 `SPEC_CPU_LP64` 的定义，perlbench 还要额外定义 `SPEC_CPU_LINUX_X64`。这样 time.h 的问题解决了，接下来遇到了新的问题，链接的时候出现 multiple definition 错误：

```shell
Opcode.c:(.text+0x1b60): multiple definition of `ferror_unlocked'; av.o:av.c:(.text+0x2f0): first defined here
collect2: error: ld returned 1 exit status
```

在网上查找，发现在 [SPEC 2017 FAQ](https://www.spec.org/cpu2017/Docs/faq.html) 里有解决方案，虽然用的是 CPU 2006，但是也一样适用，修改 `config/default.cfg`：

```
# optimization flags for base
default=base=default=default:
COPTIMIZE = -O2 -fgnu89-inline -fcommon
CXXOPTIMIZE = -O2
FOPTIMIZE = -O2

# fix compilation
int=default=default=default:
PORTABILITY = -DSPEC_CPU_LP64

400.perlbench=default=default=default:
CPORTABILITY = -DSPEC_CPU_LINUX_X64
```

### libquantum

下一个编译错误在 libquantum：

```shell
complex.c: In function 'quantum_conj':
complex.c:42:14: error: 'IMAGINARY' undeclared (first use in this function)
   42 |   return r - IMAGINARY * i;
```

和 perlbench 一样，需要额外的宏定义。参考 config 目录下的 Example config，直接把剩下几个都配置上：

```
# fix compilation
int=default=default=default:
PORTABILITY = -DSPEC_CPU_LP64

400.perlbench=default=default=default:
CPORTABILITY = -DSPEC_CPU_LINUX_X64

462.libquantum=default=default=default:
CPORTABILITY = -DSPEC_CPU_LINUX

483.xalancbmk=default=default=default:
CXXPORTABILITY = -DSPEC_CPU_LINUX

481.wrf=default=default=default:
CPORTABILITY = -DSPEC_CPU_CASE_FLAG -DSPEC_CPU_LINUX
```

### omnetpp

下一个错误是 specmake 说 CC not found：

```shell
CC -c -o EtherAppCli.o -DSPEC_CPU -DNDEBUG -I. -Iomnet_include -Ilibs/envir   -O2   -DSPEC_CPU_LP64 -fgnu89-inline -fcommon       EtherAppCli.cc
specmake: CC: Command not found
specmake: *** [EtherAppCli.o] Error 127
```

那就在配置 `config/default.cfg` 里指定绝对路径：

```
# specify compilers
default=default=default=default:
CC = /usr/bin/gcc
CXX = /usr/bin/g++
FC = /usr/bin/gfortran
```

至此所有编译错误都解决了。

### 完整配置

解决编译问题后，完整配置如下：

```
# match spec result standard
reportable = yes
# skip peak
basepeak = yes
# show live output
teeout = yes

# optimization flags for base
default=base=default=default:
COPTIMIZE = -O2 -fgnu89-inline -fcommon
CXXOPTIMIZE = -O2
FOPTIMIZE = -O2

# specify compilers
default=default=default=default:
CC = /usr/bin/gcc
CXX = /usr/bin/g++
FC = /usr/bin/gfortran

# fix compilation
int=default=default=default:
PORTABILITY = -DSPEC_CPU_LP64

400.perlbench=default=default=default:
CPORTABILITY = -DSPEC_CPU_LINUX_X64

462.libquantum=default=default=default:
CPORTABILITY = -DSPEC_CPU_LINUX

483.xalancbmk=default=default=default:
CXXPORTABILITY = -DSPEC_CPU_LINUX

481.wrf=default=default=default:
CPORTABILITY = -DSPEC_CPU_CASE_FLAG -DSPEC_CPU_LINUX
```

此时再运行 `runspec int` 就可以正常跑了。

## 其他 ISA

如果想在 AArch64 上跑，那么安装的时候会发现缺少 prebuilt 的 tools 二进制，此时就要手动按照 [Building the SPEC CPU2006 Tool Suite](https://www.spec.org/cpu2006/Docs/tools-build.html) 进行编译：

```shell
cd tools/src
./buildtools
```

需要注意，这一步需要修改文件系统，所以如果之前是直接 mount ISO，要先复制一份，此外还要把权限改成可写（`chmod -R u+w`）。

运行的时候会遇到错误，可以参考 [Build SPEC CPU2006 in riscv64 linux](https://github.com/GQBBBB/GQBBBB.github.io/issues/10) 解决，riscv64 和 aarch64 的解决方法是类似的：

1. 替换源代码下的几个 config.guess 和 config.sub（在 expat-2.0.1/conftools，make-3.82/config，rxp-1.5.0，specinvoke，specsum/build-aux，tar-1.25/build-aux，xz-5.0.0/build-aux 目录下），解决不认识 aarch64 target triple 的问题
2. 修改 `make-3.82/glob/glob.c`，把 `# if _GNU_GLOB_INTERFACE_VERSION == GLOB_INTERFACE_VERSION` 改成 `# if _GNU_GLOB_INTERFACE_VERSION >= GLOB_INTERFACE_VERSION`，解决 alloca 和 stat 的问题
2. 修改 `make-3.82/make.h`，在 `struct rlimit stack_limit;` 前面添加 `extern`，解决 -fno-common 的问题
3. 修改 `make-3.82/dir.c`，在 `dir_setup_glob` 函数里添加一句 `gl->gl_lstat = lstat;`，解决 `make: ./file.c:158: enter_file: Assertion strcache_iscached (name) failed.` 的问题（参考了 [[PATCH v2] make: 4.2.1 -> 4.3](https://lore.kernel.org/all/20200122223655.2569-1-sno@netbsd.org/T/)）
4. 修改 `tar-1.25/gnu/stdio.in.h` 和 `specsum/gnulib/stdio.in.h`，找到 `_GL_WARN_ON_USE (gets, "gets is a security hole - use fgets instead");` 一句，注释掉，解决 gets undefined 的问题（参考了 [CentOS下Git升级](https://blog.csdn.net/turbock/article/details/108851022)）
5. 修改 `buildtools`，在 perl 的 configure 命令中的 `-A ldflags` 附近，把 `-A libs=-lm` 添加到命令中，解决找不到 math 函数的问题（参考 [https://serverfault.com/a/801997/323597](https://serverfault.com/questions/761966/building-old-perl-from-source-how-to-add-math-library)）

## 自己测的数据

下面贴出自己测的数据（Estimated），不保证满足 SPEC 的要求，仅供参考。

- i9-13900K（`-O2`）: SPECint2006 79.6
- i9-13900K（`-Ofast -fomit-frame-pointer -march=native -mtune=native`）: SPECint2006
