---
layout: post
date: 2017-12-02 22:16:07 +0800
tag: [nginx,source code,TUNA]
category: programming
---

今晚参加了 Tunight ，会长给我们讲了 Nginx 的一些内部运作的机制和原理。中间的时候，会长展示的代码中用到了线程池方面的一些函数，但是大多地方只有调用 `ngx_pcalloc` 而没有看到相应的对象释放的过程，于是在演示的最后，会长应大家要求对 Nginx 魔幻的线程池实现做了现场代码分析。

在分析的中途遇到了很多坑，最后才终于理清了内存池的工作原理。这里直接解释结论吧。以下代码均摘自 Nginx 1.13.7 ，代码都可以在官方仓库找到。

首先分析一下创建一个内存池的函数：
``` c
ngx_pool_t *
ngx_create_pool(size_t size, ngx_log_t *log)
{
    ngx_pool_t  *p;

    p = ngx_memalign(NGX_POOL_ALIGNMENT, size, log);
    if (p == NULL) {
        return NULL;
    }

    p->d.last = (u_char *) p + sizeof(ngx_pool_t);
    p->d.end = (u_char *) p + size;
    p->d.next = NULL;
    p->d.failed = 0;

    size = size - sizeof(ngx_pool_t);
    p->max = (size < NGX_MAX_ALLOC_FROM_POOL) ? size : NGX_MAX_ALLOC_FROM_POOL;

    p->current = p;
    p->chain = NULL;
    p->large = NULL;
    p->cleanup = NULL;
    p->log = log;

    return p;
}
```

现在开始分段分析这个函数：在这里，一个内存池用一个 `ngx_pool_t (aka struct ngx_pool_s)` 类型的数据进行包装，所有的关于内存池的操作都基于相应的内存池对象。 `ngx_log_t` 表示输出信息的对象，与内存池无关，后面也不会讨论它。

``` c
    p = ngx_memalign(NGX_POOL_ALIGNMENT, size, log);
    if (p == NULL) {
        return NULL;
    }

    p->d.last = (u_char *) p + sizeof(ngx_pool_t);
    p->d.end = (u_char *) p + size;
    p->d.next = NULL;
    p->d.failed = 0;
```

这里通过调用 `ngx_memalign` 分配一段（能对齐就对齐，不能对齐就放弃的）以 size 为大小的内存，做为这个内存池第一个块的内存，这个块的头是完整的，其中 `p->d.last` 和 `p->d.end` 分别表示可用于分配对象的内存段的开始和结束，在用 `p->d.next` 连接起来的链表中，每个链表实际上只有 `d` 是存储了数据，后面的各个域都不再使用。这里的 `p->d.failed` 涉及到链表的优化，在以后会接触到。

``` c
    size = size - sizeof(ngx_pool_t);
    p->max = (size < NGX_MAX_ALLOC_FROM_POOL) ? size : NGX_MAX_ALLOC_FROM_POOL;

    p->current = p;
    p->chain = NULL;
    p->large = NULL;
    p->cleanup = NULL;
    p->log = log;

    return p;
```

这里的 `size` 计算出实际用于对象分配的内存大小， `p->max` 存储了当前这个块最大能容纳的对象的大小， `p->current` 会和上面的 `p->d.failed` 合在一起对链表进行优化。 `p->chain` 与其他功能关系较密切，不会在本文中展开，而 `p->cleanup` 允许外部注册一些清理函数，实现起来并不难。

接下来，由于 `ngx_pnalloc` 和 `ngx_pcalloc` 都和 `ngx_palloc` 相近，这里只对 `ngx_palloc` 进行分析：

``` c
void *
ngx_palloc(ngx_pool_t *pool, size_t size)
{
#if !(NGX_DEBUG_PALLOC)
    if (size <= pool->max) {
        return ngx_palloc_small(pool, size, 1);
    }
#endif

    return ngx_palloc_large(pool, size);
}
```

这里分了两种情况，如果要分配的内存大于一个块的最大值，那么这段内存必须要单独分配单独维护，所以调用了 `ngx_palloc_large` ，下面对其分析：

``` c
static void *
ngx_palloc_large(ngx_pool_t *pool, size_t size)
{
    void              *p;
    ngx_uint_t         n;
    ngx_pool_large_t  *large;

    p = ngx_alloc(size, pool->log);
    if (p == NULL) {
        return NULL;
    }

    n = 0;

    for (large = pool->large; large; large = large->next) {
        if (large->alloc == NULL) {
            large->alloc = p;
            return p;
        }

        if (n++ > 3) {
            break;
        }
    }

    large = ngx_palloc_small(pool, sizeof(ngx_pool_large_t), 1);
    if (large == NULL) {
        ngx_free(p);
        return NULL;
    }

    large->alloc = p;
    large->next = pool->large;
    pool->large = large;

    return p;
}
```

这里的 `ngx_alloc` 就是对 `malloc` 的简单封装，直接分配一段内存，然后向 `pool->large` 中以 `ngx_pool_large_t` 组成的链表中插入。这里有一个小优化：因为 `ngx_pool_large_t` 本身也要占用内存，为了复用已经被释放的 `ngx_pool_large_t` ，尝试链表的前几项，如果几项中都没有空的位置，因为 `ngx_pool_large_t` 本身是一个很小的对象，自然可以复用自己在内存池中分配对象的方法 `ngx_palloc_small` ，然后把它加入到 `pool->large` 的链表的第一向前。如果很大的内存都在分配后很快释放，这种方法可以复用很多的 `ngx_pool_large_t` 。

