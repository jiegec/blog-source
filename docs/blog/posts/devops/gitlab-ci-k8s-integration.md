---
layout: post
date: 2021-03-16
tags: [k8s,kubernetes,docker,gitlab,gitlabci,ci,helm]
categories:
    - devops
---

# 用 gitlab ci 构建并部署应用到 k8s

## 背景

在 k8s 集群中部署了 gitlab-runner，并且希望在 gitlab ci 构建完成后，把新的 docker image push 到 private repo，然后更新应用。

参考文档：[Gitlab CI 与 Kubernetes 的结合](https://www.qikqiak.com/post/gitlab-ci-k8s-cluster-feature/)，[Using Docker to build Docker images](https://docs.gitlab.com/ee/ci/docker/using_docker_build.html)。

## 在 gitlab ci 中构建 docker 镜像

这一步需要 DinD 来实现在容器中构建容器。为了达到这个目的，首先要在 gitlab-runner 的配置中添加一个 volume 来共享 DinD 的证书路径：

```yaml
gitlabUrl: REDACTED
rbac:
  create: true
runnerRegistrationToken: REDACTED
runners:
  config: |
    [[runners]]
      [runners.kubernetes]
        image = "ubuntu:20.04"
        privileged = true
      [[runners.kubernetes.volumes.empty_dir]]
        name = "docker-certs"
        mount_path = "/certs/client"
        medium = "Memory"
  privileged: true
```

注意两点：1. privileged 2. 多出来的 volume

用 helm 部署 gitlab runner 之后，按照下面的方式配置 gitlab-ci：

```yml
image: docker:19.03.12

variables:
  DOCKER_HOST: tcp://docker:2376
  #
  # The 'docker' hostname is the alias of the service container as described at
  # https://docs.gitlab.com/ee/ci/docker/using_docker_images.html#accessing-the-services.
  # If you're using GitLab Runner 12.7 or earlier with the Kubernetes executor and Kubernetes 1.6 or earlier,
  # the variable must be set to tcp://localhost:2376 because of how the
  # Kubernetes executor connects services to the job container
  # DOCKER_HOST: tcp://localhost:2376
  #
  # Specify to Docker where to create the certificates, Docker will
  # create them automatically on boot, and will create
  # `/certs/client` that will be shared between the service and job
  # container, thanks to volume mount from config.toml
  DOCKER_TLS_CERTDIR: "/certs"
  # These are usually specified by the entrypoint, however the
  # Kubernetes executor doesn't run entrypoints
  # https://gitlab.com/gitlab-org/gitlab-runner/-/issues/4125
  DOCKER_TLS_VERIFY: 1
  DOCKER_CERT_PATH: "$DOCKER_TLS_CERTDIR/client"
  DOCKER_DAEMON_OPTIONS: "--insecure-registry=${REGISTRY}"

services:
  - name: docker:19.03.12-dind
    entrypoint: ["sh", "-c", "dockerd-entrypoint.sh $DOCKER_DAEMON_OPTIONS"]

before_script:
  # Wait until client certs are generated
  # https://gitlab.com/gitlab-org/gitlab-runner/-/issues/27384
  - until docker info; do sleep 1; done
  - echo "$REGISTRY_PASS" | docker login $REGISTRY --username $REGISTRY_USER --password-stdin

build:
  stage: build
  script: ./build.sh
```

这里有很多细节，包括 DinD 的访问方式，等待 client cert，设置 docker 的 insecure registry 和 login 等等。经过 [@CircuitCoder](https://github.com/CircuitCoder) 的不断摸索，终于写出了可以用的配置。

如此配置以后，就可以在 gitlab ci 的构建脚本里用 docker 来 build 并且 push 到自己的 registry 了。为了防止泄露密钥，建议把这些变量放到 gitlab ci 设置的 secrets 中。

## 自动部署到 k8s

为了让 k8s 重启一个 deployment，一般的做法是：

```
kubectl -n NAMESPACE rollout restart deployment/NAME
```

我们希望 gitlab ci 在 build 之后，去执行这一个命令，但又不希望提供太多的权限给 gitlab。所以，我们创建 Service Account 并设置最小权限：

```yml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gitlab
  namespace: default

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: gitlab-test
  namespace: test
rules:
- verbs:
    - get
    - patch
  apiGroups:
    - 'apps'
  resources:
    - 'deployments'
  resourceNames:
    - 'test-deployment'

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: gitlab
  namespace: test
subjects:
  - kind: ServiceAccount
    name: gitlab
    namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: gitlab-test
```

要特别注意这几个配置的 namespace 的对应关系：Role 和 RoleBinding 需要放在同一个 ns 下。

接着，到 GitLab 的 Operations->Kubernetes 创建 cluster，把 service account 的 token 和 ca.crt 从 secret 里找到并贴到网页上。GitLab 会按照 Environment scope 匹配到 environment，如果某个 stage 的 environment 匹配上了，就会把 kube credentials 配置好。修改 gitlab-ci.yml：

```yml
deploy:
  stage: deploy
  image: bitnami/kubectl:1.20
  environment:
    name: production
  only:
    - master
  script:
    - kubectl -n test rollout restart deployment/test
```

这样就完成配置了。