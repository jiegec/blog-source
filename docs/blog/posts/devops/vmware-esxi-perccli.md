---
layout: post
date: 2021-04-15
tags: [esxi,vmware,perc,perccli,raid,megaraid,lsi,avago]
categories:
    - devops
title: 在 ESXi 中用 PERCCli 换 RAID 中的盘
---

## 背景

最近有一台机器的盘出现了报警，需要换掉，然后重建 RAID5 阵列。iDRAC 出现报错：

1. Disk 2 in Backplane 1 of Integrated RAID Controller 1 is not functioning correctly.
2. Virtual Disk 1 on Integrated RAID Controller 1 has become degraded.
3. Error occurred on Disk2 in Backplane 1 of Integrated RAID Controller 1 : (Error 2)

## 安装 PERCCli

首先，因为系统是 VMware ESXi 6.7，所以在[DELL 官网](https://www.dell.com/support/home/zh-cn/drivers/driversdetails?driverid=5v7xx)下载对应的文件。按照里面的 README 安装 vib：

```shell
esxcli software vib install -v /vmware-perccli-007.1420.vib
```

如果要升级系统，需要先卸载 vib：`esxcli software vib remove -n vmware-perccli`，因为升级的时候会发现缺少新版系统的 perccli，建议先卸载，升级后再安装新的。

需要注意的是，如果复制上去 Linux 版本的 PERCCli，虽然也可以运行，但是找不到控制器。安装好以后，就可以运行 `/opt/lsi/perccli/perccli` 。接着，运行 `perccli show all`，可以看到类似下面的信息：

```shell
$ perccli show all
--------------------------------------------------------------------------------
EID:Slt DID State  DG     Size Intf Med SED PI SeSz Model               Sp Type
--------------------------------------------------------------------------------
32:2      2 Failed  1 3.637 TB SATA HDD N   N  512B ST4000NM0033-9ZM170 U  -
32:4      4 UGood   F 3.637 TB SATA HDD N   N  512B ST4000NM0033-9ZM170 U  -
--------------------------------------------------------------------------------
```

其中 E32S2 是 Failed 的盘，属于 Disk Group 1；E32S4 是新插入的盘，准备替换掉 E32S2，目前不属于任何的 Disk Group。查看一下 Disk Group：`perccli /c0/dall show`

```shell
$ perccli /c0/dall show
-----------------------------------------------------------------------------
DG Arr Row EID:Slot DID Type  State BT       Size PDC  PI SED DS3  FSpace TR
-----------------------------------------------------------------------------
 1 -   -   -        -   RAID5 Dgrd   N    7.276 TB dflt N  N   dflt N      N
 1 0   -   -        -   RAID5 Dgrd   N    7.276 TB dflt N  N   dflt N      N
 1 0   0   32:1     1   DRIVE Onln   N    3.637 TB dflt N  N   dflt -      N
 1 0   1   32:2     2   DRIVE Failed N    3.637 TB dflt N  N   dflt -      N
 1 0   2   32:3     3   DRIVE Onln   N    3.637 TB dflt N  N   dflt -      N
```

可以看到 DG1 处于 Degraded 状态，然后 E32S4 处于 Failed 状态。参考了一下 [PERCCli 文档](https://dl.dell.com/topicspdf/cli_guide_en-us.pdf)，它告诉我们要这么做：

```shell
perccli /cx[/ex]/sx set offline
perccli /cx[/ex]/sx set missing
perccli /cx /dall show
perccli /cx[/ex]/sx insert dg=a array=b row=c
perccli /cx[/ex]/sx start rebuild
```

具体到我们这个情景，就是把 E32S2 设为 offline，然后用 E32S4 来替换它：

```shell
perccli /c0/e32/s2 set offline
perccli /c0/e32/s2 set missing
perccli /cx /dall show
perccli /cx/e32/s4 insert dg=1 array=0 row=2
perccli /cx/e32/s4 start rebuild
```

完成以后的状态：

```shell
TOPOLOGY :
========

---------------------------------------------------------------------------
DG Arr Row EID:Slot DID Type  State BT     Size PDC  PI SED DS3  FSpace TR
---------------------------------------------------------------------------
 1 -   -   -        -   RAID5 Dgrd  N  7.276 TB dflt N  N   dflt N      N
 1 0   -   -        -   RAID5 Dgrd  N  7.276 TB dflt N  N   dflt N      N
 1 0   0   32:1     1   DRIVE Onln  N  3.637 TB dflt N  N   dflt -      N
 1 0   1   32:4     4   DRIVE Rbld  Y  3.637 TB dflt N  N   dflt -      N
 1 0   2   32:3     3   DRIVE Onln  N  3.637 TB dflt N  N   dflt -      N
---------------------------------------------------------------------------
```

可以看到 E32S4 替换了原来 E32S2 的位置，并且开始重建。查看重建进度：

```shell
$ perccli /c0/32/s4 show rebuild
-----------------------------------------------------
Drive-ID   Progress% Status      Estimated Time Left
-----------------------------------------------------
/c0/e32/s4         3 In progress -
-----------------------------------------------------
$ perccli show all
Need Attention :
==============

Controller 0 :
============

-------------------------------------------------------------------------------
EID:Slt DID State DG     Size Intf Med SED PI SeSz Model               Sp Type
-------------------------------------------------------------------------------
32:4      4 Rbld   1 3.637 TB SATA HDD N   N  512B ST4000NM0033-9ZM170 U  -
-------------------------------------------------------------------------------
```

然后，查看一下出错的盘：

```shell
$ perccli /c0/e32/s2 show all
Drive /c0/e32/s2 State :
======================
Shield Counter = 0
Media Error Count = 0
Other Error Count = 6
Drive Temperature =  36C (96.80 F)
Predictive Failure Count = 0
S.M.A.R.T alert flagged by drive = No
```

果然有错误，但是也看不到更多信息了。

坏块统计：

```shell
$ perccli /c0 show badblocks
Detailed Status :
===============

-------------------------------------------------------------
Ctrl Status Ctrl_Prop       Value ErrMsg               ErrCd
-------------------------------------------------------------
   0 Failed Bad Block Count -     BadBlockCount failed     2
-------------------------------------------------------------

```

经过检查以后，发现 E32S2 盘的 SMART 并没有报告什么问题，所以也没有把盘取走，而是作为 hot spare 当备用：

```shell
$ perccli /c0/e32/s2 add hotsparedrive DG=1
$ perccli /c0/d1 show
TOPOLOGY :
========

---------------------------------------------------------------------------
DG Arr Row EID:Slot DID Type  State BT     Size PDC  PI SED DS3  FSpace TR
---------------------------------------------------------------------------
 1 -   -   -        -   RAID5 Dgrd  N  7.276 TB dflt N  N   dflt N      N
 1 0   -   -        -   RAID5 Dgrd  N  7.276 TB dflt N  N   dflt N      N
 1 0   0   32:1     1   DRIVE Onln  N  3.637 TB dflt N  N   dflt -      N
 1 0   1   32:4     4   DRIVE Rbld  Y  3.637 TB dflt N  N   dflt -      N
 1 0   2   32:3     3   DRIVE Onln  N  3.637 TB dflt N  N   dflt -      N
 1 -   -   32:2     2   DRIVE DHS   -  3.637 TB -    -  -   -    -      N
---------------------------------------------------------------------------

DG=Disk Group Index|Arr=Array Index|Row=Row Index|EID=Enclosure Device ID
DID=Device ID|Type=Drive Type|Onln=Online|Rbld=Rebuild|Optl=Optimal|Dgrd=Degraded
Pdgd=Partially degraded|Offln=Offline|BT=Background Task Active
PDC=PD Cache|PI=Protection Info|SED=Self Encrypting Drive|Frgn=Foreign
DS3=Dimmer Switch 3|dflt=Default|Msng=Missing|FSpace=Free Space Present
TR=Transport Ready
```

这样就可以做后备盘，当别的盘坏的时候，作为备用。

## 相关软件下载

可以在[这里](https://www.broadcom.com/products/storage/raid-controllers/megaraid-sas-9361-8i#downloads)寻找 StorCLI 版本。

StorCLI：

- 007.1613.0000.0000 Oct 29, 2020 [007.1613.0000.0000_Unified_StorCLI.zip](https://docs.broadcom.com/docs/007.1613.0000.0000_Unified_StorCLI.zip)
- 007.1506.0000.0000 Aug 11, 2020 [StorCLI_MR7.15.zip](https://downloadcenter.intel.com/download/30286/StorCLI-Standalone-Utility) 
- 1.15.12 Apr 23, 2015 [MR_SAS_StorCLI_6-7-1-15-12-SCGCQ00852539.zip](https://docs.broadcom.com/docs/12354905)
- 1.15.05 Jan 22, 2015 [1-15-05_StorCLI.zip](https://docs.broadcom.com/docs/12354804)

MegaCLI:

- 8.07.07 Dec 19, 2012 [8-07-07_MegaCLI.zip](https://docs.broadcom.com/docs/12351585)

PercCLI:

- 007.1420.0000.0000 Dec 10, 2020 [PERCCLI_N65F1_7.1420.00_A10_Linux.tar.gz](https://www.dell.com/support/home/zh-cn/drivers/driversdetails?driverid=n65f1) [PERCCLI_5V7XX_7.1420.0_A10_VMware.tar.gz](https://www.dell.com/support/home/zh-cn/drivers/driversdetails?driverid=5v7xx)
- 007.1327.0000.0000 July 27, 2020 [PERCCLI_D6YWP_7.1327.00_A09_Linux.tar.gz](https://www.dell.com/support/home/zh-cn/drivers/driversdetails?driverid=d6ywp)
- 007.0127.0000.0000 July 13, 2017 [perccli_7.1-007.0127_linux.tar.gz](https://www.dell.com/support/home/zh-cn/drivers/driversdetails?driverid=f48c2)