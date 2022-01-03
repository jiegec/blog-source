---
layout: post
date: 2021-01-03 22:19:00 +0800
tags: [chisel,verilog,hdl,cookbook]
category: hardware
title: Chisel3 Cookbook
---

## Chisel 版本选择

尽量选择较新版本的 Chisel。Chisel v3.5 完善了编译器插件，使得生成的代码中会包括更多变量名信息。

## 去掉输出 Verilog 文件中的寄存器随机初始化

版本：FIRRTL >= 1.5.0-RC2

代码：

```scala
new ChiselStage().execute(
  Array("-X", "verilog", "-o", s"${name}.v"),
  Seq(
    ChiselGeneratorAnnotation(genModule),
    CustomDefaultRegisterEmission(
      useInitAsPreset = false,
      disableRandomization = true
    )
  )
)
```

设置 disableRandomization=true 即可。useInitAsPreset 不建议开启。

## 关闭 FIRRTL 优化，输出尽可能与源代码一致的 Verilog

设置 Chisel 生成 MinimumVerilog：

```scala
new ChiselStage().execute(
  Array("-X", "mverilog", "-o", s"${name}.v"),
  Seq(
    ChiselGeneratorAnnotation(genModule)
  )
)
```

此时代码中会保留更多原始 Chisel 代码的元素。