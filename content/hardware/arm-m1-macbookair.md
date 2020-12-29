---
layout: post
date: 2020-11-19 18:35:00 +0800
tags: [m1,macbookair,applesilicon,macos,arm,arm64]
category: hardware
title: ARM M1 MacBook Air 开箱
---

# 购买

我是 11.12 的时候在 Apple Store 上下单的，选的是 MacBookAir ，带 M1 芯片，8 核 CPU + 8 核 GPU，加了一些内存和硬盘。今天（11.19）的时候顺丰到货，比 Apple Store 上显示的预计到达时间 21-28 号要更早。另外，我也听朋友说现在一些线下的店也有货，也有朋友直接在京东上买到了 Mac mini，总之第一波 M1 的用户最近应该都可以拿到设备了。

现在这篇博客，就是在 ARM MBA 上编写的，使用的是 Intel 的 VSCode，毕竟 VSCode 的 ARM64 版不久后才正式发布。

# 开箱

从外观来看，一切都和 Intel MBA 一样，包装上也看不出区别，模具也是一样的。

![](/arm_mac_1.png)

进了系统才能看得出区别。预装的系统是 macOS Big Sur 11.0，之后手动更新到了目前最新的 11.0.1。

顺带 @FactorialN 同学提醒我在这里提一句：包装里有电源适配器，不太环保。

# 体验

## ARM64

首先自然是传统艺能，证明一下确实是 Apple Silicon：

```shell
$ uname -a
Darwin macbookair.lan 20.1.0 Darwin Kernel Version 20.1.0: Sat Oct 31 00:07:10 PDT 2020; root:xnu-7195.50.7~2/RELEASE_ARM64_T8101 x86_64
```

啊对不起我用错了，上面是在 Rosetta 里面跑的 shell 看到的结果。实际是这样子的：

```shell
$ uname -a
Darwin macbookair.lan 20.1.0 Darwin Kernel Version 20.1.0: Sat Oct 31 00:07:10 PDT 2020; root:xnu-7195.50.7~2/RELEASE_ARM64_T8101 arm64
```

货真价实的 ARM64 内核，系统的很多 binary 也都是 Universal 的：

```shell
$ file /bin/bash
/bin/bash: Mach-O universal binary with 2 architectures: [x86_64:Mach-O 64-bit executable x86_64] [arm64e:Mach-O 64-bit executable arm64e]
/bin/bash (for architecture x86_64):	Mach-O 64-bit executable x86_64
/bin/bash (for architecture arm64e):	Mach-O 64-bit executable arm64e
```

## Rosetta

接着，就是重头戏 Rosetta 了。第一次打开 Intel 的程序的时候，会弹出窗口安装 Rosetta，确定以后立马就装好了。接着常用的各种软件啥的，都没有什么问题。

唯一能看出区别的，就是在 Activity Monitor 可以看到架构的区别：

![](/arm_mac_2.png)

实际体验的时候，其实没有什么感觉。默认情况下，在 Terminal 下打开的是 ARM64 架构的，如果要切换的话，只需要：

```shell
$ uname -m
arm64
$ arch -arch x86_64 uname -m
x86_64
```

这样就可以了。如果开了一个 x86_64 的 shell，在 shell 里面执行的命令就都是 x86_64 架构的了。

## Homebrew

目前，Homebrew 的支持是这样子的，Intel 的 Homebrew 工作很正常，没有遇到任何问题。。ARM 的 Homebrew 目前还在进行移植，由于官方的 build farm 还没有支持 ARM，所以各种包都需要自己编译，试了几个常用的软件都没问题。

目前 Homebrew 推荐的方法是，在老地方 `/usr/local/Homebrew` 下面放 Intel 的 Homebrew，在 `/opt/homebrew` 下面放 ARM 的 Homebrew。虽然还是有很多警告，但目前来看基本使用都没有什么问题。Homebrew cask 也正常，毕竟基本就是一个下载器。

