---
layout: post
date: 2023-01-13
tags: [vscode,code-server,freebsd]
categories:
    - software
---

# 在 FreeBSD 上运行 code-server

## 背景

最近在 FreeBSD 上移植开源软件，但是因为 vscode 官方不支持 FreeBSD，所以尝试使用 code-server

## 使用

首先按照官方文档安装 code-server：

```shell
curl -fsSL https://code-server.dev/install.sh | sh
```

启动 code-server：

```shell
code-server --bind-addr 0.0.0.0:8080
```

但是很快你会发现，运行日志中会报告很多错误，缺少了一些包：

```shell
sudo npm i -g yazl yauzl @microsoft/1ds-core-js vscode-regexpp xterm-headless vscode-proxy-agent --unsafe-perm
```

到这里就能在网页里看到 UI 了，但是发现很多功能都不工作。例如搜索的时候，会告诉你找不到 rg，是因为 ripgrep 没有提供 FreeBSD 的 prebuilt binary，但是可以用 pkg 安装：

```
sudo pkg install ripgrep
cd /usr/local/lib/node_modules/@vscode/ripgrep/bin && ln -s /usr/local/bin/rg
cd /usr/local/lib/node_modules/code-server/lib/vscode/node_modules/@vscode/ripgrep/bin && ln -s /usr/local/bin/rg
```

然后，日志中会显示 @parcel/watcher 启动失败，显示 Undefined symbol，这是因为这个库没有做 FreeBSD 支持。需要使用 https://github.com/parcel-bundler/watcher/pull/128 版本，编译出 watcher.node 文件，替换：

```
cd watcher
npm install
sudo cp build/Release/watcher.node /usr/local/lib/node_modules/@parcel/watcher/build/Release/
sudo cp build/Release/watcher.node /usr/local/lib/node_modules/code-server/lib/vscode/node_modules/@parcel/watcher/build/Release/watcher.node
```

这样就解决了 watcher 的问题。

最后一个问题是无法打开 Terminal，因为在 VSCode 代码中，检测到不支持的 Platform 的时候，会抛出异常：

```
[IPC Library: Pty Host] The factory function of "vs/platform/terminal/node/ptyHostMain" has thrown an exception
[IPC Library: Pty Host] Error: Platform not supported
```

可以修改源码：`sudo vim /usr/local/lib/node_modules/code-server/lib/vscode/out/vs/platform/terminal/node/ptyHostMain.js` 把这个检查改掉，例如替换 linux 为 freebsd，当成 linux 来检测。

接下来的问题和 https://github.com/coder/code-server/issues/5760 一致，安装依赖，重新 `npm install`：

```
sudo pkg install libsecret pkgconf
cd /usr/local/lib/node_modules/code-server
sudo npm install --unsafe-perm
# go back to @parcel/watcher
cd watcher
sudo cp build/Release/watcher.node /usr/local/lib/node_modules/code-server/lib/vscode/node_modules/@parcel/watcher/build/Release
```

完成这些步骤以后，Terminal 也正常了。
