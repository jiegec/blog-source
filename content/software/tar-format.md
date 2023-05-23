---
layout: post
date: 2023-05-23 21:24:00 +0800
tags: [tar]
category: software
title: Tar 文件格式
---

# 背景

最近在解压 tar.gz 文件的时候，发现如果用 unar 解压，就会出现文件名截断到 100 个字节的问题，而如果用 gnu tar 解压，文件名就是正常的，因此深入研究了一下 Tar 的文件格式。实际上，这是因为早期 tar 格式设计的时候，就设定了路径最长 100 字节的限制，后来的扩展解决了这个问题，但是 unar 没能正确地识别扩展，导致解压路径出错。

# Tar 文件格式

Tar 的文件格式比较简单，就是一系列的 File Entry，最后是两个 512 字节的全 0，表示结束。每个 File Entry 由头部和数据组成，头部的格式是：

```c
/* tar Header Block, from POSIX 1003.1-1990.  */

/* POSIX header.  */

struct posix_header
{                              /* byte offset */
  char name[100];               /*   0 */
  char mode[8];                 /* 100 */
  char uid[8];                  /* 108 */
  char gid[8];                  /* 116 */
  char size[12];                /* 124 */
  char mtime[12];               /* 136 */
  char chksum[8];               /* 148 */
  char typeflag;                /* 156 */
  char linkname[100];           /* 157 */
  char magic[6];                /* 257 */
  char version[2];              /* 263 */
  char uname[32];               /* 265 */
  char gname[32];               /* 297 */
  char devmajor[8];             /* 329 */
  char devminor[8];             /* 337 */
  char prefix[155];             /* 345 */
                                /* 500 */
};
```

来源：[Basic Tar Format](https://www.gnu.org/software/tar/manual/html_node/Standard.html)

可以看到，就是一系列的 char 数组，里面的很多数字字段，例如 mode，uid 和 gid 等，都是用 ASCII 码写的。由于头部需要对齐到 512 字节，所以实际上后面还有 12 字节的 padding。

头部的 512 字节结束后，紧接着就是文件的内容，内容的大小在头部的 size 字段已经保存，把字符串当成 8 进制数转换，就可以得到文件长度。文件也要对齐到 512 字节，所以文件后面还有若干个 0 作为 padding。

总结一下，Tar 文件的格式就是：`[头部，数据]*结尾`。每一个部分都对齐到 512 字节。

# PAX 扩展

如果仔细观察，会发现上面的 `posix_header` 里面，`name` 字段只有 100 个字节，意味着如果文件路径特别长，那就放不下，只能截断了。为了解决这个问题，Tar 引入了 PAX 扩展。

具体来说，PAX 扩展以特殊的文件形式存在。例如要记录一个名字很长的文件 `'X'*101`，实际上 Tar 中记录了两个文件：

1. PaxHeader：特殊的 PAX 文件，不对应实际的文件
2. `'X'*100`：文件名被截断，其他不变

这个 PaxHeader 在解压的时候，不会生成实际的文件。它的内容是一些键值对，例如：

```
123 path=XXXXXXXXXXXXXXXXX...
```

格式是：`length key=value\n`，然后可以有多个这样的键值对。这样就可以解决 `posix_header` 里名字长度限制的问题：只要在 PaxHeader 文件里，保存一个 key 为 path，value 为实际名字的信息。那么 tar 在看到 PaxHeader 的时候，记录下来，再遇到下一个文件的时候，就知道要用 PaxHeader 中的 path，而不是保存在 `posix_header` 中的 `name[100]`。

类似地，PaxHeader 还可以存很多其他 `posix_header` 中没有的信息，例如 `atime`、`ctime` 和 `uid` 等等。完整列表可以参考 [Extended header keywords](https://www.ibm.com/docs/en/zos/2.4.0?topic=descriptions-pax-interchange-portable-archives#r4paxsh__pxchk)。
