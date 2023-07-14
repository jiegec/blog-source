---
layout: post
date: 2022-07-16
tags: [ceph]
category: devops
title: Ceph Cookbook
---

## 概念

- OSD：负责操作硬盘的程序，一个硬盘一个 OSD
- MON：管理集群状态，比较重要，可以在多个节点上各跑一个
- MGR：监测集群状态
- RGW(optional)：提供对象存储 API
- MDS(optional)：提供 CephFS

使用 Ceph 做存储的方式：

1. librados: 库
2. radosgw: 对象存储 HTTP API
3. rbd: 块存储
4. cephfs: 文件系统

## 认证

Ceph 客户端认证需要用户名 + 密钥。默认情况下，用户名是 `client.admin`，密钥路径是 `/etc/ceph/ceph.用户名.keyring`。`ceph --user abc` 表示以用户 `client.abc` 的身份访问集群。

用户的权限是按照服务类型决定的。可以用 `ceph auth ls` 显示所有的用户以及权限：

```shell
$ ceph auth ls
osd.0
        key: REDACTED
        caps: [mgr] allow profile osd
        caps: [mon] allow profile osd
        caps: [osd] allow *
client.admin
        key: REDACTED
        caps: [mds] allow *
        caps: [mgr] allow *
        caps: [mon] allow *
        caps: [osd] allow *
```

可以看到，`osd.0` 对 OSD 有所有权限，对 mgr 和 mon 都只有 osd 相关功能的权限；`client.admin` 有所有权限。`profile` 可以认为是预定义的一些权限集合。

新建用户并赋予权限：

```shell
ceph auth get-or-create client.abc mon 'allow r'
```

修改权限：

```shell
ceph auth caps client.abc mon 'allow rw'
```

获取权限：

```shell
ceph auth get client.abc
```

删除用户：

```shell
ceph auth print-key client.abc
```

## OSD

管理 OSD 实际上就是管理存储数据的硬盘。

查看状态：

```shell
ceph osd stat
```

显示有多少个在线和离线的 OSD。

```shell
ceph osd tree
```

显示了存储的层级，其中 ID 非负数是实际的 OSD，负数是其他层级，例如存储池，机柜，主机等等。

## CRUSH

CRUSH 是一个算法，指定了如何给 PG 分配 OSD，到什么类型的设备，确定它的 failure domain 等等。例如，如果指定 failure domain 为 host，那么它就会分配到不同 host 上的 osd，这样一个 host 挂了不至于全军覆没。类似地，还可以设定更多级别的 failure domain，例如 row，rack，chassis 等等。

OSD 可以设置它的 CRUSH Location，在 ceph.conf 中定义。

为了配置数据置放的规则，需要设置 CRUSH Rule。

列举 CRUSH Rule：

```shell
ceph osd crush rule ls
ceph osd crush rule dump
```

查看 CRUSH 层级：

```shell
ceph osd crush tree --show-shadow
```

在里面可能会看到 `default~ssd`，它指的意思就是只保留 default 下面的 ssd 设备。

文本形式导出 CRUSH 配置：

```shell
ceph osd getcrushmap | crushtool -d - -o crushmap
cat crushmap
```

可以看到 Rule 的定义，如：

```
# simple replicated
rule replicated_rule {
        id 0
        # a replicated rule
        type replicated
        # iterate all devices of "default"
        step take default
        # select n osd with failure domain "osd"
        # firstn: continuous
        step chooseleaf firstn 0 type osd
        step emit
}

# erasure on hdd
rule erasure-hdd {
        id 4
        # an erasure rule
        type erasure
        # try more times to find a good mapping
        step set_chooseleaf_tries 5
        step set_choose_tries 100
        # iterate hdd devices of "default", i.e. "default~hdd"
        step take default class hdd
        # select n osd with failure domain "osd"
        # indep: replace failed osd with another
        step choose indep 0 type osd
        step emit
}

# replicated on hdd
rule replicated-hdd-osd {
        id 5
        # a replicated rule
        type replicated
        # iterate hdd devices of "default", i.e. "default~hdd"
        step take default class hdd
        # select n osd with failure domain "osd"
        # firstn: continuous
        step choose firstn 0 type osd
        step emit
}

# replicated on different hosts
rule replicated-host {
        id 6
        # a replicated rule
        type replicated
        # iterate all devices of "default"
        step take default
        # select n osd with failure domain "host"
        # firstn: continuous
        step chooseleaf firstn 0 type host
        step emit
}

# replicate one on ssd, two on hdd
rule replicated-ssd-primary {
        id 7
        # a replicated rule
        type replicated

        # iterate ssd devices of "default"
        step take default class ssd
        step chooseleaf firstn 1 type host
        step emit

        # iterate hdd devices of "default"
        step take default class hdd
        step chooseleaf firstn 2 type host
        step emit
}
```

