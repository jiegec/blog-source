---
layout: post
date: 2022-09-24
tags: [esxi,vmware,lacp]
categories:
    - devops
---

# ESXi 配置 LACP 链路聚合

## 背景

给 ESXi 接了两路 10Gbps 的以太网，需要用 LACP 来聚合。ESXi 自己不能配置 LACP，需要配合 vCenter Server 的 Distributed Switch 来配置。

<!-- more -->

## 步骤

参考文档：[LACP Support on a vSphere Distributed Switch](https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.vsphere.networking.doc/GUID-0D1EF5B4-7581-480B-B99D-5714B42CD7A9.html)

第一步是创建一个 Distributed Switch。找到 Cluster，点击 ACTIONS，在 Distributed Switch 里面选择 New Distributed Switch。里面的选项都可以用默认的，按需修改。

第二步，找到刚刚创建的 Distributed Switch，点击 Configure，在 Settings 下点击 LACP，点击 NEW，选项可以用默认的，按需修改。

第三步，找到 Distributed Switch，点击 ACTIONS，点击 Add and Manage Hosts，找到要配置的主机，在 Manage physical adapters 这一步，找到要加入到链路聚合的 vmnic，每个要聚合的 vmnic 都在右边的 Assign uplink 处选择刚刚创建的 LAG 下的 Uplink，按顺序，一一对应。其余选项可以使用默认的。这一步配置好以后，在交换机上应该就可以看到 LACP 正常运转。

第四步，如果要把虚拟机连到链路聚合的网络上，找到虚拟机，点击 ACTIONS，点击 Edit Settings，新建一个网卡，Network adapter 处选择刚刚创建的 Distributed Port Group。这一步是让虚拟机多一个网卡，可以连接到 Distributed Switch 上。这一步配置好以后，虚拟机就可以收到来自其他物理机的网络流量，但是发送不出去。

注：Static Binding 和 Ephemeral Binding 的区别见 [Static (non-ephemeral) or ephemeral port binding on a vSphere Distributed Switch (1022312)](https://kb.vmware.com/s/article/1022312)。在 vCenter 上可以给虚拟机分配到 Static binding 的 Distributed Port Group 上，而在 ESXi 上只可以分配到 Ephemeral Port Group。通常来讲，只需要 Static binding，而 Ephemeral binding 是在紧急情况下使用的。

第五步，如果要把 VMKernel 连到链路聚合的网络上，找到虚拟机，添加一个 VMKernel adapter，端口组为 Distributed Port Group，如默认创建的第一个 Distributed Port Group。类似地，此时 VMKernel 配置的 IP 地址还不能从外面访问，但是可以从同一个 Distributed Switch 的虚拟机中访问。

第六步，修改 Failover 配置，找到 Distributed Switch，点击 ACTIONS，在 Distributed Port Group 里点击 Manager Distributed Port Groups，勾选 Teaming and failover，勾上所有的 Distributed Port Group，修改下面的 Failover Order，默认状态是 Active uplinks 只有 Uplink，没有 LAG，需要修改为 Active uplinks 只有 LAG，而 Uplink 都在 Unused Uplinks 中。这样才可以让虚拟机和 VMKernel 出去的流量走链路聚合。

参考文档：[LACP Teaming and Failover Configuration for Distributed Port Groups](https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.vsphere.networking.doc/GUID-9454ED41-6CFC-49F1-9982-34C1276F775A.html) 和 [Configure a Link Aggregation Group to Handle the Traffic for Distributed Port Groups](https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.vsphere.networking.doc/GUID-45DF45A6-DBDB-4386-85BF-400797683D05.html)

这样就配置完成了。

## 非 LACP 的链路聚合

如果想要链路聚合，但是又不想用 Virtual Distributed Switch，可以在交换机上配置 Static Link Aggregation，然后在 ESXi 上添加多个 Uplink，配置 NIC teaming 为 `Route based on IP hash` 模式即可。

参考：[NIC teaming in ESXi and ESX](https://kb.vmware.com/s/article/1004088)