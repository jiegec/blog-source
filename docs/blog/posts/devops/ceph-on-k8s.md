---
layout: post
date: 2021-03-12
tags: [ceph,k8s,kubernetes,rook]
category: devops
title: 通过 rook 在 k8s 上部署 ceph 集群
---

## 背景

为了方便集群的使用，想在 k8s 集群里部署一个 ceph 集群。

[Ceph 介绍](https://docs.ceph.com/en/latest/start/intro/)

Ceph 有这些组成部分：

1. mon：monitor
2. mgr：manager
3. osd：storage
4. mds(optional)：用于 CephFS
5. radosgw(optional：用于 Ceph Object Storage

## 配置

我们采用的是 [rook](https://rook.io/) 来部署 ceph 集群。

参考文档：https://rook.github.io/docs/rook/v1.5/ceph-examples.html

首先，克隆 rook 的仓库。建议选择一个 release 版本。

接着，运行下面的命令：

```shell
sudo apt install -y lvm2
# required
kubectl apply -f rook/cluster/examples/kubernetes/ceph/crds.yaml
kubectl apply -f rook/cluster/examples/kubernetes/ceph/common.yaml
kubectl apply -f rook/cluster/examples/kubernetes/ceph/operator.yaml
# debugging only
kubectl apply -f rook/cluster/examples/kubernetes/ceph/toolbox.yaml
kubectl apply -f rook/cluster/examples/kubernetes/ceph/direct-mount.yaml
# CephFS
kubectl apply -f rook/cluster/examples/kubernetes/ceph/filesystem.yaml
kubectl apply -f rook/cluster/examples/kubernetes/ceph/csi/cephfs/storageclass.yaml
```

前面三个 yaml 是必须的，toolbox 是用来查看 ceph 状态的，direct mount 是用来 mount cephfs 的，后两个是为了用 cephfs 的。

接着，按照自己的需求编辑 `rook/cluster/exmaples/kuberenetes/ceph/cluster.yaml` 然后应用。此时你的集群应该就已经起来了。

然后，可以[进 toolbox 查看 ceph 状态](https://rook.github.io/docs/rook/v1.5/ceph-toolbox.html)：

```shell
$ kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- bash
```

也可以[进 direct-mount 容器查看 pv 路径](https://rook.github.io/docs/rook/v1.5/direct-tools.html)：

```shell
# get volume path of pvc
kubectl get pv -o custom-columns=NAME:.metadata.name,NAMSEPACE:.spec.claimRef.namespace,CLAIM:.spec.claimRef.name,PATH:.spec.csi.volumeAttributes.subvolumeName

kubectl -n rook-ceph exec -it deploy/rook-direct-mount -- bash
# in the pod
mkdir /tmp/registry
mon_endpoints=$(grep mon_host /etc/ceph/ceph.conf | awk '{print $3}')
my_secret=$(grep key /etc/ceph/keyring | awk '{print $3}')
mount -t ceph -o mds_namespace=myfs,name=admin,secret=$my_secret $mon_endpoints:/ /tmp/registry
df -h

cd /tmp/registry/volumes/csi/PATH
```

