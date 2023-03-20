---
layout: post
date: 2023-03-19 12:26:00 +0800
tags: [modulation,digital]
category: system
title: 数字调制
---

## 背景

最近在学习 802.11，需要学习很多数字调制相关的知识，因此自学了一下通信原理。

## ASK

Amplitude-Shift Keying 调整载波信号的幅度

![](/images/ask.png)

## FSK

Frequency-Shift Keying 调整载波信号的频率

![](/images/bfsk.png)

## PSK

Phase-Shift Keying 调整载波信号的相位

![](/images/bpsk.png)

DPSK(Differential Phase-Shift Keying) 是在 PSK 的基础上，把相位的绝对值变成相位的差。例如 BPSK 传输 0 对应 0 度相位，传输 1 对应 180 度相位，那么 DBPSK 传输 0 时保持相位和上一个 symbol 一样，传输 1 时相位相对上一个 symbol 增加 180 度。

## QAM

Quadrature Amplitude Modulation 两个正交载波信号之和，调整两个信号的相位和幅度

### 4-QAM

4-QAM 也等价于 4-PSK（Phase-Shift Keying），相当于调整一个载波信号的相位。

![](/images/4qam.png)

### 16-QAM

![](/images/16qam.png)