---
layout: post
date: 2020-04-21 18:10:00 +0800
tags: [k8s,kubernetes,tencentcloud,drone,ci]
category: devops
title: 在 k8s 中部署 Drone 用于 CI
---

实验了一下在 k8s 中部署 CI，在 drone gitlab-ci 和 jenkins 三者中选择了 drone，因为它比较轻量，并且基于 docker，可以用 GitHub 上的仓库，比较方便。

首先，配置 helm：

```shell
helm repo add drone https://charts.drone.io
kubectl create ns drone
```

参考 drone 的文档，编写 drone-values.yml:

```yaml
ingress:
  enabled: true
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: drone.example.com
      paths:
        - "/"
  tls:
  - hosts:
    - drone.example.com
    secretName: drone-tls
env:
  DRONE_SERVER_HOST: drone.example.com
  DRONE_SERVER_PROTO: https
  DRONE_USER_CREATE: username:YOUR_GITHUB_USERNAME,admin:true
  DRONE_USER_FILTER: YOUR_GITHUB_USERNAME
  DRONE_RPC_SECRET: REDACTED
  DRONE_GITHUB_CLIENT_ID: REDACTED
  DRONE_GITHUB_CLIENT_SECRET: REDACTED
```

需要首先去 GitHub 上配置 OAuth application，具体参考 drone 的文档。然后，生成一个 secret，设置 admin 用户并只允许 admin 用户使用 drone，防止其他人使用。然后应用：

```shell
helm install --namespace drone drone drone/drone -f drone-values.yml
# or, to upgrade
helm upgrade --namespace drone drone drone/drone --values drone-values.yml 
```

然后就可以访问上面配好的域名了。遇到了 cert manager 最近的一个 bug，来回折腾几次就好了。

接着配 drone 的 k8s runnner，也是参考 drone 的文档，编写 drone-runner-kube-values.yml：

```yml
rbac:
  buildNamespaces:
    - drone
env:
  DRONE_RPC_SECRET: REDACTED
  DRONE_NAMESPACE_DEFAULT: drone
```

然后应用：

```shell
helm install --namespace drone drone-runner-kube drone/drone-runner-kube -f drone-runner-kube-values.yml
```

然后就可以去 drone 界面上操作了。

需要注意的是，drone 需要 pv，所以我先在腾讯云里面配置了 CFS 的 storage class，然后它就会自动 provision 一个新的 pv 和 pvc 出来。

接着尝试了一下在 drone 里面构建 docker 镜像并且 push 到 registry 上。以腾讯云为例：

```yml
kind: pipeline
type: kubernetes
name: default

steps:
- name: build
  image: alpine
  commands:
  - make

- name: publish
  image: plugins/docker
  settings:
    registry: ccr.ccs.tencentyun.com
    repo: ccr.ccs.tencentyun.com/abc/def
    tags: ["${DRONE_COMMIT_SHA:0:7}","latest"]
    username:
      from_secret: docker_username
    password:
      from_secret: docker_password
```

然后在网页里配置好 docker username 和 password，它就会自动构建 docker 镜像并且 push 到 registry 上，然后再 rollout 一下 deployment 就能部署最新的 image 了。实际上可以在 drone 里面把部署这一步也完成，但目前还没有去实践。



参考文档：

[Drone provider: GitHub](provider)

[Drone helm chart](https://github.com/drone/charts/blob/master/charts/drone/docs/install.md)

[Drone runner kube helm chat](https://github.com/drone/charts/blob/master/charts/drone-runner-kube/docs/install.md)

[Building a CD pipeline with drone CI and kubernetes](https://www.magalix.com/blog/building-a-cd-pipeline-with-drone-ci-and-kubernetes)