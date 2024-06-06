---
layout: post
date: 2023-01-09
tags: [amd,cpu]
categories:
    - hardware
---

# AMD 处理器

## Ryzen 系列

注：下表中省略了 PRO 前缀，部分型号有带 PRO 和不带 PRO 的版本，部分型号仅有带 PRO 的版本，部分型号没有带 PRO 的版本。

### Ryzen 5000

| 代号     | 用途   | 核显 | 插槽  | 微架构 | 型号                                                                  |
|----------|------|------|-------|--------|-----------------------------------------------------------------------|
| Vermeer  | 桌面   | 无   | AM4   | Zen 3  | 5950X/5945/5900(X)/5845/5800(X(3D))/5700(X(3D))/5645/5600(X(3D))      |
| Chagall  | 工作站 | 无   | sWRX8 | Zen 3  | 5995WX/5975WX/5965WX/5955WX/5945WX                                    |
| Cezanne  | 桌面   | GCN5 | AM4   | Zen 3  | 5750G(E)/5700G(E)/5650G(E)/5600G(E)/5600GT/5500(GT)/5350G(E)/5300G(E) |
| Cezanne  | 笔记本 | GCN5 | FP6   | Zen 3  | 5980HX/5980HS/5900HX/5900HS/5800H(S)/5800U/5600H(S)/5600U/5560U/5400U |
| Barceló  | 笔记本 | GCN5 | FP6   | Zen 3  | 5825U/5825C/5625U/5625C/5425U/5425C/5125C                             |
| Lucienne | 笔记本 | GCN5 | FP6   | Zen 2  | 5700U/5500U/5300U                                                     |

注：Ryzen 5 5500 虽然代号是 Cezanne，但是去掉了核显。

<!-- more -->

Vermeer:

