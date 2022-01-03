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

## chiseltest

- [Fix VCS simulation binary path](https://github.com/ucb-bar/chiseltest/pull/430)
- [Fix issue #428: add blackbox sources to argument of icarus-verilog and vcs](https://github.com/ucb-bar/chiseltest/pull/429)
- [Fix VcsFlags not properly passed to vcs backend](https://github.com/ucb-bar/chiseltest/pull/426)

## FloPoCo

- [two more bug fixes by Jiajie Chen](https://gitlab.com/flopoco/flopoco/-/commit/4672586b731b22562d2ce6994c5c78e41846a452)
- [Remove the duplicate code lines: R <= (bug reported by Jiajie Chen)](https://gitlab.com/flopoco/flopoco/-/commit/5ac83babf7d6a69cd3124a6127a98a0ac58c4508)
- [Commits by me](https://gitlab.com/flopoco/flopoco/-/commits/master?author=Jiajie%20Chen)

## KNEM

- [driver/linux: use the pin API added in Linux 5.6](https://gitlab.inria.fr/knem/knem/-/commit/fa80cec4970514a6388fe165cc0c4167fd813228)

## MiKTeX

- [Initial support for native Apple Silicon target](https://github.com/MiKTeX/miktex/pull/710)

## PyNN

- [Fix weight type in brain2 backend for issue 711](https://github.com/NeuralEnsemble/PyNN/pull/723)
- [add missing __new__ for neuron 8.0.0, fixing issue #722](https://github.com/NeuralEnsemble/PyNN/pull/727)

## SpinalCrypto

- [Add cross scala version support, upgrade scalatest and fix scala 2.13 incompat code](https://github.com/SpinalHDL/SpinalCrypto/pull/13)

## SpinalHDL

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