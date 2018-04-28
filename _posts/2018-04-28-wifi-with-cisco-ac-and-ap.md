---
layout: post
date: 2018-04-28 21:58:00 +0800
tags: [cisco,wifi,vlan]
category: networking
title: 使用 Cisco AC + AP 组合搭建网络实践
---

有一台已配置好直接可用的 AC 在地址 ac-address 。我们需要搭建交换机 + AP 的网络，并且用一台 Linux 服务器进行 DHCP 从而给 AP 分发 AC 的地址。这里以 systemd-networkd 为例。

我们约定，vlan 2 上联外网， vlan 3 为 Linux 服务器和 AP 的内部网络。

接下来，配置交换机给 Linux 服务器的端口为 trunk 口，然后将下联 Cisco AP 的端口都设为 access vlan 3 模式。接下来在 Linux 服务器上配置 DHCP 服务器和 NAT 。

如果 Linux 服务器的 interface 名称为 eno1 :

配置两个 VLAN interface:
```
$ cat /etc/systemd/network/eno1.network
[Match]
Name=eno1

[Network]
VLAN=eno1.2
VLAN=eno1.3
```

相应添加 VLAN 配置：
```
$ cat /etc/systemd/network/eno1.2.network
[NetDev]
Name=eno1.2

[VLAN]
Id=2
$ cat /etc/systemd/network/eno1.3.network
[NetDev]
Name=eno1.3

[VLAN]
Id=3
```

配置上行的 eno1.2 interface 的静态地址：
```
$ cat /etc/systemd/network/eno1.2.network
[Match]
Name=eno1.2

[Network]
Address=123.123.123.123/24
Gateway=123.123.123.1
DNS=1.2.4.8
```

配置内部网络 eno1.3 interface:
```
$ cat /etc/systemd/network/eno1.3.network
[Match]
Name=eno1.3

[Network]
Address=192.168.1.1/24
```

配置 dhcpd (isc-dhcp-server):
```
$ cat /etc/dhcpd.conf
option space Cisco_LWAPP_AP;
option Cisco_LWAPP_AP.server-address code 241 = array of ip-address;

subnet 192.168.1.0 netmask 255.255.255.0 {
  range 192.168.1.100 192.168.1.200;
  option routers 192.168.1.1;
  vendor-option-space Cisco_LWAPP_AP;
  option Cisco_LWAPP_AP.server-address $ac-address;
}
```

配置 iptables 做NAT:
```
iptables -t nat -A POSTROUTING -o eno1.2 -j MASQUERADE
iptables-save > /etc/iptables/iptables.rules
```

打开 ipv4 forwarding:
```
echo 'net.ipv4.conf.all.forwarding=1' >> /etc/sysctl.d/99-ipv4-forwarding.conf
```
