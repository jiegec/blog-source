---
layout: post
date: 2023-02-03
tags: [solaris]
categories:
    - system
---

# Solaris 11.4 安装

## 下载安装镜像

访问 <https://www.oracle.com/solaris/solaris11/downloads/solaris-downloads.html>，点击下载，登录后跳转到一个新的页面。在 Platform 下拉框选择 x86，会出现一系列可以下载的文件。以 11.4.42.111.0 为例，需要下载的是：V1019840-01.iso Oracle Solaris 11.4.42.111.0 Interactive Text Install ISO (x86) for (Oracle Solaris on x86-64 (64-bit)), 890.5 MB。可以直接在浏览器中下载，也可以点击网页中的 WGET Options，用 wget 脚本下载。

下载以后，挂载 ISO 到虚拟机，正常按照指示进行安装

## 配置软件源

Solaris 的在线软件源需要订阅，如果不想订阅，需要下载和 Solaris **版本一致** 的 IPS 仓库。下载的地址和上面一样，需要 7 个 zip 文件，如 V1019847-01_1of7.zip Oracle Solaris 11.4.42.111.0 IPS Repository (SPARC, x86) for (Oracle Solaris on x86-64 (64-bit)), 2.2 GB。建议用 wget 脚本批量下载。

UPDATE: 根据 <https://blogs.oracle.com/solaris/post/building-open-source-software-on-oracle-solaris-114-cbe-release>，实际上可以不下载 IPS 仓库，而是用在线的仓库，内容和下载的一致：

```shell
sudo pkg set-publisher -G '*' -g http://pkg.oracle.com/solaris/release/ solaris
```

下载好了以后，全部解压到一个目录中，如 `/export/home/user/solaris`，然后启动本地的软件源服务：

```shell
sudo svccfg -s application/pkg/server setprop pkg/inst_root=/export/home/user/solaris
sudo svccfg -s application/pkg/server setprop pkg/readonly=true
sudo svccfg -s application/pkg/server setprop pkg/port=8081
sudo svcadm refresh application/pkg/server
sudo svcadm enable application/pkg/server
```

然后配置 `pkg` 使用本地软件源：

```shell
sudo pkg set-publisher -G '*' -g http://localhost:8081 solaris
```

之后就可以正常使用了：

```shell
sudo pkg install gcc-11
```

命令参考：<https://www.oracle.com/docs/tech/solaris-11-cheat-sheet.pdf>



