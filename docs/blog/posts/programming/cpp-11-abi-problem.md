---
layout: post
date: 2021-06-23
tags: [gcc,clang,c++,cpp,c++11,abi]
category: programming
title: C++ 11 的 ABI 问题
---

## 背景

有同学遇到这样的一个问题，代码中链接了一个第三方的动态库，在链接的时候出现了不一致的问题，比如有一个函数签名如下：

```cpp
void foobar(std::string s) {}
```

使用 GCC 11.1.0 编译上面的代码，可以发现它需要的符号是 `_Z6foobarNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE`，但是第三方库里面却是 `_Z6foobarSs`，因此找不到对应的符号，链接失败。

## 问题

经过一番研究，发现 `Ss` 在 [Itanium ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html) 中表示的是缩写：

```
In addition, the following catalog of abbreviations of the form "Sx" are used:


   <substitution> ::= St # ::std::
   <substitution> ::= Sa # ::std::allocator
   <substitution> ::= Sb # ::std::basic_string
   <substitution> ::= Ss # ::std::basic_string < char,
						 ::std::char_traits<char>,
						 ::std::allocator<char> >
   <substitution> ::= Si # ::std::basic_istream<char,  std::char_traits<char> >
   <substitution> ::= So # ::std::basic_ostream<char,  std::char_traits<char> >
   <substitution> ::= Sd # ::std::basic_iostream<char, std::char_traits<char> >
```

这看起来很正常，`_Z6foobarSs` 表示的是 `foobar(std::basic_string<char, std::char_traits<char>, std::allocator<char> >)`，但是 GCC 11.1.0 编译出来的上面的代码却没有用这个符号，而是 `foobar(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >)`。差别就在于 `__cxx11` 中。

经过一番搜索，找到了 GCC [关于这个问题的文档](https://gcc.gnu.org/onlinedocs/libstdc++/manual/using_dual_abi.html)和[网上的文章](https://developers.redhat.com/blog/2015/02/05/gcc5-and-the-c11-abi)，找到了原因：从 GCC5 开始，为了兼容 C++11 标准的改变，做了这个变动。如果要恢复原来的行为，需要添加一个定义：

```shell
$ g++ -D_GLIBCXX_USE_CXX11_ABI=0 -c test.cpp -o test.o && nm test.o | grep foobar
0000000000000000 T _Z6foobarSs
$ g++ -c test.cpp -o test.o && nm test.o | grep foobar
0000000000000000 T _Z6foobarNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE
# install g++-4.9 in ubuntu 16.04
$ g++-4.9 -c test.cpp -o test.o && nm test.o | grep foobar
0000000000000000 T _Z6foobarSs
```

这样就可以正常链接到第三方的动态库了。

