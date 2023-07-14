---
layout: post
date: 2019-08-12 20:18:00 +0800
tags: [linux,fb,framebuffer,fbgrab,fbdump]
category: software
title: 在 Linux 下捕获 Framebuffer
---

最近需要在 linux 下抓取 Framebuffer 的内容，在网上找到了两种方法，在我这里只有第二、第三种可以成功，没有细究具体原因，可能与我的 Framebuffer 配置有关。方法如下：

1. `fbgrab` ：命令就是 fbgrab image.png，直接得到 png 文件，格式是对的，但是用软件打开就是一片空白。用 ImageMagick 转换为 jpg 可以看到一些内容，但是和实际有些不一样。
2.  `fbdump` ：命令就是 fbdump > image.ppm，得到裸的 ppm 文件，图像是正确的，也可以转换为别的格式正常打开。
3. cat+脚本处理：直接 cat /dev/fb0 > image.rgb，然后用下面的脚本转换为 png。由于 Framebuffer 格式为 RGB，本来 A 所在的 channel 都为 0，所以用一些软件直接打开都是空白，只好写了脚本直接跳过 Alpha Channel。

Framebuffer 配置（ `fbset` 输出）：

```
mode "640x480-0"
        # D: 0.000 MHz, H: 0.000 kHz, V: 0.000 Hz
        geometry 640 480 1024 480 32
        timings 0 0 0 0 0 0 0
        accel false
        rgba 8/16,8/8,8/0,0/0
endmode
```

转换脚本（参考 [[Tips] 擷取 framebuffer 畫面](https://owen-hsu.blogspot.com/2016/06/tips-framebuffer.html)）：

```perl
#!/usr/bin/perl -w
 
$w = shift || 240;
$h = shift || 320;
$pixels = $w * $h;
 
open OUT, "|pnmtopng" or die "Can't pipe pnmtopng: $!\n";
 
printf OUT "P6%d %d\n255\n", $w, $h;
 
while ((read STDIN, $raw, 4) and $pixels--) {
   $short = unpack('I', $raw);
   print OUT pack("C3",
      ($short & 0xff0000) >> 16,
      ($short & 0xff00) >> 8,
      ($short & 0xff));
}
 
close OUT;
```

用法： `cat image.rgb | perl script.pl 1024 480 > console.png`

