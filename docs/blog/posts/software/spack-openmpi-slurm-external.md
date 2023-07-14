---
layout: post
date: 2020-11-08
tags: [spack,openmpi,slurm]
categories:
    - software
---

# 在 Spack 中用 external 的 Slurm 依赖编译 OpenMPI

最近在一个集群上，需要用一个自己编译的 openmpi，但并没有 root 权限，所以需要自己搞一个 spack，在 spack 里面装 openmpi。但默认的安装选项下，它没有打开 slurm 支持，所以 srun 的话会出问题，只能 sbatch 然后指定 host 去做。于是我研究了一下怎么在 spack 里引入 external 的 slurm，然后用它来编译 openmpi

首先，编译 `~/.spack/packages.yaml`：

```yaml
packages:
  slurm:
    buildable: False
    paths:
      "slurm@15-08-7-1%gcc@8.3.0 arch=linux-ubuntu16.04-haswell": /usr
```

这里 slurm 版本是 `15.08.7`，我就按照 spack 里面 slurm 的版本号来写了。可以用 `spack spec openmpi schedulers=slurm +pmi` 来确认一下外部的 slurm 确实出现在了依赖之中。

这一步配好的话，安装的时候就会直接跳过 spack 里面 slurm 的安装。但又出现了 configure 错误，找不到 pmi 的库。于是，先用 external 的 mpirun 看一下配置：

```shell
$ module load openmpi-3.0.0
$ ompi_info
...
--with-pmi=/usr
--with-pmi-libdir=/usr/lib/x86_64-linux-gnu
...
```

可以看到，需要两个 config 参数。然后，在 spack 的 openmpi package.py 中：

```python
if spec.satisfies('schedulers=slurm'):
  config_args.append('--with-pmi={0}'.format(spec['slurm'].prefix))
  if spec.satisfies('@3.1.3:') or spec.satisfies('@3.0.3'):
    if '+static' in spec:
      config_args.append('--enable-static')
```

所以，需要加一个小 patch：

```python
if spec.satisfies('schedulers=slurm'):
  config_args.append('--with-pmi={0}'.format(spec['slurm'].prefix))
  # patched here
  config_args.append('--with-pmi-libdir={0}/lib/x86_64-linux-gnu'.format(spec['slurm'].prefix))
  if spec.satisfies('@3.1.3:') or spec.satisfies('@3.0.3'):
    if '+static' in spec:
      config_args.append('--enable-static')
```

然后，就可以编译通过了。