---
layout: post
date: 2020-03-17 23:20:00 +0800
tags: [chisel,rocketchip,riscv]
category: hardware
title: 在 Rocket Chip 上挂接 TLRAM
---

最近遇到一个需求，需要在 Rocket Chip 里面开辟一块空间，通过 verilog 的 $readmemh 来进行初始化而不是用 BootROM ，这样每次修改内容不需要重新跑一次 Chisel -> Verilog 的流程。然后到处研究了一下，找到了解决的方案：

首先是新建一个 TLRAM 然后挂接到 cbus 上：

```scala
import freechips.rocketchip.tilelink.TLRAM
import freechips.rocketchip.tilelink.TLFragmenter
import freechips.rocketchip.diplomacy.LazyModule
import freechips.rocketchip.diplomacy.AddressSet

trait HasTestRAM { this: BaseSubsystem =>
  val testRAM = LazyModule(
    new TLRAM(AddressSet(0x40000000, 0x1FFF), beatBytes = cbus.beatBytes)
  )

  testRAM.node := cbus.coupleTo("bootrom") { TLFragmenter(cbus) := _ }
}

```

这里的地址和大小都可以自由定义。然后添加到自己的 Top Module 中：

```scala
class TestTop(implicit p:Parameters)
	extends RocketSystem
	// ...
	with HasTestRAM
	//...
	{
	override lazy ...    
}
```

实际上这时候 TLRAM 就已经加入到了 TileLink 总线中。接着，为了让 firrtl 生成 $readmemh 的代码，需要两个步骤：

首先是用 `chisel3.util.experimental.loadMemoryFromFile` 函数（文档在 https://github.com/freechipsproject/chisel3/wiki/Chisel-Memories）：

UPDATE：现在的文档在 [Loading Memories for simulation or FPGA initialization](https://www.chisel-lang.org/chisel3/docs/appendix/experimental-features#loading-memories-for-simulation-or-fpga-initialization-) 处，并且可以用 loadMemoryFromFileInline。

```scala
class TestTopImp(outer: TestTop)
	extends RocketSubsystemModuleImp(outer)
	// ...
	{
	loadMemoryFromFile(outer.testRAM.module.mem, "test.hex")    
}
```

这个函数会生成一个 FIRRTL Annotation，记录了在这里需要对这个 mem 生成对应的 readmemh 调用。然后在 firrtl 的调用里传入 .anno.json 和 transform：

```bash
$ runMain firrtl.stage.Main -i xxx -o xxx -X verilog -faf /path/to/xxx.anno.json -fct chisel3.util.experimental.LoadMemoryTransform
```

UPDATE: 现在不需要 `-fct chisel3.util.experimental.LoadMemoryTransform` 参数。

这里的 chisel3.util.experimental.LoadMemoryTransform 会找到 anno.json 里面对应的 Annotation，然后生成类似下面这样的 verilog 代码：

```verilog
module xxx(
	// ...
);
  // ...
	$readmemh(path, mem_xxx);
endmodule

bind TLRAM xxx xxx(.*);
```

这里采用了 Verilog 的 bind 功能，可以在不修改模块代码的时候注入，比如上面，就是注入了一个语句 $readmemh ，从而达到目的。