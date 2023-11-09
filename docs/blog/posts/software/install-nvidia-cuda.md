---
layout: post
date: 2022-07-06
tags: [nvidia,cuda]
categories:
    - software
---

# NVIDIA 驱动和 CUDA 安装速查

## 背景

最近在 Ubuntu 上配置 NVIDIA 驱动和 CUDA 环境的次数比较多，在此总结一下整个流程，作为教程供大家学习。

## 配置 NVIDIA APT 源

Ubuntu 源有自带的 NVIDIA 驱动版本，但这里我们要使用 NVIDIA 的 APT 源。首先，我们要访问 <https://developer.nvidia.com/cuda-downloads?target_os=Linux&target_arch=x86_64&Distribution=Ubuntu&target_version=20.04&target_type=deb_network>，在网页中选择我们的系统，例如：

1. Operating System: Linux
2. Architecture: x86_64
3. Distribution: Ubuntu
4. Version: 20.04
5. Installer Type: deb (network)

此时，下面就会显示一些命令，复制下来执行：

```shell
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update
```

最后一步的 `sudo apt-get -y install cuda` 可以不着急安装，我们在后面再来讨论 CUDA 版本的问题。

## NVIDIA 驱动

配置好源以后，接下来，我们就要安装 NVIDIA 驱动了。首先，我们要选取一个 NVIDIA 版本，选择的标准如下：

1. 驱动版本需要支持所使用的显卡
2. 驱动版本需要支持所使用的 CUDA 版本

这些信息在网络上都可以查到，也可以参考 [NVIDIA 驱动和 CUDA 版本信息速查](nvidia-cuda.md)。

假如我们已经选择了要安装 470.129.06 版本，那么，我们接下来要确认一下 NVIDIA 的 APT 源的版本名称：

```
sudo apt show -a nvidia-driver-470
```

在输出的结果中搜索 `470.129.06`，找到 `Version: 470.129.06-0ubuntu1`，下面写了 `APT-Sources: https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64 Packages`，这就说明这个版本是从 NVIDIA 的 APT 源来的。

所以，我们要用 `470.129.06-0ubuntu1`，而不是 `470.129.06-0ubuntu0.20.04.1`，后者是 Ubuntu 源自带的，我们要用前者。

接下来，指定版本安装驱动：

```shell
sudo apt install nvidia-driver-470=470.129.06-0ubuntu1
```

如果系统里已经安装了其他版本的 nvidia 驱动，可能会出现冲突。这时候，只需要把冲突的包也写在要安装的包里即可，例如：

```shell
sudo apt install nvidia-utils-470=470.129.06-0ubuntu1 cuda-drivers=470.129.06-1 cuda-drivers-470=470.129.06-1 nvidia-driver-470=470.129.06-0ubuntu1 libnvidia-gl-470=470.129.06-0ubuntu1 libnvidia-compute-470=470.129.06-0ubuntu1 libnvidia-decode-470=470.129.06-0ubuntu1 libnvidia-encode-470=470.129.06-0ubuntu1 libnvidia-ifr1-470=470.129.06-0ubuntu1 libnvidia-fbc1-470=470.129.06-0ubuntu1 libnvidia-common-470=470.129.06-0ubuntu1 nvidia-kernel-source-470=470.129.06-0ubuntu1 nvidia-dkms-470=470.129.06-0ubuntu1 nvidia-kernel-common-470=470.129.06-0ubuntu1 libnvidia-extra-470=470.129.06-0ubuntu1 nvidia-compute-utils-470=470.129.06-0ubuntu1 xserver-xorg-video-nvidia-470=470.129.06-0ubuntu1 libnvidia-cfg1-470=470.129.06-0ubuntu1 nvidia-settings=470.129.06-0ubuntu1 libxnvctrl0=470.129.06-0ubuntu1 nvidia-modprobe=470.129.06-0ubuntu1
```

最终，我们要保证，系统里面所有 nvidia 驱动相关的包都是同一个版本：

```shell
$ sudo apt list --installed | grep nvidia
libnvidia-cfg1-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed,automatic]
libnvidia-common-470/unknown,now 470.129.06-0ubuntu1 all [installed,automatic]
libnvidia-compute-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed]
libnvidia-decode-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed]
libnvidia-encode-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed]
libnvidia-extra-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed,automatic]
libnvidia-fbc1-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed]
libnvidia-gl-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed]
libnvidia-ifr1-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed]
nvidia-compute-utils-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed,automatic]
nvidia-dkms-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed]
nvidia-driver-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed]
nvidia-fabricmanager-470/unknown,now 470.129.06-1 amd64 [installed,automatic]
nvidia-kernel-common-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed,automatic]
nvidia-kernel-source-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed,automatic]
nvidia-modprobe/unknown,now 470.129.06-0ubuntu1 amd64 [installed,upgradable to: 515.48.07-0ubuntu1]
nvidia-settings/unknown,now 470.129.06-0ubuntu1 amd64 [installed,upgradable to: 515.48.07-0ubuntu1]
nvidia-utils-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed,automatic]
xserver-xorg-video-nvidia-470/unknown,now 470.129.06-0ubuntu1 amd64 [installed,automatic]
```

接下来，为了防止 apt 升级的时候顺手破坏了一致的版本，我们要把包固定在一个版本里：

```shell
sudo apt-mark hold cuda-drivers nvidia-modprobe nvidia-settings libxnvctrl0
```

如果有其他 nvidia 包说要自动升级，也可以类似地固定住。

## CUDA

CUDA 实际上是绿色软件，把整个目录放在任意一个目录，都可以使用。

安装 CUDA 的方式有很多，我们可以用 APT 安装全局的，也可以用 Spack 或者 Anaconda 安装到本地目录。实际上这些安装过程都是把同样的文件复制到不同的地方而已。

如果要安装全局的话，还是推荐用 NVIDIA 的 APT 源，以安装 CUDA 11.1 为例：

```shell
sudo apt install cuda-11-1
```

那么 CUDA 就会安装到 /usr/local/cuda-11.1 目录下。如果想要用 nvcc，我们可以手动把它加到 PATH 环境变量中。

CUDA 是可以多版本共存的，比如你可以把 CUDA 11.1 到 CUDA 11.7 一口气都装了。不过注意，CUDA 对 NVIDIA 驱动有版本要求，所以有一些可能会不满足 APT 的版本要求；同时，CUDA 对编译器版本有要求，所以如果系统还是 Ubuntu 16.04 或者 18.04，赶紧升级吧。


## NVIDIA Container Toolkit

安装方法：<https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#linux-distributions>

命令：

```shell
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list \
  && \
    sudo apt-get update
```