choose 和 chooseleaf 的区别是，前者可以 choose 到中间层级，例如先选择 host，再在 host 里面选 osd；而 chooseleaf 是直接找到 osd。所以 `choose type osd` 和 `chooseleaf type osd` 是等价的。

如果这个搜索条件比较复杂，例如找到了某一个 host，里面的 osd 个数不够，就需要重新搜。

新建一个 Replicated CRUSH Rule：

```shell
# root=default, failure domain=osd
ceph osd crush rule create-replicated xxx default osd
# root=default, failure domain=host, class=ssd
ceph osd crush rule create-replicated yyy default host ssd
```

如果指定了 device class，它只会在对应类型的设备上存储。

## Pool

Pool 是存储池，后续的 RBD/CephFS 功能都需要指定存储池来工作。

创建存储池：

```shell
ceph osd pool create xxx
ceph osd pool create PG_NUM
```

为了性能考虑，可以设置 PG（Placement Group）数量。默认情况下，会创建 replicated 类型的存储池，也就是会存多份，类似 RAID1。也可以设置成 erasure 类型的存储池，类似 RAID5。

每个 Placement Group 里的数据会保存在同一组 OSD 中。数据通过 hash，会分布在不同的 PG 里。

列举所有的存储池：

```shell
ceph osd lspools
```

查看存储池的使用量：

```shell
rados df
```

存储池的 IO 状态：

```shell
ceph osd pool stats
```

对存储池做快照：

```shell
ceph osd mksnap xxx snap-xxx-123
```

### PG

PG 是数据存放的组，每个对象都会放到一个 PG 里面，而 PG 会决定它保存到哪些 OSD 上（具体哪些 OSD 是由 CRUSH 决定的）。PG 数量只有一个的话，那么一个 pool 的所有数据都会存放在某几个 OSD 中，一旦这几个 OSD 都不工作了，那么整个 pool 的数据都不能访问了。PG 增多了以后，就会分布到不同的 OSD 上，并且各个 OSD 的占用也会比较均匀。

查看 PG 状态：

```shell
ceph pg dump
```

#### Auto Scale

PG 数量可以让集群自动调整：

```shell
ceph osd pool set xxx pg_autoscale_mode on
```

设置 autoscale 目标为每个 OSD 平均 100 个 PG：

```shell
ceph config set global mon_target_pg_per_osd 100
```

全局 autoscale 开关：

```shell
# Enable
ceph osd pool unset noautoscale
# Disable
ceph osd pool set unautoscale
# Read
ceph osd pool get noautoscale
```

查看 autoscale 状态：

```shell
ceph osd pool autoscale-status
```

如果没有显示，说明 autoscale 没有工作，可能的原因是，部分 pool 采用了指定 osd class 的 crush rule，例如指定了 hdd 盘，但是也有部分 pool 没有指定盘的类型，例如默认的 replicated_rule。这时候，把这些盘也设置成一个指定 osd class 的 crush rule 即可。

## RBD

RBD 把 Ceph 暴露为块设备。

### 创建

初始化 Pool 用于 RBD：

```shell
rbd pool init xxx
```

为了安全性考虑，一般会为 RBD 用户创建单独的用户：

```shell
ceph auth get-or-create client.abc mon 'profile rbd' osd 'profile rbd pool=xxx' mgr 'profile rbd pool=xxx'
```

创建 RBD 镜像：

