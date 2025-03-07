---
layout: post
date: 2022-07-02
tags: [linux,mellanox,connectx4,ethernet,infiniband,mst,mft]
categories:
    - software
---

# 切换 ConnectX-4 为以太网模式

## 背景

最近在给机房配置网络，遇到一个需求，就是想要把 ConnectX-4 当成以太网卡用，它既支持 Infiniband，又支持 Ethernet，只不过默认是 Infiniband 模式，所以需要用 mlxconfig 工具来做这个切换。

## 切换方法

在 [Using mlxconfig](https://docs.nvidia.com/networking/display/mftv422/using+mlxconfig) 文档中，写了如何切换网卡为 Infiniband 模式：

```shell
$ mlxconfig -d /dev/mst/mt4103_pci_cr0 set LINK_TYPE_P1=1 LINK_TYPE_P2=1
 
Device #1:
----------
Device type:   ConnectX3Pro
PCI device:    /dev/mst/mt4103_pci_cr0
Configurations:        Next Boot        New
  LINK_TYPE_P1         ETH(2)           IB(1)
  LINK_TYPE_P2         ETH(2)           IB(1)
 
Apply new Configuration? ? (y/n) [n] : y
Applying... Done!
-I- Please reboot machine to load new configurations.
```

那么，我们只需要反其道而行之，设置模式为 `ETH(2)` 即可。

## MST 安装

要使用 mlxconfig，就需要安装 [MFT(Mellanox Firmware Tools)](https://network.nvidia.com/products/adapter-software/firmware-tools/)。我们用的是 Debian bookworm，于是要下载 DEB：

```shell
wget https://www.mellanox.com/downloads/MFT/mft-4.20.1-14-x86_64-deb.tgz
unar mft-4.20.1-14-x86_64-deb.tgz
cd mft-4.20.1-14-x86_64-deb
```

UPDATE 2022-10-28: 现在最新版本 mft-4.21.0-99 已经修复了下面出现的编译问题。

```shell
wget https://www.mellanox.com/downloads/MFT/mft-4.21.0-99-x86_64-deb.tgz
unar mft-4.21.0-99-x86_64-deb.tgz
cd mft-4.21.0-99-x86_64-deb
```

尝试用 `sudo ./install.sh` 安装，发现 dkms 报错。查看日志，发现是因为内核过高（5.18），有函数修改了用法，即要把 pci_unmap_single 的调用改为 dma_unmap_single，并且修改第一个参数，如 [linux commit a2e759612e5ff3858856fe97be5245eecb84e29b](https://github.com/torvalds/linux/commit/a2e759612e5ff3858856fe97be5245eecb84e29b) 指出的那样：


```patch
-           pci_unmap_single(dev->pci_dev, dev->dma_props[i].dma_map, DMA_MBOX_SIZE, DMA_BIDIRECTIONAL);
+           dma_unmap_single(&dev->pci_dev->dev, dev->dma_props[i].dma_map, DMA_MBOX_SIZE, DMA_BIDIRECTIONAL);
```

修改完以后，手动 `sudo dkms install kernel-mft-dkms/4.20.1`，发现就编译成功了。再手动安装一下 mft 并启动服务：

```
$ sudo dpkg -i DEBS/mft_4.20.1-14_amd64.deb
$ sudo mst start
Starting MST (Mellanox Software Tools) driver set
Loading MST PCI module - Success
[warn] mst_pciconf is already loaded, skipping
Create devices
Unloading MST PCI module (unused) - Success
$ sudo mst status
MST modules:
------------
    MST PCI module is not loaded
    MST PCI configuration module loaded

MST devices:
------------
/dev/mst/mtxxxx_pciconf0         - PCI configuration cycles access.
                                   domain:bus:dev.fn=0000:xx:xx.0 addr.reg=yy data.reg=zz cr_bar.gw_offset=-1
                                   Chip revision is: 00
```

既然已经安装好了，最后执行 `mlxconfig` 即可切换为以太网：

```shell
$ sudo mlxconfig -d /dev/mst/mtxxxx_pciconf0 set LINK_TYPE_P1=2 LINK_TYPE_P2=2

Device #1:
----------

Device type:    ConnectX4
Name:           REDACTED
Description:    ConnectX-4 VPI adapter card; FDR IB (56Gb/s) and 40GbE; dual-port QSFP28; PCIe3.0 x8; ROHS R6
Device:         /dev/mst/mtxxxx_pciconf0

Configurations:                              Next Boot       New
         LINK_TYPE_P1                        IB(1)           ETH(2)
         LINK_TYPE_P2                        IB(1)           ETH(2)

 Apply new Configuration? (y/n) [n] : y
Applying... Done!
-I- Please reboot machine to load new configurations.
```

显示各个配置可能的选项和内容：`sudo mlxconfig -d /dev/mst/mtxxxx_pciconf0 show_confs`

整个安装流程在仓库 <https://github.com/jiegec/mft-debian-bookworm> 中用脚本实现。

UPDATE: 太新的 MFT 版本不支持比较旧的网卡，例如 4.22.1-LTS 支持 ConnectX-3，但 4.26.1-LTS 就不支持了。

## VMware ESXi

如果要在 ESXi 上把网卡改成以太网模式，可以参考下面的文档：

- https://docs.nvidia.com/networking/pages/releaseview.action?pageId=15049813
- https://docs.nvidia.com/networking/plugins/servlet/mobile?contentId=15051769#content/view/15051769

命令（ESXi 7.0U3）：

```
scp *.vib root@esxi:/some/path
esxcli software vib install -v /some/path/MEL_bootbank_mft_4.21.0.703-0.vib
esxcli software vib install -v /some/path/MEL_bootbank_nmst_4.21.0.703-1OEM.703.0.0.18434556.vib
reboot
/opt/mellanox/bin/mst start
/opt/mellanox/bin/mst status -vv
/opt/mellanox/bin/mlxfwmanager --query
/opt/mellanox/bin/mlxconfig -d mt4115_pciconf0 set LINK_TYPE_P1=2 LINK_TYPE_P2=2
reboot
```

然后就可以看到网卡了。