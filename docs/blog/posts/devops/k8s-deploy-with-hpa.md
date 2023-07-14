---
layout: post
date: 2020-03-10
tags: [k8s,kubernetes,docker]
categories:
    - devops
title: 用 Kubernetes 部署无状态服务
---

## 背景

最近需要部署一个用来跑编译的服务，服务从 MQ 取任务，编译完以后提交任务。最初的做法是包装成 docker，然后用 docker-compose 来 scale up。但既然有 k8s 这么好的工具，就试着学习了一下，踩了很多坑，总结了一些需要用到的命令。

## 搭建 Docker Registry

首先搭建一个本地的 Docker Repository，首先设置密码：

```bash
$ mkdir auth
$ htpasswd user pass > auth/passwd
```

然后运行 registry：

```bash
$ docker run -d -p 5000:5000 \
        --restart=always \
        --name registry \
        -v "$(pwd)/registry":/var/lib/registry \
        -v "$(pwd)/auth":/auth \
        -e "REGISTRY_AUTH=htpasswd" \
        -e "REGISTRY_AUTH_HTPASSWD_REALM=Registry Realm" \
        -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
        registry:2
```

简单起见没有配 tls。然后吧本地的 image push 上去：

```bash
$ docker tag $image localhost:5000/$image
$ docker push localhost:5000/$image
```

这样就可以了。

## 搭建 k8s 环境

考虑到只用了单个物理机，所以采用的是 minikube。首先下载 minikube，下载方法略去。

接着新建 minikube 虚拟机：

```bash
$ minikube start --registry-mirror=https://registry.docker-cn.com --image-mirror-country=cn --image-repository=registry.cn-hangzhou.aliyuncs.com/google_containers --vm-driver=kvm2 --insecure-registry="0.0.0.0/0" --disk-size=50GB --cpus 128 --memory 131072
```

这里的 0.0.0.0/0 可以缩小，磁盘、CPU 和内存需要在这里就设好，之后不能改，要改只能重新开个虚拟机，不过这个过程也挺快的。

然后初始化一些组件（metrics server 和 kubernetes dashboard）：

```bash
$ minikube addons enable metrics-server
$ minikube dashboard
```

如果要访问 dashboard 的话，可以用上面命令输出的链接，或者用 `kubectl proxy` 然后打开  http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/http:kubernetes-dashboard:/proxy/ （注意 http 还是 https）。

如果问到 Access Token，可以用以下 alias 获得（fish/macOS）：

```bash
$ alias kubedashboard="kubectl -n kubernetes-dashboard describe secret (kubectl -n kubernetes-dashboard get secret | grep admin-user | awk '{print \$1}') | tail -n1 | awk '{print \$2}' | pbcopy"
```

接着，配置一下 docker registry 的密钥：

```bash
$ kubectl create secret generic regcred --from-file=.dockerconfigjson=/path/to/config.json  --type=kubernetes.io/dockerconfigjson
```

然后，在 Pod/Deployment 里面设定镜像：

```yml
containers:
  - name: name
    image: IP:5000/image
imagePullSecrets:
  - name: regcred
```

然后部署即可。

## 部署水平自动伸缩（HPA）

这一步配置的是自带的 HPA 功能，需要上述的 metrics-server 打开，并且在 Pod/Deployment 里面写明 resources.requests.cpu:

```yml
- name: name
  resources:
    requests:
      cpu: "xxx"
```

然后创建 HPA 即可：

```bash
$ kubectl autoscale deployment $deployment --cpu-percent=50 --min=1 --max=10
```

通过压测，可以看到自动伸缩的记录：

```bash
$ kubectl describe hpa
Normal  SuccessfulRescale  22s   horizontal-pod-autoscaler  New size: 4; reason: cpu resource utilization (percentage of request) above target
Normal  SuccessfulRescale  6s     horizontal-pod-autoscaler  New size: 1; reason: All metrics below target
```

参考：Kubernetes 官方文档