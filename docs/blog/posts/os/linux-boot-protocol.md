---
layout: post
date: 2023-10-01
tags: [linux,uefi,boot,uboot,riscv]
categories:
    - os
---

# Linux 内核格式与启动协议

## 背景

之前在各种场合遇到过各种 Linux 内核的文件名或格式，例如：

- vmlinux
- vmlinuz
- uImage
- bzImage
- uImage

即使是同样的文件名，格式可能也是不一样的，相应的启动协议也可能不一样。这篇博客尝试结合 Linux，各种 Bootloader（QEMU，EDK-II，U-Boot，OpenSBI）的代码来研究不同的 Linux 二进制格式以及启动协议。

<!-- more -->

## amd64/x86_64

首先是常用的 amd64 架构，找几个系统，查看 `/boot` 目录下的 kernel 文件的类型：

```
/boot/vmlinuz-6.1.0-12-amd64: Linux kernel x86 boot executable bzImage, version 6.1.0-12-amd64 (debian-kernel@lists.debian.org) #1 SMP PREEMPT_DYNAMIC Debian 6.1.52-1 (2023-09-07), RO-rootFS, swap_dev 0X7, Normal VGA
/boot/vmlinuz-6.2.16-14-pve: Linux kernel x86 boot executable bzImage, version 6.2.16-14-pve (build@proxmox) #1 SMP PREEMPT_DYNAMIC PMX 6.2.16-14 (2023-09-19T08:17Z), RO-rootFS, swap_dev 0XC, Normal VGA
```

看了几个系统，发现文件名都是 `vmlinuz` 开头，文件类型都是 `Linux kernel x86 boot executable bzImage`。

### Linux/x86 Boot Protocol

