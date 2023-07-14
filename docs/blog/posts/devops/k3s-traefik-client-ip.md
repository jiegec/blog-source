---
layout: post
date: 2022-02-22
tags: [k8s,k3s,kubernetes,traefik,proxy]
categories:
    - devops
title: 解决 k3s 中 traefik 不会转发 X-Forwarded-For 等头部的问题
---

## 背景

把应用迁移到 k3s 中，然后用了 traefik 作为 Ingress Controller，发现无法获得真实的用户 IP 地址，而是 cni 内部的地址。搜索了一番，找到了靠谱的解决方案：

[Traefik Kubernetes Ingress and X-Forwarded-Headers](https://medium.com/@_jonas/traefik-kubernetes-ingresse-x-forwarded-headers-82194d319b0e)

具体来说，需要给 traefik 传额外的参数，方法是在 k3s 的配置目录下，添加一个 HelmChartConfig：

```shell
# edit /var/lib/rancher/k3s/server/manifests/traefik-config.yaml
# content:
apiVersion: helm.cattle.io/v1
kind: HelmChartConfig
metadata:
  name: traefik
  namespace: kube-system
spec:
  valuesContent: |-
    additionalArguments:
      - "--entryPoints.web.proxyProtocol.insecure"
      - "--entryPoints.web.forwardedHeaders.insecure"
```

这样相当于让 traefik 信任前一级代理传过来的这些头部。更精细的话，还可以设置信任的 IP 地址范围，不过如果 traefik 不会直接暴露出去，就不用考虑这个问题了。