另外，试了一下用 ARM Homebrew 从源码编译 GCC，编译中途失败了。

## 其他软件

换到 ARM 上自然会想到，之前的那些软件还能不能跑。答案是，大多都可以，只是很多还是 Intel 版走翻译而已。

目前已经测试过正常使用的：VSCode、Google Chrome、Alacrity、iStat Menus、Alfred、Rectangle、Typora、Microsoft Office、Karabiner Elements、Jetbrains Toolbox、WeChat、CineBench、Dozer、Squirrel、Zoom、Tencent Meeting、Seafile、Skim、Mendeley、1 Password、Wireshark、Slack、iMazing、Office for Mac。

这些里面已经移植到 ARM64 的有 Alfred、iStat Menus、Karabiner Elements、Rectangle、Google Chrome、Slack、Typora、iMazing、Office for Mac、Zoom、VSCode Insiders。

这里有一部分是已经移植到 ARM64 的，有一些也很快就会移植过来。其中 iStat Menus 的电池健康显示有点 BUG，其他没发现问题（更新：已修复）。

另外，大家也知道 ARM Mac 很重要的一点是可以跑 iOS Apps，我们也确实跑了一些，不过都有一些问题：

- Doodle Jump：跑起来很正常，就是卡关了，别问为什么，没有加速度计，再怎么晃电脑也不会动
- Bilibili：部分内容可以加载出来，部分不可以，估计是什么组件没有配置好
- QQ Music：可以跑起来，但是在启动之后的引导页面，期望用户点一下屏幕，但怎么用鼠标点都没反应
- Weibo：毕竟正常，可以正常浏览啥都，就是 UI 有点错位，估计是因为显示窗口和实际都不大一样，小问题。
- Network Tools：很正常，各种网络信息都可以正常取出来。
- NFSee：没有 NFC 读卡功能，自然没法用。
- 彩云天气（ColorfulClouds Weather）：正常使用。

其他还有很多 App 还没有测试。

## 发热

大家也知道，这款 MBA 是没有风扇的。但我实际测试的过程中发现，确实不大需要。拿 stress 跑了一段时间 CPU 满载运行，也没感觉到电脑发热，只是在更新 macOS Big Sur 11.0.1 的时候稍微热了一点点，也只是一点点，距离烫手还有很长的距离。

续航方面目前来看也挺好的，捣鼓了一个下午，也没耗多少电。

## 性能测试

在不同平台上进行 OpenSSL 测试：

