---
layout: post
date: 2019-09-28
tags: [nginx,rtmp,hls,obs]
category: software
title: 用 Nginx 作为 RTMP 服务器并提供直播服务
---

Nginx 除了可以做 HTTP 服务器以外，还可以做 RTMP 服务器，同时转成 HLS 再提供给用户，这样可以实现一个直播的服务器，用 OBS 推上来即可。

首先要安装 nginx-rtmp-server 模块，很多的发行版都已经包含了，它的主页是 https://github.com/arut/nginx-rtmp-module，下面很多内容也是来自于它的教程中。

接着，配置 Nginx，在 nginx.conf 的顶层中添加如下的配置：

```
rtmp {
    server {
            listen 1935;
            chunk_size 4096;

            application live {
                    live on;
                    record off;

                    hls on;
                    hls_path /path/to/save/hls;
                    hls_fragment 1s;
                    hls_playlist_length 10s;
            }

    }
}
```

这里表示 Nginx 要在 1935 监听一个 RTMP 服务器，然后把 live 下的视频切成片然后存在目录下，提供一个 m3u8 文件以供播放器使用。这里的参数都可以按照实际需求进行调整。这时候应该可以看到 nginx 正确监听 1935 端口，这是 rtmp 的默认端口。

接着，需要在一个 HTTP server 路径下把 HLS serve 出去：

```
        location /hls {
            # Serve HLS fragments
            types {
                application/vnd.apple.mpegurl m3u8;
                video/mp2t ts;
            }
            root /path/to/save/hls;
            add_header Cache-Control no-cache;
        }
```

这时候，如果你用 rtmp 推一个流（比如用 OBS）到 rtmp://SERVER_IP/live/SOMETHING，那么在对应的目录下会看到 SOMETHING 开头的一系列文件；用播放器打开 http://SERVER_IP/hls/SOMETHING.m3u8 就可以看到直播的视频流了。

如果要直接在浏览器里播放 HLS，需要用 Flowplayer，直接参考官方的例子即可：

```javascript
<script>
var player = flowplayer("#player", {
        clip: {
                sources: [
                {
                        type: "application/x-mpegurl",
                        src: "https://SERVER_IP/hls/SOMETHING.m3u8"
                }]
        },
        autoplay: true,
        loop: true,
        live: true
});
</script>
```

上面的各个路径可以按照实际需求改动。