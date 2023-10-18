---
layout: post
date: 2023-10-17
tags: [clang,llvm,cuda,nvidia]
categories:
    - software
---

# Clang 如何支持 CUDA 程序

## 前言

编译 CUDA 程序的主要工具是 NVIDIA 提供的闭源编译器 NVCC，但实际上，NVCC 是基于 LLVM 开发的（来源：[NVIDIA CUDA Compiler](https://developer.nvidia.com/cuda-llvm-compiler)），NVIDIA 也把 NVCC 其中一部分逻辑贡献给了 LLVM 上游，使得 [Clang 也可以在 CUDA 的配合下编译 CUDA 程序](https://llvm.org/docs/CompileCudaWithLLVM.html)。这篇博客尝试研究 Clang/LLVM 如何实现 CUDA 程序的编译，主要是 Clang 前端部分，后端部分，也就是从 LLVM IR 到 NVPTX 的这一步还没有进行深入的研究。

<!-- more -->

## 编译命令

首先按照 [Compiling CUDA with clang](https://llvm.org/docs/CompileCudaWithLLVM.html) 文档，介绍一下使用 clang 编译 CUDA 程序的命令：

```shell
clang++ axpy.cu -o axpy -L<CUDA install path>/<lib64 or lib> -lcudart/cudart_static [--cuda-gpu-arch=<GPU arch>]
```

其中 `-L<CUDA install path>/<lib64 or lib> -lcudart/cudart_static` 表示的是链接 CUDA 提供的 libcudart，它有静态库和动态库两种形式，根据实际需求选择。`--cuda-gpu-arch=<GPU arch>` 就和 NVCC 一样，指定 GPU 的 SM Architecture 版本，可以写多个。如果 CUDA 安装到 `/usr/local/cuda`，一个例子如下：

```shell
clang++ axpy.cu -o axpy -L /usr/local/cuda/lib64 -lcudart
```

编译出来的可执行文件可以直接运行，就和 NVCC 一样，只不过需要手动链接 libcudart。

## 编译流程

为了查看 clang 的编译流程，可以在编译命令中，添加 `-v` 选项让它打印出中间执行的命令，再添加 `--save-temps` 命令可以把中途的编译产物保留在当前路径下。观察输出，可以发现它进行了如下操作（省略了大量的命令行参数）：

1. `clang -triple nvptx64-nvidia-cuda -S -target-cpu sm_70 axpy.cu -o axpy-sm_70.s`：以 NVPTX 为 target，编译源代码，生成 PTX 汇编
2. `ptxas --gpu-name sm_70 --output-file axpy-sm_70.o axpy-sm_70.s`：使用 CUDA 提供的 `ptxas` 程序，把 PTX 汇编翻译成 SM 70 的 SASS 指令，打包到一个 ELF object 中
3. `fatbinary --create axpy.fatbin --image=profile=sm_70,file=axpy-sm_70.o --image=profile=compute_70,file=axpy-sm_70.s`: 使用 CUDA 提供的 `fatbinary` 程序，把 ptxas 生成的 ELF object 和 clang 生成的 PTX 汇编内容打包成一个 fatbin 文件
4. `clang -triple x86_64-pc-linux-gnu -emit-obj axpy.cu -fcuda-include-gpubinary axpy.fatbin -o axpy.o`：编译 Host 代码，把 fatbin 的内容嵌入到一个 `.nv_fatbin` section 中，生成一个 ELF object 中
5. `ld -o axpy axpy.o -lcudart`：最后一步就是常规的链接，得到最终的可执行文件

实际上还有一步预处理，这里省略了。对比通常 C++ 程序的编译流程，这里不同的点在于：

1. 用 Clang 以 NVPTX target 编译了一遍，得到 PTX 汇编
2. 用 CUDA 的 ptxas，把 PTX 汇编翻译成对应 SM Architecture 的 SASS 指令，放到一个 ELF object 里
3. 用 CUDA 的 fatbinary，把第一步和第二步的结果放到一个 fatbin 文件里
4. 把 fatbin 文件嵌入到 ELF 中

其中第一步和第四步是由 LLVM 实现的，因此可以找到相应的代码；第二步和第三步则没有源码，但是网上有很多公开的逆向，例如 [Decoding CUDA binary](https://dl.acm.org/doi/abs/10.5555/3314872.3314900)、[decodecudabinary/Decoding-CUDA-Binary](https://github.com/decodecudabinary/Decoding-CUDA-Binary/tree/master/tools) 和 [n-eiling/cuda-fatbin-decompression](https://github.com/n-eiling/cuda-fatbin-decompression)。

此外，Clang 还需要针对 Host 部分代码，进行特殊处理，因为 CUDA 有一些扩展语法（主要是启动 Kernel 的 `<<<>>>`），需要把这些部分替换为对 CUDA Runtime（也就是 libcudart）的调用。接下来要讨论的就是这一部分。

## Host 代码

首先研究的是 CUDA 的扩展语法里的启动 Kernel 语法：

```c++
axpy<<<1, kDataLen>>>(kDataLen, a, device_x, device_y);
```

实际上是怎么实现的呢？如果去查看 LLVM IR，会发现它的逻辑类似下面的代码：

```c++
success = __cudaPushCallConfiguration(1, kDataLen);
if (success) {
    __device_stub__axpy(kDataLen, a, device_x, device_y);
}
```

这段代码的生成逻辑在 [EmitCUDAKernelCallExpr](https://github.com/llvm/llvm-project/blob/52db7e27458f774fa0c6c6a864ce197fa071a230/clang/lib/CodeGen/CGCUDARuntime.cpp#L26) 函数中，可以看到它构造了两个基本块，对应 success 内的 device stub 调用（ConfigOKBlock）和完成调用的基本块（ContBlock）。

也就是说，它首先把 `<<<` 和 `>>>` 之间的参数传给了 `__cudaPushCallConfiguration`（实际上是构造了一个 `dim3` 再传进去，这里省略了），如果它成功了，再去调用一个 `__device_stub__axpy`。可以猜想，它会对参数进行检查，如果不符合 CUDA 的要求，那就直接返回错误，不去启动 Kernel。如果配置没问题，就去调用 `__device_stub__axpy`。那么这个函数是什么呢？它是在 [Clang 代码](https://github.com/llvm/llvm-project/blob/ab6d5fa3d0643e68d6ec40d9190f20fb14190ed1/clang/lib/CodeGen/CGCUDANV.cpp#L324) 里生成的：

```c++
// CUDA 9.0+ uses new way to launch kernels. Parameters are packed in a local
// array and kernels are launched using cudaLaunchKernel().
void CGNVCUDARuntime::emitDeviceStubBodyNew(CodeGenFunction &CGF,
                                            FunctionArgList &Args) {
  // omitted

  // Calculate amount of space we will need for all arguments.  If we have no
  // args, allocate a single pointer so we still have a valid pointer to the
  // argument array that we can pass to runtime, even if it will be unused.
  // Store pointers to the arguments in a locally allocated launch_args.
  // omitted

  // Lookup cudaLaunchKernel/hipLaunchKernel function.
  // cudaError_t cudaLaunchKernel(const void *func, dim3 gridDim, dim3 blockDim,
  //                              void **args, size_t sharedMem,
  //                              cudaStream_t stream);
  auto LaunchKernelName = addPrefixToName(KernelLaunchAPI);
  IdentifierInfo &cudaLaunchKernelII =
      CGM.getContext().Idents.get(LaunchKernelName);
  FunctionDecl *cudaLaunchKernelFD = nullptr;

  // Create temporary dim3 grid_dim, block_dim.
  llvm::FunctionCallee cudaPopConfigFn = CGM.CreateRuntimeFunction(
      llvm::FunctionType::get(IntTy,
                              {/*gridDim=*/GridDim.getType(),
                               /*blockDim=*/BlockDim.getType(),
                               /*ShmemSize=*/ShmemSize.getType(),
                               /*Stream=*/Stream.getType()},
                              /*isVarArg=*/false),
      addUnderscoredPrefixToName("PopCallConfiguration"));

  CGF.EmitRuntimeCallOrInvoke(cudaPopConfigFn,
                              {GridDim.getPointer(), BlockDim.getPointer(),
                               ShmemSize.getPointer(), Stream.getPointer()});

  // Emit the call to cudaLaunch
  llvm::Value *Kernel = CGF.Builder.CreatePointerCast(
      KernelHandles[CGF.CurFn->getName()], VoidPtrTy);
  CallArgList LaunchKernelArgs;
  LaunchKernelArgs.add(RValue::get(Kernel),
                       cudaLaunchKernelFD->getParamDecl(0)->getType());
  LaunchKernelArgs.add(RValue::getAggregate(GridDim), Dim3Ty);
  LaunchKernelArgs.add(RValue::getAggregate(BlockDim), Dim3Ty);
  LaunchKernelArgs.add(RValue::get(KernelArgs.getPointer()),
                       cudaLaunchKernelFD->getParamDecl(3)->getType());
  LaunchKernelArgs.add(RValue::get(CGF.Builder.CreateLoad(ShmemSize)),
                       cudaLaunchKernelFD->getParamDecl(4)->getType());
  LaunchKernelArgs.add(RValue::get(CGF.Builder.CreateLoad(Stream)),
                       cudaLaunchKernelFD->getParamDecl(5)->getType());
  llvm::FunctionCallee cudaLaunchKernelFn =
      CGM.CreateRuntimeFunction(FTy, LaunchKernelName);
  CGF.EmitCall(FI, CGCallee::forDirect(cudaLaunchKernelFn), ReturnValueSlot(),
               LaunchKernelArgs);
}
```

代码比较长，这里进行了删减，大概的逻辑是：把 device stub 的函数参数放到一个数组里，然后通过调用 `__cudaPopCallConfiguration` 把刚刚在 `__cudaPushCallConfiguration` 传入的启动配置再读取出来，再调用真正启动 CUDA Kernel 的函数 [`cudaLaunchKernel`](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__EXECUTION.html#group__CUDART__EXECUTION_1g5064cdf5d8e6741ace56fd8be951783c)：

```c++
__host__​cudaError_t cudaLaunchKernel ( const void* func, dim3 gridDim, dim3 blockDim, void** args, size_t sharedMem, cudaStream_t stream )
```

其中 `const void* func` 指向了 device stub function 本身，`args` 是 device stub 把自己的参数保存下来放到数组中的，其余的参数是经过 `__cudaPushCallConfiguration` 保存又用 `__cudaPopCallConfiguration` 取出的启动配置。

这时候你可能觉得很奇怪，为什么要传 function 本身的指针，按理说要启动 GPU 上的 CUDA Kernel，不应该给一个 CUDA Kernel 的指针吗？CUDA Runtime 怎么能通过 device stub function 的指针，判断对应的 CUDA Kernel 是哪个呢？下面来讨论这个问题。

## CUDA Runtime 注册

除了启动 Kernel 以外，Clang 还生成了很多代码，用来向 CUDA Runtime 注册一些信息。回忆前面的流程，Kernel 编译成 PTX 汇编以后，先是编译成 SASS 指令打包在了 ELF 里，后来 PTX 和 ELF 一起打包成了一个 fatbin 文件，最后嵌入到可执行程序里面。到目前为止，还没有用到它，而如果要启动 Kernel，肯定需要让 CUDA Runtime 去解析 fatbin，找到里面的 Kernel 指令，放到 GPU 上去执行。另外，根据上一节内容，CUDA Runtime 还需要知道 device stub function 和 Kernel 的对应关系，才能知道 Launch 哪份 Kernel 指令。

实际上，这个事情是由 [Clang 生成的初始化代码](https://github.com/llvm/llvm-project/blob/ab6d5fa3d0643e68d6ec40d9190f20fb14190ed1/clang/lib/CodeGen/CGCUDANV.cpp#L695)完成的：

```c++
/// Creates a global constructor function for the module:
///
/// For CUDA:
/// \code
/// void __cuda_module_ctor() {
///     Handle = __cudaRegisterFatBinary(GpuBinaryBlob);
///     __cuda_register_globals(Handle);
/// }
/// \endcode
```

Clang 会负责生成一个 `__cuda_module_ctor` 函数，放到可执行程序里面，并且把地址添加到 `.init_array` 中，这个 section 里面的函数地址会被 libc 在加载的时候调用，这也是 C++ 里全局类变量自动调用构造函数的实现方法。这个函数里面，首先调用 cudart 的 `__cudaRegisterFatBinary` 函数，把 fatbin 地址传递过去（注：实际上是一个[结构体](https://github.com/shinpei0208/gdev/blob/e328438f3cca32bd84ce64807e322673d4b66c40/cuda/runtime/ocelot/cuda/interface/cudaFatBinary.h#L138)），这样 cudart 就知道了这个程序里打包的 fatbin，也就拿到了所有的 PTX 代码和 SASS 指令。接着还调用了 `__cuda_register_globals`，这也是 [Clang 生成的](https://github.com/llvm/llvm-project/blob/ab6d5fa3d0643e68d6ec40d9190f20fb14190ed1/clang/lib/CodeGen/CGCUDANV.cpp#L523)：

```c++
/// Creates a function that sets up state on the host side for CUDA objects that
/// have a presence on both the host and device sides. Specifically, registers
/// the host side of kernel functions and device global variables with the CUDA
/// runtime.
/// \code
/// void __cuda_register_globals(void** GpuBinaryHandle) {
///    __cudaRegisterFunction(GpuBinaryHandle,Kernel0,...);
///    ...
///    __cudaRegisterFunction(GpuBinaryHandle,KernelM,...);
///    __cudaRegisterVar(GpuBinaryHandle, GlobalVar0, ...);
///    ...
///    __cudaRegisterVar(GpuBinaryHandle, GlobalVarN, ...);
/// }
/// \endcode
```

Clang 会扫描代码里的 Kernel 函数和需要和 GPU 互操作的全局变量（用于 `cudaMemcpyFromSymbol` 等函数），然后去调用 cudart 的 `__cudaRegisterFunction` 和 `__cudaRegisterVar` 函数。也就是在这个时候，建立了 device stub function 地址和 Kernel 的映射关系：cudart 的 `cudaLaunchKernel` 实现里面，可以根据 device stub function 的地址，去查询 Kernel 的符号，再根据符号去找到对应的 PTX 和 SASS 指令。

## fatbin

在前面提到了 fatbin 的过程，它作为一个容器，保存了 PTX 代码或者使用 ptxas 编译后得到的 ELF 文件。它的格式比较简单，可以在 [n-eiling/cuda-fatbin-decompression](https://github.com/n-eiling/cuda-fatbin-decompression) 和 [fatbinary](https://github.com/jiegec/fatbinary) 中看到。它的结构大体如下：

1. 开头是一个 fatbin 头部
2. 接下来是若干个 entry:
    1. 每个 entry 有一个头部
    2. 每个 entry 有一个 payload，里面是 ELF 或者 PTX，可选压缩

它在每个 entry 的头部里会记录一些信息，例如 SM Architecture 等等，方便 CUDA Runtime 快速地定位到要去使用的 ELF 或者 PTX，免得扫描完整的 ELF 或者 PTX 内容。这有点像 .a（archive）文件，本身是一个 .o（object）文件的容器，但还提供了一个索引，从符号到 object 文件的映射。虽然 fatbin 没有做映射，但是它每个 entry 头部都记录了 entry 的长度，解析时可以跳过不关心的 payload。

如果想看 fatbin 的内容，可以用 `cuobjdump` 命令来查看，它可以显示出每个 entry 在头部中记录的信息，也可以把内部的 payload 释放出来。如果想生成 fatbin，可以用 `fatbinary` 命令，它会解析 ELF 和 PTX 文件，提取一些信息，放到 entry 头部中。

fatbin 还采用了一个比较简单的压缩算法：如果出现了重复的部分，把重复的部分替换为距离上一次重复的偏移和重复的长度，那么解压的时候，只需要 memcpy 即可，不涉及到复杂的字典操作，见 [decompress 函数](https://github.com/n-eiling/cuda-fatbin-decompression/blob/9b194a9aa526b71131990ddd97ff5c41a273ace5/fatbin-decompress.c#L137)。

