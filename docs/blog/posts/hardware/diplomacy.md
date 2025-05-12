---
layout: post
date: 2022-01-05
tags: [chisel,rocketchip,diplomacy]
categories:
    - hardware
---

# 分析 Rocket Chip 中 Diplomacy 系统

## 概念

Diplomacy 主要实现了两个功能：

1. 把整个总线结构在代码中表现出来
2. 自动配置总线中各个端口的参数

具体来说，第一点实现了类似 Vivado Board Design 中连线的功能，第二点则是保证总线两端的参数一致，可以连接起来。

Diplomacy 为了表示总线的结构，每个模块可以对应一个 Node，Node 和 Node 之间连接形成一个图。Node 的类型主要有以下几个：

1. Client：对应 AXI 里面的 Master，发起请求
2. Manager：对应 AXI 里面的 Slave，处理请求
3. Adapter：对应 AXI Width Converter/Clock Converter/AXI4 to AXI3/AXI4 to AHB bridge 等，会修改 AXI 的参数，然后每个输入对应一个输出，不改变数量
4. Nexus：对应 AXI Crossbar，多个输入和多个输出，输入输出数量可能不同

每个 Node 可能作为 Manager 连接上游的 Client，这个叫做入边（Inward Edge）；同样地，也可以作为 Client 连接下游的 Manager，这个是出边（Outward Edge）。想象成一个 DAG，从若干个 Client 流向 Manager。

连接方式采用的是 `:=` `:=*` `:*=` `:*=*` 操作符，左侧是 Manager（Slave），右侧是 Client（Master）。它们的区别如下：

- `:=`：在两个 Node 之间只连一条边
- `:=*`：Query 连接，意思是在两个 Node 之间连接多条边，连接的边的数量取决于右边的 Node
- `:*=`：Star 连接，意思是在两个 Node 之间连接多条边，连接的边的数量取决于左边的 Node
- `:*=*`：Flex 连接，意思是在两个 Node 之间连接多条边，连接的边的数量取决于哪边的 Node 可以确认边的数量

由于各模块的硬件描述，需要等到连接图建立完成后，才能生成，因此 Diplomacy 采用了两阶段：

1. 第一个阶段发生在 LazyModule 中，通过 LazyModule 嵌套其他模块，并把 LazyModule 之间的 Node 连接起来，组成一个图，协商每一条边对应的参数
2. 第二个阶段发生在 LazyModuleImp 中，当访问 LazyModule 的 module 字段的时候，才会生成对应的硬件描述

比如一个加法器的例子，如果不使用 Diplomacy，就是直接写在 Module 当中：

```scala
import circt.stage.ChiselStage
import chisel3._

class Adder extends Module {
  val in1 = IO(Input(UInt(32.W)))
  val in2 = IO(Input(UInt(32.W)))
  val out = IO(Output(UInt(32.W)))
  out := in1 + in2
}

object Adder extends App {
  println(
    ChiselStage.emitSystemVerilog(
      new Adder(),
      firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
    )
  )
}
```

如果想要使用 Diplomacy，就需要把连接关系的建立，和硬件描述两部分分开：

```scala
import org.chipsalliance.diplomacy.lazymodule.LazyModule
import org.chipsalliance.diplomacy.lazymodule.LazyModuleImp
import org.chipsalliance.cde.config.Parameters
import circt.stage.ChiselStage
import chisel3._

class AdderDiplomacyModule()(implicit p: Parameters) extends LazyModule {
  lazy val module = new AdderDiplomacyModuleImp(this)
}

class AdderDiplomacyModuleImp(outer: AdderDiplomacyModule)
    extends LazyModuleImp(outer) {
  val in1 = IO(Input(UInt(32.W)))
  val in2 = IO(Input(UInt(32.W)))
  val out = IO(Output(UInt(32.W)))
  out := in1 + in2
}

object AdderDiplomacy extends App {
  println(
    ChiselStage.emitSystemVerilog(
      LazyModule(new AdderDiplomacyModule()(Parameters.empty)).module,
      firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
    )
  )
}
```

有时候，如果硬件实现部分比较简单，也可以不另起一个类，直接用 Scala 的语法写一个子类：

```scala
import org.chipsalliance.diplomacy.lazymodule.LazyModule
import org.chipsalliance.diplomacy.lazymodule.LazyModuleImp
import org.chipsalliance.cde.config.Parameters
import circt.stage.ChiselStage
import chisel3._

class AdderDiplomacyCompactModule()(implicit p: Parameters) extends LazyModule {
  lazy val module = new LazyModuleImp(this) {
    val in1 = IO(Input(UInt(32.W)))
    val in2 = IO(Input(UInt(32.W)))
    val out = IO(Output(UInt(32.W)))
    out := in1 + in2
  }
}

object AdderDiplomacyCompact extends App {
  println(
    ChiselStage.emitSystemVerilog(
      LazyModule(new AdderDiplomacyCompactModule()(Parameters.empty)).module,
      firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
    )
  )
}
```

## 代码解析

下面对着 Diplomacy 的源码进行解析。前面提到，Diplomacy 把各 Node 通过 Edge 连接成了一个图，下面介绍这个图的组织方式。

首先是 Node 的定义：它的基类是 BaseNode，它根据 InwardNode 和 OutwardNode 两个 trait，分别记录这个 Node 的入边和出边。
然后入边和出边分别对应 InwardEdge 和 OutwardEdge 两个 class，每条边上对应一个 Bundle，也对应了硬件上两个模块之间的 IO：

