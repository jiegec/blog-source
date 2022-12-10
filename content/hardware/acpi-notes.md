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

## IPMI

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
