---
layout: post
date: 2023-11-26
tags: [mkdocs,mkdocsmaterial,markdown,instant,spa]
categories:
    - software
---

# mkdocs-material 的 Instant Navigation 功能坑点

## 背景

mkdocs-material 支持 [Instant Navigation](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#instant-loading)：启用了以后，在网页里点击其他页面的时候，它会用类似 SPA 的方法，去 fetch 新的网页，然后原地替换，而不是让浏览器跳转过去，可以提升用户体验。

但是在用这个功能的时候，会发现其实并不是那么简单。。。

<!-- more -->

## Sitemap

使用 Instant Navigation 遇到的第一个问题是：本地 `mkdocs serve` 的时候可以工作，而线上 `mkdocs build` 再用 nginx 部署的时候，就不工作了，这是为啥呢？

阅读 [instant/index.ts](https://github.com/squidfunk/mkdocs-material/blob/bf6e66bddd6cc94ab4fd9becf9fb9d9a2d33f6e2/src/templates/assets/javascripts/integrations/instant/index.ts) 源代码，发现它会检查点击的链接是否在 sitemap 中出现：

```typescript
        // Skip, if URL is not included in the sitemap - this could be the case
        // when linking between versions or languages, or to another page that
        // the author included as part of the build, but that is not managed by
        // MkDocs. In that case we must not continue with instant navigation.
        if (!sitemap.includes(`${url}`))
          return EMPTY
```

但是观察了一下生成的 `site` 目录，发现下面的 sitemap.xml 是空的。查了一下，发现需要配置 `site_url` 才会生成 sitemap.xml 的内容。这也可以理解，毕竟 sitemap.xml 里面写得是绝对 URL。

添加 `site_url` 以后，终于生成了 sitemap，但是 instant navigation 依然不工作：用 Chrome Developer Tools 调试，发现代码读取出来的 sitemap 依然为空。阅读[代码](https://github.com/squidfunk/mkdocs-material/blob/bf6e66bddd6cc94ab4fd9becf9fb9d9a2d33f6e2/src/templates/assets/javascripts/integrations/sitemap/index.ts#L91)，发现：

```typescript
  const cached = __md_get<Sitemap>("__sitemap", sessionStorage, base)
  if (cached) {
    return of(cached)
  } else {
    const config = configuration()
    return requestXML(new URL("sitemap.xml", base || config.base))
      .pipe(
        map(sitemap => preprocess(getElements("loc", sitemap)
          .map(node => node.textContent!)
        )),
        catchError(() => EMPTY), // @todo refactor instant loading
        defaultIfEmpty([]),
        tap(sitemap => __md_set("__sitemap", sitemap, sessionStorage, base))
      )
  }
```

代码里缓存了 sitemap 的内容到 session storage 中，进入 developer tools，从 session storage 中删掉 sitemap，就可以发现它能获取到正确的 sitemap，instant navigation 也工作了。

## Wavedrom

Instant Navigation 虽然工作了，但是点击用了 WaveDrom 的网页后，会发现里面的 WaveDrom 代码没有被渲染出来，并且 Developer Tools 会报错。

阅读代码，发现 Instant Navigation 会重新运行新页面上内嵌的 `<script>` 标签，然而 WaveDrom 也正好会使用 `<script>` 标签来写它的 WaveJSON 配置，只不过是 `<script type="WaveDrom">`，所以不会被浏览器执行。

然而 Instant Navigation 重新运行的时候，[没有考虑到这种情况](https://github.com/squidfunk/mkdocs-material/blob/bf6e66bddd6cc94ab4fd9becf9fb9d9a2d33f6e2/src/templates/assets/javascripts/integrations/instant/index.ts#L355-L357)：

```typescript
              const script = next.createElement("script")
              // ...
              script.textContent = el.textContent
              el.replaceWith(script)
```

它创建了一个新的 `<script>` tag，从旧的复制了 textContent，但是没有复制 type。因此浏览器会把内容当成 JavaScript 去执行，自然就失败了。

这时候怎么办呢？可以有以下几种解决办法：

1. 修改 mkdocs-material 代码，让它把 type 字段也继承下来
2. 让 wavedrom 用其他 tag，因为 wavedrom 只会检查 type 是否等于 wavedrom，不会检查是什么 tag
3. 提前渲染 wavedrom 到 svg，直接内嵌 svg

最后在自己 fork 的 [mkdocs-wavedrom-plugin](https://github.com/jiegec/mkdocs-wavedrom-plugin) 中用了第三种方法。如果读者有兴趣，可以给 mkdocs-material 提交 pr。

此外，前两种方法还需要修改 WaveDrom.ProcessAll 的调用方法：模仿 mkdocs-material 的 MathJax 渲染方法，去调用 `document$.subscribe`：

```javascript
document$.subscribe(() => {
  WaveDrom.ProcessAll();
})
```

这样 Instant Navigation 在“重新加载”页面的时候，才会重新调用 `WaveDrom.ProcessAll`。

## Math

和 WaveDrom 类似，Arithmatex 扩展默认情况下，也会给数学公式生成 `<script>` tag，只不过这次是 [MathJax 的旧格式](https://github.com/facelessuser/pymdown-extensions/blob/main/docs/src/markdown/extensions/arithmatex.md#mathjax-output-format)：

```html
<script type="math/tex">
  1234
</script>
```

这个问题的解决办法在比较新的 mkdocs-material 文档里已经[给出](https://squidfunk.github.io/mkdocs-material/setup/extensions/python-markdown-extensions/#arithmatex)：

```yaml
# in mkdocs.yaml
markdown_extensions:
  - pymdownx.arithmatex:
      generic: true

extra_javascript:
  - javascripts/mathjax.js
  - https://polyfill.io/v3/polyfill.min.js?features=es6
  - https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js
```

```javascript
// in docs/javascripts/mathjax.js
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};

document$.subscribe(() => {
  MathJax.typesetPromise()
})
```

注意到熟悉的 `document$`，这也是它可以在 Instant Navigation 下正常工作的原因。

## 小结

因此，为了让 mkdocs-material 的 Instant Navigation 功能工作，你需要保证：

1. 设置 site_url，保证 sitemap 正常生成
2. 保证代码中不会出现非 javascript 的 `<script>` tag，如 wavedrom 和 math/tex
3. 如果涉及到需要用 javascript 动态渲染的内容，需要在 `document$` 上注册回调以重新渲染新页面
