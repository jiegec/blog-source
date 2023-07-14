---
layout: post
date: 2023-02-07
tags: [openbsd,xonly,security]
categories:
    - system
---

# OpenBSD xonly 实现原理

## 背景

最近看到 [xonly status](https://marc.info/?l=openbsd-tech&m=167501519712725&w=2)，看到 OpenBSD 最近在实现 xonly，也就是让一些页只能执行，不能读不能写。以往类似的做法是 `W^X`，也就是可以执行的时候不能写，可以写的时候不能执行。显然，xonly 是更加严格的，连读都不可以。查了一下历史，`W^X` 最早也是在 OpenBSD 中实现的，说不定以后 xonly 也会被各个操作系统实现。

## amd64 上的实现

在 amd64 的页表中，决定执行/读/写权限的是（见 Intel 文档 `Table 4-20. Format of a Page-Table Entry that Maps a 4-KByte Page`）：

- Bit 1(R/W): `Read/write; if 0, writes may not be allowed to the 4-KByte page referenced by this entry (see Section 4.6)`
- Bit 63(XD): `If IA32_EFER.NXE = 1, execute-disable (if 1, instruction fetches are not allowed from the 4-KByte page controlled by this entry; see Section 4.6); otherwise, reserved (must be 0)`

可以看到，在这个定义下，可能出现的权限组合：

|                    | R   | W   | X   |
| ------------------ | --- | --- | --- |
| R/W=0, NXE=0       | Y   | N   | Y   |
| R/W=1, NXE=0       | Y   | Y   | Y   |
| R/W=0, NXE=1, XD=0 | Y   | N   | Y   |
| R/W=1, NXE=1, XD=0 | Y   | Y   | Y   |
| R/W=0, NXE=1, XD=1 | Y   | N   | N   |
| R/W=1, NXE=1, XD=1 | Y   | Y   | N   |

需要注意的是，`IA32_EFER.NXE` 是全局的，而 `R/W` 和 `XD` 的粒度是页。可以看到，上面的所有组合中，都是可以读的。

那么，怎么实现 x-only 呢？OpenBSD 的实现方法是 Protection Keys。在比较新的 CPU 中，页表的 4 个位用来表示使用的 Protection Key 下标，一共有 16 个：

- Bits 62:59: `Protection key; if CR4.PKE = 1 or CR4.PKS = 1, this may control the page's access rights (see Section 4.6.2); otherwise, it is ignored and not used to control access rights.`

那么 CPU 在查页表的时候，如果 `CR4.PKE=1 or CR4.PKS=1`，就会根据这四个位去查找 PKRU 寄存器的取值。PKRU 是一个 32 位的寄存器，每两位对应一个 Protection Key，这两位表示是否允许读写：

	The PKRU register (protection-key rights for user pages) is a 32-bit
	register with the following format: for each i (0 ≤ i ≤ 15), PKRU[2i] is
	the access-disable bit for protection key i (ADi); PKRU[2i+1] is the
	write-disable bit for protection key i (WDi). The IA32_PKRS MSR has the
	same format (bits 63:32 of the MSR are reserved and must be zero).

有了这个机制以后，就可以构造出 xonly 的页表项：

- R/W=0：不允许写
- NXE=1, XD=0：允许执行
- 设置 62:59 位为一个 Key 编号，将对应的 PKRU 的两个位设为 1：不允许读，不允许写

接下来看 OpenBSD 的[代码](https://github.com/openbsd/src/commit/e9e0c464329db9b56e1f2db65b0f536e53aa7e5f#diff-ab04285d8fd81f41887d9c9de2eb231be5e44c2d465f5c479943a1e21cf977ce)：

首先，检测 CPU 是否支持 PKU 机制：

```cpp
/*
 * If PKU is available, initialize PROT_EXEC entry correctly,
 * and enable the feature before it gets used
 * XXX Some Hypervisors forget to save/restore PKU
 */
if (cpuid_level >= 0x7) {
	uint32_t ecx, dummy;
	CPUID_LEAF(0x7, 0, dummy, dummy, ecx, dummy);
	if ((ecx & SEFF0ECX_PKU) &&
	    (cpu_ecxfeature & CPUIDECX_HV) == 0) {
		lcr4(rcr4() | CR4_PKE);
		pg_xo = PG_XO;
	}
}
```

其中 `PG_XO` 的值是 `0x0800000000000000UL`，也就是只有 bit 59 位 1，对应 Protection Key #1。OpenBSD 内核设置 PKRU 寄存器为 `0xfffffffc`，即只有 Protection Key #0 不修改权限，其他 Protection Key 都是禁止读写。剩下的代码就是维护 PKRU 寄存器的取值，然后把 xonly 的页的 Protection Key 都设为 1，否则设为 0。

但需要注意的是，PKRU 寄存器用户态也可以读写。Linux 把 PKRU 暴露给了[用户态](https://www.kernel.org/doc/html/latest/core-api/protection-keys.html)，允许用户态来自己设置页表的 Protection Key。OpenBSD 的实现方法则是进内核以后，检查 PKRU 寄存器，如果值修改了，就 SIGABRT。这有一定的风险，如果攻击代码修改了 PKRU 寄存器的内容，是有可能读取本来 xonly 的页的内容的。

## powerpc64 上的实现

powerpc64 的实现方法和 amd64 类似，见 [commit](https://github.com/openbsd/src/commit/6bd9427e6879f79e0e2c1e03d8411439da5bb69)。机制和 AMD64 很像，下面引用一段 PowerISA 文档：

	The Virtual Page Class Key Protection mechanism provides the means to
	assign virtual pages to one of 32 classes, and to modify data access
	permissions for each class by modifying the Authority Mask Register
	(AMR), shown in Figure 28, and to modify instruction access permissions
	for each class by modifying the Instruction Authority Mask Register
	(IAMR) shown in Figure 29.

对应如下代码：

```c
// sys/arch/powerpc64/powerpc64/cpu.c
	/*
	 * Set AMR to inhibit loads and stores for all virtual page
	 * class keys, except for Key0 which is used for normal kernel
	 * access.  This means we can pick any other key to implement
	 * execute-only mappings.  But we pick Key1 since that allows
	 * us to use the same bit in the PTE as was used to enable the
	 * Data Access Compare mechanism on CPUs based on older
	 * versions of the architecture (such as the PowerPC 970).
	 *
	 * Set UAMOR (and AMOR just to be safe) to zero to prevent
	 * userland from modifying any bits in AMR.
	 */
	mtamr(0x3fffffffffffffff);
	mtuamor(0);
	mtamor(0);
	isync();
```

可以看到方法是一样的，Key0 正常，其他 Key 禁止读写。额外地，PowerISA 还可以设置 Protection Key 禁止执行。并且通过设置 UAMOR 寄存器，用户态不可以修改 AMR 寄存器，这让 xonly 比 AMD64 上更为完备。

最后一步，就是修改 PTE 属性，指定 Key 即可：

```c
// sys/arch/powerpc64/include/pte.h
#define PTE_AC			0x0000000000000200ULL
// sys/arch/powerpc64/powerpc64/pmap.c
	if ((prot & (PROT_READ | PROT_WRITE)) == 0)
		pte->pte_lo |= PTE_AC;
```


## 其他指令集架构

一些指令集架构的页表在设计的时候，就有独立的 R W X 权限位，于是不需要特殊的处理，直接把 mmap 的参数映射过去即可。