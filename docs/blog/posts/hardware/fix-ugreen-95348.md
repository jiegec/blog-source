---
layout: post
date: 2026-09-12
tags: [ugreen,hdmi,capture]
categories:
    - misc
---

# 修复绿联 UG307-95348 HDMI 采集卡清晰度与颜色问题

## 背景

[上文](../misc/classroom-routing.md) 提到，我打算用采集卡来录制鸿蒙电脑的输出，作为 OBS 的输入来做软件导播，用的采集卡型号是[采用了 MS2130S 芯片的绿联 UG307-95348 采集卡](https://www.lulian.cn/product/1537.html)。在使用过程中，遇到了清晰度和颜色的问题，下面介绍我是怎么研究和解决的。

<!-- more -->

## 清晰度问题

首先是遇到了清晰度问题，在 macOS 上为 OBS 设置采集卡输入时，需要关闭 Use Preset 选项，选择 `3840x2160 (16:9) - 30, 60 FPS - CS 709 - NV12 (420v)`，而不是 `3840x2160 (16:9) - 30 FPS - CS 709 - NV12 (420v)`。后者明显更糊，尽管从名称上看似乎只差一个帧率。如果勾选了 Use Preset，分辨率选 `3820x2160`，效果和上面第二种 4K 选项一样，也有些糊。

用下面这个 Swift 脚本打印采集卡的各种信息，可以发现 60 FPS 的那个版本经过了 MJPEG 压缩，从 dmb1 字段即可看出：

```shell
$ swift list_formats.swift
  3840x2160  420v  fps=30.0..30.0  dur=33333..33333us
      ext CVImageBufferColorPrimaries = ITU_R_709_2
      ext CVImageBufferTransferFunction = SMPTE_240M_1995
      ext CVImageBufferYCbCrMatrix = ITU_R_709_2
  3840x2160  420v  fps=60.0..60.0  dur=16667..16667us  fps=30.0..30.0  dur=33333..33333us
      ext CVImageBufferColorPrimaries = ITU_R_709_2
      ext CVImageBufferTransferFunction = SMPTE_240M_1995
      ext CVImageBufferYCbCrMatrix = ITU_R_709_2
      ext com.apple.cmio.format_extension.decompressed_from_format_type = 1684890161 (dmb1)
$ cat list_formats.swift
import AVFoundation
import CoreMedia

func fourcc(_ v: FourCharCode) -> String {
  let b: [UInt8] = [
    UInt8((v >> 24) & 255), UInt8((v >> 16) & 255),
    UInt8((v >> 8) & 255), UInt8(v & 255),
  ]
  let s = String(bytes: b, encoding: .ascii) ?? "?"
  return s.allSatisfy { $0.isLetter || $0.isNumber } ? s : String(format: "0x%08x", v)
}

let session = AVCaptureDevice.DiscoverySession(
  deviceTypes: [.external],
  mediaType: .video,
  position: .unspecified)

for d in session.devices {
  print("DEVICE \(d.localizedName) [\(d.uniqueID)]")
  print("  model=\(d.modelID)  manufacturer=\(d.manufacturer)")

  for f in d.formats {
    let dim = CMVideoFormatDescriptionGetDimensions(f.formatDescription)
    let sub = CMFormatDescriptionGetMediaSubType(f.formatDescription)

    var line = "  \(dim.width)x\(dim.height)  \(fourcc(sub))"
    for r in f.videoSupportedFrameRateRanges {
      line += String(
        format: "  fps=%.1f..%.1f  dur=%.0f..%.0fus",
        r.minFrameRate, r.maxFrameRate,
        CMTimeGetSeconds(r.minFrameDuration) * 1e6,
        CMTimeGetSeconds(r.maxFrameDuration) * 1e6)
    }
    print(line)

    if let ext = CMFormatDescriptionGetExtensions(f.formatDescription) as? [String: Any] {
      for k in ext.keys.sorted() {
        var v = "\(ext[k]!)"
        // decode fourcc-valued extensions such as
        //   com.apple.cmio.format_extension.decompressed_from_format_type
        if k.contains("format_type"), let n = ext[k] as? NSNumber {
          v = "\(n.uint32Value) (\(fourcc(n.uint32Value)))"
        }
        print("      ext \(k) = \(v)")

      }
    }
  }
}
```

猜想压缩的版本，实际的分辨率更高，经过压缩后可以通过 USB 5Gbps 正常传输；不压缩的版本，由于带宽限制，内部不是真正按照 4K@30Hz 处理的，导致画质有损耗。

## 颜色问题

除了清晰度问题，采集卡采到的鸿蒙电脑画面颜色不对。在鸿蒙电脑上打开 [Lagom 白饱和测试图](http://www.lagom.nl/lcd-test/zhs_white.php)，采集到的 RGB 与预期对不上，大致关系如下：

- 原来 200 -> 显示 219
- 原来 244 -> 显示 255

用 ffmpeg 观察后发现，采集卡实际给出的是 204；由于这是 limited range（16-235）下的 204，转换到 full range 后就是 `(204 - 16) / 219 * 255 = 219`。若把鸿蒙电脑直接接到显示器上，显示则正常。

深入研究后，我找到了一些通过设置 MS2130S 寄存器来改变其行为的方法（参考 [steve-m/hsdaoh](https://github.com/steve-m/hsdaoh/blob/master/src/libhsdaoh.c)）。在 AI 的帮助下定位到了问题：只要关闭 MS2130S 自带的 luma processing（即把寄存器 0xfc8e 从原来的 0x00 改为 0x11），颜色就会恢复正常。下面这个小工具可以在 OBS 开始录制后运行，用来 toggle luma processing，从而实时看到颜色变化：

```c++
/*
 * ugreen_fix_toggle - minimal hidapi-only tool for the UGREEN 95348
 *                     (MS2130S, 2b89:5348).
 *
 * Reads a video-processing register and toggles it:
 *   0x00 -> 0x11   (disable the chip's luma processing / fix the 200->219 lift)
 *   0x11 -> 0x00   (re-enable it / reproduce the bug)
 *
 * Default register is 0xfc8e (confirmed to be the luma-processing register).
 * Pass another address as the first argument if needed, e.g.
 *   ./ugreen_fix_toggle 0xfc80
 *
 * build (macOS/homebrew, hidapi only):
 *   cc -O2 -I/opt/homebrew/include/hidapi ugreen_fix_toggle.c \
 *      -L/opt/homebrew/lib -lhidapi -o ugreen_fix_toggle
 */
#include <hidapi.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define VID 0x2b89
#define PID 0x5348
#define DEFAULT_REG 0xfc8e

static hid_device *h;

/* MS2130S vendor HID feature report:
 *   [0x01, 0xb6, addrH, addrL, val, 0, 0, 0, 0]  write
 *   [0x01, 0xb5, addrH, addrL, 0, 0, 0, 0, 0]    read request
 * GET_REPORT returns 64 bytes; the value is byte 4. */
static int reg_write(uint16_t addr, uint8_t val) {
  unsigned char buf[9] = {0x01, 0xb6, addr >> 8, addr & 0xff, val, 0, 0, 0, 0};
  return hid_send_feature_report(h, buf, sizeof(buf));
}

static int reg_read(uint16_t addr, uint8_t *val) {
  unsigned char cmd[9] = {0x01, 0xb5, addr >> 8, addr & 0xff, 0, 0, 0, 0, 0};
  unsigned char rsp[64];

  if (hid_send_feature_report(h, cmd, sizeof(cmd)) < 0)
    return -1;
  memset(rsp, 0, sizeof(rsp));
  rsp[0] = 0x01;
  if (hid_get_feature_report(h, rsp, sizeof(rsp)) < 0)
    return -1;
  *val = rsp[4];
  return 0;
}

int main(int argc, char **argv) {
  uint16_t addr = DEFAULT_REG;
  uint8_t cur, next;

  if (argc > 1)
    addr = (uint16_t)strtoul(argv[1], NULL, 0);

  if (hid_init() < 0) {
    fprintf(stderr, "hid_init failed\n");
    return 1;
  }
  h = hid_open(VID, PID, NULL);
  if (!h) {
    fprintf(stderr, "UGREEN %04x:%04x not found (is it plugged in?)\n", VID,
            PID);
    return 1;
  }

  if (reg_read(addr, &cur) < 0) {
    fprintf(stderr, "register read failed: %ls\n", hid_error(h));
    hid_close(h);
    return 1;
  }

  if (cur == 0x00) {
    next = 0x11;
  } else if (cur == 0x11) {
    next = 0x00;
  } else {
    fprintf(stderr, "%04x = 0x%02x (unexpected, not touching)\n", addr, cur);
    hid_close(h);
    return 2;
  }

  if (reg_write(addr, next) < 0) {
    fprintf(stderr, "register write failed: %ls\n", hid_error(h));
    hid_close(h);
    return 1;
  }

  printf("%04x: 0x%02x -> 0x%02x\n", addr, cur, next);
  printf("(0x11 = luma processing disabled = fix on; 0x00 = default/bug)\n");

  hid_close(h);
  hid_exit();
  return 0;
}
```

编译和运行：

```shell
$ brew install hidapi
$ cc -O2 -I/opt/homebrew/include/hidapi ugreen_fix_toggle.c -L/opt/homebrew/lib -lhidapi -o ugreen_fix_toggle
# 此时是有问题的状态
$ ./ugreen_fix_toggle
fc8e: 0x00 -> 0x11
(0x11 = luma processing disabled = fix on; 0x00 = default/bug)
# toggle 以后，颜色问题修复
$ ./ugreen_fix_toggle
fc8e: 0x11 -> 0x00
(0x11 = luma processing disabled = fix on; 0x00 = default/bug)
# 再次 toggle，颜色问题重新出现
```

修复后，200 变成 199，244 变成 243。虽然仍有很小的偏差，但可以认为问题已经解决。

不过每次开始采集后都要重新跑一次这个工具，还是有点麻烦。一个一劳永逸的办法是参考 [steve-m/ms2130_patcher](https://github.com/steve-m/ms2130_patcher/blob/master/ms2130_patch.c)，给固件打补丁，让硬件往 0xfc8e 寄存器写入 0x11 而不是 0x00。

首先用 [steve-m/ms213x_flash](https://github.com/steve-m/ms213x_flash) 导出绿联 95348 自带的固件，然后让 AI 进行逆向，这个固件就是一个 8051 代码，有很多成熟的工具。具体的补丁方法和上面类似，下面直接给出 AI 对固件代码以及如何修复的分析：

### 补丁的原理

#### 复位流程

`0xfc8e` 有两个相关的位：bit 0（掩码 `0x01`）和 bit 4（掩码 `0x10`）。流重初始化流程 `FUN_CODE_c220()` 会通过位掩码辅助函数 `FUN_CODE_87c7(mask, addrH, addrL, value)` 把这两位都清零。要写入的值通过 `R3` 传入：非零表示置位被掩码选中的位，零表示清零。

| CPU 地址（bank 1） | 代码 | 作用 |
|---|---|---|
| `c268` | `MOV R3,#01h ; JNB bit05,c26f ; MOV R3,#00h`<br>`MOV R5,#01h ; MOV R7,#8eh ; MOV R6,#fch ; LJMP 87c7h` | 清除 `0xfc8e` 的 bit 0 |
| `c27e` | `MOV R3,#01h ; JNB bit05,c285 ; MOV R3,#00h`<br>`MOV R5,#10h ; MOV R7,#8eh ; MOV R6,#fch ; LJMP 87c7h` | 清除 `0xfc8e` 的 bit 4 |

两次调用之后 `0xfc8e = 0x00`。与之配套的 `0xfc8f`（色度）在 `c294`/`c2a4` 处的写入**不**受影响；修复灰度只需要改 `0xfc8e`。

#### 具体改动

把两处 `MOV R3,#00h`（`7b 00`）指令改成 `MOV R3,#01h`（`7b 01`），这样每次掩码更新都会走*置位*分支，寄存器最终变成 `0x11`。

| 文件偏移 | 原始值 | 补丁值 | 含义 |
|---:|---:|---:|---|
| `0x1429e`（bank1 `c26e`） | `00` | `01` | `0xfc8e` bit 0 的取值操作数 |
| `0x142b4`（bank1 `c284`） | `00` | `01` | `0xfc8e` bit 4 的取值操作数 |
| `0x18033` | `7c` | `7e` | 代码校验和 `0x797c` → `0x797e` |

反汇编打过补丁的字节，可以看到两处立即数现在都加载 `0x01`：

```console
c268: 7b01  MOV R3, #01h
c26a: 300502 JNB bit05, c26fh
c26d: 7b01  MOV R3, #01h      <- 原来是 #00h
c26f: 7d01  MOV R5, #01h
c271: 7f8e  MOV R7, #8eh
c273: 7efc  MOV R6, #fch
c275: 0287c7 LJMP 87c7h
```

### 小结

核心就是把上面我通过 hidapi 从 host 端写入寄存器的操作，换成了直接在固件里写入：固件本来是 clear，改成了 set，这样就禁用了 luma processing，持久化了这个改动。

这部分代码以及固件已经开源到 [jiegec/ugreen-95348-patcher](http://github.com/jiegec/ugreen-95348-patcher)，感兴趣的读者可以尝试一下，尝试之前记得备份固件，而且有变砖的风险。

## 总结

其实 MS2130S 这款芯片在网络上已经有很多现成的研究，从寄存器用法、hidapi 访问到固件补丁，都能找到前人的成果。这次能比较顺利地定位并解决问题，很大程度上是站在这些探索的肩膀上，在此对这些作者表示感谢。

相关项目链接整理如下：

- [steve-m/hsdaoh](https://github.com/steve-m/hsdaoh)：通过 hidapi 访问 MS2130S 寄存器的库，本文从 host 端修改 `0xfc8e` 的思路就来自这里。
- [steve-m/ms2130_patcher](https://github.com/steve-m/ms2130_patcher)：直接给固件打补丁、持久化寄存器配置的工具，是本文固件补丁的重要参考。
- [steve-m/ms213x_flash](https://github.com/steve-m/ms213x_flash)：用来导出/烧写 MS213x 固件的工具，本文用它导出了绿联 95348 的原始固件。

这些项目大多出自 [steve-m](https://github.com/steve-m) 之手，感谢他的开源工作。
