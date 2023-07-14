---
layout: post
date: 2018-05-08
tags: [linux,nat,forwarding,vmware,esxi,nginx,proxy]
categories:
    - networking
title: 使用 Nginx 转发 VMware ESXi
---

我们的 VMware ESXi 在一台 NAT Router 之后，但是我们希望通过域名可以直接访问 VMware ESXi。我们首先的尝试是，把 8443 转发到它的 443 端口，比如：

```shell
socat TCP-LISTEN:8443,reuseaddr,fork TCP:esxi_addr:443
```

它能工作地很好（假的，如果你把 8443 换成 9443 它就不工作了），但是，我们想要的是，直接通过 esxi.example.org 就可以访问它。于是，我们需要 Nginx 在其中做一个转发的功能。在这个过程中遇到了很多的坑，最后终于是做好了（VMware Remote Console 等功能还不行，需要继续研究）。

首先讲讲为啥把 8443 换成 9443 不能工作吧 -- 很简单，ESXi 的网页界面会请求 8443 端口。只是恰好我用 8443 转发到 443，所以可以正常工作。这个很迷，但是测试的结果确实如此。VMware Remote Console 还用到了别的端口，我还在研究之中。

来谈谈怎么配置这个 Nginx 转发吧。首先是 80 跳转 443:
```
server {
        listen 80;
        listen 8080;
        server_name esxi.example.org;

        return 301 https://$host$request_uri;
}
```

这个很简单，接下来是转发 443 端口：
```

server {
        listen 443 ssl;
        server_name esxi.example.org;
        ssl_certificate /path/to/ssl/cert.pem;
        ssl_certificate_key /path/to/ssl/key.pem;

        location / {
                proxy_pass https://esxi_addr;
                proxy_ssl_verify off;
                proxy_ssl_session_reuse on;
                proxy_set_header Host $http_host;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
        }
}
```

此时，打开 https://esxi.example.org 就能看到登录界面了。但是仍然无法登录。从 DevTools 看错误，发现它请求了 8443 端口。于是进行转发：
```
server {
        listen 8443 ssl;
        server_name esxi.example.org;
        ssl_certificate /path/to/ssl/cert.pem;
        ssl_certificate_key /path/to/ssl/key.pem;


        location / {
                if ($request_method = 'OPTIONS') {
                        add_header 'Access-Control-Allow-Origin' 'https://esxi.example.org';
                        add_header 'Access-Control-Allow-Credentials' 'true';
                        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
                        add_header 'Access-Control-Max-Age' 1728000;
                        add_header 'Access-Control-Allow-Headers' 'VMware-CSRF-Token,DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Cookie,SOAPAction';
                        add_header 'Content-Type' 'text/plain; charset=utf-8';
                        add_header 'Content-Length' 0;
                        return 204;
                }

                add_header 'Access-Control-Allow-Origin' 'https://esxi.example.org';
                add_header 'Access-Control-Allow-Credentials' 'true';
                proxy_pass https://esxi_addr:443;
                proxy_ssl_verify off;
                proxy_ssl_session_reuse on;
                proxy_set_header Host $http_host;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
        }
}
```

主要麻烦的是配置 CORS 的相关策略。我也是看了 DevTools 的错误提示半天才慢慢写出来的。这样配置以后，就可以成功登录 VMware ESXi 了。

20:02 更新：现在做了 WebSocket 转发，目前可以在浏览器中打开 Web Console 了。但是，在访问 https://esxi.example.org/ 的时候还是会出现一些问题，然而 https://esxi.example.org:8443/ 是好的。

转发 WebSocket：
```
map $http_upgrade $connection_upgrade {
        default upgrade;
        ''      close;
}

server {
        listen 8443 ssl;
        server_name esxi.example.org;
        ssl_certificate /path/to/ssl/cert.pem;
        ssl_certificate_key /path/to/ssl/key.pem;


        location / {

                if ($request_method = 'OPTIONS') {
                        add_header 'Access-Control-Allow-Origin' 'https://esxi.example.org';
                        add_header 'Access-Control-Allow-Credentials' 'true';
                        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
                        add_header 'Access-Control-Max-Age' 1728000;
                        add_header 'Access-Control-Allow-Headers' 'VMware-CSRF-Token,DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Cookie,SOAPAction';
                        add_header 'Content-Type' 'text/plain; charset=utf-8';
                        add_header 'Content-Length' 0;
                        return 204;
                }

                add_header 'Access-Control-Allow-Origin' 'https://esxi.example.org' always;
                add_header 'Access-Control-Allow-Credentials' 'true' always;

                proxy_pass https://esxi_addr:443;
                proxy_ssl_verify off;
                proxy_ssl_session_reuse on;
                proxy_set_header Host $http_host;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection $connection_upgrade;
        }
}
```

20:29 更新：找到了 VMware Remote Console 的端口：902，用 iptables 进行 DNAT 即可：
```shell
iptables -A PREROUTING -i wan_interface -p tcp -m tcp --dport 902 -j DNAT --to-destination esxi_addr:902
```

2018-05-09 08:07 更新：最后发现，还是直接隧道到内网访问 ESXi 最科学。或者，让 443 重定向到 8443：
```
server {
        listen 443 ssl;
        server_name esxi.example.org;
        ssl_certificate /path/to/ssl/cert.pem;
        ssl_certificate_key /path/to/ssl/key.pem;

        return 301 https://$host:8443$request_uri;
}
```
这样，前面也不用写那么多 CORS 的东西了。
