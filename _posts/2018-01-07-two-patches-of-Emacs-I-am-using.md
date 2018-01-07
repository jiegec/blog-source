---
layout: post
date: 2018-01-07 14:24:24 +0800
tags: [emacs, patch, multicolor font, Emoji, frame, child frame]
category: programming
title: 我正在使用的两个 Emacs 的 Patch
---

我在本地对 `emacs.rb` 进行了修改：

```patch
diff --git a/Formula/emacs.rb b/Formula/emacs.rb
index d0138cd..de3c5ff 100644
--- a/Formula/emacs.rb
+++ b/Formula/emacs.rb
@@ -4,6 +4,14 @@ class Emacs < Formula
   url "https://ftp.gnu.org/gnu/emacs/emacs-25.3.tar.xz"
   sha256 "253ac5e7075e594549b83fd9ec116a9dc37294d415e2f21f8ee109829307c00b"

+  patch do
+    url "https://gist.githubusercontent.com/aatxe/260261daf70865fbf1749095de9172c5/raw/214b50c62450be1cbee9f11cecba846dd66c7d06/patch-multicolor-font.diff"
+  end
+
+  patch do
+    url "https://debbugs.gnu.org/cgi/bugreport.cgi?filename=0001-Fix-child-frame-placement-issues-bug-29953.patch;bug=29953;att=1;msg=8"
+  end
+
   bottle do
     sha256 "d5ce62eb55d64830264873a363a99f3de58c35c0bd1602cb7fd0bc37137b0c9d" => :high_sierra
     sha256 "4d7ff7f96c9812a9f58cd45796aef789a1b5d26c58e3e68ecf520fab34af524d" => :sierra

```

主要涉及到两个 Patch ：

1. 启用对 Multicolor font ，比如 Emoji 的支持。由于一些 ethic problems 暂时在 Emacs 中被禁用了，所以自己启用回来。
2. 打上我前几天上报的 [BUG #29953](https://debbugs.gnu.org/cgi/bugreport.cgi?bug=29953) 的修复。已经在上游 Merge 到 `emacs-26` 分支中，这个修复会在下一个版本中。

有了第一个，就可以正常显示 Emoji （对不起，RMS）；有了第二个，就解决了 `pyim` 和 `lsp-ui-peek` 用 `child-frame` 显示的一些问题了。

另外还有一个我自己在用的 `recoll.rb` ：
```patch
# Documentation: https://docs.brew.sh/Formula-Cookbook.html
#                http://www.rubydoc.info/github/Homebrew/brew/master/Formula
# PLEASE REMOVE ALL GENERATED COMMENTS BEFORE SUBMITTING YOUR PULL REQUEST!

class Recoll < Formula
  desc "Recoll is a desktop full-text search tool."
  homepage "https://www.lesbonscomptes.com/recoll/"
  url "https://www.lesbonscomptes.com/recoll/recoll-1.23.5.tar.gz"
  sha256 "9b6b6941efc3e87c8325e95a69a5d0a37c022c3c45773c71dccd0fb3f364475f"

  depends_on "xapian"
  depends_on "qt"
  depends_on "aspell"

  def install
    inreplace "Makefile.in",
      "-Wl,--no-undefined -Wl,--warn-unresolved-symbols", "--no-undefined --warn-unresolved-symbols"

    system "./configure", "--disable-dependency-tracking",
                          "--disable-silent-rules",
                          "--without-x",
                          "--disable-x11mon",
                          "--with-aspell",
                          "--enable-recollq",
                          "--disable-webkit", # requires qtwebkit, which is not bundled with qt5
                          "--prefix=#{prefix}"
    system "make", "install"

    mkdir libexec
    mv bin/"recoll.app", libexec/"recoll.app"
  end

  test do
    # `test do` will create, run in and delete a temporary directory.
    #
    # This test will fail and we won't accept that! For Homebrew/homebrew-core
    # this will need to be a test that verifies the functionality of the
    # software. Run the test with `brew test recoll`. Options passed
    # to `brew install` such as `--HEAD` also need to be provided to `brew test`.
    #
    # The installed folder is not in the path, so use the entire path to any
    # executables being tested: `system "#{bin}/program", "do", "something"`.
    system "false"
  end
end

```
