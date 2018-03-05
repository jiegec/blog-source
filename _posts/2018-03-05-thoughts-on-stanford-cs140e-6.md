---
layout: post
date: 2018-03-05 19:55:49 +0800
tags: [Rust,OS,Stanford,CS140e,FAT32,fuzz test]
category: programming
title: 近来做 Stanford CS140e 的一些进展和思考（6）
---

在[上一篇文章](/programming/2018/03/03/thoughts-on-stanford-cs140e-5/)之后，作者终于更新了测试的用例，我的程序终于可以成功跑过所有测试，也成功在树莓派跑起来。不过，我的代码中很多地方的错误处理比较偷懒，往往直接 `panic` ，显然并不友好。同时，我想到了使用 [cargo-fuzz](https://github.com/rust-fuzz/cargo-fuzz) 来进行自动化测试，果然，使用这个很快就修复了不少我没想到的会出错的地方，比如乘法溢出，目录项没有正确结束等等。目前还发现一个 `timeout` 的问题，研究发现大概是文件的 `cluster chain` 中出现了环，导致一直读取文件而没有停止。要解决这个问题，我目前想到的是 `Floyd` 的判圈算法，但还没上实现。等过几天，新的 `Assignment 3` 出了以后，再继续更新。希望作者少点跳票，多点勤奋，哈哈哈哈哈