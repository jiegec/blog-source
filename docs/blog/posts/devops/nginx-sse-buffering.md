---
layout: post
date: 2026-03-05
tags: [nginx,sse,buffering]
categories:
    - devops
---

# Nginx 反代导致 SSE 延迟变高的问题与解决方法

## 背景

最近有同学遇到这么一个问题：在 Nginx 反代后面搭了一个使用 SSE（Server Sent Events）机制的服务端，但客户端观察到请求延迟比较高，数据批量到达，而不是一行一行地出现。经过排查，发现是 Nginx 的 buffering 机制导致的。本文通过实验复现该问题，并探索了几种解决方法。

<!-- more -->

## 问题复现

为了复现这个问题，我 Vibe Coding 了一个测试服务端 `server.py`，监听 8080 端口，在 `/events` 路径下每秒发送一条 SSE 消息，共发送 5 次：

```python
#!/usr/bin/env python3
"""SSE server that sends 5 messages, one every second."""

import time
from http.server import HTTPServer, BaseHTTPRequestHandler


class SSEHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()

            for i in range(5):
                message = f"data: Message {i + 1} at {time.time()}\n\n"
                self.wfile.write(message.encode("utf-8"))
                self.wfile.flush()
                time.sleep(1)

            self.wfile.close()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), SSEHandler)
    print("SSE server starting on http://0.0.0.0:8080")
    server.serve_forever()
```

启动服务端，使用 curl 访问 `localhost:8080/events`，可以看到每秒输出一条消息，没有延迟。接下来在 docker compose 里启动 Nginx，配置如下：

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - sse-server
    networks:
      - sse-network

  sse-server:
    image: python:3.11-slim
    command: python /app/server.py
    volumes:
      - ./server.py:/app/server.py:ro
    ports:
      - "8080:8080"
    networks:
      - sse-network

networks:
  sse-network:
    driver: bridge
```

接着是 nginx 的配置：

```conf
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;

        location /events {
            proxy_pass http://sse-server:8080;

            # Add additional config later here
        }
    }
}
```

启动 docker compose，用 curl 分别访问 80 和 8080 端口的 `/events`，观察到以下现象：

- 通过 80 端口访问 nginx：5 秒后一次性输出所有 data
- 通过 8080 端口直接访问 server：每秒输出一条 data

这说明确实是 nginx 导致的。接下来测试几种解决方法。

## 解决方法

首先，查阅 nginx 的[文档](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering)，可以看到它的描述：

```
Syntax: 	proxy_buffering on | off;
Default: 	proxy_buffering on;
Context: 	http, server, location

Enables or disables buffering of responses from the proxied server.

When buffering is enabled, nginx receives a response from the proxied server as soon as possible, saving it into the buffers set by the proxy_buffer_size and proxy_buffers directives. If the whole response does not fit into memory, a part of it can be saved to a temporary file on the disk. Writing to temporary files is controlled by the proxy_max_temp_file_size and proxy_temp_file_write_size directives.

When buffering is disabled, the response is passed to a client synchronously, immediately as it is received. nginx will not try to read the whole response from the proxied server. The maximum size of the data that nginx can receive from the server at a time is set by the proxy_buffer_size directive.

Buffering can also be enabled or disabled by passing “yes” or “no” in the “X-Accel-Buffering” response header field. This capability can be disabled using the proxy_ignore_headers directive. 
```

根据描述，可以想到一些可能的解决方法：

1. Nginx 配置添加 `proxy_buffering off;`：工作
2. 服务端在响应的 header 里添加 `X-Accel-Buffering: no`（`self.send_header("X-Accel-Buffering", "no")`）：工作

在一开头的场景里，由于中间的 Nginx 配置改起来比较麻烦，最后就用了第二种方法。回想起来，一开始思路走偏了，一直在往 cache 方向想，实际上是 buffering 的问题：Nginx 会先从 server 读取一大片数据，攒够了再发给 client，避免来回转发小段数据的开销，但 SSE 又希望有较低的延迟，这就冲突了。

小结一下：排查这类问题要理解 Nginx 的工作机制，找错方向可能很难定位；同时，利用 LLM 快速构建可复现的测试环境，有助于验证假设。
