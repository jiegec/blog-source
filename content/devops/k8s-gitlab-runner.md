---
layout: post
date: 2020-03-14 23:05:00 +0800
tags: [k8s,kubernetes,gitlab,gitlab-runner]
category: devops
title: 在 Kubernetes 集群上部署 gitlab—runner
---

按照 GitLab 上的教程试着把 gitlab-runner 部署到 k8s 集群上，发现异常地简单，所以简单做个笔记：

编辑 `values.yaml`

```yml
gitlabUrl: GITLAB_URL
runnerRegistrationToken: "REDACTED"
rbac:
    create: true
```

此处的信息按照 "Set up a specific Runner manually" 下面的提示填写。然后用 Helm 进行安装：

```bash
$ helm repo add gitlab https://charts.gitlab.io
$ kubectl create namespace gitlab-runner
$ helm install --namespace gitlab-runner gitlab-runner -f values.yaml gitlab/gitlab-runner
```

然后去 Kubernetes Dashboard 就可以看到部署的情况，回到 GitLab 也可以看到出现了 “Runners activated for this project” ，表示配置成功。