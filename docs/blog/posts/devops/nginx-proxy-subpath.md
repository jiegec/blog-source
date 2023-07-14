---
layout: post
date: 2018-06-01
tags: [nginx,http]
categories:
    - devops
title: 在 Nginx 将某个子路径反代
---

现在遇到这么一个需求，访问根下面是提供一个服务，访问某个子路径（/abc），则需要提供另一个服务。这两个服务处于不同的机器上，我们现在通过反代把他们合在一起。在配置这个的时候，遇到了一些问题，最后得以解决。

```
upstream root {
    server 1.2.3.4:1234;
}
upstream subpath {
    server 4.3.2.1:4321;
}

server {
    listen 443 ssl;
    server_name test.example.com;

    # the last slash is useful, see below
    location /abc/ {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # the last slash is useful too, see below
        proxy_pass http://subpath/;
    }

    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://root;
    }
}
```

由于并不想 subpath 他看到路径中 /abc/ 这一层，导致路径和原来在根下不同，通过这样配置以后，特别是两个末尾的斜杠，可以让 nginx 把 GET /abc/index.html 改写为 GET /index.html，这样我们就可以减少许多配置。当然，我们还是需要修改一下配置，现在是 host 在一个新的域名的一个新的子路径下，这主要是为了在返回的页面中，连接写的是正确的。
