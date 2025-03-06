---
layout: post
date: 2025-03-06
tags: [linux,android,interpreter,runtime,art]
draft: true
categories:
    - software
---

# Android Runtime 解释器的实现探究

## 背景

在 [V8 Ignition 解释器的内部实现探究](./v8-ignition-internals.md) 中探究了 JavaScript 引擎 V8 的解释器的实现，接下来分析一下 Android Runtime (ART) 的解释器，其原理也是类似的。本博客在 ARM64 Ubuntu 24.04 平台上针对 [Android Runtime (ART) 15.0.0 r1](https://android.googlesource.com/platform/art/+/refs/tags/android-15.0.0_r1/runtime/interpreter/) 版本进行分析。

<!-- more -->

## Dalvik Bytecode

在分析解释器的代码前，需要先了解一下解释器的输入，也就是它执行的字节码格式是什么。Android Runtime 继承和发展了 [Dalvik VM 的字节码 Dalvik Bytecode](https://source.android.com/docs/core/runtime/dalvik-bytecode) 格式，因此在打包 Android 应用的时候，Java 代码会被翻译成 Dalvik Bytecode 而不是 JVM 的 Bytecode。

## 解释器

Android Runtime (ART) 的解释器放在 `runtime/interpreter` 目录下。如果进行一些[考古](https://stackoverflow.com/questions/22187630/what-does-mterp-mean)，可以看到这个解释器的实现是从更早的 Dalvik VM 来的。它有两种不同的解释器实现：

第一个解释器基于 switch-case 的 C++ 代码实现，其逐个遍历 Opcode，根据 Opcode 执行相应的操作，类似下面的代码：

```c
for (each opcode of current function) {
  switch (opcode) {
    case opcode_add:
      // implement add here
      break;
    // ... other opcode handlers
  }
}
```

第二个解释器以 [Token threading](https://en.wikipedia.org/wiki/Threaded_code#Token_threading) 的方式实现，每个 Opcode 对应一段代码。这段代码在完成 Opcode 的操作后，读取下一个 Opcode，再间接跳转到下一个 Opcode 对应的代码。其工作原理类似下面的代码，这里 [`goto *`](https://gcc.gnu.org/onlinedocs/gcc/Labels-as-Values.html) 是 GNU C 的扩展，意思是一个间接跳转，目的地址取决于 `handlers[next_opcode]` 的值，意思是根据下一个 opcode，找到对应的 handler，直接跳转过去：

```c
  // op handlers array
  handlers = {&op_add, &op_sub};

op_add:
  // implement add here
  goto *handlers[next_opcode];
```

实际实现的时候更进一步，用汇编实现各个 opcode handler，并把 handler 放在了 128 字节对齐的位置，保证每个 handler 不超过 128 个字节，从而把读取 `handlers` 数组再跳转的 `goto *` 改成了用乘法和加法计算出 handler 的地址再跳转（computed goto）：

```asm
handlers_begin:
op_add:
  .balign 128
  # implement add here
  jmp to (handlers_begin + 128 * next_opcode);

op_sub:
  .balign 128
  # implement add here
  jmp to (handlers_begin + 128 * next_opcode);
```

下面结合源码来分析这两种解释器的实现。

### 基于 switch-case 的解释器

### 基于 token threading 的解释器 mterp (nterp)

由于这些代码是用汇编写的，直接写会有很多重复的部分。为了避免重复的代码，目前的解释器 mterp (现在叫 nterp) 用 Python 脚本来生成最终的汇编代码。要生成它，也很简单：

```shell
cd runtime/interpreter/mterp
./gen_mterp.py mterp_arm64ng.S arm64ng/*.S
```

这个脚本是平台无关的，例如如果要生成 amd64 平台的汇编，只需要：

```shell
cd runtime/interpreter/mterp
./gen_mterp.py mterp_x86_64ng.S x86_64ng/*.S
```

这样就可以看到完整的汇编代码了，后续的分析都会基于这份汇编代码。

## 参考

- [What does mterp mean?](https://stackoverflow.com/questions/22187630/what-does-mterp-mean)
- [Android 11 新引入的 Dalvik 字节码解释器 Nterp](https://zhuanlan.zhihu.com/p/523692715)
