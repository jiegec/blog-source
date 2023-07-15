---
layout: post
date: 2022-08-05
tags: [tex,latex,ps,dvi,pdf]
categories:
    - software
---

# 从 TeX 到 PDF 的过程

## 背景

今天跑 `xdvipdfmx` 的时候出现了报错，忽然想研究一下，DVI 格式是什么，TeX 是如何一步步变成 PDF 的。

<!-- more -->

## 流程

实际上从 TeX 到 PDF 有不同的工具，其中可能经历了不同的转化过程。

我们今天来看一种比较原始的转换方式：从 TeX 到 DVI，从 DVI 到 PS，再 PS 到 PDF，主要目的是看看这些格式内部都是什么样子的。

## 从 TeX 到 DVI

举一个很小的例子，例如 `test.tex` 有如下的内容：

```tex
Hello, world!
\bye
```

在命令行中运行 `tex test.tex`，可以看到它生成了 `test.dvi` 文件：

```shell
$ tex test.tex
(test.tex [1] )
Output written on test.dvi (1 page, 228 bytes).
Transcript written on test.log.
```

那么 DVI 就是 TeX 引擎输出的默认格式了。我们可以用 dviinfox 和 dviasm 工具来看它的一些信息：

```shell
$ dviinfox test.dvi
test.dvi: DVI format 2; 1 page
  Magnification: 1000/1000
  Size unit: 1000x25400000/(1000x473628672)dum = 0.054dum = 1.000sp
  Page size: 469ptx667pt = 16.510cmx23.449cm
  Stack size: 2
  Comment: " TeX output 2022.08.05:2055"
  Font   0:     cmr10 at 10.000 (design size 10.000, checksum=1274110073)
$ dviasm test.dvi
[preamble]
id: 2
numerator: 25400000
denominator: 473628672
magnification: 1000
comment: ' TeX output 2022.08.05:2058'

[postamble]
maxv: 667.202545pt
maxh: 469.754990pt
maxs: 2
pages: 1

[font definitions]
fntdef: cmr10 at 10pt

[page 1 0 0 0 0 0 0 0 0 0]
push:
  down: -14pt
pop:
down: 643.202545pt
push:
  down: -633.202545pt
  push:
    right: 20pt
    fnt: cmr10 at 10pt
    set: 'Hello,'
    right: 3.333328pt
    set: 'w'
    right: -0.277786pt
    set: 'orld!'
  pop:
pop:
down: 24pt
push:
  right: 232.377487pt
  set: '1'
pop:
```

可以看到，它定义了文档的一些尺寸和字体信息，然后主体部分就是每个页面上需要绘制的内容：

```
push:
  down: -14pt
pop:
down: 643.202545pt
push:
  down: -633.202545pt
  push:
    right: 20pt
    fnt: cmr10 at 10pt
    set: 'Hello,'
    right: 3.333328pt
    set: 'w'
    right: -0.277786pt
    set: 'orld!'
  pop:
pop:
down: 24pt
push:
  right: 232.377487pt
  set: '1'
pop:
```

可以看到，它保存了一些命令，就像是在移动光标，然后输出文字：

1. 向下移动 643.20 pt
2. 向上移动 633.20 pt
3. 向右移动 20.00 pt
4. 设置字体为 cmr10
5. 输出 "Hello,"
6. 向右移动 3.33 pt
7. 输出 "w"
8. 向左移动 0.28 pt
9. 输出 "orld!"

实际上，它的编码也比较简单，就是一个字节的命令加上若干字节的参数。DVI 二进制格式详细的文档可见 <https://www.mn.uio.no/ifi/tjenester/it/hjelp/latex/dvi.pdf>。

## 从 DVI 到 PS

有了 DVI 文件以后，下一步是用 `dvips` 工具来生成 PS 文件：

```shell
$ dvips test.dvi
This is dvips(k) 2020.1 Copyright 2020 Radical Eye Software (www.radicaleye.com)
' TeX output 2022.08.05:2058' -> test.ps
</usr/share/texlive/texmf-dist/dvips/base/tex.pro>
</usr/share/texlive/texmf-dist/dvips/base/texps.pro>.
</usr/share/texlive/texmf-dist/fonts/type1/public/amsfonts/cm/cmr10.pfb>[1]
```

