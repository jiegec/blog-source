---
layout: page
date: 1970-01-01
title: 开源软件贡献
permalink: /open-source-contributions/
---

记录我对开源软件的一些微小的贡献，以勉励自己，督促自己不忘为社区做贡献。

## Maintenance

我主要参与如下开源项目的维护：

- [lsof-org/lsof](https://github.com/lsof-org/lsof)
- [NixOS/nixpkgs](https://github.com/nixos/nixpkgs)
- [canokeys](https://github.com/canokeys)
- [nfcim](https://github.com/nfcim)

## aws-cdk

- [feat(cloudfront): support Behavior-specific viewer protocol policy for CloudFrontWebDistribution](https://github.com/aws/aws-cdk/pull/16389)

## bandersnatch

- [Skip downloading based on file size and upload time instead of sha256sum](https://github.com/pypa/bandersnatch/pull/822)

## cargo

- [Don't create hardlink for library test and integrations tests, fixing #7960](https://github.com/rust-lang/cargo/pull/7965)

## chiseltest

- [Fix VCS simulation binary path](https://github.com/ucb-bar/chiseltest/pull/430)
- [Fix issue #428: add blackbox sources to argument of icarus-verilog and vcs](https://github.com/ucb-bar/chiseltest/pull/429)
- [Fix VcsFlags not properly passed to vcs backend](https://github.com/ucb-bar/chiseltest/pull/426)

## FloPoCo

- [two more bug fixes by Jiajie Chen](https://gitlab.com/flopoco/flopoco/-/commit/4672586b731b22562d2ce6994c5c78e41846a452)
- [Remove the duplicate code lines: R <= (bug reported by Jiajie Chen)](https://gitlab.com/flopoco/flopoco/-/commit/5ac83babf7d6a69cd3124a6127a98a0ac58c4508)
- [Commits by me](https://gitlab.com/flopoco/flopoco/-/commits/master?author=Jiajie%20Chen)

## force-riscv

- [Fixed compilation error: std::string and int64_t undefined](https://github.com/openhwgroup/force-riscv/pull/54)

## FreeBSD

- [Add kf_file_nlink field to kf_file and populate it](https://reviews.freebsd.org/D38169)

## gpaw

- [Fix issue #269 to add additional broadcast in some cases](https://gitlab.com/gpaw/gpaw/-/merge_requests/863)
- [Capture and ignore AttributeError thrown in getpreferredencoding() in newer Python versions](https://gitlab.com/gpaw/gpaw/-/merge_requests/858)

## gtkwave

- [Fix compilation under macOS for Nix](https://github.com/gtkwave/gtkwave/pull/136)

## iwd

- [[PATCH 1/2] knownnetworks: fix potential out of bounds write](https://lore.kernel.org/iwd/20230226062526.3115588-1-c@jia.je/T/#u)
	- [knownnetworks: fix printing SSID in hex](https://git.kernel.org/pub/scm/network/wireless/iwd.git/commit/?id=98b758f8934a95f961e3b5779bcc9b25b30ae97a)
	- [knownnetworks: fix potential out of bounds write](https://git.kernel.org/pub/scm/network/wireless/iwd.git/commit/?id=89309a862108c4caac41995b5fc76ade859d87a8)

## KiCad

- [libcontext: Initial support for Apple Silicon](https://gitlab.com/kicad/code/kicad/-/merge_requests/602)

## KNEM

- [driver/linux: use the pin API added in Linux 5.6](https://gitlab.inria.fr/knem/knem/-/commit/fa80cec4970514a6388fe165cc0c4167fd813228)

## MiKTeX

- [Initial support for native Apple Silicon target](https://github.com/MiKTeX/miktex/pull/710)

## Nixpkgs

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

# 尚未合并

- <https://lists.denx.de/pipermail/u-boot/2023-February/509789.html>