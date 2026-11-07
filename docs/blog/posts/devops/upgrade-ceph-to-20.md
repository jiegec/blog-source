---
layout: post
date: 2026-11-07
tags: [rook,ceph]
categories:
    - devops
---

# 升级 Ceph 集群到 20 Tentacle 版本

## 背景

之前一直用 Cephadm 维护了一个 Ceph 集群，作为一个 K8s 集群的存储，通过 Rook External Ceph Cluster 来维护。Ceph 出了一个比较严重的 [CVE-2025-30156](https://docs.ceph.com/en/latest/security/CVE-2025-30156/)，需要把已有的 key 都 rotate 一遍，这里把这个过程记录一下。

<!-- more -->

## 升级过程

最开始的时候，Ceph 版本是 19.2.3，Rook 版本是 1.18.11，此时这个 Ceph 版本是有安全问题的，需要升级，核心就是上面的那个 CVE：原来的认证用的是 aes 算法，无论是客户端还是 Ceph 自己的各服务。但是，这个算法的实现有安全问题，居然用固定的 IV，还是 AES-128-CBC，所以需要换到新的 aes256k 上，然后把原来的 key 都淘汰掉。Ceph 的各服务和 Rook 自己的客户端都好说，升级版本以后，就可以替换为新的 key，麻烦的是，很多 CephFS 是通过 Linux 内核挂载的，而 Linux 内核直到 7.0 才支持 aes256k。旧版本内核，如果指定 aes256k 的 secret，会说 secret length 错误，无法挂载。

所以第一步，就是给各虚拟机都升级到了 7.0 的内核：trixie 和 trixie-security 都不够新，所以就用了 trixie-backports 的 7.2 内核。

升级完 Linux 内核后，就可以开始动手升级 Ceph 了，首先用 cephadm 升级 Ceph 到 20.2.5：

```shell
ceph orch upgrade start --image quay.io/ceph/ceph:v20.2.5
```

经过一段时间的等待，Ceph 的各服务都升级到了 20.2.5，并且 Cephadm 自动把服务用到的各种 key 都替换成了 aes256k。但是，还是有一些 key 需要手动操作，比如 client.admin。参考 [Upgrading and Rotating CephX Keys](https://docs.ceph.com/en/latest/rados/configuration/auth-config-ref/#cephx-upgrade)，把 client.admin 的 key 给 rotate 掉：

```shell
ceph mon set auth_allowed_ciphers aes,aes256k
ceph mon set auth_preferred_cipher aes256k
ceph auth get-or-create client.admin-backup mon "allow *" | tee ./client.admin-backup.keyring
ceph -n client.admin-backup -k ./client.admin-backup.keyring auth ls
ceph auth rotate --key-type=aes256k client.admin | tee ./client.admin.keyring
```

对于 Cephadm，修改一台机器上的 `/etc/ceph/ceph.client.admin.keyring`，把里面的 admin key 换了，然后分发到其他机器上：

```shell
ceph orch client-keyring set client.admin "label:_admin"
```

剩下的需要 Rotate 的 key，就都是 Rook 需要的了：

- client.csi-cephfs-node
- client.csi-cephfs-provisioner
- client.csi-rbd-node
- client.csi-rbd-provisioner
- client.healthchecker

这些 Key 都保存在 rook ceph 用于 external cluster 的 namespace 里的各 secret，根据名字很容易找到。我把 Rook 升级到 v1.21.2 后，直接在 Headlamp 里手动做的替换，虽然官方也给了脚本，但是脚本有一些依赖装起来比较麻烦，有 APT 的依赖问题。以 client.csi-cephfs-node 为例，其实就是：

```shell
ceph auth rotate --key-type=aes256k client.csi-cephfs-node
```

然后把新的 key，替换掉 rook-csi-cephfs-node Secret 里面的 adminKey。其他几个也是类似的。

把所有的 key 都 rotate 成 aes256k 后（通过看 key 的长度能看出是 aes 还是 aes256k），禁用旧的 aes key 的使用：

```shell
ceph config set mon 'mon auth allow insecure key' false
ceph mon set auth_service_cipher aes256k
ceph auth wipe-rotating-service-keys
ceph mon set auth_allowed_ciphers aes256k
```

最后，ceph health 没有任何关于 insecure key 的 warning，就算迁移完成。

## 参考文档

- [Upgrading and Rotating CephX Keys](https://docs.ceph.com/en/latest/rados/configuration/auth-config-ref/#cephx-upgrade)
- [CVE-2025-30156: AES-CBC misuse in CephX facilitating authentication bypass](https://docs.ceph.com/en/latest/security/CVE-2025-30156/)
- [Ceph CVE notice and Rook advisory](https://github.com/rook/rook/issues/18203)
