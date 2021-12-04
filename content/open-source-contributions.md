---
layout: page
date: 1970-01-01
title: 开源软件贡献
permalink: /open-source-contributions/
---

记录我对开源软件的一些微小的贡献，以勉励自己，督促自己不忘为社区做贡献。

## aws-cdk

- [feat(cloudfront): support Behavior-specific viewer protocol policy for CloudFrontWebDistribution](https://github.com/aws/aws-cdk/pull/16389)

## bandersnatch

- [Skip downloading based on file size and upload time instead of sha256sum](https://github.com/pypa/bandersnatch/pull/822)

## cargo

- [Don't create hardlink for library test and integrations tests, fixing #7960](https://github.com/rust-lang/cargo/pull/7965)

## chisel-testers2

- [Fix VCS simulation binary path](https://github.com/ucb-bar/chisel-testers2/pull/430)
- [Fix issue #428: add blackbox sources to argument of icarus-verilog and vcs](https://github.com/ucb-bar/chisel-testers2/pull/429)
- [Fix VcsFlags not properly passed to vcs backend](https://github.com/ucb-bar/chisel-testers2/pull/426)

## FloPoCo

- [two more bug fixes](https://gitlab.inria.fr/fdupont/flopoco/-/commit/4672586b731b22562d2ce6994c5c78e41846a452)
- [Remove the duplicate code lines: R <= (bug reported by Jiajie Chen)](https://gitlab.inria.fr/fdupont/flopoco/-/commit/5ac83babf7d6a69cd3124a6127a98a0ac58c4508)
- [Other commits by me](https://gitlab.inria.fr/fdupont/flopoco/-/commits/master?author=Jiajie%20Chen)

## KNEM

- [driver/linux: use the pin API added in Linux 5.6](https://gitlab.inria.fr/knem/knem/-/commit/fa80cec4970514a6388fe165cc0c4167fd813228)

## MiKTeX

- [Initial support for native Apple Silicon target](https://github.com/MiKTeX/miktex/pull/710)

## PyNN

- [add missing __new__ for neuron 8.0.0, fixing issue #72](https://github.com/NeuralEnsemble/PyNN/pull/727)

## SpinalHDL

- [Add axi4 slave factory](https://github.com/SpinalHDL/SpinalHDL/pull/404)
- [Add writeByteEnable to BusSlaveFactory and support unaligned access in read/writeMultiWord for AXI4](https://github.com/SpinalHDL/SpinalHDL/pull/402)
- [Pass simulator flags to iverilog and ghdl](https://github.com/SpinalHDL/SpinalHDL/pull/383)
- [Add support for multiple rtl file benchmark](https://github.com/SpinalHDL/SpinalHDL/pull/378)
- [Add support for multi word memory access in BusSlaveFactory](https://github.com/SpinalHDL/SpinalHDL/pull/367)
- [Fix iverilog simulation under macOS](https://github.com/SpinalHDL/SpinalHDL/pull/365)