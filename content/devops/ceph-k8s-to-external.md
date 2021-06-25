---
layout: post
date: 2021-06-25 20:29:00 +0800
tags: [k8s,ceph,rook,cephfs,cephadm]
category: devops
title: 将 k8s rook ceph 集群迁移到 cephadm
---

## 背景

前段时间用 rook 搭建了一个 k8s 内部的 ceph 集群，但是使用过程中遇到了一些稳定性问题，所以想要用 cephadm 重建一个 ceph 集群。

## 重建过程

重建的时候，我首先用 cephadm 搭建了一个 ceph 集群，再把原来的 MON 数据导入，再恢复各个 OSD。理论上，可能有更优雅的办法，但我还是慢慢通过比较复杂的办法解决了。

### cephadm 搭建 ceph 集群

首先，配置 [TUNA 源](https://mirrors.tuna.tsinghua.edu.cn/help/ceph/)，在各个节点上安装 `docker-ce` 和 `cephadm`。接着，在主节点上 bootstrap：

```shell
cephadm bootstrap --mon-ip HOST1_IP
```

此时，在主节点上会运行最基础的 ceph 集群，不过此时还没有任何数据。寻找 ceph 分区，会发现因为 FSID 不匹配而无法导入。所以，首先要恢复 MON 数据。

参考文档：[cephadm install](https://docs.ceph.com/en/latest/cephadm/install/)。

### 恢复 MON 数据

首先，关掉 rook ceph 集群，找到留存下来的 MON 数据目录，默认路径是 `/var/lib/rook` 下的 `mon-[a-z]` 目录，找到最新的一个即可。我把目录下的路径覆盖到 cephadm 生成的 MON 目录下，然后跑起来，发现有几个问题：

1. cephadm 生成的 /etc/ceph/ceph.client.admin.keyring 与 MON 中保存的 auth 信息不匹配，导致无法访问
2. FSID 不一致，而 cephadm 会将各个设置目录放到 `/var/lib/ceph/$FSID` 下

第一个问题的解决办法就是临时用 MON 目录下的 keyring 进行认证，再创建一个新的 client.admin 认证。第二个问题的解决办法就是将遇到的各种 cephadm 生成的 FSID 替换为 MON 中的 FSID，包括目录名、各个目录下 unit.run 中的路径和 systemd unit 的名称。

进行一系列替换以后，原来的 MON 已经起来了，可以看到原来保留的各个 pool 和 cephfs 信息。

### 扩展到多节点

接下来，由于 MON 中保存的数据更新了，所以要重新生成 cephadm 的 SSH 密钥。将 SSH 密钥复制到各节点后，再用 cephadm 的 orch 功能部署到其他节点上。此时 FSID 都已经是 MON 中的 FSID，不需要替换。此时可以在 `ceph orch ps` 命令中看到在各个节点上运行的程序。接下来，还需要恢复各个 OSD。

### 导入 OSD

为了从 ceph 分区从导出 OSD 的配置文件，需要用 `ceph-volume` 工具。这个工具会生成一个 `/var/lib/ceph/osd-ID` 目录，在 cephadm 的概念里属于 legacy，因此我们首先要把路径 mount 到 shell 里面：

```shell
$ cephadm shell --mount /var/lib/ceph:/var/lib/ceph
```

接着，生成 osd 目录配置：

```shell
$ ceph-volume lvm activate --all --no-systemd
```

然后，可以看到创建了对应的 osd 路径，再用 cephadm 进行转换：

```shell
$ cephadm adopt --style legacy --name osd.ID
```

这样就可以用 cephadm 管理了。