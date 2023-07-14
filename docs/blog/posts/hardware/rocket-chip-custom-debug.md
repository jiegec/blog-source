---
layout: post
date: 2022-05-13
tags: [rocketchip,riscv,debug]
categories:
    - hardware
---

# 向 Rocket Chip 添加自定义调试信号

## 背景

最近在尝试把核心作为一个 Tile 加到 Rocket System 中，所以想要把核心之前自定义的调试信号接到顶层上去。Rocket System 自带的支持是 trace，也就是输出每个周期 retire 的指令信息，但和自定义的不大一样，所以研究了一下怎么添加自定义的调试信号，并且连接到顶层。

## 分析 Trace 信号连接方式

首先，观察 Rocket Chip 自己使用的 Trace 信号是如何连接到顶层的。在顶层上，可以找到使用的是 `testchipip.CanHaveTraceIO`:

```scala
trait CanHaveTraceIO { this: HasTiles =>
  val module: CanHaveTraceIOModuleImp

  // Bind all the trace nodes to a BB; we'll use this to generate the IO in the imp
  val traceNexus = BundleBridgeNexusNode[Vec[TracedInstruction]]()
  val tileTraceNodes = tiles.flatMap {
    case ext_tile: WithExtendedTraceport => None
    case tile => Some(tile)
  }.map { _.traceNode }

  tileTraceNodes.foreach { traceNexus := _ }
}
```

可以看到，它采用了 diplomacy 的 BundleBridgeNexusNode，把每个 tile 取出来，把它的 traceNode 接到 traceNexus 上。再看一下模块 `CanHaveTraceIOModuleImp` 是怎么实现的：

```scala
trait CanHaveTraceIOModuleImp { this: LazyModuleImpLike =>
  val outer: CanHaveTraceIO with HasTiles
  implicit val p: Parameters

  val traceIO = p(TracePortKey) map ( traceParams => {
    val extTraceSeqVec = (outer.traceNexus.in.map(_._1)).map(ExtendedTracedInstruction.fromVec(_))
    val tio = IO(Output(TraceOutputTop(extTraceSeqVec)))

    val tileInsts = ((outer.traceNexus.in) .map { case (tileTrace, _) => DeclockedTracedInstruction.fromVec(tileTrace) }

    // Since clock & reset are not included with the traced instruction, plumb that out manually
    (tio.traces zip (outer.tile_prci_domains zip tileInsts)).foreach { case (port, (prci, insts)) =>
      port.clock := prci.module.clock
      port.reset := prci.module.reset.asBool
      port.insns := insts
    }

    tio
  })
}
```

可以看到，它从 traceNexus 上接了若干的 trace 信号，然后通过 `IO(TraceOutputTop())` 接到了顶层的输出信号。

再来看看 Rocket 是如何连接的，首先是 `traceNode` 的定义：

```scala
/** Node for the core to drive legacy "raw" instruction trace. */
val traceSourceNode = BundleBridgeSource(() => Vec(traceRetireWidth, new TracedInstruction()))
/** Node for external consumers to source a legacy instruction trace from the core. */
val traceNode: BundleBridgeOutwardNode[Vec[TracedInstruction]] = traceNexus := traceSourceNode
```

然后 Rocket Tile 实现的时候，把自己的 trace 接到 traceSourceNode 上：

```scala
outer.traceSourceNode.bundle <> core.io.trace
```

## 添加自定义调试信号

到这里，整个思路已经比较清晰了，我们只需要照猫画虎地做一个就行。比如要把自己的 Custom Debug 接口暴露出去，首先也是在 Tile 里面创建一个 SourceNode：

```scala
// expose debug
val customDebugSourceNode =
BundleBridgeSource(() => new CustomDebug())
val customDebugNode: BundleBridgeOutwardNode[CustomDebug] =
customDebugSourceNode
```

在 BaseTileModuleImp 里，进行信号的连接：

```scala
// expose debug
outer.customDebugSourceNode.bundle := core.io.debug
```

为了暴露到顶层，我们可以类似地做。在 Subsystem 中：

```scala
// expose debug
val customDebugNexus = BundleBridgeNexusNode[CustomDebug]()
val tileCustomDebugNodes = tiles
  .flatMap { case tile: MeowV64Tile =>
    Some(tile)
  }
  .map { _.customDebugNode }

tileCustomDebugNodes.foreach { customDebugNexus := _ }
```

最后在 SubsystemModule Imp 中连接到 IO：

```scala
// wire custom debug signals
val customDebugIO = outer.customDebugNexus.in.map(_._1)
val customDebug = IO(
  Output(
    Vec(customDebugIO.length, customDebugIO(0).cloneType)
  )
)
for (i <- 0 until customDebug.length) {
  customDebug(i) := customDebugIO(i)
}
```

这样就搞定了。

## 总结

找到这个实现方法，基本是对着自带的 trace 接口做的，比较重要的是理解 diplomacy 里面的两层，第一层是把不同的模块进行一些连接，然后第二层在 ModuleImp 中处理实际的信号和逻辑。