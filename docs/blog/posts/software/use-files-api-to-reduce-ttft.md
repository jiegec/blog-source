---
layout: post
date: 2026-10-12
tags: [deepseek,axonhub,api,llm]
categories:
    - software
---

# 用 Files API 减少图片体积导致的 TTFT 膨胀

## 背景

最近我经常用 DeepSeek-V4.1-Flash 模型读图。由于每次请求都要传完整上下文，随着上下文里的图片越来越多，上传图片所花的时间很快就成了 TTFT 的主要瓶颈；如果走的是 OpenCode Go，甚至动辄要几分钟。为了解决这个问题，可以用 Files API 提前把图片上传到 DeepSeek，然后在上下文里直接用 id 引用文件。为此，我随手 Vibe 了一个 [pi-files-api](https://github.com/jiegec/pi-files-api) 插件，给 Pi Agent 加上这个能力。

<!-- more -->

## 具体现象

我最近发现一个现象：在一些会话里，TTFT 稳定地偏高，而且越来越高，10s、12s 一路上涨，有时甚至到几分钟的量级，而这些会话都包含大量的图片读取。一开始我以为是服务端的问题，后来通过交流和分析才发现，图片在每次请求时都会被重新发送给后端；随着读图不断累积，TTFT 里的大部分时间都耗在了上传图片上。

一开始，我还寄希望于有状态的 OpenAI Responses API：每次只发送相对上一次请求的增量，从而避免图片的重复上传。然而 DeepSeek 目前还没有实现这个功能，所以只能用 Files API。

## Files API

可以把 Files API 理解为一个临时的网盘，它支持上传、列举、删除和查询，有 OpenAI 和 Anthropic 两个版本，不过功能大同小异。在这个临时网盘里，每个文件都有唯一的 id，可以出现在 chat completions/responses/anthropic messages 请求体中，用来代替实际的图片。

因此，如果 Agent 懂得使用 Files API，先上传图片，再用 file id 填充请求体，就可以解决上述 TTFT 暴增的问题。DeepSeek Harness 是支持的，但前提是使用第一方 API；像我这样通过 AxonHub 统一管理 API key 的情况，它就不会用这个 Files API 了。

另外，我日常使用的 Pi Agent 也没有做这个优化。不过，在 AI 时代，做这样一个优化，也就是写几句 Prompt、写个插件的事情。

## pi-files-api

最终，我快速 Vibe 出了一个插件 [pi-files-api](https://github.com/jiegec/pi-files-api)：它从 models.json 读取配置，替换上下文里的图片 base64，上传到指定的 Files API Endpoint，然后用 file id 替代图片内容；插件内部还维护了一份 sha256 到 file id 的映射。

当然，目前 AxonHub 还不支持代理 Files API，所以我只能被迫在本地给 Pi 配置 DeepSeek 的 API key：先通过 api.deepseek.com 上传图片，再通过 AxonHub 发送实际的请求体，非常不优雅。希望 AxonHub 后续能增加对 Files API 的支持，不过这也会带来一个问题：切换 API 上游时，Files 不会跟着迁移，换了一个供应商以后，原来的 file id 就失效了。这个问题我还没想好怎么办，只能先曲线救国一下。