- [5600](https://www.amd.com/en/product/11831)
- [5600X](https://www.amd.com/en/product/10471)
- [5600X3D](https://www.amd.com/en/product/13541)
- [PRO 5645](https://www.amd.com/en/product/12186)
- [5700X](https://www.amd.com/en/product/11826)
- [5800](https://www.amd.com/en/product/10791)
- [5800X](https://www.amd.com/en/product/10466)
- [5800X3D](https://www.amd.com/en/product/11576)
- [PRO 5845](https://www.amd.com/en/product/12176)
- [5900X](https://www.amd.com/en/product/10461)
- [5900](https://www.amd.com/en/product/10796)
- [PRO 5945](https://www.amd.com/en/product/12181)
- [5950X](https://www.amd.com/en/product/10456)

Chagall:

- [PRO 5945WX](https://www.amd.com/en/product/11806)
- [PRO 5955WX](https://www.amd.com/en/product/11801)
- [PRO 5965WX](https://www.amd.com/en/product/11796)
- [PRO 5975WX](https://www.amd.com/en/product/11791)
- [PRO 5995WX](https://www.amd.com/en/product/11786)

Cezanne 桌面：

- [5300G](https://www.amd.com/en/product/11181)
- [5300GE](https://www.amd.com/en/product/11196)
- [PRO 5350G](https://www.amd.com/en/product/11246)
- [PRO 5350GE](https://www.amd.com/en/product/11251)
- [5500](https://www.amd.com/en/product/11811)
- [5600G](https://www.amd.com/en/product/11176)
- [5600GE](https://www.amd.com/en/product/11191)
- [PRO 5650G](https://www.amd.com/en/product/11241)
- [PRO 5650GE](https://www.amd.com/en/product/11236)
- [5700G](https://www.amd.com/en/product/11171)
- [5700GE](https://www.amd.com/en/product/11186)
- [PRO 5750G](https://www.amd.com/en/product/11231)
- [PRO 5750GE](https://www.amd.com/en/product/11226)

### Ryzen 6000

| 代号      | 用途   | 核显  | 插槽 | 微架构 | 型号                                                      |
|-----------|------|-------|------|--------|-----------------------------------------------------------|
| Rembrandt | 笔记本 | RDNA2 | FP7  | Zen 3+ | 6980HX/6980HS/6900HX/6900HS/6800H(S)/6800U/6600H(S)/6600U |

### Ryzen 7000

| 代号         | 用途   | 核显  | 插槽          | 微架构         | 型号                                                               |
|--------------|------|-------|---------------|----------------|--------------------------------------------------------------------|
| Storm Peak   | 工作站 | 无    | sTR5          | Zen 4          | 7995WX/7985WX/7980X/7975WX/7970X/7965WX/7060X/7955WX/7945WX        |
| Raphael      | 桌面   | RDNA2 | AM5           | Zen 4          | 7950X(3D)/7945/7900(X(3D))/7800X3D/7745/7700(X)/7645/7600(X)/7500F |
| Dragon Range | 笔记本 | RDNA2 | FL1           | Zen 4          | 7945HX(3D)/7845HX/7745HX/7645HX                                    |
| Phoenix      | 笔记本 | RDNA3 | FP7/FP7r2/FP8 | Zen 4          | 7940H(S)/7840H(S)/7840U/7640H(S)/7640U/7540U                       |
| Phoenix      | 笔记本 | RDNA3 | FP7/FP7r2     | Zen 4 + Zen4 c | 7545U/7440U                                                        |
| Rembrandt R  | 笔记本 | RDNA2 | FP7/FP7r2     | Zen 3+         | 7735H(S)/7736U/7735U/7535HS/7535U/7335U                            |
| Barcelo R    | 笔记本 | GCN5  | FP6           | Zen 3          | 7730U/7530U/7330U                                                  |
| Mendocino    | 笔记本 | RDNA2 | FT6           | Zen 2          | 7520U//7520C/7320U/7320C                                           |

AMD 笔记本处理器产品从 2023 年到 2025 年采用新的[命名方式](https://www.anandtech.com/show/18718/amd-2023-ryzen-mobile-7000-cpus-unveiled-zen-4-phoenix-takes-point)：

- 数字第一位：7 对应 2023，8 对应 2024，9 对应 2025，约等于 Intel 的代次
- 数字第二位：1 对应 Athlon Silver，2 对应 Athlon Gold，3-4 对应 Ryzen 3，5-6 对应 Ryzen 5，7-8 对应 Ryzen 7，8-9 对应 Ryzen 9，类似 Intel 的 i3/i5/i7/i9
- 数字第三位：1 对应 Zen/Zen+，2 对应 Zen 2，依次类推
- 数字第四位：0 表示低端，5 表示高端
- 后缀：性能从高到低 HX，HS，U/C

因此代号和编号有直接的对应关系：

- Dragon Range: 7045, Extreme Gaming and Creator
- Phoenix: 7040, Elite Ultrathin
- Rembrandt R: 7035, Premium Thin & Light
- Bracelo R: 7030, Mainstream Thin & Light
- Mendocino: 7020, Everyday Computing

### Ryzen 8000

| 代号       | 用途   | 核显  | 插槽          | 微架构 | 型号                                                       |
|------------|------|-------|---------------|--------|------------------------------------------------------------|
| Hawk Point | 笔记本 | RDNA3 | FP7/FP7r2/FP8 | Zen 4  | 8945HS/8845HS/8840HS/8840U/8645HS/8640HS/8640U/8540U/8440U |
| Phoenix    | 桌面   | RDNA3 | AM5           | Zen 4  | 8700G/8600G/8500G/8300G                                    |
| Phoenix    | 桌面   | 无    | AM5           | Zen 4  | 8700F/8400F                                                      |

### Ryzen 9000

| 代号          | 用途 | 核显  | 插槽 | 微架构 | 型号                    |
|---------------|----|-------|------|--------|-------------------------|
| Granite Ridge | 桌面 | RDNA2 | AM5  | Zen 5  | 9950X/9900X/9700X/9600X |

### AI

| 代号        | 用途        | 核显    | 插槽 | 微架构 | 型号      |
|-------------|-----------|---------|------|--------|-----------|
| Strix Point | 笔记本，桌面 | RDNA3.5 | FP8  | Zen 5  | HX370/365 |

### Z1

Ryzen Z1 系列：

- [Ryzen Z1](https://www.amd.com/en/product/13226)
- [Ryzen Z1 Extreme](https://www.amd.com/en/product/13221)

### 核显

- AMD Radeon™ 890M: RDNA 3.5
- AMD Radeon™ 740M/760M/780M: RDNA 3
- AMD Radeon™ 610M/660M/680M: RDNA 2

### 参考资料

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
- Storm Peak: [AMD Launches The Ryzen Threadripper 7000 Series: Up To 96 Cores, DDR5 RDIMMs, PRO & HEDT CPUs](https://www.phoronix.com/review/amd-ryzen-threadripper-7000)
- Storm Peak: [AMD Introduces New AMD Ryzen Threadripper 7000 Series Processors and Ryzen Threadripper PRO 7000 WX-Series Processors for the Ultimate Workstation](https://www.amd.com/en/newsroom/press-releases/2023-10-19-amd-introduces-new-amd-ryzen-threadripper-7000-ser.html)
- Hawk Point: [AMD Extends Mobile PC Leadership with AMD Ryzen™ 8040 Series Processors and Makes Ryzen™ AI Software Widely Available, Advancing the AI PC Era](https://ir.amd.com/news-events/press-releases/detail/1172/amd-extends-mobile-pc-leadership-with-amd-ryzen-8040)
- Hawk Point: [AMD Expands Commercial AI PC Portfolio to Deliver Leadership Performance Across Professional Mobile and Desktop Systems](https://ir.amd.com/news-events/press-releases/detail/1190/amd-expands-commercial-ai-pc-portfolio-to-deliver)
- Phoenix: [AMD Reveals Next-Gen Desktop Processors for Extreme PC Gaming and Creator Performance](https://www.amd.com/en/newsroom/press-releases/2024-1-8-amd-reveals-next-gen-desktop-processors-for-extrem.html)
- Granite Ridge: [AMD Unveils Ryzen 9000 CPUs For Desktop, Zen 5 Takes Center Stage at Computex 2024](https://www.anandtech.com/show/21415/amd-unveils-ryzen-9000-cpus-for-desktop-zen-5-takes-center-stage-at-computex-2024)


## EPYC 系列

| 代号    | 编号 | 最大核心数 | 微架构 | 插槽 |
|---------|------|------------|--------|------|
| Naples  | 7001 | 32         | Zen 1  | SP3  |
| Rome    | 7002 | 64         | Zen 2  | SP3  |
| Milan   | 7003 | 64         | Zen 3  | SP3  |
| Milan-X | 7003 | 64         | Zen 3  | SP3  |
| Genoa   | 9004 | 96         | Zen 4  | SP5  |
| Genoa-X | 9004 | 96         | Zen 4  | SP5  |
| Bergamo | 97X4 | 128        | Zen 4c | SP5  |

### 参考资料

- [AMD Gives Details on EPYC Zen4: Genoa and Bergamo, up to 96 and 128 Cores](https://www.anandtech.com/show/17055/amd-gives-details-on-epyc-zen4-genoa-and-bergamo-up-to-96-and-128-cores)

## Family, Model, Stepping

AMD 的 CPUID 分为三部分：Family，Model 和 Stepping，例如：

- AMD EPYC 7001 Naples: Family=23(0x17), Model=1(0x01), Stepping=2(0x02)
- AMD EPYC 7002 Rome: Family=23(0x17), Model=49(0x31), Stepping=0(0x00)
- AMD Ryzen 7020U Mendocino: Family=23(0x17), Model=160(0xa0), Stepping=0(0x00)

可以在 [amd-ucode](https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/tree/amd-ucode/README) 查阅最新 microcode 版本。

修复 EPYC 7002 Rome 的 [Zenbleed](https://github.com/google/security-research/security/advisories/GHSA-v6wh-rxpg-cmm8) 漏洞的 microcode 版本是 [0x0830107a](https://lore.kernel.org/linux-firmware/20230719191757.3210370-1-john.allen@amd.com/)。