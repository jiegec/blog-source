---
layout: post
date: 2023-01-09 19:37:00 +0800
tags: [amd,cpu]
category: hardware
title: AMD 处理器
---

# Ryzen 系列

## Ryzen 5000

| 代号       | 用途  | 核显   | 插槽    | 微架构   | 型号                                                                    |
| -------- | --- | ---- | ----- | ----- | --------------------------------------------------------------------- |
| Vermeer  | 桌面  | 无    | AM4   | Zen 3 | 5950X/5900(X)/5800(X(3D))/5700X/5600(X)                               |
| Chagall  | 工作站 | 无    | sWRX8 | Zen 3 | 5995WX/5975WX/5965WX/5955WX/5945WX                                    |
| Cezanne  | 桌面  | GCN5 | AM4   | Zen 3 | 5700G(E)/5600G(E)/5300G(E)                                            |
| Cezanne  | 笔记本 | GCN5 | FP6   | Zen 3 | 5980HX/5980HS/5900HX/5900HS/5800H(S)/5800U/5600H(S)/5600U/5560U/5400U |
| Barceló  | 笔记本 | 有    | FP6   | Zen 3 | 5825U/5825C/5625U/5625C/5425U/5425C/5125C                             |
| Lucienne | 笔记本 | GCN5 | FP6   | Zen 2 | 5700U/5500U/5300U                                                     |

## Ryzen 6000

| 代号        | 用途  | 核显    | 插槽  | 微架构    | 型号                                                        |
| --------- | --- | ----- | --- | ------ | --------------------------------------------------------- |
| Rembrandt | 笔记本 | RDNA2 | FP7 | Zen 3+ | 6980HX/6980HS/6900HX/6900HS/6800H(S)/6800U/6600H(S)/6600U |

## Ryzen 7000

| 代号           | 用途  | 核显    | 插槽            | 微架构    | 型号                                            |
| ------------ | --- | ----- | ------------- | ------ | --------------------------------------------- |
| Raphael      | 桌面  | RDNA2 | AM5           | Zen 4  | 7950X(3D)/7900(X(3D))/7800X3D/7700(X)/7600(X) |
| Dragon Range | 笔记本 | 有     | FL1           | Zen 4  | 7945HX/7845HX/7745HX/7645HX                   |
| Phoenix      | 笔记本 | RDNA3 | FP7/FP7r2/FP8 | Zen 4  | 7940HS/7840HS/7640HS                          |
| Rembrandt R  | 笔记本 | RDNA2 | FP7           | Zen 3+ | 7735HS/7535HS/7736U/7735U/7535U/7335U         |
| Barcelo R    | 笔记本 | 有     | FP6           | Zen 3  | 7730U/7530U/7330U                             |
| Mendocino    | 笔记本 | RDNA2 | ？             | Zen 2  | 7520U/7320U                                   |