Linux 在 x86 下定义了一套 [Linux/x86 Boot Protocol](https://www.kernel.org/doc/html/v5.6/x86/boot.html)，它规定了 bootloader 在启动 Linux 的时候，需要做哪些事情，传递哪些参数，以什么形式传递参数，那么 Linux 就可以在这给基础上启动起来。

首先，Boot Protocol 定义了 Linux 内核的格式，使得 Bootloader 可以得到关于 Linux 内核的一些信息。这个格式定义在 [The Real-Mode Kernel Header](https://www.kernel.org/doc/html/v5.6/x86/boot.html#the-real-mode-kernel-header)，是一个巨大的结构体，对应的[代码](https://github.com/torvalds/linux/blob/e402b08634b398e9feb94902c7adcf05bb8ba47d/arch/x86/boot/header.S#L283-L584)如下：

```asm
	.section ".header", "a"
	.globl	sentinel
sentinel:	.byte 0xff, 0xff        /* Used to detect broken loaders */

	.globl	hdr
hdr:
setup_sects:	.byte 0			/* Filled in by build.c */
root_flags:	.word ROOT_RDONLY
syssize:	.long 0			/* Filled in by build.c */
ram_size:	.word 0			/* Obsolete */
vid_mode:	.word SVGA_MODE
root_dev:	.word 0			/* Filled in by build.c */
boot_flag:	.word 0xAA55
```

后面还有很长，都是这个结构体里的字段。其中也可以看到熟悉的 `0xAA55`，熟悉的启动分区结尾。这片数据通过 [linker script](https://github.com/torvalds/linux/blob/e402b08634b398e9feb94902c7adcf05bb8ba47d/arch/x86/boot/setup.ld#L16-L21) 来放置到从文件开始偏移 0x1f1 处：

```
	. = 495;
	.header		: { *(.header) }
	.entrytext	: { *(.entrytext) }
	.inittext	: { *(.inittext) }
	.initdata	: { *(.initdata) }
	__end_init = .;
```

这里 `495=0x1ef`，再加上两个 `sentinel` 字节，最终 `hdr` 就会落在 0x1f1 地址处。前面看到的 `file` 命令输出里的各个字段，其实也是从这里[读来](https://github.com/file/file/blob/de7d52dce3e7a0bb1a72f299a265c2b641187842/magic/Magdir/linux#L137-L163)的：

```
/boot/vmlinuz-6.1.0-12-amd64: Linux kernel x86 boot executable bzImage, version 6.1.0-12-amd64 (debian-kernel@lists.debian.org) #1 SMP PREEMPT_DYNAMIC Debian 6.1.52-1 (2023-09-07), RO-rootFS, swap_dev 0X7, Normal VGA
```

```
# Linux kernel boot images, from Albert Cahalan <acahalan@cs.uml.edu>
# and others such as Axel Kohlmeyer <akohlmey@rincewind.chemie.uni-ulm.de>
# and Nicolas Lichtmaier <nick@debian.org>
# All known start with: b8 c0 07 8e d8 b8 00 90 8e c0 b9 00 01 29 f6 29
# Linux kernel boot images (i386 arch) (Wolfram Kleff)
# URL: https://www.kernel.org/doc/Documentation/x86/boot.txt
514	string		HdrS		Linux kernel
!:strength + 55
# often no extension like in linux, vmlinuz, bzimage or memdisk but sometimes
# Acronis Recovery kernel64.dat and Plop Boot Manager plpbtrom.bin
# DamnSmallLinux 1.5 damnsmll.lnx 
!:ext	/dat/bin/lnx
>510	leshort		0xAA55		x86 boot executable
>>518	leshort		>0x1ff
>>>529	byte		0		zImage,
>>>529	byte		1		bzImage,
>>>526	lelong		>0
>>>>(526.s+0x200) string	>\0	version %s,
>>498	leshort		1		RO-rootFS,
>>498	leshort		0		RW-rootFS,
>>508	leshort		>0		root_dev %#X,
>>502	leshort		>0		swap_dev %#X,
>>504	leshort		>0		RAMdisksize %u KB,
>>506	leshort		0xFFFF		Normal VGA
>>506	leshort		0xFFFE		Extended VGA
>>506	leshort		0xFFFD		Prompt for Videomode
>>506	leshort		>0		Video mode %d
```

这里的判断和 Linux 源码的对应关系如下：

```
514	string		HdrS		Linux kernel
		.ascii	"HdrS"		# header signature

>510	leshort		0xAA55		x86 boot executable
boot_flag:	.word 0xAA55

>>>529	byte		0		zImage,
>>>529	byte		1		bzImage,
loadflags:
		.byte	LOADED_HIGH	# The kernel is to be loaded high

>>>>(526.s+0x200) string	>\0	version %s,
		.word	kernel_version-512 # pointing to kernel version string
					# above section of header is compatible
					# with loadlin-1.5 (header v1.5). Don't
					# change it.

>>498	leshort		1		RO-rootFS,
>>498	leshort		0		RW-rootFS,
root_flags:	.word ROOT_RDONLY

>>508	leshort		>0		root_dev %#X,
root_dev:	.word 0			/* Filled in by build.c */

>>502	leshort		>0		swap_dev %#X,
syssize:	.long 0			/* Filled in by build.c */

>>504	leshort		>0		RAMdisksize %u KB,
ram_size:	.word 0			/* Obsolete */

>>506	leshort		0xFFFF		Normal VGA
>>506	leshort		0xFFFE		Extended VGA
>>506	leshort		0xFFFD		Prompt for Videomode
>>506	leshort		>0		Video mode %d
vid_mode:	.word SVGA_MODE
```

在此基础上，Bootloader 初始化 [`struct boot_params`](https://github.com/torvalds/linux/blob/e402b08634b398e9feb94902c7adcf05bb8ba47d/arch/x86/include/uapi/asm/bootparam.h#L184-L232) 并传给 Linux 内核：

```c
/* The so-called "zeropage" */
struct boot_params {
	struct screen_info screen_info;			/* 0x000 */
	struct apm_bios_info apm_bios_info;		/* 0x040 */
	__u8  _pad2[4];					/* 0x054 */
	__u64  tboot_addr;				/* 0x058 */
	struct ist_info ist_info;			/* 0x060 */
	__u64 acpi_rsdp_addr;				/* 0x070 */
	/* omitted */

	/*
	 * The sentinel is set to a nonzero value (0xff) in header.S.
	 *
	 * A bootloader is supposed to only take setup_header and put
	 * it into a clean boot_params buffer. If it turns out that
	 * it is clumsy or too generous with the buffer, it most
	 * probably will pick up the sentinel variable too. The fact
	 * that this variable then is still 0xff will let kernel
	 * know that some variables in boot_params are invalid and
	 * kernel should zero out certain portions of boot_params.
	 */
	__u8  sentinel;					/* 0x1ef */
	__u8  _pad6[1];					/* 0x1f0 */
	struct setup_header hdr;    /* setup header */	/* 0x1f1 */
	__u8  _pad7[0x290-0x1f1-sizeof(struct setup_header)];
	__u32 edd_mbr_sig_buffer[EDD_MBR_SIG_MAX];	/* 0x290 */
	struct boot_e820_entry e820_table[E820_MAX_ENTRIES_ZEROPAGE]; /* 0x2d0 */
	/* omitted */
}
```

接着 Kernel 就会启动，根据 `struct boot_params` 的各个字段进行初始化。

### EFI boot stub

如果用 `xxd` 查看文件开头，会发现它具有 PE 和 COFF 头部：

```
00000000: 4d5a ea07 00c0 078c c88e d88e c08e d031  MZ.............1
00000010: e4fb fcbe 4000 ac20 c074 09b4 0ebb 0700  ....@.. .t......
00000020: cd10 ebf2 31c0 cd16 cd19 eaf0 ff00 f000  ....1...........
00000030: 0000 0000 0000 0000 cd23 8281 8200 0000  .........#......
00000040: 5573 6520 6120 626f 6f74 206c 6f61 6465  Use a boot loade
00000050: 722e 0d0a 0a52 656d 6f76 6520 6469 736b  r....Remove disk
00000060: 2061 6e64 2070 7265 7373 2061 6e79 206b   and press any k
00000070: 6579 2074 6f20 7265 626f 6f74 2e2e 2e0d  ey to reboot....
00000080: 0a00 5045 0000 6486 0400 0000 0000 0000  ..PE..d.........
00000090: 0000 0100 0000 a000 0602 0b02 0214 00fe  ................
000000a0: a504 0000 0000 0000 0000 9c07 cf00 0002  ................
```

这样做的目的是让 UEFI 认为 vmlinux 也是一个合法的 UEFI 程序，而 UEFI 的程序格式正是 [PE](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)，这种做法就是 [EFI boot stub](https://docs.kernel.org/admin-guide/efi-stub.html)，生成一个满足 UEFI 要求的头部。在 Linux 源码 [arch/x86/boot/header.S](https://github.com/torvalds/linux/blob/e402b08634b398e9feb94902c7adcf05bb8ba47d/arch/x86/boot/header.S#L39-L96)中，使用汇编来构造出一个 MS-DOS Stub：

```asm
	.section ".bstext", "ax"

	.global bootsect_start
bootsect_start:
#ifdef CONFIG_EFI_STUB
	# "MZ", MS-DOS header
	.word	MZ_MAGIC
#endif
```

首先是经典的 `MZ`，也就是 MS-DOS Stub 的 magic。MS-DOS Stub 在偏移 `0x3c` 的地方，记录了到 PE 头部的偏移：

```asm
#ifdef CONFIG_EFI_STUB
	.org	0x38
	#
	# Offset to the PE header.
	#
	.long	LINUX_PE_MAGIC
	.long	pe_header
#endif /* CONFIG_EFI_STUB */
```

后面才是实际的 COFF 头部，在汇编中填写 COFF 头部的各个字段：

```asm
#ifdef CONFIG_EFI_STUB
pe_header:
	.long	PE_MAGIC

coff_header:
#ifdef CONFIG_X86_32
	.set	image_file_add_flags, IMAGE_FILE_32BIT_MACHINE
	.set	pe_opt_magic, PE_OPT_MAGIC_PE32
	.word	IMAGE_FILE_MACHINE_I386
#else
	.set	image_file_add_flags, 0
	.set	pe_opt_magic, PE_OPT_MAGIC_PE32PLUS
	.word	IMAGE_FILE_MACHINE_AMD64
#endif
	.word	section_count			# nr_sections
	.long	0 				# TimeDateStamp
	.long	0				# PointerToSymbolTable
	.long	1				# NumberOfSymbols
	.word	section_table - optional_header	# SizeOfOptionalHeader
	.word	IMAGE_FILE_EXECUTABLE_IMAGE	| \
		image_file_add_flags		| \
		IMAGE_FILE_DEBUG_STRIPPED	| \
		IMAGE_FILE_LINE_NUMS_STRIPPED	# Characteristics
```

后面还有很多内容，这里没有完整贴出来。里面比较重要的是 AddressOfEntryPoint，也就是 PE 程序的入口。UEFI 在执行 PE 程序的时候，会按照下面的[函数签名调用](https://uefi.org/specs/UEFI/2.10/07_Services_Boot_Services.html#efi-image-entry-point)：

```
typedef
EFI_STATUS
(EFIAPI *EFI_IMAGE_ENTRY_POINT) (
   IN EFI_HANDLE                             ImageHandle,
   IN EFI_SYSTEM_TABLE                       *SystemTable
   );
```

所以 Linux 也按照这个签名实现了一个[函数](https://github.com/torvalds/linux/blob/e402b08634b398e9feb94902c7adcf05bb8ba47d/drivers/firmware/efi/libstub/x86-stub.c#L449)：

```c
/*
 * Because the x86 boot code expects to be passed a boot_params we
 * need to create one ourselves (usually the bootloader would create
 * one for us).
 */
efi_status_t __efiapi efi_pe_entry(efi_handle_t handle,
				   efi_system_table_t *sys_table_arg);
```

那么当从 UEFI 执行 vmlinuz 的时候，UEFI 就会从 COFF 头部找到 `efi_pe_entry` 函数的地址，传入两个参数，然后调用它。这个函数负责的是，模仿 Bootloader 的行为，填写 `struct boot_param`，然后跳转到真正的内核 entrypoint。

### 内核压缩

Linux 内核还经常会以压缩的形式存在，压缩的算法可能采用 gzip 等等。压缩的同时，也会放一份没有被压缩的汇编代码，用来解压。为了区分内核是否经过压缩，通常约定 `vmlinux` 表示没有经过压缩，`vmlinuz` 表示经过压缩。

### Image/zImage/bzImage/uImage

有时候还会看到另一种术语：Image 添加一个前缀，如：

- Image：未经过压缩的 Linux 内核
- zImage：经过压缩的 Linux 内核
- bzImage：big zImage，而不是 bzip Image，是 zImage 的后续格式

bzImage 和 zImage 从 Boot Protocol 来看，[加载的地址不同](https://www.kernel.org/doc/html/v5.6/x86/boot.html#loading-the-rest-of-the-kernel)：

```c
is_bzImage = (protocol >= 0x0200) && (loadflags & 0x01);
load_address = is_bzImage ? 0x100000 : 0x10000;
```

这样解决了 Image/zImage 的大小上限问题（地址范围 0x10000-0x90000，512KB），所以基本只能见到 bzImage 了。

而 uImage 其实是 U-Boot 的启动镜像格式，在 Linux 内核外面套了一层自己的格式。但现在 U-Boot 设计了新的格式：U-Boot FIT Image。由于 x86 上一般不会用 U-Boot，这里就不涉及了。

在编译内核过程中，这些文件关系是：

- vmlinux: 首先链接出来的 ELF
- arch/x86/boot/compressed/vmlinux.bin: 从 vmlinux objcopy 得到的 ELF 文件，去掉了 .comment section
- arch/x86/boot/compressed/vmlinux.bin.gz: 对 arch/x86/boot/compressed/vmlinux.bin 进行压缩
- arch/x86/boot/compressed/vmlinux: 把 arch/x86/boot/compressed/vmlinux.bin.gz（通过 arch/x86/boot/compressed/piggy.S 使用 .incbin 引入）和解压缩程序打包在一起，成为一个新的 vmlinux
- arch/x86/boot/vmlinux.bin: 从 arch/x86/boot/compressed/vmlinux objcopy 得到的二进制文件，去掉了 .note 和 .comment section
- arch/x86/boot/bzImage: 把 arch/x86/boot/vmlinux.bin 组装成最终的格式

这个过程中执行的命令，可以从目录下对应的 `.cmd` 文件里找到：

```shell
$ cat arch/x86/boot/compressed/.vmlinux.bin.cmd
cmd_arch/x86/boot/compressed/vmlinux.bin := objcopy  -R .comment -S vmlinux arch/x86/boot/compressed/vmlinux.bin
$ cat arch/x86/boot/compressed/.vmlinux.bin.gz.cmd
cmd_arch/x86/boot/compressed/vmlinux.bin.gz := cat arch/x86/boot/compressed/vmlinux.bin arch/x86/boot/compressed/vmlinux.relocs | gzip -n -f -9 > arch/x86/boot/compressed/vmlinux.bin.gz
$ cat arch/x86/boot/compressed/.vmlinux.cmd
cmd_arch/x86/boot/compressed/vmlinux := ld -m elf_x86_64 --no-ld-generated-unwind-info  -pie  --no-dynamic-linker --orphan-handling=warn -z noexecstack --no-warn-rwx-segments -T arch/x86/boot/compressed/vmlinux.lds arch/x86/boot/compressed/kernel_info.o arch/x86/boot/compressed/head_64.o arch/x86/boot/compressed/misc.o arch/x86/boot/compressed/string.o arch/x86/boot/compressed/cmdline.o arch/x86/boot/compressed/error.o arch/x86/boot/compressed/piggy.o arch/x86/boot/compressed/cpuflags.o arch/x86/boot/compressed/early_serial_console.o arch/x86/boot/compressed/kaslr.o arch/x86/boot/compressed/ident_map_64.o arch/x86/boot/compressed/idt_64.o arch/x86/boot/compressed/idt_handlers_64.o arch/x86/boot/compressed/mem_encrypt.o arch/x86/boot/compressed/pgtable_64.o arch/x86/boot/compressed/sev.o arch/x86/boot/compressed/acpi.o arch/x86/boot/compressed/tdx.o arch/x86/boot/compressed/tdcall.o arch/x86/boot/compressed/efi_thunk_64.o arch/x86/boot/compressed/efi.o drivers/firmware/efi/libstub/lib.a -o arch/x86/boot/compressed/vmlinux
$ cat arch/x86/boot/.vmlinux.bin.cmd
cmd_arch/x86/boot/vmlinux.bin := objcopy  -O binary -R .note -R .comment -S arch/x86/boot/compressed/vmlinux arch/x86/boot/vmlinux.bin
$ cat arch/x86/boot/.bzImage.cmd
cmd_arch/x86/boot/bzImage := arch/x86/boot/tools/build arch/x86/boot/setup.bin arch/x86/boot/vmlinux.bin arch/x86/boot/zoffset.h arch/x86/boot/bzImage
```

最后就由 `installkernel` 命令把 `bzImage` 复制到 `/boot` 下，并改名为 `vmlinuz`。

对于这一过程的完整描述，推荐阅读 [老司机带你探索内核编译系统](https://richardweiyang-2.gitbook.io/kernel-exploring/00_index/06_building_vmlinux_under_root)，写的比较详细。

### Unified Kernel Image

[Unified Kernel Image](https://wiki.gentoo.org/wiki/Unified_Kernel_Image) 也是一种比较新的格式，它把启动时候需要的一些文件（Linux 内核，微码，initramfs 等等），都放在一个文件里，这样方便 Secure Boot，只需要对一个大文件进行签名即可。

## riscv64

RISC-V 现在通常有两套固件标准，一套是 SBI（Supervisor Binary Interface），另一套是 UEFI。

### SBI

[SBI](https://github.com/riscv-non-isa/riscv-sbi-doc) 是 M 态程序提供给 S 态程序的一套接口。SBI 一个的常见实现就是 OpenSBI，当 OpenSBI 加载 Linux 的时候，做了如下[约定](https://github.com/riscv-software-src/opensbi/blob/b7e9d34edf4f728bb02d11f73a2f9f79ad4acce4/lib/sbi/sbi_hsm.c#L138-L157)：

- a0: hart id
- a1: dtb 地址

代码如下：

```c
void __noreturn sbi_hsm_hart_start_finish(struct sbi_scratch *scratch,
					  u32 hartid)
{
	unsigned long next_arg1;
	unsigned long next_addr;
	unsigned long next_mode;
	struct sbi_hsm_data *hdata = sbi_scratch_offset_ptr(scratch,
							    hart_data_offset);

	if (!__sbi_hsm_hart_change_state(hdata, SBI_HSM_STATE_START_PENDING,
					 SBI_HSM_STATE_STARTED))
		sbi_hart_hang();

	next_arg1 = scratch->next_arg1;
	next_addr = scratch->next_addr;
	next_mode = scratch->next_mode;
	hsm_start_ticket_release(hdata);

	sbi_hart_switch_mode(hartid, next_arg1, next_addr, next_mode, false);
}
```

这里 `sbi_hart_switch_mode` 前两个参数就是最终要传给 Linux 的参数，第一个参数 `hartid` 通过 `a0` 寄存器传递，第二个参数 `next_arg1` 通过 `a1` 寄存器传递。

当 Linux 启动的时候，就会从 dtb 中获取系统的各项信息。这样的设计接口比较简单，只需要传两个寄存器，但是很多东西就要放到 dtb 里面去传了，例如 initrd 的地址，cmdline 等等。无论是 bootloader 还是 Linux，都需要附带 dtb 解析和修改的代码，不像 x86 那样，只需要传一个固定结构的结构体即可。

QEMU 支持直接加载 Kernel，也就是说 QEMU 也要负责[实现](https://github.com/qemu/qemu/blob/36e9aab3c569d4c9ad780473596e18479838d1aa/target/riscv/kvm.c#L1010-L1021)上面的 Boot Protocol：

```cpp
void kvm_riscv_reset_vcpu(RISCVCPU *cpu)
{
    CPURISCVState *env = &cpu->env;

    if (!kvm_enabled()) {
        return;
    }
    env->pc = cpu->env.kernel_addr;
    env->gpr[10] = kvm_arch_vcpu_id(CPU(cpu)); /* a0 */
    env->gpr[11] = cpu->env.fdt_addr;          /* a1 */
    env->satp = 0;
}
```

### UEFI

RISC-V 也支持用 UEFI 启动，它的做法和 x86 类似，也是做一个 EFI Boot Stub。稍微不一样的是，通过[构造](https://github.com/torvalds/linux/blob/e402b08634b398e9feb94902c7adcf05bb8ba47d/arch/riscv/kernel/head.S#L21-L39)，EFI boot stub 可以保证它在直接当成 RISC-V 程序执行的时候，也可以正常工作：

```asm
__HEAD
ENTRY(_start)
	/*
	 * Image header expected by Linux boot-loaders. The image header data
	 * structure is described in asm/image.h.
	 * Do not modify it without modifying the structure and all bootloaders
	 * that expects this header format!!
	 */
#ifdef CONFIG_EFI
	/*
	 * This instruction decodes to "MZ" ASCII required by UEFI.
	 */
	c.li s4,-13
	j _start_kernel
#else
	/* jump to start kernel */
	j _start_kernel
	/* reserved */
	.word 0
#endif
```

在 RISC-V 下，PE 头部的 `MZ` 可以被解析成合法的指令，在它后面跳转到实际的 Kernel 入口，这样即使 Bootloader 没有实现 UEFI，例如 OpenSBI，跳转到 Kernel 第一条指令开始执行，也可以正常进入到 `_start_kernel` 当中。

和 x86 类似，EFI boot stub 的实际 entry point 是一个单独的[函数](https://github.com/torvalds/linux/blob/e402b08634b398e9feb94902c7adcf05bb8ba47d/drivers/firmware/efi/libstub/efi-stub-entry.c#L19-L26)，而不是原来的 `_start_kernel`：

```c
/*
 * EFI entry point for the generic EFI stub used by ARM, arm64, RISC-V and
 * LoongArch. This is the entrypoint that is described in the PE/COFF header
 * of the core kernel.
 */
efi_status_t __efiapi efi_pe_entry(efi_handle_t handle,
				   efi_system_table_t *systab);
```

这个函数的接口和前面 amd64 UEFI 是一样的，因为是 UEFI 标准规定的。它做的事情是，从 UEFI 获取系统信息，构造出一个 dtb，然后从 UEFI 中获取 hart id（见后），然后再[跳转到实际的 `_start_kernel`](https://github.com/torvalds/linux/blob/e402b08634b398e9feb94902c7adcf05bb8ba47d/drivers/firmware/efi/libstub/riscv.c#L90-L97)，传递的参数和前面 SBI 时是一样的：

```c
void __noreturn efi_enter_kernel(unsigned long entrypoint, unsigned long fdt,
				 unsigned long fdt_size)
{
	unsigned long kernel_entry = entrypoint + stext_offset();
	jump_kernel_func jump_kernel = (jump_kernel_func)kernel_entry;

	/*
	 * Jump to real kernel here with following constraints.
	 * 1. MMU should be disabled.
	 * 2. a0 should contain hartid
	 * 3. a1 should DT address
	 */
	csr_write(CSR_SATP, 0);
	jump_kernel(hartid, fdt);
}
```

为了让 EFI boot stub 可以获取到 boot hart id，还设计了 [`RISCV_EFI_BOOT_PROTOCOL`](https://github.com/riscv-non-isa/riscv-uefi/blob/main/boot_protocol.adoc)，使得 EFI boot stub 可以[获取 boot hart id](https://github.com/torvalds/linux/blob/ec8c298121e3616f8013d3cf1db9c7169c9b0b2d/drivers/firmware/efi/libstub/riscv.c#L46-L57)：

```c
static efi_status_t get_boot_hartid_from_efi(void)
{
	efi_guid_t boot_protocol_guid = RISCV_EFI_BOOT_PROTOCOL_GUID;
	struct riscv_efi_boot_protocol *boot_protocol;
	efi_status_t status;

	status = efi_bs_call(locate_protocol, &boot_protocol_guid, NULL,
			     (void **)&boot_protocol);
	if (status != EFI_SUCCESS)
		return status;
	return efi_call_proto(boot_protocol, get_boot_hartid, &hartid);
}
```

这个函数就会在 UEFI 固件中实现，例如 [edk2](https://github.com/tianocore/edk2/blob/f36e1ec1f0a5fd3be84913e09181d7813444b620/UefiCpuPkg/CpuDxeRiscV64/CpuDxe.c#L21-L45)：

```c
/**
  Get the boot hartid

  @param  This                   Protocol instance structure
  @param  BootHartId             Pointer to the Boot Hart ID variable

  @retval EFI_SUCCESS            If BootHartId is returned
  @retval EFI_INVALID_PARAMETER  Either "BootHartId" is NULL or "This" is not
                                 a valid RISCV_EFI_BOOT_PROTOCOL instance.

**/
EFI_STATUS
EFIAPI
RiscvGetBootHartId (
  IN RISCV_EFI_BOOT_PROTOCOL  *This,
  OUT UINTN                   *BootHartId
  )
{
  if ((This != &gRiscvBootProtocol) || (BootHartId == NULL)) {
    return EFI_INVALID_PARAMETER;
  }

  *BootHartId = mBootHartId;
  return EFI_SUCCESS;
}
```

以及 [U-Boot](https://github.com/u-boot/u-boot/blob/2173c4a990664d8228d4dadd814bd64fdc12948f/lib/efi_loader/efi_riscv.c#L21-L44)：

```c
/**
 * efi_riscv_get_boot_hartid() - return boot hart ID
 * @this:		RISCV_EFI_BOOT_PROTOCOL instance
 * @boot_hartid:	caller allocated memory to return boot hart id
 * Return:		status code
 */
static efi_status_t EFIAPI
efi_riscv_get_boot_hartid(struct riscv_efi_boot_protocol *this,
			  efi_uintn_t *boot_hartid)
{
	EFI_ENTRY("%p, %p",  this, boot_hartid);

	if (this != &riscv_efi_boot_prot || !boot_hartid)
		return EFI_EXIT(EFI_INVALID_PARAMETER);

	*boot_hartid = gd->arch.boot_hart;

	return EFI_EXIT(EFI_SUCCESS);
}

struct riscv_efi_boot_protocol riscv_efi_boot_prot = {
	.revision = RISCV_EFI_BOOT_PROTOCOL_REVISION,
	.get_boot_hartid = efi_riscv_get_boot_hartid
};
```