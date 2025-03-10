---
layout: post
date: 2025-02-04
tags: [feishu,calendar]
categories:
    - software
---

# 导出飞书日历为 iCalendar 格式

## 背景

之前用了一段时间飞书日历，想要把日历里的事件导出来备份，但是发现飞书自己的导出功能太弱，因此参考 [从飞书导出日历到 Fastmail - Xuanwo's Blog](https://xuanwo.io/reports/2023-35/) 进行了导出的尝试。

<!-- more -->

## 导出方法

上面提到的文章，是通过 CalDAV 的方式进行的日历同步。因此我第一步也是配置飞书的 CalDAV 服务：

1. 打开飞书客户端
2. 点击设置
3. 点击日历
4. 设置 CalDAV 同步

按照界面所示，配置 CalDAV 同步，就可以得到用于 CalDAV 的域名、用户名和密码了。如果只是要订阅，那么到这一步，就可以直接用 CalDAV 客户端来同步了。但我想进一步得到 iCalendar 格式的日历文件。

于是我参考了上述文章的评论区的做法：

```
@jason5ng32 jason5ng32
Oct 28, 2024

分享一下我的方法：

1. 在服务器上安装 vdirsyncer ，这个工具可以同步 CalDAV 的内容，在同步设置里，不需要先找到 UUID，可以直接用飞书提供的 URL。
2. 写一个 Python 脚本，将 vdirsyncer 同步的内容合并成单一的 ics 文件。
3. 将 ics 文件放到一个地址稍微复杂一点的 http 目录里，可以外部访问。
4. 写一个 run.sh 脚本，通过 crontab 每 10 分钟执行一次 vdirsyncer 同步和日历文件合成。
```

也就是说，用 vdirsyncer 把日历同步到本地，再转换为 iCalendar 格式的日历文件。参考 [vdirsyncer](https://vdirsyncer.pimutils.org/en/stable/installation.html#installation) 文档，这件事情并不复杂：

1. 按照 vdirsyncer: `pip3 install vdirsyncer`
2. 编辑 `~/.vdirsyncer/config`，填入在飞书处得到的用户密码：
    ```
    [general]
    status_path = "~/.vdirsyncer/status/"

    [pair my_contacts]
    a = "my_contacts_local"
    b = "my_contacts_remote"
    collections = ["from a", "from b"]

    [storage my_contacts_local]
    type = "filesystem"
    path = "~/.contacts/"
    fileext = ".ics"

    [storage my_contacts_remote]
    type = "caldav"

    url = "https://caldav.feishu.cn"
    username = "REDACTED"
    password = "REDACTED"
    ```
3. 配置好以后，进行同步：`vdirsyncer discover && vdirsyncer sync`

此时在 `~/.contacts` 目录下，已经能看到很多个 ics 文件了，每个 ics 文件对应了日历中的一个事件。实际上，这些文件就已经是 iCalendar 格式了，只不过每个文件只有一个事件。

为了让一个 `.ics` 文件包括日历的所有事件，写了一个脚本，实际上就是处理每个 ics 文件，去掉每个文件开头结尾的 `BEGIN:VCALENDAR` 和 `END:VCALENDAR`，把中间的部分拼起来，最后再加上开头结尾：

```python
import sys

all_lines = []
all_lines += ["BEGIN:VCALENDAR"]
for f in sys.argv[1:]:
	content = open(f).read().strip()
	lines = content.splitlines()
	all_lines += lines[1:-1]
all_lines += ["END:VCALENDAR"]
print("\n".join(all_lines))
```

运行上述脚本：`python3 dump.py ~/.contacts/*/*.ics > dump.ics`，这样得到的 `.ics` 文件就可以直接导入到日历软件了。

UPDATE: 我在之前写的飞书文档备份工具 [feishu-backup](https://github.com/jiegec/feishu-backup) 的基础上，添加了飞书日历的导出功能，把原始的 json 保存下来，并转换得到 iCalendar 格式的 `.ics` 文件。

## 导出 iCloud 国区的日历和联系人

除了导出飞书的日历，也可以用类似的方法导出 iCloud 国区的日历：把 url 改成 `"https://caldav.icloud.com.cn"`，在 Apple ID 上生成 App 密码，填入上面的 password，再把邮箱写到 username 即可。

更进一步，也可以导出 iCloud 国区的联系人：

1. 把配置中 `fileext = ".ics"` 改成 `fileext = ".vcf"`，因为联系人的格式是 [vCard](https://en.wikipedia.org/wiki/VCard)，其文件名后缀是 `.vcf`
2. 把 `type = "caldav"` 改成 `type = "carddav"`，把 `url = "https://caldav.icloud.com.cn` 改成 `url = "https://contacts.icloud.com.cn"`，表示同步联系人而不是日历

如果既要同步日历，又要同步联系人，或者需要同步来自不同来源的日历，建议把 status 和 storage local 放到不同的目录下，避免出现冲突。

