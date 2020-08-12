---
layout: post
date: 2020-08-12 09:46:00 +0800
tags: [certbot,route53,aws,letsencrypt,iam]
category: devops
title: 用 certbot 申请 route53 上的域名的 LetsEncrypt 证书并上传到 IAM
---

最近遇到了 AWS Certificate Manager 的一些限制，所以只能用 IAM 证书。于是上网找到了通过 certbot 申请 LE 证书，通过 route53 API 验证的方法。

首先配置 aws 的 credential。然后，按照 certbot：

```shell
pip3 install -U certbot certbot_dns_route53
```

然后，就可以申请证书了：

```shell
certbot certonly --dns-route53 --config-dir "./letsencrypt" --work-dir "./letsencrypt" --logs-dir "./letsencrypt"  -d example.com --email a@b.com --agree-tos
```

如果申请成功，在当前目录下可以找到证书。然后上传到 IAM：

```shell
aws iam upload-server-certificate --server-certificate-name NameHere \
    --certificate-body file://letsencrypt/live/example.com/cert.pem \
    --private-key file://letsencrypt/live/example.com/privkey.pem \
    --certificate-chain file://letsencrypt/live/example.com/chain.pem \
    --path /cloudfront/
```

如果要用于 cloudfront，才需要最后的路径参数；否则可以去掉。这样就完成了 IAM 证书的上传。