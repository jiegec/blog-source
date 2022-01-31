---
layout: post
date: 2022-01-30 20:50:00 +0800
tags: [windows,vmware,m1,vm]
category: os
title: 在 M1 上运行 Windows ARM 虚拟机
---

目前 Windows ARM 出了预览版，可以从 [Windows Insider Preview Downloads](https://www.microsoft.com/en-us/software-download/windowsinsiderpreviewARM64) 下载，得到一个 9.5GB 的 vhdx 文件。

接着，用 qemu-img 转换为 vmdk 格式：

```shell
$ qemu-img convert Windows11_InsiderPreview_Client_ARM64_en-us_22533.vhdx -O vmdk -o adapter_type=lsilogic Windows11_InsiderPreview_Client_ARM64_en-us_22533.vmdk
```

转换后，在 VMWare Fusion for Apple Silicon Tech Preview 中，选择从已有的 vmdk 中创建虚拟机，启动前修改一些设置，特别是内存，默认 256MB 肯定不够，默认单核 CPU 也太少了一些。内存不足可能导致安装失败，记住要第一次启动前设置。

启动以后会无法访问网络，按照下面网页里的方法设置网络：

https://www.gerjon.com/vmware/vmware-fusion-on-apple-silicion-m1/

需要注意的是，bcdedit 选项填的 IP 地址一般是 bridge 上的地址，比如 bridge101 的地址。

然后就可以正常工作了！

在 [VMWare 论坛里](https://communities.vmware.com/t5/Fusion-for-Apple-Silicon-Tech/Vmware-Fusion-Apple-Silicon-Support-Windows/m-p/2868331)，还谈到了下面几个问题的解决方法：

为了让声音工作，可以修改 vmx 文件，设置 guestOS：

```
guestOS = "arm-windows11-64"
```

这样声音就可以正常播放了。

分辨率的问题，可以用 RDP 来解决：首先在虚拟机里打开 Remote Desktop，然后用 macOS 的 Microsoft Remote Desktop Beta 访问即可。

系统里没有 Microsoft Store，要安装的话，用命令行的 Powershell 执行下面的命令：

```
wsreset.exe -i
```

这个方法见 [Parallels Desktop KB128520](https://kb.parallels.com/128520)。