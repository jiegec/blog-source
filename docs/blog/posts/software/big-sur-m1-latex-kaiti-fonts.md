---
layout: post
date: 2021-02-09
tags: [c++,fortran,gcc,clang,ld,linking,symbols,objdump]
categories:
    - software
---

# 在 Big Sur(M1) 上解决 LaTeX 找不到楷体字体的问题

## 背景

最近在尝试移植 [MiKTeX 到 Apple Silicon 上](https://github.com/MiKTeX/miktex/pull/710)，添加了一些 patch 以后就可以工作了，但遇到了新的问题，即找不到 KaiTi

```shell
~/Library/Application Support/MiKTeX/texmfs/install/tex/latex/ctex/fontset/ctex-fontset-macnew.def:99:
   Package fontspec Error:
      The font "Kaiti SC" cannot be found.
```

用 `miktex-fc-list` 命令找了一下，确实没有找到：

```shell
$ /Applications/MiKTeX\ Console.app/Contents/bin/miktex-fc-list | grep Kaiti
# Nothing
```

上网搜了一下，找到了一个[解决方案](https://www.jianshu.com/p/8f35c57901e3)：字体在目录 `/System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/ATS.framework/Versions/A/Support/FontSubsets/Kaiti.ttc` 里，所以手动安装一下，就可以让 LaTeX 找到了。但我觉得，与其安装多一份在文件系统里，不如让 LaTeX 去找它。

## 解决方法

按照上面的线索，找到了 `Kaiti.ttc` 所在的路径：

```shell
$ fd Kaiti.ttc
/System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets/Kaiti.ttc
```

可以看到，和上面的路径又不大一样。研究了一下 fontconfig，发现可以用 `miktex-fc-conflist` 找到配置文件的目录：

```shell
$ /Applications/MiKTeX\ Console.app/Contents/bin/miktex-fc-conflist
+ ~/Library/Application Support/MiKTeX/texmfs/config/fontconfig/config/localfonts2.conf: No description
+ ~/Library/Application Support/MiKTeX/texmfs/config/fontconfig/config/localfonts.conf: No description
...
```

看了下第一个文件（localfonts.conf）：

```xml
<?xml version="1.0" encoding="UTF-8"?>

<!--
  DO NOT EDIT THIS FILE! It will be replaced when MiKTeX is updated.
  Instead, edit the configuration file localfonts2.conf.
-->

<fontconfig>
<include>localfonts2.conf</include>
<dir>/Library/Fonts/</dir>
<dir>/System/Library/Fonts/</dir>
<dir>~/Library/Application Support/MiKTeX/texmfs/install/fonts/type1</dir>
<dir>~/Library/Application Support/MiKTeX/texmfs/install/fonts/opentype</dir>
<dir>~/Library/Application Support/MiKTeX/texmfs/install/fonts/truetype</dir>
</fontconfig>
```

可以看到，我们可以添加路径，不过建议修改的是 `localfonts2.conf`。按照类似的格式，修改成：

```xml
<?xml version="1.0"?>
<fontconfig>
<dir>/System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets</dir>
<!-- REMOVE THIS LINE
<dir>Your font directory here</dir>
<dir>Your font directory here</dir>
<dir>Your font directory here</dir>
     REMOVE THIS LINE -->
</fontconfig>
```

UPDATE: 新版本 macOS 中，路径建议加上 `/System/Library/AssetsV2/com_apple_MobileAsset_Font7`：

```xml
<dir>/System/Library/AssetsV2/com_apple_MobileAsset_Font7</dir>
```

这样，就可以找到 Kaiti SC 了：

```shell
$ miktex-fc-list | grep Kaiti
/System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets/Kaiti.ttc: Kaiti TC,楷體\-繁,楷体\-繁:style=Regular,標準體,常规体
/System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets/Kaiti.ttc: Kaiti SC,楷體\-簡,楷体\-简:style=Regular,標準體,常规体
/System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets/Kaiti.ttc: Kaiti SC,楷體\-簡,楷体\-简:style=Bold,粗體,粗体
/System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets/Kaiti.ttc: Kaiti TC,楷體\-繁,楷体\-繁:style=Bold,粗體,粗体
/System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets/Kaiti.ttc: Kaiti SC,楷體\-簡,楷体\-简:style=Black,黑體,黑体
/System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets/Kaiti.ttc: Kaiti TC,楷體\-繁,楷体\-繁:style=Black,黑體,黑体
/System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets/Kaiti.ttc: STKaiti:style=Regular,標準體,Ordinær,Normal,Normaali,Regolare,レギュラー,일반체,Regulier,Обычный,常规体
```

这样就搞定了，用 LaTeX 找字体的时候也没有出现问题了。

如果你用的是 TeX Live，那么直接把上面的 Kaiti.ttc 路径复制到 `~/Library/Fonts` 下即可。

如果是用 Nixpkgs 装的 Tex Live，则建议用符号链接的方法，把相关的字体添加到 `~/Library/Fonts` 下：

```shell
cd ~/Library/Fonts
ln -s /System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets/华文细黑.ttf # STHeiti
ln -s /System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets/华文黑体.ttf # STHeiti
ln -s /System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets/华文仿宋.ttf # STFangsong
ln -s /System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets/Kaiti.ttc # STKaiti
```

寻找系统自带字体文件和对应字体名字的方法：

```shell
fc-scan /System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/Subsets
```