```shell
rbd create --size 1024 xxx/yyy
```

表示在 Pool xxx 上面创建了一个名字为 yyy 大小为 1024MB 的镜像。

### 状态

列举 Pool 里的镜像：

```shell
rbd ls
rbd ls xxx
```

默认的 Pool 名字是 `rbd`。

查看镜像信息：

```shell
rbd info yyy
rbd info xxx/yyy
```

### 扩容

修改镜像的容量：

```shell
rbd resize --size 2048 yyy
rbd resize --size 512 yyy --allow-shrink
```

### 挂载

在其他机器挂载 RBD 的时候，首先要修改 `/etc/ceph` 下配置，确认有用户，密钥和 MON 的地址。

然后，用 rbd 挂载设备：

```shell
rbd device map xxx/yyy --id abc
```

以用户 abc 的身份挂载 Pool xxx 下面的 yyy 镜像。

这时候就可以在 `/dev/rbd*` 或者 `/dev/rbd/` 下面看到设备文件了。

显示已经挂载的设备：

```shell
rbd device list
```

## CephFS

### 创建

如果配置了编排器（Orchestrator），可以直接用命令：

```shell
ceph fs volume create xxx
```
创建一个名为 `xxx` 的 CephFS。

也可以手动创建：

```
ceph osd pool create xxx_data0
ceph osd pool create xxx_metadata
ceph fs new xxx xxx_metadata xxx_data0
```

这样就创建了两个 pool，分别用于存储元数据和文件数据。一个 CephFS 需要一个 pool 保存元数据，若干个 pool 保存文件数据。

创建了 CephFS 以后，相应的 MDS 也会启动。

### 状态

查看 MDS 状态：

```
ceph mds stat
```

### 客户端配置

在挂载 CephFS 之前，首先要配置客户端。

在集群里运行 `ceph config generate-minimal-conf`，它会生成一个配置文件：

```shell
$ ceph config generate-minimal-conf
# minimal ceph.conf for <fsid>
[global]
        fsid = <fsid>
        mon_host = [v2:x.x.x.x:3300/0,v1:x.x.x.x:6789/0]
```

把内容复制到客户端的 `/etc/ceph/ceph.conf`。这样客户端就能找到集群的 MON 地址和 FSID。

接着，我们在集群上给客户端创建一个用户：

```
ceph fs authorize xxx client.abc / rw
```

创建一个用户 abc，对 CephFS xxx 有读写的权限。把输出保存到客户端的 `/etc/ceph/ceph.client.abc.keyring` 即可。

### 挂载

挂载：

```shell
mount -t ceph abc@.xxx=/ MOUNTPOINT
# or
mount -t ceph abc@<fsid>.xxx=/ MOUNTPOINT
# or
mount -t ceph abc@<fsid>.xxx=/ -o mon_addr=x.x.x.x:6789,secret=REDACTED MOUNTPOINT
#or
mount -t ceph abc@.xxx=/ -o mon_addr=x.x.x.x:6789/y.y.y.y:6789,secretfile=/etc/ceph/xxx.secret MOUNTPOINT
# or
mount -t ceph -o name=client.abc,secret=REDACTED,mds_namespace=xxx MON_IP:/ MOUNTPOINT
```

以用户 `client.abc` 的身份登录，挂载 CepFS `xxx` 下面的 `/` 目录到 `MOUNTPOINT`。它会读取 `/etc/ceph` 下面的配置，如果已经 `ceph.conf` 写了，命令行里就可以不写。

fsid 指的不是 CephFS 的 ID，实际上是集群的 ID：`ceph fsid`。

### 限额

CephFS 可以对目录进行限额：

```shell
setfattr -n ceph.quota.max_bytes -v LIMIT PATH
setfattr -n ceph.quota.max_files -v LIMIT PATH
getfattr -n ceph.quota.max_bytes PATH
getfattr -n ceph.quota.max_files PATH
```

限制目录大小和文件数量。LIMIT 是 0 的时候表示没有限制。

### NFS

可以把 CephFS 或者 RGW 通过 NFS 的方式共享出去。

启动 NFS 服务：

