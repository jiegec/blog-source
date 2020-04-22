---
layout: post
date: 2020-04-22 19:02:00 +0800
tags: [k8s,kubernetes,tencentcloud,vscode,code-server]
category: devops
title: 在 k8s 中部署 code-server
---

实验了一下在 k8s 中部署 [code-server](https://github.com/cdr/code-server)，并不复杂，和之前几篇博客的配置是类似的：

```yaml
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: code
  labels:
    app: code
spec:
  selector:
    matchLabels:
      app: code
  replicas: 1
  template:
    metadata:
      labels:
        app: code
    spec:
      volumes:
        - name: code-volume
          persistentVolumeClaim:
              claimName: code-pvc
      initContainers:
      - name: home-init
        image: busybox
        command: ["sh", "-c", "chown -R 1000:1000 /home/coder"]
        volumeMounts:
        - mountPath: "/home/coder"
          name: code-volume
      containers:
      - image: codercom/code-server:latest
        imagePullPolicy: Always
        name: code
        volumeMounts:
          - mountPath: "/home/coder"
            name: code-volume
        resources:
          limits:
            cpu: "0.5"
            memory: "500Mi"
        ports:
        - containerPort: 8080
        env:
          - name: PASSWORD
            value: REDACTED

---
apiVersion: v1
kind: Service
metadata:
  name: code
  labels:
    app: code
spec:
  ports:
    - port: 8080
  selector:
    app: code

---
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: ingress-code
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.org/websocket-services: "code"
spec:
  tls:
  - hosts:
    - example.com
    secretName: code-tls
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        backend:
          serviceName: code
          servicePort: 8080

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: code-pvc
spec:
  accessModes:
    - ReadWriteOnce
  volumeMode: Filesystem
  resources:
    requests:
      storage: 1Gi
```

需要注意的几个点：

1. 用了一个 pvc 用于 /home/coder 的持久化，所以你的集群里得有相应的 pv/storage class
2. 我用的是 Nginx Inc. 的 ingress controller，它的 websocket 支持需要一句 nginx.org/websocket-services 设置
3. 额外添加了一个 init container，为了处理 home 目录的权限

