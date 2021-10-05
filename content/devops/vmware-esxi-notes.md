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

## 升级方法

1. 下载 Offline Bundle 文件
2. 上传到 ESXi datastore 中
3. 在 `/vmfs/volumes/` 里找到更新文件
4. 查询 profile 列表 `esxcli software sources profile list -d <zip>`
5. 更新到 profile `esxcli software profiel update -p <profile> -d <zip>`

ref: [Upgrade or Update a Host with Image Profiles](https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.esxi.upgrade.doc/GUID-E51C5DB6-F28E-42E8-ACA4-0EBDD11DF55D.html)