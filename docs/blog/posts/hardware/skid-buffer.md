---
layout: post
date: 2021-01-26
tags: [hdl,pipeline,spinalhdl,skid,buffer,register]
categories:
    - hardware
title: Skid Buffer
---

## Skid buffer

Skid buffer 指的就是，对于 valid + ready 的握手信号，用空间（更多的逻辑）来换取时间（更好的时序）的一个硬件模块。

简单来说，背景就是，为了解决 valid 和 ready 信号在数据流水线上一路经过组合逻辑导致的时序问题，在中途加上一些寄存器来阻隔。当然了，代价就是延迟和面积，不过吞吐量还是需要保持的。

由于需求的不同，Skid buffer 也有不同的实现。目前，找到了四个实现，实现上有所不同，特性也不大一样。

### 统一约定

由于我在 SpinalHDL 语言中重新实现了下面的这些 Skid buffer，所以按照 SpinalHDL 的 Stream 定义接口：

```scala
class SkidBufferCommon[T <: Data](
    gen: => T
) extends Component {
  val io = new Bundle {
    val s = slave(Stream(gen))
    val m = master(Stream(gen))
  }
}
```

在这里，`io.s` 表示从上游取的数据，`io.m` 表示传递给下游的数据。

输出信号共有：`io.s.ready`、`io.m.valid` 和 `io.m.payload`。

### ZipCPU 版本

第一个版本来自 ZipCPU：

博客地址：[Building a Skid Buffer for AXI processing](https://zipcpu.com/blog/2019/05/22/skidbuffer.html)
代码地址：[skidbuffer.v](https://github.com/ZipCPU/wb2axip/blob/master/rtl/skidbuffer.v)

它有两个参数，一个表示是否有额外的输出寄存器（outputReg），一个表示是否低功耗（lowPower）。

### FPGACPU 版本

第二个版本来自 FPGACPU：

文章地址：[Pipeline Skid Buffer](http://fpgacpu.ca/fpga/Pipeline_Skid_Buffer.html)

### SpinalHDL S2M 版本

第三个版本来自 SpinalHDL Library 的 s2mPipe：

代码地址：[Stream.scala L348](https://github.com/SpinalHDL/SpinalHDL/blob/f9eda46bb5968659fe4e97cad8b69c8c0cb2bf89/lib/src/main/scala/spinal/lib/Stream.scala#L348)

### SpinalHDL M2S 版本

第四个版本来自 SpinalHDL Library 的 m2sPipe：

代码地址：[Stream.scala L327](https://github.com/SpinalHDL/SpinalHDL/blob/f9eda46bb5968659fe4e97cad8b69c8c0cb2bf89/lib/src/main/scala/spinal/lib/Stream.scala#L327)

### 四个版本的对比

在研究了代码以后，可以看到这四个版本的区别：

| 版本         | ZipCPU w/ outputReg | ZipCPU w/o outputReg | FPGACPU | S2M  | M2S  |
| ------------ | ------------------- | -------------------- | ------- | ---- | ---- |
| io.s.ready   | Reg                 | Reg                  | Reg     | Reg  | Comb |
| io.m.valid   | Reg                 | Comb                 | Reg     | Comb | Reg  |
| io.m.payload | Reg                 | Comb                 | Reg     | Comb | Reg  |
| latency      | 1                   | 0                    | 1       | 0    | 1    |
| buffer 数量  | 1                   | 1                    | 2       | 1    | 1    |

注：

1. Reg 表示从寄存器输出，Comb 表示从组合逻辑输出
2. Latency 表示从 `io.s.fire` 到 `io.m.fire` 的延迟
3. Buffer 表示缓冲的 payload 个数
4. ZipCPU w/o outputReg 和 S2M 实现的逻辑是一样的

### 形式化验证

为了确认上面这些类型的 Skid Buffer 都可以正常工作，按照 ZipCPU Skid Buffer 的文章，也照着写了几个 property：

1: 在 valid && ~ready 的时候，valid 需要继续保持为高，并且 payload 不变：

```scala
// When valid goes high, data is stable and valid stays high before ready
when(past(stream.valid && ~stream.ready && ~outerReset)) {
    slaveAssume(stream.valid);
    if (dataStable) {
        slaveAssume(stable(stream.payload.asBits));
    }
}
```

2: 在 reset 释放的第一个周期里，valid 不能为高：

参考 AXI 标准 (IHI0022E Page 38 A3.1.2) 原文：

```text
The earliest point after reset that a master is permitted to begin driving ARVALID, AWVALID, or WVALID HIGH is at a rising ACLK edge after ARESETn is HIGH.
```

```scala
// Valid is low in the first cycle after reset falls
when(pastValid && past(outerReset) && ~outerReset) {
    slaveAssume(~stream.valid);
}
```

3: 添加 cover property，要求 `io.s` 和 `io.m` 可以连续若干个周期 valid && ready，保证吞吐率：

```scala
cover(
    pastValid && genPast(pastValid, null, cycles) && genPast(
        ~outerReset,
        null,
        cycles
    ) && genPast(stream.fire, payload, cycles)
)
```

采用 `yosys-smtbmc` 工具验证了以上四种 Skid buffer 都满足这些属性。
