---
layout: post
date: 2021-03-12
tags: [k8s,k3s,kubernetes]
categories:
    - devops
---

# 用 k3s 部署 k8s

## 背景

最近需要部署一个 k8s 集群，觉得之前配置 kubeadm 太繁琐了，想要找一个简单的。比较了一下 k0s 和 k3s，最后选择了 k3s。

## 配置

k3s 的好处就是配置十分简单：https://rancher.com/docs/k3s/latest/en/quick-start/。不需要装 docker，也不需要装 kubeadm。

1. 在第一个 node 上跑：`curl -sfL https://get.k3s.io | sh -`
2. 在第一个 node 上获取 token：`cat /var/lib/rancher/k3s/server/node-token`
3. 在其他 node 上跑：`curl -sfL https://get.k3s.io | K3S_URL=https://myserver:6443 K3S_TOKEN=mynodetoken sh -`

然后就搞定了。从第一个 node 的 `/etc/rancher/k3s/k3s.yaml` 获取 `kubectl` 配置。

## 给 api server 添加额外的 TLS SAN

默认情况下，k3s 的 api server 的 TLS 证书的 SAN 比较有限，如果在外面套了一层端口转发，那么就会导致 IP 地址和 TLS 证书对不上的情况。解决办法：

1. 运行 `kubectl edit secrets -n kube-system k3s-serving`，在 `metadata.annotations` 下创建条目：`listener.cattle.io/cn-x.x.x.x: x.x.x.x`，意思是把 `x.x.x.x` 地址添加到 TLS SAN 当中
2. 运行 `k3s certificate rotate`，重新生成 TLS 证书
3. 运行 `systemctl restart k3s`，重启 k3s

这样就可以了。

参考：

- [How to add a domain to k3s certificate](https://serverfault.com/questions/1152961/how-to-add-a-domain-to-k3s-certificate)
- [k3s certificate](https://docs.k3s.io/cli/certificate)
