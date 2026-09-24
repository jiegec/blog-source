---
layout: post
date: 2026-09-12
tags: [ugreen,hdmi,capture]
categories:
    - hardware
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
```

对应的 Swift 源码：

```swift
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

两次调用之后 `0xfc8e = 0x00`。

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

P.S. 实测发现，把 `0xfc8e` 改为 `0x11` 只对 `3840x2160 (16:9) - 30, 60 FPS - CS 709 - NV12 (420v)` 模式生效；对 `3840x2160 (16:9) - 30 FPS - CS 709 - NV12 (420v)` 模式则无效：前者画面清晰、颜色正确，后者画面模糊、颜色也不对。具体原因尚未深入分析。

## 总结

其实 MS2130S 这款芯片在网络上已经有很多现成的研究，从寄存器用法、hidapi 访问到固件补丁，都能找到前人的成果。这次能比较顺利地定位并解决问题，很大程度上是站在这些探索的肩膀上，在此对这些作者表示感谢。

相关项目链接整理如下：

- [steve-m/hsdaoh](https://github.com/steve-m/hsdaoh)：通过 hidapi 访问 MS2130S 寄存器的库，本文从 host 端修改 `0xfc8e` 的思路就来自这里。
- [steve-m/ms2130_patcher](https://github.com/steve-m/ms2130_patcher)：直接给固件打补丁、持久化寄存器配置的工具，是本文固件补丁的重要参考。
- [steve-m/ms213x_flash](https://github.com/steve-m/ms213x_flash)：用来导出/烧写 MS213x 固件的工具，本文用它导出了绿联 95348 的原始固件。

这些项目大多出自 [steve-m](https://github.com/steve-m) 之手，感谢他的开源工作。

## 附录

以下是这个采集卡的 EDID：

```
00ffffffffffff0054f248538d0135012b230103803c2278022895a7554ea3260f5054010000d1c081c0010001000100010001000100023a801871382d40582c4500c48e2100001e9c45007251d01e206e28550055502100001e000000fd0018501e641e000a202020202020000000fc0055475245454e2d39353334380a01c002032d724c1f222120133e3d3c5f64676223090707830100006d030c001000003c200060010203e50e616066656a5e00a0a0a0295030202500b0133200000019640080a3a02b50b0103510b01332000000352f00a0a0a0295030202500b001320000000000000000000000000000000000000000000000000000000000000058
```

用 [edid-decode](https://people.freedesktop.org/~imirkin/edid-decode/) 出来的结果：

```
edid-decode (hex):

00 ff ff ff ff ff ff 00 54 f2 48 53 8d 01 35 01
2b 23 01 03 80 3c 22 78 02 28 95 a7 55 4e a3 26
0f 50 54 01 00 00 d1 c0 81 c0 01 00 01 00 01 00
01 00 01 00 01 00 02 3a 80 18 71 38 2d 40 58 2c
45 00 c4 8e 21 00 00 1e 9c 45 00 72 51 d0 1e 20
6e 28 55 00 55 50 21 00 00 1e 00 00 00 fd 00 18
50 1e 64 1e 00 0a 20 20 20 20 20 20 00 00 00 fc
00 55 47 52 45 45 4e 2d 39 35 33 34 38 0a 01 c0

02 03 2d 72 4c 1f 22 21 20 13 3e 3d 3c 5f 64 67
62 23 09 07 07 83 01 00 00 6d 03 0c 00 10 00 00
3c 20 00 60 01 02 03 e5 0e 61 60 66 65 6a 5e 00
a0 a0 a0 29 50 30 20 25 00 b0 13 32 00 00 00 19
64 00 80 a3 a0 2b 50 b0 10 35 10 b0 13 32 00 00
00 35 2f 00 a0 a0 a0 29 50 30 20 25 00 b0 01 32
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 58

----------------

Block 0, Base EDID:
  EDID Structure Version & Revision: 1.3
  Vendor & Product Identification:
    Manufacturer: UGR
    Model: 21320
    Serial Number: 20251021
    Made in: week 43 of 2025
  Basic Display Parameters & Features:
    Digital display
    Maximum image size: 60 cm x 34 cm
    Gamma: 2.20
    Monochrome or grayscale display
    First detailed timing is the preferred timing
  Color Characteristics:
    Red  : 0.6523, 0.3339
    Green: 0.3066, 0.6367
    Blue : 0.1503, 0.0595
    White: 0.3134, 0.3291
  Established Timings I & II:
    DMT 0x09:   800x600    60.316541 Hz   4:3     37.879 kHz     40.000000 MHz
  Standard Timings:
    DMT 0x52:  1920x1080   60.000000 Hz  16:9     67.500 kHz    148.500000 MHz
    DMT 0x55:  1280x720    60.000000 Hz  16:9     45.000 kHz     74.250000 MHz
  Detailed Timing Descriptors:
    DTD 1:  1920x1080   60.000000 Hz  16:9     67.500 kHz    148.500000 MHz (708 mm x 398 mm)
                 Hfront   88 Hsync  44 Hback  148 Hpol P
                 Vfront    4 Vsync   5 Vback   36 Vpol P
    DTD 2:  1280x720   144.000000 Hz  16:9    108.000 kHz    178.200000 MHz (597 mm x 336 mm)
                 Hfront  110 Hsync  40 Hback  220 Hpol P
                 Vfront    5 Vsync   5 Vback   20 Vpol P
    Display Range Limits:
      Monitor ranges (GTF): 24-80 Hz V, 30-100 kHz H, max dotclock 300 MHz
    Display Product Name: 'UGREEN-95348'
  Extension blocks: 1
Checksum: 0xc0

----------------

Block 1, CTA-861 Extension Block:
  Revision: 3
  Basic audio support
  Supports YCbCr 4:4:4
  Supports YCbCr 4:2:2
  Native detailed modes: 2
  Video Data Block:
    VIC  31:  1920x1080   50.000000 Hz  16:9     56.250 kHz    148.500000 MHz
    VIC  34:  1920x1080   30.000000 Hz  16:9     33.750 kHz     74.250000 MHz
    VIC  33:  1920x1080   25.000000 Hz  16:9     28.125 kHz     74.250000 MHz
    VIC  32:  1920x1080   24.000000 Hz  16:9     27.000 kHz     74.250000 MHz
    VIC  19:  1280x720    50.000000 Hz  16:9     37.500 kHz     74.250000 MHz
    VIC  62:  1280x720    30.000000 Hz  16:9     22.500 kHz     74.250000 MHz
    VIC  61:  1280x720    25.000000 Hz  16:9     18.750 kHz     74.250000 MHz
    VIC  60:  1280x720    24.000000 Hz  16:9     18.000 kHz     59.400000 MHz
    VIC  95:  3840x2160   30.000000 Hz  16:9     67.500 kHz    297.000000 MHz
    VIC 100:  4096x2160   30.000000 Hz 256:135   67.500 kHz    297.000000 MHz
    VIC 103:  3840x2160   24.000000 Hz  64:27    54.000 kHz    297.000000 MHz
    VIC  98:  4096x2160   24.000000 Hz 256:135   54.000 kHz    297.000000 MHz
  Audio Data Block:
    Linear PCM:
      Max channels: 2
      Supported sample rates (kHz): 48 44.1 32
      Supported sample sizes (bits): 24 20 16
  Speaker Allocation Data Block:
    FL/FR - Front Left/Right
  Vendor-Specific Data Block (HDMI), OUI 00-0C-03:
    Source physical address: 1.0.0.0
    Maximum TMDS clock: 300 MHz
    Extended HDMI video details:
      HDMI VICs:
        HDMI VIC 1:  3840x2160   30.000000 Hz  16:9     67.500 kHz    297.000000 MHz
        HDMI VIC 2:  3840x2160   25.000000 Hz  16:9     56.250 kHz    297.000000 MHz
        HDMI VIC 3:  3840x2160   24.000000 Hz  16:9     54.000 kHz    297.000000 MHz
  YCbCr 4:2:0 Video Data Block:
    VIC  97:  3840x2160   60.000000 Hz  16:9    135.000 kHz    594.000000 MHz
    VIC  96:  3840x2160   50.000000 Hz  16:9    112.500 kHz    594.000000 MHz
    VIC 102:  4096x2160   60.000000 Hz 256:135  135.000 kHz    594.000000 MHz
    VIC 101:  4096x2160   50.000000 Hz 256:135  112.500 kHz    594.000000 MHz
  Detailed Timing Descriptors:
    DTD 3:  2560x1440   60.000199 Hz  16:9     88.860 kHz    241.700000 MHz (analog composite, sync-on-green, 944 mm x 531 mm)
                 Hfront   48 Hsync  32 Hback   80 Hpol N
                 Vfront    2 Vsync   5 Vback   34 Vpol N
    DTD 4:  2560x1440   49.997581 Hz  16:9     74.146 kHz    256.250000 MHz (analog composite, sync-on-green, 944 mm x 531 mm)
                 Hfront  176 Hsync 272 Hback  448 Hpol N
                 Vfront    3 Vsync   5 Vback   35 Vpol N
    DTD 5:  2560x1440   30.000099 Hz  16:9     44.430 kHz    120.850000 MHz (analog composite, sync-on-green, 944 mm x 513 mm)
                 Hfront   48 Hsync  32 Hback   80 Hpol N
                 Vfront    2 Vsync   5 Vback   34 Vpol N
Checksum: 0x58

----------------

Preferred Video Timing if only Block 0 is parsed:
  DTD   1:  1920x1080   60.000000 Hz  16:9     67.500 kHz    148.500000 MHz (708 mm x 398 mm)
                 Hfront   88 Hsync  44 Hback  148 Hpol P
                 Vfront    4 Vsync   5 Vback   36 Vpol P

----------------

Preferred Video Timings if Block 0 and CTA-861 Blocks are parsed:
  DTD   1:  1920x1080   60.000000 Hz  16:9     67.500 kHz    148.500000 MHz (708 mm x 398 mm)
                 Hfront   88 Hsync  44 Hback  148 Hpol P
                 Vfront    4 Vsync   5 Vback   36 Vpol P
  VIC  31:  1920x1080   50.000000 Hz  16:9     56.250 kHz    148.500000 MHz
                 Hfront  528 Hsync  44 Hback  148 Hpol P
                 Vfront    4 Vsync   5 Vback   36 Vpol P

----------------

Native Video Resolution if only Block 0 is parsed:
  1920x1080

----------------

Native Video Resolutions if Block 0 and CTA-861 Blocks are parsed:
  1280x720
  1920x1080

----------------

edid-decode SHA: 84ddf9155376 2021-10-03 10:37:45

Warnings:

Block 1, CTA-861 Extension Block:
  IT Video Formats are overscanned by default, but normally this should be underscanned.

Failures:

Block 0, Base EDID:
  Standard Timings: Use 0x0101 as the invalid Standard Timings code, not 0x0100.
  Standard Timings: Use 0x0101 as the invalid Standard Timings code, not 0x0100.
  Standard Timings: Use 0x0101 as the invalid Standard Timings code, not 0x0100.
  Standard Timings: Use 0x0101 as the invalid Standard Timings code, not 0x0100.
  Standard Timings: Use 0x0101 as the invalid Standard Timings code, not 0x0100.
  Standard Timings: Use 0x0101 as the invalid Standard Timings code, not 0x0100.
  Detailed Timing Descriptor #1: Mismatch of image size 708x398 mm vs display size 600x340 mm.
Block 1, CTA-861 Extension Block:
  Detailed Timing Descriptor #3: Mismatch of image size 944x531 mm vs display size 600x340 mm.
  Detailed Timing Descriptor #4: Mismatch of image size 944x531 mm vs display size 600x340 mm.
  Detailed Timing Descriptor #5: Mismatch of image size 944x513 mm vs display size 600x340 mm.
  Required 640x480p60 timings are missing in the established timings and the SVD list (VIC 1).
  HDMI VIC Codes must have their CTA-861 VIC equivalents in the VSB.
  Missing VCDB, needed for Set Selectable RGB Quantization to avoid interop issues.
EDID:
  Base EDID: Some timings are out of range of the Monitor Ranges:
    Vertical Freq: 24.000 - 144.000 Hz (Monitor: 24.000 - 80.000 Hz)
    Horizontal Freq: 18.000 - 108.000 kHz (Monitor: 30.000 - 100.000 kHz)
  CTA-861: Native progressive timings are a mix of several resolutions.

EDID conformity: FAIL
```

也就是说，它的 4K 60Hz 从输入侧已经是 YCbCr 4:2:0 了，也就是每 2x2 的四个像素里，有四个 Y，一个 Cb 和一个 Cr。这样平均下来，8-bit 深度下每个像素的空间是 $(4*8+8+8)/4 = 12$ bit。如果是 4:2:2 的话，每 2x2 的四个像素里，有四个 Y，两个 Cb 和两个 Cr，平均下来，8-bit 深度下每个像素的空间是 $(4*8+2*8+2*8)/4 = 16$ bit。如果直接保存 RGB 4:4:4，8-bit 深度下就是 $3*8=24$ bit。
