---
layout: post
date: 2020-05-21
tags: [ecc,crypto]
categories:
    - crypto
---

# 各种 ecc 曲线

## 背景知识

椭圆曲线有如下的形式：

第一种：

$$E: y^2 \equiv x^3 + ax + b \mod{p}$$

曲线的参数共有 $(p, a, b, G, n, h)$。$G$ 是一个点 $(G_x, G_y)$，$n$ 是 $G$ 的阶。

第二种：

$$E: y^2+xy=x^3+ax^2+1$$

称为 Kbolitz curve。不同的曲线有不同的参数 $(m,f(x),a,b,G,n,h)$，对应不同的 $GF(2^m)$ 域。

## OpenSSL

看一下 openssl 支持的曲线参数（`openssl ecparam -list_curves`）：

```
  secp112r1 : SECG/WTLS curve over a 112 bit prime field
  secp112r2 : SECG curve over a 112 bit prime field
  secp128r1 : SECG curve over a 128 bit prime field
  secp128r2 : SECG curve over a 128 bit prime field
  secp160k1 : SECG curve over a 160 bit prime field
  secp160r1 : SECG curve over a 160 bit prime field
  secp160r2 : SECG/WTLS curve over a 160 bit prime field
  secp192k1 : SECG curve over a 192 bit prime field
  secp224k1 : SECG curve over a 224 bit prime field
  secp224r1 : NIST/SECG curve over a 224 bit prime field
  secp256k1 : SECG curve over a 256 bit prime field
  secp384r1 : NIST/SECG curve over a 384 bit prime field
  secp521r1 : NIST/SECG curve over a 521 bit prime field
  prime192v1: NIST/X9.62/SECG curve over a 192 bit prime field
  prime192v2: X9.62 curve over a 192 bit prime field
  prime192v3: X9.62 curve over a 192 bit prime field
  prime239v1: X9.62 curve over a 239 bit prime field
  prime239v2: X9.62 curve over a 239 bit prime field
  prime239v3: X9.62 curve over a 239 bit prime field
  prime256v1: X9.62/SECG curve over a 256 bit prime field
  sect113r1 : SECG curve over a 113 bit binary field
  sect113r2 : SECG curve over a 113 bit binary field
  sect131r1 : SECG/WTLS curve over a 131 bit binary field
  sect131r2 : SECG curve over a 131 bit binary field
  sect163k1 : NIST/SECG/WTLS curve over a 163 bit binary field
  sect163r1 : SECG curve over a 163 bit binary field
  sect163r2 : NIST/SECG curve over a 163 bit binary field
  sect193r1 : SECG curve over a 193 bit binary field
  sect193r2 : SECG curve over a 193 bit binary field
  sect233k1 : NIST/SECG/WTLS curve over a 233 bit binary field
  sect233r1 : NIST/SECG/WTLS curve over a 233 bit binary field
  sect239k1 : SECG curve over a 239 bit binary field
  sect283k1 : NIST/SECG curve over a 283 bit binary field
  sect283r1 : NIST/SECG curve over a 283 bit binary field
  sect409k1 : NIST/SECG curve over a 409 bit binary field
  sect409r1 : NIST/SECG curve over a 409 bit binary field
  sect571k1 : NIST/SECG curve over a 571 bit binary field
  sect571r1 : NIST/SECG curve over a 571 bit binary field
  c2pnb163v1: X9.62 curve over a 163 bit binary field
  c2pnb163v2: X9.62 curve over a 163 bit binary field
  c2pnb163v3: X9.62 curve over a 163 bit binary field
  c2pnb176v1: X9.62 curve over a 176 bit binary field
  c2tnb191v1: X9.62 curve over a 191 bit binary field
  c2tnb191v2: X9.62 curve over a 191 bit binary field
  c2tnb191v3: X9.62 curve over a 191 bit binary field
  c2pnb208w1: X9.62 curve over a 208 bit binary field
  c2tnb239v1: X9.62 curve over a 239 bit binary field
  c2tnb239v2: X9.62 curve over a 239 bit binary field
  c2tnb239v3: X9.62 curve over a 239 bit binary field
  c2pnb272w1: X9.62 curve over a 272 bit binary field
  c2pnb304w1: X9.62 curve over a 304 bit binary field
  c2tnb359v1: X9.62 curve over a 359 bit binary field
  c2pnb368w1: X9.62 curve over a 368 bit binary field
  c2tnb431r1: X9.62 curve over a 431 bit binary field
  wap-wsg-idm-ecid-wtls1: WTLS curve over a 113 bit binary field
  wap-wsg-idm-ecid-wtls3: NIST/SECG/WTLS curve over a 163 bit binary field
  wap-wsg-idm-ecid-wtls4: SECG curve over a 113 bit binary field
  wap-wsg-idm-ecid-wtls5: X9.62 curve over a 163 bit binary field
  wap-wsg-idm-ecid-wtls6: SECG/WTLS curve over a 112 bit prime field
  wap-wsg-idm-ecid-wtls7: SECG/WTLS curve over a 160 bit prime field
  wap-wsg-idm-ecid-wtls8: WTLS curve over a 112 bit prime field
  wap-wsg-idm-ecid-wtls9: WTLS curve over a 160 bit prime field
  wap-wsg-idm-ecid-wtls10: NIST/SECG/WTLS curve over a 233 bit binary field
  wap-wsg-idm-ecid-wtls11: NIST/SECG/WTLS curve over a 233 bit binary field
  wap-wsg-idm-ecid-wtls12: WTLS curve over a 224 bit prime field
  Oakley-EC2N-3: 
	IPSec/IKE/Oakley curve #3 over a 155 bit binary field.
	Not suitable for ECDSA.
	Questionable extension field!
  Oakley-EC2N-4: 
	IPSec/IKE/Oakley curve #4 over a 185 bit binary field.
	Not suitable for ECDSA.
	Questionable extension field!
  brainpoolP160r1: RFC 5639 curve over a 160 bit prime field
  brainpoolP160t1: RFC 5639 curve over a 160 bit prime field
  brainpoolP192r1: RFC 5639 curve over a 192 bit prime field
  brainpoolP192t1: RFC 5639 curve over a 192 bit prime field
  brainpoolP224r1: RFC 5639 curve over a 224 bit prime field
  brainpoolP224t1: RFC 5639 curve over a 224 bit prime field
  brainpoolP256r1: RFC 5639 curve over a 256 bit prime field
  brainpoolP256t1: RFC 5639 curve over a 256 bit prime field
  brainpoolP320r1: RFC 5639 curve over a 320 bit prime field
  brainpoolP320t1: RFC 5639 curve over a 320 bit prime field
  brainpoolP384r1: RFC 5639 curve over a 384 bit prime field
  brainpoolP384t1: RFC 5639 curve over a 384 bit prime field
  brainpoolP512r1: RFC 5639 curve over a 512 bit prime field
  brainpoolP512t1: RFC 5639 curve over a 512 bit prime field
  SM2       : SM2 curve over a 256 bit prime field
```

