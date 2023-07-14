---
layout: post
date: 2018-07-15 01:10:00 +0800
tags: [debian,stretch,mussh]
category: devops
title: 用 MuSSH 快速对多台机器进行软件包升级
---

Debian Stretch 9.5 刚刚更新，自己手上有不少 stretch 的机器，于是顺手把他们都升级了。不过，这个过程比较繁琐，于是我采用了 MuSSH 的方法，让这个效率可以提高，即自动同时 SSH 到多台机器上进行更新。

首先编写 hostlist 文件，一行一个地址，分别对应每台机器。

然后采用 MuSSH 对每台机器执行同样的命令

```shell
$ mussh -H hostlist -c 'apt update && apt upgrade -y'
```

此时要求，ssh 上去以后有相应的权限。这个有许多方法，不再赘述。然后就可以看到一台台机器升级，打上安全补丁，爽啊。
