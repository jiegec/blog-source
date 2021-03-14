---
layout: post
date: 2021-03-13 23:11:00 +0800
tags: [gnome,scaling,x11,wayland,xwayland]
category: software
title: Gnome 的 Fractional Scaling
---

## 背景

最近发现部分软件（包括Google Chrome，Firefox 和 Visual Studio Code） 在 125% 的 Fractional Scaling 模式下会很卡。找到了一些临时解决方法，但是很不优雅，也很麻烦。所以深入研究了一下 Fractional Scaling 的工作方式。

## 临时解决方法

根据关键字，找到了 [Chrome menus too slow after enabling fractional scaling in Ubuntu 20.04](https://askubuntu.com/questions/1274719/chrome-menus-too-slow-after-enabling-fractional-scaling-in-ubuntu-20-04)。按它的方法，关闭 Google Chrome 的硬件加速，发现卡顿问题确实解决了。

类似地，也可以[关闭 VSCode 的硬件加速](Chrome menus too slow after enabling fractional scaling in Ubuntu 20.04)，在 Firefox 里也可以找到相应的设置。这样操作确实可以解决问题。但是，对于每一个出问题的应用都这样搞一遍，还是挺麻烦的。

另一个思路是，[不使用 Fractional Scaling，而只是把字体变大](https://askubuntu.com/questions/1230208/fractional-scaling-does-not-work-properly-ubuntu-20-04/1272794#1272794)。但毕竟和我们想要的效果不大一样。

## 一些发现

在物理机进行了一些实验以后，发现一个现象：125% 的时候卡顿，而其他比例（100%，150%，175%，200%）都不卡顿。

网上一顿搜到，找到了 xrandr 工具。下面是观察到的一些现象（GNOME 设置分辨率一直是 1920x1080）：

| 放缩比例 | xrandr 显示的分辨率 | xrandr 显示的 transform |
| -------- | ------------------- | ----------------------- |
| 100%     | 1920x1080           | diag(1.0, 1.0, 1.0)     |
| 125%     | 3072x1728           | diag(1.6, 1.6, 1.0)     |
| 150%     | 2560x1440           | diag(1.33, 1.33, 1.0)   |
| 175%     | 2208x1242           | diag(1.15, 1.15, 1.0)   |
| 200%     | 1920x1080           | diag(1.0, 1.0, 1.0)     |

在 [xrandr 文档](https://www.x.org/releases/X11R7.5/doc/man/man1/xrandr.1.html) 中，写了：transform 是一个 3x3 矩阵，矩阵乘以输出的点的坐标得到图形缓存里面的坐标。

由此可以猜想：fractional scaling 的工作方式是，把绘制的 buffer 调大，然后再用 transform 把最终输出分辨率调成 1920x1080 。可以看到，xrandr 显示的分辨率除以 transform 对应的值，就是 1920x1080。但这并不能解释 100% 和 200% 的区别，所以肯定还漏了什么信息。

翻了翻 [mutter 实现 fractional scaling 的 pr](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/3/diffs#989734a4aea877b0c1d80fa73cbe2ee59de79fba_376_422)，找到了实现 scale 的一部分：

```cpp
if (clutter_actor_get_resource_scale (priv->actor, &resource_scale) &&
    resource_scale != 1.0f)
  {
    float paint_scale = 1.0f / resource_scale;
    cogl_matrix_scale (&modelview, paint_scale, paint_scale, 1);
  }
```

然后找到了一段对 scale 做 ceiling 的[代码](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/3/diffs#989734a4aea877b0c1d80fa73cbe2ee59de79fba_238_265)：

```cpp
if (_clutter_actor_get_real_resource_scale (priv->actor, &resource_scale))
  {
    ceiled_resource_scale = ceilf (resource_scale);
    stage_width *= ceiled_resource_scale;
    stage_height *= ceiled_resource_scale;
  }
```

这样，100% 和其他比例就区分开了。

另外，也在[代码](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/3/diffs#d66a28cda989fbb17c8a7302b3f6360640c3c152_33_33) 中发现：

```cpp
#define SCALE_FACTORS_PER_INTEGER 4
#define SCALE_FACTORS_STEPS (1.0 / (float) SCALE_FACTORS_PER_INTEGER)
#define MINIMUM_SCALE_FACTOR 1.0f
#define MAXIMUM_SCALE_FACTOR 4.0f
```

这段代码规定了比例只能是 25% 的倍数。

我也试了一下用 xrandr --scale 1.5x1.5：效果就是窗口看起来都更小了，分辨率变成了 2880x1620，transform 是 diag(1.5, 1.5, 1.0)。

## 虚拟机测试

接着，用虚拟机做了一些测试。为了在 GNOME over Wayland 上使用 fractional scaling，需要运行：

```shell
$ gsettings set org.gnome.mutter experimental-features "['scale-monitor-framebuffer']"
```

接着又做了类似上面的测试（GNOME 设置分辨率一直是 2560x1600）：

| 放缩比例 | xrandr 显示的分辨率 |
| -------- | ------------------- |
| 100%     | 2560x1600           |
| 125%     | 2048x1280           |
| 150%     | 1704x1065           |
| 175%     | 1464x915            |
| 200%     | 1280x800            |

在这个测试中，xrandr 显示的 transform 一直都是单位矩阵；还用了来自 [xyproto/wallutils](https://github.com/xyproto/wallutils) 的 `wayinfo` 命令查看输出的分辨率，一直是 2560x1600，DPI 一直是 96。用 wallutils 的 xinfo 看到的结果和 xrandr 一致（通过 XWayland）。但是和物理机有一点不同：物理机有一个选项问要不要打开 fractional scaling，下面还会提示性能下降的问题；但是虚拟机上并没有这个提示，而是直接给了一些 Scale 比例的选项。

尝试了一下，在 GNOME over X11 上是找不到 fractional scaling 的（没有出现设置 scale 的选项）。找到一个实现这个功能的 fork：https://github.com/puxplaying/mutter-x11-scaling，不过没有尝试过。

我也尝试在虚拟机中用 xrandr --scale，结果就是输出黑屏，需要重启 gdm 来恢复到登录界面。
