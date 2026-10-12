---
layout: post
date: 2026-10-12
tags: [deepseek,axonhub,api,llm]
categories:
    - software
---

# 用 Files API 减少因图片体积导致的 TTFT 膨胀

## 背景

最近经常用 DeepSeek-V4.1-Flash 模型读图，随着上下文里图片越来越多，因为每次都要传完整的上下文，照片上传的时间很快就成为了 TTFT 的主要瓶颈，如果是走了 OpenCode Go，则轻松上几分钟。为了解决这个问题，可以用 Files API 来提前上传图片到 DeepSeek，然后在上下文里直接用 id 来指定文件，为此 Vibe 了一个 [pi-files-api](https://github.com/jiegec/pi-files-api) 插件来给 Pi Agent 添加这个能力。

<!-- more -->

## 具体现象

最近发现一个现象，就是在一些会话里，TTFT 稳定的高，而且越来越高：10s，12s，一路往上涨，有时候甚至能到几分钟的量级，这些会话都有大量的照片读取。一开始还以为是服务端的问题，后来通过交流和分析，发现图片会在每次请求的时候都重新发给后端，而随着读图的累积，TTFT 大部分时间都耗在了上传图片上。

一开始，我还寄希望于 Stateful 的 OpenAI Responses API，即每次只发送和上次请求的增量，避免图片的重复上传。然而 DeepSeek 目前还没有实现这个功能，所以只能用 Files API。

## Files API

Files API 可以理解为一个临时的网盘：可以上传、列举、删除和查询，有 OpenAI 和 Anthropic 两种版本，不过功能大差不差。这个临时的网盘里，每个文件都有一个唯一的 id，可以出现在 chat completions/responses/anthropic messages 的请求体里，代替实际的图片。

所以，如果 Agent 知道用这个 Files API，用它先上传图片，再用 file id 来填补请求体，就可以解决上述的 TTFT 暴增问题。DeepSeek Harness 是支持的，但是得是第一方的 API；像我这样通过一个 AxonHub 统一管理我的 API key 的情况下，它就不知道要用这个 Files API 了。

然后我日常的 Pi Agent 也没有做这个优化。但是，在 AI 时代，做个优化，就是几句 Prompt 写个插件的事情。

## pi-files-api

最后，我就快速 Vibe 了一个插件 [pi-files-api](https://github.com/jiegec/pi-files-api) 出来，通过修改 models.json 配置，它就知道要替换上下文里的图片 base64，上传到指定的 Files API Endpoint，然后用 file id 替代图片内容，插件内部维护了一个 sha256sum 到 file id 的映射。

当然，目前 AxonHub 还不支持 Files API 的代理，所以目前还是被迫在本地给 Pi 配了 DeepSeek 的 api key，然后先通过 api.deepseek.com 上传图片，再通过 axonhub 发实际的请求体，非常不优雅。后续希望 AxonHub 能增加 Files API 支持，不过这也会带来一个问题：切换 API 上游的情况下，Files 不会跟着跑，换了一个供应商以后，原来的 file id 就失效了。这个还没想好怎么办，就只能先曲线救国一下。