AMD 笔记本处理器产品从 2023 年到 2025 年采用新的[命名方式](https://www.anandtech.com/show/18718/amd-2023-ryzen-mobile-7000-cpus-unveiled-zen-4-phoenix-takes-point)：

- 数字第一位：7 对应 2023，8 对应 2024，9 对应 2025，约等于 Intel 的代次

- 数字第二位：1 对应 Athlon Silver，2 对应 Athlon Gold，3-4 对应 Ryzen 3，5-6 对应 Ryzen 5，7-8 对应 Ryzen 7，8-9 对应 Ryzen 9，类似 Intel 的 i3/i5/i7/i9

- 数字第三位：1 对应 Zen/Zen+，2 对应 Zen 2，依次类推

- 数字第四位：0 表示低端，5 表示高端

- 后缀：性能从高到低 HX，HS，U/C

# 参考资料

- [List of AMD Ryzen processors](https://en.wikipedia.org/wiki/List_of_AMD_Ryzen_processors)
- Vermeer: [AMD Zen 3 Ryzen Deep Dive Review: 5950X, 5900X, 5800X and 5600X Tested](https://www.anandtech.com/show/16214/amd-zen-3-ryzen-deep-dive-review-5950x-5900x-5800x-and-5700x-tested)
- Chagall: [AMD Announces Ryzen Threadripper Pro 5000 WX-Series: Zen 3 For OEM Workstations](https://www.anandtech.com/show/17296/amd-announces-ryzen-threadripper-pro-5000-wx-series-zen-3-core-for-oem-workstations)
- Cezanne: [AMD Launches Ryzen 5000 Mobile: Zen 3 and Cezanne for Notebooks](https://www.anandtech.com/show/16405/amd-launches-ryzen-5000-mobile-zen-3-and-cezanne-for-notebooks)
- Cezanne: [AMD Ryzen 9 5980HS Cezanne Review: Ryzen 5000 Mobile Tested](https://www.anandtech.com/show/16446/amd-ryzen-9-5980hs-cezanne-review-ryzen-5000-mobile-tested)
- Cezanne: [The AMD Ryzen 7 5700G, Ryzen 5 5600G, and Ryzen 3 5300G Review](https://www.anandtech.com/show/16824/amd-ryzen-7-5700g-and-ryzen-5-5600g-apu-review)
- Barcelo: [AMD’s Barcelo: Zen 3 APU Refresh for 2022](https://www.anandtech.com/show/17190/amds-barcelo-zen-3-apu-refresh-for-2022)
- Barcelo: [AMD Announces Ryzen 5000 C-Series For High-End Chromebooks](https://www.anandtech.com/show/17373/amd-announces-ryzen-5000-cseries-for-highend-chromebooks)
- Lucienne: [AMD's Ryzen 5000 Lucienne: Not Simply Rebranded Ryzen 4000 Renoir](https://www.anandtech.com/show/16451/amds-ryzen-5000-lucienne-not-simply-rebranded-ryzen-4000-renoir-)
- Rembrandt: [AMD's Ryzen 9 6900HS Rembrandt Benchmarked: Zen3+ Power and Performance Scaling](https://www.anandtech.com/show/17276/amd-ryzen-9-6900hs-rembrandt-benchmark-zen3-plus-scaling)
- Raphael: [AMD Zen 4 Ryzen 9 7950X and Ryzen 5 7600X Review: Retaking The High-End](https://www.anandtech.com/show/17585/amd-zen-4-ryzen-9-7950x-and-ryzen-5-7600x-review-retaking-the-high-end)
- Mendocino: [AMD Launches Mendocino APUs: Zen 2-based Ryzen and Athlon 7020 Series with RDNA 2 Graphics](https://www.anandtech.com/show/17584/amd-launches-mendocino-apus-zen-2-ryzen-and-athlon-7020-series-with-rdna-2-graphics)
- Barcelo R: [Barcelo-R Ryzen 5 7530U brings Zen 3 into the mix for the messy AMD Ryzen 7000 mobile APU lineup](https://www.notebookcheck.net/Barcelo-R-Ryzen-5-7530U-brings-Zen-3-into-the-mix-for-the-messy-AMD-Ryzen-7000-mobile-APU-lineup.662046.0.html)
- Dragon Range: [AMD Announces Ryzen Mobile 7045 HX-Series CPUs, Up to 16-Cores and 5.4 GHz for Laptops](https://www.anandtech.com/show/18716/amd-announces-ryzen-7045-hx-series-cpus-for-laptops-up-to-16-cores-and-5-4-ghz)
- Phoenix/Rembrandt R: [AMD Lays Out 2023 Ryzen Mobile 7000 CPUs: Top-to-Bottom Updates, New Zen 4 'Phoenix' CPU Takes Point](https://www.anandtech.com/show/18718/amd-2023-ryzen-mobile-7000-cpus-unveiled-zen-4-phoenix-takes-point)
- 
