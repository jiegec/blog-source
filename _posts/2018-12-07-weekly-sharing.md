---
layout: post
date: 2018-12-07 15:57:00 +0800
tags: [weeklysharing]
category: misc
title: 每周分享第 1 期
---

向阮一峰学习，把自己在一周里看到的有趣的事情分享一下。不过形式就比较随意了。

1. 最近写 MongoDB + NodeJS 学到的新操作：$addToSet $nin $ne Mongoose 的 setDefaultsOnInsert
2. Promise 真香，真好用
3. 几天前惠老师还在说 "IE, The best Chrome Downloader Downloader, ever" 今天 EdgeHTML 就宣告死亡了
4. WPF, Windows Forms 和 WinUI 开源了，mono 这是要凉？ [链接](https://blogs.windows.com/buildingapps/2018/12/04/announcing-open-source-of-wpf-windows-forms-and-winui-at-microsoft-connect-2018/)
5. 有人逆向了 FGPA 的 bitstream 格式，希望 FPGA 有朝一日可以进入 开源时代？ [链接](https://github.com/mmicko/prjtang)
6. 造机的 baseline 就决定是 [它](https://github.com/Icenowy/ice-risc) 了
7. 根据 AST 炼丹判相似度还行，好奇它跨语言的预测水准 [链接](https://code2vec.org/)
8. 可视化 h264 nalu 的软件 [H264Naked](https://github.com/shi-yan/H264Naked) （做的好糙啊，想交 pr）
9. ffprobe -show_packets 和 ffprobe -show_frame 真好用
10. 发现一个解决 ArchLinux 滚内核后无法 modprobe 的[方案](https://github.com/saber-nyan/kernel-modules-hook)
11. 010 Editor 和 Hex Fiend 是二进制分析的神器啊... Kaitai 还有待加油
12. [CSS-in-JS for ClojureScript](https://github.com/roman01la/cljss) 真香 有空可以试试用 ClojureScript 写前端
13. Safari Technology Preview 71 加入了 Web Authentication 这是要支持 U2F 的节奏？
14. Grafana+InfluxDB+Telegraf 真科学，随手写了一些简单的 Telegraf 的 input plugin
15. 给 010 Editor 写了俩 .bt 文件，见我上一篇博客
16. 海思 cc 居然支持 ASan : /opt/hisi-linux/x86-arm/arm-hisiv600-linux/arm-hisiv600-linux-gnueabi/lib/a7/libasan.so
17. 遇到了 [设备名有空格导致 telegraf 读取 S.M.A.R.T. 信息失败](https://github.com/influxdata/telegraf/issues/4881) 的锅，不过似乎没人修
18. 看到了一个很有意思的 Interview Pass Rate 关于使用的编辑器的调查，很有意思 [链接](https://triplebyte.com/blog/editor-report-the-rise-of-visual-studio-code)
19. 发现一个 JSX 的替代品，用了 Template literal syntax ，挺好的 [链接](https://github.com/developit/htm)

也不知道能不能坚持下来，就这样了，发布（逃