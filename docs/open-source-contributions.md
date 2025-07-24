---
layout: page
date: 1970-01-01
permalink: /open-source-contributions/
---

# 开源软件贡献

记录我对开源软件的一些微小的贡献，以勉励自己，督促自己不忘为社区做贡献。

## Maintenance

我主要参与如下开源项目的维护：

- [AOSC-Dev](https://github.com/AOSC-Dev)
- [NixOS](https://github.com/nixos)
- [Termony](https://github.com/TermonyHQ)
- [canokeys](https://github.com/canokeys)
- [capstone-rs](https://github.com/capstone-rust)
- [lsof](https://github.com/lsof-org)
- [nfcim](https://github.com/nfcim)

## aosc-os-abbs

- [pull requests by jiegec](https://github.com/AOSC-Dev/aosc-os-abbs/pulls?q=is%3Apr+author%3Ajiegec)

## aws-cdk

- [feat(cloudfront): support Behavior-specific viewer protocol policy for CloudFrontWebDistribution](https://github.com/aws/aws-cdk/pull/16389)

## bandersnatch

- [Skip downloading based on file size and upload time instead of sha256sum](https://github.com/pypa/bandersnatch/pull/822)

## binutils

- [as: Add new estimated reciprocal instructions in LoongArch v1.1](https://sourceware.org/git/?p=binutils-gdb.git;a=commit;h=cd51849c90e8fd13779bec69f5d4c7aadf03a532)
- [as: Add new atomic instructions in LoongArch v1.1](https://sourceware.org/git/?p=binutils-gdb.git;a=commit;h=9ff4752d0f6d46ca0f7d275ea07e05790ac8dd1d)

## capstone

- [Add LoongArch support](https://github.com/capstone-engine/llvm-capstone/pull/47)
- [Initial auto-sync LoongArch support](https://github.com/capstone-engine/capstone/pull/2349)
- [Drop MatchByTypeName check in opIsPartOfiPTRPattern](https://github.com/capstone-engine/llvm-capstone/pull/79)

## cargo

- [Don't create hardlink for library test and integrations tests, fixing #7960](https://github.com/rust-lang/cargo/pull/7965)

## chiseltest

- [Fix VCS simulation binary path](https://github.com/ucb-bar/chiseltest/pull/430)
- [Fix issue #428: add blackbox sources to argument of icarus-verilog and vcs](https://github.com/ucb-bar/chiseltest/pull/429)
- [Fix VcsFlags not properly passed to vcs backend](https://github.com/ucb-bar/chiseltest/pull/426)

## delve

- [proc: use CPUID to determine ZMM_Hi256 region offset](https://github.com/go-delve/delve/pull/3831)

## DynamoRIO

- [i#2297: AARCH64: Implement mbr & cbr instrumentation](https://github.com/DynamoRIO/dynamorio/pull/7005)

## emacs

- [bug#23909: 25.1.50; `button-label' must be called in the buffer where ...](https://lists.gnu.org/archive/html/bug-gnu-emacs/2016-07/msg00307.html)
	- [button-* function doc string clarifications](https://github.com/emacs-mirror/emacs/commit/9eda79fc8c2b3e66ff6934ef0a8f2b747c27d245)

## flashrom

- [jlink_spi: add cs=tms option to jlink_spi programmer](https://github.com/flashrom/flashrom/commit/592c1c3e5fd9ae42a261966c82ddd83f777ce2b6)

## FloPoCo

- [two more bug fixes by Jiajie Chen](https://gitlab.com/flopoco/flopoco/-/commit/4672586b731b22562d2ce6994c5c78e41846a452)
- [Remove the duplicate code lines: R <= (bug reported by Jiajie Chen)](https://gitlab.com/flopoco/flopoco/-/commit/5ac83babf7d6a69cd3124a6127a98a0ac58c4508)
- [Commits by me](https://gitlab.com/flopoco/flopoco/-/commits/master?author=Jiajie%20Chen)

## force-riscv

- [Fixed compilation error: std::string and int64_t undefined](https://github.com/openhwgroup/force-riscv/pull/54)

## FreeBSD

- [Add kf_file_nlink field to kf_file and populate it](https://reviews.freebsd.org/D38169)

## gcc

- [LoongArch: extend.texi: Fix typos in LSX intrinsics](https://gcc.gnu.org/git/?p=gcc.git;a=commit;h=84ad1b5303dcfd95161f78add68b0b6b013536a5)

## gpaw

- [Fix issue #269 to add additional broadcast in some cases](https://gitlab.com/gpaw/gpaw/-/merge_requests/863)
- [Capture and ignore AttributeError thrown in getpreferredencoding() in newer Python versions](https://gitlab.com/gpaw/gpaw/-/merge_requests/858)

## gtkwave

- [Fix compilation under macOS for Nix](https://github.com/gtkwave/gtkwave/pull/136)

## homebrew-cask

- [Update notion to 1.0.5](https://github.com/Homebrew/homebrew-cask/pull/59122)
- [Add MacGesture v2.2.5](https://github.com/Homebrew/homebrew-cask/pull/57291)
- [Update next to 0.07](https://github.com/Homebrew/homebrew-cask/pull/42698)
- [Update bilibili to 2.14](https://github.com/Homebrew/homebrew-cask/pull/14330)
- [Update bilibili to 2.13](https://github.com/Homebrew/homebrew-cask/pull/14316)

## iproute2mac

- [Fix ip route for macOS Catalina issue #30 ](https://github.com/brona/iproute2mac/pull/31)

## iwd

- [[PATCH 1/2] knownnetworks: fix potential out of bounds write](https://lore.kernel.org/iwd/20230226062526.3115588-1-c@jia.je/T/#u)
	- [knownnetworks: fix printing SSID in hex](https://git.kernel.org/pub/scm/network/wireless/iwd.git/commit/?id=98b758f8934a95f961e3b5779bcc9b25b30ae97a)
	- [knownnetworks: fix potential out of bounds write](https://git.kernel.org/pub/scm/network/wireless/iwd.git/commit/?id=89309a862108c4caac41995b5fc76ade859d87a8)

## KiCad

- [libcontext: Initial support for Apple Silicon](https://gitlab.com/kicad/code/kicad/-/merge_requests/602)

## KNEM

- [driver/linux: use the pin API added in Linux 5.6](https://gitlab.inria.fr/knem/knem/-/commit/fa80cec4970514a6388fe165cc0c4167fd813228)

## litedram

- [Add support for clam shell topology](https://github.com/enjoy-digital/litedram/pull/332)

## litex

- [Add support for clam shell topology](https://github.com/enjoy-digital/litex/pull/1673)

## legacy-homebrew

- [emscripten 1.35.9](https://github.com/Homebrew/legacy-homebrew/pull/46005)
- [gnuradio 3.7.8.1](https://github.com/Homebrew/legacy-homebrew/pull/45598)
- [emscripten 1.35.2](https://github.com/Homebrew/legacy-homebrew/pull/45289)
- [emscripten 1.35.0](https://github.com/Homebrew/legacy-homebrew/pull/45186)
- [emscripten 1.34.12](https://github.com/Homebrew/legacy-homebrew/pull/44990)
- [emscripten 1.34.11](https://github.com/Homebrew/legacy-homebrew/pull/44611)
- [airspy 1.0.6](https://github.com/Homebrew/legacy-homebrew/pull/44581)
- [libbladerf 2015.07](https://github.com/Homebrew/legacy-homebrew/pull/44580)
- [uhd 003.009.000](https://github.com/Homebrew/legacy-homebrew/pull/43469)
- [uhd 003.008.005](https://github.com/Homebrew/legacy-homebrew/pull/42796)
- [hbase v0.89.9](https://github.com/Homebrew/legacy-homebrew/pull/35235)


## MiKTeX

- [Initial support for native Apple Silicon target](https://github.com/MiKTeX/miktex/pull/710)

## Nixpkgs

- [hdf5_1_10: 1.10.9 -> 1.10.11](https://github.com/NixOS/nixpkgs/pull/268889)
- [glibc: use libutil.a when libutil.so.1 is unavailable](https://github.com/NixOS/nixpkgs/pull/254334)
- [boost183: init at 1.83.0](https://github.com/NixOS/nixpkgs/pull/253144)
- [dhcpcd: 9.4.1 -> 10.0.3](https://github.com/NixOS/nixpkgs/pull/253129)
- [ifrextractor-rs: init at 1.5.1](https://github.com/NixOS/nixpkgs/pull/248689)
- [mucommander: 1.2.0-1 -> 1.3.0-1](https://github.com/NixOS/nixpkgs/pull/246596)
- [copilot-cli: 1.28.0 -> 1.29.0](https://github.com/NixOS/nixpkgs/pull/246594)
- [cbmc: 5.87.0 -> 5.88.1](https://github.com/NixOS/nixpkgs/pull/246593)
- [cbmc: 5.76.1 -> 5.86.0](https://github.com/NixOS/nixpkgs/pull/241120)
- [spark2014: do not hardcode gnat12 version](https://github.com/NixOS/nixpkgs/pull/238663)
- [flashrom: unbreak darwin](https://github.com/NixOS/nixpkgs/pull/230794)
- [circt: 1.34.0 -> 1.37.0](https://github.com/NixOS/nixpkgs/pull/224621)
- [mucommander: 1.1.0-1 -> 1.2.0-1](https://github.com/NixOS/nixpkgs/pull/224304)
- [copilot-cli: 1.26.0 -> 1.27.0](https://github.com/NixOS/nixpkgs/pull/224303)
- [rain: 1.2.0 -> 1.3.3](https://github.com/NixOS/nixpkgs/pull/217061)
- [spice-gtk: unbreak on darwin](https://github.com/NixOS/nixpkgs/pull/207657)
- [pcsclite: fix libsystemd switch](https://github.com/NixOS/nixpkgs/pull/199946)
- [python3Packages.brian2: init at 2.5.1](https://github.com/NixOS/nixpkgs/pull/198885)
- [nest: init at 3.3](https://github.com/NixOS/nixpkgs/pull/198872)
- [bpftools: fix build on ppc64le](https://github.com/NixOS/nixpkgs/pull/198587)
- [ngspice: add darwin to platforms](https://github.com/NixOS/nixpkgs/pull/198374)
- [spark2014: init at unstable-2022-05-25](https://github.com/NixOS/nixpkgs/pull/197926)
- [Add support for gnuradio on darwin](https://github.com/NixOS/nixpkgs/pull/197639)
- [darwin.iproute2mac: 1.4.0 -> 1.4.1](https://github.com/NixOS/nixpkgs/pull/191867)
- [jsonmerge: skip failed tests](https://github.com/NixOS/nixpkgs/pull/191624)
- [krunvm: add support for darwin](https://github.com/NixOS/nixpkgs/pull/187003)
- [recoll: fix no/bad configuration error on darwin](https://github.com/NixOS/nixpkgs/pull/186368)
- [sioyek: unbreak on darwin](https://github.com/NixOS/nixpkgs/pull/185502)
- [circleci-cli: 0.1.17142 -> 0.1.20397](https://github.com/NixOS/nixpkgs/pull/185111)
- [foremost: unbreak on Darwin](https://github.com/NixOS/nixpkgs/pull/184825)
- [prometheus-influxdb-exporter: 0.8.0 -> 0.10.0](https://github.com/NixOS/nixpkgs/pull/182563)
- [rain: init at 1.2.0](https://github.com/NixOS/nixpkgs/pull/182351)
- [hal-hardware-analyzer: fix build with python 3.10](https://github.com/NixOS/nixpkgs/pull/182062)
- [arpack: unbreak on aarch64-darwin](https://github.com/NixOS/nixpkgs/pull/182057)
- [cvc3: unbreak on darwin](https://github.com/NixOS/nixpkgs/pull/182056)
- [python310Packages.chalice: 1.26.6 -> 1.27.1](https://github.com/NixOS/nixpkgs/pull/181914)
- [aws-sam-cli: 1.52.0 -> 1.53.0](https://github.com/NixOS/nixpkgs/pull/181912)
- [python310Packages.aws-sam-translator: 1.46.0 -> 1.47.0](https://github.com/NixOS/nixpkgs/pull/181911)
- [rustup: 1.24.3 -> 1.25.1](https://github.com/NixOS/nixpkgs/pull/181686)
- [cbmc: init at 5.63.0](https://github.com/NixOS/nixpkgs/pull/181597)
- [lsof: fix -fno-common builds on darwin](https://github.com/NixOS/nixpkgs/pull/181553)
- [libbsd: fix build on darwin](https://github.com/NixOS/nixpkgs/pull/181353)
- [libressl: fix build on aarch64-darwin](https://github.com/NixOS/nixpkgs/pull/181239)
- [glances: fix tests on darwin](https://github.com/NixOS/nixpkgs/pull/181073)
- [mono: 6.12.0.122 -> 6.12.0.182](https://github.com/NixOS/nixpkgs/pull/181051)
- [aws-workspaces: 4.0.1.1302 -> 4.1.0.1523](https://github.com/NixOS/nixpkgs/pull/180854)
- [copilot-cli: init at 1.19.0](https://github.com/NixOS/nixpkgs/pull/180844)
- [wkhtmltopdf: unbreak on darwin](https://github.com/NixOS/nixpkgs/pull/180669)
- [Fix hdfview issue 179793 and bump hdfview to 3.1.4](https://github.com/NixOS/nixpkgs/pull/180613)
- [Add darwin support for hdfview](https://github.com/NixOS/nixpkgs/pull/180225)
- [hdf5_1_10: 1.10.6 -> 1.10.9](https://github.com/NixOS/nixpkgs/pull/180085)
- [hdf5: 1.12.1 -> 1.12.2](https://github.com/NixOS/nixpkgs/pull/180083)
- [musescore: 2.1 -> 3.6.2.548020600 on darwin](https://github.com/NixOS/nixpkgs/pull/179977)
- [darwin.network_cmds: fix build on aarch64-darwin](https://github.com/NixOS/nixpkgs/pull/179971)
- [darwin.xnu: fix build on aarch64-darwin](https://github.com/NixOS/nixpkgs/pull/179921)
- [openconnect: 8.20 -> 9.01](https://github.com/NixOS/nixpkgs/pull/179859)
- [python310Packages.cocotb: unbreak on Darwin](https://github.com/NixOS/nixpkgs/pull/178918)
- [darwin.iproute2mac: 1.2.1 -> 1.4.0](https://github.com/NixOS/nixpkgs/pull/178822)
- [htmldoc: fix darwin build](https://github.com/NixOS/nixpkgs/pull/178725)
- [radare2: unbreak on Darwin](https://github.com/NixOS/nixpkgs/pull/178662)
- [radare2: 5.6.8 -> 5.7.2](https://github.com/NixOS/nixpkgs/pull/178659)
- [gtkwave: support darwin build](https://github.com/NixOS/nixpkgs/pull/178552)
- [cairo: add patch to fix crashes on darwin](https://github.com/NixOS/nixpkgs/pull/178551)

## openFPGALoader

- [Add flash support for VCU128](https://github.com/trabucayre/openFPGALoader/pull/316)
- [Add initial support for VCU128](https://github.com/trabucayre/openFPGALoader/pull/313)

## PyNN

- [Fix quantities error and x-y order in plotting](https://github.com/NeuralEnsemble/PyNN/pull/763)
- [Fix weight type in brain2 backend for issue 711](https://github.com/NeuralEnsemble/PyNN/pull/723)
- [add missing __new__ for neuron 8.0.0, fixing issue #722](https://github.com/NeuralEnsemble/PyNN/pull/727)

## qemu

- [Lower TCG vector ops to LSX](https://patchew.org/QEMU/20230908022302.180442-1-c@jia.je/)
- [target/loongarch: fix ASXE flag conflict](https://patchew.org/QEMU/20230930112837.1871691-1-c@jia.je/)
- [linux-user/elfload: Enable LSX/LASX in HWCAP for LoongArch](https://patchew.org/QEMU/20231001085315.1692667-1-c@jia.je/)
- [hw/loongarch: Fix ACPI processor id off-by-one error](https://patchew.org/QEMU/20230820105658.99123-2-c@jia.je/)
- [Add la32 & va32 support for loongarch64-softmmu](https://patchew.org/QEMU/20230809083258.1787464-1-c@jia.je/)
- [target/loongarch: Split fcc register to fcc0-7 in gdbstub](https://patchew.org/QEMU/20230808054315.3391465-1-c@jia.je/)
- [target/loongarch: Fix CSR.DMW0-3.VSEG check](https://github.com/qemu/qemu/commit/505aa8d8f29b79fcef77563bb4124208badbd8d4)

## rocket-chip

- [Doc fixes and add comments to axi4 bundles](https://github.com/chipsalliance/rocket-chip/pull/2925)

## SpinalCrypto

- [Add cross scala version support, upgrade scalatest and fix scala 2.13 incompat code](https://github.com/SpinalHDL/SpinalCrypto/pull/13)

## SpinalHDL

- [Use scalafmt to format code](https://github.com/SpinalHDL/SpinalHDL/pull/539)
- [Add support for write byte enable in BusSlaveFactory.writeMemWordAligned](https://github.com/SpinalHDL/SpinalHDL/pull/533)
- [Fix typos and improve error messages](https://github.com/SpinalHDL/SpinalHDL/pull/524)
- [Add option to enable logging of ghdl/iverlog backend](https://github.com/SpinalHDL/SpinalHDL/pull/506)
- [Cross scala versions build](https://github.com/SpinalHDL/SpinalHDL/pull/456)
- [Add support for Virtex UltraScale+ in xilinx eda bench](https://github.com/SpinalHDL/SpinalHDL/pull/406)
- [Add axi4 slave factory](https://github.com/SpinalHDL/SpinalHDL/pull/404)
- [Add writeByteEnable to BusSlaveFactory and support unaligned access in read/writeMultiWord for AXI4](https://github.com/SpinalHDL/SpinalHDL/pull/402)
- [Pass simulator flags to iverilog and ghdl](https://github.com/SpinalHDL/SpinalHDL/pull/383)
- [Add support for multiple rtl file benchmark](https://github.com/SpinalHDL/SpinalHDL/pull/378)
- [Add support for multi word memory access in BusSlaveFactory](https://github.com/SpinalHDL/SpinalHDL/pull/367)
- [Fix iverilog simulation under macOS](https://github.com/SpinalHDL/SpinalHDL/pull/365)

## U-Boot

- [spi: xilinx_spi: Fix spi reset](https://github.com/u-boot/u-boot/commit/4fffbc1108f3f5e2932cdefea8b5f831b46040c7)

## 尚未合并
