---
layout: post
date: 2021-03-12 11:35:00 +0800
tags: [switch,router]
category: devops
title: 常用交换机命令
---

# 背景

最近接触了 Cisco，DELL，Huawei，H3C，Ruijie 的网络设备，发现配置方式各有不同，故记录一下各个厂家的命令。

# Huawei

测试型号：S5320

## 保存配置

```
<HUAWEI>save
The current configuration will be written to flash:/vrpcfg.zip.
Are you sure to continue?[Y/N]y
Now saving the current configuration to the slot 0....
Save the configuration successfully.
```

## 进入配置模式

```
<HUAWEI> system-view
```

## 查看当前配置

```
[HUAWEI] display current-configuration
```

## 查看 LLDP 邻居

```
[HUAWEI]display lldp neighbor brief
```


# DELL

测试型号：N3048

## 保存配置

```
console#copy running-config startup-config

This operation may take few minutes.
Management interfaces will not be available during this time.

Are you sure you want to save? (y/n) y

Configuration Saved!
```

## 进入配置模式

```
console>enable
console# configure
```

## 查看当前配置

```
console# show running-config
```

## 查看 LLDP 邻居

```
console#show lldp remote-device all
```

## VLAN Trunk 配置

```
console(config)#interface Gi1/0/1
console(config-if-Gi1/0/1)#switchport mode trunk
console(config-if-Gi1/0/1)#switchport trunk allowed vlan xxx,xxx-xxx
```

## VLAN Access 配置

```
console(config)#interface Gi1/0/1
console(config-if-Gi1/0/1)#switchport mode access
console(config-if-Gi1/0/1)#switchport access vlan xxx
```

## 查看 VLAN 配置

```
console#show vlan
```

## 批量配置 interface

```
console(config)#interface range Gi1/0/1-4
```

# H3C

## 进入配置模式

```
<switch>system-view
System View: return to User View with Ctrl+Z.
[switch]
```

## 查看当前配置

```
[switch]display current-configuration
```

## 查看 lldp 邻居

```
[switch]display lldp neighbor-information
```

## 保存配置

```
[switch]save
The current configuration will be written to the device. Are you sure? [Y/N]:y
Please input the file name(*.cfg)[flash:/startup.cfg]
(To leave the existing filename unchanged, press the enter key):y
The file name is invalid(does not end with .cfg).
```