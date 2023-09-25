---
layout: post
date: 2023-09-25
tags: [docker,rootless,podman]
categories:
    - software
---

# Podman 和 Docker Rootless 实践

最近在配置公用机器的环境，需求是很多用户需要使用 docker，但是众所周知，有 docker 权限就等于有了 root 权限，因此正好想尝试一下现在的 Rootless 容器化方案，例如 docket rootless 和 podman。

<!-- more -->

## Docker Rootless

首先是 Docker，官方已经支持 Rootless 部署，文档在 <https://docs.docker.com/engine/security/rootless/>，使用上分为两步：

1. 管理员用 root 权限配置好各项依赖
2. 每个用户跑一次 setup 脚本，然后正常用 docker

第一步安装 docker 不必赘述，为了 docker rootless，还需要安装额外的包：

```shell
sudo apt install uidmap dbus-user-session fuse-overlayfs slirp4netns docker-ce-rootless-extras
```

建议用比较新的发行版，旧发行版对 docker rootless 的支持可能会比较差。

安装完以后，每个用户自己执行一个初始化脚本：

```shell
dockerd-rootless-setuptool.sh install
```

之后就可以正常使用 docker 了，从 `docker info` 可以看到目前是 rootless 模式：

```shell
docker info | grep Context
```

更多的注意事项可以看 Docker 官方的文档。

### GPU

如果想要在 Docker Rootless 中使用 NVIDIA GPU，默认情况下是会报错的，可以参考 [GPU with rootless Docker](https://stackoverflow.com/a/61489688/2148614) 文档解决。修改文件后，就会发现可以在容器里使用 `nvidia-smi` 了：

```shell
docker run -it --rm --gpus all debian nvidia-smi
```

## Podman Rootless

Podman Rootless 的官方文档在 <https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md>，相比 Docker，Podman Rootless 配置更加简单，不需要用户运行 install 脚本，和前文一样配置好依赖以后，直接运行 podman 即可。

### GPU

要在 Podman Rootless 中使用 NVIDIA GPU，也需要像上面 Docker 那样，修改配置 `no-cgroups=true`，然后按照 [Support for Container Device Interface](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/cdi-support.html) 配置 [Container Device Interface](https://github.com/cncf-tags/container-device-interface)：

```shell
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
nvidia-ctk cdi list
```

此时就会生成 `/etc/cdi/nvidia.yaml` 配置文件，里面是为了让容器可以用 NVIDIA GPU 所需要的配置。如果想在 podman 里使用 NVIDIA GPU，运行：

```shell
podman run --device nvidia.com/gpu=all -it --rm debian nvidia-smi
```

如果 Podman 版本不够新，可能会遇到 `nvidia-smi not found` 的问题。这是因为，虽然 Podman 从 [3.2.0](https://github.com/containers/podman/blob/main/RELEASE_NOTES.md#320) 版本开始支持 Container Device Interface。但是如果 nvidia container 版本比较新，生成了 0.5.0 版本的 CDI Spec，就需要比较新的 Podman 版本（大概 4.1.0 以后）。实际测试了一下，Ubuntu 22.04 打包的 Podman 3.4.4 版本不够新，可以按照 [Podman Installation Instrucions](https://podman.io/docs/installation#ubuntu) 文档安装最新的 Podman 4.6.2：

```shell
sudo mkdir -p /etc/apt/keyrings
curl -fsSL "https://download.opensuse.org/repositories/devel:kubic:libcontainers:unstable/xUbuntu_$(lsb_release -rs)/Release.key" \
  | gpg --dearmor \
  | sudo tee /etc/apt/keyrings/devel_kubic_libcontainers_unstable.gpg > /dev/null
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/devel_kubic_libcontainers_unstable.gpg]\
    https://download.opensuse.org/repositories/devel:kubic:libcontainers:unstable/xUbuntu_$(lsb_release -rs)/ /" \
  | sudo tee /etc/apt/sources.list.d/devel:kubic:libcontainers:unstable.list > /dev/null
sudo apt-get update -qq
sudo apt-get -qq -y install podman
```

更新 podman 以后，就可以在容器里使用 NVIDIA GPU：

```shell
podman run --device nvidia.com/gpu=all -it --rm debian nvidia-smi
```

注：网上可以查到一些 podman 用 nvidia gpu 的教程，使用的是旧的 oci hooks 机制，可能在新版本系统上无法工作，需要按照上面提示的 Container Device Interface 方法进行配置。新的 nvidia-container-toolkit 包已经不包含 oci hooks 配置，所以建议用上面的新使用方法。

## 总结

总而言之，在比较新的发行版里，无论是 docker 还是 podman，其 rootless 都已经比较成熟，建议在共享服务器上使用，减少 rootful docker 的使用。目前 nvidia gpu 的支持方面，docker 比较易用，podman 还需要比较多的配置，以及足够新的版本。

测试环境：

- Ubuntu 22.04 + [Kubic repo](https://build.opensuse.org/package/show/devel:kubic:libcontainers:unstable/podman)
- docker 23.0.4
- containerd 1.6.16
- runc 1.1.4
- slirp4netns 1.2.2
- fuse-overlayfs 1.13
- crun 1.9
- podman 4.6.2