---
layout: post
date: 2019-01-16
tags: [vscode,vim,vscodevim,chinese]
categories:
    - software
---

# 实现 VSCodeVim 中支持中文分词的单词移动

最近用 VS Code 写中文 LaTeX 比较多，但是编辑起来总是比较麻烦，不能用各种带 w 的 motion，不然整行都没了。于是 @xalanq 提出能不能拿一个 JS 的分词库，魔改一下 VSCode Vim 来得到同样效果？答案是可以的。

最后代码在 [jiegec/VSCodeVimChinese](https://github.com/jiegec/VSCodeVimChinese) 里，还没有合并到上游的打算。不定期根据上游发版本同步更新，在 Github Release 里发布 vsix 文件，目前版本为 v1.0.1。在 VS Code 里 `Extensions: Install from VSIX...` 即可安装。

经过对代码的研究，发现对 motion w 的处理都是通过 `getWordLeft` `getWordRight` 和 `getCurrentWordEnd` 完成的。于是我修改了这三个函数，根据原来的返回值把字符串喂给分词器，再返回的新的位置。一开始用的是 `nodejieba` ，但是因为需要用到 `node-gyp` 遇到了 Node 版本不兼容的问题，于是换了一个纯 Node 的实现 `node-segment` ，就完成了这个功能。

