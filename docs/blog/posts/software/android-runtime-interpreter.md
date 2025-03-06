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

在分析解释器的代码前，需要先了解一下解释器的输入，也就是它执行的字节码格式是什么。Android Runtime 继承和发展了 [Dalvik VM 的字节码 Dalvik Bytecode](https://source.android.com/docs/core/runtime/dalvik-bytecode) 格式，因此在打包 Android 应用的时候，Java 代码最终会被翻译成 Dalvik Bytecode。

接下来来实践一下这个过程，从 Java 代码到 Dalvik Bytecode：

第一步是编写一个简单的 Java 程序如下，保存到 `MainActivity.java`：

```java
public class MainActivity {
    public static void main(String[] args) {
        System.out.println("Hello, world!");
    }

    public static int add(int a, int b) {
        return a + b;
    }
}
```

首先用 `javac MainActivity.java` 命令把源码编译到 Java Bytecode。可以用 `javap -c MainActivity.class` 查看生成的 Java Bytecode：

```log
Compiled from "MainActivity.java"
public class MainActivity {
  public MainActivity();
    Code:
       0: aload_0
       1: invokespecial #1                  // Method java/lang/Object."<init>":()V
       4: return

  public static void main(java.lang.String[]);
    Code:
       0: getstatic     #7                  // Field java/lang/System.out:Ljava/io/PrintStream;
       3: ldc           #13                 // String Hello, world!
       5: invokevirtual #15                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
       8: return

  public static int add(int, int);
    Code:
       0: iload_0
       1: iload_1
       2: iadd
       3: ireturn
}
```

Java Bytecode 是个典型的栈式字节码，因此从 `int add(int, int)` 函数可以看到，它分别压栈第零个和第一个局部遍变量（即参数 `a` 和 `b`），然后用 `iadd` 指令从栈顶弹出两个元素，求和后再把结果压栈。

接着，用 Android SDK 的 Build Tools 提供的命令 `d8` 来把它转换为 Dalvik Bytecode。如果你还没有安装 Android SDK，可以按照 [sdkmanager 文档](https://developer.android.com/tools/sdkmanager) 来安装 sdkmanager，再用 sdkmanager 安装较新版本的 `build-tools`。转换的命令为 `$ANDROID_HOME/build-tools/$VERSION/d8 MainActivity.class`，结果会保存在当前目录的 `classes.dex` 文件内。接着可以用 `$ANDROID_HOME/build-tools/$VERSION/dexdump -d classes.dex` 来查看 Dalvik Bytecode：

```log
Processing 'classes.dex'...
Opened 'classes.dex', DEX version '035'
Class #0            -
  Class descriptor  : 'LMainActivity;'
  Access flags      : 0x0001 (PUBLIC)
  Superclass        : 'Ljava/lang/Object;'
  Interfaces        -
  Static fields     -
  Instance fields   -
  Direct methods    -
    #0              : (in LMainActivity;)
      name          : '<init>'
      type          : '()V'
      access        : 0x10001 (PUBLIC CONSTRUCTOR)
      code          -
      registers     : 1
      ins           : 1
      outs          : 1
      insns size    : 4 16-bit code units
00016c:                                        |[00016c] MainActivity.<init>:()V
00017c: 7010 0400 0000                         |0000: invoke-direct {v0}, Ljava/lang/Object;.<init>:()V // method@0004
000182: 0e00                                   |0003: return-void
      catches       : (none)
      positions     :
        0x0000 line=1
      locals        :
        0x0000 - 0x0004 reg=0 this LMainActivity;

    #1              : (in LMainActivity;)
      name          : 'add'
      type          : '(II)I'
      access        : 0x0009 (PUBLIC STATIC)
      code          -
      registers     : 2
      ins           : 2
      outs          : 0
      insns size    : 2 16-bit code units
000158:                                        |[000158] MainActivity.add:(II)I
000168: b010                                   |0000: add-int/2addr v0, v1
00016a: 0f00                                   |0001: return v0
      catches       : (none)
      positions     :
        0x0000 line=7
      locals        :
        0x0000 - 0x0002 reg=0 (null) I
        0x0000 - 0x0002 reg=1 (null) I

    #2              : (in LMainActivity;)
      name          : 'main'
      type          : '([Ljava/lang/String;)V'
      access        : 0x0009 (PUBLIC STATIC)
      code          -
      registers     : 2
      ins           : 1
      outs          : 2
      insns size    : 8 16-bit code units
000184:                                        |[000184] MainActivity.main:([Ljava/lang/String;)V
000194: 6201 0000                              |0000: sget-object v1, Ljava/lang/System;.out:Ljava/io/PrintStream; // field@0000
000198: 1a00 0100                              |0002: const-string v0, "Hello, world!" // string@0001
00019c: 6e20 0300 0100                         |0004: invoke-virtual {v1, v0}, Ljava/io/PrintStream;.println:(Ljava/lang/String;)V // method@0003
0001a2: 0e00                                   |0007: return-void
      catches       : (none)
      positions     :
        0x0000 line=3
        0x0007 line=4
      locals        :
        0x0000 - 0x0008 reg=1 (null) [Ljava/lang/String;

  Virtual methods   -
  source_file_idx   : 9 (MainActivity.java)
```

对比 Java Bytecode，在 Dalvik Bytecode 里的 `add` 函数的实现就大不相同了：

1. `add-int/2addr v0, v1`: 求寄存器 `v1` 和寄存器 `v0` 之和，在这里就对应 `a` 和 `b` 两个参数，结果写到 `v0` 寄存器当中
2. `return v0`: 以寄存器 `v0` 为返回值，结束当前函数

可见 Dalvik Bytecode 采用的是类似 V8 的基于寄存器的字节码，不过没有 V8 的 `accumulator`。

Dalvik Bytecode 的完整列表见 [Dalvik bytecode format](https://source.android.com/docs/core/runtime/dalvik-bytecode)，它的格式基本上是两个字节为一组，每组里第一个字节代表 Op 类型，第二个字节代表参数，有一些 Op 后面还会带有多组参数。

例如上面的 `add-int/2addr vA, vB` 指令的编码是：

1. 第一个字节是 `0xb0`，表示这是一个 `add-int/2addr` Op
2. 第二个字节共 8 位，低 4 位编码了 `vA` 的寄存器编号 `A`，高 4 位编码了 `vB` 的寄存器编号 `B`

所以 `add-int/2addr v0, v1` 的编码就是 `0xb0, 0 | (1 << 4)` 即 `0xb0, 0x10`。因为存得很紧凑，寄存器编号只有 4 位，所以这个 Op 的操作数不能访问 v16 或更高的寄存器。

`return vAA` 指令的编码类似，不过因为只需要编码一个操作数，所以有 8 位可以编码返回值用哪个寄存器；为了区分是 4 位的编码还是 8 位的编码，这里用 `vAA` 表示可以用 8 位来记录寄存器编号。`return vAA` 的第一个字节是 `0x0f` 表示 Op 类型，第二个字节就是寄存器编号 `A`。上面出现的 `return v0` 的编码就是 `0x0f, 0x00`。

一些比较复杂的 Op 会附带更多的参数，此时编码就可能涉及到更多的字节。比如 `invoke-virtual {vC, vD, vE, vF, vG}, meth@BBBB`，可以携带可变个寄存器参数，在编码的时候，格式如下：

1. 第一个字节 `0x6e` 表示这是一个 `invoke-virtual` Op
2. 第二个字节的高 4 位记录了参数个数
3. 第三和第四个字节共 16 位，记录了要调用的函数的 index，这个 index 会被拿来索引 DEX 的 method_ids 表
4. 第五和第六个字节共 16 位，配合第二个字节的低 4 位，最多可以传递 5 个寄存器参数，每个寄存器参数 4 位

因此在上面的代码中，`invoke-virtual {v1, v0}, Ljava/io/PrintStream;.println:(Ljava/lang/String;)V // method@0003` 被编码为：`0x6e, 0x20, 0x03, 0x00, 0x01, 0x00`。另外构造了一个例子，把五个参数都用上：`invoke-virtual {v1, v4, v0, v2, v3}, LMainActivity;.add4:(IIII)I // method@0002` 被编码为 `0x6e, 0x53, 0x02, 0x00, 0x41, 0x20`，可以看到五个参数的编码顺序是第五个字节的低 4 位（`v1`）和高 4 位（`v4`），第六个字节的低 4 位（`v0`）和高 4 位（`v2`），最后是第二个字节的低 4 位（`v3`）。

了解了 Dalvik Bytecode 的结构，接下来观察它是怎么被解释执行的。

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
