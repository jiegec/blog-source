---
layout: post
date: 2022-07-16 19:32:00 +0800
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

Ceph 客户端认证需要用户名+密钥。默认情况下，用户名是 `client.admin`，密钥路径是 `/etc/ceph/ceph.用户名.keyring`。`ceph --user abc` 表示以用户 `client.abc` 的身份访问集群。

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

## Pool

Pool 是存储池，后续的 RBD/CephFS 功能都需要指定存储池来工作。

创建存储池：

```shell
ceph osd pool create xxx
ceph osd pool create PG_NUM
```

为了性能考虑，可以设置 PG（Placement Group）数量。默认情况下，会创建 replicated 类型的存储池，也就是会存多份，类似 RAID1。也可以设置成 erasure 类型的存储池，类似 RAID5。

每个 Placement Group 里的数据会保存在同一组 OSD 中。数据通过 hash ，会分布在不同的 PG 里。

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
- [ceph 架构和概念](https://llussy.github.io/2019/08/17/ceph-architecture/)
- [RedHat Object Gateway Guide](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/5/html/object_gateway_guide/the-ceph-object-gateway_rgw)