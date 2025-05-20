---
layout: post
date: 2020-10-18
tags: [vmware,esxi,vcsa,baremetal,visualization]
categories:
    - devops
---

# 在裸机上部署 ESXi 和 vCSA 7

之前在另一篇文章里提到过 vCSA 的安装，这次又在另一台机器上重新做了一遍，特此记录一下。

首先在官网上下载 [ESXi+VCSA 7.0](https://my.vmware.com/group/vmware/evalcenter?p=vsphere-eval-7) ，应该得到两个文件：

```
7.9G VMware-VCSA-all-7.0.1-16860138.iso
358M VMware-VMvisor-Installer-7.0U1-16850804.x86_64.iso
```

首先安装 ESXi，用 UNetBootin 制作 ESXi 的安装光盘。注意不能用 dd，因为它是 CDFS 格式的，不能直接 boot。启动以后，按照界面要求，一路安装即可。

接着，就可以用网页访问 ESXi 进行配置。比如安装一些 Linux 发行版，然后在 Linux 虚拟机里面 mount 上面的 VCSA 的 iso：

```bash
sudo mount /dev/sr0 /mnt
```

接着，复制并修改 `/mnt/vcsa-cli-installer/templates/install/embedded_vCSA_on_ESXi.json`，按照代码注释进行修改。需要注意几点：

1. 密码都可以设为空，然后运行 cli 的时候输入
2. ESXi 的密码和 vCSA 的密码是不一样的
3. 可以把 ceip 关掉，设置 ceip_enabled: false
4. 配的域名可以解析到正确的 IP

接着，进行安装：

```bash
/mnt/vcsa-cli-installer/lin64/vcsa-deploy install --accept-eula /path/to/customized.json -v
```

慢慢等待它安装成功即可。做好心理准备：这个过程很漫长，而且可能出各种错误，需要去修复。

安装完成后，进入 vCSA，新建一个 Datacenter，然后选择新建的 Datacenter，选择 Add host，输入 ESXi 的地址和用户密码信息即可。
