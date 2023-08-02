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

## 基本概念

SPEC CPU 2006 分 int 和 fp 两种，又分不同的模式：

1. speed：跑单进程，看看单进程多少时间能完成；不开 OpenMP，但是编译器可以自动并行化（ICC）
2. rate：跑多进程，看看单位时间内能跑多少个任务

根据编译选项的不同，分为：

1. base：所有测例都用同样的优化选项
2. peak：不同测例可以用不同的优化选项

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

### gamess

gamess 是 SPECfp 里面的测例，编译的时候报错：

```
aldeci.fppized.f:1674:72:

 1674 |       CALL BINOM6(X(LIFA),NACT)
      |                                                                        1
Error: Type mismatch in argument 'ifa' at (1); passed REAL(8) to INTEGER(4)
```

参考 [Disable argument-mismatch errors for SPEC CPU2006 416.gamess for GCC >= 8](https://github.com/advancetoolchain/advance-toolchain/issues/549)，添加编译选项 `-std=legacy` 来解决：

```
# optimization flags for base
default=base=default=default:
COPTIMIZE = -O2 -fgnu89-inline -fcommon
CXXOPTIMIZE = -O2
FOPTIMIZE = -O2 -std=legacy
```

### dealII

dealII 是 SPECfp 里面的测例，编译的时候报错：

```shell
parameter_handler.cc: In member function 'long int ParameterHandler::get_integer(const std::string&) const':
parameter_handler.cc:763:26: error: ISO C++ forbids comparison between pointer and integer [-fpermissive]
  763 |   AssertThrow ((s.c_str()!='\0') || (*endptr == '\0'),
      |                 ~~~~~~~~~^~~~~~
include/base/exceptions.h:596:15: note: in definition of macro 'AssertThrow'
  596 |         if (!(cond))                                                 \
      |               ^~~~
```

编译选项打开 `-fpermissive` 即可：

```
# optimization flags for base
default=base=default=default:
COPTIMIZE = -O2 -fgnu89-inline -fcommon
CXXOPTIMIZE = -O2 -fpermissive
FOPTIMIZE = -O2 -std=legacy
```

### soplex

soplex 是 SPECfp 里面的测例，编译的时候报错：

```shell
mpsinput.cc: In member function 'bool soplex::MPSInput::readLine()':
mpsinput.cc:75:52: error: no match for 'operator==' (operand types are 'std::basic_istream<char>::__istream_type' {aka 'std::basic_istream<char>'} and 'int')
   75 |          if (m_input.getline(m_buf, sizeof(m_buf)) == 0)
      |              ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ^~ ~
      |                             |                         |
      |                             |                         int
      |                             std::basic_istream<char>::__istream_type {aka std::basic_istream<char>}
```

解决办法：降低 C++ 标准版本：

```
# optimization flags for base
default=base=default=default:
COPTIMIZE = -O2 -fgnu89-inline -fcommon
CXXOPTIMIZE = -O2 -fpermissive --std=c++98
FOPTIMIZE = -O2 -std=legacy
```

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
CXXOPTIMIZE = -O2 -fpermissive --std=c++98
FOPTIMIZE = -O2 -std=legacy

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
2. 修改 `make-3.82/glob/glob.c`，把 `# if _GNU_GLOB_INTERFACE_VERSION == GLOB_INTERFACE_VERSION` 改成 `# if _GNU_GLOB_INTERFACE_VERSION >= GLOB_INTERFACE_VERSION`，禁用 make 自带的 glob 实现，解决 alloca 和 stat 的问题

    ```diff
    @@ -52,7 +52,7 @@
     #define GLOB_INTERFACE_VERSION 1
     #if !defined _LIBC && defined __GNU_LIBRARY__ && __GNU_LIBRARY__ > 1
     # include <gnu-versions.h>
    -# if _GNU_GLOB_INTERFACE_VERSION == GLOB_INTERFACE_VERSION
    +# if _GNU_GLOB_INTERFACE_VERSION >= GLOB_INTERFACE_VERSION
     #  define ELIDE_CODE
     # endif
     #endif
    ```

3. 修改 `make-3.82/make.h`，在 `struct rlimit stack_limit;` 前面添加 `extern`，解决 -fno-common 的问题

    ```diff
    @@ -344,7 +344,7 @@
     #endif
     #ifdef SET_STACK_SIZE
     # include <sys/resource.h>
    -struct rlimit stack_limit;
    +extern struct rlimit stack_limit;
     #endif
    
     struct floc
    ```

4. 修改 `make-3.82/dir.c`，在 `dir_setup_glob` 函数里添加一句 `gl->gl_lstat = lstat;`，解决 `make: ./file.c:158: enter_file: Assertion strcache_iscached (name) failed.` 的问题（参考了 [[PATCH v2] make: 4.2.1 -> 4.3](https://lore.kernel.org/all/20200122223655.2569-1-sno@netbsd.org/T/)）

    ```diff
    @@ -1213,6 +1213,7 @@
       gl->gl_readdir = read_dirstream;
       gl->gl_closedir = ansi_free;
       gl->gl_stat = local_stat;
    +  gl->gl_lstat = lstat;
       /* We don't bother setting gl_lstat, since glob never calls it.
          The slot is only there for compatibility with 4.4 BSD.  */
     }
    ```

5. 修改 `tar-1.25/gnu/stdio.in.h` 和 `specsum/gnulib/stdio.in.h`，找到 `_GL_WARN_ON_USE (gets, "gets is a security hole - use fgets instead");` 一句，注释掉，解决 gets undefined 的问题（参考了 [CentOS下Git升级](https://blog.csdn.net/turbock/article/details/108851022)）

    ```diff
    @@ -159,7 +159,7 @@
        so any use of gets warrants an unconditional warning.  Assume it is
        always declared, since it is required by C89.  */
     #undef gets
    -_GL_WARN_ON_USE (gets, "gets is a security hole - use fgets instead");
    +// _GL_WARN_ON_USE (gets, "gets is a security hole - use fgets instead");
    
     #if @GNULIB_FOPEN@
     # if @REPLACE_FOPEN@
    ```

6. 修改 `buildtools`，在 perl 的 configure 命令中的 `-A ldflags` 附近，把 `-A libs=-lm -A ccflags=-fwrapv` 添加到命令中，解决找不到 math 函数的问题和 numconvert.t 测试失败的问题（参考 [https://serverfault.com/a/801997/323597](https://serverfault.com/questions/761966/building-old-perl-from-source-how-to-add-math-library) 和 [如何在Hifive Unmatched开发板上安装SPEC CPU 2006](https://zhuanlan.zhihu.com/p/441856175)）：

    ```diff
    @@ -355,7 +355,7 @@
         LD_LIBRARY_PATH=`pwd`
         DYLD_LIBRARY_PATH=`pwd`
         export LD_LIBRARY_PATH DYLD_LIBRARY_PATH
    -    ./Configure -dOes -Ud_flock $PERLFLAGS -Ddosuid=undef -Dprefix=$INSTALLDIR -Dd_bincompat3=undef -A ldflags=-L${INSTALLDIR}/lib -A ccflags=-I${INSTALLDIR}/include -Ui_db -Ui_gdbm -Ui_ndbm -Ui_dbm -Uuse5005threads ; testordie "error configuring perl"
    +    ./Configure -dOes -Ud_flock $PERLFLAGS -Ddosuid=undef -Dprefix=$INSTALLDIR -Dd_bincompat3=undef -A libs=-lm -A ccflags=-fwrapv -A ldflags="-L${INSTALLDIR}/lib" -A ccflags="-I${INSTALLDIR}/include -g" -Ui_db -Ui_gdbm -Ui_ndbm -Ui_dbm -Uuse5005threads ; testordie "error configuring perl"
         $MYMAKE; testordie "error building Perl"
         ./perl installperl; testordie "error installing Perl"
         setspecperllib
    ```

7. 修改 `perl-5.12.3/Configure`，把判断 GCC 版本的 `1*` 都改成 `1.*`，解决 miniperl Segmentation fault 的问题（参考 [unmatched(riscv64)上编译,安装和移植SPEC CPU 2006](https://zhuanlan.zhihu.com/p/429399630)）

    ```diff
    @@ -4536,7 +4536,7 @@
     fi
     $rm -f try try.*
     case "$gccversion" in
    -1*) cpp=`./loc gcc-cpp $cpp $pth` ;;
    +1.*) cpp=`./loc gcc-cpp $cpp $pth` ;;
     esac
     case "$gccversion" in
     '') gccosandvers='' ;;
    @@ -5128,7 +5140,7 @@
     case "$hint" in
     default|recommended)
            case "$gccversion" in
    -       1*) dflt="$dflt -fpcc-struct-return" ;;
    +       1.*) dflt="$dflt -fpcc-struct-return" ;;
            esac
            case "$optimize:$DEBUGGING" in
            *-g*:old) dflt="$dflt -DDEBUGGING";;
    @@ -5143,7 +5155,7 @@
                    ;;
            esac
            case "$gccversion" in
    -       1*) ;;
    +       1.*) ;;
            2.[0-8]*) ;;
            ?*)     set strict-aliasing -fno-strict-aliasing
                    eval $checkccflag
    @@ -5245,7 +5257,7 @@
     *)  cppflags="$cppflags $ccflags" ;;
     esac
     case "$gccversion" in
    -1*) cppflags="$cppflags -D__GNUC__"
    +1.*) cppflags="$cppflags -D__GNUC__"
     esac
     case "$mips_type" in
     '');;
    ```

8. 修改 `perl-5.12.3/Configure`，在 `if $ok; then` 后面加上如下代码，解决 magic.t 测试失败的问题（参考 [如何在Hifive Unmatched开发板上安装SPEC CPU 2006](https://zhuanlan.zhihu.com/p/441856175) 和 [Tests fail with GCC 5.0 because Errno cannot obtain errno constants](https://github.com/Perl/perl5/issues/14491)）：

    ```
    elif echo 'Maybe "'"$cc"' -E -ftrack-macro-expansion=0" will work...'; \
           $cc -E -ftrack-macro-expansion=0 <testcpp.c >testcpp.out 2>&1; \
           $contains 'abc.*xyz' testcpp.out >/dev/null 2>&1 ; then
           echo "Yup, it does."
           x_cpp="$cc $cppflags -E -ftrack-macro-expansion=0"
           x_minus='';
    elif echo 'Maybe "'"$cc"' -E -ftrack-macro-expansion=0 -" will work...';
           $cc -E -ftrack-macro-expansion=0 - <testcpp.c >testcpp.out 2>&1; \
           $contains 'abc.*xyz' testcpp.out >/dev/null 2>&1 ; then
           echo "Yup, it does."
           x_cpp="$cc $cppflags -E -ftrack-macro-expansion=0"
           x_minus='-';
    ```

    ```diff
    @@ -4688,6 +4688,18 @@
    
     if $ok; then
            : nothing
    +elif echo 'Maybe "'"$cc"' -E -ftrack-macro-expansion=0" will work...'; \
    +       $cc -E -ftrack-macro-expansion=0 <testcpp.c >testcpp.out 2>&1; \
    +       $contains 'abc.*xyz' testcpp.out >/dev/null 2>&1 ; then
    +       echo "Yup, it does."
    +       x_cpp="$cc $cppflags -E -ftrack-macro-expansion=0"
    +       x_minus='';
    +elif echo 'Maybe "'"$cc"' -E -ftrack-macro-expansion=0 -" will work...';
    +       $cc -E -ftrack-macro-expansion=0 - <testcpp.c >testcpp.out 2>&1; \
    +       $contains 'abc.*xyz' testcpp.out >/dev/null 2>&1 ; then
    +       echo "Yup, it does."
    +       x_cpp="$cc $cppflags -E -ftrack-macro-expansion=0"
    +       x_minus='-';
     elif echo 'Maybe "'"$cc"' -E" will work...'; \
            $cc -E <testcpp.c >testcpp.out 2>&1; \
            $contains 'abc.*xyz' testcpp.out >/dev/null 2>&1 ; then
    ```

9. 修改 `TimeDate-1.20/t/getdate.t` 的 `my $offset = Time::Local::timegm(0,0,0,1,0,70);` 为 `my $offset = Time::Local::timegm(0,0,0,1,0,1970);`，解决 `error running TimeDate-1.20 test suite` 报错（参考 [unmatched(riscv64)上编译,安装和移植SPEC CPU 2006](https://zhuanlan.zhihu.com/p/429399630)）：

    ```diff
    @@ -156,7 +156,7 @@
    !;

    require Time::Local;
    -my $offset = Time::Local::timegm(0,0,0,1,0,70);
    +my $offset = Time::Local::timegm(0,0,0,1,0,1970);

    @data = split(/\n/, $data);
    ```

这样就可以正常完成 `./buildtools` 了，中间 perl 测试出错，按 `y` 忽略即可。

编译完成以后，回到复制后的 ISO 根目录进行打包，打包完正常安装即可：

```shell
source shrc
packagetools linux-aarch64
export SPEC_INSTALL_NOCHECK=1
./install.sh -d /install/path
```

添加 `export SPEC_INSTALL_NOCHECK=1` 环境变量是因为修改了源码，md5 对不上，所以要跳过校验。

在 AArch64 上跑 SPEC 的时候，可能会遇到 [Miscompare #7](https://www.spec.org/cpu2006/Docs/faq.html#Miscompare.07)，在编译选项里加上 `-fsigned-char` 即可：

```
# fix compilation and miscompare
int=default=default=default:
PORTABILITY = -DSPEC_CPU_LP64 -fsigned-char
```

## 自己测的数据

因为 GCC 没有自动并行化，所以都是单核运行。跑一次测试要 5000+/17000+ 秒。

实测在 -Ofast 编译选项下，SPECfp 里的 gamess 和 bwaves 会失败，改成 -O3/-O2/-O1 以后 gamess 依然失败，只有不开 -O 或者 -O0 才能跑通 gamess。所以就不测 SPECfp 了，只测 SPECint。

下面贴出自己测的数据（Estimated，base），不保证满足 SPEC 的要求，仅供参考。

- i9-13900K Raptor Lake（`-O2`）: SPECint2006 79.6
- i9-13900K Raptor Lake（`-Ofast -fomit-frame-pointer -march=native -mtune=native`）: SPECint2006 85.3 86.8
- Kunpeng 920 TaiShan V110（`-O2`）: SPECint2006 23.3

## 网上的数据

### Speed（SPECint2006）

[Anandtech 的数据](https://www.anandtech.com/show/16084/intel-tiger-lake-review-deep-dive-core-11th-gen/8)：

- i9-10900K Comet Lake: 58.76
- R9 3950X Zen 2: 50.02
- R7 4800U Zen 2: 37.10
- Amazon Graviton 2 Neoverse-N1: 29.99

[Anandtech 的数据](https://www.anandtech.com/show/14694/amd-rome-epyc-2nd-gen/9)：

- EPYC 7742 Zen 2: 39.25
- EPYC 7601 Zen 1: 31.45

[Baikal 的数据](https://www.163.com/dy/article/IB0CL7PU0511838M.html):

- Baikal-S：19
- Kunpeng 920: 26

### Rate（SPECint_rate2006）

[Kunpeng 920 官方数据](https://www.hisilicon.com/en/products/Kunpeng/Huawei-Kunpeng/Huawei-Kunpeng-920)：

- Kunpeng 920 64 Cores: >930

[夏晶的数据](https://www.zhihu.com/question/308299017/answer/592860614)：

- AMD Zen 2 64 Cores: ~1200
- Intel Skylake 8180 v5 28 Cores: ~750
- Cavium TX2 32 Cores: ~750
- AMD Zen 1 7601 32 Cores: ~700
- Qualcomm 2400 48 Cores: ~650
- Phytium FT2000 64 Cores: ~600
- intel skylake 6148 v5 20 Cores: ~550