这个列表很长，主要有几个参数：

1. 什么域：素数域还是 $GF(2^m)$ 域
2. 位数：域有多少位
3. 标准：NIST/SECG/WTLS/X9.62/RFC 5639/SM2/Oakley 表示的是不同的标准

## NIST

NIST 在 [FIPS 186-4](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.186-4.pdf) 中定义了基于素数域的 Curve P-192, Curve P-224, Curve P-256, Curve P-384 和 Curve P-521。在 [RFC5656](https://tools.ietf.org/html/rfc5656) 中，这几条曲线又名 nistp192 nistp224 nistp256 nistp384 和 nistp521。

Curve P-192: 

$$p = 2^{192}-2^{64}-1$$

Curve P-224: 

$$p=2^{224}-2^{96}-1$$

Curve P-256: 

$$p=2^{256}-2^{224}+2^{192}+2^{96}-1$$

Curve P-384: 

$$p=2^{384}-2^{128}-2^{96}+2^{32}-1$$

Curve P-521: 

$$p=2^{521}-1$$

另一类是基于 Binary Field（$GF(2^m)$）的曲线，有 Curve K-163，Curve B-163，Curve K-233，Curve B-233，Curve K-283，Curve B-283，Curve K-409，Curve B-409，Curve K-571，Curve B-571。相应地，RFC 5656 里又名 nistk163，nistk233，nistb233，nistk283，nistk409，nistb409，nistt571（我觉得是 nistb571/nistk571，不知道是不是写错了）

Degree 163 (K-163/B-163) :

$$p(t)=t^{163}+t^7+t^6+t^3+1$$

Degree 233 (K-233/B-233) :

$$p(t)=t^{233}+t^{74}+1$$

Degree 283 (K-283/B-283) :

$$p(t)=t^{283}+t^{12}+t^7+t^5+1$$

Degree 409 (K-409/B-409) :

$$p(t)=t^{409}+t^{87}+1$$

Degree 571 (K-571/B-571) :

$$p(t)=t^{571}+t^{10}+t^5+t^2+1$$

## SECG

SECG 在 [SEC2](https://www.secg.org/sec2-v2.pdf) 中定义了若干的曲线，其中一部分和上面的 NIST 是同一个曲线。首先是基于素数域的：

| NIST     | SEC       | OID                 | ANSI       |
| -------- | --------- | ------------------- | ---------- |
| nistp192 | secp192r1 | 1.2.840.10045.3.1.1 | prime192v1 |
|          | secp192k1 | 1.3.132.0.31        |            |
| nistp224 | secp224r1 | 1.3.132.0.33        |            |
|          | secp224k1 | 1.3.132.0.32        |            |
| nistp256 | secp256r1 | 1.2.840.10045.3.1.7 | prime256v1 |
|          | secp256k1 | 1.3.132.0.10        |            |
| nistp384 | secp384r1 | 1.3.132.0.34        |            |
|          | secp384k1 |                     |            |
| nistp521 | secp521r1 | 1.3.132.0.35        |            |
|          | secp521k1 |                     |            |

然后是基于 $GF(2^m)$ 域的：

| NIST                               | SEC       | OID          |
| ---------------------------------- | --------- | ------------ |
| nistk163                           | sect163k1 | 1.3.132.0.1  |
|                                    | sect163r1 | 1.3.132.0.2  |
| nistb163                           | sect163r2 | 1.3.132.0.15 |
| nistk233                           | sect233k1 | 1.3.132.0.26 |
| nistb233                           | sect233r1 | 1.3.132.0.27 |
|                                    | sect239k1 | 1.3.132.0.3  |
| nistk283                           | sect283k1 | 1.3.132.0.16 |
| nistb283                           | sect283r1 | 1.3.132.0.17 |
| nistk409                           | sect409k1 | 1.3.132.0.36 |
| nistb409                           | sect409r1 | 1.3.132.0.37 |
| nistk571 (RFC 5656 写的是 nistt571) | sect571k1 | 1.3.132.0.38 |
| nistb571                           | sect571r1 | 1.3.132.0.39 |

sec 命名里，第四个字符里 $p$ 表示是素数域，$t$ 表示是 $GF(2^m)$ 域。后面的字母表示的 $k$ 表示 Koblitz，$r$ 表示 random，是参数的选取方式。

OID 有两种前缀：

```
1.3.132.0.x:
iso(1) identified-organization(3) certicom(132) curve(0)
1.2.840.10045.3.1.x:
iso(1) member-body(2) us(840) 10045 curves(3) prime(1)
```

完整列表见 [OID 1.3.132.0](https://oidref.com/1.3.132.0) 和 [OID 1.2.840.10045.3.1](https://oidref.com/1.2.840.10045.3.1)

## ANSI

ANSI 也有 [X9.62 标准](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.202.2977&rep=rep1&type=pdf)，在附录里面也定义了若干个曲线。附录 `J.5.1` 里面有三个例子，就是 prime192v1 prime192v2 和 prime192v3，之后则是 prime239v1 prime239v2 prime239v3 和 prime256v1。

| ANSI       | 别名               | OID                 |
| ---------- | ------------------ | ------------------- |
| prime192v1 | nistp192/secp192r1 | 1.2.840.10045.3.1.1 |
| prime192v2 |                    | 1.2.840.10045.3.1.2 |
| prime192v3 |                    | 1.2.840.10045.3.1.3 |
| prime239v1 |                    | 1.2.840.10045.3.1.4 |
| prime239v2 |                    | 1.2.840.10045.3.1.5 |
| prime239v3 |                    | 1.2.840.10045.3.1.6 |
| prime256v1 | nistp256/secp256r1 | 1.2.840.10045.3.1.7 |

## 总结

对于同一个曲线，不同的组织给出了不同的名字，见下表：

| OpenSSL    | NIST     | SECG      | ANSI       |
| ---------- | -------- | --------- | ---------- |
| prime192v1 | nistp192 | secp192r1 | prime192v1 |
| secp224r1  | nistp224 | secp224r1 |            |
| prime256v1 | nistp256 | secp256r1 | prime256v1 |
| secp384r1  | nistp384 | secp384r1 |            |
| secp521r1  | nistp521 | secp521r1 |            |
| sect163k1  | nistk163 | sect163k1 |            |
| sect163r2  | nistb163 | sect163r2 |            |
| sect233k1  | nistk233 | sect233k1 |            |
| sect233r1  | nistb233 | sect233r1 |            |
| sect283k1  | nistk233 | sect283k1 |            |
| sect283r1  | nistb283 | sect283r1 |            |
| sect409k1  | nistk409 | sect409k1 |            |
| sect409r1  | nistb409 | sect409r1 |            |
| sect571k1  | nistk571 | sect571k1 |            |
| sect571r1  | nistb571 | sect571r1 |            |

在 RFC4492 里也可以看到一个类似的表。