---
layout: post
date: 2014-05-30
tags: [java,intellijidea]
categories:
    - csdn
title: IntelliJ IDEA 手动更新方法
---

迁移自本人在 CSDN 上的博客：https://blog.csdn.net/build7601/article/details/27704683

经常，IntelliJ IDEA 更新时，会发现这个：

download-cf.jetbrains.com/idea/IU-135.690-135.909-patch-win.jar 下载不了。不然只能去下载完全版重新安装一次

解决方案如下：

使用代理下载上面那个文件（视版本而定），

拷贝到 IntelliJ IDEA 安装目录，

敲击 java -classpath IU-135.690-135.909-patch-win.jar com.intellij.updater.Runner install . 

注意，最后那个点表示更新到当前目录。

会输出这个：Exception in thread "main" java.lang.NoClassDefFoundError: org/apache/log4j/Layo
ut
        at java.lang.Class.getDeclaredMethods0(Native Method)
        at java.lang.Class.privateGetDeclaredMethods(Unknown Source)
        at java.lang.Class.getMethod0(Unknown Source)
        at java.lang.Class.getMethod(Unknown Source)
        at sun.launcher.LauncherHelper.validateMainClass(Unknown Source)
        at sun.launcher.LauncherHelper.checkAndLoadMain(Unknown Source)
Caused by: java.lang.ClassNotFoundException: org.apache.log4j.Layout
        at java.net.URLClassLoader$1.run(Unknown Source)
        at java.net.URLClassLoader$1.run(Unknown Source)
        at java.security.AccessController.doPrivileged(Native Method)
        at java.net.URLClassLoader.findClass(Unknown Source)
        at java.lang.ClassLoader.loadClass(Unknown Source)
        at sun.misc.Launcher$AppClassLoader.loadClass(Unknown Source)
        at java.lang.ClassLoader.loadClass(Unknown Source)
        ... 6 more


发现少了 log4j，发现 lib 目录下就有，果断加到 classpath：

java -classpath IU-135.690-135.909-patch-win.jar;.\lib\log4j.jar com.intellij.updater.Runner install .
弹出升级窗口，成功！

IntelliJ IDEA 设置代理升级失败，设置系统代理也失败。。可能是 rp？但是浏览器就可以。