---
layout: post
date: 2020-04-17 17:30:00 +0800
tags: [k8s,kubernetes,tencentcloud,tke,nginx,nginx-ingress]
category: devops
title: 在 TKE 上配置不使用 LB 的 Nginx Ingress Controller
---

## 背景

想要在 k8s 里面 host 一个网站，但又不想额外花钱用 LB，想直接用节点的 IP。

## 方法

首先安装 nginx-ingress：

```shell
$ helm repo add nginx-stable https://helm.nginx.com/stable
$ helm repo update
$ helm install ingress-controller nginx-stable/nginx-ingress --set controller.service.type=NodePort --set controller.hostNetwork=true
```

这里给 ingress controller chart 传了两个参数：第一个指定 service 类型是 NodePort，替代默认的 LoadBalancer；第二个指定 ingress controller 直接在节点上监听，这样就可以用节点的公网 IP 访问了。

然后配一个 ingress：

```yml
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: ingress-example
  annotations:
    kubernetes.io/ingress.class: "nginx"
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        backend:
          serviceName: example-service
          servicePort: 80
```

然后就可以发现请求被正确路由到 example-service 的 80 端口了。