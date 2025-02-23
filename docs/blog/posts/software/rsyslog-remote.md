---
layout: post
date: 2022-07-01
tags: [linux,rsyslog,remote,logging]
categories:
    - software
---

# rsyslog 收集远程日志

## 背景

最近在运维的时候发现网络设备（如交换机）有一个远程发送日志的功能，即可以通过 syslog udp 协议发送日志到指定的服务器。为此，可以在服务器上运行 rsyslog 并收集日志。

## rsyslog 配置

默认的 rsyslog 配置是收集系统本地的配置，因此我们需要编写一个 rsyslog 配置，用于收集远程的日志。

首先复制 `/etc/rsyslog.conf` 到 `/etc/rsyslog-remote.conf`，然后修改：

1. 注释掉 `imuxsock` 和 `imklog` 相关的 module 加载
2. 去掉 `imudp` 和 `imtcp` 相关的注释，这样就会监听在相应的端口上
3. 修改 `$WorkDirectory`，例如 `$WorkDirectory /var/spool/rsyslog-remote`，防止与已有的 rsyslog 冲突
4. 注释 `$IncludeConfig`，防止引入了不必要的配置
5. 注释所有已有的 `RULES` 下面的配置
6. 添加如下配置：

```conf
$template FromIp,"/var/log/rsyslog-remote/%FROMHOST-IP%.log"
*.* ?FromIp
```

这样，就会按照来源的 IP 地址进行分类，然后都写入到 `/var/log/rsyslog-remote/x.x.x.x.log` 文件里。最后的 `/etc/rsyslog-remote.conf` 内容如下：

```conf
module(load="imudp")
input(type="imudp" port="514" address="1.2.3.4")

module(load="imtcp")
input(type="imtcp" port="514" address="1.2.3.4")

$FileOwner root
$FileGroup adm
$FileCreateMode 0640
$DirCreateMode 0755
$Umask 0022

$WorkDirectory /var/spool/rsyslog-remote

$template FromIp,"/var/log/rsyslog-remote/%FROMHOST-IP%.log"
*.* ?FromIp
```

此外，还需要手动创建 `/var/spool/rsyslog-remote` 和 `/var/log/rsyslog-remote` 目录。

## systemd service

最后，写一个 systemd service `/etc/systemd/system/rsyslog-remote.service` 让它自动启动：

```toml
[Unit]
ConditionPathExists=/etc/rsyslog-remote.conf
Description=Remote Syslog Service

[Service]
Type=simple
PIDFile=/var/run/rsyslogd-remote.pid
ExecStart=/usr/sbin/rsyslogd -n -f /etc/rsyslog-remote.conf -i /var/run/rsyslogd-remote.pid
ExecReload=/bin/kill -HUP $MAINPID

[Install]
WantedBy=multi-user.target
```

立即启动并设置开机启动：

```shell
systemctl daemon-reload
systemctl enable --now rsyslog-remote
```

这样就实现了远程日志的收集。

## logrotate 设置

为了防止日志太多，还需要配置 logrotate。

复制 `/etc/logrotate.d/rsyslog` 到 `/etc/logrotate.d/rsyslog-remote`，然后修改开头为 `/var/log/rsyslog-remote/*.log` 即可，路径和上面对应：

```conf
/var/log/rsyslog-remote/*.log
{
        rotate 4
        weekly
        missingok
        notifempty
        compress
        delaycompress
        sharedscripts
        postrotate
                /usr/lib/rsyslog/rsyslog-remote-rotate
        endscript
}
```

注意脚本 `/usr/lib/rsyslog/rsyslog-remote` 也需要复制一份到 `/usr/lib/rsyslog/rsyslog-remote-rotate`，然后修改一下 systemd service 名字：

```shell
#!/bin/sh

if [ -d /run/systemd/system ]; then
    systemctl kill -s HUP rsyslog-remote.service
fi
```

## 参考文档

- [How to Set Up Remote Logging on Linux Using rsyslog](https://www.makeuseof.com/set-up-linux-remote-logging-using-rsyslog/)
- [Configuring Remote Logging using rsyslog in CentOS/RHEL](https://www.thegeekdiary.com/configuring-remote-logging-using-rsyslog-in-centos-rhel/)
- [How to Setup Central Logging Server with Rsyslog in Linux](https://www.tecmint.com/install-rsyslog-centralized-logging-in-centos-ubuntu/)
- [How to Setup Rsyslog Client to Send Logs to Rsyslog Server in CentOS 7](https://www.tecmint.com/setup-rsyslog-client-to-send-logs-to-rsyslog-server-in-centos-7/)