接下来分析 `ngx_palloc_small` ：

``` c
static ngx_inline void *
ngx_palloc_small(ngx_pool_t *pool, size_t size, ngx_uint_t align)
{
    u_char      *m;
    ngx_pool_t  *p;

    p = pool->current;

    do {
        m = p->d.last;

        if (align) {
            m = ngx_align_ptr(m, NGX_ALIGNMENT);
        }

        if ((size_t) (p->d.end - m) >= size) {
            p->d.last = m + size;

            return m;
        }

        p = p->d.next;

    } while (p);

    return ngx_palloc_block(pool, size);
}
```

首先，从 `pool->current` 遍历（这样做的原因下面会提到）已有的各个块，寻找有没有哪个块能容纳下现在需要的大小，如果能就可以调整 `p->d.last` 返回，否则就分配一个新的块到内存池中，再从新的块中分配需要的大小的内存。需要一提的是，在设计中，小的对象是随着整个内存池的销毁而被一起释放的，不会在中途被释放，而大的对象尽量要用完即释放。接下来分析 `ngx_palloc_block` ：

``` c
static void *
ngx_palloc_block(ngx_pool_t *pool, size_t size)
{
    u_char      *m;
    size_t       psize;
    ngx_pool_t  *p, *new;

    psize = (size_t) (pool->d.end - (u_char *) pool);

    m = ngx_memalign(NGX_POOL_ALIGNMENT, psize, pool->log);
    if (m == NULL) {
        return NULL;
    }

    new = (ngx_pool_t *) m;

    new->d.end = m + psize;
    new->d.next = NULL;
    new->d.failed = 0;

    m += sizeof(ngx_pool_data_t);
    m = ngx_align_ptr(m, NGX_ALIGNMENT);
    new->d.last = m + size;

    for (p = pool->current; p->d.next; p = p->d.next) {
        if (p->d.failed++ > 4) {
            pool->current = p->d.next;
        }
    }

    p->d.next = new;

    return m;
}
```

为了节省内存，结构体中并没有记录实际分配的内存块的大小，于是根据第一个块的大小分配当前的块，虽然这里用的也是一个类型为 `ngx_pool_t` 结构体，实际上只用到了 `new->d` 中的内容维护块组成的链表和块内的分配情况。然后从 `pool->current` 开始找块的链表的结尾，找到节尾后把当前的块加到结尾的后面，然后把刚才需要分配的小对象的地址返回。与此同时，由于调用这个函数的时候，一定是当前的对象在已有的从 `pool->current` 开始的块中都放不下了，我们给这些块的 `p->d.failed` 进行自增，意思是说这个块在分配新的对象的时候又一次放不下了，如果放不下的次数比较多，我们可以认为这个块已经装得比较满了，那么，我们把 `pool->current` 设为它的后继，以后在分配新的对象的时候就会自动跳过这些比较满的块，从而提高了效率。

``` c
ngx_int_t
ngx_pfree(ngx_pool_t *pool, void *p)
{
    ngx_pool_large_t  *l;

    for (l = pool->large; l; l = l->next) {
        if (p == l->alloc) {
            ngx_log_debug1(NGX_LOG_DEBUG_ALLOC, pool->log, 0,
                           "free: %p", l->alloc);
            ngx_free(l->alloc);
            l->alloc = NULL;

            return NGX_OK;
        }
    }

    return NGX_DECLINED;
}
```

从 `ngx_pfree` 的实现可以看出，只有大的对象才会要求尽快释放，小的对象和没有被手动释放的大的对象都会随着内存池生命周期的结束而一起释放。如 `ngx_destroy_pool` 中的实现：

``` c
void
ngx_destroy_pool(ngx_pool_t *pool)
{
    ngx_pool_t          *p, *n;
    ngx_pool_large_t    *l;
    ngx_pool_cleanup_t  *c;

    for (c = pool->cleanup; c; c = c->next) {
        if (c->handler) {
            ngx_log_debug1(NGX_LOG_DEBUG_ALLOC, pool->log, 0,
                           "run cleanup: %p", c);
            c->handler(c->data);
        }
    }

#if (NGX_DEBUG)

    /*
     * we could allocate the pool->log from this pool
     * so we cannot use this log while free()ing the pool
     */

    for (l = pool->large; l; l = l->next) {
        ngx_log_debug1(NGX_LOG_DEBUG_ALLOC, pool->log, 0, "free: %p", l->alloc);
    }

    for (p = pool, n = pool->d.next; /* void */; p = n, n = n->d.next) {
        ngx_log_debug2(NGX_LOG_DEBUG_ALLOC, pool->log, 0,
                       "free: %p, unused: %uz", p, p->d.end - p->d.last);

        if (n == NULL) {
            break;
        }
    }

#endif

    for (l = pool->large; l; l = l->next) {
        if (l->alloc) {
            ngx_free(l->alloc);
        }
    }

    for (p = pool, n = pool->d.next; /* void */; p = n, n = n->d.next) {
        ngx_free(p);

        if (n == NULL) {
            break;
        }
    }
}
```

这个函数首先调用了一系列用户定义的 `pool->cleanup` 链表中的函数，允许自定义回收一些特定的资源。然后对每一个 `pool->large` 链表中的内容分别释放，最后再把各个块中所有的内存整块释放。注意 `ngx_large_block_t` 也是存在块中的，所以顺序不能反了。
