---
layout: post
date: 2021-03-12
tags: [switch,router]
categories:
    - devops
title: 常用交换机命令
---

## 背景

最近接触了 Cisco，DELL，Huawei，H3C，Ruijie 的网络设备，发现配置方式各有不同，故记录一下各个厂家的命令。

## Huawei

测试型号：S5320

### 保存配置

```
<HUAWEI>save
The current configuration will be written to flash:/vrpcfg.zip.
Are you sure to continue?[Y/N]y
Now saving the current configuration to the slot 0....
Save the configuration successfully.
```

### 进入配置模式

```
<HUAWEI> system-view
```

### 查看当前配置

```
[HUAWEI] display current-configuration
```

### 查看 LLDP 邻居

```
[HUAWEI]display lldp neighbor brief
```

### 查看 CDP 邻居

```
[HUAWEI]display cdp neighbor brief
```

### 启用 LLDP

```
[HUAWEI]lldp enable
```

### 启用 CDP

```
[HUAWEI-XGigabitEthernet0/0/1]lldp compliance cdp txrx
```

### 启用只读 SNMPv1 community

```
[HUAWEI]snmp-agent sys-info version all
Warning: This command may cause confliction in netconf status. Continue? [Y/N]:y
Warning: SNMPv1/SNMPv2c is not secure, and it is recommended to use SNMPv3.
[HUAWEI]snmp-agent community read [COMMUNITY NAME]
Warning: This command may cause confliction in netconf status. Continue? [Y/N]:y
```

### 启用 SNMP iso view

默认情况下 SNMP 会缺少一些标准的 MIB（比如 LLDP），可以打开 iso view：

```
[HUAWEI]snmp-agent mib-view included iso-view iso
Warning: This command may cause confliction in netconf status. Continue? [Y/N]:y
[HUAWEI]snmp-agent community read [COMMUNITY NAME] mib-view iso-view
```

### 查看 ARP 表

```
[HUAWEI]display arp
```

### ARPING

```
[HUAWEI]arp send-packet X.X.X.X ffff-ffff-ffff interface Vlanif VLAN
```

### 启用 STP 协议

```
[HUAWEI]stp enable
[HUAWEI]stp mode vbst
```

### 设置 NTP 服务器

```
[HUAWEI]ntp-service unicast-server x.x.x.x
```

### 设置远程 syslog 服务器

```
[HUAWEI]info-center loghost x.x.x.x
```

### 设置 LACP 链路聚合

```
[HUAWEI-XGigabitEthernet0/0/1]eth-trunk 1
[HUAWEI-XGigabitEthernet0/0/2]eth-trunk 1
[HUAWEI]interface Eth-Trunk 1
[HUAWEI-Eth-Trunk1]mode lacp
```

## DELL

测试型号：N3048

### 保存配置

```
console#copy running-config startup-config

This operation may take few minutes.
Management interfaces will not be available during this time.

Are you sure you want to save? (y/n) y

Configuration Saved!
```

### 进入配置模式

```
console>enable
console# configure
```

### 查看当前配置

```
console# show running-config
```

### 查看 LLDP 邻居

```
console#show lldp remote-device all
```

### VLAN Trunk 配置

```
console(config)#interface Gi1/0/1
console(config-if-Gi1/0/1)#switchport mode trunk
console(config-if-Gi1/0/1)#switchport trunk allowed vlan xxx,xxx-xxx
```

### VLAN Access 配置

```
console(config)#interface Gi1/0/1
console(config-if-Gi1/0/1)#switchport mode access
console(config-if-Gi1/0/1)#switchport access vlan xxx
```

### 查看 VLAN 配置

```
console#show vlan
```

### 批量配置 interface

```
console(config)#interface range Gi1/0/1-4
```

### 启用 SSH 服务器

```
console(config)#crypto key generate rsa
console(config)#crypto key generate dsa
console(config)#ip ssh server
```

### 启用 CDP(DELL 称之为 ISDP)

```
console(config)#isdp enable
```

### 启用只读 SNMPv1 community

```
console(config)#snmp-server community [COMMUNITY NAME] ro
```

### 设置 NTP 服务器

```
console(config)#sntp unicast client enable
console(config)#sntp server x.x.x.x
```

### 设置 NTP 服务器

```
console(config)#sntp unicast client enable
console(config)#sntp server x.x.x.x
```

### 设置 STP 协议

```
console(config)#spanning-tree mode rapid-pvst
```

## H3C

### 进入配置模式

```
<switch>system-view
System View: return to User View with Ctrl+Z.
[switch]
```

### 查看当前配置

```
[switch]display current-configuration
```

### 查看 lldp 邻居

```
[switch]display lldp neighbor-information
```

### 保存配置

```
[switch]save
The current configuration will be written to the device. Are you sure? [Y/N]:y
Please input the file name(*.cfg)[flash:/startup.cfg]
(To leave the existing filename unchanged, press the enter key):y
The file name is invalid(does not end with .cfg).
```

### 批量配置 interface

```
[switch]interface range GigabitEthernet 1/0/1 to GigabitEthernet 1/0/24
[switch-if-range]
```

### 查看 MAC 地址表

```
[switch]show mac-address
```

### 打开 LLDP 和 CDP

```
[switch]lldp global enable
[switch]lldp compliance cdp
```

## Mellanox

### 进入配置模式

```
switch > enable
switch # configure terminal
switch (config) #
```

### 查看当前配置

```
switch (config) # show running-config
```

### 查看 interface 状态

```
switch (config) # show interfaces brief
```

### 查看以太网端口状态

```
switch (config) # show interfaces ethernet status
```

### 查看 lldp 邻居

```
switch (config) # show lldp remote
```

### 保存配置

```
switch (config) # configuration write
```

### 批量配置 interface

```
switch (config) # interface ethernet 1/1/1-1/1/4
switch (config interface ethernet 1/1/1-1/1/4) #
```

### 查看 MAC 地址表

```
switch (config) # show mac-address-table
```

### 查看链路聚合状态

```
switch (config) # show interfaces port-channel summary
```

### 把拆分的四个 SFP 口恢复成一个

```
switch (config interface ethernet 1/1/1) # module-type qsfp 
```

### 把一个 QSFP 口拆分成四个

```
switch (config interface ethernet 1/1) # shutdown
switch (config interface ethernet 1/1) # module-type qsfp-split-4
```

### 设置链路聚合

```
switch (config interface ethernet 1/1) # channel-group 1 mode active
switch (config interface ethernet 1/2) # channel-group 1 mode active
```

模式可以选择：active(LACP)/passive(LACP)/on(Static)

### 设置 STP 协议

```
switch (config) # spanning-tree mode rpvst
```

### 设置远程 syslog 服务器

```
switch (config) # logging x.x.x.x
```

### 设置 NTP 服务器

```
switch (config) # ntp server x.x.x.x
```

## Cisco

### 设置 NTP 服务器

```
# ntp server x.x.x.x
```