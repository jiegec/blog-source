---
layout: post
date: 2020-05-18
tags: [nfc,usb,fido,fido2,ctap,u2f]
category: hardware
title: FIDO U2F、FIDO2 和 CTAP 的关系
---

## 背景

2012 年，Yubico 和 Google 设计了 U2F 协议，第二年 U2F 成为 FIDO 组织的标准，之后加入了 NFC 的支持。之后，FIDO2 作为替代 U2F 的新标准产生，原来的 U2F 以兼容的方式成为了 CTAP1，而采用 CBOR 封装格式的 CTAP(CTAP2) 则是 FIDO2 的主要协议。

## U2F

### 命令格式

U2F 定义了它的[命令格式](https://fidoalliance.org/specs/fido-u2f-v1.2-ps-20170411/fido-u2f-raw-message-formats-v1.2-ps-20170411.pdf)，基于 ISO7816-4 APDU（short APDU） ：

| CLA    | INS    | P1     | P2     | Lc        | data            | Le        |
| ------ | ------ | ------ | ------ | --------- | --------------- | --------- |
| 1 byte | 1 byte | 1 byte | 1 byte | 0-1 bytes | variable length | 0-1 bytes |

比如 U2F_VERSION 就是：

| CLA  | INS  | P1   | P2   | Lc   | data  | Le   |
| ---- | ---- | ---- | ---- | ---- | ----- | ---- |
| 00   | 03   | 00   | 00   | 0    | empty | 00   |

返回的数据就是 `U2F_V2` 的 ASCII 加上 `9000` 的状态。

除此之外，它还有一种 extended length 格式的 APDU，和上面的是等价的不同表示。

### 传输方式

实际使用 U2F 的时候，又有三种情况，分别是 USB、Bluetooth 和 NFC。

#### USB

在 [U2FHID](https://fidoalliance.org/specs/fido-u2f-v1.2-ps-20170411/fido-u2f-hid-protocol-v1.2-ps-20170411.pdf) 里面，为了让 U2F 的命令通过 HID 接口传输，它规定了两个 endpoint，分别是 Interrupt IN 和 Interrupt OUT，还有一个固定的 HID Report Descriptor。为了发 U2F 命令，首先会进行一次封装：

| CMD        | BCNT | DATA    |
| ---------- | ---- | ------- |
| U2FHID_MSG | 4..n | n bytes |

添加了一个头，表示载荷是一个 U2F 的 command（自然也是 APDU）。

在 cmd 之上，还会封装一层，为了解决 USB 的 packet size 限制等问题，定义了 init packet：

| CID     | CMD    | BCNTH  | BCNTL  | DATA            |
| ------- | ------ | ------ | ------ | --------------- |
| 4 bytes | 1 byte | 1 byte | 1 byte | variable length |

如果数据太长，就会拆分成一个 init 和 多个 continuation packet：

| CID     | SEQ    | DATA            |
| ------- | ------ | --------------- |
| 4 bytes | 1 byte | variable length |

把 init 和 continuation 里面的 data 组合起来，就是 U2F 的 message，message 里面可能又有 U2F raw command，也就是 APDU。

发送的时候，先 Interrupt OUT 发送请求，再 Interrupt IN 读取回应。

#### Bluetooth

在 [U2F/Bluetooth](https://fidoalliance.org/specs/fido-u2f-v1.2-ps-20170411/fido-u2f-bt-protocol-v1.2-ps-20170411.pdf) 里面，也用了一个类似的封装格式，请求：

| CMD    | HLEN   | LLEN   | DATA            |
| ------ | ------ | ------ | --------------- |
| 1 byte | 1 byte | 1 byte | variable length |

这里的 DATA payload 就是 extended length 格式的 APDU

#### NFC

在 [U2F/NFC](https://fidoalliance.org/specs/fido-u2f-v1.2-ps-20170411/fido-u2f-nfc-protocol-v1.2-ps-20170411.pdf) 里面，既然 ISO 7816-4 本来就是 NFC-native 的格式，就不要额外的封装了。只需要规定一个 Applet 的 AID 即可：`A0000006472F0001`

### 总结

总而言之，U2F raw commands 就是在 APDU 格式上定义了几个命令。在 USB 和 Bluetooth 上都加了几个小的 Header，而 NFC 上则是规定了一个 AID。这对应用程序来说很方便，核心的命令只有一套，需要的时候封装一下即可。

## FIDO2

在之后，[FIDO2](https://fidoalliance.org/specs/fido-v2.0-rd-20170927/fido-client-to-authenticator-protocol-v2.0-rd-20170927.html#message-encoding) 出现了，在保持 U2F 兼容的基础上添加了新的功能，并且出现了 WebAuthN 作为浏览器使用 FIDO2 的协议。U2F 就变成了第一代的 CTAP，称为 CTAP1，然后 CTAP 默认指的就是 CTAP2。

### 命令格式

FIDO2 里面，定义了一些 CTAP 命令，比如 authenticatorMakeCredential，对应 U2F 的 U2F_REGISTER 命令。然后，规定了一个 [CBOR](https://tools.ietf.org/html/rfc7049) 的格式，来表示命令附带的数据。CBOR 是 RFC 7049，所以也是借用过来的格式。

### 传输方式

FIDO2 定义了在 USB 和 NFC 上的传输格式。

#### USB

在 USB 上传输的时候，定义了 CTAPHID 的协议，与 U2FHID 基本是一样的，规定了 init packet 和 continuation packet，packet 里面也是 CTAPHID 的消息，这部分是兼容 U2F 的。并且，额外添加了 CTAPHID_CBOR 消息：

| CMD          | BCNT     | DATA         | DATA + 1             |
| ------------ | -------- | ------------ | -------------------- |
| CTAPHID_CBOR | 1..(n+1) | CTAP command | n bytes of CBOR data |

它的载荷就是 CBOR 格式的请求。

类似地，它也是通过 Interrupt OUT 发送请求，从 Interrupt IN 读取回应。

#### NFC

在 NFC 上传输的时候，因为内部的格式是 CBOR，不再是 APDU 了，所以需要一些封装。

首先，它也定义了一个 Applet ID：`A0000006472F0001`，和 U2F 一样。为了保持兼容，它都支持 U2F 定义的 APDU 命令。

那怎么区分设备是否支持 CTAP1/U2F 和 CTAP2 呢？使用前面提到的 U2F_VERSION 命令即可。如果得到 U2F_V2，说明是支持 CTAP1/U2F 的；如果得到是其他的，说明只支持 CTAP2，不支持 CTAP1/U2F。

如果要发 CTAP2 的命令，就要把 CTAP command 和 CBOR 格式的数据封装到 APDU 里面：

| CLA  | INS  | P1   | P2   | Data                        | Le       |
| ---- | ---- | ---- | ---- | --------------------------- | -------- |
| 80   | 10   | 00   | 00   | CTAP Command \|\| CBOR Data | variable |

它规定，如果请求采用的是 extended length 的 APDU，那么响应也要是 extended length 的 APDU；如果请求是 short APDU，那么响应也要支持 short APDU 的 chaining。

### 兼容性

可以看到，CTAP2 设计的基本都考虑了兼容 U2F，允许用 U2F 的 API 操作 U2F 和 CTAP2 的设备；也允许用 CTAP2 的 API 操作 U2F（只支持部分命令）和  CTAP2 的设备。

## 总结

可以看到，这里有一堆套娃的过程：

U2F：

|      | USB HID        | Bluetooth | NFC                   |
| ---- | -------------- | --------- | --------------------- |
| 4    | APDU           | APDU      | APDU                  |
| 3    | U2F message    |           |                       |
| 2    | USB HID packet |           |                       |
| 1    | USB            | Bluetooth | ISO 14443-4/ISO 18092 |

FIDO2:

|      | USB HID                  | NFC                      |
| ---- | ------------------------ | ------------------------ |
| 4    | CTAP command + CBOR data | CTAP command + CBOR data |
| 3    | CTAP message             | APDU                     |
| 2    | USB HID packet           |                          |
| 1    | USB                      | ISO 14443-4/ISO 18092    |

