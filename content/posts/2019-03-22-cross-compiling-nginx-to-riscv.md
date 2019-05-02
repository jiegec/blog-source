---
layout: post
date: 2019-03-22 23:18:00 +0800
tags: [rcore,riscv,crosscompiling,musl]
category: software
title: 交叉编译 Nginx 1.14.2 到 RISC-V
---

最近又把一定的精力放到了 RISC-V 64 上的 rCore 用户态程序的支持上，同时也借到了 HiFive Unleashed 板子，所以有真实硬件可以拿来跑了。在这之前先在 QEMU 上把能跑的都跑起来。

由于 rCore 对 glibc 的支持一直有问题，RISC-V 也不例外，所以还是选择用 musl 来做这件事情。一般搜索，终于找到了 Linux 下能用的 [musl-riscv-toolchain](<https://github.com/rv8-io/musl-riscv-toolchain>) 。编译好工具链以后，很多需要 libc 的用户态都能跑了，于是想着试一下 nginx 的编译。试着编译了一下，遇到了各种问题，最后搜到了[交叉编译Hi3536上面使用的nginx](<https://www.jianshu.com/p/5d9b60f7b262>)，里面的方法解决了这个问题。最后总结出了这样的 patch :

```diff
diff --git a/nginx-1.14.2/auto/cc/name b/nginx-1.14.2/auto/cc/name
index ded93f5..d6ab27a 100644
--- a/nginx-1.14.2/auto/cc/name
+++ b/nginx-1.14.2/auto/cc/name
@@ -7,7 +7,7 @@ if [ "$NGX_PLATFORM" != win32 ]; then
 
     ngx_feature="C compiler"
     ngx_feature_name=
-    ngx_feature_run=yes
+    ngx_feature_run=no
     ngx_feature_incs=
     ngx_feature_path=
     ngx_feature_libs=
diff --git a/nginx-1.14.2/auto/lib/openssl/make b/nginx-1.14.2/auto/lib/openssl/make
index 126a238..7a0e768 100644
--- a/nginx-1.14.2/auto/lib/openssl/make
+++ b/nginx-1.14.2/auto/lib/openssl/make
@@ -51,7 +51,7 @@ END
 $OPENSSL/.openssl/include/openssl/ssl.h:	$NGX_MAKEFILE
 	cd $OPENSSL \\
 	&& if [ -f Makefile ]; then \$(MAKE) clean; fi \\
-	&& ./config --prefix=$ngx_prefix no-shared no-threads $OPENSSL_OPT \\
+	&& ./config --prefix=$ngx_prefix no-shared no-threads --cross-compile-prefix=riscv64-linux-musl- $OPENSSL_OPT \\
 	&& \$(MAKE) \\
 	&& \$(MAKE) install_sw LIBDIR=lib
 
diff --git a/nginx-1.14.2/auto/types/sizeof b/nginx-1.14.2/auto/types/sizeof
index 480d8cf..52c7287 100644
--- a/nginx-1.14.2/auto/types/sizeof
+++ b/nginx-1.14.2/auto/types/sizeof
@@ -33,7 +33,7 @@ int main(void) {
 END
 
 
-ngx_test="$CC $CC_TEST_FLAGS $CC_AUX_FLAGS \
+ngx_test="gcc $CC_TEST_FLAGS $CC_AUX_FLAGS \
           -o $NGX_AUTOTEST $NGX_AUTOTEST.c $NGX_LD_OPT $ngx_feature_libs"
 
 eval "$ngx_test >> $NGX_AUTOCONF_ERR 2>&1"

```

接着，在 `./configure --with-cc=riscv64-linux-musl-gcc --with-cc-opt=-static --with-ld-opt=-static --without-pcre --without-http_rewrite_module --without-http_gzip_module --with-poll_module --without-http_upstream_zone_module` 之后，修改 `objs/ngx_auto_config.h`，加入：

```c
#ifndef NGX_SYS_NERR
#define NGX_SYS_NERR  132
#endif

#ifndef NGX_HAVE_SYSVSHM
#define NGX_HAVE_SYSVSHM 1
#endif
```

接着就可以正常编译了：

```bash
$ file objs/nginx
objs/nginx: ELF 64-bit LSB executable, UCB RISC-V, version 1 (SYSV), statically linked, with debug_info, not stripped
```

