---
layout: post
date: 2023-10-31
tags: [apple,cpu]
categories:
    - hardware
---

# Apple 处理器

## M 系列

| 名称     | CPU 核心  | GPU 核心 | 神经网络引擎 | 内存带宽        | 内存大小                  |
|----------|-----------|----------|--------------|-----------------|---------------------------|
| M1       | 4+4       | 7/8      | 16           |                 | 8GB/16GB                  |
| M1 Pro   | 6+2/8+2   | 14/16    | 16           | 200GB/s         | 16GB/32GB                 |
| M1 Max   | 8+2       | 24/32    | 16           | 400GB/s         | 32GB/64GB                 |
| M1 Ultra | 16+4      | 48/64    | 32           | 800GB/s         | 64GB/128GB                |
| M2       | 4+4       | 8/10     | 16           | 100GB/s         | 8GB/16GB/24GB             |
| M2 Pro   | 6+4/8+4   | 16/19    | 16           | 200GB/s         | 16GB/32GB                 |
| M2 Max   | 8+4       | 30/38    | 16           | 400GB/s         | 32GB/64GB/96GB            |
| M2 Ultra | 16+8      | 60/76    | 32           | 800GB/s         | 64GB/128GB/192GB          |
| M3       | 4+4       | 10       | 16           | 100GB/s         | 8GB/16GB/24GB             |
| M3 Pro   | 5+6/6+6   | 14/18    | 16           | 150GB/s         | 18GB/36GB                 |
| M3 Max   | 10+4/12+4 | 30/40    | 16           | 300GB/s/400GB/s | 36GB/48GB/64GB/96GB/128GB |

来源：

- [MacBook Pro (14-inch, 2021) - Technical Specifications](https://support.apple.com/kb/SP854?viewlocale=en_US&locale=en_US)
- [iMac (24-inch, M1, 2021) - Technical Specifications](https://support.apple.com/kb/SP839?viewlocale=en_US&locale=en_US)
- [MacBook Air (M2, 2022) - Technical Specifications](https://support.apple.com/kb/SP869?viewlocale=en_US&locale=en_US)
- [MacBook Pro (16-inch, 2023) - Technical Specifications](https://support.apple.com/kb/SP890?viewlocale=en_US&locale=en_US)
- [Mac mini (2023) - Technical Specifications](https://support.apple.com/kb/SP891?viewlocale=en_US&locale=en_US)
- [Mac Studio (2022) - Technical Specifications](https://support.apple.com/kb/SP865?locale=en_US)
- [Mac Studio (2023) - Technical Specifications](https://support.apple.com/kb/SP894?locale=en_US)

/proc/cpuinfo:

Apple M1 Firestorm:

```
Features        : fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid asimdrdm jscvt fcma lrcpc dcpop sha3 asimddp sha512 asimdfhm dit uscat ilrcpc flagm ssbs sb paca pacg dcpodp flagm2 frint
CPU implementer : 0x61
CPU architecture: 8
CPU variant     : 0x1
CPU part        : 0x023
CPU revision    : 1
```

Apple M1 Icestorm:

```
Features        : fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid asimdrdm jscvt fcma lrcpc dcpop sha3 asimddp sha512 asimdfhm dit uscat ilrcpc flagm ssbs sb paca pacg dcpodp flagm2 frint
CPU implementer : 0x61
CPU architecture: 8
CPU variant     : 0x1
CPU part        : 0x022
CPU revision    : 1
```

See also: https://github.com/util-linux/util-linux/blob/198e920aa24743ef6ace4e07cf6237de527f9261/sys-utils/lscpu-arm.c#L200.
