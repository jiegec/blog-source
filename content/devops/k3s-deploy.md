---
layout: post
date: 2021-03-12 00:41:00 +0800
tags: [k8s,k3s,kubernetes]
category: devops
title: 用 k3s 部署 k8s
---

## 背景

最近需要部署一个 k8s 集群，觉得之前配置 kubeadm 太繁琐了，想要找一个简单的。比较了一下 k0s 和 k3s，最后选择了 k3s。

## 配置

k3s 的好处就是配置十分简单：https://rancher.com/docs/k3s/latest/en/quick-start/。不需要装 docker，也不需要装 kubeadm。

1. 在第一个 node 上跑：`curl -sfL https://get.k3s.io | sh -`
2. 在第一个 node 上获取 token：`cat /var/lib/rancher/k3s/server/node-token`
3. 在其他 node 上跑：`curl -sfL https://get.k3s.io | K3S_URL=https://myserver:6443 K3S_TOKEN=mynodetoken sh -`

然后就搞定了。从第一个 node 的 `/etc/rancher/k3s/k3s.yaml`获取 `kubectl` 配置。
