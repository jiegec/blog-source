---
layout: post
date: 2024-12-10
tags: [linux,perf,pmu,arm,aarch64]
draft: true
categories:
    - software
---

# Linux 的性能分析（Perf）实现探究

## 背景

最近使用 Linux 的性能分析功能比较多，但是很少去探究背后的原理，例如硬件的 PMU 是怎么配置的，每个进程乃至每个线程级别的 PMU 是怎么采样的。这篇博客尝试探究这背后的原理。

<!-- more -->

## 硬件

支撑性能分析的背后是硬件自己的性能计数器，硬件会提供一些可以配置的性能计数器，在对应的硬件事件触发是，更新这些计数器，然后再由程序读取计数器的值并统计。下面以 ARMv8 为例，分析一下硬件提供的性能计数的接口：

1. Cycle 计数器：Cycle Counter Register(PMCCNTR_EL0) 和 Cycle Count Filter Register(PMCCFILTR_EL0)，其中后者控制前者在什么特权态下会进行计数
2. 最多 31 个通用性能计数器：
    1. 该性能计数器记录的硬件事件以及计数的条件：PMEVTYPER<n>_EL0，n 取 0 到 31
    2. 该性能计数器当前的值：PMEVCNTR<n>_EL0，n 取 0 到 31
3. 控制 Cycle 计数器和通用性能计数器的状态：PMCNTENCLR_EL0/PMCNTENSET_EL0/PMCR_EL0
4. 各计数器是否溢出：PMOVSCLR_EL0/PMOVSSET_EL0
5. 当计数器溢出时，PMU 会拉起中断，针对这些中断的配置：PMINTENCLR_EL1/PMINTENSET_EL1

注：实际上，由于经常会对指令数进行采样，ARM v9.4/8.9 允许硬件实现一个额外的指令计数器，和 Cycle 计数器类似。

如果想要在用户态频繁地读取性能计数器（cap_user_rdpmc），避免频繁进入内核的开销，也可以在用户态中直接读取性能计数器 PMCCNTR_EL0/PMEVCNTR<n>_EL0：内核在 PMUSERENR_EL0 中进行相应的权限配置即可。v3.9 或更高版本的 PMU 实现允许按照每个 counter 的粒度来控制用户态是否允许访问（PMUACR）。

LoongArch 也是类似的，其接口更简单：它只有通用性能计数器，有如下的 csr 来配置各个性能计数器：

1. 性能计数器的值：perfcntr<n>
2. 性能计数器的配置：perfctrl<n>，有如下字段：
    1. EVENT: 事件编号
    2. PLV{0,1,2,3}: 特权态过滤，对应四个特权态下是否采样
    3. IE：是否启用溢出中断
3. misc.rpcntl3：允许用户态程序读取性能计数器

## 内核驱动

在 Linux 内核中，负责控制 ARMv8 性能计数接口的代码在 [arm_pmuv3.c](https://github.com/torvalds/linux/blob/master/drivers/perf/arm_pmuv3.c) 当中。根据这个硬件接口，可以预想到，如果要对一段程序观察它在某个计数器上的取值，需要：

1. 分配一个性能计数器，可能是 Cycle 计数器或者通用性能计数器：对应 [armv8pmu_get_event_idx](https://github.com/torvalds/linux/blob/7cb1b466315004af98f6ba6c2546bb713ca3c237/drivers/perf/arm_pmuv3.c#L938) 函数，先分配 Cycle 计数器，再从剩下的通用性能计数器中找到一个空闲的
2. 配置并启用该性能计数器，对应 [armv8pmu_enable_event](https://github.com/torvalds/linux/blob/7cb1b466315004af98f6ba6c2546bb713ca3c237/drivers/perf/arm_pmuv3.c#L796) 函数：
    1. 把事件类型写入到 PMEVTYPER<n>_EL0 中，对应 [armv8pmu_write_event_type](https://github.com/torvalds/linux/blob/7cb1b466315004af98f6ba6c2546bb713ca3c237/drivers/perf/arm_pmuv3.c#L629) 函数
    2. 启用事件对应的溢出中断，写入 PMINTENSET_EL1，对应 [armv8pmu_enable_event_irq](https://github.com/torvalds/linux/blob/7cb1b466315004af98f6ba6c2546bb713ca3c237/drivers/perf/arm_pmuv3.c#L714) 函数
    3. 事件开始计数，写入 PMCNTENSET_EL0，对应 [armv8pmu_enable_event_counter](https://github.com/torvalds/linux/blob/7cb1b466315004af98f6ba6c2546bb713ca3c237/drivers/perf/arm_pmuv3.c#L675) 函数
3. 在程序开始前，从 PMEVCNTR<n>_EL0 读取一次计数器的当前取值，对应 [armv8pmu_read_counter](https://github.com/torvalds/linux/blob/7cb1b466315004af98f6ba6c2546bb713ca3c237/drivers/perf/arm_pmuv3.c#L566) 函数
4. 在程序结束时，再读取一次计数器的当前取值，和程序开始时的值求差
5. 为了解决溢出的问题：配置中断，在溢出时会进入中断处理代码，统计溢出次数，计入差值的高位，对应 [armv8pmu_handle_irq](https://github.com/torvalds/linux/blob/7cb1b466315004af98f6ba6c2546bb713ca3c237/drivers/perf/arm_pmuv3.c#L840) 函数

## Perf 子系统

除了由单独的架构相关的内核驱动负责配置硬件以外，还需要由 Perf 子系统来处理来自用户的 perf 使用。具体地，内核驱动会注册一个 `struct pmu` 给 Perf 子系统，实现这些函数：

```c
// Fully disable/enable this PMU
void (*pmu_enable)		(struct pmu *pmu); /* optional */
void (*pmu_disable)		(struct pmu *pmu); /* optional */
// Try and initialize the event for this PMU.
int (*event_init)		(struct perf_event *event);
// Adds/Removes a counter to/from the PMU
int  (*add)			(struct perf_event *event, int flags);
void (*del)			(struct perf_event *event, int flags);
// Starts/Stops a counter present on the PMU.
void (*start)			(struct perf_event *event, int flags);
void (*stop)			(struct perf_event *event, int flags);
// Updates the counter value of the event.
void (*read)			(struct perf_event *event);
```

可见在内核里，PMU 计数器的抽象是 `struct perf_event`，这个是架构无关的，根据用户态程序通过 `perf_event_open` 构造出来的；内核驱动就会根据这个 `struct perf_event` 去进行实际的硬件计数器的配置。例如用户程序在 `struct perf_event_attr` 里设置 `exclude_kernel = 1`，就会传到 `struct perf_event` 当中，最后在相应的内核驱动中，变成硬件性能计数器配置里，计数时忽略内核所在特权态的配置。

TODO: sampling

TODO: cap_user_rdpmc

TODO: thread/process context switch

## 虚拟化

TODO: kvm

## 参考

- [Arm Architecture Reference Manual for A-profile architecture](https://developer.arm.com/documentation/ddi0487/latest/)
- [LoongArch Reference Manual Volume 1: Basic Architecture](https://loongson.github.io/LoongArch-Documentation/LoongArch-Vol1-EN.html)

