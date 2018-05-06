---
layout: post
date: 2018-04-17 13:08:00 +0800
tags: [macos,gdb,homebrew]
category: programming
title: 把 GDB 降级到 8.0.1
---

在 macOS 上使用 GDB 需要 codesigning 。但是在 GDB 升级到 8.1 后这种方法不知道为何失效了。所以我安装回了 GDB 8.0.1 并且重新 codesigning ，现在又可以正常升级了。

对 Formula 进行 patch：

```patch
diff --git a/Formula/gdb.rb b/Formula/gdb.rb
index 29a1c590..25360893 100644
--- a/Formula/gdb.rb
+++ b/Formula/gdb.rb
@@ -1,14 +1,15 @@
 class Gdb < Formula
   desc "GNU debugger"
   homepage "https://www.gnu.org/software/gdb/"
-  url "https://ftp.gnu.org/gnu/gdb/gdb-8.1.tar.xz"
-  mirror "https://ftpmirror.gnu.org/gdb/gdb-8.1.tar.xz"
-  sha256 "af61a0263858e69c5dce51eab26662ff3d2ad9aa68da9583e8143b5426be4b34"
+  url "https://ftp.gnu.org/gnu/gdb/gdb-8.0.1.tar.xz"
+  mirror "https://ftpmirror.gnu.org/gdb/gdb-8.0.1.tar.xz"
+  sha256 "3dbd5f93e36ba2815ad0efab030dcd0c7b211d7b353a40a53f4c02d7d56295e3"
 
   bottle do
-    sha256 "43a6d6cca157ef70d13848f35c04e11d832dc0c96f5bcf53a43330f524b3ac40" => :high_sierra
-    sha256 "fe7c6261f9164e7a744c9c512ba7e5afff0e74e373ece9b5aa19d5da6443bfc2" => :sierra
-    sha256 "cd89001bcf8c93b5d6425ab91a400aeffe0cd5bbb0eccd8ab38c719ab5ca34ba" => :el_capitan
+    sha256 "e98ad847402592bd48a9b1468fefb2fac32aff1fa19c2681c3cea7fb457baaa0" => :high_sierra
+    sha256 "0fdd20562170c520cfb16e63d902c13a01ec468cb39a85851412e7515b6241e9" => :sierra
+    sha256 "f51136c70cff44167dfb8c76b679292d911bd134c2de3fef40777da5f1f308a0" => :el_capitan
+    sha256 "2b32a51703f6e254572c55575f08f1e0c7bc2f4e96778cb1fa6582eddfb1d113" => :yosemite
   end
 
   deprecated_option "with-brewed-python" => "with-python@2"
```
