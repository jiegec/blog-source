---
layout: post
date: 2018-07-06
tags: [container,lxc,systemd-nspawn,systemd-run]
category: devops
title: 通过 systemd-run 直接在容器中执行命令
---

之前使用 `systemd-nspawn` 开了容器，然后通过 `machinectl shell` 进去，想要起一个服务然后丢到后台继续执行，但是发现离开这个 session 后这个进程总是会被杀掉，于是找了 `systemd-run` 的方案，即：

```shell
systemd-run --machine machine_name_here absolute_path_to_executable args_here
```

这样可以直接在容器中跑服务，而且用这个命令输出的临时 server 名称，还可以看到日志：

```shell
journalctl --machine machine_name_here -u unit_name_above
```
