---
layout: post
date: 2023-11-23
tags: [macOS,apple,m1,x86,linux,arm64]
categories:
    - software
---

# 在 Apple Silicon macOS 上跑 Linux 虚拟机 + Rosetta

## 背景

最近需要跑某个 x86 only 且需要 GUI 的程序，以往都是跑在远程 Linux/Windows 机器上再远程桌面去使用。最近看到了一些比较成熟的在 macOS 上跑 Linux 虚拟机 + Rosetta 的办法（[M1 Mac で Vivado が動いた！](https://qiita.com/jin0g/items/692fde40cd895b81f39e)），因此记录下来。

<!-- more -->

本文参考了很多 [M1 Mac で Vivado が動いた！](https://qiita.com/jin0g/items/692fde40cd895b81f39e) 的内容。

## 安装 lima 和 xquartz

用 homebrew 安装：

```shell
brew install lima
brew install xquartz
```

lima 是用来管理虚拟机的工具，XQuartz 是为了让虚拟机里的进程可以在 macOS 上通过 X11 显示 GUI。

因为需要跑 x86，还需要 rosetta：

```shell
softwareupdate --install-rosetta
```

## 创建 Linux 虚拟机

用 lima 创建 Linux 虚拟机：

```shell
limactl start template://debian --rosetta --vm-type=vz
```

创建的时候，选择编辑配置，让 ssh 转发 X11：

```yaml
ssh:
  forwardX11: true
  forwardX11Trusted: true
```

安装完成以后，运行 `limactl shell debian`，就可以进入到 Linux shell 了。

如果想要添加额外的 mount，可以修改配置，或者在 `limactl start` 命令行参数上添加 `--mount`，例如：`limactl start template://debian --rosetta --vm-type=vz --mount /Volumes/Data:w`。

## 运行 X11 程序

启动 XQuartz，在 XQuartz 的 Terminal 里启动并连接 lima，安装 x11-app 并显示：

```shell
limactl shell debian
# In Linux
sudo apt install xauth
# Back to macOS
echo $DISPLAY
limactl shell debian
# In Linux
sudo apt install x11-apps
echo $DISPLAY
xeyes
```

就可以在 macOS 上看到 xeyes 的输出了，它实际上是运行在 Linux 虚拟机里面，通过 ssh 转发出来。如果没有安装 xauth，会出现 X11 转发失败（见 [X11 forwarding request failed on channel 0](https://stackoverflow.com/a/42735336/2148614)）。

Rosetta 也已经注册到 binfmt 中：

```shell
$ cat /proc/sys/fs/binfmt_misc/rosetta
enabled
interpreter /mnt/lima-rosetta/rosetta
flags: OCF
offset 0
magic 7f454c4602010100000000000000000002003e00
mask fffffffffffefe00fffffffffffffffffeffffff
```

因此可以直接运行 x86_64 的程序。当然了，如果 x86 的程序需要动态库，还需要它的动态库依赖。比较简单的解决办法是用 docker/podman。lima 默认安装了 containerd，可以用 nerdctl 来运行容器：

```shell
# AMD64 container
nerdctl run -it --platform amd64 --rm debian:stable
# ARM64 container
nerdctl run -it --rm debian:stable
```

不喜欢 containerd，也可以用 podman：`sudo apt install podman`，

```shell
# AMD64 rootful container
sudo podman run -it --arch amd64 --rm debian:stable
# AMD64 rootless container
podman run -it --arch amd64 --rm debian:stable
```

可以进一步在 AMD64 container 中运行 wine：

```shell
limactl shell debian
# In Linux
sudo podman run -it --rm --arch amd64 --network host -e DISPLAY=$DISPLAY -e HOME=$HOME -u $(id -u):$(id -g) -v $HOME:$HOME -v /Volumes/Data:/Volumes/Data docker.io/tobix/wine:stable
# In container
wine64 regedit
```
