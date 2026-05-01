---
layout: post
date: 2024-11-24
tags: [benchmark,spec]
categories:
    - software
---

# SPEC CPU 2017 在其他指令集上的编译

SPEC CPU 2017 官方只附带了 arm/ppc/sparc/riscv/x86 指令集的预编译 tools，如果要在其他指令集上使用，就需要首先编译 tools，过程如下：

```shell
# https://gist.github.com/cyyself/4cee148ad11081dde7b938e3584b4536
wget -O config.guess 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD'
wget -O config.sub 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD'
cp config.* /mnt/tools/src/expat-2.1.0/conftools/
cp config.* /mnt/tools/src/make-4.2.1/config/
cp config.* /mnt/tools/src/rxp-1.5.0/
cp config.* /mnt/tools/src/specinvoke/
cp config.* /mnt/tools/src/specsum/build-aux/
cp config.* /mnt/tools/src/tar-1.28/build-aux/
cp config.* /mnt/tools/src/xz-5.2.2/build-aux/
# fix glob impl
# https://github.com/GQBBBB/GQBBBB.github.io/issues/10
# http://git.savannah.gnu.org/cgit/make.git/patch/?id=48c8a116a914a325a0497721f5d8b58d5bba34d4
sed -i 's/_GNU_GLOB_INTERFACE_VERSION ==/_GNU_GLOB_INTERFACE_VERSION >=/' /mnt/tools/src/make-4.2.1/glob/glob.c
# fix missing test_driver.pl
# https://bugs.gentoo.org/613772
# http://git.savannah.gnu.org/cgit/make.git/commit/tests/run_make_tests.pl?id=d9d4e06084a4c7da480bd49a3487aadf6ba77b54
sed -i 's/require "test_driver.pl";/use FindBin;\nuse lib "$FindBin::Bin";\n\0/' /mnt/tools/src/make-4.2.1/tests/run_make_tests.pl
# fix wildcard test sigsegv
# https://lore.kernel.org/all/20200122223655.2569-1-sno@netbsd.org/T/
# http://git.savannah.gnu.org/cgit/make.git/commit/?id=193f1e81edd6b1b56b0eb0ff8aa4b41c7b4257b4
sed -i 's/gl->gl_stat = local_stat;/gl->gl_lstat = lstat;\n\0/' /mnt/tools/src/make-4.2.1/dir.c
# missing include ctype.h for isxdigit
sed -i 's/#include "xfreopen.h"/#include <ctype.h>\n\0/' /mnt/tools/src/specsum/src/md5sum.c
# fix gcc version detection
sed -i 's/1\*)/1.\*)/g' /mnt/tools/src/perl-5.24.0/Configure
# fix gettime test
sed -i 's/timegm(0,0,0,1,0,70)/timegm(0,0,0,1,0,1970)/g' /mnt/tools/src/TimeDate-2.30/t/getdate.t
# fix re.o generated instead of re.so
sed -i 's/main/int main/g' /mnt/tools/src/perl-5.24.0/hints/linux.sh
# GCC 15 default C23 fixes:
# 1. missing __alignof_is_defined && alignof macro
sed -i 's/#include <stdalign.h>/#define __alignof_is_defined 1\n#define alignof _Alignof\n\0/' /mnt/tools/src/specsum/tests/test-stdalign.c
# 2. hack stdbool.h detection
sed -i 's/#ifdef HAVE_STDBOOL_H/#if 1/' /mnt/tools/src/specinvoke/specinvoke.h
# 3. fix conflicting types for cleanup_os
sed -i 's/cleanup_os();/cleanup_os(specinvoke_state_t *si);/' /mnt/tools/src/specinvoke/specinvoke.h
# 4. fix char ** incompatible conversion to char*
sed -i 's/safesysrealloc(environ,/safesysrealloc((char*)environ,/' /mnt/tools/src/perl-5.24.0/util.c
sed -i 's/safesysfree(environ);/safesysfree((char*)environ);/' /mnt/tools/src/perl-5.24.0/perl.c
# 5. fix SDBM_FILE* incompatible conversion to char *
sed -i 's/safefree(db)/safefree((char*)db)/' /mnt/tools/src/perl-5.24.0/ext/SDBM_File/SDBM_File.xs
# 6. fix conflicting types for malloc/free
sed -i 's/extern Malloc_t malloc/extern void *malloc/' /mnt/tools/src/perl-5.24.0/ext/SDBM_File/sdbm.c
sed -i 's/extern Free_t free proto((Malloc_t))/extern void free proto((void *))/' /mnt/tools/src/perl-5.24.0/ext/SDBM_File/sdbm.c
# build tools
cd /mnt && echo 'y' | SKIPTOOLSINTRO=1 FORCE_UNSAFE_CONFIGURE=1 MAKEFLAGS=-j16 ./tools/src/buildtools
```

例如在 LoongArch 上编译 SPEC CPU 2017 的 Dockerfile，假设 SPEC CPU 2017 已经解压到 `/mnt`：

