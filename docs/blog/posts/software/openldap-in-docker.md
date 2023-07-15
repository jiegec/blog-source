---
layout: post
date: 2023-05-13
tags: [ldap,openldap,docker]
categories:
    - software
---

# 使用 Docker 部署 OpenLDAP

OpenLDAP 是一个开源的用户系统实现，主要支持 LDAP 协议，可以给其他系统提供用户认证。下面讨论了如何在 Docker 中部署 OpenLDAP。

<!-- more -->

## Docker-Compose

OpenLDAP 可以用现成的 Docker 镜像：[bitnami/openldap](https://hub.docker.com/r/bitnami/openldap/)，配合 Docker-Compose 进行部署：

```yml
version: '2'

services:
  openldap:
    image: bitnami/openldap:2.6
    ports:
      - '1389:1389' # LDAP
    environment:
      - LDAP_ROOT=dc=example,dc=com # example.com
    env_file: .env # admin password
    volumes:
      - './data:/bitnami/openldap' # data storage
```

admin 密码建议单独保存，例如写在 `.env` 中：

```shell
LDAP_ADMIN_PASSWORD=12345678REDACTED
```

启动服务：

```shell
# prepare data folder
sudo rm -rf data
sudo mkdir data
sudo chown 1001:root data
# launch docker compose
sudo docker-compose up -d
```

然后就可以通过 ldapsearch 列出所有对象，默认情况下不需要登录（Bind DN），可以只读访问：

```shell
# search elements under dc=example,dc=com
# -x: Simple authentication without user and password
# -b dc=example,dc=com: base dn for search
# -H: ldap server
$ ldapsearch -x -b dc=example,dc=com -H ldap://localhost:1389/
# user01, users, example.com
dn: cn=user01,ou=users,dc=example,dc=com
cn: User1
cn: user01
sn: Bar1
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
userPassword:: Yml0bmFtaTE=
uid: user01
uidNumber: 1000
gidNumber: 1000
homeDirectory: /home/user01

# user02, users, example.com
dn: cn=user02,ou=users,dc=example,dc=com
cn: User2
cn: user02
sn: Bar2
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
userPassword:: Yml0bmFtaTI=
uid: user02
uidNumber: 1001
gidNumber: 1001
homeDirectory: /home/user02
```

可以看到 Docker 镜像初始化了两个用户，仅供测试用，它用的密码比较弱。

## TLS

接着，给 OpenLDAP 配置 TLS。首先用 OpenSSL 生成 CA 和证书：

```shell
# https://arminreiter.com/2022/01/create-your-own-certificate-authority-ca-using-openssl/
# setup CA
rm -rf certs
mkdir -p certs

openssl genrsa -out certs/ldap_ca.key 4096
openssl req -x509 -new -nodes -key certs/ldap_ca.key -sha256 -days 1826 -out certs/ldap_ca.crt -subj "/CN=Example Com CA/ST=Somewhere/L=Earth/O=ExampleOrg"

# setup cert
# CN must match hostname
openssl req -new -nodes -out certs/ldap_server.csr -newkey rsa:4096 -keyout certs/ldap_server.key -subj "/CN=$(hostname)/ST=Somewhere/L=Earth/O=ExampleOrg"
openssl x509 -req -in certs/ldap_server.csr -CA certs/ldap_ca.crt -CAkey certs/ldap_ca.key -CAcreateserial -out certs/ldap_server.crt -days 730 -sha256

chown -R 1001:root certs
```

然后修改 docker-compose.yml：

```yml
version: '2'

services:
  openldap:
    image: bitnami/openldap:2.6
    ports:
      - '1389:1389' # LDAP
      - '1636:1636' # LDAPS
    environment:
      - LDAP_ROOT=dc=example,dc=com # example.com
      - LDAP_ENABLE_TLS=yes
      - LDAP_TLS_CERT_FILE=/opt/bitnami/openldap/certs/ldap_server.crt
      - LDAP_TLS_KEY_FILE=/opt/bitnami/openldap/certs/ldap_server.key
      - LDAP_TLS_CA_FILE=/opt/bitnami/openldap/certs/ldap_ca.crt
    env_file: .env # admin password
    volumes:
      - './data:/bitnami/openldap' # data storage
      - './certs:/opt/bitnami/openldap/certs'
```

再重新启动，就可以用 LDAPS 来访问 LDAP Server：

```shell
# LDAP
$ ldapsearch -x -b dc=example,dc=com -H ldap://localhost:1389/
# LDAPS
$ LDAPTLS_CACERT=$PWD/certs/ldap_ca.crt ldapsearch -x -b dc=example,dc=com -H ldaps://localhost:1636/
```

## 修改密码

管理员修改用户的密码，使用 ldappasswd 修改：

```shell
# Generate a new password for cn=user01,ou=users,dc=example,dc=com
# -W: prompt for bind(login) password
# -D cn=admin,dc=example,dc=com: bind(login) to admin user
$ ldappasswd -x -W -D cn=admin,dc=example,dc=com -H ldap://localhost:1389/ cn=user01,ou=users,dc=example,dc=com
Enter LDAP Password:
New password: REDACTED

# Set password for for cn=user01,ou=users,dc=example,dc=com
# -S: prompt for new password
$ ldappasswd -x -W -S -D cn=admin,dc=example,dc=com -H ldap://localhost:1389/ cn=user01,ou=users,dc=example,dc=com
New password:
Re-enter new password:
Enter LDAP Password:
```

默认情况下，用户没有权限修改自己的密码。可以进入 Docker 容器，修改数据库的权限：

```shell
$ sudo docker-compose exec openldap bash
# Authenticate using local user
openldap$ ldapmodify -Y EXTERNAL -H "ldapi:///"
SASL/EXTERNAL authentication started
SASL username: gidNumber=0+uidNumber=1001,cn=peercred,cn=external,cn=auth
SASL SSF: 0
# Paste the following lines
# Allow user to change its own password
dn: olcDatabase={2}mdb,cn=config
changetype: modify
replace: olcAccess
olcAccess: {0}to attrs=userPassword
  by anonymous auth
  by self write
  by * none
olcAccess: {1}to *
  by * read
```

此时用户就可以自己修改密码了：

```shell
$ ldappasswd -x -W -S -D cn=user01,ou=users,dc=example,dc=com -H ldap://localhost:1389/
New password:
Re-enter new password:
Enter LDAP Password:
```

并且 userPassword 也对非 admin 用户被隐藏了：

```shell
$ ldapsearch -x -b dc=example,dc=com -H ldap://localhost:1389/
# user01, users, craft.cn
dn: cn=user01,ou=users,dc=craft,dc=cn
cn: User1
cn: user01
sn: Bar1
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
uid: user01
uidNumber: 1000
gidNumber: 1000
homeDirectory: /home/user01
```

## ldap-ui

如果想要 Web 管理界面，可以用 ldap-ui，在 docker-compose 添加：

```yaml
  ldap-ui:
    image: dnknth/ldap-ui
    ports:
      - '5000:5000'
    links:
      - openldap
    environment:
      - LDAP_URL=ldap://openldap:1389/
      - BASE_DN=dc=example,dc=com
      - BIND_PATTERN=cn=%s,dc=example,dc=com
```

访问 localhost:5000，就可以用 admin 用户登录了。如果想用其他用户登录，由于 BIND 路径多了一级 ou=users，所以要么修改 BIND_PATTERN，要么用户名要写成 user01,ou=users

## 权限管理

前面修改了权限，从而允许用户修改自己的密码：

```shell
$ sudo docker-compose exec openldap bash
# Authenticate using local user
openldap$ ldapmodify -Y EXTERNAL -H "ldapi:///"
SASL/EXTERNAL authentication started
SASL username: gidNumber=0+uidNumber=1001,cn=peercred,cn=external,cn=auth
SASL SSF: 0
# Paste the following lines
# Allow user to change its own password
dn: olcDatabase={2}mdb,cn=config
changetype: modify
replace: olcAccess
olcAccess: {0}to attrs=userPassword
  by anonymous auth
  by self write
  by * none
olcAccess: {1}to *
  by * read
```

核心部分的含义如下：

1. to attrs=userPassword：针对 userPassword 这个字段，任何人都可以认证，用户自己可以写，其他人没有权限
2. to *：任何人可以读

如果想要进一步收缩权限，例如：

1. 不登录看不到任何信息
2. 普通用户登录后，只能读取自己的信息

那么，可以写出如下的配置：

```ldif
dn: olcDatabase={2}mdb,cn=config
changetype: modify
replace: olcAccess
olcAccess: {0}to attrs=userPassword
  by anonymous auth
  by self write
  by * none
olcAccess: {1}to *
  by self read
  by * none
```

由于从前往后匹配，找到第一个匹配就不看后面的规则的原因，更精确的过滤要放在前面。

## LDAP 用于其他软件的认证

LDAP 很重要的一个用途是用于其他软件的认证，一般来说有两种用法：

1. LDAP 自身带了认证的功能（Simple Auth），那么就需要把用户名（user01）映射到 LDAP 的 Bind DN 上（cn=user01,ou=users,cn=example,cn=com），Bind DN 和密码会传输到 LDAP Server；在 LDAP Server 上密码会与用户的 userPassword 进行匹配，如果 Bind 成功，就认为用户登录成功
2. LDAP 附带了列用户的功能（Search），那么这个时候，一般是要创建一个用于搜索的 DN 来控制权限；然后其他软件 Bind 到用于搜索的 DN 上，搜索用户，把用户信息同步到本地

第一种使用方法要求用户和 DN 有直接映射关系，例如上面的 `cn=%s,ou=users,cn=example=com`，好处是比较简单，缺点是要把所有用户放在同一个 DN 下面，不适合比较复杂的组织结构。

第二种使用方法，则是其他软件先进行搜索（搜索本身可能需要 Bind 到用于搜索的 DN 上），找到匹配用户名或者邮箱的用户，再进行 Simple Auth。这样的好处是灵活性更好，用户不需要放在同一个 DN 下面，可以有更多层级。

由于使用了 Simple Auth，密码会明文发送给 LDAP Server，因此为了安全性，建议配置 TLS。
