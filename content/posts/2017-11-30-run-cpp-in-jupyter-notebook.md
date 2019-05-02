---
layout: post
date: 2017-11-30 18:07:10 +0800
tag: [jupyter, cling, c++]
category: programming
---

刚刚在HN上看到了这么一个文章：[Interactive Workflows for C++ with Jupyter](https://blog.jupyter.org/interactive-workflows-for-c-with-jupyter-fe9b54227d92) [HN](https://news.ycombinator.com/item?id=15808809) ，终于可以在Jupyter Notebook里跑C++代码了，很开心，于是开始自己研究了起来怎么本地跑。

首先当然是更新一波jupyter，安装一波cling：

```shell
pip3 install -U jupyter
brew install cling
```

然后根据[官方教程](https://github.com/root-project/cling/tree/master/tools/Jupyter)里的要求执行：

```shell
cd /usr/local/share/cling/Jupyter/kernel
pip3 install -e .
jupyter kernelspec install cling-cpp11
jupyter kernelspec install cling-cpp14
jupyter kernelspec install cling-cpp17
jupyter kernelspec install cling-cpp1z
```

结果发现找不到`jupyter-kernelspec`，遂重装了一下`jupyter-client`这个包，果然就可以了。打开一个notebook测试：

```
jupyter notebook
```

然后创建一个C++14的Notebook，结果发现一直Kernel rebooting，错误信息是说找不到`../Cellar/cling/0.5/lib/libclingJupyter.dylib`。这一看就是路径处理的问题，当前目录肯定不是`/usr/local`，肯定出现了什么问题，然后研究发现`cling-kernel.py`中对`cling`判断是否是个连接，如果是连接则按照连接去找`cling`的安装目录，但是！没有考虑到这个连接是个相对路径的问题（Homebrew你背锅吗）。于是我愉快地改了代码并提交了[PR](https://github.com/root-project/cling/pull/198)。修复了以后就可以用了。

以下是一个小小的例子：
```shell
>> jupyter console --kernel cling-cpp14
Jupyter console 5.2.0

cling-X


In [1]: #include <stdio.h>
Out[1]:

In [2]: char *s = "Hello, world!";
input_line_4:2:12: warning: ISO C++11 does not allow conversion from string literal to 'char *' [-Wwritable-strings]
 char *s = "Hello, world!";
           ^
Out[2]:

In [3]: printf("%s",s);
Hello, world!Out[3]:
(int) 13

```

Okay，大功告成！
