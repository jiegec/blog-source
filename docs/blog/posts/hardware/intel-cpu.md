---
layout: post
date: 2023-01-11
tags: [intel,cpu]
categories:
    - hardware
---

# Intel 处理器

## Xeon 系列

[命名方式](https://www.intel.com/content/www/us/en/support/articles/000059657/processors/intel-xeon-processors.html)：

- 第一位数字：8-9 对应 Platinum，5-6 对应 Gold，4 对应 Silver，3 对应 Bronze
- 第二位数字：对应代次，1 对应 1st Generation，2 对应 2nd Generation，依此类推
- 第三位第四位数字：一般越大性能越好
- 后缀：H/L/M/N/P/Q/S/T/U/V/Y/Y+/+
  - L：大内存
  - M：媒体/大内存
  - N：网络
  - P：虚拟化，IaaS
  - Q：水冷
  - S：存储/搜索
  - T：长寿命
  - U：单插槽
  - V：虚拟化，SaaS
  - Y：Speed Select

<!-- more -->

### Intel® Xeon® 6

- [CPU 型号列表](https://www.intel.com/content/www/us/en/ark/products/series/240357/intel-xeon-6.html)
- 发布时间：Q1'25, Q2'24
- 代号：Granite Rapids/Sierra Forest
- 微架构：Redwood Cove/Crestmont
- 用途：Server
- 旗舰：Xeon 6980P(128C256T，Redwood Cove, 504 MB L3), Xeon 6780E(144C144T, Crestmont, 108 MB L3)

### 5th Generation Intel® Xeon® Scalable Processors

- [CPU 型号列表](https://www.intel.com/content/www/us/en/ark/products/series/236644/5th-gen-intel-xeon-scalable-processors.html)
- 发布时间：Q4'23
- 代号：Emerald Rapids
- 微架构：Raptor Cove
- 用途：Server
- 旗舰：Xeon Platinum 8593Q(64C128T，320 MB L3)

### 4th Generation Intel® Xeon® Scalable Processors/Xeon CPU Max Series

- [CPU 型号列表](https://ark.intel.com/content/www/us/en/ark/products/series/228622/4th-generation-intel-xeon-scalable-processors.html) [Xeon CPU Max 型号列表](https://ark.intel.com/content/www/us/en/ark/products/series/232643/intel-xeon-cpu-max-series.html)
- 发布时间：Q1'23
- 代号：Sapphire Rapids/Sapphire Rapids HBM
- 微架构：Golden Cove
- 用途：Server
- 旗舰：Xeon CPU Max 9480(56C112T，112.5 MB L3，HBM)/Xeon Platinum 8490H(60C120T，112.5 MB L3)/Xeon Platinum 8480+(56C112T，105 MB L3)

### 3rd Generation Intel® Xeon® Scalable Processors

- [CPU 型号列表](https://ark.intel.com/content/www/us/en/ark/products/series/204098/3rd-generation-intel-xeon-scalable-processors.html)
- 发布时间：Q2'21(Ice Lake), Q2'20(Cooper Lake)
- 代号：Cooper Lake/Ice Lake
- 微架构：Sunny Cove
- 用途：Server
- 旗舰：Xeon Platinum 8380(40C80T，Sunny Cove，60 MB L3)
- 相关阅读：[Ice Lake](https://www.anandtech.com/show/16594/intel-3rd-gen-xeon-scalable-review)

### 2nd Generation Intel® Xeon® Scalable Processors

- [CPU 型号列表](https://ark.intel.com/content/www/us/en/ark/products/series/192283/2nd-generation-intel-xeon-scalable-processors.html)
- 发布时间：Q1'20, Q2'19
- 代号：Cascade Lake
- 用途：Server
- 旗舰：Xeon Platinum 9282(56C112T)，Xeon Platinum 8280(28C56T，38.5 MB L3)
- 相关阅读：[Cascade Lake](https://www.anandtech.com/show/14146/intel-xeon-scalable-cascade-lake-deep-dive-now-with-optane)

### 1st Generation Intel® Xeon® Scalable Processors

- [CPU 型号列表](https://ark.intel.com/content/www/us/en/ark/products/series/125191/intel-xeon-scalable-processors.html)
- 发布时间：Q2'18, Q3'17
- 代号：Skylake
- 用途：Server
- 旗舰：Xeon Platinum 8180(28C56T)

## Core 系列

[命名方式](https://www.intel.com/content/www/us/en/processors/processor-numbers.html)

- i3/i5/i7/i9：数字越大越高端
- 万位 + 千位：对应代次，13 对应 13 代
- 百位 + 十位 + 千位：型号，一般越大越高端
- 后缀：F/H/HK/HX/K/P/U/X/XE/Y
  - F：桌面，无核显
  - H：笔记本，高性能
  - HK：笔记本，高性能，可超频
  - HX：笔记本，高高性能，可超频
  - K：桌面，高性能，可超频
  - P：笔记本，轻薄本
  - S：桌面，特别版
  - U：笔记本，节能
  - X/XE：桌面，高高性能，可超频
  - Y：特别节能

### Intel® Core™ Ultra Processors (Series 2)

- [CPU 型号列表](https://www.intel.com/content/www/us/en/ark/products/series/241071/intel-core-ultra-processors-series-2.html)
- 发布时间：Q1'25
- 代号：Arrow Lake，大小核
- 用途：移动/桌面

### Intel® Core™ processors (Series 2)

- [CPU 型号列表](https://www.intel.com/content/www/us/en/ark/products/series/238783/intel-core-processors-series-2.html)
- 发布时间：Q1'25
- 代号：Raptor Lake，大小核
- 用途：嵌入式/移动

### Intel® Core™ Ultra Processors (Series 1)

- [CPU 型号列表](https://www.intel.com/content/www/us/en/ark/products/series/236803/intel-core-ultra-processors-series-1.html)
- 发布时间：Q2'24
- 代号：Meteor Lake，大小核
- 用途：嵌入式/移动

### Intel® Core™ processors (Series 1)

- [CPU 型号列表](https://www.intel.com/content/www/us/en/ark/products/series/236798/intel-core-processors-series-1.html)
- 发布时间：Q2'24
- 代号：Raptor Lake，大小核
- 用途：嵌入式

### 14th Generation Intel® Core™ Processors

- [i9 CPU 型号列表](https://www.intel.com/content/www/us/en/ark/products/series/236143/intel-core-i9-processors-14th-gen.html) [i7 CPU 型号列表](https://www.intel.com/content/www/us/en/ark/products/series/236170/intel-core-i7-processors-14th-gen.html) [i5 CPU 型号列表](https://www.intel.com/content/www/us/en/ark/products/series/236175/intel-core-i5-processors-14th-gen.html) [i3 CPU 型号列表](https://www.intel.com/content/www/us/en/ark/products/series/236176/intel-core-i3-processors-14th-gen.html)
- 发布时间：Q1'24
- 代号：Raptor Lake，大小核
- 用途：桌面，笔记本
- 旗舰：i9-14900K（8+16C32T）

### 13th Generation Intel® Core™ Processors

- [i9 CPU 型号列表](https://ark.intel.com/content/www/us/en/ark/products/series/230485/13th-generation-intel-core-i9-processors.html) [i7 CPU 型号列表](https://ark.intel.com/content/www/us/en/ark/products/series/230486/13th-generation-intel-core-i7-processors.html) [i5 CPU 型号列表](https://ark.intel.com/content/www/us/en/ark/products/series/230487/13th-generation-intel-core-i5-processors.html) [i3 CPU 型号列表](https://ark.intel.com/content/www/us/en/ark/products/series/230488/13th-generation-intel-core-i3-processors.html)
- 发布时间：Q1'23，Q4'22
- 代号：Raptor Lake，大小核
- 用途：桌面，笔记本
- 旗舰：i9-13900K（8+16C32T）/i9-13900KF
- 相关阅读：[Intel Core i9-13900K and i5-13600K Review: Raptor Lake Brings More Bite](https://www.anandtech.com/show/17601/intel-core-i9-13900k-and-i5-13600k-review)

### 12th Generation Intel® Core™ Processors

- [i9 CPU 型号列表](https://ark.intel.com/content/www/us/en/ark/products/series/217839/12th-generation-intel-core-i9-processors.html)
- 发布时间：Q1'22，Q4'21
- 代号：Alder Lake，大小核
- 旗舰：i9-12900KS（8+8C24T）
- 相关阅读：[The Intel Core i9-12900KS Review: The Best of Intel's Alder Lake, and the Hottest](https://www.anandtech.com/show/17479/the-intel-core-i9-12900ks-review-the-best-of-intel-s-alder-lake-and-the-hottest)

### 11th Generation Intel® Core™ Processors

- [i9 CPU 型号列表](https://ark.intel.com/content/www/us/en/ark/products/series/202984/11th-generation-intel-core-i9-processors.html)
- 发布时间：Q2'21，Q1'21
- 代号：Rocket Lake
- 旗舰：i9-11900K（8C16T）

### 10th Generation Intel® Core™ Processors

- [i9 CPU 型号列表](https://ark.intel.com/content/www/us/en/ark/products/series/195735/10th-generation-intel-core-i9-processors.html) [Intel® Core™ X-series Processors](https://ark.intel.com/content/www/us/en/ark/products/series/123588/intel-core-x-series-processors.html)
- 发布时间：Q3'20，Q2'20，Q4'19
- 代号：Comet Lake
- 旗舰：i9-10900K（10C20T，Comet Lake）；特别地，在 X-series 系列中还有 i9-10980XE（18C36T，Cascade Lake）