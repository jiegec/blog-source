---
layout: post
date: 2021-10-05T21:19:00+08:00
tags: [esxi,vmware]
category: devops
title: ESXi 常用信息
---

## 常用链接

- [检查 CPU microcode 版本](http://blog.erben.sk/2020/02/04/how-to-check-cpu-microcode-revision-in-esxi/)：

```shell
vsish -e cat /hardware/cpu/cpuList/0 | grep -i -E 'family|model|stepping|microcode|revision'
```

- [ESXi 从 6.7 到 6.7U1 升级时出现版本问题](https://kb.vmware.com/s/article/56145)
- [ESXi 6.7 OEM 版本下载](https://customerconnect.vmware.com/downloads/info/slug/datacenter_cloud_infrastructure/vmware_vsphere/6_7#custom_iso)
- [ESXi 7.0 OEM 版本下载](https://customerconnect.vmware.com/downloads/info/slug/datacenter_cloud_infrastructure/vmware_vsphere/7_0#custom_iso)
- [ESXi 7.0 标准版下载](https://customerconnect.vmware.com/en/web/vmware/evalcenter?p=free-esxi7)
- [NUC 11 ESXi 7.0 网卡支持](https://flings.vmware.com/community-networking-driver-for-esxi/comments)

```shell
$ esxcli software vib install -d $PWD/Net-Community-Driver_1.2.0.0-1vmw.700.1.0.15843807_18028830.zip
```

## 升级方法

1. 下载 Offline Bundle 文件
2. 上传到 ESXi datastore 中
3. 在 `/vmfs/volumes/` 里找到更新文件
4. 查询 profile 列表 `esxcli software sources profile list -d <zip>`
5. 更新到 profile `esxcli software profiel update -p <profile> -d <zip>`

ref: [Upgrade or Update a Host with Image Profiles](https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.esxi.upgrade.doc/GUID-E51C5DB6-F28E-42E8-ACA4-0EBDD11DF55D.html)

## 防火墙

列出所有防火墙规则：

```shell
$ esxcli network firewall ruleset list
```

允许出站 SSH：

```shell
$ esxcli network firewall ruleset set --enabled=true --ruleset-id=sshClient
```

关闭出站 SSH：

```shell
$ esxcli network firewall ruleset set --enabled=false --ruleset-id=sshClient
```

## NUC11i5 ESXi 7.0 安装过程

1. 下载 ESXi ISO 文件，用 UNetbootin 制作安装盘
2. 插入 U 盘，在 NUC 上安装 ESXi，在 81% 的时候卡住了，不管直接重启
3. 用 root 无密码登录进去，然后重置网络设置
4. 配置 usb 网卡，然后通过网页访问 ESXi，打开 SSH
5. 下载 Fling 上面的社区网卡支持，用 esxcli 安装
6. 重启以后，就可以看到 vmnic0 网卡了

参考：[Solution: ESXi Installation with USB NIC only fails at 81%](https://www.virten.net/2020/07/solution-esxi-installation-with-usb-nic-only-fails-at-81/)