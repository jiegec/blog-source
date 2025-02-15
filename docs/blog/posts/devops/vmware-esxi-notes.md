---
layout: post
date: 2021-10-05
tags: [esxi,vmware]
categories:
    - devops
---

# ESXi 常用信息

## 常用链接

- [检查 CPU microcode 版本](http://blog.erben.sk/2020/02/04/how-to-check-cpu-microcode-revision-in-esxi/)：

```shell
vsish -e cat /hardware/cpu/cpuList/0 | grep -i -E 'family|model|stepping|microcode|revision'
```

- [AMD 最新 microcode 版本](https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/tree/amd-ucode/README)
- [ESXi 从 6.7 到 6.7U1 升级时出现版本问题](https://kb.vmware.com/s/article/56145)
- [ESXi 6.7 OEM 版本下载](https://customerconnect.vmware.com/downloads/info/slug/datacenter_cloud_infrastructure/vmware_vsphere/6_7#custom_iso)
- [ESXi 7.0 OEM 版本下载](https://customerconnect.vmware.com/downloads/info/slug/datacenter_cloud_infrastructure/vmware_vsphere/7_0#custom_iso)
- [ESXi 8.0 OEM 版本下载](https://customerconnect.vmware.com/downloads/info/slug/datacenter_cloud_infrastructure/vmware_vsphere/8_0#custom_iso)
- [ESXi 7.0 标准版下载](https://customerconnect.vmware.com/downloads/info/slug/datacenter_cloud_infrastructure/vmware_vsphere/7_0)
- [ESXi 8.0 标准版下载](https://customerconnect.vmware.com/downloads/info/slug/datacenter_cloud_infrastructure/vmware_vsphere/8_0)
- [NUC 11 ESXi 7.0 网卡支持](https://flings.vmware.com/community-networking-driver-for-esxi/comments)：

```shell
$ esxcli software vib install -d $PWD/Net-Community-Driver_1.2.0.0-1vmw.700.1.0.15843807_18028830.zip
```

## 离线升级方法

1. 下载 Offline Bundle 文件
2. 上传到 ESXi datastore 中
3. 在 `/vmfs/volumes/` 里找到更新文件
4. 查询 profile 列表 `esxcli software sources profile list -d <zip>`
5. 更新到 profile `esxcli software profile update -p <profile> -d <zip>`

ref: [Upgrade or Update a Host with Image Profiles](https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.esxi.upgrade.doc/GUID-E51C5DB6-F28E-42E8-ACA4-0EBDD11DF55D.html)

如果 CPU 比较旧，可能会有警告：[Updated Plan for CPU Support Discontinuation In Future Major vSphere Releases](https://kb.vmware.com/s/article/82794)，按照信息添加参数忽略即可，ESXi 7.0 系列都是支持的，如果之后出了新的版本可能不支持。

## 在线升级方法

```shell
$ esxcli network firewall ruleset set -e true -r httpClient
# find profile name
$ esxcli software sources profile list -d https://hostupdate.vmware.com/software/VUM/PRODUCTION/main/vmw-depot-index.xml
# upgrade to 7.0u3 for example
$ esxcli software profile update -p ESXi-7.0U3-18644231-standard -d https://hostupdate.vmware.com/software/VUM/PRODUCTION/main/vmw-depot-index.xml
```

ref: [Update Standalone ESXi Host](https://docs.macstadium.com/docs/update-standalone-esxi-host-via-online-bundle)

目前 OEM 版本还没找到在线升级方法，需要下载 zip 然后按照离线升级方法安装。

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

## 推荐博客

发现以下博客有很多关于 ESXi 的内容：

- https://williamlam.com/
- https://www.virten.net/

## 重要版本更新

参考 ESXi/vCSA Release Notes：

- Performance improvements for AMD Zen CPUs: With ESXi 7.0 Update 2, out-of-the-box optimizations can increase AMD Zen CPU performance by up to 30% in various benchmarks. The updated ESXi scheduler takes full advantage of the AMD NUMA architecture to make the most appropriate placement decisions for virtual machines and containers. AMD Zen CPU optimizations allow a higher number of VMs or container deployments with better performance.
- Reduced compute and I/O latency, and jitter for latency sensitive workloads: Latency sensitive workloads, such as in financial and telecom applications, can see significant performance benefit from I/O latency and jitter optimizations in ESXi 7.0 Update 2. The optimizations reduce interference and jitter sources to provide a consistent runtime environment. With ESXi 7.0 Update 2, you can also see higher speed in interrupt delivery for passthrough devices.
- vSphere Lifecycle Manager fast upgrades: Starting with vSphere 7.0 Update 2, you can configure vSphere Lifecycle Manager to suspend virtual machines to memory instead of migrating them, powering them off, or suspending them to disk. For more information, see Configuring vSphere Lifecycle Manager for Fast Upgrades.
- Zero downtime, zero data loss for mission critical VMs in case of Machine Check Exception (MCE) hardware failure: With vSphere 7.0 Update 3, mission critical VMs protected by VMware vSphere Fault Tolerance can achieve zero downtime, zero data loss in case of Machine Check Exception (MCE) hardware failure, because VMs fallback to the secondary VM, instead of failing. For more information, see How Fault Tolerance Works.

## vCSA 相关常见错误

- https://kb.vmware.com/s/article/85468 vCSA 日志分区 `/storage/log` 满，原因是访问 vmware 网站失败打印的日志太大：`/storage/log/vmware/analytics/analytics-runtime.log*`；解决方法：`vmon-cli -r analytics` 重启服务，然后删掉旧的日志。
- https://kb.vmware.com/s/article/83070 vCSA 日志分区 `/storage/log` 满，原因是 tomcat 日志太大。
- `XXX Service Health Alarm`：尝试重启对应服务，比如 `vmon-cli -r perfcharts` 对应 `Performance Charts`，`vmon-cli -r vapi-endpoint` 对应 `VMWare vAPI Endpoint`

查看更新状态：`cat /storage/core/software-update/stage_operation`；更新文件下载路径：`/storage/updatemgr/software-update*/stage`。有一个包特别大：`wcpovf` 需要两个多 G。

CLI 更新方法：https://earlruby.org/2021/01/upgrading-vcenter-7-via-the-command-line/

## 迁移虚拟机到不同 VM

首先，unregister 原来的 VM，然后把文件移动到新的路径下。对于 Thin Provisioned Disk，需要特殊处理，否则直接复制的话，会变成 Thick Provisioned Disk，正确方法是采用 `vmkfstool`：

```shell
vmkfstool -i "old.vmdk" -d thin "new.vmdk"
```

需要注意的是，这里的路径用的是不带 `-flat` 的 vmdk，因为这个文件记录了 metadata，而 `-flat.vmdk` 保存了实际的数据。可以用 `du` 命令看实际的硬盘占用，从而确认它确实是 Thin Provisioned。

如果已经在 Web UI 上复制了，你会发现无法停止复制，解决办法是：

```shell
/etc/init.d/hostd restart
```

这样就会重启 Web UI，不过等它恢复需要很长的时间，还要删掉 cookie。

## 手动分区并创建 datastore

有时候在 ESXi Web UI 上会发现创建 Datastore 的按钮是灰的，但是又想创建 datastore，可以通过 SSH 进去手动分区并创建 datastore：

1. 重新创建 GPT 分区表：`partedUtil mklabel /dev/disks/<DISK> gpt`
2. 创建 VMFS 分区表：`partedUtil add /dev/disks/<DISK> gpt "<PARTITION NUMBER> <START SECTOR> <END SECTOR> AA31E02A400F11DB9590000C2911D1B8 0"`
3. 创建 datastore：`vmkfstools -C vmfs6 -S <NAME> <DISK>:<PARTITION NUMBER>`

参考：[Using partedUtil command line disk partitioning utility on ESXi](https://knowledge.broadcom.com/external/article/323144/using-partedutil-command-line-disk-parti.html) [New datastore Greyed out ](https://community.broadcom.com/vmware-cloud-foundation/discussion/new-datastore-greyed-out)
