---
layout: post
date: 2018-10-04
tags: [gpg,gpgmail,macos,radare2]
categories:
    - software
---

# 绕过 GPGMail 的激活检测

前段时间 GPGMail [宣布不再免费](https://gpgtools.org/support-plan)，在三十天的试用期后就不给用了。唉，可能是官方实在没钱维护了，也可能是官方想赚钱了。不过，既然 GPGMail 采用的是[自由的许可证](https://github.com/GPGTools/GPGMail/blob/high-sierra/LICENSE.txt)，意味着我们可以自己对代码进行更改。和许可证验证相关的[代码](https://github.com/GPGTools/GPGMail/blob/c08ce21eee08a1089c82c04af1fab5b85d72de68/Source/GPGMailBundle.m#L846)如下：

```
- (BOOL)hasActiveContract {
    NSDictionary *contractInformation = [self contractInformation];
    return [contractInformation[@"Active"] boolValue];
}
```

我们只要改成 `return TRUE` ，在自己的电脑上手动编译、并复制到 `/Library/Application Support/GPGTools/GPGMail` 下即可。

另：还有一个直接对二进制打 patch 的方法（仍然符合许可证），利用了最近打 CTF 学到的一些知识。找到以上这个函数，然后把返回值修改成非零即可。这里就不提供方法了。最后的更改：

```
$ radiff2 -D
--- 0x0000282f  410fbec7
- movsx eax, r15b
+++ 0x0000282f  4c89e090
+ mov rax, r12
+ nop
```

当然了，还需要额外 `codesign --remove-signature` 一下。

谨慎对非自由软件采用这个方法。可能有法律风险。
