---
layout: page
date: 1970-01-01
title: JieLabs 是如何工作的
permalink: /jielabs
---

# 简介

JieLabs 是陈嘉杰、高一川、刘晓义（按姓氏拼音首字母排序）于 2020 年新型冠状病毒疫情期间开发的在线数字逻辑电路实验系统，用于清华大学 2020 年春季学期数字逻辑电路实验课程。其包括前端、后端和固件三部分，分别主要由刘晓义、陈嘉杰和高一川负责开发。核心功能实现用时一周，后续界面和稳定性优化用时两周。本文会详细地介绍 JieLabs 的工作原理和一些技术细节，希望对各位同学有所帮助。

## 太长；不看。

采用了如下的技术方案：

前端：React 框架 + Redux 状态管理 + Monaco 编辑器 + WebAssembly 实时通信

后端：Actix-Web 框架 + Diesel/PostgreSQL 数据库 + Redis 消息队列 + Quartus 构建 + Kubernetes 构建容器编排

固件：Xilinx FPGA 控制 + Buildroot 系统 + Linux 内核

