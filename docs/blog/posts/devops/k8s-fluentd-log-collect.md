---
layout: post
date: 2021-04-02
tags: [k8s,kubernetes,fluentd,logging]
categories:
    - devops
---

# 用 fluentd 收集 k8s 中容器的日志

## 背景

在维护一个 k8s 集群的时候，一个很常见的需求就是把日志持久化存下来，一方面是方便日后回溯，一方面也是聚合 replicate 出来的同一个服务的日志。

在我目前的需求下，只需要把日志持久下来，还不需要做额外的分析。所以我并没有部署类似 ElasticSearch 的服务来对日志进行索引。

## 实现

实现主要参考官方的仓库：https://github.com/fluent/fluentd-kubernetes-daemonset。它把一些常用的插件打包到 docker 镜像中，然后提供了一些默认的设置，比如获取 k8s 日志和 pod 日志等等。为了达到我的需求，我希望：

1. 每个结点上有一个 fluentd 收集日志，forward 到单独的 log server 上的 fluentd
2. log server 上的 fluentd 把收到的日志保存到文件

由于 log server 不由 k8s 管理，所以按照[官网](https://docs.fluentd.org/installation/install-by-deb)的方式手动安装：

```shell
curl -fsSL https://toolbelt.treasuredata.com/sh/install-debian-bookworm-fluent-package5.sh | sh
```

然后，编辑配置 `/etc/td-agent/td-agent.conf`：

```shell
<source>
  @type forward
  @id input_forward
  bind x.x.x.x
</source>

<match **>
  @type file
  path /var/log/fluentd/k8s
  compress gzip
  <buffer>
    timekey 1d
    timekey_use_utc true
    timekey_wait 10m
  </buffer>
</match>
```

分别设置输入：监听 fluentd forward 协议；输出：设置输出文件，和 buffer 配置。如有需要，可以加鉴权。

接着，按照 https://github.com/fluent/fluentd-kubernetes-daemonset/blob/master/fluentd-daemonset-forward.yaml，我做了一些修改，得到了下面的配置：

```yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: fluentd
  namespace: kube-system

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: fluentd
  namespace: kube-system
rules:
- apiGroups:
  - ""
  resources:
  - pods
  - namespaces
  verbs:
  - get
  - list
  - watch

---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: fluentd
roleRef:
  kind: ClusterRole
  name: fluentd
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: fluentd
  namespace: kube-system

---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: kube-system
  labels:
    k8s-app: fluentd-logging
    version: v1
spec:
  selector:
    matchLabels:
      k8s-app: fluentd-logging
      version: v1
  template:
    metadata:
      labels:
        k8s-app: fluentd-logging
        version: v1
    spec:
      serviceAccount: fluentd
      serviceAccountName: fluentd
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      containers:
      - name: fluentd
        image: fluent/fluentd-kubernetes-daemonset:v1-debian-forward
        env:
          - name: FLUENT_FOWARD_HOST
            value: "x.x.x.x"
          - name: FLUENT_FOWARD_PORT
            value: "24224"
          - name: FLUENTD_SYSTEMD_CONF
            value: "disable"
        resources:
          limits:
            memory: 200Mi
          requests:
            cpu: 100m
            memory: 200Mi
        volumeMounts:
        - name: config-volume
          mountPath: /fluentd/etc/tail_container_parse.conf
          subPath: tail_container_parse.conf
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
      terminationGracePeriodSeconds: 30
      volumes:
      - name: config-volume
        configMap:
          name: fluentd-config
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: kube-system
data:
  tail_container_parse.conf: |-
    <parse>
      @type cri
    </parse>
```

和原版有几点细节上的不同：

1. k8s 启用了 rbac，所以需要对应的配置；照着仓库里其他带 rbac 配置的文件抄一下即可。
2. 禁用了 SYSTEMD 日志的抓取，因为我用的是 k3s，而不是 kubeadm，自然找不到 kubelet 的 systemd service。
3. 覆盖了 container 日志的读取，因为使用的 container runtime 日志格式和默认的不同，这部分设置在仓库的 README 中也有提到。

部署到 k8s 中即可。为了保证日志的准确性，建议各个结点都保持 NTP 的同步。
