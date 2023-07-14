---
layout: post
date: 2021-08-06
tags: [intel,intrinsics]
categories:
    - misc
---

# 轶事一则

7.31 号周六的时候，发现 Intel Intrinsics Guide(https://software.intel.com/sites/landingpage/IntrinsicsGuide/) 出现错误，加载数据失败，于是在 Intel 的网站上提交了一个 bug。

8.2 号的时候，Intel 发邮件过来，说已经复现了问题，已经汇报给了后端团队。邮件原文：

	Thank you for bringing this to our attention. We have verified and
	encountered the same issue. Please know that we have escalated this
	issue to our backend technical team. 
	
	We will get back to you as soon as we have an update. Have a nice day
	ahead!

8.4 号的时候，Intel 再次发邮件过来，说后端团队正在处理这个问题，会尽快完成修复，请我耐心等待。这个时候我去网站上看，还是有问题。邮件原文：

	Our backend team is still working on this issue. We are trying our level
	best to get back to you with an update soon.
	
	Have a nice day ahead!

8.6 号 19:27 的时候，Intel 又发了一次邮件，说后端团队依然在处理这个问题，并且正在进行一个永久性的修复（言下之意是现在提供了一个临时性的修复）。这个时候去网站上看，终于是修好了。邮件原文：

	We have received an update from our backend team is that they are
	working on this issue and, a more permanent fix is in the works.
	Hopefully, it will resolve soon.
	
	We appreciate your patience and understanding on this matter. Have a
	nice day!

我回复了一下邮件，告诉 Intel 我这边看到已经是修复好的版本，紧接着又收到了一封邮件，告诉我可以从网站上下载离线版的 Intrinsics Guide：

	Thank you for your prompt response. We are glad that your issue has been
	resolved and we would like to thank you for your co operation.  Please
	be informed that the offline version of the Intrinsic Guide is now
	available for download from the site. The offline version of the guide
	has the same content as the site, but is viewable offline by the user. A
	link to the download is now added in the left column of the site:
	https://software.intel.com/sites/landingpage/IntrinsicsGuide/
	
	That said, we are closing this ticket and if you have further issues
	please open another ticket and we will be happy to help you.
	
	After case closure, you will receive a survey email. We appreciate it if
	you can complete this survey regarding the support you received.  Your
	feedback will help us improve our support.
	
	For any concerns related to Intel® Developer Zone account, login or
	website, please feel free to open a new ticket:
	https://software.intel.com/en-us/support

这次 Intel Support 的反应挺快的，给个好评。就是希望 Intel 能够不挤牙膏，能拿出和 AMD 相当水平的 CPU。

