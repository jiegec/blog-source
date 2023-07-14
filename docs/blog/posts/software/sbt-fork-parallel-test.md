---
layout: post
date: 2020-04-13
tags: [sbt,scala,testing]
categories:
    - software
title: 在 sbt 中 fork 并且并行运行测试
---

## 问题

最近在 sbt 使用遇到一个问题，有两个测试，分别用 testOnly 测试的时候没有问题，如果同时测试就会出问题，应该是全局的状态上出现了冲突。一个自然的解决思路是 fork，但是 sbt 默认 fork 之后 test 是顺序执行的，这会很慢。所以搜索了一下，找到了 fork 并且并行测试的方法。

## 解决方法

解决方法在 sbt 文档中其实就有（[原文](https://www.scala-sbt.org/release/docs/Testing.html#Forking+testsl)）。简单来说就是：把每个 test 放到单独的 TestGroup 中，每个 TestGroup 分别用一个 forked JVM 去运行；然后让 sbt 的并行限制设高一些：

```scala
// move each test into a group and fork them to avoid race condition
import Tests._
def singleTests(tests: Seq[TestDefinition]) =
  tests map { test =>
    new Group(
      name = test.name,
      tests = Seq(test),
      SubProcess(ForkOptions()))
  }

Test / testGrouping := singleTests( (Test / definedTests).value )
// allow multiple concurrent tests
concurrentRestrictions in Global := Seq(Tags.limitAll(4))
```

这样就可以了。

