---
layout: post
date: 2023-07-24
tags: [linux,pcie,driver,vfio]
categories:
    - software
---

# VFIO - Virtual Function I/O

## 背景

VFIO 是 Linux 内核中的一个功能，目的是把 PCIe 设备暴露给用户态的程序，进而可以暴露给虚拟机内的系统，也就是常说的虚拟机 PCIe 直通。为了保证安全性，VFIO 还会配置好 IOMMU，保证用户态程序无法利用设备的 DMA 访问到其他地址空间的数据。

本文探讨 VFIO 暴露的用户态 API 以及如何在用户态中使用 VFIO 直接控制 PCIe 设备。

<!-- more -->

推荐阅读 [VFIO 官方文档](https://docs.kernel.org/driver-api/vfio.html)，下面的例子也参考了这个文档。

## 需求

在探讨 VFIO 提供哪些接口之前，首先要考虑到在用户态操作 PCIe 设备的需求：例如在用户态要操作一个网卡，那肯定需要相应的网卡驱动，那么网卡驱动需要做的事情有：

1. 初始化硬件，为了读写寄存器，需要能够访问 PCIe 设备的 BAR 空间，BAR 空间的物理地址提前已经分配好了，在内核中直接把物理地址转换为内核态的虚拟地址就可以访问了；为了配置中断等 PCIe 的功能，需要能够访问 PCIe 设备的 Configuration 空间，在内核中按 PCIe ECAM 方法计算出物理地址，然后转换为虚拟地址也就可以访问了
2. 发送数据，需要在内存里准备好数据，让网卡进行 DMA，意味着需要知道在内存中分配的数据的物理地址；同理，接收数据的时候，要在内存里分配好缓冲区，把物理地址交给网卡，让网卡 DMA
3. 设置中断，例如配置 PCIe 的 MSI/MSI-X 功能，然后在内核的中断处理代码里注册相应的处理函数；当 PCIe 设备通过 MSI/MSI-X 发送中断给中断控制器的时候，内核最终要能把这个中断路由给网卡驱动

简单总结一下，包括如下的需求：

1. 访问 Configuration 空间和 BAR 空间
2. 对于需要 DMA 的内存区域，可以得到它的物理地址（有了 IOMMU 以后是设备虚拟地址 IOVA），让硬件去读写内存
3. 可以注册中断，当设备发送中断的时候，驱动的中断处理函数会被调用

因此 VFIO 也应该提供以上的这些功能。额外地，为了保证安全性，在第二步的时候，需要和 IOMMU 打配合，保证 PCIe 设备只能看到用户程序向 VFIO 上注册的内存区域。

## IOMMU

IOMMU 是需要硬件支持的，因此 VFIO 的实现会受制于硬件的 IOMMU 实现。IOMMU 在硬件上的实现方式类似 CPU 上的 MMU，只不过对象是 PCIe 设备，当 PCIe 设备在发起内存读写请求的时候，需要经过 IOMMU，IOMMU 按照预先配置好的设定进行地址转换，如果转换不成功，那就拒绝请求，保证了安全性。

但是有些情况下 IOMMU 不能保证给每个设备都单独一个地址转换，也就是说，不能保证把每个设备的地址空间都隔离开，可能有若干个设备需要共享同一个地址空间映射。此时这些共享地址空间的设备就组成一个 IOMMU Group，Group 内的设备不隔离，Group 之间隔离。

于是同一个 IOMMU Group 内的设备不能让用户态程序和内核态驱动（非 VFIO）混用：同一个 Group 内不保证隔离，如果混用了，用户态程序就可以通过 PCIe 设备访问内核态驱动的数据了。

IOMMU Group 只是地址隔离的最小粒度。有些时候，程序希望同时控制多个 PCIe 设备，它们分处不同的 IOMMU Group，如果要逐个 IOMMU Group 配置过去，未免有点麻烦。此时 VFIO 也提供了更高一级的抽象：Container。Container 包括多个 Group，这些 Group 共享同样的地址空间。换句话说，硬件上支持隔离，但反正是同一个程序，那就人为地让它不隔离。

总而言之，VFIO 考虑到 IOMMU 的物理限制，设计了三个层级：

- Device：实际的 PCIe 设备
- Group：IOMMU 隔离地址空间的粒度
- Container：为了软件上方便同时操作多个 Group

## 用户 API

VFIO 的用户 API 在 [include/uapi/linux/vfio.h](https://github.com/torvalds/linux/blob/master/include/uapi/linux/vfio.h) 中定义，形式是若干个 ioctl 调用，大致的初始化流程如下：

1. 把 vfio-pci 设备绑定在 PCIe 设备上
2. 根据 PCIe 设备，找到它所属的 IOMMU Group ID，例如是 26
3. 创建一个 Container：`container = open("/dev/vfio/vfio")`
4. 打开 IOMMU Group：`group = open("/dev/vfio/2")`
5. 把 Group 放到 Container 中：`ioctl(group, VFIO_GROUP_SET_CONTAINER, &container)`
6. 打开 Group 中的 Device：`device = ioctl(group, VFIO_GROUP_GET_DEVICE_FD, "0000:06:0d.0")`

上面的初始化过程忽略了一部分调用，详情请阅读 VFIO 文档。

有了 Container，Group 和 Device 的 FD 以后，可以做以下的事情：

1. 对 Container 设置 DMA 映射：`ioctl(container, VFIO_IOMMU_MAP_DMA, &dma_Map)`
2. 把 Device 的 BAR 空间映射到用户态：`ioctl(device, VFIO_DEVICE_GET_REGION_INFO, &reg)` 之后 `mmap`
3. 读写 Device 的 Configuration 空间：`ioctl(device, VFIO_DEVICE_GET_REGION_INFO, &reg)` 得到 Configuration 空间的偏移，把 Device FD 当成文件，用 `pread/pwrite` 在指定偏移上进行读写
4. 设置中断：`ioctl(device, VFIO_DEVICE_SET_IRQS, irq_set)`，参数中包括了一个 eventfd，当内核收到来自设备的中断时，更新 eventfd，用户态可以通过 epoll 监测 eventfd 的更新

回顾一下文章开头讲到的驱动对 VFIO 的需求：

1. 访问 Configuration 空间：通过 `pread/pwrite` 读写
2. 访问 BAR 空间：`mmap` 到用户态的虚拟地址，然后直接 MMIO
3. DMA：配置用户态虚拟地址和设备虚拟地址（IOVA）的映射，然后把 IOVA 传给设备，设备在 DMA 的时候，IOMMU 负责把 IOVA 转换为实际的物理地址
4. 中断：配置 MSI/MSI-X，设备发送中断时，内核通过 eventfd 通知用户态程序

可见这些需求都已经满足，可以在用户态实现设备驱动。

## QEMU

### 初始化

接下来分析 QEMU 是如何通过 VFIO 实现 PCIe 设备直通的。在命令行中，可以用 `-device vfio-pci` 来添加直通设备，每个设备对应一个 `VFIOPCIDevice` 结构体：

```c
#define TYPE_VFIO_PCI "vfio-pci"
OBJECT_DECLARE_SIMPLE_TYPE(VFIOPCIDevice, VFIO_PCI)

struct VFIOPCIDevice {
    PCIDevice pdev;
    VFIODevice vbasedev;
    VFIOINTx intx;
    unsigned int config_size;
    uint8_t *emulated_config_bits; /* QEMU emulated bits, little-endian */
    off_t config_offset; /* Offset of config space region within device fd */
    unsigned int rom_size;
    off_t rom_offset; /* Offset of ROM region within device fd */
    void *rom;
    int msi_cap_size;
    VFIOMSIVector *msi_vectors;
    VFIOMSIXInfo *msix;
    int nr_vectors; /* Number of MSI/MSIX vectors currently in use */
    int interrupt; /* Current interrupt type */
    VFIOBAR bars[PCI_NUM_REGIONS - 1]; /* No ROM */
    VFIOVGA *vga; /* 0xa0000, 0x3b0, 0x3c0 */
    void *igd_opregion;
    PCIHostDeviceAddress host;
    QemuUUID vf_token;
    EventNotifier err_notifier;
    EventNotifier req_notifier;
    int (*resetfn)(struct VFIOPCIDevice *);
    uint32_t vendor_id;
    uint32_t device_id;
    uint32_t sub_vendor_id;
    uint32_t sub_device_id;
    uint32_t features;
#define VFIO_FEATURE_ENABLE_VGA_BIT 0
#define VFIO_FEATURE_ENABLE_VGA (1 << VFIO_FEATURE_ENABLE_VGA_BIT)
#define VFIO_FEATURE_ENABLE_REQ_BIT 1
#define VFIO_FEATURE_ENABLE_REQ (1 << VFIO_FEATURE_ENABLE_REQ_BIT)
#define VFIO_FEATURE_ENABLE_IGD_OPREGION_BIT 2
#define VFIO_FEATURE_ENABLE_IGD_OPREGION \
                                (1 << VFIO_FEATURE_ENABLE_IGD_OPREGION_BIT)
    OnOffAuto display;
    uint32_t display_xres;
    uint32_t display_yres;
    int32_t bootindex;
    uint32_t igd_gms;
    OffAutoPCIBAR msix_relo;
    uint8_t pm_cap;
    uint8_t nv_gpudirect_clique;
    bool pci_aer;
    bool req_enabled;
    bool has_flr;
    bool has_pm_reset;
    bool rom_read_failed;
    bool no_kvm_intx;
    bool no_kvm_msi;
    bool no_kvm_msix;
    bool no_geforce_quirks;
    bool no_kvm_ioeventfd;
    bool no_vfio_ioeventfd;
    bool enable_ramfb;
    bool defer_kvm_irq_routing;
    bool clear_parent_atomics_on_exit;
    VFIODisplay *dpy;
    Notifier irqchip_change_notifier;
};

static Property vfio_pci_dev_properties[] = {
    DEFINE_PROP_PCI_HOST_DEVADDR("host", VFIOPCIDevice, host),
    DEFINE_PROP_UUID_NODEFAULT("vf-token", VFIOPCIDevice, vf_token),
    DEFINE_PROP_STRING("sysfsdev", VFIOPCIDevice, vbasedev.sysfsdev),
    DEFINE_PROP_ON_OFF_AUTO("x-pre-copy-dirty-page-tracking", VFIOPCIDevice,
                            vbasedev.pre_copy_dirty_page_tracking,
                            ON_OFF_AUTO_ON),
    DEFINE_PROP_ON_OFF_AUTO("display", VFIOPCIDevice,
                            display, ON_OFF_AUTO_OFF),
    DEFINE_PROP_UINT32("xres", VFIOPCIDevice, display_xres, 0),
    DEFINE_PROP_UINT32("yres", VFIOPCIDevice, display_yres, 0),
    DEFINE_PROP_UINT32("x-intx-mmap-timeout-ms", VFIOPCIDevice,
                       intx.mmap_timeout, 1100),
    DEFINE_PROP_BIT("x-vga", VFIOPCIDevice, features,
                    VFIO_FEATURE_ENABLE_VGA_BIT, false),
    DEFINE_PROP_BIT("x-req", VFIOPCIDevice, features,
                    VFIO_FEATURE_ENABLE_REQ_BIT, true),
    DEFINE_PROP_BIT("x-igd-opregion", VFIOPCIDevice, features,
                    VFIO_FEATURE_ENABLE_IGD_OPREGION_BIT, false),
    DEFINE_PROP_ON_OFF_AUTO("enable-migration", VFIOPCIDevice,
                            vbasedev.enable_migration, ON_OFF_AUTO_AUTO),
    DEFINE_PROP_BOOL("x-no-mmap", VFIOPCIDevice, vbasedev.no_mmap, false),
    DEFINE_PROP_BOOL("x-balloon-allowed", VFIOPCIDevice,
                     vbasedev.ram_block_discard_allowed, false),
    DEFINE_PROP_BOOL("x-no-kvm-intx", VFIOPCIDevice, no_kvm_intx, false),
    DEFINE_PROP_BOOL("x-no-kvm-msi", VFIOPCIDevice, no_kvm_msi, false),
    DEFINE_PROP_BOOL("x-no-kvm-msix", VFIOPCIDevice, no_kvm_msix, false),
    DEFINE_PROP_BOOL("x-no-geforce-quirks", VFIOPCIDevice,
                     no_geforce_quirks, false),
    DEFINE_PROP_BOOL("x-no-kvm-ioeventfd", VFIOPCIDevice, no_kvm_ioeventfd,
                     false),
    DEFINE_PROP_BOOL("x-no-vfio-ioeventfd", VFIOPCIDevice, no_vfio_ioeventfd,
                     false),
    DEFINE_PROP_UINT32("x-pci-vendor-id", VFIOPCIDevice, vendor_id, PCI_ANY_ID),
    DEFINE_PROP_UINT32("x-pci-device-id", VFIOPCIDevice, device_id, PCI_ANY_ID),
    DEFINE_PROP_UINT32("x-pci-sub-vendor-id", VFIOPCIDevice,
                       sub_vendor_id, PCI_ANY_ID),
    DEFINE_PROP_UINT32("x-pci-sub-device-id", VFIOPCIDevice,
                       sub_device_id, PCI_ANY_ID),
    DEFINE_PROP_UINT32("x-igd-gms", VFIOPCIDevice, igd_gms, 0),
    DEFINE_PROP_UNSIGNED_NODEFAULT("x-nv-gpudirect-clique", VFIOPCIDevice,
                                   nv_gpudirect_clique,
                                   qdev_prop_nv_gpudirect_clique, uint8_t),
    DEFINE_PROP_OFF_AUTO_PCIBAR("x-msix-relocation", VFIOPCIDevice, msix_relo,
                                OFF_AUTOPCIBAR_OFF),
    /*
     * TODO - support passed fds... is this necessary?
     * DEFINE_PROP_STRING("vfiofd", VFIOPCIDevice, vfiofd_name),
     * DEFINE_PROP_STRING("vfiogroupfd, VFIOPCIDevice, vfiogroupfd_name),
     */
    DEFINE_PROP_END_OF_LIST(),
};
```

QEMU 解析命令行以后，就会把命令行里传给 `-device vfio-pci` 的额外参数填入到结构体对应字段当中。另一方面，QEMU 也会把 VFIOPCIDevice 作为 PCIe 设备挂载到 QEMU 的虚拟 PCIe 总线上。在初始化 PCIe 的时候，就会调用 `vfio_realize` 函数，下面列出了 `vfio_realize` 的实现中比较重要的部分：

```c
static void vfio_realize(PCIDevice *pdev, Error **errp)
{
    // locate device in sysfs
    vbasedev->sysfsdev =
        g_strdup_printf("/sys/bus/pci/devices/%04x:%02x:%02x.%01x",
                        vdev->host.domain, vdev->host.bus,
                        vdev->host.slot, vdev->host.function);

    // locate iommu group via sysfs
    tmp = g_strdup_printf("%s/iommu_group", vbasedev->sysfsdev);
    len = readlink(tmp, group_path, sizeof(group_path));

    // open /dev/vfio/$group_id and bind to container
    group = vfio_get_group(groupid, pci_device_iommu_address_space(pdev), errp);

    // get device fd
    ret = vfio_get_device(group, name, vbasedev, errp);

    // initialize device
    vfio_populate_device(vdev, &err);

    // mmap BAR spaces
    vfio_bars_register(vdev);
}
```

### BAR 空间

在映射 Memory-Mapped 的 BAR 空间的时候，QEMU 会在虚拟机内的物理地址空间内分配相应的空间，并且设置读写回调函数：

```c
static void vfio_populate_device(VFIOPCIDevice *vdev, Error **errp)
{
    for (i = VFIO_PCI_BAR0_REGION_INDEX; i < VFIO_PCI_ROM_REGION_INDEX; i++) {
        char *name = g_strdup_printf("%s BAR %d", vbasedev->name, i);

        ret = vfio_region_setup(OBJECT(vdev), vbasedev,
                                &vdev->bars[i].region, i, name);
    }
}

int vfio_region_setup(Object *obj, VFIODevice *vbasedev, VFIORegion *region,
                      int index, const char *name)
{
    memory_region_init_io(region->mem, obj, &vfio_region_ops,
                              region, name, region->size);
}

const MemoryRegionOps vfio_region_ops = {
    .read = vfio_region_read,
    .write = vfio_region_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
    .valid = {
        .min_access_size = 1,
        .max_access_size = 8,
    },
    .impl = {
        .min_access_size = 1,
        .max_access_size = 8,
    },
};
```

那么在虚拟机读写这段内存的时候，回调函数 vfio_region_read/vfio_region_write 会被调用，此时再去通过 Device FD 来访问实际的 BAR 空间：

```c
uint64_t vfio_region_read(void *opaque,
                          hwaddr addr, unsigned size)
{
    VFIORegion *region = opaque;
    VFIODevice *vbasedev = region->vbasedev;
    union {
        uint8_t byte;
        uint16_t word;
        uint32_t dword;
        uint64_t qword;
    } buf;
    uint64_t data = 0;

    if (pread(vbasedev->fd, &buf, size, region->fd_offset + addr) != size) {
        error_report("%s(%s:region%d+0x%"HWADDR_PRIx", %d) failed: %m",
                     __func__, vbasedev->name, region->nr,
                     addr, size);
        return (uint64_t)-1;
    }
    switch (size) {
    case 1:
        data = buf.byte;
        break;
    case 2:
        data = le16_to_cpu(buf.word);
        break;
    case 4:
        data = le32_to_cpu(buf.dword);
        break;
    case 8:
        data = le64_to_cpu(buf.qword);
        break;
    default:
        hw_error("vfio: unsupported read size, %u bytes", size);
        break;
    }

    /* Same as write above */
    vbasedev->ops->vfio_eoi(vbasedev);

    return data;
}
```

但是这种方法并不高效，因为每次访问 BAR 空间都需要调用一次回调函数。所以下面采用地址映射的方式，先从 Device FD 的指定偏移上把 BAR 空间映射到 QEMU 的虚拟地址空间，再把地址注册到虚拟机内的物理地址空间：

```c
// error handling code removed
int vfio_region_mmap(VFIORegion *region)
{
    int i, prot = 0;
    char *name;

    prot |= region->flags & VFIO_REGION_INFO_FLAG_READ ? PROT_READ : 0;
    prot |= region->flags & VFIO_REGION_INFO_FLAG_WRITE ? PROT_WRITE : 0;

    for (i = 0; i < region->nr_mmaps; i++) {
        region->mmaps[i].mmap = mmap(NULL, region->mmaps[i].size, prot,
                                     MAP_SHARED, region->vbasedev->fd,
                                     region->fd_offset +
                                     region->mmaps[i].offset);
        name = g_strdup_printf("%s mmaps[%d]",
                               memory_region_name(region->mem), i);
        memory_region_init_ram_device_ptr(&region->mmaps[i].mem,
                                          memory_region_owner(region->mem),
                                          name, region->mmaps[i].size,
                                          region->mmaps[i].mmap);
        memory_region_add_subregion(region->mem, region->mmaps[i].offset,
                                    &region->mmaps[i].mem);
    }

    return 0;
}
```

这样配置了以后，虚拟机可以直接访问到 BAR 空间，而不用每次调用都 trap 到 QEMU。

### Configuration Space

当虚拟机要读写 PCIe Configuration Space 的时候，QEMU 会首先判断，要读取的字段是否被自己模拟，如果不是，再从 VFIO 提供的 Device FD 中读取 PCIe 设备的对应字段：

```c
// error handling code removed
uint32_t vfio_pci_read_config(PCIDevice *pdev, uint32_t addr, int len)
{
    VFIOPCIDevice *vdev = VFIO_PCI(pdev);
    uint32_t emu_bits = 0, emu_val = 0, phys_val = 0, val;

    memcpy(&emu_bits, vdev->emulated_config_bits + addr, len);
    emu_bits = le32_to_cpu(emu_bits);

    if (emu_bits) {
        emu_val = pci_default_read_config(pdev, addr, len);
    }

    if (~emu_bits & (0xffffffffU >> (32 - len * 8))) {
        ssize_t ret = pread(vdev->vbasedev.fd, &phys_val, len,
                    vdev->config_offset + addr);
        phys_val = le32_to_cpu(phys_val);
    }

    val = (emu_val & emu_bits) | (phys_val & ~emu_bits);

    return val;
}
```

因此如果 QEMU 想在 PCIe passthrough 的时候，伪装一些 Configuration Space 的内容，就可以通过修改 emulated_config_bits 来实现。
