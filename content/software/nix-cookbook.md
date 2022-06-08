---
layout: post
date: 2022-06-07 22:29:00 +0800
tags: [nix,nixos,cookbook]
category: software
title: Nix Cookbook
---

## 背景

最近在尝试 NixOS 和在 macOS 上跑 Nix，下面记录一些我在使用过程中遇到的一些小问题和解决思路。

## NixOS

### 全局配置

NixOS 的全局配置路径：`/etc/nixos/configuration.nix` 和 `/etc/nixos/hardware-configuration.nix`

应用更新后的全局配置：

```shell
nixos-rebuild switch
# or
nixos-rebuild switch --upgrade
```

### 更新大版本

如果要更新 NixOS 21.11 到 22.05:

```shell
nix-channel --list
nix-channel --add https://nixos.org/channels/nixos-22.05 nixos
nixos-rebuild switch --upgrade
```

可以考虑改或者不改 `/etc/nixos/configuration.nix` 中的 `system.stateVersion`。

### 常用配置

常用的 NixOS 配置：

```nix
# Enable XFCE
services.xserver.enable = true;
services.xserver.desktopManager.xfce.enable = true;

# System wide packages
environment.systemPackages = with pkgs; [
  xxx
];

# Fish shell
programs.fish.enable = true;
users.users.xxx = {
  shell = pkgs.fish;
}

# Command not found
programs.command-not-found.enable = true;

# Steam gaming
nixpkgs.config.allowUnfree = true;
programs.steam.enable = true;

# NOPASSWD for sudo
security.sudo.wheelNeedsPassword = false;

# QEMU guest
services.qemuGuest.enable = true;
services.spice-vdagentd.enable = true;

# XRDP
services.xrdp.enable = true;
services.xrdp.defaultWindowManager = "xfce4-session";
services.xrdp.openFirewall = true;

# OpenSSH server
services.openssh.enable = true;

# Udev rules for Altera USB Blaster
services.udev.packages = with pkgs; [
  usb-blaster-udev-rules
];
```

### VSCode Remote

VSCode Remote 会在远程的机器上运行一个预编译的 nodejs，运行的时候会因为路径问题无法执行。

解决方法在 [NixOS Wiki](https://nixos.wiki/wiki/Visual_Studio_Code#Remote_SSH) 上有，具体来说，首先，需要安装 `nodejs`：

```nix
environment.systemPackages = with pkgs; [
  nodejs-16_x # vscode remote
];
```

然后，用软链接来覆盖 nodejs：

```shell
cd ~/.vscode-server/bin/HASH
ln -sf /run/current-system/sw/bin/node
```

这样就可以正常使用 VSCode Remote 了。

## Home Manager

[Home Manager](https://github.com/nix-community/home-manager) 描述用户默认看到的程序，而 NixOS 的配置是所有用户的。

### 配置文件

配置文件：`~/.config/nixpkgs/home.nix`

应用配置文件：

```shell
home-manager switch
```

### 常用配置

常用的 Home Manager 配置：

```nix
# Allow unfree
nixpkgs.config.allowUnfree = true;

# User wide packages
home.packages = with pkgs; [
  xxx
];
```

### 覆盖依赖版本

设置 JVM 程序依赖的 JDK 版本：

```nix
# Maven with java 11
home.packages = with pkgs; [
  (maven.override { jdk = jdk11; })
];

# Many packages with the same JDK
home.packages = 
  let java = pkgs.jdk11; in
  with pkgs; [
    (maven.override { jdk = java; })
    (sbt.override { jre = java; })
  ];
```

具体的参数命名要看 nixpkgs 上对应的包的开头。

## 实用工具

### nixpkgs-fmt

[nixpkgs-fmt](https://github.com/nix-community/nixpkgs-fmt) 用来格式化 Nix 代码。

### search.nixos.org

[search.nixos.org](search.nixos.org) 可以搜索 nixpkgs 上的各种包，也可以看到不同平台支持情况。缺点是看不出是否 unfree 和 broken，并且一些 darwin os-specific 的包不会显示。

### nix-tree

显示各个 nix derivation 的硬盘占用和依赖关系。

## 打包

可以很容易地编写 `default.nix` 来给自己的项目打包。

### CMake

对于一个简单的 cmake 程序，可以按照如下的格式编写 `default.nix`：

```nix
with import <nixpkgs> {};

stdenv.mkDerivation {
  name = "xyz";
  version = "1.0";

  src = ./.;

  nativeBuildInputs = [
    cmake
  ];

  buildInputs = [
    xxx
    yyy
  ];
}
```

可以用 `nix-build` 命令来构建，生成结果会在当前目录下创建一个 `result` 的软链接，里面就是安装目录。

由于 `nix-build` 的时候也会创建 `build` 目录，为了防止冲突，建议开发的时候用其他的名字。

### Qt

对于 Qt 项目来说，由于有不同的 Qt 大版本，所以实现的时候稍微复杂一些，要拆成两个文件，首先是 `default.nix`：

```nix
with import <nixpkgs> {};

libsForQt5.callPackage ./xxx.nix { }
```

这里就表示用 `qt5` 来编译，那么编写 `xxx.nix` 的时候，传入的 `qtbase` 等库就是 `qt5` 的版本：

```nix
{ stdenv, qtbase, wrapQtAppsHook, cmake }:

stdenv.mkDerivation {
  name = "xxx";
  version = "1.0";

  src = ./.;

  nativeBuildInputs = [
    cmake
    wrapQtAppsHook # must-have for qt apps
  ];

  buildInputs = [
    qtbase
  ];
}
```

实际测试中发现，运行的程序可能会报告 `Could not initialize GLX` 的错误，这个方法可以通过 `wrapProgram` 添加环境变量解决：

```
  # https://github.com/NixOS/nixpkgs/issues/66755#issuecomment-657305962
  # Fix "Could not initialize GLX" error
  postInstall = ''
    wrapProgram "$out/bin/xxx" --set QT_XCB_GL_INTEGRATION none
  '';
```

## 开发环境

除了打包以外，通常还会在 `shell.nix` 中定义开发环境需要的包：

```nix
{ pkgs ? import <nixpkgs> {}
}:

pkgs.mkShell {
  buildInputs = with pkgs; [
    cmake
  ];
}
```

然后可以用 `nix-shell` 来进入开发环境。如果不希望外面的环境变量传递进去，可以用 `nix-shell --pure`。