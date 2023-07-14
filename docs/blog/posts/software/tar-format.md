---
layout: post
date: 2023-05-23 21:24:00 +0800
tags: [tar]
category: software
title: Tar 文件格式
---

本文的内容已经整合到[知识库](/kb/software/tar.html)中。

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

总结一下，Tar 文件的格式就是：`(头部，数据)*结尾`。每一个部分都对齐到 512 字节。

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

# Bard

Bard 讲解 Tar 格式：

A tar file is an archive file format that is used to store a collection of files in a single file. The tar format is a standard format on Unix-like operating systems and is also supported by many other operating systems.

A tar file consists of a series of blocks, each of which contains 512 bytes of data. Each block contains a header and a body. The header contains information about the file, such as the file name, the file size, and the file permissions. The body contains the actual contents of the file.

The tar format is a simple and efficient format for storing files. It is also a portable format, which means that tar files can be moved from one computer to another without any problems.

Here is a more detailed description of the tar file format:

* The header of a tar file is 512 bytes long. It contains the following information:
    * The name of the file
    * The size of the file
    * The permissions of the file
    * The modification time of the file
    * The owner of the file
    * The group of the file
* The body of a tar file contains the actual contents of the file. The body is padded to a multiple of 512 bytes.
* Tar files can be compressed using a variety of compression algorithms, such as gzip, bzip2, and xz.

Tar files are a versatile format that can be used for a variety of purposes. They are commonly used for backing up files, distributing software, and archiving files.

Here are some of the benefits of using tar files:

* Tar files are a standard format that is supported by many operating systems.
* Tar files are a portable format, which means that they can be moved from one computer to another without any problems.
* Tar files can be compressed using a variety of compression algorithms, which can significantly reduce the size of the archive.
* Tar files can be easily created and managed using the tar command-line tool.

If you need to store a collection of files in a single file, then a tar file is a good option to consider.

Bard 讲解 PAX 扩展：

The POSIX 1003.1-2001 (pax) format for tar archives supports file names longer than 256 characters by using a different format for storing file names and metadata than the traditional ustar format. In the pax format, file names are stored as null-terminated strings, which means that they can be any length up to the maximum file size supported by the underlying file system. The metadata for each file is also stored in a separate record, which allows for more flexibility in the types of metadata that can be stored.

To create a tar archive in the pax format, you can use the following command:

```
tar cf - --format=pax /path/to/files
```

To extract a tar archive in the pax format, you can use the following command:

```
tar xvf - --format=pax archive.tar
```

The pax format is a more flexible and powerful format than the ustar format, and it is recommended for use when creating or extracting tar archives that may contain file names longer than 256 characters.

Here are some additional details about the pax format:

* File names are stored as null-terminated strings, which means that they can be any length up to the maximum file size supported by the underlying file system.
* The metadata for each file is stored in a separate record, which allows for more flexibility in the types of metadata that can be stored.
* The pax format is supported by most modern tar implementations.

Here are some examples of file names that can be stored in the pax format:

* "This is a file name with more than 256 characters."
* "/path/to/a/file/with/a/long/name."
* "file.with.spaces.in.its.name"

The pax format is a good choice for storing file names that may be long, contain special characters, or be stored in a directory hierarchy with a long path.