```dockerfile
RUN cd /mnt && tar xvf install_archives/tools-src.tar
RUN wget -O config.guess 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD'
RUN wget -O config.sub 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD'
RUN cp config.* /mnt/tools/src/expat-2.1.0/conftools/
RUN cp config.* /mnt/tools/src/make-4.2.1/config/
RUN cp config.* /mnt/tools/src/rxp-1.5.0/
RUN cp config.* /mnt/tools/src/specinvoke/
RUN cp config.* /mnt/tools/src/specsum/build-aux/
RUN cp config.* /mnt/tools/src/tar-1.28/build-aux/
RUN cp config.* /mnt/tools/src/xz-5.2.2/build-aux/
# https://gist.github.com/cyyself/4cee148ad11081dde7b938e3584b4536
# fix glob impl
# https://github.com/GQBBBB/GQBBBB.github.io/issues/10
# http://git.savannah.gnu.org/cgit/make.git/patch/?id=48c8a116a914a325a0497721f5d8b58d5bba34d4
RUN sed -i 's/_GNU_GLOB_INTERFACE_VERSION ==/_GNU_GLOB_INTERFACE_VERSION >=/' /mnt/tools/src/make-4.2.1/glob/glob.c
# fix missing test_driver.pl
# https://bugs.gentoo.org/613772
# http://git.savannah.gnu.org/cgit/make.git/commit/tests/run_make_tests.pl?id=d9d4e06084a4c7da480bd49a3487aadf6ba77b54
RUN sed -i 's/require "test_driver.pl";/use FindBin;\nuse lib "$FindBin::Bin";\n\0/' /mnt/tools/src/make-4.2.1/tests/run_make_tests.pl
# fix wildcard test sigsegv
# https://lore.kernel.org/all/20200122223655.2569-1-sno@netbsd.org/T/
# http://git.savannah.gnu.org/cgit/make.git/commit/?id=193f1e81edd6b1b56b0eb0ff8aa4b41c7b4257b4
RUN sed -i 's/gl->gl_stat = local_stat;/gl->gl_lstat = lstat;\n\0/' /mnt/tools/src/make-4.2.1/dir.c
# missing include ctype.h for isxdigit
RUN sed -i 's/#include "xfreopen.h"/#include <ctype.h>\n\0/' /mnt/tools/src/specsum/src/md5sum.c
# fix gcc version detection
RUN sed -i 's/1\*)/1.\*)/g' /mnt/tools/src/perl-5.24.0/Configure
# fix gettime test
RUN sed -i 's/timegm(0,0,0,1,0,70)/timegm(0,0,0,1,0,1970)/g' /mnt/tools/src/TimeDate-2.30/t/getdate.t
# fix re.o generated instead of re.so
RUN sed -i 's/main/int main/g' /mnt/tools/src/perl-5.24.0/hints/linux.sh
# GCC 15 default C23 fixes:
# 1. missing __alignof_is_defined && alignof macro
RUN sed -i 's/#include <stdalign.h>/#define __alignof_is_defined 1\n#define alignof _Alignof\n\0/' /mnt/tools/src/specsum/tests/test-stdalign.c
# 2. hack stdbool.h detection
RUN sed -i 's/#ifdef HAVE_STDBOOL_H/#if 1/' /mnt/tools/src/specinvoke/specinvoke.h
# 3. fix conflicting types for cleanup_os
RUN sed -i 's/cleanup_os();/cleanup_os(specinvoke_state_t *si);/' /mnt/tools/src/specinvoke/specinvoke.h
# 4. fix char ** incompatible conversion to char*
RUN sed -i 's/safesysrealloc(environ,/safesysrealloc((char*)environ,/' /mnt/tools/src/perl-5.24.0/util.c
RUN sed -i 's/safesysfree(environ);/safesysfree((char*)environ);/' /mnt/tools/src/perl-5.24.0/perl.c
# 5. fix SDBM_FILE* incompatible conversion to char *
RUN sed -i 's/safefree(db)/safefree((char*)db)/' /mnt/tools/src/perl-5.24.0/ext/SDBM_File/SDBM_File.xs
# 6. fix conflicting types for malloc/free
RUN sed -i 's/extern Malloc_t malloc/extern void *malloc/' /mnt/tools/src/perl-5.24.0/ext/SDBM_File/sdbm.c
RUN sed -i 's/extern Free_t free proto((Malloc_t))/extern void free proto((void *))/' /mnt/tools/src/perl-5.24.0/ext/SDBM_File/sdbm.c
# build tools
RUN cd /mnt && echo 'y' | SKIPTOOLSINTRO=1 FORCE_UNSAFE_CONFIGURE=1 MAKEFLAGS=-j16 ./tools/src/buildtools
RUN mkdir -p /mnt/config
RUN cd /mnt && . ./shrc && packagetools linux-loong64
RUN /mnt/install.sh -f
```

参考官方文档：[Building the SPEC CPU®2017 Toolset](https://www.spec.org/cpu2017/Docs/tools-build.html)。
