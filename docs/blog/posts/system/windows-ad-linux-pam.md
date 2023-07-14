---
layout: post
date: 2018-05-05
tags: [windows,ad,pam,winbind,samba]
categories:
    - system
title: 在 Archlinux 上用 winbind 配合 pam 配置 Windows AD 认证登录
---

作为不清真的网络管理员，为了配置一套完整的统一认证系统，陈老师采用了 Windows AD 的方法给这里配置统一认证。重装了系统，自然要把之前的统一认证再配到新装的 Archlinux 上。

参考资料： [Active Directory Integration](https://wiki.archlinux.org/index.php/Active_Directory_Integration)

首先安装相应的包：

```shell
pacman -S samba
```

我们还没有配好 Kerberos，所以跳过。

然后配置 /etc/samba/smb.conf，以下是一个例子。可以根据文档微调。

```
[global]
        security = ads
        realm = YOUR-AD-HERE
        workgroup = YOUR-GROUP-HERE
        idmap uid = 10000-20000
        idmap gid = 10000-20000
        winbind enum users = yes
        winbind enum groups = yes
        template homedir = /home/%D/%U
        template shell = /bin/bash
        client use spnego = yes
        client ntlmv2 auth = yes
        encrypt passwords = yes
        winbind use default domain = yes
        restrict anonymous = 2

```

这样，域上的用户 user 会拿到 home 目录为 /home/YOUR-DOMAIN-HERE/user，uid 在 10000-2000 范围内的用户。在一会经过配置之后，可以通过 `getent passwd` 验证。

接下来，需要把本机的 samba 登入到域的管理员，并且启动服务。

```shell
net ads join -U your-user-name
systemctl enable --now smb
systemctl enable --now nmb
systemctl enable --now winbind
```

更改 /etc/nsswitch.conf，在 passwd, shadow 和 group 都增添 winbind：

```
passwd: files mymachines systemd winbind
group: files mymachines systemd winbind
shadow: files winbind
```

接下来，可以进一步验证配置是否正确：

```shell
wbinfo -u
wbinfo -g
getent passwd
getent group
net ads info
net ads lookup
```

接下来可以配置 PAM 了。这一部分踩到了一些坑，现在终于做得差不多了。

需求：

1. 如果一个用户名既有本地用户也有域上的用户，选择前者
2. 用户要修改密码的话，如果是域用户，则要求走 Windows AD 那套方法改密码；否则仅修改本地用户密码。

实现：

修改 /etc/pam.d/system-auth:

第一部分：auth

```
auth [success=1 default=ignore]         pam_localuser.so
auth [success=2 default=die]            pam_winbind.so krb5_auth krb5_ccache_type=FILE cached_login try_first_pass
auth [success=1 default=die]            pam_unix.so nullok_secure
auth requisite                          pam_deny.so
auth optional                           pam_permit.so
auth required                           pam_env.so
```

首先利用 pam_localuser.so 匹配用户名和 `/etc/passwd` ，如果有， `success=1` 代表跳过下面一条规则，故会跳到 pam_unix.so 这一行。如果失败，`default=ignore` 表示忽略它的结果。如果是本地用户，匹配 pam_localuser.so 成功后跳到 pam_unix.so，如果成功了则跳到第五行，pam_permit.so 代表通过，最后由 pam_env.so 配置环境变量。如果是域用户，则由 pam_winbind.so 处理，如果成功，同样跳到第 5 条。如果本地用户和域用户都失败，就 pam_deny.so 认证失败。

第二部分：account

```
account required                        pam_unix.so
account [success=1 default=ignore]      pam_localuser.so
account required                        pam_winbind.so
account optional                        pam_permit.so
account required                        pam_time.so
```

这一部分仍有疑问。留待以后来补充。

第三部分：password

```
password [success=1 default=ignore]     pam_localuser.so
password [default=die]                  pam_echo.so file=/etc/pam.d/messages/ad_reject_change_passwd.txt
password optional                       pam_echo.so file=/etc/pam.d/messages/local_user_passwd.txt
password [success=1 default=die]        pam_unix.so sha512 shadow
password requisite                      pam_deny.so
password optional                       pam_permit.so
```

这里实现了我们的需求：如果是本地用户，提醒用户当前要修改的是本地用户的密码；如果是域用户，则输出信息后直接拒绝。

这里的 /etc/pam.d/messages/ad_reject_change_passwd.txt 内容如下：

```
Hi %u, please go to xxxxxxx to change your Active Directory password!
```

第四部分：session

```int
session   required                      pam_limits.so
session   required                      pam_mkhomedir.so skel=/etc/skel/ umask=0022
session   required                      pam_unix.so
session   [success=1 default=ignore]    pam_localuser.so
session   required                      pam_winbind.so
session   optional                      pam_permit.so
```

这里与 Wiki 上内容无异。

然后修改 /etc/pam.d/passwd :

```
password        required        pam_cracklib.so difok=2 minlen=8 dcredit=2 ocredit=2 retry=3
password        include         system-auth
#password       requisite       pam_deny.so
#password       required        pam_unix.so sha512 shadow nullok
```

首先判断密码强度。通过后则直接用刚才更改的 system-auth 中的 password 部分规则。

这样就配好了认证。自己对这套东西的理解还不够深，以后遇到了要继续钻研。

扩展阅读： [PAM 配置简介 - 王邈](https://innull.com/pam-configuration-how-to/)
