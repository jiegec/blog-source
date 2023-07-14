---
layout: post
date: 2018-05-20
tags: [vmware,vcsa,esxi]
category: devops
title: 在 VMware ESXi 上部署 vCSA 实践
---

首先获取 vCSA 的 ISO 镜像，挂载到 Linux 下（如 /mnt），然后找到 /mnt/vcsa-cli-installer/templates/install 下的 embedded_vCSA_on_ESXi.json，复制到其它目录并且修改必要的字段，第一个 `password` 为 ESXi 的登录密码，一会在安装的过程中再输入。下面有个 deployment_option，根据你的集群大小来选择，我则是用的 small。下面配置这台机器的 IP 地址，用内网地址即可。下面的 system_name 如果要写 fqdn，记得要让这个域名可以解析到正确的地址，不然会安装失败，我因此重装了一次。下面的密码都可以留空，在命令行中输入即可。SSO 为 vSphere Client 登录时用的密码和域名，默认用户名为 Administrator@domain_name (默认的话，则是 Administrator@vsphere.local) 这个用户名在安装结束的时候也会提示。下面的 CEIP 我选择关闭，设置为 false。

接下来进行安装。

```bash
$ /mnt/vcsa-cli-installer/lin64/vcsa-deploy install /path/to/embedded_vCSA_on_ESXi.json --accept-eula
```

一路输入密码，等待安装完毕即可。然后通过 443 端口进入 vSphere Client, 通过 5480 端口访问 vCSA 的管理页面。两个的密码可以不一样。


2018-05-21 Update: 想要设置 VMKernel 的 IPv6 网关的话，ESXi 中没找到配置的地方，但是在 vSphere Client 中可以进行相关配置。