DVI 是二进制格式，而 PS 是纯文本格式，我们可以用编辑器打开，看到里面大概有几部分内容：

1. 开头的元数据
2. tex.pro 文件的内容
3. texps.pro 文件的内容
4. 定义 CMR10 字体
5. 描述文档内容

让我们直接来看最后一部分：

```postscript
TeXDict begin 39158280 55380996 1000 600 600 (test.dvi)
@start /Fa 136[60 4[33 2[42 2[23 6[37 46 27[62 22[42
4[23 10[23 33[{}10 83.022 /CMR10 rf end
%%EndProlog
%%BeginSetup
%%Feature: *Resolution 600dpi
TeXDict begin
%%BeginPaperSize: a4
/setpagedevice where
{ pop << /PageSize [595 842] >> setpagedevice }
{ /a4 where { pop a4 } if }
ifelse
%%EndPaperSize
 end
%%EndSetup
%%Page: 1 1
TeXDict begin 1 0 bop 166 83 a Fa(Hello,)28 b(w)n(orld!)1929
5539 y(1)p eop end
%%Trailer

userdict /end-hook known{end-hook}if
%%EOF
```

看到这个，肯定觉得很疑惑，这都是啥？除了隐约可以看到的 `Hello,` `w` `orld!` 字样以外，有很多不明含义的字母和代码。

为了读懂这些代码在做什么，首先来学习一下 PostScript。PostScript 是一个基于栈的语言，类似 Forth，所以很多运算都和我们平时看到的不一样。例如：

```postscript
userdict /end-hook known{end-hook}if
```

实际上做的事情是，判断 userdict 中是否存在 `/end-hook`，如果存在，则展开它。它的计算过程是：

```postscript
userdict
userdict /end-hook
userdict /end-hook known
true
true {end-hook}
true {end-hook} if
end-hook
```

那么回过头来看 `Hello, world!` 相关的代码：

```postscript
TeXDict begin 1 0 bop 166 83 a Fa(Hello,)28 b(w)n(orld!)1929
5539 y(1)p eop end
```

这里出现的 `TeXDict` `bop` `a` 等等应该也是在前面定义的了。往回翻，发现正是 `tex.pro` 文件定义了这些对象。让我们一点点来看：

```postscript
/TeXDict 300 dict def   % define a working dictionary
```

表示 `TexDict` 会展开为 `300 dict`，即创建一个最大容量为 300 的 dict。接下来的 begin 和 end 就是在这个 dict 的作用域中进行运算。

接下来是 `1 0 bop`，那么我们要看 `bop` 的定义，根据 DVI 中同名的命令，我们知道它的意思是 `begin of page`:

```postscript
/bop           % %t %d bop -  -- begin a brand new page, %t=pageno %d=seqno
  {
    userdict /bop-hook known { bop-hook } if
    /SI save N
    @rigin
%
%   Now we check the resolution.  If it's correct, we use RV as V,
%   otherwise we use QV.
%
    0 0 moveto
    /V matrix currentmatrix
    A 1 get A mul exch 0 get A mul add .99 lt
    {/QV} {/RV} ifelse load def
    pop pop
  } N
```

这里有一些代码的含义我还不清楚，先跳过。

接下来的 `166 83 a`，根据定义就可以判断出来它是在移动位置：

```postscript
/a { moveto } B    % absolute positioning
```

紧随其后的 `Fa` 指的是字体。

接下来是 `(Hello,)`，即把 `Hello,` 这些文字压入栈。

接下来看到 `28 b`，它输出了栈顶的文本，进行了一个相对的水平移动，并且更新了 delta：

```postscript
/delta 0 N         % we need a variable to hold space moves
%
%   The next ten macros allow us to make horizontal motions that
%   are within 4 of the previous horizontal motion with a single
%   character.  These are typically used for spaces.
%
/tail { A /delta X 0 rmoveto } B
/M { S p delta add tail } B
/b { S p tail } B      % show and tail!
```

