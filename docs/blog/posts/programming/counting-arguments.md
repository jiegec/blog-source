---
layout: post
date: 2023-04-14
tags: [c,printf,gcc,builtin]
categories:
    - programming
title: C/C++ 数参数个数的特别方法
---

## 背景

群友上个月提了一个未知来源问题：

实现一个你自己的 `printf(int, ...)` 函数，该函数包含可变参数。为简便期间，假设所有参数均为 int 类型。

1. 第一个参数是一个普通参数，不表示后续可变参数的数目
2. 在 printf 中逐个输出所有传入的整数值（可使用系统自带的 kprintf 实现输出）
3. 思考如何判定参数结束，是否有副作用

## va_args

我们知道，传统的处理可变参数的方法是 va_args，但是它无法知道传入了多少参数，而要像 POSIX printf 那样，解析 format 参数，然后一个一个去取。

所以问题的关键是，如何获取参数的个数？一个思路是宏，尝试用宏的魔法来计算出参数个数，这个方法可能是可以的，但是没有深究。另一个思路是利用 ABI 的特点，例如 i386 上参数是通过栈传递的，那或许可以在栈上找到所有的 int，但是问题是无法确认参数在哪里结束。

## __builtin_va_arg_pack_len

今天，另一位群友发了一个链接：<https://gcc.gnu.org/onlinedocs/gcc/Constructing-Calls.html#Constructing-Calls>，讲述了 GCC 中一些特别的 builtin 函数，用于函数调用相关的魔法，其中一段描述吸引了我的眼球：

	Built-in Function: int __builtin_va_arg_pack_len ()

	This built-in function returns the number of anonymous arguments of an
	inline function. It can be used only in inline functions that are always
	inlined, never compiled as a separate function, such as those using
	__attribute__ ((__always_inline__)) or __attribute__ ((__gnu_inline__))
	extern inline functions. For example following does link- or run-time
	checking of open arguments for optimized code:

这正好实现了前面提到的获取参数个数，实现思路也可以想到，就是编译器在 inline 的时候，顺便做了一次替换。也因此，这个函数必须被 inline，不能正常调用。有了这个思路以后，经过一番尝试，写入了下面的代码：

```c
#include <stdio.h>
#include <stdarg.h>

void my_printf_inner(int count, ...) {
    va_list args;
    va_start(args, count);

    for (int i = 0;i < count;i++) {
        printf("%d\n", va_arg(args, int));
    }
    va_end(args);
}

__attribute__ ((__always_inline__)) inline
void my_printf(int a, ...) {
    int count = __builtin_va_arg_pack_len();
    printf("%d\n", a);
    my_printf_inner(count, __builtin_va_arg_pack());
}

int main() {
    my_printf(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);
    return 0;
}
```

这个代码在 GCC 中可以正确地输出 1-10 的十个数字。我一开始尝试的时候，把循环也写到 `my_printf` 函数中，但是 GCC 的 inline 就罢工了，最后只好拆成两个函数，把不知道参数个数的问题，转化成知道参数的问题，剩下就好解决了。

最后生成的汇编如下：

```asm
main:
        push    rbp
        mov     rbp, rsp
        sub     rsp, 16
        mov     DWORD PTR [rbp-4], 1
        mov     DWORD PTR [rbp-8], 9
        mov     eax, DWORD PTR [rbp-4]
        mov     esi, eax
        mov     edi, OFFSET FLAT:.LC0
        mov     eax, 0
        call    printf
        mov     eax, DWORD PTR [rbp-8]
        push    10
        push    9
        push    8
        push    7
        mov     r9d, 6
        mov     r8d, 5
        mov     ecx, 4
        mov     edx, 3
        mov     esi, 2
        mov     edi, eax
        mov     eax, 0
        call    my_printf_inner
        add     rsp, 32
        nop
        mov     eax, 0
        leave
        ret
```

可以看到，它 inline 了 `my_printf` 的实现，先调用了第一个 `printf`，然后把剩下的参数个数 `9` 赋值给了 `edi`，剩下就是正常的传参了。

以上实验都在 Godbolt Compiler Explorer 中进行：<https://godbolt.org/z/KjYzETn5Y>。

