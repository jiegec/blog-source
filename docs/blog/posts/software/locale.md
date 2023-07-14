---
layout: post
date: 2021-09-02
tags: [locale,sort]
categories:
    - software
---

# Locale 影响排序的特殊副作用

## 背景

最近在答疑的时候，发现同一条命令在不同系统上行为不同，一开始以为是 bash 版本问题，排查后最后发现是 locale 的问题。一个例子如下：

```shell
$ cat poc.txt | tr '\\n' ' '
1 + - * / \ a b A B 一 二 测 试 α
$ LANG="" sort poc.txt | tr '\\n' ' '
* + - / 1 A B \ a b α 一 二 测 试
$ LANG="zh_CN.UTF-8" sort poc.txt | tr '\\n' ' '
* + - / \ 1 测 二 试 一 a A b B α
$ LANG="en_US.UTF-8" sort poc.txt | tr '\\n' ' '
* + - / \ 1 a A b B α 一 二 测 试
```

注意 \ 1 a A 的顺序，在不同的 locale 下结果不同。

网上也有关于这个问题的讨论：

1. https://unix.stackexchange.com/questions/75341/specify-the-sort-order-with-lc-collate-so-lowercase-is-before-uppercase
2. https://stackoverflow.com/questions/43448655/weird-behavior-of-bash-glob-regex-ranges