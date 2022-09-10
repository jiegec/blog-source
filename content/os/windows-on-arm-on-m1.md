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

UPDATE:

VMware Fusion 发布了新版本 [22H2](https://blogs.vmware.com/teamfusion/2022/07/just-released-vmware-fusion-22h2-tech-preview.html)，有官方的 Windows 11 on ARM 支持了：

- Windows 11 on Intel and Apple Silicon with 2D GFX and Networking
- VMtools installation for Windows 11 GOS on M1
- Improved Linux support on M1
- 3D Graphics HW Acceleration and OpenGL 4.3 in Linux VMs* (Requires Linux 5.19+ & Mesa 22.1.3+)
- Virtual TPM Device
- Fast Encryption
- Universal Binary

并且不需要上面写的网卡的 workaround 了：

	vmxnet3 Networking Drivers for Windows on ARM
	
	While Windows does not yet ship with our vmxnet3 networking driver for
	Windows on ARM as it now does for Intel, the VMware Tools ISO on ARM
	contains the 2 currently supported drivers for graphics and networking.

实测安装 VMware Tools 以后，就可以成功用 vmxnet3 网卡上网了，不需要之前的 bcdedit 方案。

但是目前测试 Linux 虚拟机有一些问题，一些内核版本在启动的时候 vmwgfx 驱动会报错，不能正常显示，但是系统是正常启动的，可以通过 SSH 访问。我测试的情况见下：

Linux 5.19.6(5.19.0-1-arm64): 可以正常启动和显示

Linux 5.18(5.18.0-0.bpo.1-arm64): `VMware Fusion has encountered an error and has shut down the virtual machine`

Linux 5.16(5.16.0-0.bpo.4-arm64): SSH 也没启动，看不到内核日志

Linux 5.15.15(5.15.0-0.bpo.3-arm64):

```
[   10.765945] kernel BUG at drivers/gpu/drm/vmwgfx/vmwgfx_drv.h:1627!
[   10.766206] Call trace:
[   10.766207]  vmw_event_fence_action_queue+0x328/0x330 [vmwgfx]
[   10.766210]  vmw_stdu_primary_plane_atomic_update+0xd8/0x220 [vmwgfx]
[   10.766214]  drm_atomic_helper_commit_planes+0xf8/0x21c [drm_kms_helper]
[   10.766222]  drm_atomic_helper_commit_tail+0x5c/0xb0 [drm_kms_helper]
[   10.766225]  commit_tail+0x160/0x190 [drm_kms_helper]
[   10.766227]  drm_atomic_helper_commit+0x16c/0x400 [drm_kms_helper]
[   10.766230]  drm_atomic_commit+0x58/0x6c [drm]
[   10.766242]  drm_atomic_helper_set_config+0xe0/0x120 [drm_kms_helper]
[   10.766245]  drm_mode_setcrtc+0x1ac/0x680 [drm]
[   10.766249]  drm_ioctl_kernel+0xd0/0x120 [drm]
[   10.766253]  drm_ioctl+0x250/0x460 [drm]
[   10.766257]  vmw_generic_ioctl+0xbc/0x160 [vmwgfx]
[   10.766261]  vmw_unlocked_ioctl+0x24/0x30 [vmwgfx]
[   10.766264]  __arm64_sys_ioctl+0xb4/0x100
[   10.766287]  invoke_syscall+0x50/0x120
[   10.766300]  el0_svc_common.constprop.0+0x4c/0xf4
[   10.766302]  do_el0_svc+0x30/0x9c
[   10.766303]  el0_svc+0x28/0xb0
[   10.766327]  el0t_64_sync_handler+0x1a4/0x1b0
[   10.766328]  el0t_64_sync+0x1a0/0x1a4
```