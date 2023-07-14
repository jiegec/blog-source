---
layout: post
date: 2022-01-03
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

## 重命名 AXI4 为标准命名

Rocket Chip 中 AXI4Bundle 直接生成的名字和标准写法不同，可以利用 Chisel3 3.5.0 的 DataView 功能进行重命名：

```scala
// https://www.chisel-lang.org/chisel3/docs/explanations/dataview.html
// use standard names
class StandardAXI4BundleBundle(val addrBits: Int, val dataBits: Int, val idBits: Int)
    extends Bundle {
  val AWREADY = Input(Bool())
  val AWVALID = Output(Bool())
  val AWID = Output(UInt(idBits.W))
  val AWADDR = Output(UInt(addrBits.W))
  val AWLEN = Output(UInt(8.W))
  val AWSIZE = Output(UInt(3.W))
  val AWBURST = Output(UInt(2.W))
  val AWLOCK = Output(UInt(1.W))
  val AWCACHE = Output(UInt(4.W))
  val AWPROT = Output(UInt(3.W))
  val AWQOS = Output(UInt(4.W))

  val WREADY = Input(Bool())
  val WVALID = Output(Bool())
  val WDATA = Output(UInt(dataBits.W))
  val WSTRB = Output(UInt((dataBits / 8).W))
  val WLAST = Output(Bool())

  val BREADY = Output(Bool())
  val BVALID = Input(Bool())
  val BID = Input(UInt(idBits.W))
  val BRESP = Input(UInt(2.W))

  val ARREADY = Input(Bool())
  val ARVALID = Output(Bool())
  val ARID = Output(UInt(idBits.W))
  val ARADDR = Output(UInt(addrBits.W))
  val ARLEN = Output(UInt(8.W))
  val ARSIZE = Output(UInt(3.W))
  val ARBURST = Output(UInt(2.W))
  val ARLOCK = Output(UInt(1.W))
  val ARCACHE = Output(UInt(4.W))
  val ARPROT = Output(UInt(3.W))
  val ARQOS = Output(UInt(4.W))

  val RREADY = Output(Bool())
  val RVALID = Input(Bool())
  val RID = Input(UInt(idBits.W))
  val RDATA = Input(UInt(dataBits.W))
  val RRESP = Input(UInt(2.W))
  val RLAST = Input(Bool())
}

object StandardAXI4BundleBundle {
  implicit val axiView = DataView[StandardAXI4BundleBundle, AXI4Bundle](
    vab =>
      new AXI4Bundle(
        AXI4BundleParameters(vab.addrBits, vab.dataBits, vab.idBits)
      ),
    // AW
    _.AWREADY -> _.aw.ready,
    _.AWVALID -> _.aw.valid,
    _.AWID -> _.aw.bits.id,
    _.AWADDR -> _.aw.bits.addr,
    _.AWLEN -> _.aw.bits.len,
    _.AWSIZE -> _.aw.bits.size,
    _.AWBURST -> _.aw.bits.burst,
    _.AWLOCK -> _.aw.bits.lock,
    _.AWCACHE -> _.aw.bits.cache,
    _.AWPROT -> _.aw.bits.prot,
    _.AWQOS -> _.aw.bits.qos,
    // W
    _.WREADY -> _.w.ready,
    _.WVALID -> _.w.valid,
    _.WDATA -> _.w.bits.data,
    _.WSTRB -> _.w.bits.strb,
    _.WLAST -> _.w.bits.last,
    // B
    _.BREADY -> _.b.ready,
    _.BVALID -> _.b.valid,
    _.BID -> _.b.bits.id,
    _.BRESP -> _.b.bits.resp,
    // AR
    _.ARREADY -> _.ar.ready,
    _.ARVALID -> _.ar.valid,
    _.ARID -> _.ar.bits.id,
    _.ARADDR -> _.ar.bits.addr,
    _.ARLEN -> _.ar.bits.len,
    _.ARSIZE -> _.ar.bits.size,
    _.ARBURST -> _.ar.bits.burst,
    _.ARLOCK -> _.ar.bits.lock,
    _.ARCACHE -> _.ar.bits.cache,
    _.ARPROT -> _.ar.bits.prot,
    _.ARQOS -> _.ar.bits.qos,
    // R
    _.RREADY -> _.r.ready,
    _.RVALID -> _.r.valid,
    _.RID -> _.r.bits.id,
    _.RDATA -> _.r.bits.data,
    _.RRESP -> _.r.bits.resp,
    _.RLAST -> _.r.bits.last
  )
  implicit val axiView2 = StandardAXI4BundleBundle.axiView.invert(ab =>
    new StandardAXI4BundleBundle(
      ab.params.addrBits,
      ab.params.dataBits,
      ab.params.idBits
    )
  )
}

// usage
val MEM = IO(new StandardAXI4BundleBundle(32, 64, 4))
MEM <> target.mem_axi4.head.viewAs[StandardAXI4BundleBundle]
```

