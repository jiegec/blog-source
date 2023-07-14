---
layout: post
date: 2016-07-23
tags: [git, compression]
categories:
    - programming
---

I have found a good way to track changes in .gz files:
Add these to ~/.gitconfig:

```config
[core]
  attributesFile = ~/.gitattributes
[diff "zip"]
  textconv = unzip -p
  binary = true
[diff "gz"]
  textconv = gzcat
  binary = true
[diff "bz2"]
  textconv = bzcat
  binary = true
[diff "xz"]
  textconv = xzcat
  binary = true
[diff "tar"]
  textconv = tar -O -xf
  binary = true
[diff "tar-bz2"]
  textconv = tar -O -xjf
  binary = true
[diff "tar-gz"]
  textconv = tar -O -xzf
  binary = true
[diff "tar-xz"]
  textconv = tar -O -xJf
  binary = true

[diff "odf"]
  textconv = odt2txt
[diff "pdf"]
  textconv = pdfinfo
[diff "bin"]
  textconv = hexdump -v -C
```

And these to ~/.gitattributes:

```config
*.tar diff=tar
*.tar.bz2 diff=tar-bz2
*.tar.gz diff=tar-gz
*.tar.xz diff=tar-xz
*.bz2 diff=bz2
*.gz diff=gz
*.zip diff=zip
*.xz diff=xz

*.odf diff=odf
*.odt diff=odf
*.odp diff=odf
*.pdf diff=pdf
*.exe diff=bin
*.png diff=bin
*.jpg diff=bin

```

And then you can `git diff` for .gz files.

Codes are adapted from https://gist.github.com/RsrchBoy/11197048
and https://git.wiki.kernel.org/index.php/GitTips#Getting_a_plain-text_diff and https://gist.github.com/kbaird/2654115.
