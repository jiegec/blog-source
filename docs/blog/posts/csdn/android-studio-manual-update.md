---
layout: post
date: 2014-12-06
tags: [java,intellijidea,android,androidstudio]
category: csdn
title: Android Studio 手工更新小记
---

迁移自本人在 CSDN 上的博客：https://blog.csdn.net/build7601/article/details/41776599

因为长时间不更新 Android Studio，回头一看，我的版本才 135.1339820，最新版本都 135.1626825 去了，我就萌生了更新的念头。。

首先，我尝试调用 update_studio.sh。。。。。但是！！404 Not Found！！看来版本跨度太大无法打补丁了呢。。

那只好看看 https://dl.google.com/android/studio/patches/updates.xml 这个里面了，找到我的版本号：

```xml
<channel id="AI-0-beta" name="Android Studio updates" status="beta" url="http://tools.android.com/recent" feedback="https://code.google.com/p/android/issues/entry?template=Android+Studio+bug" majorVersion="0">
<build number="135.1623071" version="0.9.9">
<message>
<![CDATA[
<html> A new Android Studio 0.9.9 is available in the beta channel.<br> This patch will allow you to update from 0.x to 1.x.<br> After updating, please check for updates again to install 1.0 RC.<p/> </html>
]]>
</message>
<button name="Download" url="http://developer.android.com/sdk/installing/studio.html" download="true"/>
<button name="Release Notes" url="http://tools.android.com/recent"/>
<patch from="135.1339820" size="176"/>
<!-- 0.8.6 -->
<patch from="135.1404660" size="176"/>
<!-- 0.8.9 -->
<patch from="135.1446794" size="161"/>
<!-- 0.8.11 -->
<patch from="135.1503853" size="90"/>
<!-- 0.8.12 -->
<patch from="135.1525417" size="89"/>
<!-- 0.8.13 -->
<patch from="135.1538390" size="89"/>
<!-- 0.8.14 -->
<patch from="135.1551333" size="71"/>
<!-- 0.9.0 -->
<patch from="135.1561280" size="71"/>
<!-- 0.9.1 -->
<patch from="135.1569493" size="71"/>
<!-- 0.9.2 -->
<patch from="135.1585741" size="71"/>
<!-- 0.9.3 -->
</build>
</channel>
```

还好还好，差点就升不上去了。。。

立马下载 https://dl.google.com/android/studio/patches/AI-135.1339820-135.1623071-patch-mac.jar ..也是大，差不多和重新下载一样大了。。

进入 Android Studio 目录，输入 java -cp AI-135.1339820-135.1623071-patch-mac.jar com.intellij.updater.Runner install . （记住后面的。表示安装目录）。

弹出窗口，升级成功，yeah！

以后要想用 patch 升级，一定要尽快啊～

吐槽一下 update_studio.sh 的编写人，我要改进一下他的脚本。。升不上去太挫了。。

题外话：

打完补丁，出现 Java not found 错误，发现我的 java 版本是 Oracle1.8，而他要的是 Apple1.6.。。那我只好安装一下，然后呢？就好了！！！！！