```shell
ceph nfs cluster create xxx
ceph nfs cluster create xxx "host1,host2"
```

在主机上运行 NFS 服务器，NFS 集群的名字叫做 xxx。

查看 NFS 集群信息：

```shell
ceph nfs cluster info xxx
```

列举所有 NFS 集群：

```shell
ceph nfs cluster ls
```

NFS 导出 CephFS：

```shell
ceph nfs export create cephfs --cluster-id xxx --pseudo-path /a/b/c --fsname some-cephfs-name [--path=/d/e/f] [--client_addr y.y.y.y]
```

这样就导出了 CephFS 内的一个目录，客户端可以通过 NFS 挂载 /a/b/c 路径（pseudo path）来访问。可以设置客户端的 IP 访问权限。

这样在客户端就可以 mount：

```shell
mount -t nfs x.x.x.x:/a/b/c /mnt
```

## RadosGW

RGW 提供了 S3 或者 OpenStack Swift 兼容的对象存储 API。

TODO

## 编排器

由于 Ceph 需要运行多个 daemon，并且都在不同的容器中运行，所以一般会跑一个系统级的编排器，用于新增和管理这些容器。

查看当前编排器：

```shell
$ ceph orch status
Backend: cephadm
Available: Yes
Paused: No
```

比较常见的就是 cephadm，安装的时候如果用了 cephadm，那么编排器也是它。

被编排的服务：

```shell
ceph orch ls
```

被编排的容器：

```shell
ceph orch ps
```

被编排的主机：

```shell
ceph orch host ls
```

### 添加新机器

首先，复制 `/etc/ceph/ceph.pub` 到新机器的 `/root/.ssh/authorized_keys` 中

接着，添加机器到编排器中：

```shell
ceph orch host add xxxx y.y.y.y
```

导出编排器配置：

```shell
ceph orch ls --export > cephadm.yaml
```

如果想让一些 daemon 只运行在部分主机上，可以修改：

```yaml
# change
placement:
  host_pattern: '*'
# to
placement:
  host_pattern: 'xxx'
```

然后应用：

```shell
ceph orch apply -i cephadm.yaml
```

### 配置监控

添加监控相关的服务：

```shell
ceph orch apply node-exporter
ceph orch apply alertmanager
ceph orch apply prometheus
ceph orch apply grafana
ceph orch ps
```

然后就可以访问 Grafana 看到集群的状态。

## 更新

使用容器编排器来升级：

```shell
ceph orch upgrade start --ceph-version x.x.x
ceph orch upgrade start --image quay.io/ceph/ceph:vx.x.x
```

如果 docker hub 上找不到 image，就从 quay.io 拉取。

查看升级状态：

```shell
ceph orch upgrade status
ceph -s
```

查看 cephadm 日志：

```shell
ceph -W cephadm
```

## 参考文档

- [Ceph Architecture](https://docs.ceph.com/en/latest/architecture/)
- [Ceph User Management](https://docs.ceph.com/en/latest/rados/operations/user-management/)
- [Ceph Create a Ceph File System](https://docs.ceph.com/en/latest/cephfs/createfs/)
- [mount.ceph](https://docs.ceph.com/en/latest/man/8/mount.ceph/)
- [Ceph CephFS Quota](https://docs.ceph.com/en/latest/cephfs/quota/)
- [Ceph Basic Block Device Commands](https://docs.ceph.com/en/latest/rbd/rados-rbd-cmds/)
- [Ceph Upgrade](https://docs.ceph.com/en/quincy/cephadm/upgrade/)
- [Ceph CephFS & RGW Exports Over NFS](https://docs.ceph.com/en/latest/mgr/nfs/)
- [CRUSH Maps](https://docs.ceph.com/en/quincy/rados/operations/crush-map/)
- [CRUSH Map Edits](https://docs.ceph.com/en/latest/rados/operations/crush-map-edits/)
- [ceph 架构和概念](https://llussy.github.io/2019/08/17/ceph-architecture/)
- [RedHat Object Gateway Guide](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/5/html/object_gateway_guide/the-ceph-object-gateway_rgw)