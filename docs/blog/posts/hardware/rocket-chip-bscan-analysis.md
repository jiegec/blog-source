---
layout: post
date: 2020-02-09
tags: [fpga,riscv,rocketchip,bscan,jtag,openocd]
categories:
    - hardware
---

# 研究 Rocket Chip 的 BSCAN 调试原理

## 前言

最近 [@jsteward](https://github.com/KireinaHoro) 在研究如何通过 JTAG 对 FPGA 里的 Rocket Chip 进行调试。之前 [@sequencer](https://github.com/sequencer) 已经做了一些实践，我们在重复他的工作，同时也研究了一下这是怎么工作的。

## 原理

我们从 @sequencer 得到了一份可用的 [Scala 代码](https://github.com/sequencer/rocket-playground/blob/7fa3c51113be607add2034f3abe0ae973caac04a/playground/src/FPGA.scala#L83) 和 [OpenOCD 配置](https://github.com/sequencer/rocket-playground/blob/7fa3c51113be607add2034f3abe0ae973caac04a/playground/debugger/openocd.cfg#L16)，并且了解到：

1. 可以通过 openocd 找到并调试 Rocket Chip
2. openocd 是通过 JTAG 向 FPGA 的 TAP 的 IR 写入 USER4，然后往 DR 写入特定格式的数据，然后控制 Rocket Chip 的 JTAG。

这里涉及到一个“封装”的过程，在一个仅可以控制 DR 的 JTAG 中控制另一个 JTAG。首先可以找到 OpenOCD 端的[操作代码](https://github.com/riscv/riscv-openocd/blob/7cb8843794a258380b7c37509e5c693977675b2a/src/target/riscv/riscv.c#L361)：

```cpp
tunneled_ir[3].num_bits = 3;
tunneled_ir[3].out_value = bscan_zero;
tunneled_ir[3].in_value = NULL;
tunneled_ir[2].num_bits = bscan_tunnel_ir_width;
tunneled_ir[2].out_value = ir_dtmcontrol;
tunneled_ir[1].in_value = NULL;
tunneled_ir[1].num_bits = 7;
tunneled_ir[1].out_value = tunneled_ir_width;
tunneled_ir[2].in_value = NULL;
tunneled_ir[0].num_bits = 1;
tunneled_ir[0].out_value = bscan_zero;
tunneled_ir[0].in_value = NULL;
```

如果画成图，大概是这个样子（IR）：

| 3 bits | IR Width bits | 7 bits            | 1 bit | TDI  | Data Register   | TDO  |
| ------ | ------------- | ----------------- | ----- | ---- | --------------- | ---- |
| 0      | Payload       | Tunneled IR Width | 0     | ->   | Rocket Chip TAP | ->   |

DR：

| 3 bits | DR Width bits | 7 bits            | 1 bit | TDI  | Data Register   | TDO  |
| ------ | ------------- | ----------------- | ----- | ---- | --------------- | ---- |
| 0      | Payload       | Tunneled DR Width | 1     | ->   | Rocket Chip TAP | ->   |

这里 TDI 和 TDO 是直接接到 Rocket Chip 的 JTAG 中的，所以我们期望，当 Rocket Chip TAP 在 Shift-IR/Shift-DR 阶段的时候，刚好通过的是 Payload 部分。而控制 TAP 状态机，需要控制 TMS，这个则是通过一段 [HDL](https://github.com/sifive/fpga-shells/blob/c099bd9b4f916bc0ba88030939a9614d0b0daf2d/src/main/scala/ip/xilinx/Xilinx.scala#L13) 来完成的：

```verilog
always@(*) begin 
        if (counter_neg == 8'h04) begin 
                jtag_tms = TDI_REG; 
        end else if (counter_neg == 8'h05) begin 
                jtag_tms = 1'b1; 
        end else if ((counter_neg == (8'h08 + shiftreg_cnt)) || (counter_neg == (8'h08 + shiftreg_cnt - 8'h01))) begin 
                jtag_tms = 1'b1; 
        end else begin 
                jtag_tms = 1'b0; 
        end 
end
```

这里 `TDI_REG` 取的是第一个 bit 的反（也就是上面 IR 对应 0，DR 对应 1 的那一位），`shiftreg_cnf` 则是之后 7 个 bit，对应上面的 Tunneled IR/DR Width。那么，在选择 IR 时 TMS 的序列为：

| 4 cycles      | 1 cycle        | 1 cycle        | 2 cycles             | shiftreg_cnt-1 cycles | 2 cycles            | rest cycles   |
| ------------- | -------------- | -------------- | -------------------- | --------------------- | ------------------- | ------------- |
| 0             | 1              | 1              | 0                    | 0                     | 1                   | 0             |
| Run-Test/Idle | Select-DR-Scan | Select-IR-Scan | Capture-IR, Shift-IR | Shift-IR              | Exit1-IR, Update-IR | Run-Test/Idle |

类似地，如果是选择 DR：

| 4 cycles      | 1 cycle       | 1 cycle        | 2 cycles             | shiftreg_cnt-1 cycles | 2 cycles            | rest cycles   |
| ------------- | ------------- | -------------- | -------------------- | --------------------- | ------------------- | ------------- |
| 0             | 0             | 1              | 0                    | 0                     | 1                   | 0             |
| Run-Test/Idle | Run-Test/Idle | Select-DR-Scan | Capture-DR, Shift-DR | Shift-DR              | Exit1-DR, Update-DR | Run-Test/Idle |

这样，刚好在 Shift-IR/DR 状态下，Payload 会被写入 IR/DR，从而完成了期望的操作。通过规定一个特定格式的 Data Register，可以实现嵌套的 TAP 的 IR 和 DR 的操作。

## 参考

1. JTAG Standard
2. [sequencer/rocket-playground](https://github.com/sequencer/rocket-playground)
3. SiFive's JTAG Tunnel: https://github.com/sifive/fpga-shells/blob/c099bd9b4f916bc0ba88030939a9614d0b0daf2d/src/main/scala/ip/xilinx/Xilinx.scala#L13
4. https://github.com/watz0n/arty_xjtag
5. https://github.com/riscv/riscv-openocd/blob/7cb8843794a258380b7c37509e5c693977675b2a/src/target/riscv/riscv.c#L361
6. UG740: 7 Series FPGAs Configuration