```shell
$ openssl speed aes-128-cbc aes-256-cbc des-ede3 rsa2048 sha256 
# M1 MacBookAir OpenSSL w/ AArch64 ASM enabled
OpenSSL 1.1.1h  22 Sep 2020
built on: Tue Nov 24 01:17:25 2020 UTC
options:bn(64,64) rc4(int) des(int) aes(partial) idea(int) blowfish(ptr)
compiler: clang -fPIC -arch arm64 -O3 -Wall -DL_ENDIAN -DOPENSSL_PIC -DOPENSSL_CPUID_OBJ -DOPENSSL_BN_ASM_MONT -DSHA1_ASM -DSHA256_ASM -DSHA512_ASM -DKECCAK1600_ASM -DVPAES_ASM -DECP_NISTZ256_ASM -DPOLY1305_ASM -D_REENTRANT -DNDEBUG
The 'numbers' are in 1000s of bytes per second processed.
type             16 bytes     64 bytes    256 bytes   1024 bytes   8192 bytes  16384 bytes
des ede3         30345.42k    30462.29k    30720.51k    30620.67k    30702.19k    30692.69k
aes-128 cbc     304095.84k   318020.97k   318105.51k   315161.26k   317307.12k   317466.03k
aes-256 cbc     231153.93k   237928.01k   232901.21k   236751.53k   238025.55k   237524.16k
sha256          377327.95k  1101483.62k  1853731.02k  2272785.12k  2427495.08k  2442317.40k
                  sign    verify    sign/s verify/s
rsa 2048 bits 0.000559s 0.000014s   1787.7  69910.5
# AMD EPYC 7551 OpenSSL
OpenSSL 1.1.1d  10 Sep 2019
built on: Mon Apr 20 20:23:01 2020 UTC
options:bn(64,64) rc4(8x,int) des(int) aes(partial) blowfish(ptr)
compiler: gcc -fPIC -pthread -m64 -Wa,--noexecstack -Wall -Wa,--noexecstack -g -O2 -fdebug-prefix-map=/build/openssl-8Ocme2/openssl-1.1.1d=. -fstack-protector-strong -Wformat -Werror=format-security -DOPENSSL_USE_NODELETE -DL_ENDIAN -DOPENSSL_PIC -DOPENSSL_CPUID_OBJ -DOPENSSL_IA32_SSE2 -DOPENSSL_BN_ASM_MONT -DOPENSSL_BN_ASM_MONT5 -DOPENSSL_BN_ASM_GF2m -DSHA1_ASM -DSHA256_ASM -DSHA512_ASM -DKECCAK1600_ASM -DRC4_ASM -DMD5_ASM -DAESNI_ASM -DVPAES_ASM -DGHASH_ASM -DECP_NISTZ256_ASM -DX25519_ASM -DPOLY1305_ASM -DNDEBUG -Wdate-time -D_FORTIFY_SOURCE=2
The 'numbers' are in 1000s of bytes per second processed.
type             16 bytes     64 bytes    256 bytes   1024 bytes   8192 bytes  16384 bytes
des ede3         20908.92k    21132.29k    21282.73k    21310.12k    21241.86k    21293.74k
aes-128 cbc     160187.39k   166072.96k   167093.25k   168903.34k   168523.09k   168940.89k
aes-256 cbc     121768.89k   125651.37k   126532.18k   126644.91k   126440.79k   127325.53k
sha256          147462.49k   381143.42k   782357.16k  1092831.23k  1236314.79k  1247537.83k
                  sign    verify    sign/s verify/s
rsa 2048 bits 0.001097s 0.000033s    911.7  30344.2
# Intel Xeon E5-2680 v4 (Broadwell) OpenSSL
OpenSSL 1.0.2g  1 Mar 2016
built on: reproducible build, date unspecified
options:bn(64,64) rc4(16x,int) des(idx,cisc,16,int) aes(partial) blowfish(idx)
compiler: cc -I. -I.. -I../include  -fPIC -DOPENSSL_PIC -DOPENSSL_THREADS -D_REENTRANT -DDSO_DLFCN -DHAVE_DLFCN_H -m64 -DL_ENDIAN -g -O2 -fstack-protector-strong -Wformat -Werror=format-security -Wdate-time -D_FORTIFY_SOURCE=2 -Wl,-Bsymbolic-functions -Wl,-z,relro -Wa,--noexecstack -Wall -DMD32_REG_T=int -DOPENSSL_IA32_SSE2 -DOPENSSL_BN_ASM_MONT -DOPENSSL_BN_ASM_MONT5 -DOPENSSL_BN_ASM_GF2m -DSHA1_ASM -DSHA256_ASM -DSHA512_ASM -DMD5_ASM -DAES_ASM -DVPAES_ASM -DBSAES_ASM -DWHIRLPOOL_ASM -DGHASH_ASM -DECP_NISTZ256_ASM
The 'numbers' are in 1000s of bytes per second processed.
type             16 bytes     64 bytes    256 bytes   1024 bytes   8192 bytes
des ede3         27937.45k    28254.25k    28298.84k    28288.68k    28270.59k
aes-128 cbc     128697.71k   141368.87k   144291.16k   145353.73k   145782.10k
aes-256 cbc      93993.22k   100904.09k   102572.29k   103140.01k   103230.12k
sha256           70095.90k   164419.73k   308743.00k   388798.12k   420260.52k
                  sign    verify    sign/s verify/s
rsa 2048 bits 0.000646s 0.000019s   1546.9  52719.7
# Intel Xeon Gold 5218 (Cascade Lake) OpenSSL
OpenSSL 1.1.1d  10 Sep 2019
built on: Mon Apr 20 20:23:01 2020 UTC
options:bn(64,64) rc4(16x,int) des(int) aes(partial) blowfish(ptr)
compiler: gcc -fPIC -pthread -m64 -Wa,--noexecstack -Wall -Wa,--noexecstack -g -O2 -fdebug-prefix-map=/build/openssl-8Ocme2/openssl-1.1.1d=. -fstack-protector-strong -Wformat -Werror=format-security -DOPENSSL_USE_NODELETE -DL_ENDIAN -DOPENSSL_PIC -DOPENSSL_CPUID_OBJ -DOPENSSL_IA32_SSE2 -DOPENSSL_BN_ASM_MONT -DOPENSSL_BN_ASM_MONT5 -DOPENSSL_BN_ASM_GF2m -DSHA1_ASM -DSHA256_ASM -DSHA512_ASM -DKECCAK1600_ASM -DRC4_ASM -DMD5_ASM -DAESNI_ASM -DVPAES_ASM -DGHASH_ASM -DECP_NISTZ256_ASM -DX25519_ASM -DPOLY1305_ASM -DNDEBUG -Wdate-time -D_FORTIFY_SOURCE=2
The 'numbers' are in 1000s of bytes per second processed.
type             16 bytes     64 bytes    256 bytes   1024 bytes   8192 bytes  16384 bytes
des ede3         31859.82k    32367.83k    32325.29k    32363.86k    32388.44k    32440.32k
aes-128 cbc     248045.72k   257097.86k   257922.99k   261073.92k   260590.25k   260483.75k
aes-256 cbc     189070.60k   193881.34k   194477.40k   195246.76k   195163.48k   195641.34k
sha256           85306.65k   193124.61k   355518.55k   447338.15k   481337.34k   484294.66k
                  sign    verify    sign/s verify/s
rsa 2048 bits 0.000544s 0.000016s   1839.6  62426.2
# IBM POWER8NVL OpenSSL
OpenSSL 1.0.2g  1 Mar 2016
built on: reproducible build, date unspecified
options:bn(64,64) rc4(ptr,char) des(idx,risc1,16,long) aes(partial) blowfish(idx)
compiler: cc -I. -I.. -I../include  -fPIC -DOPENSSL_PIC -DOPENSSL_THREADS -D_REENTRANT -DDSO_DLFCN -DHAVE_DLFCN_H -m64 -DL_ENDIAN -g -O3 -fstack-protector-strong -Wformat -Werror=format-security -Wdate-time -D_FORTIFY_SOURCE=2 -Wl,-Bsymbolic-functions -Wl,-z,relro -Wa,--noexecstack -Wall -DOPENSSL_BN_ASM_MONT -DSHA1_ASM -DSHA256_ASM -DSHA512_ASM -DAES_ASM -DVPAES_ASM
The 'numbers' are in 1000s of bytes per second processed.
type             16 bytes     64 bytes    256 bytes   1024 bytes   8192 bytes
des ede3         18783.27k    18991.25k    19043.67k    18974.04k    18972.67k
aes-128 cbc     106504.73k   110757.33k   113190.23k   113867.43k   114065.41k
aes-256 cbc      80060.80k    82383.13k    83770.20k    84134.57k    84243.80k
sha256           59540.44k   150015.98k   284114.35k   369889.62k   405607.77k
                  sign    verify    sign/s verify/s
rsa 2048 bits 0.003516s 0.000096s    284.4  10383.2
```

## 总结

总的来说，还是挺香的。不错的性能，没有风扇的喧闹，没有烫手的键盘。可能有少部分软件还不能正常运行，然后很多程序还需要 Rosetta 翻译，但目前来看兼容性还是挺不错的，并且这些应该明年就都适配地差不多了吧。