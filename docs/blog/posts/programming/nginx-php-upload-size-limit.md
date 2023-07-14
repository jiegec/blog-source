---
layout: post
date: 2018-06-10
tags: [nginx,php,mediawiki]
categories:
    - programming
---

# 调整 Nginx 和 PHP 的上传文件大小限制

之前迁移的 MediaWiki，有人提出说无法上传一个 1.4M 的文件。我去看了一下网站，上面写的是限制在 2M，但是一上传就说 Entity Too Large，无法上传。后来经过研究，是 Nginx 对 POST 的大小进行了限制，同时 PHP 也有限制。

Nginx 的话，可以在 nginx.conf 的 http 中添加，也可以在 server 或者 location 中加入这么一行：

```
client_max_body_size 100m;
```

我的建议是，尽量缩小范围到需要的地方，即 location > server > http。

在 PHP 中，则修改 /etc/php/7.0/fpm/php.ini：

```
post_max_size = 100M
```

回到 MediaWiki 的上传页面，可以看到显示的大小限制自动变成了 100M，这个是从 PHP 的配置中直接获得的。
