---
layout: post
date: 2025-03-06
tags: [linux,android,interpreter,runtime,art]
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

第一个解释器基于 switch-case 的 C++ 代码实现，其逐个遍历 Op，根据 Op 的类型 Opcode 执行相应的操作，类似下面的代码：

```c
for (each op of current function) {
  switch (op.opcode) {
    case op_add:
      // implement add here
      break;
    // ... other opcode handlers
  }
}
```

第二个解释器以 [Token threading](https://en.wikipedia.org/wiki/Threaded_code#Token_threading) 的方式实现，每种 Op 对应一段代码。这段代码在完成 Op 的操作后，读取下一个 Op，再间接跳转到下一个 Op 对应的代码。其工作原理类似下面的代码，这里 [`goto *`](https://gcc.gnu.org/onlinedocs/gcc/Labels-as-Values.html) 是 GNU C 的扩展，对应间接跳转指令，其目的地址取决于 `handlers[next_opcode]` 的值，意思是根据下一个 op 的 Opcode，找到对应的 handler，直接跳转过去：

```c
  // op handlers array
  handlers = {&op_add, &op_sub};

op_add:
  // implement add here
  // read next opcode here
  goto *handlers[next_opcode];
```

实际实现的时候更进一步，用汇编实现各个 op handler，并把 handler 放在了 128 字节对齐的位置，保证每个 handler 不超过 128 个字节，从而把读取 `handlers` 数组再跳转的 `goto *` 改成了用乘法和加法计算出 handler 的地址再跳转（computed goto）：

```asm
handlers_begin:
op_add:
  .balign 128
  # implement add here
  # read next opcode here
  jmp to (handlers_begin + 128 * next_opcode);

op_sub:
  .balign 128
  # implement add here
  # read next opcode here
  jmp to (handlers_begin + 128 * next_opcode);
```

下面结合源码来具体分析这两种解释器的实现。

### 基于 switch-case 的解释器

目前 Android Runtime 包括一个基于 switch-case 的解释器，实现在 `runtime/interpreter/interpreter_switch_impl-inl.h` 文件当中，它的核心逻辑就是一个循环套 switch-case：

```c++
  while (true) {
    const Instruction* const inst = next;
    dex_pc = inst->GetDexPc(insns);
    shadow_frame.SetDexPC(dex_pc);
    TraceExecution(shadow_frame, inst, dex_pc);
    uint16_t inst_data = inst->Fetch16(0);
    bool exit = false;
    bool success;  // Moved outside to keep frames small under asan.
    if (InstructionHandler<transaction_active, Instruction::kInvalidFormat>(
            ctx, instrumentation, self, shadow_frame, dex_pc, inst, inst_data, next, exit).
            Preamble()) {
      DCHECK_EQ(self->IsExceptionPending(), inst->Opcode(inst_data) == Instruction::MOVE_EXCEPTION);
      switch (inst->Opcode(inst_data)) {
#define OPCODE_CASE(OPCODE, OPCODE_NAME, NAME, FORMAT, i, a, e, v)                                \
        case OPCODE: {                                                                            \
          next = inst->RelativeAt(Instruction::SizeInCodeUnits(Instruction::FORMAT));             \
          success = OP_##OPCODE_NAME<transaction_active>(                                         \
              ctx, instrumentation, self, shadow_frame, dex_pc, inst, inst_data, next, exit);     \
          if (success && LIKELY(!interpret_one_instruction)) {                                    \
            continue;                                                                             \
          }                                                                                       \
          break;                                                                                  \
        }
  DEX_INSTRUCTION_LIST(OPCODE_CASE)
#undef OPCODE_CASE
      }
    }
    // exit condition handling omitted
  }
```

代码中使用了 [X macro](https://en.wikipedia.org/wiki/X_macro) 的编程技巧：如果你需要在不同的地方重复出现同一个 list，比如在这里，就是所有可能的 Opcode 类型，你可以在一个头文件中用一个宏，以另一个宏为参数去列出来：

```c++
// V(opcode, instruction_code, name, format, index, flags, extended_flags, verifier_flags);
#define DEX_INSTRUCTION_LIST(V) \
  V(0x00, NOP, "nop", k10x, kIndexNone, kContinue, 0, kVerifyNothing) \
  V(0x01, MOVE, "move", k12x, kIndexNone, kContinue, 0, kVerifyRegA | kVerifyRegB) \
  // omitted
```

这个宏定义在 `libdexfile/dex/dex_instruction_list.h` 头文件当中。在使用的时候，临时定义一个宏，然后把新定义的宏传入 `DEX_INSTRUCTION_LIST` 的参数即可。例如要生成一个数组，记录所有的 op 名字，可以：

```cpp
// taken from libdexfile/dex/dex_instruction.cc
const char* const Instruction::kInstructionNames[] = {
#define INSTRUCTION_NAME(o, c, pname, f, i, a, e, v) pname,
#include "dex_instruction_list.h"
  DEX_INSTRUCTION_LIST(INSTRUCTION_NAME)
#undef DEX_INSTRUCTION_LIST
#undef INSTRUCTION_NAME
};
```

这段代码经过 C 预处理器，首先会被展开为：

```c
const char* const Instruction::kInstructionNames[] = {
#define INSTRUCTION_NAME(o, c, pname, f, i, a, e, v) pname,
  INSTRUCTION_NAME(0x00, NOP, "nop", k10x, kIndexNone, kContinue, 0, kVerifyNothing) \
  INSTRUCTION_NAME(0x01, MOVE, "move", k12x, kIndexNone, kContinue, 0, kVerifyRegA | kVerifyRegB) \
  // omitted
#undef INSTRUCTION_NAME
};
```

继续展开，就得到了想要留下的内容：

```c++
const char* const Instruction::kInstructionNames[] = {
  "nop",
  "move",
  // omitted
};
```

回到 switch-case 的地方，可以预见到，预处理会生成的代码大概是：

```cpp
switch (inst->Opcode(inst_data)) {
  case 0x00: {                                                                            \
    next = inst->RelativeAt(Instruction::SizeInCodeUnits(Instruction::k10x));             \
    success = OP_NOP<transaction_active>(                                                 \
        ctx, instrumentation, self, shadow_frame, dex_pc, inst, inst_data, next, exit);   \
    if (success && LIKELY(!interpret_one_instruction)) {                                  \
      continue;                                                                           \
    }                                                                                     \
    break;                                                                                \
  }
  // omitted
}
```

其中 `next = inst->RelativeAt(Instruction::SizeInCodeUnits(Instruction::k10x));` 语句根据当前 Op 类型计算出它会占用多少个字节，从而得到下一个 Op 的地址。之后就是调用 `OP_NOP` 函数来进行实际的操作了。当然了，这个实际的操作，还是需要开发者去手动实现（`OP_NOP` 函数会调用下面的 `NOP` 函数）：

```c++
HANDLER_ATTRIBUTES bool NOP() {
  return true;
}

HANDLER_ATTRIBUTES bool MOVE() {
  SetVReg(A(), GetVReg(B()));
  return true;
}

HANDLER_ATTRIBUTES bool ADD_INT() {
  SetVReg(A(), SafeAdd(GetVReg(B()), GetVReg(C())));
  return true;
}
```

### 基于 token threading 的解释器 mterp (nterp)

第二个解释器则是基于 token threading 的解释器，它的源码在 `runtime/interpreter/mterp` 目录下。由于这些代码是用汇编写的，直接写会有很多重复的部分。为了避免重复的代码，目前的解释器 mterp (现在叫 nterp) 用 Python 脚本来生成最终的汇编代码。要生成它，也很简单：

```shell
cd runtime/interpreter/mterp
./gen_mterp.py mterp_arm64ng.S arm64ng/*.S
```

这个脚本是平台无关的，例如如果要生成 amd64 平台的汇编，只需要：

```shell
cd runtime/interpreter/mterp
./gen_mterp.py mterp_x86_64ng.S x86_64ng/*.S
```

这样就可以看到完整的汇编代码了，后续的分析都会基于这份汇编代码。如果读者对 amd64 汇编比较熟悉，也可以在本地生成一份 amd64 的汇编再结合本文进行理解。

上面提到过 `add-int/2addr vA, vB` 这个做整数加法的 Op，直接在生成的汇编中，找到它对应的代码：

```asm
    .balign NTERP_HANDLER_SIZE
.L_op_add_int_2addr: /* 0xb0 */
    /* omitted */
    /* binop/2addr vA, vB */
    lsr     w3, wINST, #12              // w3<- B
    ubfx    w9, wINST, #8, #4           // w9<- A
    GET_VREG w1, w3                     // w1<- vB
    GET_VREG w0, w9                     // w0<- vA
    FETCH_ADVANCE_INST 1                // advance rPC, load rINST
    add     w0, w0, w1                  // w0<- op, w0-w3 changed
    GET_INST_OPCODE ip                  // extract opcode from rINST
    SET_VREG w0, w9                     // vAA<- w0
    GOTO_OPCODE ip                      // jump to next instruction
    /* omitted */
```

其中 `wINST` 表示当前 Op 的前两个字节的内容，前面提到，`add-int/2addr vA, vB` 编码为两个字节，第一个字节是固定的 `0xb0`，第二个字节共 8 位，低 4 位编码了 `vA` 的寄存器编号 `A`，高 4 位编码了 `vB` 的寄存器编号 `B`。由于这是小端序的处理器，那么解释为 16 位整数，从高位到低位依次是：4 位的 `B`，4 位的 `A` 和 8 位的 `0xb0`。知道这个背景以后，再来分析每条指令做的事情，就很清晰：

1. `lsr w3, wINST, #12`：求 `wINST` 右移动 12 位，得到了 `B`
2. `ubfx w9, wINST, #8, #4`: `ubfx` 是 Bit Extract 指令，这里的意思是从 `wINST` 第 8 位开始取 4 位数据出来，也就是 `A`
3. `GET_VREG w1, w3`: 读取寄存器编号为 `w3` 的值，写到 `w1` 当中，结合第一条指令，可知此时 `w1` 等于 `B` 寄存器的值
4. `GET_VREG w0, w9`: 读取寄存器编号为 `w9` 的值，写到 `w0` 当中，结合第二条指令，可知此时 `w0` 等于 `A` 寄存器的值
5. `FETCH_ADVANCE_INST 1`: 把 "PC" 往前移动 1 个单位的距离，也就是两个字节，并读取下一个 Op 到 `rINST` 当中
6. `add w0, w0, w1`: 进行实际的整数加法运算，结果保存在 `w0` 当中
7. `GET_INST_OPCODE ip`: 根据第五条指令读取的下一个 Op 的值 `rINST`，解析出它的 Opcode
8. `SET_VREG w0, w9`: 把整数加法的结果写回到寄存器编号为 `w9` 的寄存器当中，结合第二条指令，可知写入的是 `A` 寄存器
9. `GOTO_OPCODE ip`: 跳转到下一个 Op 对应的 handler

整体代码还是比较清晰的，只是说把计算 `A + B` 写入 `A` 的过程和读取下一个 Op 并跳转的逻辑穿插了起来，手动做了一次寄存器调度。那么这些 `GET_REG` 和 `FETCH_ADVANCE_INST` 等等具体又是怎么实现的呢？下面把宏展开后的代码贴出来：

```asm
    .balign NTERP_HANDLER_SIZE
.L_op_add_int_2addr: /* 0xb0 */
    /* omitted */
    /* binop/2addr vA, vB */

    // wINST is w23, the first 16-bit code unit of current instruction
    // lsr     w3, wINST, #12              // w3<- B
    lsr w3, w23, #12 
    // ubfx    w9, wINST, #8, #4           // w9<- A
    ubfx w9, w23, #8, #4 

    // virtual registers are stored relative to xFP(x29), the interpreted frame pointer, used for accessing locals and args
    // GET_VREG w1, w3                     // w1<- vB
    ldr w1, [x29, w3, uxtw #2] 
    // GET_VREG w0, w9                     // w0<- vA
    ldr w0, [x29, w9, uxtw #2] 

    // xPC(x22) is the interpreted program counter, used for fetching instructions
    // FETCH_ADVANCE_INST 1                // advance rPC, load rINST
    // a pre-index load instruction that both reads wINST from memory and increments xPC(x22) by 2
    ldrh w23, [x22, #2]!

    // add     w0, w0, w1                  // w0<- op, w0-w3 changed
    add w0, w0, w1 

    // ip(x16) is a scratch register, used to store the first byte (opcode) of wINST
    // GET_INST_OPCODE ip                  // extract opcode from rINST
    and x16, x23, 0xff

    // save addition result to virtual register, which is relative to xFP(x29)
    // also set its object references to zero, which is relative to xREFS(x25)
    // SET_VREG w0, w9                     // vAA<- w0
    str w0, [x29, w9, uxtw #2]
    str wzr, [x25, w9, uxtw #2]

    // now x16 saves the opcode, and xIBASE(x24) interpreted instruction base pointer, used for computed goto
    // for opcode #k, the handler address of it would be `xIBASE + k * 128`
    // GOTO_OPCODE ip                      // jump to next instruction
    add x16, x24, x16, lsl #7
    br x16
    /* omitted */
```

各个寄存器的含义已经在上面的注释中写出，比如 `w23` 记录了当前 Op 的前 16 位的内容，`x29` 记录了当前的 frame pointer，通过它可以访问各个 virtual register；`x11` 是 PC，记录了正在执行的 Op 的地址；`x24` 记录了这些 op handler 的起始地址，由于每个 handler 都不超过 128 字节，且都对齐到 128 字节边界（`.balign NTERP_HANDLER_SIZE`），所以只需要简单的运算 `xIBASE + opcode * 128` 即可找到下一个 op 的 handler 地址，不需要再进行一次访存。

如果要比较一下 Android Runtime 的 mterp (nterp) 和 [V8 的 Ignition 解释器](./v8-ignition-internals.md)的实现，有如下几点相同与不同：

1. 两者都采用了 token threading 的方法，即在一个 Op 处理完成以后，计算出下一个 Op 的 handler 的地址，跳转过去
2. V8 的 op handler 是动态生成的（`mksnapshot` 阶段），长度没有限制，允许生成比较复杂的汇编，但如果汇编比较短（比如 release 模式下），也可以节省一些内存；代价是需要一次额外的对 dispatch table 的访存，来找到 opcode 对应的 handler
3. mterp 的 op handler 对齐到 128B 边界，带来的好处是不需要访问 dispatch table，直接根据 opcode 计算地址即可，不过由于很多 handler 很短，可能只有十条指令左右，就会浪费了一些内存
4. V8 没有 handler 长度的限制，所以针对一些常见的 Op 做了优化（Short Star），可以减少一些跳转的开销
5. V8 在区分 Smi(Small integer) 和对象的时候，做法是在 LSB 上打标记：0 表示 Smi，1 表示对象；mterp 则不同，它给每个虚拟寄存器维护了两个 32 位的值：一个保存在 xFP 指向的数组当中，记录的是它的实际的值，比如 int 的值，或者对象的引用；另一个保存在 xREFS 指向的数组当中，记录的是它引用的对象，如果不是对象，则记录的是 0

除了以上列举的不同的地方以外，其实整体来看是十分类似的，下面是二者实现把整数加载到寄存器（`const/4 vA, #+B` 和 `LdaSmi`）的汇编的对比：


| Operation             | mterp (nterp)                                             | Ignition                                        |
|-----------------------|-----------------------------------------------------------|-------------------------------------------------|
| Extract Dest Register | `ubfx w0, w23, #8, #4`                                    | N/A (destination is always the accumulator)     |
| Extract Const Integer | `sbfx w1, w23, #12, #4`                                   | `add x1, x19, #1; ldrsb w1, [x20, x1]`          |
| Read Next Op          | `ldrh w23, [x22, #2]!`                                    | `add x19, x19, #2; ldrb w3, [x20, x19]`         |
| Save Result           | `str w1, [x29, w0, uxtw #2]; str wzr, [x25, w0, uxtw #2]` | `add w0, w1, w1`                                |
| Computed Goto         | `and x16, x23, 0xff; add x16, x24, x16, lsl #7; br x16`   | `ldr x2, [x21, x3, lsl #3]; mov x17, x2; br x2` |

在寄存器的约定和使用上的区别：

| Purpose          | mterp (nterp)          | Ignition                       |
|------------------|------------------------|--------------------------------|
| Intepreter PC    | base + offset in `x22` | base in `x20`, offset in `x19` |
| Virtual Register | relative to `x29`      | relative to `fp`               |
| Dispatch Table   | computed from `x24`    | saved in `x21`                 |

## Lua 解释器

既然已经分析了 [V8](./v8-ignition-internals.md) 和 Android Runtime 的解释器，也来简单看一下 [Lua](https://www.lua.org/) 的解释器实现。它写的非常简单，核心代码就在 `lvm.c` 当中：

```c
vmdispatch (GET_OPCODE(i)) {
  vmcase(OP_MOVE) {
    StkId ra = RA(i);
    setobjs2s(L, ra, RB(i));
    vmbreak;
  }
  vmcase(OP_LOADI) {
    StkId ra = RA(i);
    lua_Integer b = GETARG_sBx(i);
    setivalue(s2v(ra), b);
    vmbreak;
  }
  // ...
}
```

可以看到，它把 `switch`、`case` 和 `break` 替换成了三个宏 `vmdispatch`、`vmcase` 和 `vmbreak`。接下来看它可能的定义，第一种情况是编译器不支持 `goto *` 语法，此时就直接展开：

```c
#define vmdispatch(o)	switch(o)
#define vmcase(l)	case l:
#define vmbreak	break
```

如果编译器支持 `goto *` 语法，则展开成对应的 `computed goto` 形式：

```c
#define vmdispatch(x) goto *disptab[x];
#define vmcase(l) L_##l:
#define vmbreak	mfetch(); vmdispatch(GET_OPCODE(i));

static const void *const disptab[NUM_OPCODES] = {
  &&L_OP_MOVE,
  &&L_OP_LOADI,
  // ...
};
```

和之前写的解释器的不同实现方法对应，就不多阐述了。

## 参考

- [What does mterp mean?](https://stackoverflow.com/questions/22187630/what-does-mterp-mean)
- [Android 11 新引入的 Dalvik 字节码解释器 Nterp](https://zhuanlan.zhihu.com/p/523692715)
