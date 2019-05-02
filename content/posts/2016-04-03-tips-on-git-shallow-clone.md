---
layout: post
date: 2016-04-03 14:38:09 +0800
tags: [git,clone,tips]
category: programming
---

Just learned a new tip on git shallow clone. As you know, some repository are really really large, such as emacs and linux. Cloning is slow and unstable. And there is no way to pause and resume a git clone. So I use shallow clone to clone them. But what if I want to clone other branches?


From here: http://stackoverflow.com/a/27393574/2148614

```
git remote set-branches origin '*'
```