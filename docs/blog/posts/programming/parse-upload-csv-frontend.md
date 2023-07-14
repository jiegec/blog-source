---
layout: post
date: 2019-07-17
tags: [js,frontend,iconv,encoding,gbk]
category: programming
title: 前端解析上传的 CSV
---

之前做过一个在前端解析上传的 CSV 的功能，但是只能支持部分的 encoding，遇到 gbk 就傻眼了。一番研究以后，找到了比较科学的方案：

```javascript
import * as Chardet from 'chardet';
import * as Iconv from 'iconv-lite';

const reader = new FileReader();
reader.onload = (e) => {
  const data = e.target.result;
  const view = Buffer.from(data);
  // detect encoding and convert
  const encoding = Chardet.detect(view);
  const result = Iconv.decode(view, encoding);
  const csvData = Papa.parse(result).data;
  // do anything with it
};

reader.readAsArrayBuffer(blob_here);
```

依赖了两个库：`chardet` 和 `iconv-lite` ，测试了一下，解析 UTF-8 GBK UTF-16BE 都没问题。

P.S. 在生成 csv 的时候，也会出现 Excel 打开后乱码的问题，一开始我以为需要转 UTF-16 然后再添加 BOM Mark，后来发现只要在最前面加上 0xEF 0xBB 0xFB（UTF-8 编码下的 BOM Mark）即可。