```scala
/** Contains information about an inward edge of a node */
case class InwardEdge[Bundle <: Data, EdgeInParams](
  params: Parameters,
  bundle: Bundle,
  edge:   EdgeInParams,
  node:   OutwardNode[_, _, Bundle])

/** Contains information about an outward edge of a node */
case class OutwardEdge[Bundle <: Data, EdgeOutParams](
  params: Parameters,
  bundle: Bundle,
  edge:   EdgeOutParams,
  node:   InwardNode[_, _, Bundle])
```

InwardEdge 记录了它是从哪个 OutwardNode 过来的；OutwardEdge 记录了它要连接到哪个 InwardNode 上。InwardNode 记录了它从哪些 OutwardNode 通过 InwardEdge 建立了连接；OutwardNode 记录了它通过 OutwardEdge 连接到了哪些 InwardNode 上：

```scala
/** A Node that defines inward behavior, meaning that it can have edges coming into it and be used on the left side of
  * binding expressions.
  */
trait InwardNode[DI, UI, BI <: Data] extends BaseNode {
  /** accumulates input connections. */
  private val accPI = ListBuffer[(Int, OutwardNode[DI, UI, BI], NodeBinding, Parameters, SourceInfo)]()
}

/** A Node that defines outward behavior, meaning that it can have edges coming out of it. */
trait OutwardNode[DO, UO, BO <: Data] extends BaseNode {
  /** Accumulates output connections. */
  private val accPO = ListBuffer[(Int, InwardNode[DO, UO, BO], NodeBinding, Parameters, SourceInfo)]()
}
```

一个 Node 可以同时继承 InwardNode 和 OutwardNode。

特别地，为了方便使用，在连接的时候未必是每次只连接一条边，比如可能一次性把多个 AXI 都接过去，比如前面提到的 Query/Star/Flex connection，这个信息会被记录在 NodeBinding 类型中。具体的连接个数，是通过 lazy evaluation + recursion 计算出来的。

## Rocket Chip 总线结构

Rocket Chip 主要有以下几个总线：

1. sbus: System Bus
2. mbus: Memory Bus
3. cbus: Control Bus
4. pbus: Periphery Bus
5. fbus: Frontend Bus

图示可以见参考文档中的链接，不过链接中的结构和实际的有一些区别。目前的 Rocket Chip 内存结构大致是这样：

```
fbus -> sbus -> mbus
tile --/    \-> cbus -> pbus
```

主要是 pbus 的位置从连接 sbus 移动到了连接 cbus。

相关代码：

```scala
/** Parameterization of a topology containing three additional, optional buses for attaching MMIO devices. */
case class HierarchicalBusTopologyParams(
  pbus: PeripheryBusParams,
  fbus: FrontBusParams,
  cbus: PeripheryBusParams,
  xTypes: SubsystemCrossingParams,
  driveClocksFromSBus: Boolean = true
) extends TLBusWrapperTopology(
  instantiations = List(
    (PBUS, pbus),
    (FBUS, fbus),
    (CBUS, cbus)),
  connections = List(
    (SBUS, CBUS, TLBusWrapperConnection  .crossTo(xTypes.sbusToCbusXType, if (driveClocksFromSBus) Some(true) else None)),
    (CBUS, PBUS, TLBusWrapperConnection  .crossTo(xTypes.cbusToPbusXType, if (driveClocksFromSBus) Some(true) else None)),
    (FBUS, SBUS, TLBusWrapperConnection.crossFrom(xTypes.fbusToSbusXType, if (driveClocksFromSBus) Some(false) else None)))
)
```

当然了，也有简化版的 JustOneBusTopology，那就只有 SystemBus 了。如果再配置了 CoherentBusTopology，那么 SBUS 和 MBUS 之间还有一层 L2:

```scala
/** Parameterization of a topology containing a banked coherence manager and a bus for attaching memory devices. */
case class CoherentBusTopologyParams(
  sbus: SystemBusParams, // TODO remove this after better width propagation
  mbus: MemoryBusParams,
  l2: BankedL2Params,
  sbusToMbusXType: ClockCrossingType = NoCrossing,
  driveMBusClockFromSBus: Boolean = true
) extends TLBusWrapperTopology(
  instantiations = (if (l2.nBanks == 0) Nil else List(
    (MBUS, mbus),
    (L2, CoherenceManagerWrapperParams(mbus.blockBytes, mbus.beatBytes, l2.nBanks, L2.name, sbus.dtsFrequency)(l2.coherenceManager)))),
  connections = if (l2.nBanks == 0) Nil else List(
    (SBUS, L2,   TLBusWrapperConnection(driveClockFromMaster = Some(true), nodeBinding = BIND_STAR)()),
    (L2,  MBUS,  TLBusWrapperConnection.crossTo(
      xType = sbusToMbusXType,
      driveClockFromMaster = if (driveMBusClockFromSBus) Some(true) else None,
      nodeBinding = BIND_QUERY))
  )
)
```

## 参考文档

- [TileLink and Diplomacy Reference](https://chipyard.readthedocs.io/en/latest/TileLink-Diplomacy-Reference/index.html)
- [Rocket Chip - Memory System](https://chipyard.readthedocs.io/en/latest/Generators/Rocket-Chip.html#memory-system)
- [chipsalliance/diplomacy](https://github.com/chipsalliance/diplomacy)
