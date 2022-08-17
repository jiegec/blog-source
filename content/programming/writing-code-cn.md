---
layout: post
date: 2022-07-12 10:49:00 +0800
tags: [mit,plagiarism]
category: programming
title: 编程作业中的学术诚信
---

本文是我自己对 [Academic Integrity at MIT: Writing Code](https://integrity.mit.edu/handbook/writing-code) 的非官方中文翻译。本文已经得到了官方的邮件授权。

## 编写代码 Writing Code

与学术写作类似，当你在做课程项目的时候，如果使用了或者改编了其他人开发的代码，你必须要引用代码的来源。你可以在代码注释中引用代码来源。这些注释不仅保护了他人的劳动成果，也会帮助你理解代码和调试。

	Writing code is similar to academic writing in that when you use or
	adapt code developed by someone else as part of your project, you must
	cite your source. However, instead of quoting or paraphrasing a source,
	you include an inline comment in the code. These comments not only
	ensure you are giving proper credit, but help with code understanding
	and debugging.

## 什么时候应该在代码中引用来源？ When should I cite a source in my code?


1. 当你从外部来源复制了代码。无论你是复制了代码片段，还是一整个模块，你都需要引用来源。

		When you copy code from an external source. Whether you are copying a
		snippet of code or an entire module, you should credit the source.

2. 当你复制了代码并做了改动，你依然要引用来源。你并不是代码的原作者。

		When you copy the code and adapt it, you should still credit the source.
		You were not the original developer of the code.


## 我应该如何引用代码？ How should I cite the code?

1. 通常来说，代码的网址和下载时间就足够了。如果可以让读者更加清晰地了解到代码来源，可以增加更多的细节。

		Generally, the URL and the date of retrieval are sufficient. Add
		more details if it will help the reader get a clearer
		understanding of the source.

2. 如果你修改了代码，你需要注明：“Adapted from:”（修改自） 或者“Based on”（基于）。这样读者就知道你修改了代码。

		If you adapted the code, you should indicate “Adapted from:” or
		“Based on” so it is understood that you modified the code.

3. 你的老师可能会对你如何引用代码有具体的要求。如果你不能确认什么是可行的，请询问你的老师。

		Your instructor may have specific instructions on how you should
		or should not cite your sources. If you are not clear on what is
		acceptable, ask your instructor.

## 开源软件的使用 Use of Open Source Software

当你使用开源软件项目的代码的时候，你不仅要注明代码的来源，还需要遵循代码的开源软件许可证。请记住：

	When you use code from an open source project, you need both to
	attribute the source and follow the terms of any open source license
	that applies to the code you are using. Keep in mind:

1. 当你下载源码的时候，它的开源软件许可证通常也在源码中。

		When you download the source, the license is typically part of the
		download.

2. 同时，代码里也通常会包括它的版权和使用条款。

		Also, the source code itself will typically contain the
		copyright and terms of use.

3. 当你引入了开源代码，并且它附带了开源软件许可证，你应该把它的版权声明复制到你的代码中，和/或把许可证复制到代码目录中的文件。

		When you incorporate open-source-licensed code into a program,
		it is good practice to duplicate the copyright in your code,
		and/or store the license in a file with the code.

4. 如果在下载的文件里没有找到开源软件许可证，你可以在开源项目的网站上找到全文，如 [Apache HTTP Server 网站](https://httpd.apache.org/) 或者 [Open Source Initiative (OSI) 网站](https://opensource.org/)。

		If you don’t obtain the license with the download, you should be
		able to find it on the site of the open source project, such as
		Apache HTTP Server site, or on the Open Source Initiative (OSI)
		site.

## 老师决定具体的代码复用程度 Instructors determine the specific expectations around re-use of code in each class.

通常，老师会确定课程的协作规则。如果这个规则没有明确地给出来，或者你不确认什么是可行的，请询问你的老师。

	Often, the requirements are described in the collaboration policy for
	the class. If policy is not clearly described in the course materials
	and you are not sure what is acceptable, ask your instructor.

### 例子

下面给出一个例子，是课程（Spring 2012 6.005 Elements of Software Construction）的协作规则：

	Collaboration policy from Spring 2012 6.005 Elements of Software
	Construction: (used with the permission of Professor Rob Miller, Dept of
	Electrical Engineering & Computer Science)


我们鼓励同学们互相帮助，但是为了保证每个人都有良好的独立学习体验，我们对你们做了如下的限制：

	We encourage you to help each other with work in this class, but there
	are limits to what you can do, to ensure that everybody has a good
	individual learning experience.

#### 单人作业 Individual work

课程里的习题都要单人完成。我们鼓励同学们讨论实现方法，但是你的代码和报告都需要自己完成。

	Problem sets in this class are intended to be primarily individual
	efforts. You are encouraged to discuss approaches with other students
	but your code and your write-up must be your own.

你不能使用其他同学编写的资料，无论是这个学期还是以往学期的同学。你也不可以把你的成果提供给其他同学。

	You may not use materials produced as course work by other students,
	whether in this term or previous terms, nor may you provide work for
	other students to use.

帮助其他同学是应该的。但要保证一个原则，当你在帮助其他同学的时候，你自己的答案或代码不应该可以看到，无论是自己还是其他同学。可以养成一个习惯，帮助他人的时候把笔记本电脑合上。

	It’s good to help other students. But as a general rule, during the time
	that you are helping another student, your own solution should not be
	visible, either to you or to them. Make a habit of closing your laptop
	while you’re helping.

在帮助其他同学，阅读同学的代码的时候，你会看到同学的解答。你可以从同学的方法里获得灵感，但是不能复制他们的成果。

	During code review, you will see classmates’ solutions to a problem set.
	While it is fine to take inspiration from their approach, do not copy
	their work.

你可以用外部网站上的资料，比如 StackOverflow，但前提是加上引用，并且作业要求里允许这么做。特别地，如果作业要求里写了“实现 X 功能”，那么你必须自己实现 X 功能，而不能复用外部的代码。

	It’s fine to use material from external sources like StackOverflow, but
	only with proper attribution, and only if the assignment allows it. In
	particular, if the assignment says “implement X,” then you must create
	your own X, not reuse one from an external source.

你也可以用课程组提供的代码，不需要引用。老师提供的代码在未经允许的情况下，不能公开分享，我们后面会讨论这个问题。

	It’s also fine to use any code provided by this semester’s 6.031 staff
	(in class, readings, or problem sets), without need for attribution.
	Staff-provided code may not be publicly shared without permission,
	however, as discussed later in this document.


例子一 Example 1：

- A 和 B 做作业的时候坐在一起。他们简略地讨论实现的不同方法。他们在白板上画流程图。当 A 发现 Java 标准库中一个有用的类，她把这个发现告诉了 B。当 B 发现了 StackOverflow 上的一个回答，他给 A 发送了 URL。可以。

		Alyssa and Ben sit next to each other with their laptops while
		working on a problem set. They talk in general terms about
		different approaches to doing the problem set. They draw
		diagrams on the whiteboard. When Alyssa discovers a useful class
		in the Java library, she mentions it to Ben. When Ben finds a
		StackOverflow answer that helps, he sends the URL to Alyssa. OK.

- 在他们编写代码的时候，他们把代码大声念出来，好让双方都可以编写正确的代码。错误！

		As they type lines of code, they speak the code aloud to the
		other person, to make sure both people have the right code.
		INAPPROPRIATE.

- 在作业最困难的部分，A 和 B 互相看电脑屏幕，并对比代码，确认他们代码实现都是正确的。错误！

		In a tricky part of the problem set, Alyssa and Ben look at each
		other’s screens and compare them so that they can get their code
		right. INAPPROPRIATE.

例子二 Example 2：

- J 已经完成了作业，但是他的朋友 B 正在努力解决一个 bug。J 坐在 B 旁边，看他的代码，帮他调试出了问题。可以。

		Jerry already finished the problem set, but his friend Ben is
		now struggling with a nasty bug. Jerry sits next to Ben, looks
		at his code, and helps him debug. OK.

- J 打开了自己的笔记本，找到自己的答案，然后指着自己的代码给 B 纠正错误。错误！

		Jerry opens his own laptop, finds his solution to the problem
		set, and refers to it while he’s helping Ben correct his code.
		INAPPROPRIATE.

例子三 Example 3：

- L 这周有很多作业，但是因为时间和身体原因来不及做。他已经错过截止时间两天了，但基本没有什么进度。B 觉得 L 可怜，想要帮助 L。在 L 写作业的时候，B 告诉 L 他是怎么做作业的。B 已经提交了自己的答案，并且在帮助 L 的时候，不打开自己的笔记本电脑。可以。

		Louis had three problem sets and two quizzes this week, was away
		from campus for several days for a track meet, and then got
		sick. He’s already taken two slack days on the deadline and has
		made almost no progress on the problem set. Ben feels sorry for
		Louis and wants to help, so he sits down with Louis and talks
		with him about how to do the problem set while Louis is working
		on it. Ben already handed in his own solution, but he doesn’t
		open his own laptop to look at it while he’s helping Louis. OK.

- B 打开了自己的笔记本电脑，并且在帮助 L 的时候阅读自己的代码。错误！

		Ben opens his laptop and reads his own code while he’s helping
		Louis. INAPPROPRIATE.

- B 花了几个小时帮助 L，但是 L 还是没有完成。但是 B 需要去做自己的事情了。在 L 承诺只有在必要的时候才会看 B 的代码之后，B 把自己的代码上传到 Dropbox 并且分享给了 L。错误！

		Ben has by now spent a couple hours with Louis, and Louis still
		needs help, but Ben really needs to get back to his own work. He
		puts his code in a Dropbox and shares it with Louis, after Louis
		promises only to look at it when he really has to.
		INAPPROPRIATE.

例子四 Example 4：

- J 和 E 独立完成作业。他们交换了自己的测例来检查作业。错误！测例是题目的一部分，也是学习体验的一部分。如果你使用了其他人的测例，就是在抄袭，即使只是临时的。

		John and Ellen both worked on their problem sets separately.
		They exchange their test cases with each other to check their
		work. INAPPROPRIATE. Test cases are part of the material for the
		problem set, and part of the learning experience of the course.
		You are copying if you use somebody else’s test cases, even if
		temporarily.

注意，在上面的例子中，双方都负有学术不端的责任。抄袭作业，或者把自己的作业提供给他人，是一个很严重的事情，可能导致分数扣减，课程不及格甚至处分。抄袭作业，或者帮助他人抄袭，可能会给你的成绩单上添加一个不能消除的 F。

	Note that in the examples marked inappropriate above, both people are
	held responsible for the violation in academic honesty. Copying work, or
	knowingly making work available for copying, in contravention of this
	policy is a serious offense that may incur reduced grades, failing the
	course, and disciplinary action. Copying, or helping somebody copy, may
	result in an F on your transcript that you will not be able to drop.

上述的要求对课程所有的单人作业都使用。

	This policy applies to all coursework that is handed in by an
	individual: problem sets, reading exercises, nanoquiz makeups, etc.

#### 组队作业 Group work

你应该和你的队友合作完成组队作业，并且每个人都应该有接近的任务量。

	You should collaborate with your partners on all aspects of group
	project work and in-class collaborative exercises, and each of you is
	expected to contribute a roughly equal share to design and
	implementation.

你可以复用自己在学期内早些时候编写的代码等（包括之前自己和其他队友完成的）。你也可以用课程提供的任何代码。

	You may reuse designs, ideas and code from your own work earlier in the
	semester (even if it was done with a different partner). You may also
	use any code provided by this semester’s 6.031 staff.

你可以使用外部代码，只要：

1. 所有同学都可以访问这个资料
2. 进行了合理的引用
3. 作业允许你这么做

特别地，如果作业要求你“实现 X 功能”，你就必须自己实现 X 功能，不能复用他人的。

你们组不能复用其他组的代码和思路，无论是其他组是当前学期还是以往学期的同学。

	You may also use material from external sources, so long as: (1) the
	material is available to all students in the class; (2) you give proper
	attribution; and (3) the assignment itself allows it. In particular, if
	the assignment says “implement X,” then you must create your own X, not
	reuse someone else’s. Finally, your group may not reuse designs, ideas,
	or code created by another group, in this semester or previous
	semesters.

## 即使修改网络上的代码很常见 Although it is common practice to adapt code examples found on the web,

- 你不能抄袭其他同学的代码。你的同学不是一个合法的代码来源。

		You should never copy code from other students. Your peers are
		not considered an authorized source.

- 你不能简单地复用网上的代码。就像学术写作，你可以采用别人的思路，但是你也要把自己的理解加进去。

		You should not simply re-use code as the solution to an
		assignment. Like academic writing, your code can incorporate the
		ideas of others but should reflect your original approach to the
		problem.

## 引用代码的例子 Examples of citing code sources

例子一 Example 1：

在 Apache 项目的源码的 PluginProxyUtil 类中，开发者引用了论坛的 URL，作者和时间：

	In describing the class PluginProxyUtil in the Apache Project source
	code, the developer cites the source as a post in a forum and includes
	the URL, author and date:

```java
/**
* A utility class that gives applets the ability to detect proxy host settings.
* This was adapted from a post from Chris Forster on 20030227 to a Sun Java
* forum here:
* http://forum.java.sun.com/thread.jspa?threadID=364342&tstart=120
[…]
*/
```

（来源: Apache Project 源代码 http://svn.apache.org 于 2019 年 7 月获取）

	(Source: Apache Project source code http://svn.apache.org retrieved in
	July 2019.)

例子二 Example 2：

在 Google Chrome `stack_trace_win` 的 `OutputTraceToStream` 函数中，开发者引用了 Microsoft Developer Network 并且附带了 URL：

	In the function OutputTraceToStream in the Google Chrome stack_trace_win
	source code, the developer cites the source code as the Microsoft
	Developer Network and includes a URL:

```cpp
// Code adapted from MSDN example:
// http://msdn.microsoft.com/en-us/library/ms680578(VS.85).aspx 
```

（来源： https://github.com/adobe/chromium/blob/master/base/debug/stack_trace_win.cc 于 2019 年 7 月获取） 

	(Source:
	https://github.com/adobe/chromium/blob/master/base/debug/stack_trace_win.cc
	retrieved in July 2019.)


## 引用附有开源许可证的代码的例子 Example of open-source-licensed code:

在 Google Chrome `stack_trace_win` 代码的开头，可以看到版权声明和开源许可证的引用：

	At the top of the Google Chrome stack_trace_win source file, note the
	copyright and reference to the open source license:

```cpp
// Copyright (c) 2011 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
```

如果你把这个代码加入到你的程序中，你需要遵守 Chromium 作者的开源许可证协议中的条款。虽然这个开源许可证只要求你在重分发的时候复制一份版权声明和许可证，一个好习惯是无论是否要求，你都要复制它的版权声明到代码中，和/或把它的许可证放到代码目录的文件中。这样的话，如果你在将来想要重分发你的代码，就很容易检查知识产权相关的问题。

	If you incorporate this code into a program, you should follow the terms
	outlined in The Chromium Authors' open source license file, which is
	shown below. While this license only requires that you duplicate the
	copyright and license if you are redistributing the code, it is good
	practice to always duplicate the copyright in your code, and/or store
	the license in a file with the code. This way, if you want to
	redistribute the code later, intellectual property reviewing becomes
	much easier.

```cpp
// Copyright (c) 2014 The Chromium Authors. All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are
// met:
//
//* Redistributions of source code must retain the above copyright
// notice, this list of conditions and the following disclaimer.
//* Redistributions in binary form must reproduce the above
// copyright notice, this list of conditions and the following disclaimer
// in the documentation and/or other materials provided with the
// distribution.
//* Neither the name of Google Inc. nor the names of its
// contributors may be used to endorse or promote products derived from
// this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
// A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
// OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
// LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
```

（来源：The Chromium Authors license file https://src.chromium.org/viewvc/chrome/trunk/src/LICENSE 于 2019 年 7 月获取）

	(Source: The Chromium Authors license file
	https://src.chromium.org/viewvc/chrome/trunk/src/LICENSE retrieved in
	July 2019.)