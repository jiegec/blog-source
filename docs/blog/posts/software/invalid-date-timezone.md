---
layout: post
date: 2022-07-26
tags: [linux,timezone,date,tzdata]
categories:
    - software
---

# invalid date 报错与时区的关系

## 背景

最近在验题的时候，@HarryChen 发现了一个现象：

```shell
$ date -d "1919-04-13"
date: invalid date ‘1919-04-13’
$ TZ=UTC date -d "1919-04-13"
Sun Apr 13 00:00:00 UTC 1919
```

也就是说，这个现象与时区有关，那么为啥 `1919-04-13` 是一个不合法的日期呢？

## 时区

实际上，对于某一个时区来说，有的时间是不存在的，最常见的就是夏令时。在 [Timezone DB](https://timezonedb.com/time-zones/Asia/Shanghai) 里可以看到，恰好在 1919 年 4 月 13 日发生了一次 UTC+8 到 UTC+9 的变化，因此零点变成了一点，就变成了不合法的日期。

这个数据，实际上保存在 tzdata 中，可以用 zdump 工具查看：

```shell
$ tzdata -v Asia/Shanghai
Asia/Shanghai  Fri Dec 13 20:45:52 1901 UTC = Sat Dec 14 04:45:52 1901 CST isdst=0
Asia/Shanghai  Sat Dec 14 20:45:52 1901 UTC = Sun Dec 15 04:45:52 1901 CST isdst=0
Asia/Shanghai  Sat Apr 12 15:59:59 1919 UTC = Sat Apr 12 23:59:59 1919 CST isdst=0
Asia/Shanghai  Sat Apr 12 16:00:00 1919 UTC = Sun Apr 13 01:00:00 1919 CDT isdst=1
Asia/Shanghai  Tue Sep 30 14:59:59 1919 UTC = Tue Sep 30 23:59:59 1919 CDT isdst=1
Asia/Shanghai  Tue Sep 30 15:00:00 1919 UTC = Tue Sep 30 23:00:00 1919 CST isdst=0
Asia/Shanghai  Fri May 31 15:59:59 1940 UTC = Fri May 31 23:59:59 1940 CST isdst=0
Asia/Shanghai  Fri May 31 16:00:00 1940 UTC = Sat Jun  1 01:00:00 1940 CDT isdst=1
Asia/Shanghai  Sat Oct 12 14:59:59 1940 UTC = Sat Oct 12 23:59:59 1940 CDT isdst=1
Asia/Shanghai  Sat Oct 12 15:00:00 1940 UTC = Sat Oct 12 23:00:00 1940 CST isdst=0
Asia/Shanghai  Fri Mar 14 15:59:59 1941 UTC = Fri Mar 14 23:59:59 1941 CST isdst=0
Asia/Shanghai  Fri Mar 14 16:00:00 1941 UTC = Sat Mar 15 01:00:00 1941 CDT isdst=1
Asia/Shanghai  Sat Nov  1 14:59:59 1941 UTC = Sat Nov  1 23:59:59 1941 CDT isdst=1
Asia/Shanghai  Sat Nov  1 15:00:00 1941 UTC = Sat Nov  1 23:00:00 1941 CST isdst=0
Asia/Shanghai  Fri Jan 30 15:59:59 1942 UTC = Fri Jan 30 23:59:59 1942 CST isdst=0
Asia/Shanghai  Fri Jan 30 16:00:00 1942 UTC = Sat Jan 31 01:00:00 1942 CDT isdst=1
Asia/Shanghai  Sat Sep  1 14:59:59 1945 UTC = Sat Sep  1 23:59:59 1945 CDT isdst=1
Asia/Shanghai  Sat Sep  1 15:00:00 1945 UTC = Sat Sep  1 23:00:00 1945 CST isdst=0
Asia/Shanghai  Tue May 14 15:59:59 1946 UTC = Tue May 14 23:59:59 1946 CST isdst=0
Asia/Shanghai  Tue May 14 16:00:00 1946 UTC = Wed May 15 01:00:00 1946 CDT isdst=1
Asia/Shanghai  Mon Sep 30 14:59:59 1946 UTC = Mon Sep 30 23:59:59 1946 CDT isdst=1
Asia/Shanghai  Mon Sep 30 15:00:00 1946 UTC = Mon Sep 30 23:00:00 1946 CST isdst=0
Asia/Shanghai  Mon Apr 14 15:59:59 1947 UTC = Mon Apr 14 23:59:59 1947 CST isdst=0
Asia/Shanghai  Mon Apr 14 16:00:00 1947 UTC = Tue Apr 15 01:00:00 1947 CDT isdst=1
Asia/Shanghai  Fri Oct 31 14:59:59 1947 UTC = Fri Oct 31 23:59:59 1947 CDT isdst=1
Asia/Shanghai  Fri Oct 31 15:00:00 1947 UTC = Fri Oct 31 23:00:00 1947 CST isdst=0
Asia/Shanghai  Fri Apr 30 15:59:59 1948 UTC = Fri Apr 30 23:59:59 1948 CST isdst=0
Asia/Shanghai  Fri Apr 30 16:00:00 1948 UTC = Sat May  1 01:00:00 1948 CDT isdst=1
Asia/Shanghai  Thu Sep 30 14:59:59 1948 UTC = Thu Sep 30 23:59:59 1948 CDT isdst=1
Asia/Shanghai  Thu Sep 30 15:00:00 1948 UTC = Thu Sep 30 23:00:00 1948 CST isdst=0
Asia/Shanghai  Sat Apr 30 15:59:59 1949 UTC = Sat Apr 30 23:59:59 1949 CST isdst=0
Asia/Shanghai  Sat Apr 30 16:00:00 1949 UTC = Sun May  1 01:00:00 1949 CDT isdst=1
Asia/Shanghai  Fri May 27 14:59:59 1949 UTC = Fri May 27 23:59:59 1949 CDT isdst=1
Asia/Shanghai  Fri May 27 15:00:00 1949 UTC = Fri May 27 23:00:00 1949 CST isdst=0
Asia/Shanghai  Sat May  3 17:59:59 1986 UTC = Sun May  4 01:59:59 1986 CST isdst=0
Asia/Shanghai  Sat May  3 18:00:00 1986 UTC = Sun May  4 03:00:00 1986 CDT isdst=1
Asia/Shanghai  Sat Sep 13 16:59:59 1986 UTC = Sun Sep 14 01:59:59 1986 CDT isdst=1
Asia/Shanghai  Sat Sep 13 17:00:00 1986 UTC = Sun Sep 14 01:00:00 1986 CST isdst=0
Asia/Shanghai  Sat Apr 11 17:59:59 1987 UTC = Sun Apr 12 01:59:59 1987 CST isdst=0
Asia/Shanghai  Sat Apr 11 18:00:00 1987 UTC = Sun Apr 12 03:00:00 1987 CDT isdst=1
Asia/Shanghai  Sat Sep 12 16:59:59 1987 UTC = Sun Sep 13 01:59:59 1987 CDT isdst=1
Asia/Shanghai  Sat Sep 12 17:00:00 1987 UTC = Sun Sep 13 01:00:00 1987 CST isdst=0
Asia/Shanghai  Sat Apr 16 17:59:59 1988 UTC = Sun Apr 17 01:59:59 1988 CST isdst=0
Asia/Shanghai  Sat Apr 16 18:00:00 1988 UTC = Sun Apr 17 03:00:00 1988 CDT isdst=1
Asia/Shanghai  Sat Sep 10 16:59:59 1988 UTC = Sun Sep 11 01:59:59 1988 CDT isdst=1
Asia/Shanghai  Sat Sep 10 17:00:00 1988 UTC = Sun Sep 11 01:00:00 1988 CST isdst=0
Asia/Shanghai  Sat Apr 15 17:59:59 1989 UTC = Sun Apr 16 01:59:59 1989 CST isdst=0
Asia/Shanghai  Sat Apr 15 18:00:00 1989 UTC = Sun Apr 16 03:00:00 1989 CDT isdst=1
Asia/Shanghai  Sat Sep 16 16:59:59 1989 UTC = Sun Sep 17 01:59:59 1989 CDT isdst=1
Asia/Shanghai  Sat Sep 16 17:00:00 1989 UTC = Sun Sep 17 01:00:00 1989 CST isdst=0
Asia/Shanghai  Sat Apr 14 17:59:59 1990 UTC = Sun Apr 15 01:59:59 1990 CST isdst=0
Asia/Shanghai  Sat Apr 14 18:00:00 1990 UTC = Sun Apr 15 03:00:00 1990 CDT isdst=1
Asia/Shanghai  Sat Sep 15 16:59:59 1990 UTC = Sun Sep 16 01:59:59 1990 CDT isdst=1
Asia/Shanghai  Sat Sep 15 17:00:00 1990 UTC = Sun Sep 16 01:00:00 1990 CST isdst=0
Asia/Shanghai  Sat Apr 13 17:59:59 1991 UTC = Sun Apr 14 01:59:59 1991 CST isdst=0
Asia/Shanghai  Sat Apr 13 18:00:00 1991 UTC = Sun Apr 14 03:00:00 1991 CDT isdst=1
Asia/Shanghai  Sat Sep 14 16:59:59 1991 UTC = Sun Sep 15 01:59:59 1991 CDT isdst=1
Asia/Shanghai  Sat Sep 14 17:00:00 1991 UTC = Sun Sep 15 01:00:00 1991 CST isdst=0
Asia/Shanghai  Mon Jan 18 03:14:07 2038 UTC = Mon Jan 18 11:14:07 2038 CST isdst=0
Asia/Shanghai  Tue Jan 19 03:14:07 2038 UTC = Tue Jan 19 11:14:07 2038 CST isdst=0
```

可以看到，它列出来了历史上 Asia/Shanghai 时区的变化历史。具体的历史，可以查看 [中国时区](https://zh.wikipedia.org/zh-cn/%E4%B8%AD%E5%9C%8B%E6%99%82%E5%8D%80)。

此外，历史上，从儒略历到格里高利历的演变过程，也出现了一段“不存在”的日期，如 [Setting October 14 ,1582 fails in java.sql.Date](https://stackoverflow.com/questions/35194544/setting-october-14-1582-fails-in-java-sql-date)。