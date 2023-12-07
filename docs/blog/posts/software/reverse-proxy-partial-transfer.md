---
layout: post
date: 2023-12-07
tags: [nginx,proxy,http,network]
categories:
    - software
---

# 反向代理的 Partial Transfer 问题

反向代理已经是无处不在，但是如果反向代理没有根据使用场景调优，或者出现了一些异常，可能会带来不好的用户体验，并且现象十分奇怪，例如访问某 GitLab 实例的时候，偶尔会出现页面加载不完整的情况。

这些问题困扰了我们很久，到最后才发现，原来问题在反向代理上。下面就来回顾一下事情的经过。

<!-- more -->

## GitLab 页面加载不完整现象

某 GitLab 实例从某一天开始，用户就开始反馈页面经常刷不出来的问题。打开浏览器的 Developer Tools 查看 HTTP 请求，会发现出现报错 `ERR_CONTENT_LENGTH_MISMATCH`（Chrome）或者 `NS_ERROR_NET_PARTIAL_TRANSFER`（Firefox）。从名字来看，这个错误的意思是，浏览器只收到了 HTTP 响应的一部分，但是 HTTP 响应头部的 Content-Length 却比实际收到的内容要多，说明确实是没发全。用 Wireshark 抓包，可以看到是网站主动发的 FIN，也不像是 NAT 网关的问题。

这个问题困扰了用户和管理员很久，一直没有找到原因。做一些简单的测试，会发现下载是否完全和 HTTP 响应的内容大小有关，例如浏览一些大的 HTML，就容易被截断，并且截断以后的长度比较稳定地出现在几个数字之间：130304 和 130269，大概 130 KB。

