---
layout: post
date: 2020-03-09
tags: [jailkit,chroot,scp]
category: devops
title: 用 jailkit 限制用户仅 scp
---

最近需要用 scp 部署到生产机器，但又不想出现安全问题，所以用了 jailkit 的方法。首先是创建单独的用户，然后生成 ssh key 来认证，不再赘述。此时是可以 scp 了，但用户依然可以获得 shell，不够安全。

然后找到了下面参考链接，大概摘录一下所需要的命令和配置：

```shell
mkdir /path/to/jail
chown root:root /path/to/jail
chmod 701 /path/to/jail
jk_init -j /path/to/jail scp sftp jk_lsh
jk_jailuser -m -j /path/to/jail jailed_user
vim /path/to/jail/etc/jailkit/jk_lsh.ini
# Add following lines
[jailed_user]
paths = /usr/bin, /usr/lib
exectuables = /usr/bin/scp
```

之后可以发现该用户的 shell 已经更改 jk_chrootsh，并且只能用 scp。

参考：https://blog.tinned-software.net/restrict-linux-user-to-scp-to-his-home-directory/