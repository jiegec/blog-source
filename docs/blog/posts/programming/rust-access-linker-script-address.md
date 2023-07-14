---
layout: post
date: 2019-01-07
tags: [rust,ld,linker,ffi]
categories:
    - programming
---

# Rust 获取 Linker Script 中的地址

在 Linker Script 中可以记录下一个地址到一个变量中，大概这样：

```text
.text: {
	PROVIDE(__text_start = .);
    *(.text .text.* .gnu.linkonce.t*)
    PROVIDE(__text_end = .);
}
```

这里的 `PROVIDE()` 是可选的。这样，代码里就可以获取到 .text 段的地址了。在 C 中，直接 extern 一个同名的变量就可以了，但在 Rust 中，需要这样获取：

```rust
extern "C" {
    fn __text_start();
    fn __text_end();
}

// __text_start as usize
// __text_end as usize
```

这样就可以拿到地址了。