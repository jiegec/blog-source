---
layout: post
date: 2023-08-10
tags: [loongson,loongarch,cpu]
categories:
    - hardware
---

# LoongArch 处理器

整理市面上的 LoongArch 处理器以及相关产品。

<!-- more -->

## 3A5000

[主页](https://www.loongson.cn/product/show?id=10)

4 核 LA464

不同的版本：

- 3A5000-HV: High Voltage, 2.5GHz
- 3A5000-LL: 2.3GHz
- 3A5000M: Mobile, 2.0GHz
- 3A5000-iHV: Industrial High Voltage, 1.5/2.0GHz
- 3A5000-i: Industrial: 1.5GHz
- 3B5000: Server, 2.3GHz

| 型号                                                           | 类型            | 桥片/显卡         | 内存 | 硬盘  | 价格 |
|----------------------------------------------------------------|---------------|-------------------|------|-------|------|
| [PN-L520A](https://item.jd.com/10074790246806.html)            | 台式机          | 7A2000            | 16GB | 512GB | 2699 |
| [GPC-100](https://item.jd.com/100017987513.html)               | 台式机          | 7A1000 + 独显     | 8GB  | 256GB | 3825 |
| [M540Z](https://item.jd.com/100044255754.html)                 | 台式机          | 独显              | 8GB  | 256GB | 4599 |
| [悦睿](https://item.jd.com/100023656622.html)                  | 台式机          | 独显              | 8GB  | 256GB | 4608 |
| [EC-80G](https://item.jd.com/100029037278.html)                | 台式机          | AMD R5 230        | 8GB  | 256GB | 7266 |
| [ML5A-D01](https://www.eaecis.com/cp_94/874.html)              | 台式机          | 7A1000            | N/A  | N/A   | N/A  |
| [ML5C-D04](https://www.eaecis.com/cp_94/873.html)              | 台式机          | 7A2000            | N/A  | N/A   | N/A  |
| [TR11A2](https://item.jd.com/100043060855.html)                | 台式机 + 显示器 | 独显              | 8GB  | 256GB | 5890 |
| [TL630-V001-2](https://item.jd.com/100044512026.html)          | 台式机 + 显示器 | 独显              | 8GB  | 256GB | 6200 |
| [JL630-V001](https://item.jd.com/100047587985.html)            | 台式机 + 显示器 | 独显              | 16GB | 512GB | 6999 |
| [GDC-1401](https://item.jd.com/100016595171.html)              | 笔记本          | 7A1000+AMD R5 340 | 8GB  | 256GB | 6375 |
| [L860-T2](https://item.jd.com/100037403828.html)               | 笔记本          | 独显              | 8GB  | 256GB | 6999 |
| [L71](https://www.eaecis.com/cp_95/877.html)                   | 笔记本          | 独显              | N/A  | N/A   | N/A  |
| [L71S](https://www.eaecis.com/cp_95/875.html)                  | 笔记本          | 7A2000            | N/A  | N/A   | N/A  |
| [L71F](https://www.eaecis.com/cp_95/924.html)                  | 笔记本          | 7A1000 + 独显     | N/A  | N/A   | N/A  |
| [龙芯开发板](https://item.taobao.com/item.htm?id=682906828504) | 主板+CPU        | 7A2000            | N/A  | N/A   | 1700 |
| [智芯元](https://item.taobao.com/item.htm?id=717408690295)     | 主板+CPU        | 7A2000            | N/A  | N/A   | 1798 |
| [我爱开发板](https://item.taobao.com/item.htm?id=683776108019) | 主板+CPU        | 7A2000            | N/A  | N/A   | 1900 |
| [迅为](https://item.taobao.com/item.htm?id=690758505114)       | 主板+CPU        | 7A2000            | 8GB  | 128GB | 5910 |
| [ML5A](https://www.eaecis.com/cp_92/853.html)                  | 主板+CPU        | 7A1000            | N/A  | N/A   | N/A  |
| [ML5C](https://www.eaecis.com/cp_92/872.html)                  | 主板+CPU        | 7A2000            | N/A  | N/A   | N/A  |

## 3C5000

[主页](https://www.loongson.cn/product/show?id=15)

16 核 LA464

不同的版本：

- 3C5000: 32MB L3 Cache, 2.2GHz
- 3C5000-LL: 32MB L3 Cache, 2.0GHz
- 3C5000L: 64MB L3 Cache, 2.2GHz
- 3C5000L-LL: 64MB L3 Cache, 2.0GHz

3C5000L 是由四个 3A5000 芯片集成，而 3C5000 不是。

- <https://item.jd.com/100053674064.html> GDC-2000 两路 3C5000
- <https://item.jd.com/100054670954.html> JL620-G3-00 两路 3C5000L
- <https://item.jd.com/100054668922.html> JL620-G3-01 两路 3C5000
- <https://item.jd.com/10079447545921.html> G4129-ET25 两路 3C5000
- <https://www.eaecis.com/chanpinleixingfenlei/334.html> SL12R-S01 两路 3C5000
- <https://item.jd.com/100033473676.html> GS6000L-4C5L 四路 3C5000L
- <https://item.jd.com/100041722164.html> GDC-2000 四路 3C5000L
- <https://item.jd.com/100060558727.html> GS6000 LA240 四路 3C5000

## 3D5000

[主页](https://www.loongson.cn/product/show?id=21)

32 核 LA464

## 3A6000

4 核 8 线程 LA664

![](loongarch-cpu-3a6000.png)

来源：[龙芯中科 2023 年半年度业绩说明会](https://roadshow.sseinfo.com/roadshowIndex.do?id=14977)

根据 <http://basic.10jqka.com.cn/688047/interactive.html>:

- ROB 项数达到 256 项
- 四定点、四浮点、四访存共 12 个功能部件

开发板 <https://bbs.loongarch.org/d/309-3a6000>：

- XA612A0: 3A6000 + 7A2000
- XA61200: 3A6000 + 7A2000

主板：

- [DL37](https://item.jd.com/10092331777554.html) [官网](https://www.eaecis.com/cp_92/963.html)
- [龙芯俱乐部](https://item.taobao.com/item.htm?id=743837636202)

台式机：

- [ZKL360-TF](https://item.jd.com/10092886566388.html)：16GB+1024GB，2699 元
- [PN-L530A](https://item.jd.com/10090990632336.html) [官网](https://pnxc.cn/Products-Center/12/262.html): 16GB+512GB，2999 元
- [EC-80G](https://item.jd.com/100076186619.html): 8GB + 256GB + 独显，4699 元
- [DL37-D05](https://item.jd.com/10092330519232.html) [官网](https://www.eaecis.com/cp_94/960.html)
- [龙芯俱乐部](https://item.taobao.com/item.htm?id=746096291480)
- [F918](https://item.taobao.com/item.htm?id=747648718264) [天猫](https://detail.tmall.com/item.htm?id=745565351633)

笔记本：

- [NL38-N09](https://item.jd.com/10092331328613.html) [官网](https://www.eaecis.com/cp_95/962.html)

## 3C6000

![](3c6000.png)

来源：[龙芯中科 2023 年第三季度业绩说明会](https://roadshow.sseinfo.com/roadshowIndex.do?id=16536)

## 2K3000

![](loongarch-cpu-2k3000.png)

来源：[龙芯中科 2023 年第三季度业绩说明会](https://roadshow.sseinfo.com/roadshowIndex.do?id=16536)

## 2K2000

[2K2000](https://www.loongson.cn/product/show?id=20): 2 核 LA364

- [GM7-3002](https://www.taobao.com/list/item/744723394450.htm)
- [龙芯 2K2000 全国产化工控机](http://www.chaec.com.cn/lx2k1000aqyypt/226.html)

## 2K1500

[2K1500](https://www.loongson.cn/product/show?id=19): 2 核 LA264

## 2K1000LA

[2K1000LA](https://www.loongson.cn/product/show?id=8): 2 核 LA264

- [开发板](https://ic-item.jd.com/10075817807406.html)

## 2K0500

[2K0500](https://www.loongson.cn/product/show?id=9): 1 核 LA264

- [开发板](https://ic-item.jd.com/10087557916057.html)

## 其他

- [1C103](https://www.loongson.cn/product/show?id=18): 1 核 LA132

## 固件

- <https://github.com/loongson/Firmware>
- <https://gitee.com/loongson/Firmware>
- <https://gitea.whlug.cn/3A6000/3A6000>
