---
layout: post
date: 2018-06-15
tags: [ebpf,tc,iproute2,hyperloglog]
category: programming
title: 编写 eBPF 程序和利用 HyperLogLog 统计包的信息
---

前段时间在写概率论与数理统计的期末论文，讨论的主题是如何对一个十分巨大的多重集合（或者是流）中相异元素个数进行估计，写的是 HyperLogLog 等算法。联想到前段时间 LWN 上多次提到的 eBPF 和 BCC 的文章，我准备自己用 eBPF 实现一个高效的估计 inbound packet 中来相异源地址的个数和 outbound packet 中相异目的地址的个数。经过了许多的尝试和努力，最终是写成了 [jiegec/hll_ebpf](https://github.com/jiegec/hll_ebpf) ，大致原理如下：

由于 eBPF 是一个采用专用的 bytecode 并且跑在内核中的语言，虽然我们可以用 clang 写 C 语言然后交给 LLVM 生成相应地 eBPF bytecode，但仍然收到许多的限制。而且，我很少接触 Linux 内核开发，于是在找内核头文件时费了一番功夫。首先是核心代码：

```c
struct bpf_map_def SEC("maps") hll_ebpf_out_daddr = {
    .type = BPF_MAP_TYPE_PERCPU_ARRAY,
    .key_size = sizeof(u32),
    .value_size = sizeof(u32),
    .max_entries = 256,
    .pinning = 2 // PIN_GLOBAL_NS
};

SEC("out_daddr")
int bpf_out_daddr(struct __sk_buff *skb) {
  u32 daddr = get_daddr(skb);
  u32 hash = Murmur3(daddr, 0);
  update_hll(&hll_ebpf_out_daddr, hash);
  return 0;
}
```

首先是声名一个类型为 PERCPU_ARRAY 的 eBPF MAP 类型。这里的 MAP 不是字典，Array 才是真是的数据结构，只不过提供的 API 是类似于字典的。SEC 宏则是指定这个东西要放在哪一个段，这个在后面会提到。这个函数的作用就是，获取 IP 包的目的地址（其实应该判断一下是否是 IPv4 的），然后根据 HyperLogLog 的要求，进行哈希（这里采用的是 Murmur3），然后对得到的哈希值分段，前一部分用于索引，后一部分的 nlz（clz, whatever）用于估计。具体算法详情可以参考 HyperLogLog 的论文。

接着，我们可以把这个 eBPF 函数进行编译，并且应用起来：

```shell
$ export KERN=4.16.0-2 # or use uname -r with awk, see Makefile
$ clang -O2 -I /usr/src/linux-headers-${KERN}-common/include -I /usr/src/linux-headers-${KERN}-common/arch/x86/include -emit-llvm -c bpf.c -o - | llc -march=bpf -filetype=obj -o bpf.o
$ export IFACE=en0 
$ sudo tc qdisc add dev ${IFACE} clsact || true
$ sudo tc filter del dev ${IFACE} egress
$ sudo tc filter add dev ${IFACE} egress bpf obj bpf.o sec out_daddr
$ sudo tc filter del dev ${IFACE} ingress
$ sudo tc filter add dev ${IFACE} ingress bpf obj bpf.o sec in_saddr
```

我们需要在用户态读出上面这个 MAP 中的内容。由于它是全局的，我们可以在 `/sys/fs/bpf/tc/globals` 中找到他们。然后，把统计得到的数据进行综合，得到结果：

```c
void read_file(const char *file) {
  int fd = bpf_obj_get(file);
  const static int b = 6;
  const static int m = 1 << b;
  int M[m] = {0};
  int V = 0;
  double sum = 0;
  for (unsigned long i = 0; i <m; i++) {
    unsigned long value[2] = {0};
    bpf_map_lookup_elem(fd, &i, &value);
    M[i] = value[0] > value[1] ? value[0] : value[1]; // assuming 2 CPUs, will change later
    if (M[i] == 0)
      V++;
    sum += pow(2, -M[i]);
  }
  double E = 0.709 * m * m / sum;
  if (E <= 5 * m / 2) {
    if (V != 0) {
      E = m * log(1.0 * m / V);
    }
  } else if (E> pow(2, 32) / 30) {
    E = -pow(2, 32) * log(1 - E / pow(2, 32));
  }
  printf("%ld\n", lround(E));
}
```

可以手动通过 `nmap` 测试，例如扫描一个段，可以看到数据会增长许多。如果扫描相同的段，则数字不会变化，但如果扫描新的段，数字会有变化。这是一个 利用了 eBPF 的 HyperLogLog 的实现。
