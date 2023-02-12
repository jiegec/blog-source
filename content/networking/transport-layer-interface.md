---
layout: post
date: 2023-02-12 20:52:00 +0800
tags: [solaris,tli,xti,sysv,unix]
category: networking
title: Transport Layer Interface 考古
---

## Transport Layer Interface

现在网络编程主要采用的是 BSD Sockets API，但实际上当年还有另一套 API，就是 TLI（Transport Layer Interface），后来 BSD Sockets 胜出，成为了 POSIX 标准，TLI 后面也标准化为了 XTI，现在可以在部分 Unix 系统中找到。TLI/XTI 的使用方法和 Sockets API 有些类似，但是比较特别的一点在于，Sockets API 第一步是 `socket` 调用，传的参数就决定了这是 TCP 还是 UDP 还是其他什么协议，而 TLI 是通过打开不同的设备文件来进行区分：

```c
int fd = t_open("/dev/udp", O_RDWR, NULL);
```

比如 TCP 就是 `/dev/tcp`，UDP 就是 `/dev/udp`，同理还有 `/dev/icmp` 等等。这颇有 Unix 的哲学：everything is a file。而 BSD Sockets API 则是有对应的系统调用，libc 基本不需要做什么事情。

沿着这个思路，既然 TLI 第一步是打开一个文件，难道后面的一系列的 bind、connect、send、recv 等操作也是对文件读写吗？是的！如果我们查看 illumos 的[源码](https://github.com/illumos/illumos-gate/blob/46f52c84cb830d1636c093bd5c2d83074aeaf21c/usr/src/lib/libnsl/nsl/_conn_util.c#L76-L82)，会发现 `t_connect` 函数的核心实现是：

```c
	creq = (struct T_conn_req *)ctlbufp->buf;
	creq->PRIM_type = T_CONN_REQ;
	creq->DEST_length = call->addr.len;
	creq->DEST_offset = 0;
	creq->OPT_length = call->opt.len;
	creq->OPT_offset = 0;

	if (putmsg(fd, ctlbufp,
	    (struct strbuf *)(call->udata.len? &call->udata: NULL), 0) < 0) {
		t_errno = TSYSERR;
		return (-1);
	}
```

可以看到，这段在 libnsl 中的代码构造了一个结构体 `struct T_conn_req`，然后通过 `putmsg` 系统调用发送出去。可以预想，内核那边虚拟了一个 `/dev/tcp` 设备，这个设备注册了 putmsg 的回调函数。在回调函数中，解析结构体的字段，然后执行相应的操作。用户调用 TLI 函数，然后 libnsl 负责把函数的参数封装成一个结构体，然后向 `t_open` 打开的设备文件发送结构体的内容。内核和 libnsl 约定好了结构体，然后不同的操作根据结构体的 `PRIM_type` 字段来区分。实际上，这个约定也是一个标准，叫做 TPI(Transport Provider Interface)。

## Transport Provider Interface

TPI(Transport Provider Interface) 约定了内核和 libnsl 之间的接口。内核和用户态之间互相发送消息，有点像 HTTP，一个请求过去，一个响应回来。只不过请求是 “connect” 或者 “accept” 等等。相比 Sockets API，确实绕了很多，首先要封装到 struct 里面，然后通过统一的读写 syscall 进入到内核，再解析一遍 struct，再做实际的操作。如果直接 syscall 的话，内核实现会比较简单，只不过不 “Unix” 了。实际上，如过你阅读 Illumos 源码，它在解析 struct 以后，也会转而执行相应的 Sockets 处理函数，然后把返回值再封装成 TLI 的响应，发送给用户程序。

比较有意思的是，TPI 本身也是有状态的：Idle，Unbound，Data Transfer，等待 ACK 等等。所以如果你在 Solaris 上跑 netstat，会发现 UDP 也有状态（Idle/Unbound），那实际上不是 UDP 的状态，而是 TPI 的状态。正因此，我在维护 lsof 的时候，经常看到 TCP/TPI state，不明所以，才会研究 TPI 的历史，然后找到 TLI，才知道除了 Sockets 以外，还有一套 Unix 上的网络 API。有趣的是，TLI 是 System V 提供的，以前经常听到 System V ABI 的说法，却不知道 System V 是一个 Unix 操作系统，现在依然还可以在很多地方看到它的身影。

## 参考资料

- [Networking Services (XNS)](https://pubs.opengroup.org/onlinepubs/9647699/toc.pdf)
- [Transport Provider Interface](http://www.openss7.org/docs/tpi.pdf)