---
layout: post
date: 2017-12-12
tags: [lsp, cpp, clang, compilation_database, cquery, clangd]
category: programming
---

之前时间，巨硬发布了 LSP（Language Server Protocol），目的是解决目前 IDE 和各语言的 m+n 问题。想法很好，不过直到最近，终于有我觉得可以用的工具出来了，并且已经代替了我在使用的其它的插件。

由于我最近主要就是做做程设作业，做做 OJ 这些，主要就是和 C++打交道。所以我当然就开始找一些比较成熟的 C++的 LSP server。有一个 Sourcegraph 维护的 [langserver.org](https://langserver.org/) ，上面有着目前的各个语言和编辑器/IDE 的支持情况，我刚才提到的 cquery 也会加入到这个列表里去。从这个列表里可以看到，我用的比较多的 Python 和 Haskell 都已经有不错的的 LSP server，我已经开始在本地体验 pyls 和 hie 了，感觉做得挺不错的。

回到 C++，我的主力编辑器是 Emacs，其次是 CLion，而 Emacs 上的[LSP 支持 lsp-mode](https://github.com/emacs-lsp/lsp-mode)也在快速发展，与之配合的[lsp-ui](https://github.com/emacs-lsp/lsp-ui) 也出现了很多很棒的功能。

下面开始编译并配置[cquery](https://github.com/jacobdufault/cquery)：

``` shell
git clone https://github.com/jacobdufault/cquery --recursive
cd cquery
./waf configure # to use system clang, append --use-system-clang
./waf build
```

然后配置 Emacs：

``` elisp
(use-package lsp-mode
  :ensure t
  :diminish
  lsp-mode
  :commands
  (lsp-mode)
  :config
  (lsp-define-stdio-client
   lsp-pyls
   "python"
   #'get-project-root
   '("/usr/local/bin/pyls")))

(use-package lsp-ui
  :commands
  lsp-ui-mode
  :init
  (add-hook 'lsp-mode-hook 'lsp-ui-mode))

(use-package cquery
  :load-path
  "path_to_cquery/emacs"
  :config
  (setq
     cquery-executable "path_to_cquery/build/app"
     cquery-resource-dir "path_to_cquery/clang_resource_dir"))
```

接下来，需要配置 基于 Clang 的 工具都需要的 Compilation Database。Sacrasm 对这个有一个非常完整的[总结](https://sarcasm.github.io/notes/dev/compilation-database.html) ，可以查看里面的方法。我这里推荐在 CMake 项目中用 CMake 自带的，加上[nickdiego/compiledb-generator](https://github.com/nickdiego/compiledb-generator) 应付基于Makefile/Autotools的项目。如果都不适用，就按照cquery的README写一个简单的.cquery文件即可，不需要Bear那种必须关闭SIP的方案。

然后就可以享受很多功能了！还是挺好用的。
