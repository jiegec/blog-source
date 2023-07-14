---
layout: post
date: 2020-09-13
tags: [rust,rust-analyzer,arm,arm64,aarch64]
categories:
    - programming
title: 在 arm64 上使用 rust-analyzer
---

远程到 arm64 的机器上进行开发，发现没有 rust-analyzer 的支持。研究了一下，发现在 rustup 里面可以找到，不过要配置一下：

```bash
> rustup toolchain add nightly
> rustup component add --toolchain nightly rust-analyzer-preview
```

这个时候，应该可以找到 `~/.rustup/toolchains/nightly-aarch64-unknown-linux-gnu/bin/rust-analyzer` 文件，接下来，配置 VSCode 插件即可：

```json
{
    "rust-analyzer.serverPath": "~/.rustup/toolchains/nightly-aarch64-unknown-linux-gnu/bin/rust-analyzer"
}
```

路径在 `~/.vscode-server/data/Machine/settings.json`。



参考：https://github.com/rust-analyzer/rust-analyzer/issues/5256