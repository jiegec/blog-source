---
layout: post
date: 2018-02-04 22:28:23 +0800
tags: [rust,os,stanford,cs140e,kernel,gpio,hardware,rpi3,xmodem]
category: programming
title: 近来做 Stanford CS140e 的一些进展和思考
---

最近，受各路安利，剁手买下了 [这个淘宝商家的树莓派的套餐C](https://item.taobao.com/item.htm?id=537501616420) ，还买了许多 LED 灯泡、杜邦线和电阻，开始按照 [CS 140e](http://web.stanford.edu/class/cs140e/) 学习 Rust 并且用 Rust 编译写一个简易的操作系统。Assignment 0 的目标就是编写一个向 GPIO 16 连接的 LED 灯闪烁。首先当然就是愉快地按照教程下载 bootloader ，下载交叉编译工具链，顺带装一个 Raspbian 到机器上，随时可以当成一个低性能的 ARM/ARM64 （实际上，Raspbian 只用了armv7l，没有用 64bit）机器来用，以后如果配上 [@scateu](https://scateu.me) 团购的 Motorola Laptop Dock 的话就是一个几百块的笔记本了。把课程上的文件丢上去，可以看到绿色的活动指示灯闪烁，后面又把 CP2102 模块连上去，又能看到 Blink on, Blink off 的输出。然后按照要求，自己先码一段 C 语言，实现 blinky:

```c++
#define GPIO_BASE (0x3F000000 + 0x200000)

volatile unsigned *GPIO_FSEL1 = (volatile unsigned *)(GPIO_BASE + 0x04);
volatile unsigned *GPIO_SET0  = (volatile unsigned *)(GPIO_BASE + 0x1C);
volatile unsigned *GPIO_CLR0  = (volatile unsigned *)(GPIO_BASE + 0x28);

static void spin_sleep_us(unsigned int us) {
  for (unsigned int i = 0; i < us * 6; i++) {
    asm volatile("nop");
  }
}

static void spin_sleep_ms(unsigned int ms) {
  spin_sleep_us(ms * 1000);
}

int main(void) {
  // STEP 1: Set GPIO Pin 16 as output.
  *GPIO_FSEL1 = 0b001 << 18;
  // STEP 2: Continuously set and clear GPIO 16.
  while (1) {
    *GPIO_SET0 = 1 << 16;
    spin_sleep_ms(1000);
    *GPIO_CLR0 = 1 << 16;
    spin_sleep_ms(1000);
  }
}
```

其中大部分代码都已经给出了，自己要实现也只是查询一下 BCM2837 SoC 的 GPIO 文档，按照文档把该做的内存操作和位运算都写一下即可。最后发现，闪烁的频率特别慢，几秒钟才闪烁一次。毕竟是按照 CPU 的 clock speed 进行粗略的计时，而生成的代码也不是很高效，没有 inline。接着则是用 Rust 再实现一下上面这部分的代码：

```rust
#![feature(compiler_builtins_lib, lang_items, asm, pointer_methods)]
#![no_builtins]
#![no_std]

extern crate compiler_builtins;

pub mod lang_items;

const GPIO_BASE: usize = 0x3F000000 + 0x200000;

const GPIO_FSEL1: *mut u32 = (GPIO_BASE + 0x04) as *mut u32;
const GPIO_SET0: *mut u32 = (GPIO_BASE + 0x1C) as *mut u32;
const GPIO_CLR0: *mut u32 = (GPIO_BASE + 0x28) as *mut u32;

#[inline(never)]
fn spin_sleep_ms(ms: usize) {
    for _ in 0..(ms * 600) {
        unsafe { asm!("nop" :::: "volatile"); }
    }
}

#[no_mangle]
pub unsafe extern "C" fn kmain() {
    // STEP 1: Set GPIO Pin 16 as output.
    GPIO_FSEL1.write_volatile(1 << 18);
    // STEP 2: Continuously set and clear GPIO 16.
    loop {
        GPIO_SET0.write_volatile(1 << 16);
        spin_sleep_ms(1000);
        GPIO_CLR0.write_volatile(1 << 16);
        spin_sleep_ms(1000);
    }
}
```

这边和上面一样，很多东西都已经给出了，只是重新改写一下而已。不过，这边的实测结果则是，一秒钟会闪烁很多下，看了下汇编，生成的循环比较紧凑，所以也没有达到想要的效果，不过后面到我实现了 Timer 的读取之后，就很精准了。

接下来就是痛苦的学习 Rust 的过程，Assignment 1 上来就是解答关于 Rust 语言的一些问题，在过程中被 Rust 十分严格的 Lifetime 和 Borrow checker 弄得想死，好歹最后还是让测试都通过了。接下来就是真正地提供一些封装硬件接口的 API，然后利用这些 API 去实现更多功能，首先是利用栈上分配的空间模拟一个变长数组的 API：`stack-vec` ，然后是把底层的直接操作硬件的内存操作封装成类型安全的 `volatile` ，然后实现一个简单的支持断点续传的传文件的协议 `xmodem` ，又做了一个辅助电脑上使用 TTY+XMODEM 的小工具 `ttywrite` ，然后就开始撸硬件了：时钟 `timer` ，针对 GPIO pin 的类型安全的状态机 `GPIO` 。目前只实现到这里，然后做出了一个准确一秒闪烁的 blinky （令人惊讶的是，因为这里的 kernel 直接从文件头开始就是代码，最后的 binary 异常地小，而之前的代码从文件的偏移 0x8000 开始。目前看来，是因为之前的代码是整个文件加载到 0x0000 上，而代码默认了从  0x8000 开始，所以除了最开头的一个跳转指令，中间留了许多空余的空间。而这里的代码是直接被 bootloader 加载到了 0x80000 处并且跳转到这里执行，所以省去了许多空间）：

```rust
fn blinky() {
    let mut pin16 = Gpio::new(16);
    let mut pin_out16 = pin16.into_output();

    loop {
        pin_out16.set();
        spin_sleep_ms(1000);
        pin_out16.clear();
        spin_sleep_ms(1000);
    }
}

#[no_mangle]
pub extern "C" fn kmain() {
    // FIXME: Start the shell.
    blinky();
}
```

目前只做到这里。后面还有大把的坑要踩，难写的 Rust 还得继续啃下去。我的代码都以 diff 的形式放在了 [jiegec/cs140e](https://github.com/jiegec/cs140e) ，写得并不美观。接下来就是实现 `UART` 了，终于要实现串口通信了。

2018-01-06 更新： [下一篇文章已经更新](/programming/2018/02/06/thoughts-on-stanford-cs140e-2/) 。
