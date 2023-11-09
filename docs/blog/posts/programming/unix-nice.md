---
layout: post
date: 2016-02-24
tags: [unix,nice,process,twitter]
category:
    - programming
---

I just saw this interesting tweet:
```
Unix系统的每个进程，都有一个nice值。这个值越大，优先级越低。然后，还有一个nice命令，每运行一次，指定进程的nice值＋10。它的意思就是做人要nice，把更多的CPU时间留给别人。nice值越高，你留给自己的份额就越少。
```

From [here](https://twitter.com/ruanyf/status/702382281990791172)by [@ruanyf](https://twitter.com/ruanyf).

And i didn't known that until now. Cool! The name 'nice' is nice, too.

Don't worry if you can't read Chinese. See also [here](http://www.thegeekstuff.com/2013/08/nice-renice-command-examples/) and [here](https://en.wikipedia.org/wiki/Nice_(Unix)). 