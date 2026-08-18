---
layout: post
date: 2026-08-18
tags: [cpu,loongson,loongarch]
categories:
    - hardware
---

# 谈谈龙芯的 LoongLeak 漏洞

## 背景

近日，龙芯龙架构 CPU LA464/LA664 微架构部分步进的漏洞 [LoongLeak](https://loongleakattack.com/) 正式披露，龙芯官方也发布了 [公告](https://www.loongson.cn/news/show?id=850)。作为公告中提到的“其他国内独立研究者”之一，我在此分享一下我的视角。

<!-- more -->

## 发现和披露的过程

这些年来，我在龙架构上做了不少工作，从参与 AOSC 社区的龙架构移植，到后来专注于 [LSX/LASX/LBT 指令集第三方文档](https://jia.je/unofficial-loongarch-intrinsics-guide/) 的维护，一直持续关注龙架构处理器的微架构信息，包括安全特性。我也曾尝试在龙架构上复现一些经典的攻击手段，比如 Meltdown，当然最终并未成功，这说明硬件层面已做了相应防护。最近我也在做一些微架构攻击方面的研究，比如一篇对苹果分支预测器攻击的论文被 ACM CCS 26 录用（[iEnFlow](https://craft.cs.tsinghua.edu.cn/publication/ienflow-endogenous-control-flow-attacks-via-conditional-branch-prediction-on-apple-silicon/)），所以也自然而然地研究到了龙芯上。

今年五月，我开始梳理可能适用于龙架构的经典微架构攻击方法，其中注意到了 [ZenBleed](https://lock.cmpxchg8b.com/zenbleed.html)。该漏洞揭示了 AMD 处理器上 AVX 寄存器数据泄露的问题。我几年前曾在 EPYC 处理器上复现过此漏洞，印象深刻：这类缺陷极为隐蔽，难以通过常规测试发现，触发条件苛刻（因此是通过模糊测试挖掘出来的），但确实能够泄漏物理寄存器中残留的数据。该漏洞后来通过微码更新得以修复。

回顾 ZenBleed 时，我联想到 Chips and Cheese 在 2023 年发布的分析文章 [Loongson’s LSX and LASX Vector Extensions](https://chipsandcheese.com/p/loongsons-lsx-and-lasx-vector-extensions)，其中提到执行 LSX 指令后，向量寄存器的高位部分可能出现“随机”数值。文章并未从漏洞角度深入探究，但结合 ZenBleed 的经验，我很快意识到这很可能同样源于未清空的物理寄存器数据。随后我进行了一系列实验，迅速在 LA464 和 LA664 两个微架构上复现了类似 ZenBleed 的漏洞，并将其命名为 LoongBleed。

5 月 12 日，我向龙芯公司提交了漏洞报告。他们迅速完成了复现，并将其转交给 CPU 团队。6 月 9 日，我收到通知：这是一个已知漏洞的独立发现。这意味着在我之前，已有其他研究者发现了该漏洞并报告给了龙芯，我推测这应该就是 LoongLeak 作者团队的工作。此后我按照漏洞披露的惯例继续保密，直至官方公开披露，我才将相关信息公开。此前我将其命名为 LoongBleed（因其与 ZenBleed 在原理和现象上相似），源代码已托管于 [LoongBleed](https://github.com/jiegec/LoongBleed) 仓库。LoongLeak 与 LoongBleed 本质上是同一漏洞，只是触发方式略有差异，由两个团队（我的团队即我本人）独立发现。

## 漏洞原理与修复

关于该漏洞的原理，目前存在两种推测：一是 LoongLeak 论文中提出的从 L1D 缓存行泄露数据；二是我更倾向的物理寄存器高位未清空假说。目前我尚未深入验证哪种推测成立，亦可能两者并存。但无论如何，LASX 寄存器的高位部分在执行 LSX 指令后本不应被使用，更不应泄露数据，正如 ZenBleed 那样。

至于修复方式，在微架构层面应设法固定多余的位数，例如置为全零或全一。具体实现方案取决于泄漏的根源，需补充相应逻辑。对于存在漏洞的硬件，能否修复取决于是否预留了相关的控制位（chicken bit）以屏蔽问题逻辑路径。但由于龙芯处理器不支持微码更新，无法像 AMD 那样通过发布微码来修补。

从危害程度来看，攻击者若获取本地执行权限，即可泄漏部分原本不可访问的敏感信息，不过这些数据是碎片化的，拼凑难度较大。总体而言，其危害相比 [GhostWrite](https://ghostwriteattack.com/) 那类任意内存读写的漏洞要弱得多。

## 对龙芯的观察

在这次漏洞披露流程中，龙芯的表现总体得体，尽管这可能是首个公开的龙芯微架构漏洞。此次事件之后，势必会有更多研究者将目光投向龙架构。尤其是 USENIX Security 26 上那篇 LoongLeak 论文发表后，新的研究方向已被开辟，此前各类攻击方法很可能被陆续移植到龙架构上进行测试，出现新漏洞也并非意外。

这也为龙芯提出了新的挑战：如何在微架构设计阶段，既追求性能，又充分考虑安全性，并做好冗余设计，以便在安全问题出现时拥有足够的应对手段。不过，所有处理器厂商都是这样走过来的。即便是 Intel，至今仍在持续修复各类硬件漏洞，只是像当年 Meltdown 那样可读取任意地址的严重漏洞确实越来越少了。可以说，这是处理器发展过程中必经的阶段。

最后，祝龙芯越来越好。
