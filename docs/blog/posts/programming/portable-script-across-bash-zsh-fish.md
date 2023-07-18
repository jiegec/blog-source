---
layout: post
date: 2023-07-18
tags: [shell,bash,zsh,fish]
categories:
    - programming
---

# 写一个 bash zsh 和 fish 都能跑的脚本

## 背景

bash 和 zsh 都实现了 POSIX shell 标准，因此写脚本的时候，比较容易兼容这两种常见的 shell。但现在 fish 也很流行，而 fish 不符合 POSIX shell 标准，很多地方语法多不兼容，能否写一个脚本，可以用 bash，zsh 和 fish 跑？

```shell
# The following commands should work
bash test.sh
zsh test.sh
fish test.sh
```

<!-- more -->

## 简单版本

简单版本是，给不同的 shell 写不同的版本，然后写一个小的通用版本，负责执行不同的版本：

```shell
type status >/dev/null 2>/dev/null && exec fish ./code-fish.sh
type zstyle >/dev/null 2>/dev/null && exec zsh ./code-zsh.sh
exec bash ./code-bash.sh
```

原理是利用 `type` 内置命令判断是否存在某个命令：`status` 是 `fish` 特有的，`zstyle` 是 `zsh` 特有的，如果判断成功，就去执行相应的脚本。因为用了 `exec`，所以如果执行到 `exec`，后面的代码就不会执行了。

## 复杂版本

那么，如果头铁，想要用 `if-then-else` 来实现呢？首先，POSIX shell 中的写法是：

```shell
if expression
then
        # do something
else
        # do something
fi
```

fish shell 的写法是：

```shell
if expression
    # do something
else
    # do something
end
```

这就出现了矛盾：POSIX shell 需要 `then` 和 `fi`，fish shell 需要的是 `end`。怎么办呢？

shell 里面有一个特别的命令：`alias`，可以给命令起别名。如果可以让 `then` 和 `fi` 在 fish 里面变成 no-op，让 `end` 在 bash 里变成 no-op，那是不是就好了？

按照这个思路，可以写出下面的脚本：

```shell
alias then="true"

if status current-command 2>/dev/null | grep -q fish
then
    echo "I'm in fish"
else
    echo "I'm in bash"
fi
exit 0
end
```

这里利用到一点：Bash 看到 `then` 的时候，是不会管 alias 的，所以对它来说，这个 alias 不生效。然后就会正常走 else 分支，然后在走到 `end` 之前就退出了。在 fish 眼里，fish 不认识 `then`，所以它就会应用上 alias，变成一个 `true` 命令，所以在 fish 眼里，看到的是下面的代码：

```shell
if status current-command 2>/dev/null | grep -q fish
    true
    echo "I'm in fish"
else
    echo "I'm in bash"
    fi
    exit 0
end
```

这样就解决了 bash 和 fish 的 if 语法不兼容的问题。但是，如果在 zsh 里跑，就会遇到错误：

```
test-bash-fish.sh:6: parse error near `else'
```

这说明当 zsh 解析到 `then` 的时候，它会展开为 `true`，于是就出现了语法错误。可见虽然 bash 和 zsh 都实现了 POSIX shell，但是在 alias 的展开时机上实现并不一样。怎么办呢？alias 的反义词是 unalias，可以把它取消掉：

```shell
alias then="true"
type unalias >/dev/null 2>&1 && unalias then

if status current-command 2>/dev/null | grep -q fish
then
    echo "I'm in fish"
else
    type zstyle >/dev/null 2>&1 && echo "I'm in zsh" || echo "I'm in bash"
fi
exit 0
end
```

这里再次利用了 `type` 命令来判断 `unalias` 是否存在。搞了一大通，才实现了三种 shell 都可以跑的 if else 语句。
