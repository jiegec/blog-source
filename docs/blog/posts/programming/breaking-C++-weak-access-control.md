---
layout: post
date: 2018-03-07
tags: [c++,hack]
categories:
    - programming
title: 〖新手向〗绕过 C++ 类的访问限制
---

这是一篇很水的文章，面向萌新，已经知道了的可以自觉绕道。

昨天上课，有同学问，如果用户偷偷把 `private` 改成 `public` 再和原有的库链接，是不是就可以在用户代码里更改了。这个答案是肯定的。下面我们就做个实验：

首先，创建 good_class.h 和 good_class.cpp:

```c++
class SomeClass {
private:
    int data;
public:
    int getData();
};
```

```c++
#include "good_class.h"

int SomeClass::getData() {
    return data;
}
```

然后，首先编译，

```shell
clang++ -c good_class.cpp -o good_class.o
```

然后，修改 good_class.cpp 并写一个 evil_user.cpp

```c++
class SomeClass {
public:
    int data;
public:
    int getData();
};
```

```c++
#include <stdio.h>
#include "good_class.h"

int main() {
    SomeClass a;
    a.data = 37;
    printf("%d\n", a.getData());
    return 0;
}
```

编译：

```shell
clang++ good_class.o evil_user.cpp -o evil
```

然后 `evil` 如愿地输出了 `37` 。

一些提醒：

1. `C++` 的访问控制十分的弱，仅仅是编译期。所以是很容易绕过的。
2. 对于不想泄露源代码的库，不要导出 `C++` 的类和函数。选择导出 `C` 函数，结构体用 incomplete type 或者干脆 `void *` 。

扩展阅读： [L 叔的通过虚函数表访问私有函数](https://liam0205.me/2018/01/23/crack-private-member-function-by-vtable/) 。
