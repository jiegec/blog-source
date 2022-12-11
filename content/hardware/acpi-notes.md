---
layout: post
date: 2022-12-10 20:44:00 +0800
tags: [acpi,notes,learn]
category: hardware
title: ACPI 学习笔记
---

## 标准

ACPI 标准可以从[官网](https://uefi.org/specifications)下载。

ACPI 的表现形式为一颗树，结点可能是属性，或者是一些函数。操作系统可以操作上面的属性，调用 ACPI 中的函数，来进行一些硬件相关的操作。ACPI 一般与主板密切相关，主板厂家配置好 ACPI 后，操作系统就不需要给每个主板都写一遍代码了。

## ASL

为了开发 ACPI，需要使用 ACPI Source Language(ASL) 来进行编程，使用 iasl 编译成 ACPI 表以后，由操作系统进行解释执行。推荐阅读一个比较好的 ASL 教程：[ACPI Source Language (ASL) Tutorial](https://acpica.org/sites/acpica/files/asl_tutorial_v20190625.pdf)。

简单来说，ASL 中的变量类型：

- Integer: `int32_t/int64_t`
- String: `char *`
- Buffer: `uint8_t []`
- Package: `object []`
- Object Reference: `object &`
- Method

ACPI 需要访问硬件，一般是通过 MMIO 或者 IO Port 来进行访问。在内核开发的时候，MMIO 一般是用一系列 volatile 指针来对应硬件的寄存器定义。ASL 中也可以做类似的事情，分为两步：`OperationRegion` 和 `Field`。

`OperationRegion` 就是声明了一片地址空间，以及对应的类型，常见的类型有 SystemMemory、SystemIO、PCI_Config、SMBus 等等。当 ACPI 中的代码要访问 `OperationRegion` 中的数据的时候，内核按照类型去进行实际的访问。

有了地址空间以后，还需要根据寄存器的定义，给各个字段起个名字，这就是 `Field`。`Field` 给 `OperationRegion` 中的字段起名，与硬件的定义想对应，这就像在内核中定义一个结构体，保证结构体的成员的偏移和硬件是一致的。这样就可以通过成员来访问，而不是每次都去计算一次偏移。

## 获取当前系统的 ACPI 表

使用以下命令获取 ACPI 表并转换为可以阅读的格式：

```shell
sudo acpidump -o acpi.raw
acpixtract -a acpi.raw
iasl -d *.dat
```

## 串口

### x86_64

下面来看一个具体的例子，主板 `WS X299 PRO/SE` 的 ACPI 表中记录的串口信息：

```asl
Device (UAR1)
{
    Name (_HID, EisaId ("PNP0501") /* 16550A-compatible COM Serial Port */)  // _HID: Hardware ID
    Name (_UID, 0x00)  // _UID: Unique ID
    Name (LDN, 0x02)
    Method (_STA, 0, NotSerialized)  // _STA: Status
    {
        Return (^^SIO1.DSTA (0x00))
    }

    Method (_DIS, 0, NotSerialized)  // _DIS: Disable Device
    {
        ^^SIO1.DCNT (0x00, 0x00)
    }

    Method (_CRS, 0, NotSerialized)  // _CRS: Current Resource Settings
    {
        Return (^^SIO1.DCRS (0x00, 0x00))
    }

    Method (_SRS, 1, NotSerialized)  // _SRS: Set Resource Settings
    {
        ^^SIO1.DSRS (Arg0, 0x00)
    }

    Name (_PRS, ResourceTemplate ()  // _PRS: Possible Resource Settings
    {
        StartDependentFn (0x00, 0x00)
        {
            IO (Decode16,
                0x03F8,             // Range Minimum
                0x03F8,             // Range Maximum
                0x01,               // Alignment
                0x08,               // Length
                )
            IRQNoFlags ()
                {4}
            DMA (Compatibility, NotBusMaster, Transfer8, )
                {}
        }
        StartDependentFnNoPri ()
        {
            IO (Decode16,
                0x03F8,             // Range Minimum
                0x03F8,             // Range Maximum
                0x01,               // Alignment
                0x08,               // Length
                )
            IRQNoFlags ()
                {4}
            DMA (Compatibility, NotBusMaster, Transfer8, )
                {}
        }
        StartDependentFnNoPri ()
        {
            IO (Decode16,
                0x02F8,             // Range Minimum
                0x02F8,             // Range Maximum
                0x01,               // Alignment
                0x08,               // Length
                )
            IRQNoFlags ()
                {3}
            DMA (Compatibility, NotBusMaster, Transfer8, )
                {}
        }
        StartDependentFnNoPri ()
        {
            IO (Decode16,
                0x03E8,             // Range Minimum
                0x03E8,             // Range Maximum
                0x01,               // Alignment
                0x08,               // Length
                )
            IRQNoFlags ()
                {4}
            DMA (Compatibility, NotBusMaster, Transfer8, )
                {}
        }
        StartDependentFnNoPri ()
        {
            IO (Decode16,
                0x02E8,             // Range Minimum
                0x02E8,             // Range Maximum
                0x01,               // Alignment
                0x08,               // Length
                )
            IRQNoFlags ()
                {3}
            DMA (Compatibility, NotBusMaster, Transfer8, )
                {}
        }
        EndDependentFn ()
    })
    Method (_PRW, 0, NotSerialized)  // _PRW: Power Resources for Wake
    {
        Return (GPRW (0x6B, 0x04))
    }
}
```

这个设备在 Linux 中的路径是 `/sys/devices/LNXSYSTM:00/LNXSYBUS:00/PNP0A08:00/device:86/PNP0501:00`，进一步可以发现，它的 `path` 是 `\_SB_.PC00.LPC0.UAR1`，与 DSDT 中的路径一致。进一步探索，可以发现它匹配到了 Linux 的 `serial` 驱动，并且最终对应到了 `/dev/ttyS0` 设备。还可以看到 Linux 生成的 `resources` 描述：

```
state = active
io 0x3f8-0x3ff
irq 4
dma disabled
```

这和上面看到的是一致的：

```
IO (Decode16,
    0x03F8,             // Range Minimum
    0x03F8,             // Range Maximum
    0x01,               // Alignment
    0x08,               // Length
    )
```

这里表达的正是 `0x3F8-0x3FF` 这一段 IO Port。这个地址和 [OSDev](https://wiki.osdev.org/Serial_Ports#Port_Addresses) 上看到的也是吻合的。

进一步分析代码，`_STA` 函数返回设备当前的状态。可以在 Linux 的 ACPI 结点路径下看 `status` 文件，其内容是 `15`，表示工作正常。实现中，它调用了 `^^SIO1.DSTA(0x00)`，这里的 `^` 表示上一级命名空间。进一步找到 `DSTA` 的实现：

```asl
Method (DSTA, 1, NotSerialized)
{
    ENFG (CGLD (Arg0))
    Local0 = ACTR /* \_SB_.PC00.LPC0.SIO1.ACTR */
    EXFG ()
    If ((Local0 == 0xFF))
    {
        Return (0x00)
    }

    Local0 &= 0x01
    If ((Arg0 < 0x10))
    {
        IOST |= (Local0 << Arg0)
    }

    If (Local0)
    {
        Return (0x0F)
    }
    ElseIf ((Arg0 < 0x10))
    {
        If (((0x01 << Arg0) & IOST))
        {
            Return (0x0D)
        }
        Else
        {
            Return (0x00)
        }
    }
    Else
    {
        Return (0x00)
    }
}
```

可以看到，核心是要判断 `ACTR` 的取值，继续寻找，可以发现 `ACTR` 是一个 SuperIO 的寄存器：

```asl
Name (SP1O, 0x2E)

OperationRegion (IOID, SystemIO, SP1O, 0x02)
Field (IOID, ByteAcc, NoLock, Preserve)
{
    INDX,   8, 
    DATA,   8
}

IndexField (INDX, DATA, ByteAcc, NoLock, Preserve)
{
    // omitted
    ACTR,   8, 
}
```

`ACTR` 寄存器需要通过 0x2E/0x2F 这两个 IO Port 来访问，所以这里使用了 `IndexField`，例如要读取 `ACTR` 的当前值的话，首先要往 `0x2E` 处写入 `ACTR` 的偏移，再从 `0x2F` 处读出当前值。这些寄存器应该就属于 SuperIO 了。目前没有找到 SuperIO 的寄存器定义，就不细究了。

其他的几个函数含义是，`_CRS` 返回当前的资源配置，`_SRS` 可以修改资源配置，`_PRS` 列出可能的资源配置，`_DIS` 禁用设备。

### ARM64

前面看过了 x86_64 平台的串口，是需要通过 IO Port 进行访问的。在 ARM 平台上，则一般是通过 MMIO 访问。搜索内核日志，可以发现内核从 SPCR(Serial Port Console Redirection table) 表获取得到串口的信息：

```dmesg
ACPI: SPCR: console: uart,mmio,0x3f00002f8,115200
```

SPCR 表的内容：

```
[024h 0036   1]               Interface Type : 00
[025h 0037   3]                     Reserved : 000000

[028h 0040  12]         Serial Port Register : [Generic Address Structure]
[028h 0040   1]                     Space ID : 00 [SystemMemory]
[029h 0041   1]                    Bit Width : 08
[02Ah 0042   1]                   Bit Offset : 00
[02Bh 0043   1]         Encoded Access Width : 01 [Byte Access:8]
[02Ch 0044   8]                      Address : 00000003F00002F8

[034h 0052   1]               Interrupt Type : 08
[035h 0053   1]          PCAT-compatible IRQ : 00
[036h 0054   4]                    Interrupt : 000001E4
[03Ah 0058   1]                    Baud Rate : 07
[03Bh 0059   1]                       Parity : 00
[03Ch 0060   1]                    Stop Bits : 01
[03Dh 0061   1]                 Flow Control : 00
[03Eh 0062   1]                Terminal Type : 03
```

SPCR 表的定义可以在 [Serial Port Console Redirection Table (SPCR)](https://learn.microsoft.com/en-us/windows-hardware/drivers/serports/serial-port-console-redirection-table) 处看到：

- Interface Type(00): Full 16550 interface
- Interrupt Type(08): ARMH GIC interrupt (Global System Interrupt)
- Baud Rate(07): 115200
- Terminal Type(03): ANSI

和内核得到的信息是一致的。内核中解析 SPCR 表的函数是 `acpi_sparse_spcr`：

```c
int __init acpi_parse_spcr(bool enable_earlycon, bool enable_console)
{
    // omitted
	if (table->serial_port.space_id == ACPI_ADR_SPACE_SYSTEM_MEMORY) {
        // omitted
		switch (ACPI_ACCESS_BIT_WIDTH((bit_width))) {
		case 8:
			iotype = "mmio";
			break;
		}
    }

	switch (table->interface_type) {
        // omitted
	case ACPI_DBG2_16550_COMPATIBLE:
		uart = "uart";
		break;
	}

	switch (table->baud_rate) {
        // omitted
	case 7:
		baud_rate = 115200;
		break;
	}

	if (!baud_rate) {
		snprintf(opts, sizeof(opts), "%s,%s,0x%llx", uart, iotype,
			 table->serial_port.address);
	} else {
        // uart,mmio,0x3f00002f8,115200
		snprintf(opts, sizeof(opts), "%s,%s,0x%llx,%d", uart, iotype,
			 table->serial_port.address, baud_rate);
	}

    // omitted
}
```

## IPMI

### x86_64

接下来，再来看 ACPI 中是如何声明 IPMI 的。主板依然是 `WS X299 PRO/SE`，主板自带了 BMC，可以在 DSDT 中搜到相关的部分：

```asl
Name (IDTP, 0x0CA2)
Name (ICDP, 0x0CA3)

Device (SPMI)
{
    Name (_HID, EisaId ("IPI0001"))  // _HID: Hardware ID
    Name (_STR, Unicode ("IPMI_KCS"))  // _STR: Description String
    Name (_UID, 0x00)  // _UID: Unique ID
    OperationRegion (IPST, SystemIO, ICDP, 0x01)
    Field (IPST, ByteAcc, NoLock, Preserve)
    {
        STAS,   8
    }

    Method (_STA, 0, NotSerialized)  // _STA: Status
    {
        Local0 = STAS /* \_SB_.PC00.LPC0.SPMI.STAS */
        If ((Local0 == 0xFF))
        {
            Return (0x00)
        }
        Else
        {
            Return (0x0F)
        }
    }

    Name (ICRS, ResourceTemplate ()
    {
        IO (Decode16,
            0x0000,             // Range Minimum
            0x0000,             // Range Maximum
            0x00,               // Alignment
            0x00,               // Length
            _Y1E)
        IO (Decode16,
            0x0000,             // Range Minimum
            0x0000,             // Range Maximum
            0x00,               // Alignment
            0x00,               // Length
            _Y1F)
    })
    Method (_CRS, 0, NotSerialized)  // _CRS: Current Resource Settings
    {
        If (IDTP)
        {
            CreateWordField (ICRS, \_SB.PC00.LPC0.SPMI._Y1E._MIN, IPDB)  // _MIN: Minimum Base Address
            CreateWordField (ICRS, \_SB.PC00.LPC0.SPMI._Y1E._MAX, IPDH)  // _MAX: Maximum Base Address
            CreateByteField (ICRS, \_SB.PC00.LPC0.SPMI._Y1E._LEN, IPDL)  // _LEN: Length
            IPDB = IDTP /* \IDTP */
            IPDH = IDTP /* \IDTP */
            IPDL = 0x01
        }

        If (ICDP)
        {
            CreateWordField (ICRS, \_SB.PC00.LPC0.SPMI._Y1F._MIN, IPCB)  // _MIN: Minimum Base Address
            CreateWordField (ICRS, \_SB.PC00.LPC0.SPMI._Y1F._MAX, IPCH)  // _MAX: Maximum Base Address
            CreateByteField (ICRS, \_SB.PC00.LPC0.SPMI._Y1F._LEN, IPCL)  // _LEN: Length
            IPCB = ICDP /* \ICDP */
            IPCH = ICDP /* \ICDP */
            IPCL = 0x01
        }

        Return (ICRS) /* \_SB_.PC00.LPC0.SPMI.ICRS */
    }

    Method (_IFT, 0, NotSerialized)  // _IFT: IPMI Interface Type
    {
        Return (0x01)
    }

    Method (_SRV, 0, NotSerialized)  // _SRV: IPMI Spec Revision
    {
        Return (SRVV) /* \SRVV */
    }
}
```

在 Linux 中可以找到相应的结点：`/sys/devices/LNXSYSTM:00/LNXSYBUS:00/PNP0A08:00/device:86/IPI0001:00`。可以发现匹配到了 `ipmi_si` 驱动，并且可以正常工作。

函数 `_STA` 返回设备的当前状态，它读取了 IO Port 0x0CA3 的内容，进而判断 IPMI 是否正常。

函数 `_CRS` 返回当前的资源配置，它动态地计算出一个资源配置，对应 IO Port 是 0x0CA2 或者 0x0CA3。

函数 `_IFT` 返回 IPMI Interface Type，0x01 表示 KCS，`_SRV` 返回 IPMI Spec Revision，在这里是 0x0200，也就是 IPMI 2.0。

这些内容可以在 Linux 下 ACPI 结点的 `physical_node/params` 文件中看到：`kcs,i/o,0xca2,rsp=1,rsi=1,rsh=0,irq=0,ipmb=32`。

查阅 Linux 源码，可以找到 `acpi_ipmi_probe` 函数，这个函数负责从 ACPI 中寻找 IPMI 配置：

```c
static int acpi_ipmi_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct si_sm_io io;
	acpi_handle handle;
	acpi_status status;
	unsigned long long tmp;
	struct resource *res;

	if (!si_tryacpi)
		return -ENODEV;

	handle = ACPI_HANDLE(dev);
	if (!handle)
		return -ENODEV;

	memset(&io, 0, sizeof(io));
	io.addr_source = SI_ACPI;
	dev_info(dev, "probing via ACPI\n");

	io.addr_info.acpi_info.acpi_handle = handle;

	/* _IFT tells us the interface type: KCS, BT, etc */
	status = acpi_evaluate_integer(handle, "_IFT", NULL, &tmp);
	if (ACPI_FAILURE(status)) {
		dev_err(dev, "Could not find ACPI IPMI interface type\n");
		return -EINVAL;
	}

	switch (tmp) {
	case 1:
		io.si_type = SI_KCS;
		break;
	case 2:
		io.si_type = SI_SMIC;
		break;
	case 3:
		io.si_type = SI_BT;
		break;
	case 4: /* SSIF, just ignore */
		return -ENODEV;
	default:
		dev_info(dev, "unknown IPMI type %lld\n", tmp);
		return -EINVAL;
	}

	io.dev = dev;
	io.regsize = DEFAULT_REGSIZE;
	io.regshift = 0;

	res = ipmi_get_info_from_resources(pdev, &io);
	if (!res)
		return -EINVAL;

	/* If _GPE exists, use it; otherwise use standard interrupts */
	status = acpi_evaluate_integer(handle, "_GPE", NULL, &tmp);
	if (ACPI_SUCCESS(status)) {
		io.irq = tmp;
		io.irq_setup = acpi_gpe_irq_setup;
	} else {
		int irq = platform_get_irq_optional(pdev, 0);

		if (irq > 0) {
			io.irq = irq;
			io.irq_setup = ipmi_std_irq_setup;
		}
	}

	io.slave_addr = find_slave_address(&io, io.slave_addr);

	dev_info(dev, "%pR regsize %d spacing %d irq %d\n",
		 res, io.regsize, io.regspacing, io.irq);

	request_module("acpi_ipmi");

	return ipmi_si_add_smi(&io);
}

static const struct acpi_device_id acpi_ipmi_match[] = {
	{ "IPI0001", 0 },
	{ },
};
```

和上面的分析是可以对上的。

### ARM64

再看一个 ARM64 平台上的 IPMI：

```
Device (IPI0)
{
    Name (_HID, "IPI0001")  // _HID: Hardware ID
    Method (_IFT, 0, NotSerialized)  // _IFT: IPMI Interface Type
    {
        Return (0x03)
    }

    Name (_CRS, ResourceTemplate ()  // _CRS: Current Resource Settings
    {
        QWordMemory (ResourceConsumer, PosDecode, MinFixed, MaxFixed, Cacheable, ReadWrite,
            0x0000000000000000, // Granularity
            0x00000003F00000E4, // Range Minimum
            0x00000003F00000E7, // Range Maximum
            0x0000000000000000, // Translation Offset
            0x0000000000000004, // Length
            ,, , AddressRangeMemory, TypeStatic)
        Interrupt (ResourceConsumer, Level, ActiveHigh, Shared, ,, )
        {
            0x000001E4,
        }
    })
}
```

这里的 `_IFT` 返回值是 0x3，查阅文档可知这表示的是 BT 类型。`_CRS` 中使用了 QWordMemory 宏来描述地址空间，这里实际上就是表示内存地址 `0x3F00000E4-0x3F00000E7`。

## IO APIC

在 DSDT 中，可以找到 IO APIC 的基地址：

```asl
Device (APIC)
{
    Name (_HID, EisaId ("PNP0003") /* IO-APIC Interrupt Controller */)  // _HID: Hardware ID
    Name (_CRS, ResourceTemplate ()  // _CRS: Current Resource Settings
    {
        Memory32Fixed (ReadOnly,
            0xFEC00000,         // Address Base
            0x00100000,         // Address Length
            )
    })
}
```

可以看到 IO APIC 基地址是 0xFEC00000，在网上也可以查到同样的结果。实际上，在 Multiple APIC Description Table (MADT) 中也可以找到 IO APIC 的基地址：

```
[1ECh 0492   1]                Subtable Type : 01 [I/O APIC]
[1EDh 0493   1]                       Length : 0C
[1EEh 0494   1]                  I/O Apic ID : 08
[1EFh 0495   1]                     Reserved : 00
[1F0h 0496   4]                      Address : FEC00000
[1F4h 0500   4]                    Interrupt : 00000000

[1F8h 0504   1]                Subtable Type : 01 [I/O APIC]
[1F9h 0505   1]                       Length : 0C
[1FAh 0506   1]                  I/O Apic ID : 09
[1FBh 0507   1]                     Reserved : 00
[1FCh 0508   4]                      Address : FEC01000
[200h 0512   4]                    Interrupt : 00000018

[204h 0516   1]                Subtable Type : 01 [I/O APIC]
[205h 0517   1]                       Length : 0C
[206h 0518   1]                  I/O Apic ID : 0A
[207h 0519   1]                     Reserved : 00
[208h 0520   4]                      Address : FEC08000
[20Ch 0524   4]                    Interrupt : 00000020

[210h 0528   1]                Subtable Type : 01 [I/O APIC]
[211h 0529   1]                       Length : 0C
[212h 0530   1]                  I/O Apic ID : 0B
[213h 0531   1]                     Reserved : 00
[214h 0532   4]                      Address : FEC10000
[218h 0536   4]                    Interrupt : 00000028

[21Ch 0540   1]                Subtable Type : 01 [I/O APIC]
[21Dh 0541   1]                       Length : 0C
[21Eh 0542   1]                  I/O Apic ID : 0C
[21Fh 0543   1]                     Reserved : 00
[220h 0544   4]                      Address : FEC18000
[224h 0548   4]                    Interrupt : 00000030
```

## DMA

继续搜索 `_HID`，还可以找到一些传统的设备，比如 DMA Controller：

```asl
Device (DMAC)
{
    Name (_HID, EisaId ("PNP0200") /* PC-class DMA Controller */)  // _HID: Hardware ID
    Name (_CRS, ResourceTemplate ()  // _CRS: Current Resource Settings
    {
        IO (Decode16,
            0x0000,             // Range Minimum
            0x0000,             // Range Maximum
            0x00,               // Alignment
            0x10,               // Length
            )
        IO (Decode16,
            0x0081,             // Range Minimum
            0x0081,             // Range Maximum
            0x00,               // Alignment
            0x03,               // Length
            )
        IO (Decode16,
            0x0087,             // Range Minimum
            0x0087,             // Range Maximum
            0x00,               // Alignment
            0x01,               // Length
            )
        IO (Decode16,
            0x0089,             // Range Minimum
            0x0089,             // Range Maximum
            0x00,               // Alignment
            0x03,               // Length
            )
        IO (Decode16,
            0x008F,             // Range Minimum
            0x008F,             // Range Maximum
            0x00,               // Alignment
            0x01,               // Length
            )
        IO (Decode16,
            0x00C0,             // Range Minimum
            0x00C0,             // Range Maximum
            0x00,               // Alignment
            0x20,               // Length
            )
        DMA (Compatibility, NotBusMaster, Transfer8, )
            {4}
    })
}
```

可以看到，它定义了如下的 IO Port 范围：

- `0x00-0x0F`
- 0x81, 0x87, 0x89, 0x8F
- `0xC0-0xDE`

寄存器定义可以在 [ISA DMA - OSDev](https://wiki.osdev.org/ISA_DMA) 处找到。

## CMOS/RTC

经典的 CMOS/RTC 的 IO 端口定义也可以找到：

```
Device (RTC)
{
    Name (_HID, EisaId ("PNP0B00") /* AT Real-Time Clock */)  // _HID: Hardware ID
    Name (_CRS, ResourceTemplate ()  // _CRS: Current Resource Settings
    {
        IO (Decode16,
            0x0070,             // Range Minimum
            0x0070,             // Range Maximum
            0x01,               // Alignment
            0x02,               // Length
            )
        IO (Decode16,
            0x0074,             // Range Minimum
            0x0074,             // Range Maximum
            0x01,               // Alignment
            0x04,               // Length
            )
        IRQNoFlags ()
            {8}
    })
    Method (_STA, 0, NotSerialized)  // _STA: Status
    {
        If ((STAS == 0x01))
        {
            Return (0x0F)
        }
        Else
        {
            Return (0x00)
        }
    }
}
```

可以看到，它的 IO Port 是 0x70-0x71 和 0x74-0x78，中断号 8，和 [CMOS - OSDev](https://wiki.osdev.org/CMOS) 是一致的。

## 启动图片

启动图片以 BMP 格式保存在内存中，基地址记录在 BGRT 表中。可以直接从 `/sys/firmware/acpi/bgrt/image` 获取启动的图片内容。


## PCIe

### Root Bridge

PCIe 总线是自带枚举功能的，所以只需要找到 Root Bridge，其他设备都可以枚举出来。而 ACPI 就提供了寻找 Root Bridge 的方法。

搜索 `PNP0A08` 可以找到 PCIe 总线：

```asl
Device (PC00)
{
    Name (_HID, EisaId ("PNP0A08") /* PCI Express Bus */)  // _HID: Hardware ID
    Name (_CID, EisaId ("PNP0A03") /* PCI Bus */)  // _CID: Compatible ID

    Name (P0RS, ResourceTemplate ()
    {
        WordBusNumber (ResourceProducer, MinFixed, MaxFixed, PosDecode,
            0x0000,             // Granularity
            0x0000,             // Range Minimum
            0x0015,             // Range Maximum
            0x0000,             // Translation Offset
            0x0016,             // Length
            ,, )
        IO (Decode16,
            0x0CF8,             // Range Minimum
            0x0CF8,             // Range Maximum
            0x01,               // Alignment
            0x08,               // Length
            )
        WordIO (ResourceProducer, MinFixed, MaxFixed, PosDecode, EntireRange,
            0x0000,             // Granularity
            0x0000,             // Range Minimum
            0x0CF7,             // Range Maximum
            0x0000,             // Translation Offset
            0x0CF8,             // Length
            ,, , TypeStatic, DenseTranslation)
        WordIO (ResourceProducer, MinFixed, MaxFixed, PosDecode, EntireRange,
            0x0000,             // Granularity
            0x1000,             // Range Minimum
            0x57FF,             // Range Maximum
            0x0000,             // Translation Offset
            0x4800,             // Length
            ,, , TypeStatic, DenseTranslation)
        DWordMemory (ResourceProducer, PosDecode, MinFixed, MaxFixed, Cacheable, ReadWrite,
            0x00000000,         // Granularity
            0x000A0000,         // Range Minimum
            0x000BFFFF,         // Range Maximum
            0x00000000,         // Translation Offset
            0x00020000,         // Length
            ,, , AddressRangeMemory, TypeStatic)
        DWordMemory (ResourceProducer, PosDecode, MinFixed, MaxFixed, Cacheable, ReadWrite,
            0x00000000,         // Granularity
            0x00000000,         // Range Minimum
            0x00000000,         // Range Maximum
            0x00000000,         // Translation Offset
            0x00000000,         // Length
            ,, _Y00, AddressRangeMemory, TypeStatic)
        DWordMemory (ResourceProducer, PosDecode, MinFixed, MaxFixed, NonCacheable, ReadWrite,
            0x00000000,         // Granularity
            0xFE010000,         // Range Minimum
            0xFE010FFF,         // Range Maximum
            0x00000000,         // Translation Offset
            0x00001000,         // Length
            ,, , AddressRangeMemory, TypeStatic)
        DWordMemory (ResourceProducer, PosDecode, MinFixed, MaxFixed, NonCacheable, ReadWrite,
            0x00000000,         // Granularity
            0xFD000000,         // Range Minimum
            0xFE7FFFFF,         // Range Maximum
            0x00000000,         // Translation Offset
            0x01800000,         // Length
            ,, , AddressRangeMemory, TypeStatic)
        DWordMemory (ResourceProducer, PosDecode, MinFixed, MaxFixed, NonCacheable, ReadWrite,
            0x00000000,         // Granularity
            0x70000000,         // Range Minimum
            0x92FFFFFF,         // Range Maximum
            0x00000000,         // Translation Offset
            0x23000000,         // Length
            ,, , AddressRangeMemory, TypeStatic)
        QWordMemory (ResourceProducer, PosDecode, MinFixed, MaxFixed, NonCacheable, ReadWrite,
            0x0000000000000000, // Granularity
            0x0000000000000000, // Range Minimum
            0x0000000000000000, // Range Maximum
            0x0000000000000000, // Translation Offset
            0x0000000000000000, // Length
            ,, , AddressRangeMemory, TypeStatic)
    })

    Method (_CRS, 0, NotSerialized)  // _CRS: Current Resource Settings
    {
        EROM ()
        Return (P0RS) /* \_SB_.PC00.P0RS */
    }
}
```

上面省略掉了很多内容，不过可以看到 Root Bridge 的资源，这部分内容和 Linux 的 dmesg 是一致的：

```
ACPI: PCI Root Bridge [PC00] (domain 0000 [bus 00-15])
acpi PNP0A08:00: _OSC: OS supports [ExtendedConfig ASPM ClockPM Segments MSI]
acpi PNP0A08:00: _OSC: platform does not support [SHPCHotplug AER LTR]
acpi PNP0A08:00: _OSC: OS now controls [PCIeHotplug PME PCIeCapability]
acpi PNP0A08:00: host bridge window expanded to [mem 0xfd000000-0xfe7fffff window]; [mem 0xfd000000-0xfe7fffff window] ignored
PCI host bridge to bus 0000:00
pci_bus 0000:00: root bus resource [io  0x0000-0x0cf7 window]
pci_bus 0000:00: root bus resource [io  0x1000-0x57ff window]
pci_bus 0000:00: root bus resource [mem 0x000a0000-0x000bffff window]
pci_bus 0000:00: root bus resource [mem 0x000c4000-0x000c7fff window]
pci_bus 0000:00: root bus resource [mem 0xfd000000-0xfe7fffff window]
pci_bus 0000:00: root bus resource [mem 0x70000000-0x92ffffff window]
pci_bus 0000:00: root bus resource [bus 00-15]
```

Linux 相关代码在 `acpi_pci_root_create` 函数中：

```c
struct pci_bus *acpi_pci_root_create(struct acpi_pci_root *root,
				     struct acpi_pci_root_ops *ops,
				     struct acpi_pci_root_info *info,
				     void *sysdata)
{
    // omitted
    ret = acpi_pci_probe_root_resources(info);
    // omitted
    pci_acpi_root_add_resources(info);
	pci_add_resource(&info->resources, &root->secondary);
	bus = pci_create_root_bus(NULL, busnum, ops->pci_ops,
				  sysdata, &info->resources);
}
```

### MCFG

除了上面的 Root Bridge 以外，还有一个很重要的问题是，如何访问 PCIe 的 Configuration Space。传统的办法是通过 IO Port 0xCF8 和 0xCFC，但是这个方法慢，并且有局限性。而较新的办法是 Enhanced Configuration Access Mechanism (ECAM)，把 PCIe 设备的 Configuration Space 映射到内存中，那么就需要一个基地址。这个基地址是在 MCFG 表中给出的：

```asl
[02Ch 0044   8]                 Base Address : 0000000060000000
[034h 0052   2]         Segment Group Number : 0000
[036h 0054   1]             Start Bus Number : 00
[037h 0055   1]               End Bus Number : FF
[038h 0056   4]                     Reserved : 00000000
```

内核输出：

```
PCI: MMCONFIG for domain 0000 [bus 00-ff] at [mem 0x60000000-0x6fffffff] (base 0x60000000)
PCI: MMCONFIG at [mem 0x60000000-0x6fffffff] reserved in E820
```

有了这个信息以后，就可以计算出要访问 Configuration Space 时 MMIO 的地址了：

![](/images/pcie_ecam.png)

### 相关文档

Linux 的文档 [ACPI considerations for PCI host bridges](https://docs.kernel.org/PCI/acpi-info.html) 对 ACPI PCIe 描述的比较详细，摘录如下：

    The general rule is that the ACPI namespace should describe everything the
    OS might use unless there’s another way for the OS to find it [1, 2].

    For example, there’s no standard hardware mechanism for enumerating PCI host
    bridges, so the ACPI namespace must describe each host bridge, the method
    for accessing PCI config space below it, the address space windows the host
    bridge forwards to PCI (using _CRS), and the routing of legacy INTx
    interrupts (using _PRT).
    
    PCI devices, which are below the host bridge, generally do not need to be
    described via ACPI. The OS can discover them via the standard PCI
    enumeration mechanism, using config accesses to discover and identify
    devices and read and size their BARs. However, ACPI may describe PCI devices
    if it provides power management or hotplug functionality for them or if the
    device has INTx interrupts connected by platform interrupt controllers and a
    _PRT is needed to describe those connections.

文档和上面讲的是一致的，对于 PCIe 自己可以枚举出来的，ACPI 就不需要再重复；但是枚举需要首先知道有哪些 Root Bridge 以及 ECAM 的基地址，这个信息只能由 ACPI 来提供。

    The PCIe spec requires the Enhanced Configuration Access Method (ECAM)
    unless there’s a standard firmware interface for config access, e.g., the
    ia64 SAL interface [7]. A host bridge consumes ECAM memory address space and
    converts memory accesses into PCI configuration accesses. The spec defines
    the ECAM address space layout and functionality; only the base of the
    address space is device-specific. An ACPI OS learns the base address from
    either the static MCFG table or a _CBA method in the PNP0A03 device.

这一段讲的其实就是 ECAM 与 MCFG 的关系。

## 修改 ACPI 表内容

想要修改 ACPI 表内容，最根本的办法是修改固件，但是修改起来比较麻烦。Linux 提供了一些方法来运行时打补丁：

- [Upgrading ACPI tables via initrd](https://www.kernel.org/doc/html/latest/admin-guide/acpi/initrd_table_override.html)：覆盖 ACPI 表
- [SSDT Overlays](https://www.kernel.org/doc/html/latest/admin-guide/acpi/ssdt-overlays.html)：添加额外的 SSDT 表，类似 DT Overlay

在黑苹果中，一般则是在 Bootloader(Clover/OpenCore) 一步把 ACPI 表修改了，如 [How to Patch Laptop DSDT and SSDTs](https://elitemacx86.com/threads/how-to-patch-laptop-dsdt-and-ssdts.178/。
