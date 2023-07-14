---
layout: post
date: 2019-05-22
tags: [nginx,https]
categories:
    - devops
---

# Nginx 反代到 HTTPS 上游

这次遇到一个需求，要反代到不在内网的地址，为了保证安全，还是得上 HTTPS，所以尝试了一下怎么给 upstream 配置自签名 HTTPS 证书的验证。

```
upstream subpath {
    server 4.3.2.1:4321;
}

server {
    listen 443 ssl;
    server_name test.example.com;

    location /abc {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_ssl_trusted_certificate /path/to/self_signed_cert.crt;
        proxy_ssl_name 1.2.3.4; // to override server name checking
        proxy_ssl_verify on;
        proxy_ssl_depth 2;
        proxy_ssl_reuse on;
        proxy_pass https://subpath;
    }
}
```

可以用 `openssl` 获得自签名的 cert :

```
echo | openssl s_client -showcerts -connect 4.3.2.1:4321 2>/dev/null | \
                              openssl x509 -text > /path/to/self_signed_cert.crt
```

ref: https://stackoverflow.com/questions/7885785/using-openssl-to-get-the-certificate-from-a-server
