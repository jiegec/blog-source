---
layout: post
date: 2018-05-08
tags: [linux,nat,forwarding,ftp]
categories:
    - networking
title: 搭建 FTP server behind NAT
---

我们出现新的需求，要把以前的 FTP 服务器迁移到 NAT 之后的一台机器上。但是，FTP 不仅用到 20 21 端口，PASV 还会用到高端口，这给端口转发带来了一些麻烦。我们一开始测试，直接在 Router 上转发 20 和 21 端口到 Server 上。但是很快发现，Filezilla 通过 PASV 获取到地址为（内网地址，端口高 8 位，端口低 8 位），然后，Filezilla 检测出这个地址是内网地址，于是转而向 router_ip:port 发包，这自然是不会得到结果的。

此时我们去网上找了找资料，找到了一个很粗暴的方法：
```shell
iptables -A PREROUTING -i external_interface -p tcp -m tcp --dport 20 -j DNAT --to-destination internal_ip:20
iptables -A PREROUTING -i external_interface -p tcp -m tcp --dport 21 -j DNAT --to-destination internal_ip:21
iptables -A PREROUTING -i external_interface -p tcp -m tcp --dport 1024:65535 -j DNAT --to-destination internal_ip:1024-65535
```


有趣地是，macOS 自带的 ftp 命令（High Sierra 似乎已经删去）可以正常使用。研究发现，它用 EPSV（Extended Passive Mode）代替 PASV，这里并没有写内网地址，因而可以正常使用。

这么做，Filezilla 可以成功访问了。但是，用其它客户端的时候，它会直连那个内网地址而不是 Router 的地址，于是还是连不上。而且，使用了 1024-65535 的所有端口，这个太浪费而且会影响我们其它的服务。

我们开始研究我们 FTP 服务器 (pyftpdlib) 的配置。果然，找到了适用于 FTP behind NAT 的相关配置：
```
     - (str) masquerade_address:
        the "masqueraded" IP address to provide along PASV reply when
        pyftpdlib is running behind a NAT or other types of gateways.
        When configured pyftpdlib will hide its local address and
        instead use the public address of your NAT (default None).
     - (dict) masquerade_address_map:
        in case the server has multiple IP addresses which are all
        behind a NAT router, you may wish to specify individual
        masquerade_addresses for each of them. The map expects a
        dictionary containing private IP addresses as keys, and their
        corresponding public (masquerade) addresses as values.
     - (list) passive_ports:
        what ports the ftpd will use for its passive data transfers.
        Value expected is a list of integers (e.g. range(60000, 65535)).
        When configured pyftpdlib will no longer use kernel-assigned
        random ports (default None).
```

于是，我们配置了 `masquerade_address` 使得 FTP 服务器会在 PASV 中返回 Router 的地址，并且在 `passive_ports` 中缩小了 `pyftpdlib` 使用的端口范围。

进行配置以后，我们在前述的 iptables 命令中相应修改了端口范围，现在工作一切正常。
