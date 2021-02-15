---
layout: post
date: 2021-02-15 10:44:00 +0800
tags: [sssd,ldap,pam,nss,starttls]
category: software
title: 使用 SSSD 的 LDAP 认证
---

## 前言

最近在研究替换一个老的用户系统，于是顺便学习了一下 LDAP，还有 SSSD。LDAP 是一个目录协议，顺带的，因为用户信息也可以存在里面，所以也就成了一个常见的用户认证协议。SSSD 就是一个 daemon，把系统的 NSS PAM 的机制和 LDAP 连接起来。

## 配置

其实很简单，安装 sssd 并且配置即可：

```shell
$ sudo apt install sssd
$ sudo vim /etc/sssd/sssd.conf
# file content:
[sssd]
config_file_version = 2
services = nss,pam
domains = LDAP

[domain/LDAP]
cache_credentials = true
enumerate = true
entry_cache_timeout = 10
ldap_network_timeout = 2

id_provider = ldap
auth_provider = ldap
chpass_provider = ldap

ldap_uri = ldap://127.0.0.1/
ldap_chpass_uri = ldap://127.0.0.1/
ldap_search_base = dc=example,dc=com
ldap_default_bind_dn = cn=localhost,ou=machines,dc=example,dc=com
ldap_default_authtok = REDACTED
$ sudo systemctl enable --now sssd
```

一些字段需要按照实际情况编写，请参考[sssd.conf](https://manpages.debian.org/testing/sssd-common/sssd.conf.5.en.html) 和 [sssd-ldap](https://manpages.debian.org/testing/sssd-ldap/sssd-ldap.5.en.html)。

## 协议

那么，LDAP 里面的用户是如何和 Linux 里的用户对应起来的呢？可以看到，SSSD 会查询 posixAccount：

```text
(&(objectclass=posixAccount)(uid=*)(uidNumber=*)(gidNumber=*))
```

然后，可以查到 [posixAccount 的 schema](https://ldapwiki.com/wiki/PosixAccount)，里面可以见到对应 `/etc/passwd` 的各个字段。相应的，也有 `shadowAccount` 对应 `/etc/shadow`。

按照要求配好以后（建议用 ldapvi 工具），就可以用 `getent passwd` 看到新增的用户了。

上面的部分是通过 NSS 接口来查询的，除了用户以外，还有其他的一些 NIS 信息可以通过 LDAP 查询。此外，如果要登录的话，则是用 PAM 认证，SSSD 则会把 PAM 认证转换成 LDAP 的 Bind：

```shell
$ su test
Password:
# sssd: bind to dn of test user with password
```

如果 Bind 成功，则认为登录成功；否则就是登录失败。

如果用户要修改密码，SSSD 默认用的是 [RFC3062 Password Modify Extended Operation](https://tools.ietf.org/html/rfc3062) 的方式；如果服务器不支持的话，可以按照 [文档](https://sssd.io/docs/design_pages/chpass_without_exop.html) 使用 ldap modify 方式来修改密码。
