---
layout: post
date: 2020-04-04
tags: [vivado,simulation,verilog,tcl]
categories:
    - hardware
---

# 在命令行中进行 Vivado 仿真

## 已有 Vivado 项目

想要在命令行里进行 Vivado 仿真，所以查了下 Xilinx 的 UG900 文档，找到了命令行仿真的方法。首先是生成仿真所需的文件：

```tcl
# assuming batch mode
open_project xxx.xpr
set_property top YOUR_SIM_TOP [current_fileset -simset]
export_ip_user_files -no_script -force
export_simulation -simulator xsim -force
```

可以把这些语句放到 tcl 文件里然后用 batch mode 执行。执行成功以后，会在 `export_sim/xsim` 目录下生成一些文件。里面会有生成的脚本以供仿真：

```bash
cd export_sim/xsim && ./YOUR_SIM_TOP.sh
```

默认情况下它会执行 export_sim/xsim/cmd.tcl 里面的命令。如果想要记录 vcd 文件，修改内容为：

```tcl
open_vcd
log_vcd
run 20us
close_vcd
quit
```

这样就可以把仿真的波形输出到 dump.vcd 文件，拖到本地然后用 GTKWave 看。更多支持的命令可以到 UG900 里找。

## 无项目模式

如果没有创建 Vivado 项目，也可以单独进行仿真，具体分为三个步骤：

1. 第一步，对每个源 Verilog 文件，运行 `xvlog module.v` 命令
2. 第二步，生成 snapshot，运行 `xelab -debug all --snapshot snapshot_name top_module_name`
3. 第三步，仿真，运行 `xsim snapshot_name`

如果想要生成波形文件，编辑 `xsim.tcl` 为以下内容：

```tcl
open_vcd
log_vcd *
run -all
close_vcd
quit
```

把第三步运行的命令改为：`xsim snapshot_name -tclbatch xsim.tcl` 即可。
