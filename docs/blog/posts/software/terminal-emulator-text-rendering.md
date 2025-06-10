---
layout: post
date: 2025-06-10
tags: [huawei,arm64,matebook,matebookpro,harmonyos,termony]
categories:
    - hardware
---

# 终端模拟器的文字绘制

## 背景

最近在造鸿蒙电脑上的终端模拟器 [Termony](https://github.com/jiegec/Termony)，一开始用 ArkTS 的 Text + Span 空间来绘制终端，后来发现这样性能和可定制性比较差，就选择了自己用 OpenGL 实现，顺带学习了一下终端模拟器的文字绘制是什么样的一个过程。

<!-- more -->

## 读取字形

文本绘制，首先就要从字体文件中读取字形，提取出 Bitmap 来，然后把 Bitmap 绘制到该去的地方。为了提取这些信息，首先用 FreeType 库，它可以解析字体文件，然后计算出给定大小的给定字符的 Bitmap。但是，这个 Bitmap 它只记录字体非空白的部分（准确的说，是 Bounding Box），如下图的 width * height 部分：

![](terminal-emulator-text-rendering-font.png)

（图源：[Managing Glyphs - FreeType Tutorial II](https://freetype.org/freetype2/docs/tutorial/step2.html)）

其中 x 轴，应该是同一行的字体对齐的，这样才会看到有高有低的字符出现在同一行，而不是全部上对齐或者下对齐。得到的 Bitmap 是行优先的，也就是说：

- 图中左上角，坐标 (xMin, yMax) 对应 Bitmap 数组的下标是 `0`
- 图中右上角，坐标 (xMax, yMax) 对应 Bitmap 数组的下标是 `width-1`
- 图中左下角，坐标 (xMin, yMin) 对应 Bitmap 数组的下标是 `width*(height-1)`
- 图中右下角，坐标 (xMax, yMax) 对应 Bitmap 数组的下标是 `width*(height-1)+width-1`

得到这个 Bitmap 后，如果我们不用 OpenGL，而是直接生成 PNG，那就直接进行一次 copy 甚至 blend 就可以把文字绘制上去了。但是，我们要用 OpenGL 的 shader，就需要把 bitmap 放到 texture 里面。由于目前我们用的就是单色的字体，所以它对应只有一个 channel 的 texture。

OpenGL 的 texture，里面也是保存的 bitmap，但它的坐标系统的命名方式不太一样：它的水平向右方向是 U 轴，竖直向上方向是 V 轴，然后它的 bitmap 保存个数也是行优先，但是从 (0, 0) 坐标开始保存像素，然后 U 和 V 的范围都是 0 到 1。

所以，如果我们创建一个 width*height 的单通道 texture，直接把上面的 bitmap 拷贝到 texture 内部，实际的效果大概是：

```
 V
 ^
 |
 C      D
 |
 |
 A------B--->U
```

上图中几个点的坐标以及对应的 bitmap 数组的下标：

- A 点：U = 0，V = 0，对应 bitmap 数组下标 `0`
- B 点：U = 1，V = 0，对应 bitmap 数组下标 `width-1`
- C 点：U = 0，V = 1，对应 bitmap 数组下标 `width*(height-1)`
- D 点：U = 1，V = 1，对应 bitmap 数组下标 `width*(height-1)+width-1`

所以在向 OpenGL 的 texture 保存 bitmap 的时候，相当于做了一个上下翻转，不过这没有关系，后续在指定三角形顶点的 U V 坐标的时候，保证对应关系即可。

## 逐个字符绘制

有了这个基础以后，就可以实现逐个字符绘制：提前把所有要用到的字符，从字体提取出对应的 Bitmap，每个字符对应到一个 Texture。然后要绘制文字的时候，逐个字符，用对应的 Texture，在想要绘制的位置上，绘制一个字符。为了实现这个目的，写一个简单的 Shader：

```c
// vertex shader
#version 320 es

in vec4 vertex; // xy is position, zw is its texture coordinates
out vec2 texCoors; // output texture coordinates
void main() {
  gl_Position.xy = vertex.xy;
  gl_Position.z = 0.0; // we don't care about depth now
  gl_Position.w = 1.0; // (x, y, z, w) corresponds to (x/w, y/w, z/w), so we set w = 1.0
  texCoords = vertex.zw;
}
// fragment shader
#version 320 es
precision lowp float;
in vec2 texCoords;
out vec4 color;
uniform sampler2D text;
void main() {
  float alpha = texture(text, texCoords).r;
  color = vec4(1.0, 1.0, 1.0, alpha);
}
```

在这里，我们给每个顶点设置四个属性，包在一个 vec4 中：

- xy：记录了这个顶点的坐标，x 和 y 范围都是 -1 到 1
- zw：记录了这个顶点的 texture 坐标 u 和 v，范围都是 0 到 1

vertex shader 只是简单地把这些信息传递到顶点的坐标和 fragment shader。fragment shader 做的事情是：

- 根据当前点经过插值出来的 u v 坐标，在 texture 中进行采样
- 由于这个 texture 只有单通道，所以它的第一个 channel 也就是 `texture(text, texCoords).r` 就代表了这个字体在这个位置的 alpha 值
- 然后把 alpha 值输出：`(1.0, 1.0, 1.0, alpha)`，即带有 alpha 的白色

在绘制文字之前，先绘制好背景色，然后通过设置 blending function：

```cpp
glEnable(GL_BLEND);
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);  
```

它使得 blending 采用如下的公式：

```cpp
final = src * src.alpha + dest * (1 - src.alpha);
```

这里 dest 就是绘制文本前的颜色，src 就是 fragment shader 输出的颜色，也就是 `(1.0, 1.0, 1.0, alpha)`。代入公式，就知道最终的结果是：

```cpp
final.r = 1 * alpha + dest.r * (1 - alpha);
final.g = 1 * alpha + dest.g * (1 - alpha);
final.b = 1 * alpha + dest.b * (1 - alpha);
```

也就是以 alpha 为不透明度，把白色和背景颜色进行了一次 blend。

如果要设置字体颜色，只需要修改一下 fragment shader：

```c
#version 320 es
precision lowp float;
in vec2 texCoords;
out vec4 color;
uniform sampler2D text;
uniform vec3 textColor;
void main() {
  float alpha = texture(text, texCoords).r;
  color = vec4(textColor, alpha);
}
```

此时 src 等于 `(textColor.r, textColor.g, textColor.b, alpha)`，经过融合后的结果为：

```cpp
final.r = textColor.r * alpha + dest.r * (1 - alpha);
final.g = textColor.g * alpha + dest.g * (1 - alpha);
final.b = textColor.b * alpha + dest.b * (1 - alpha);
```

即最终颜色，等于字体颜色和原来背景颜色，基于 bitmap 的 alpha 值的融合。

解决了颜色，接下来考虑如何设置顶点的信息。前面提到，得到的 bitmap 是一个矩形，而 OpenGL 绘图的基本元素是三角形，因此我们需要拆分成两个三角形来绘图，假如说要绘制一个矩形，它个四个顶点如下：

```
3-4
| |
1-2
```

如果确定左下角 3 这个顶点的坐标是 (xpos, ypos)，然后矩形的宽度是 w，高度是 h，考虑到 OpenGL 的坐标系也是向右 X 正方向，向上 Y 正方向，那么这四个顶点的坐标：

- 顶点 1：(xpos, ypos)
- 顶点 2：(xpos + w, ypos)
- 顶点 3：(xpos, ypos + h)
- 顶点 4：(xpos + w, ypos + h)

接下来考虑这些顶点对应的 uv 坐标。首先，我们知道这些顶点对应的 bitmap 的下标在哪里；然后我们又知道这些 bitmap 的下标对应的 uv 坐标，那就每个顶点找一次对应关系：

- 顶点 1：(xpos, ypos)，下标是 `width*(height-1)`，uv 坐标是 (0, 1)
- 顶点 2：(xpos + w, ypos)，下标是 `width*(height-1)+width-1`，uv 坐标是 (1, 1)
- 顶点 3：(xpos, ypos + h)，下标是 `0`，uv 坐标是 (0, 0)
- 顶点 4：(xpos + w, ypos + h)，下标是 `width-1`，uv 坐标是 (1, 0)

为了绘制这个矩形，绘制两个三角形，分别是 3->1->2 和 3->2->4，一共六个顶点的 (x, y, u, v) 信息就是：

- 3: (xpos    , ypos + h, 0, 0)
- 1: (xpos    , ypos    , 0, 1)
- 2: (xpos + w, ypos    , 1, 1)
- 3: (xpos    , ypos + h, 0, 0)
- 2: (xpos + w, ypos    , 1, 1)
- 4: (xpos + w, ypos + h, 1, 0)

把这些数传递给 vertex shader，就可以画出来这个字符了。

最后还有一个小细节：上述的 xpos 和 ypos 说的是矩形左下角的坐标，但是我们画图的时候，实际上期望的是把字符都画到同一条线上。也就是说，我们指定 origin 的 xy 坐标，然后根据每个字符的 bearingX 和 bearingY 来算出它的矩形的左下角的坐标 xpos 和 ypos：

- xpos = originX + bearingX
- ypos = originY + bearingY - height

至此就实现了逐个字符绘制需要的所有内容。这也是 [Text Rendering - Learn OpenGL](https://learnopengl.com/In-Practice/Text-Rendering) 这篇文章所讲的内容。

## Texture Atlas

上面这种逐字符绘制的方法比较简单，但是也有硬伤，比如每次绘制字符，都需要切换 texture，更新 buffer，再进行一次 glDrawArrays 进行绘制，效率比较低。所以一个想法是，把这些 bitmap 拼接起来，合成一个大的 texture，然后把每个字符在这个大的 texture 内的 uv 坐标保存下来。这样，可以一次性把所有字符的所有三角形都传递给 OpenGL，一次绘制完成，不涉及到 texture 的切换。这样效率会高很多。

具体到代码上，也就是分成两步：

- bitmap 的拼接，这一步比较灵活，理想情况下是构造一个比较紧密的排布，但也可以留一些空间，直接对齐到最大宽度/高度的整数倍网格上，然后进行 uv 坐标的计算
- 剩下的，就是在计算顶点信息的时候，用计算好的 uv 坐标，其中 left/right 对应 bitmap 左右两侧的 u 坐标，top/bottom 对应 bitmap 上下两侧的 v 坐标（注意 top 比 bottom 小，因为竖直方向是反的）：
    - 3: (xpos    , ypos + h, left , top   )
    - 1: (xpos    , ypos    , left , bottom)
    - 2: (xpos + w, ypos    , right, bottom)
    - 3: (xpos    , ypos + h, left , top   )
    - 2: (xpos + w, ypos    , right, bottom)
    - 4: (xpos + w, ypos + h, right, top   )

此外，在前面的 shader 代码里，字体颜色用的是 uniform，也就是每次调用只能用同一种颜色。修改的方法，就是把它也变成顶点的属性，从 vertex shader 直接传给 fragment shader，替代 uniform 变量。不过由于 vec4 已经放不下更多的维度了，所以需要另外开一个 attribute：

```c
// vertex shader
#version 320 es

in vec4 vertex; // xy is position, zw is its texture coordinates
in vec3 textColor;
out vec2 texCoors; // output texture coordinates
out vec3 fragTextColor; // send to fragment shader
void main() {
  gl_Position.xy = vertex.xy;
  gl_Position.z = 0.0; // we don't care about depth now
  gl_Position.w = 1.0; // (x, y, z, w) corresponds to (x/w, y/w, z/w), so we set w = 1.0
  texCoords = vertex.zw;
  fragTextColor = textColor;
}

// fragment shader
#version 320 es
precision lowp float;
in vec2 texCoords;
in vec3 fragTextColor;
out vec4 color;
uniform sampler2D text;
void main() {
  float alpha = texture(text, texCoords).r;
  color = vec4(fragTextColor, alpha);
}
```

## 背景和光标绘制

接下来回到终端模拟器，它除了绘制字符，还需要绘制背景颜色和光标。前面在绘制字符的时候，只把 bounding box 绘制了出来，那么剩下的空白部分是没有绘制的。但是终端里，每一个位置的背景颜色都可能不同，所以还需要给每个位置绘制对应的背景颜色。这里有两种做法：

第一种做法是，把前面每个字符的 bitmap 扩展到终端里一个固定的位置的大小，这样每次绘制的矩形，就是完整的一个位置的区域，这个时候再去绘制背景颜色，就比较容易了：修改 vertex shader 和 fragment shader，在内部进行一次 blend：`color = vec4(fragTextColor * alpha + fragBackgroundColor * (1.0 - alpha), 1.0)`，相当于是丢掉了 OpenGL 的 blend function，自己完成了前景和后景的绘制。

但这个方法有个问题：并非所有的字符的 bitmap 都可以放到一个固定大小的矩形里的。有一些特殊字符，要么长的太高，要么在很下面的位置。后续可能还有更复杂的需求，比如 CJK 和 Emoji，那么字符的宽度又不一样了。所以这个时候导出了第二种做法：

- 第一轮，先绘制出终端每个位置的背景颜色
- 第二轮，再绘制出每个位置的字符，和背景进行融合

这时候 shader 没法自己做 blend，所以这考虑怎么用 blend function 来实现这个 blend 的计算。首先，要考虑我们最终需要的结果是：

```cpp
final.r = textColor.r * alpha + dest.r * (1 - alpha);
final.g = textColor.g * alpha + dest.g * (1 - alpha);
final.b = textColor.b * alpha + dest.b * (1 - alpha);
final.a = textColor.a * alpha + dest.a * (1 - alpha);
```

由于是 OpenGL 做的 blending，我们需要用 OpenGL 自带的 blending mode 来实现上述公式。OpenGL 可以指定 RGB 的 source 和 dest 的 blending 方式，比如：

- GL_ONE：乘以 1 的系数
- GL_ONE_MINUS_SRC_ALPHA：乘以 (1 - source.a) 的系数

根据这个，就可以想到，设置 `source = textColor * alpha`，设置 source 采用 GL_ONE 方式，dest 采用 GL_ONE_MINUS_SRC_ALPHA 模式，那么 OpenGL 负责剩下的 blending 工作 `final = source * 1 + dest * (1 - source.a)`：

```cpp
final.r = source.r * 1.0 + dest.r * (1 - source.a) = textColor.r * alpha + dest.r * (1 - alpha);
final.g = source.g * 1.0 + dest.g * (1 - source.a) = textColor.g * alpha + dest.g * (1 - alpha);
final.b = source.b * 1.0 + dest.b * (1 - source.a) = textColor.b * alpha + dest.b * (1 - alpha);
final.a = source.a * 1.0 + dest.a * (1 - source.a) = textColor.a * alpha + dest.a * (1 - alpha);
```

正好实现了想要的计算公式。这个方法来自于 [Text Rendering - WebRender](https://github.com/servo/webrender/blob/main/webrender/doc/text-rendering.md)。有了这个推导后，就可以分两轮，完成终端里前后景的绘制了。

目前 [Termony](https://github.com/jiegec/Termony) 用的就是这种实现方法：

- 首先把不同字重的各种字符的 bitmap 拼在一起，放在一个 texture 内部
- 使用两阶段绘制，第一阶段

注：如果不考虑 textColor 的 alpha 值，也可以在 source 使用 GL_SRC_ALPHA，此时设置 `source = vec4(textColor.rgb, alpha)`，这样 `final.r = source.r * source.a + dest.r * (1 - source.a) = textColor.r * alpha + dest.r * (1 - alpha)`，结果是一样的，不过这个时候 final 的 alpha 值等于 `source.a * source.a + dest.a * (1 - source.a)` 是 alpha 和 dest.a 经过 blend 以后的结果，如果不用它就无所谓。

## 参考

- [Text Rendering - Learn OpenGL](https://learnopengl.com/In-Practice/Text-Rendering)
- [Text Rendering - WebRender](https://github.com/servo/webrender/blob/main/webrender/doc/text-rendering.md)
