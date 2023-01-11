---
layout: post
date: 2023-01-10 21:38:00 +0800
tags: [mit,mit6824,distributed,raft,mapreduce,gfs,zookeeper]
category: system
title: MIT 6.824 Distributed Systems 学习笔记
---

## 背景

本来打算去年上分布式系统课的，但是由于时间冲突没有选，今年想上的时候课程又没有开，因此利用寒假时间自学 [MIT 6.824 Distributed Systems 课程 Spring 2022](https://pdos.csail.mit.edu/6.824/index.html)，跟着看视频，Lecture Notes 还有论文，同时也完成课程的实验。在这里分享一下我在学习过程中的一些笔记和感悟。

## MapReduce

### 背景

第一篇论文是 2004 年发表的 [MapReduce: Simplified Data Processing on Large Clusters](https://pdos.csail.mit.edu/6.824/papers/mapreduce.pdf)，论文的作者是耳熟能详的 Jeffrey Dean 和 Sanjay Ghemawat，这个思想到现在依然在广泛使用，目前比较常见的开源 MapReduce 实现是 Apache Hadoop。

论文要解决的问题是，随着数据量增大，需要在集群上并行完成任务，那么如何在集群上并行计算，分发数据，并且在机器出问题的时候继续工作，就成了很大的问题。所以如果有一个框架，负责完成并行、容错和复杂均衡这些底层细节，向上层应用提供一个简单的抽象，这样就可以减轻开发者的负担。MapReduce 就是这样的一个框架。

### 编程抽象

从框架的角度，需要设计一个合理的抽象，向下适合并行计算，向上适合应用的实现。从并行的角度来说，最容易想到的就是尴尬并行，直接把数据分布到各个节点上，每个节点处理自己的一部分数据。但是很多应用不能用尴尬并行实现，比如排序，每个节点对自己得到的一部分数据排好序以后，还需要进行合并，得到最终全局排好序的数据。所以 MapReduce 设计抽象的时候，分成了两个步骤：Map 和 Reduce。如果直接采用函数式编程中的 Map 和 Reduce 的定义，可以用下面的方式表示（类型采用 Haskell 的约定）：

- 输入类型是 A，数据是一个 A 数组，表示为 `[A]`
- Map 函数: 输入类型 A，输出类型 B，表示为 `A -> B`
- Reduce 函数：输入两个 B，输出一个 B，表示为 `B -> B -> B`
- 计算过程就是对输入的每个元素应用一次 Map 函数，然后通过 Reduce 函数进行规约，最后输出一个 B

从并行计算的角度来说，Map 函数可以尴尬并行，如果 Reduce 函数满足结合律，那么可以用树形的方式进行规约，否则就只能串行规约。拿排序的例子来说，如果要排序一个 int 数组，首先把数组分成 n 份，每一份的类型是 `[Integer]`，把它作为 Map 函数的输入，也就是说，A 就是 `[Integer]`，Map 函数进行排序，输出排序后的数组，类型 B 也是 `[Integer]`，然后 Reduce 函数合并两个已经排好序的数组。这里的 Reduce 满足结合律，所以可以很好地并行。

再考虑另一个应用，单词出现次数统计：输入若干段文本，Map 函数计算一段文本中的单词出现次数，输入一个字符串，输出一个 `Map String Integer`，键是单词，值是出现次数，所以 Map 函数的类型是 `String -> Map String Integer`，Reduce 函数类型是 `Map String Integer -> Map String Integer -> Map String Integer`，得到单词在所有文本中出现的总次数。可以想象，Reduce 实现类似下面的代码：

	Input: Left, Right
	Output: Result
	For each key in Left.keys() \/ Right.keys():
		Result[key] = (Left[key] or 0) + (Right[key] or 0)

可以看到，Reduce 函数的内层循环也是可以尴尬并行的，既然可以尴尬并行，那并行度会比树形规约更高，同时也更容易实现。如果基于单词次数统计算法进行抽象，重新设计：

- 输入类型是 A，数据是一个 A 数组，表示为 `[A]`
- Map 函数: 输入类型 A，输出类型 `Map B C`，表示为 `A -> Map B C`
- Reduce 函数：输入 B 和 C 数组，输出 C，表示为 `B -> [C] -> C`
- 计算过程就是对输入的每个元素应用一次 Map 函数，得到若干个 `Map B C`，然后按照 B 进行划分，因为不同的 A 经过 Map 后可以得到同样的 B，所以 Reduce 输入是一个 B 以及多个 C。因为 Reduce 函数已经尴尬并行了，所以 Reduce 内部就没有再做树形规约。

单词统计在上面的抽象下，A 对应 `String`，也就是输入的文本内容，Map 函数统计单词的出现次数，B 是 `String`，`C` 是 Integer；Reduce 之前，同样的单词的 C 会被合并为一个数组 `[Integer]`，那么 Reduce 函数就是给定一个单词，以及它在各个文本中出现的次数数组，只需要对数组进行求和，就可以得到最终结果。

这个抽象已经和论文中给出的十分接近了，下面摘抄论文中的描述：

	map (k1, v1) -> list(k2, v2)
	reduce (k2, list(v2)) -> list(v2)

	Map, written by the user, takes an input pair and produces a set of
	intermediate key/value pairs. The MapReduce library groups together all
	intermediate values associated with the same intermediate key I and
	passes them to the Reduce function. The Reduce function, also written by
	the user, accepts an intermediate key I and a set of values for that
	key. It merges together these values to form a possibly smaller set of
	values. Typically just zero or one output value is produced per Reduce
	invocation. The intermediate values are supplied to the user’s reduce
	function via an iterator. This allows us to handle lists of values that
	are too large to fit in memory.

所以 MapReduce 可以分为三个步骤：

1. Map 阶段：节点并行执行 Map 函数，每个节点处理一部分的 `(k1, v1)` 输入
2. Shuffle 阶段：收集 Map 阶段的计算结果，根据 k2 分发到不同的节点
3. Reduce 阶段：节点并行执行 Reduce 函数，每个节点处理一部分的 `(k2, list(k2))` 中间结果

### 实现

讲完上层实现以后，MapReduce 框架本身需要处理底层的细节，比如给节点分配任务，监控任务的执行情况，如果出现节点宕机需要恢复等等。

首先考虑一个问题，就是输入保存在哪，输出要写到什么地方。一般来讲，数据规模比较大的时候，一个节点无法保存下所有数据，就需要一个分布式的文件系统来保存。在 MapReduce 的场景下，输入是保存在分布式的文件系统上的若干个文件，输出也会写入到分布式的文件系统中。既然 MapReduce 是 Google 出品的，论文中分布式文件系统用的是 Google 自家的 GFS（Google File System）。GFS 的细节先不考虑，后面阅读 GFS 论文的时候再讨论，目前只需要知道是一个分布式的文件系统，现在常用的 Hadoop 使用的则是 HDFS 作为分布式文件系统。

输入文件在 GFS 准备好以后，首先需要有一个机制来分配 Map 任务给各个计算节点。论文采用的方法是在**一个节点**上运行 Master，由 Master 负责分配任务。论文的考虑是，MapReduce 任务一般执行时间不长，在这段时间内，具体某个节点宕机的概率很小，但是在上千个节点中，至少有一个节点宕机的概率不小。所以它只用了一个 Master 节点。在 Map 阶段，Master 向各个 Worker 分配任务（实际实现上可能是 Worker 向 Master RPC 获取任务），Worker 从 GFS 读取输入数据，调用用户编写的 Map 函数，把结果写到**本地存储**中。没有保存 GFS 的原因是，后续 Shuffle 阶段还需要把数据传输到 Reduce 的节点，如果保存到 GFS 中，就要先通过网络写一次到 GFS 中，再从 GFS 读一次，比较耗费带宽和时间。放在本地存储的话，直接把中间结果通过网络从执行 Map 的节点传输到执行 Reduce 的节点即可。这里有一个权衡：如果中间结果保存在 GFS 中，好处是如果计算中途宕机了，可以从 GFS 中恢复，继续计算没有算完的部分，坏处是耗费较多网络带宽和存储（GFS 会重复保存多份）；如果中间结果保存在本地存储中，好处是网络开销小，坏处是一旦宕机了，就要从头开始计算。在论文的场景中，网络是一个瓶颈，因此选择了后者。

得到中间文件以后，下一步需要进行 Shuffle，而 Shuffle 的目的是要进行 Reduce。为了方便 Shuffle，在保存中间结果的时候，就首先对中间结果进行划分，例如要划分为 `R` 份，每一份对应一个 Reduce 任务（注意 `R` 不等于执行 Reduce 操作的节点的个数），那就对 key 进行哈希操作：`hash(key) mod R`，把中间结果写到 R 个文件中。这样，Master 把 `R` 个 Reduce 任务分配给各个 Worker 节点，并且告诉这些 Worker 所有的 Map 临时结果保存的节点地址信息。Worker 就从各个 Map 节点的机器上读取中间结果，进行排序和合并，然后对每个 Key 调用一次用户的 Reduce 函数。最后结果写到 GFS 中，以 `R` 个文件的形式来保存，这样就完成了整个 MapReduce 过程。你可能觉得奇怪，为什么最后不把 `R` 个文件合并起来？因为一次 MapReduce 的结果可以成为下一次 MapReduce 的输入，既然 MapReduce 输入就是多个文件，那中间的 MapReduce 输出保持多个文件就好了。到最后不再需要进行 MapReduce 的时候，再合并输出。

### 故障恢复

如果运行过程中，Worker 宕机了，Master 可以通过 heartbeat 发现宕机的 Worker，然后把任务分配到其他正常运行的 Worker 中。如果 Master 宕机了，如果 Master 没有保存状态，很不幸，只能重新来过。论文没有怎么考虑这个情况，因为在这个场景下，Master 宕机概率很小。

还有一种“故障”，就是部分节点因为一些原因，它可以正常工作，但是执行任务特别慢。如果不处理的话，可能大部分任务都完成了，只有几个节点在慢吞吞地跑，其他节点都在等待。论文提出的办法是，如果整体任务快完成了，Master 可以给不同 Worker 同样的任务，这些 Worker 只要有一个跑出了结果即可，不需要等待最慢的那一个。其实就是拿更多的计算量换取更短的完成时间。

### 小结

MapReduce 论文提出了一个框架，以 Map 和 Reduce 操作的方式，使得很多应用可以简单地在集群上并行地完成计算，降低了集群使用的门槛。