## 给所有模块添加名称前缀

有些时候，我们希望给所有模块添加一个名称前缀，防止可能出现的冲突。

在 Chisel 3 中，可以使用自定义 FIRRTL Transform 来实现这个功能。这一部分的实现参考了 [chisel issue #1059](https://github.com/chipsalliance/chisel3/issues/1059#issuecomment-814353578)：

```scala
import firrtl._
import firrtl.annotations.NoTargetAnnotation
import firrtl.options.Dependency
import firrtl.passes.PassException
import firrtl.transforms.DedupModules

// adapted from https://github.com/chipsalliance/chisel3/issues/1059#issuecomment-814353578

/** Specifies a global prefix for all module names. */
case class ModulePrefix(prefix: String) extends NoTargetAnnotation

/** FIRRTL pass to add prefix to module names
  */
object PrefixModulesPass extends Transform with DependencyAPIMigration {
  // we run after deduplication to save some work
  override def prerequisites = Seq(Dependency[DedupModules])

  // we do not invalidate the results of any prior passes
  override def invalidates(a: Transform) = false

  override protected def execute(state: CircuitState): CircuitState = {
    val prefixes = state.annotations.collect { case a: ModulePrefix =>
      a.prefix
    }.distinct
    prefixes match {
      case Seq() =>
        logger.info("[PrefixModulesPass] No ModulePrefix annotation found.")
        state
      case Seq("") => state
      case Seq(prefix) =>
        val c = state.circuit.mapModule(onModule(_, prefix))
        state.copy(circuit = c.copy(main = prefix + c.main))
      case other =>
        throw new PassException(
          s"[PrefixModulesPass] found more than one prefix annotation: $other"
        )
    }
  }

  private def onModule(m: ir.DefModule, prefix: String): ir.DefModule =
    m match {
      case e: ir.ExtModule => e.copy(name = prefix + e.name)
      case mod: ir.Module =>
        val name = prefix + mod.name
        val body = onStmt(mod.body, prefix)
        mod.copy(name = name, body = body)
    }

  private def onStmt(s: ir.Statement, prefix: String): ir.Statement = s match {
    case i: ir.DefInstance => i.copy(module = prefix + i.module)
    case other             => other.mapStmt(onStmt(_, prefix))
  }
}
```

实现思路就是遍历 IR，找到所有的 Module 并改名，再把所有模块例化也做一次替换。最后在生成 Verilog 的时候添加 Annotation 即可：

```scala
new ChiselStage().execute(
  Array("-o", s"${name}.v"),
  Seq(
    ChiselGeneratorAnnotation(genModule),
    RunFirrtlTransformAnnotation(Dependency(PrefixModulesPass)),
    ModulePrefix(prefix)
  )
```

如果使用新的 MLIR FIRRTL Compiler，则可以利用 `sifive.enterprise.firrtl.NestedPrefixModulesAnnotation` annotation，让 firtool 来进行 [prefix 操作](https://github.com/llvm/circt/blob/fc6b00fd20d8a50f17a908cc681c8cf3a4d1c000/lib/Dialect/FIRRTL/Transforms/PrefixModules.cpp)：

```scala
package sifive {
  package enterprise {
    package firrtl {
      import _root_.firrtl.annotations._

      case class NestedPrefixModulesAnnotation(
          val target: Target,
          prefix: String,
          inclusive: Boolean
      ) extends SingleTargetAnnotation[Target] {

        def duplicate(n: Target): Annotation =
          NestedPrefixModulesAnnotation(target, prefix, inclusive)
      }
    }
  }
}

object AddPrefix {
  def apply(module: Module, prefix: String, inclusive: Boolean = true) = {
    annotate(new ChiselAnnotation {
      def toFirrtl =
        new NestedPrefixModulesAnnotation(module.toTarget, prefix, inclusive)
    })
  }
}
```

这个方法的灵感来自 @sequencer。唯一的缺点就是比较 Hack，建议 SiFive 把相关的类也开源出来用。
