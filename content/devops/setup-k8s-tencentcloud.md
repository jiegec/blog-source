---
layout: post
date: 2020-03-17 21:56:00 +0800
tags: [k8s,kubernetes,tencentcloud,dashboard]
category: devops
title: 体验 Tencent Kubernetes Engine
---

之前在机器上试验了一下 kubernetes，感觉挺不错的，所以就想把腾讯云上面的机器也交给 kubernetes 管理。找到容器服务，新建集群，选择模板里的标准托管集群就可以了。然后开启下面的公网访问，设置一个比较小的 IP 地址段，按照页面下面的要求合并一下 kube config（因为还有别的 k8s cluster）：

```bash
$ KUBECONFIG=~/.kube/config:/path/to/new/config kubectl config view --merge --flatten > new_config
$ cp new_config ~/.kube/config
```

覆盖之前先确认原来的配置还在，然后就可以用 kubectl 切换到新的 context：

```bash
$ kubectl config get-contexts
$ kubectl config use-context new-context-here
$ kubectl get node
NAME          STATUS   ROLES    AGE   VERSION
172.21.0.17   Ready    <none>   75m   v1.16.3-tke.3
```

可以看到我们的 k8s node 已经上线了。我一般习惯先配好 kubernetes-dashboard：

```bash
$ kubectl create -f https://raw.githubusercontent.com/cilium/cilium/v1.6/install/kubernetes/quick-install.yaml
$ kubectl proxy &
$ kubectl -n kubernetes-dashboard describe secret (kubectl -n kubernetes-dashboard get secret | grep admin-user | awk '{print \$1}') | tail -n1 | awk '{print \$2}' | pbcopy
```

然后在浏览器里访问 http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#/overview?namespace=default 然后把剪贴板里的 token 粘贴进去即可。

默认情况下 kubernetes-dashboard 的权限比较少，可以让它获得更多权限：

```bash
$ kubectl edit clusterrole.rbac.authorization.k8s.io/kubernetes-dashboard
# use '*' for ultimate 
# use `kubectl get clusterrole.rbac.authorization.k8s.io/cluster-admin -o yaml` to see full permissions
```

接下来配置 metrics-server。下载 metrics-server 仓库，然后修改镜像地址：

```bash
$ wget https://github.com/kubernetes-sigs/metrics-server/archive/v0.3.6.zip
$ unar v0.3.6.zip
$ cd metrics-server-0.3.6/deploy/1.8+
$ vim metrics-server-deployment
# change: k8s.gcr.io/metrics-server-amd64:v0.3.6
# to: registry.cn-hangzhou.aliyuncs.com/google_containers/metrics-server-amd64:v0.3.6
# add line below image: args: ["--kubelet-insecure-tls"]
$ kubectl apply -f .
```

等一段时间，就可以看到 metrics server 正常运行了。

参考：https://tencentcloudcontainerteam.github.io/tke-handbook/