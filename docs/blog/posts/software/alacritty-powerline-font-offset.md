---
layout: post
date: 2019-01-10
tags: [alacritty,font]
categories:
    - software
title: 调整 Alacritty 的 Powerline 字体显示偏移
---

今天体验了一下 Alacritty，以前一直在用 iTerm2，但是它的高级功能我都没用到。于是现在用了下 Alacritty，把 Solarized Dark 配置了，发现 Inconsolata for Powerline 字体显示有点偏差，于是调整了一下：

```yaml
# Font configuration (changes require restart)
font:
  # Normal (roman) font face
  normal:
    family: Inconsolata for Powerline
    # The `style` can be specified to pick a specific face.
    #style: Regular

  # Bold font face
  bold:
    family: Inconsolata for Powerline
    # The `style` can be specified to pick a specific face.
    #style: Bold

  # Italic font face
  italic:
    family: Inconsolata for Powerline
    # The `style` can be specified to pick a specific face.
    #style: Italic

  # Point size
  size: 18.0

  # Offset is the extra space around each character. `offset.y` can be thought of
  # as modifying the line spacing, and `offset.x` as modifying the letter spacing.
  offset:
    x: 0
    y: 0

  # Glyph offset determines the locations of the glyphs within their cells with
  # the default being at the bottom. Increasing `x` moves the glyph to the right,
  # increasing `y` moves the glyph upwards.
  glyph_offset:
    x: 0
    y: 3

```

主要是这里的 glyph_offset 设置为 3（2 也可以，我更喜欢 3） ，这样箭头就基本对齐了不会突出来。

然后按照官方 Wiki，配置了 Solarized Dark 配色：

```yaml
## Colors (Solarized Dark)
colors:
  # Default colors
  primary:
    background: '0x002b36' # base03
    foreground: '0x839496' # base0

  # Normal colors
  normal:
    black:   '0x073642' # base02
    red:     '0xdc322f' # red
    green:   '0x859900' # green
    yellow:  '0xb58900' # yellow
    blue:    '0x268bd2' # blue
    magenta: '0xd33682' # magenta
    cyan:    '0x2aa198' # cyan
    white:   '0xeee8d5' # base2

  # Bright colors
  bright:
    black:   '0x002b36' # base03
    red:     '0xcb4b16' # orange
    green:   '0x586e75' # base01
    yellow:  '0x657b83' # base00
    blue:    '0x839496' # base0
    magenta: '0x6c71c4' # violet
    cyan:    '0x93a1a1' # base1
    white:   '0xfdf6e3' # base3

```

真香