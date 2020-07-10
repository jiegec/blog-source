---
layout: post
date: 2020-07-10 09:24:00 +0800
tags: [k8s,kubernetes,tencentcloud,prometheus,helm]
category: devops
title: 在 k8s 中部署 Prometheus
---

实验了一下在 k8s 中部署 Prometheus，因为它和 k8s 有比较好的集成，很多 App 能在 k8s 里通过 service discovery 被 Prometheus 找到并且抓取数据。实践了一下，其实很简单。

用 helm 进行配置：

```shell
helm upgrade --install prometheus stable/prometheus
```

这样就可以了，如果已经有 StorageClass （比如腾讯云的话，CBS 和 CFS），它就能自己起来了，然后在 Lens 里面也可以看到各种 metrics 的可视化。

如果是自建的单结点的 k8s 集群，那么还需要自己创造 PV，并且把 PVC 绑定上去。我采用的是 local 类型的 PV：

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-volume-1
  labels:
    type: local
spec:
  storageClassName: manual
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/srv/k8s-data-1"

---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-volume-2
  labels:
    type: local
spec:
  storageClassName: manual
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/srv/k8s-data-2"
```

这样，结点上的两个路径分别对应两个 PV，然后只要让 PVC 也用 manual 的 StorageClass 就可以了：

```yaml
server:
    persistentVolume:
        storageClass: manual

alertmanager:
    persistentVolume:
        storageClass: manual
```

把这个文件保存为 values.yaml 然后：

```bash
helm upgrade --install prometheus stable/prometheus -f values.yaml
```

这样就可以了。不过 PVC 不能在线改，可能需要删掉重来。

然后，由于权限问题，还需要在结点上修改一下两个目录的权限：

```bash
sudo chown -R 65534:65534 /srv/k8s-data-1
sudo chown -R 65534:65534 /srv/k8s-data-2
```

这样容器内就可以正常访问了。