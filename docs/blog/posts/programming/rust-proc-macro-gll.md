---
layout: post
date: 2019-11-15
tags: [rust,gll,parsing,parser,metaprogramming]
category: programming
title: 用 Rust Procedure Macro 实现 GLL Parser
---

## 背景

在编译原理课上，PA 框架采用的是 [MashPlant/lalr1](https://github.com/MashPlant/lalr1) ，是一个比较好用的 Lexer + Parser 的工具，它的大概语法见 [一个完整的例子](https://mashplant.gitbook.io/decaf-doc/pa1a/lalr1-shi-yong-zhi-dao/yi-ge-wan-zheng-de-li-zi) 。然后之前看到了 GLL Parser，想着可不可以照着类似的语法也写一个 GLL 的 Parser Generator，也是用 Rust Procedure Macro 的方法，就开始了研究。

## 尝试

首先是阅读 GLL 的论文，它并不长，大概的意思就是，LL(1) 文法需要考虑 PS 冲突的情况，而 GLL 的解决方法就是“都试一下”，然后为了效率，用了 GSS 表示解析过程和 SPPF 表示解析结果。然后就开始照着论文手写了不同版本的实现，见 [jiegec/gll-test](https://github.com/jiegec/gll-test) 。

第一种就是按照论文里第一段实现直接抄过来，每个可能性作为一个 Continuation 存下来，它有自己的栈和执行位置（Label）。这样 Work 以后呢，我又想到了 async/await，用类似的方法又写了一遍，相对要简洁一些，也是很平常的递归下降的写法，而不是 Loop + Label 的形式。但这些都不能做到合并栈的目的，所以遇到十分有歧义的文法的时候会很糟糕。

然后开始按照论文中的 GSS 进行编写，基本还是按照论文进行翻译，然后一步一步做，做好以后把 GSS 画出来，和论文的图可以对的上；然后照着 GLL parse-tree generation 的论文把 SPPF 实现了，这时候就可以从 recongizer 变成一个 parser 了。

## 宏

得到一份可行的代码以后，就要扩展到通用的情况上。学习了一下 MashPlant/lalr1 的实现，实现了一个 proc macro，它读取了用户的程序，从一个模板文件开始，往里面插入一些生成的代码，丢给编译器去编译。这时候就涉及到编译期和运行时的不同了，我把运行时一些通用的结构放到了 `gll-pg-core` 中，把编译期的代码放到了 `gll-pg-macros` 。

代码生成的时候，基本按照之前自己写的样子抄，只不过这个时候要按照用户编写的产生式进行生成了，各种名字都要规范化，变得可以复用，然后尽量减少命名空间的污染等等这些常见的写宏需要注意的操作。

不过，考虑到现在还没有实现 Lexer，所以先用了 Logos 库作为 Lexer。但我其实不大喜欢它，因为它太简单，也没有行号的信息，不过暂且先这样吧，以后可能会自己实现。

然后 0.1.0 版本就诞生了，它的样例长这样：

```rust
//! This example is taken from MashPlant/lalr1

use gll_pg_core::LogosToken;
use gll_pg_macros::gll;
use logos::Logos;

#[derive(Logos, Debug, Eq, PartialEq, Clone)]
pub enum Token {
    #[end]
    End,
    #[error]
    Error,
    #[token = " "]
    _Eps,
    #[token = "+"]
    Add,
    #[token = "-"]
    Sub,
    #[token = "*"]
    Mul,
    #[token = "/"]
    Div,
    #[token = "%"]
    Mod,
    #[token = "("]
    LPar,
    #[token = ")"]
    RPar,
    #[regex = "[0-9]+"]
    IntLit,
}

#[gll(Expr, Token)]
impl Parser {
    #[rule(Expr -> Expr Add Expr)]
    fn expr_add(l: i32, _op: LogosToken<Token>, r: i32) -> i32 {
        l + r
    }
    #[rule(Expr -> Expr Sub Expr)]
    fn expr_sub(l: i32, _op: LogosToken<Token>, r: i32) -> i32 {
        l - r
    }
    #[rule(Expr -> Expr Mul Expr)]
    fn expr_mul(l: i32, _op: LogosToken<Token>, r: i32) -> i32 {
        l * r
    }
    #[rule(Expr -> Expr Div Expr)]
    fn expr_div(l: i32, _op: LogosToken<Token>, r: i32) -> i32 {
        l / r
    }
    #[rule(Expr -> Expr Mod Expr)]
    fn expr_mod(l: i32, _op: LogosToken<Token>, r: i32) -> i32 {
        l % r
    }
    #[rule(Expr -> Sub Expr)]
    fn expr_neg(_op: LogosToken<Token>, r: i32) -> i32 {
        -r
    }
    #[rule(Expr -> LPar Expr RPar)]
    fn expr_paren(_l: LogosToken<Token>, i: i32, _r: LogosToken<Token>) -> i32 {
        i
    }
    #[rule(Expr -> IntLit)]
    fn expr_int(i: LogosToken<Token>) -> i32 {
        i.slice.parse().unwrap()
    }
}

#[test]
fn gll() {
    let mut lexer = Token::lexer("1 + 2 * 3");
    let res = Parser::parse(&mut lexer);
    // two ways to parse
    assert_eq!(res, [7, 9]);
}
```

可以看到，它解析的结果是一个数组，对应所有可能出现的情况。这样比较简单，但是要求中间各种类型都是 Clone，因为同一个结点可能会被用多次。它的计算方法就是在最终的 SPPF 上递归找到所有可能性，然后调用用户代码，最后放到一个 Vec 中。

## 记忆化

但是，上面的做法有一个很大的问题，就是，虽然 SPPF 的空间复杂度是有限的，但所有可能的解析树可以有很多，如果把每一个情况都完整的存在一个 Vec 中，空间要求是很高的，中间也有很多重复计算的情况。所以需要做记忆化，然后每次给出一个。因为依赖自己内部的状态，所以不能是 Iterator 只能是 StreamingIterator。

记忆化也花了我一番功夫，现在用了一个比较土的办法，在每个结点上记录了当前遇到过的所有可能，这个是逐渐构造的，意味着如果只需要第一种解析树，不需要额外的空间。然后逐渐扩张，如果有可以重用的结构就重用，把涉及的所有的结构都放在一个 Vec 中，用完之后一起 drop 掉。

当然了，这个时候，各种东西都变成了引用：

```rust
//! This example is taken from MashPlant/lalr1

use gll_pg_core::*;
use gll_pg_macros::gll;
use logos::Logos;

#[derive(Logos, Debug, Eq, PartialEq, Clone)]
enum Token {
    #[end]
    End,
    #[error]
    Error,
    #[token = " "]
    _Eps,
    #[token = "+"]
    Add,
    #[token = "-"]
    Sub,
    #[token = "*"]
    Mul,
    #[token = "/"]
    Div,
    #[token = "%"]
    Mod,
    #[token = "("]
    LPar,
    #[token = ")"]
    RPar,
    #[regex = "[0-9]+"]
    IntLit,
}

#[derive(Default)]
struct Parser {
    literals: Vec<i32>,
}

#[gll(Expr, Token)]
impl Parser {
    // you can omit self
    #[rule(Expr -> Expr Add Expr)]
    fn expr_add(l: &i32, _op: &LogosToken<Token>, r: &i32) -> i32 {
        *l + *r
    }
    // you can use &self
    #[rule(Expr -> Expr Sub Expr)]
    fn expr_sub(&self, l: &i32, _op: &LogosToken<Token>, r: &i32) -> i32 {
        *l - *r
    }
    // you can use &mut self as well
    // but all of these have &mut self in fact
    #[rule(Expr -> Expr Mul Expr)]
    fn expr_mul(&mut self, l: &i32, _op: &LogosToken<Token>, r: &i32) -> i32 {
        *l * *r
    }
    #[rule(Expr -> Expr Div Expr)]
    fn expr_div(l: &i32, _op: &LogosToken<Token>, r: &i32) -> i32 {
        *l / *r
    }
    #[rule(Expr -> Expr Mod Expr)]
    fn expr_mod(l: &i32, _op: &LogosToken<Token>, r: &i32) -> i32 {
        *l % *r
    }
    #[rule(Expr -> Sub Expr)]
    fn expr_neg(_op: &LogosToken<Token>, r: &i32) -> i32 {
        -*r
    }
    #[rule(Expr -> LPar Expr RPar)]
    fn expr_paren(_l: &LogosToken<Token>, i: &i32, _r: &LogosToken<Token>) -> i32 {
        *i
    }
    // so you can make your IDE happy with &mut self here
    #[rule(Expr -> IntLit)]
    fn expr_int(&mut self, i: &LogosToken<Token>) -> i32 {
        let lit = i.slice.parse().unwrap();
        self.literals.push(lit);
        lit
    }
}

#[test]
fn ambiguous() {
    let mut lexer = Token::lexer("1 + 2 + 3");
    let mut parser = Parser { literals: vec![] };
    let res = parser.parse(&mut lexer).unwrap();
    // two ways to parse
    let res: Vec<_> = res.cloned().collect();
    assert_eq!(res, vec![6, 6]);
}

```

这时候就是 0.3.0 版本，基本达到了我一开始想要的程度。

## 错误处理

在之前写编译原理 PA1 的时候，遇到的一个问题就是，如果自己的代码有错，因为宏展开以后丢失了位置信息，所以报错都会在错误的位置。一番查找以后，找到了解决方案：原样记录下原来的代码（syn::Block），然后通过 quote 宏直接拼接到最终的 TokenStream 中，这样在结果里，虽然代码还是那些代码，但部分的 Token 就有了正确的位置，这样就很方便用户代码的修改了。不过还是不方便找模板部分的代码错误，毕竟那部分确实在原来的代码中没有出现过。

对于模板中的代码错误，我最终的解决方案是 `cargo-expand` ，把我的测试代码和展开后的代码拼接起来，然后在茫茫的无关报错下去找我的错误的地方。虽然不是很好用，但毕竟还是 work 的。另外，宏还需要对用户代码的一些类型进行检查，比如上面的 Expr 对应 i32，这个就需要在各处都保持一致，但这个就需要自己进行检查了。使用了一下 proc_macro_diagnostic 的 API，还不是很好用，等它 stable 吧。

## 总结

终于自己手写了一个 Procedure Macro，感觉现有的工具已经比较成熟了，有 syn quote 以后很多操作都很方便。但代码还有很多地方可以优化，慢慢搞吧。