后面的也都是类似的操作，让我们简单来总结一下 `TeXDict begin 1 0 bop 166 83 a Fa(Hello,)28 b(w)n(orld!)1929 5539 y(1)p eop end` 都做了什么：

1. `1 0 bop`: 创建了新页面
2. `166 83 a`: 移动坐标到 `(166, 83)`
3. `Fa`: 设置字体
4. `(Hello,)`: 压栈 "Hello,"
5. `28 b`: 输出栈顶，移动坐标，对应 `dviasm` 输出中的 `right: 3.333328pt`
6. `(w)`: 压栈 "w"
7. `n`: 输出栈顶，移动坐标，对应 `dviasm` 输出中的 `right: -0.277786pt`
8. `(orld!)`: 压栈 "orld!"
9. `1929 5539 y`: 输出栈顶，移动坐标到页码的位置，对应 `dviasm` 输出中的 `down: 24pt` 和 `right: 232.377487.pt`
10. `(1)`: 压栈 "1"
11. `p`: 输出栈顶
12. `eop`: 结束页面

由此我们基本明白了从 DVI 到 PS 是怎么一个流程：

1. 首先在 `tex.pro` 中定义了一些函数，来实现 DVI 中的命令
2. 把 DVI 中的命令翻译成 PS 代码
3. 把 `tex.pro`、字体等还有翻译出来的 PS 拼接起来作为最终的输出

这算是一种元编程，在 PS 中定义了一个 DSL，可以很方便地执行 DVI 指令。

在 [这里](https://github.com/MiKTeX/miktex/blob/ab8ebca7c70fe8c9a1392dfb2393a0a7683e14cc/Programs/DviWare/dvips/source/tex.lpro) 可以看到原始的带注释的 `tex.lpro` 实现，上面涉及 `tex.pro` 的代码内容也是从这里复制来的。

## 从 PS 到 PDF

最后一步，我们可以用 `ps2pdf` 把 PS 转换为 PDF。转换以后，就可以用常见的 PDF 浏览器来阅读了。让我们解压缩其中被压缩的部分，这样就方便阅读它的内容了：

```shell
ps2pdf test.ps
pdftk test.pdf output test.unc.pdf uncompress
```

在里面就可以找到我们的 `Hello, world!` 了：

```pdf
5 0 obj

<<
/Length 225
>>
stream
q 0.1 0 0 0.1 0 0 cm
0 g
q
10 0 0 10 0 0 cm BT
/R7 9.96264 Tf
1 0 0 1 91.9199 710.04 Tm
[(H)3.21024(e)-1.66516(llo)-5.88993(,)-337.276(w)23.3747(o)-5.88993(r)-6.48419(ld)0.929988(!)]TJ
211.56 -654.72 Td
[(1)-5.8887]TJ
ET
Q
Q

endstream
endobj
```

阅读 [PDF 标准](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf)，可以发现它的输出文本部分是这样的：

```pdf
BT
	/R7 9.96264 Tf
	1 0 0 1 91.9199 710.04 Tm
	[(H)3.21024(e)-1.66516(llo)-5.88993(,)-337.276(w)23.3747(o)-5.88993(r)-6.48419(ld)0.929988(!)]TJ
	211.56 -654.72 Td
	[(1)-5.8887]TJ
ET
```

其中：

1. `/R7 9.96264 Tf` 设置了字体 `/R7`，大小是 `9.96264`
2. `1 0 0 1 91.9199 710.04 Tm` 设置 Text matrix
3. `[(H)3.21024(e)-1.66516(llo)-5.88993(,)-337.276(w)23.3747(o)-5.88993(r)-6.48419(ld)0.929988(!)]TJ` 输出一系列的 `Hello, world!`，中间的数字表示的是文字之间移动的坐标
4. `211.56 -654.72 Td` 移动坐标到页码的位置
5. `[(1)-5.8887]TJ` 输出页码

可以看到，从 PS 到 PDF 这一步就不是简单的映射了，例如在 DVI 和 PS 中都是 `Hello,` `w` `orld!` 这样断开，而在 PDF 里面则是 `H` `e` `llo` `,` `w` `o` `r` `ld` `!`。