继续挖掘，会发现在 libc 中出现了 __builtin_va_arg_pack_len 的身影，在 fcntl2.h 中：

```c
__errordecl (__open_too_many_args,
             "open can be called either with 2 or 3 arguments, not more");
__errordecl (__open_missing_mode,
             "open with O_CREAT or O_TMPFILE in second argument needs 3 arguments");

__fortify_function int
open (const char *__path, int __oflag, ...)
{
  if (__va_arg_pack_len () > 1)
    __open_too_many_args ();

  if (__builtin_constant_p (__oflag))
    {
      if (__OPEN_NEEDS_MODE (__oflag) && __va_arg_pack_len () < 1)
        {
          __open_missing_mode ();
          return __open_2 (__path, __oflag);
        }
      return __open_alias (__path, __oflag, __va_arg_pack ());
    }

  if (__va_arg_pack_len () < 1)
    return __open_2 (__path, __oflag);

  return __open_alias (__path, __oflag, __va_arg_pack ());
}
```

可以看到，它核心的思想就是根据 open 第三个参数的有无，调用相应的 `__open_2` 或者 `__open_alias` 函数，这样就不用再用 `va_args` 方法了，并且如果传入了过多的参数，可以直接在编译期指出错误。例子：

```c
#include <fcntl.h>

int main() {
    open("123", 0, 0, 0, 0);
    return 0;
}
```

报错：

```c
In file included from /usr/include/fcntl.h:301,
                 from <source>:2:
In function 'open',
    inlined from 'main' at <source>:5:5:
/usr/include/x86_64-linux-gnu/bits/fcntl2.h:44:5: error: call to '__open_too_many_args' declared with attribute error: open can be called either with 2 or 3 arguments, not more
   44 |     __open_too_many_args ();
      |     ^~~~~~~~~~~~~~~~~~~~~~~
ASM generation compiler returned: 1
In file included from /usr/include/fcntl.h:301,
                 from <source>:2:
In function 'open',
    inlined from 'main' at <source>:5:5:
/usr/include/x86_64-linux-gnu/bits/fcntl2.h:44:5: error: call to '__open_too_many_args' declared with attribute error: open can be called either with 2 or 3 arguments, not more
   44 |     __open_too_many_args ();
      |     ^~~~~~~~~~~~~~~~~~~~~~~
Execution build compiler returned: 1
```

Compiler Explorer:<https://godbolt.org/z/hebshz3P5>.

## 使用 C 宏

和 Claude 聊了一下，是否能够用 C 宏来实现，它的回答是：

```c
#define PRINTF(...) printf(__VA_ARGS__)
#define NARG(...)  (sizeof((int[]){__VA_ARGS__})/sizeof(int))

int printf(const char *format, ...) {
    va_list args;
    va_start(args, format);
    
    // Access the variable arguments using va_arg based on 
    // the number of arguments passed, obtained using NARG
    
    va_end(args);
}

// Usage:
PRINTF(1, 2, 3);     // Prints 1 2 3 
PRINTF(1, 2, 3, 4); // Prints 1 2 3 4
```

核心思路就是把参数列表放到数组里，然后让编译器去推断数组大小。沿着这个思路，实现出代码：

```c
#include <stdio.h>
#include <stdarg.h>

void my_printf_inner(int count, ...) {
    va_list args;
    va_start(args, count);

    for (int i = 0;i < count;i++) {
        printf("%d\n", va_arg(args, int));
    }
    va_end(args);
}

#define MY_PRINTF(...) do {int len=(sizeof((int[]){__VA_ARGS__})/sizeof(int)); my_printf_inner(len, __VA_ARGS__); } while(0);

int main() {
    MY_PRINTF(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);
    return 0;
}
```

也是可以工作的。Compiler Explorer 链接：<https://godbolt.org/z/TxKb3YEcf>。

## ChatGPT

尝试询问了一下 ChatGPT：<https://shareg.pt/IXUKjYK>，它可以写出额外传入 int 个数的版本，可以写出哨兵（传入 `-1` 表示结束）的版本，提示了 builtin 以后，再提示 inline 和 always_inline，最后让它拆分成两个函数，得到的代码距离正确结果已经比较接近，但还是有一些问题。

