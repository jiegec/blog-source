---
layout: post
date: 2019-11-17 14:40:00 +0800
tags: [rust,decaf,lsp,tokio]
category: programming
title: 实现一个简单的 Decaf LSP 
---

# 背景

编译原理课程在做 Decaf 的 PA ，之前做了一些比较简单的尝试，包括在线 Decaf、在线 TAC VM 等等，都是套一个前端，然后整个编译到 wasm 跑前端就可以了。如果要做 LSP 的话，工作量会稍微大一些，不过也更加实用。

然后有一天，助教 @equation314 写了 [decaf-vscode](https://github.com/equation314/decaf-vscode) 一个 VSCode 对 Decaf 的语法高亮插件，我就 Fork 了一份到 [jiegec/decaf-vscode](https://github.com/jiegec/decaf-vscode)，然后添加了 LSP 的支持，让它有了一些更高级的功能。

# 实现

LSP 服务端一般是一个命令行程序，通过 JSONRPC 进行消息通讯，然后就上午找有没有现成的框架。比较重要的是 [lsp-types](https://crates.io/crates/lsp-types) 和 [tower-lsp](https://crates.io/crates/tower-lsp) ，前者封装了 LSP 协议的各个结构体，后者提供了服务端的大概实现。不过由于后者做的不大全，所以我自己 fork 了一份添加了一些。

实际实现的时候，需要实现几个函数，分别相应客户端的请求，比如在 initialize 的时候告诉客户端我都实现了哪些东西，然后相应地提供各种信息，如 symbol，hover，folding，definition等等。为了实现简单，我要求客户端每次修改的时候都把完整的文件传过来，虽然不是很高效，但是很简单，目前也没有啥很长的 Decaf 程序嘛。

每次拿到 Decaf 程序之后，就按照 decaf-rs 的方法，Lex 然后 Parse ，然后遍历 AST ，分别把需要的各个信息都存下来，当客户端在请求的时候，直接返回即可。然后就会在 VSCode 中出现，比如实现了 document symbol ，在左边的 Outline 中就会出现相应的结构；实现了 hover ，当移动到一些地方的时候，客户端发出请求，服务端就把相应的 hover 信息返回给客户端。整个协议并不复杂，后面实际实现其实才是比较复杂的地方。

实现的功能中，symbols hovers ranges definition 都是在得到 AST 后一次遍历都计算好，然后返回，同时在遇到错误的时候，也通过 diagnostic 的形式把检查出来的错误汇报给用户。由于 VSCode 的良好支持，基本不需要写 TypeScript 代码。

至于代码补全，现在做的比较粗糙，仅仅补全了一些内置函数：Print ReadInteger 和 ReadLine 。还在考虑支持函数调用的补全，但是在补全的时候会出现语法错误，意味着需要保证在补全的时候我还能拿到之前正确的类型信息，需要一些工作量，现在还没有去做。

# 使用

我自己测试的方法就是两个窗口，一个是 [decaf-lsp](https://github.com/jiegec/decaf-lsp) ，首先克隆下来，然后 `cargo install --path . --force` 来安装到全局；另一个就是我 Fork 的 [decaf-vscode](https://github.com/jiegec/decaf-vscode) ，克隆下来，然后按 `F5` 进入 VSCode 的调试模式，它会打开一个新窗口，里面启用了 Decaf for VSCode 插件。这个时候看 Decaf 代码就可以看到上面提到的那些东西了。

# 总结

感觉 LSP 是一个比较好实现的 Protocol ，但 Protocol 承载的 Data 才是比较困难的东西。要实现一个完整的 completion 还需要很多东西，现在只能说是个 naive implementation 吧。

刚写完就发现 Neovim 发布了 [官方的 LSP client](https://github.com/neovim/nvim-lsp) 。