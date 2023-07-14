---
layout: post
date: 2020-04-17
tags: [k8s,kubernetes,tencentcloud,ingress,nginx-ingress,letsencrypt,cert-manager]
categories:
    - devops
---

# 在 k8s 内用 Cert Manager 配合 Nginx Ingress Controller 配置 Let's Encrypt HTTPS 证书

上一篇博客讲了 nginx ingress 的配置，那自然第一步要配上 https。首先配置 cert-manager：

```shell
$ kubectl create namespace cert-manager
$ kubectl apply --validate=false -f https://github.com/jetstack/cert-manager/releases/download/v0.14.1/cert-manager.crds.yaml
$ helm repo add jetstack https://charts.jetstack.io
$ helm repo update
$ helm install \
  cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --version v0.14.1

```

然后，配置 Cluster Issuer，应用以下的 yaml：

```yml
apiVersion: cert-manager.io/v1alpha2
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
  namespace: cert-manager
spec:
  acme:
    email: example@example.com
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

然后在 ingress 里面进行配置：

```yml
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: ingress-example
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - example.com
    secretName: example-tls
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        backend:
          serviceName: example-service
          servicePort: 80
```

应用以后，用 `kubectl describe certificate` 查看证书获取进度。成功后，访问改域名的 HTTP，就会自动跳转到 HTTPS，并且提供了正确的证书。