在网上搜索关键词，可以找到这么一篇 [StackOverflow 回答](https://stackoverflow.com/questions/37908967/express-and-nginx-neterr-content-length-mismatch/46694782#46694782)：`Express and nginx net::ERR_CONTENT_LENGTH_MISMATCH`，看起来和我们遇到的现象很类似。回答中提到，Nginx 有内建的 buffering 机制，关掉它就可以解决问题。但是这看起来太暴力了，不像是合理的解决办法，毕竟 buffering 机制是有用的。

从 [Nginx 官网](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering)可以找到 buffering 机制的说明：

```
When buffering is enabled, nginx receives a response from the proxied server as
soon as possible, saving it into the buffers set by the proxy_buffer_size and
proxy_buffers directives. If the whole response does not fit into memory, a part
of it can be saved to a temporary file on the disk. Writing to temporary files
is controlled by the proxy_max_temp_file_size and proxy_temp_file_write_size
directives.
```

翻译成中文，意思就是 Nginx 打开 buffering 机制后，会尽量快地从后端服务器读取响应。这很合理，因为一般后端服务器的资源比较宝贵，如果有很多个链接堵塞了，TCP 发送窗口满了，发不了新的数据，一直在等待客户端回复 ACK，这样就会维持很多 TCP 连接，影响服务器处理新连接的能力，这种累活应该还是由 Nginx 来干。但是问题来了：Nginx 从后端尽量快地读取响应，但浏览器并不一定能够很快地从 Nginx 读取响应，因为浏览器到 Nginx 的网络可能很慢。速率不匹配，那么 Nginx 肯定要实现一定的缓存，这就是 buffering 机制。

具体地，为了实现高效的 buffering 机制，很自然地回想到用内存做 buffer。但是内存容量也是相对有限的，内存放不下，自然就只能写到硬盘里面。那么问题来了，要是硬盘也满了，或者写入硬盘失败了，怎么办？一方面，还得赶紧从后端读取响应，让后端去做别的事情；另一方面，客户端在慢吞吞地收数据，硬盘又写不进去。这时候 Nginx 只能放弃挣扎，把连接断掉。于是客户端就看到了 HTTP 响应传了一半的情况。

这也就能解释之前观察到的一个现象：有的网页，走有线网能够完整打开，走无线网打开是不完整的。从 buffering 机制来解释，就是有线网能够在 buffer 满之前把数据都传完，而无线网来不及。

## 本地复现

理论理解了，下面来实践一下。我们用 docker compose 启动两个容器，一个容器 proxy 作为反向代理，运行一个 nginx；另一个容器 backend 作为后端，为了简单，也跑了个 nginx，服务一个简单的大 HTML 文件。后端用其他软件也是一样的，只要可以构建出足够大的 HTTP 响应（MB 量级）。

Docker compose 配置：

```yaml
services:
  backend:
    image: nginx:stable
    ports:
      - "127.0.0.1:8001:80"
    volumes:
      - ./backend.conf:/etc/nginx/conf.d/default.conf:ro
      - ./backend:/web:ro
  proxy:
    image: nginx:stable
    ports:
      - "127.0.0.1:8002:80"
    volumes:
      - ./proxy.conf:/etc/nginx/conf.d/default.conf:ro
```

后端 Nginx 配置：

```conf
server {
	listen 80;
	location / {
		root /web;
	}
}
```

反向代理 Nginx 配置：

```conf
server {
	listen 80;
	location / {
		proxy_pass http://backend;
	}
}
```

那么对反代的访问，就能访问到后端上的 `index.html` 了。在本地创建一个足够大的 `index.html` 文件，确认下载都没有问题。

在搞破坏之前，可以先用 `inotifywait` 工具来观察 Nginx 读写文件的行为：

```shell
apt update
apt install inotify-tools
docker exec -it nginx-partial-content-test-proxy-1 /bin/bash
inotifywait -r -m /var/cache/nginx
```

用 ApacheBench 进行性能测试：`ab -n 10000 -c 10 http://localhost:8002/`，可以看到 `inotifywait` 显示 Nginx 进程对 `/var/cache/nginx/proxy_temp` 目录下进行了大量的读写，这就是前面所述的 buffering 机制，用来保存文件的路径。

接下来修改权限，让 Nginx 无法读取该目录：

```shell
docker exec -it nginx-partial-content-test-proxy-1 /bin/bash
chmod 000 /var/cache/nginx/proxy_temp
```

此时再去跑 ApacheBench，会发现大部分请求都因为长度问题失败了：

```log
Concurrency Level:      10
Time taken for tests:   5.707 seconds
Complete requests:      10000
Failed requests:        9999
   (Connect: 0, Receive: 0, Length: 9999, Exceptions: 0)
```

用 curl 也可以测试出类似的错误：`curl: (18) transfer closed with 455593 bytes remaining to read`。此时 proxy 容器也会报错：`open() "/var/cache/nginx/proxy_temp/7/63/0000014637" failed (13: Permission denied) while reading upstream, client: 172.18.0.1, server: , request: "GET / HTTP/1.1", upstream: "http://172.18.0.3:80/", host: "localhost:8002"`。用浏览器访问，也复现了之前在 GitLab 实例上看到的现象。恢复目录权限以后，一切都正常了。

这印证了之前的猜想：`proxy_temp` 目录写不进去，就有概率出现 Partial Transfer 的情况。但是，此时下载的文件大小比较随机，不像之前那样集中在 130 KB。这时候就要思考 Partial Transfer 的原理了：客户端发起 HTTP 请求，proxy 容器收到请求，转发给 backend；backend 收到 HTTP 请求后，就给 proxy 发送 HTTP 响应。然后 proxy 容器一边从 backend 接收 HTTP 响应，另一边还要发给客户端。什么情况下会断开呢？就是内存里的 buffer 都用完了，backend 给 proxy 发送得快，proxy 给客户端发送得慢，速度的差，决定了内存里的 buffer 可以撑多久。

为了验证这个理论，手动给客户端到 proxy 容器的链路上添加一个延迟，这样就拖慢了 proxy 给客户端发送的速录。在 Linux 上，可以用 [tc 给网络接口人为地添加延迟](https://medium.com/@kazushi/simulate-high-latency-network-using-docker-containerand-tc-commands-a3e503ea4307)：

```shell
tc qdisc add dev [bridge_name] root netem delay 100ms
```

`bridge_name`` 是以 br- 开头的 bridge 网络接口名。此时用 ping 测量，从 proxy 容器访问 host 要 100 ms，proxy 容器访问 backend 容器要 0.02 ms。这就达成了不对称的目的。添加了延迟后，发现 curl 下载的文件大小稳定在 109312 字节附近，也就是 109 KB。虽然和前面的 130 KB 不相等，但是也足以证明了是类似的情况。这个大小，应该和 nginx 在内存中给每个链接维护的 buffer 大小有关，也和网络上传输的过程有关。

小结：

1. 因 nginx 容器上 proxy_temp 路径下无法写入文件（例如权限不正确、盘满了），nginx 的 buffering 机制在遇到内存中 buffer 用完的情况下，会截断 HTTP 响应；
2. 根据客户端到 nginx，nginx 到后端的带宽和延迟情况，可能会截断到不同的位置。

## 权限问题

有意思的是，管理员表示之前并没有改过目录的权限。在网上查了一下，有网友反馈遇到了类似的问题：[Changing ownership of proxy_temp and other temp directories](https://forum.nginx.org/read.php?2,296793,296793#msg-296793)。网友表示，他升级 nginx 之前，proxy_temp 路径的权限是归 nobody 所有，nginx 也是用 nobody 用户运行的，所以没有问题。升级 nginx 以后，nginx 用单独的 nginx 用户去执行，此时它没有办法访问 nobody 用户创建的文件夹，因为权限是 `rwx------`。

如果深入观察邮件回复，会发现最终引到了一个 [GitHub commit](https://github.com/vmware/photon/commit/abbfedfda7dfd7905d2953745cf1332fde80689c#diff-9a5cc4e7b91577cbccbb6aacc4bc2ee46672ccbe984b89581fc600b2877729f5)，它在给 nginx 添加新功能的同时，修改了默认的 nginx 用户设置，使得默认用户变成了 nginx。从维护者的角度来看，把 nobody 换成 nginx 用户，应该不会有什么影响。却不知道 nginx 会用 nobody 用户创建 proxy_temp 等目录，并且设置了严格的权限。一升级，用户一变，nginx 自己就用不了了。于是就出现了问题。

在某 GitLab 实例的问题上，最后发现确实是权限问题。但是细节和上面的也不完全一样，具体权限怎么坏的，目前还是一个谜。