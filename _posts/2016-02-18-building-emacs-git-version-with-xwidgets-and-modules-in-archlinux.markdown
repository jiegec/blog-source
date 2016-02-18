---
layout: post
date: 2016-02-18 12:37:52 +0800
tags: [emacs,git,archlinux]
category: programming
---

First you need to install these packages:

{% highlight shell %}
sudo pacman -S git autoconf automake gtk3 webkitgtk
git clone --depth 1 https://github.com/emacs-mirror/emacs.git (or git protocol if you like)
cd emacs
./autogen.sh all
./configure --with-xwidgets --with-x --with-x-toolkit=gtk3 --with-modules
make
cd lisp
make autoloads
make
make
make
{% endhighlight %}

Until you got everything ok.

Then you can just:
{% highlight shell %}
cd src
./emacs
{% endhighlight %}

And then, M-x webkit-browse-url RET

What's more, you can use ssh and X11 Forward to show Emacs in Mac OS X! Cool!