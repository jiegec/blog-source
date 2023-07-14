---
layout: post
date: 2022-03-14
tags: [synthesis,synopsys,dc,designcompiler]
categories:
    - hardware
---

# Synopsys Design Compiler 综合实践

## 工艺库

综合很重要的一步是把 HDL 的逻辑变成一个个单元，这些单元加上连接方式就成为了网表。那么，基本单元有哪些，怎么决定用哪些基本单元？

这个就需要工艺库了，工艺库定义了一个个单元，单元的引脚、功能，还有各种参数，这样 Design Compiler 就可以按照这些信息去找到一个优化的网表。

### Liberty 格式

网上可以找到一些 Liberty 格式的工艺库，比如 [Nangate45](https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/master/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib)，它的设定是 25 摄氏度，1.10 伏，属于 TT（Typical/Typical）的 Process Corner。

在里面可以看到一些基本单元的定理，比如 `AND2_X1`，就是一个 drive strength 是 1 的二输入与门：

```liberty
cell (AND2_X1) {
    drive_strength : 1;
    pin (A1) {
        direction : input;
    }
    pin (A2) {
        direction : input;
    }
    pin (ZN) {
        direction : output;
        function : "(A1 & A2)";
    }
    /* ... */
}
```

这样就定义了两个输入 pin，一个输出 pin，还有它实现的功能。还有很重要的一点是保存了时序信息，比如：

```liberty
lu_table_template (Timing_7_7) {
    variable_1 : input_net_transition;
    variable_2 : total_output_net_capacitance;
    index_1 ("0.0010,0.0020,0.0030,0.0040,0.0050,0.0060,0.0070");
    index_2 ("0.0010,0.0020,0.0030,0.0040,0.0050,0.0060,0.0070");
}
cell (AND2_X1) {
    pin (ZN) {
        timing () {
			related_pin	: "A1";
            timing_sense : positive_unate;
			cell_fall(Timing_7_7) {
				index_1 ("0.00117378,0.00472397,0.0171859,0.0409838,0.0780596,0.130081,0.198535");
				index_2 ("0.365616,1.893040,3.786090,7.572170,15.144300,30.288700,60.577400");
				values ("0.0217822,0.0253224,0.0288237,0.0346827,0.0448323,0.0636086,0.100366", \
				        "0.0233179,0.0268545,0.0303556,0.0362159,0.0463659,0.0651426,0.101902", \
				        "0.0296429,0.0331470,0.0366371,0.0425000,0.0526603,0.0714467,0.108208", \
				        "0.0402311,0.0440292,0.0477457,0.0538394,0.0641187,0.0829203,0.119654", \
				        "0.0511250,0.0554077,0.0595859,0.0662932,0.0771901,0.0963434,0.133061", \
				        "0.0625876,0.0673198,0.0719785,0.0794046,0.0910973,0.110757,0.147656", \
				        "0.0748282,0.0800098,0.0851434,0.0933663,0.106111,0.126669,0.163872");
			}
    }
}
```

首先要看 cell_fall 后面的 template 是 Timing_7_7，可以看到 variable_1 和 variable_2 对应的是 input_net_transition 和 total_output_net_capacitance。这里 cell_fall 指的是输出 pin ZN 从 1 变成 0 的时候，这个变化从 A1 的变化传播到 ZN 的时间，这个时间和输入的 transition 时间（大概是从 0 到 1、从 1 到 0 的时间，具体从多少百分比到多少百分比见设置）和输出的 capacitance 有关，所以是一个查找表，查找的时候找最近的点进行插值。输出的 capacitance 取决于 wire load 和连接了这个输出的其他单元的输入。

除了 cell_fall/cell_rise 两种类型，还有 fall_transition 和 rise_transition，这就是输出引脚的变化时间，又作为后继单元的输入 transition 时间。

接下来，还能看到功耗的数据：

```liberty
power_lut_template (Power_7_7) {
    variable_1 : input_transition_time;
    variable_2 : total_output_net_capacitance;
    index_1 ("0.0010,0.0020,0.0030,0.0040,0.0050,0.0060,0.0070");
    index_2 ("0.0010,0.0020,0.0030,0.0040,0.0050,0.0060,0.0070");
}
internal_power () {
    related_pin	         : "A1";
    fall_power(Power_7_7) {
        index_1 ("0.00117378,0.00472397,0.0171859,0.0409838,0.0780596,0.130081,0.198535");
        index_2 ("0.365616,1.893040,3.786090,7.572170,15.144300,30.288700,60.577400");
        values ("2.707163,2.939134,3.111270,3.271119,3.366153,3.407657,3.420511", \
                "2.676697,2.905713,3.073189,3.236823,3.334156,3.373344,3.387400", \
                "2.680855,2.891263,3.047784,3.212948,3.315296,3.360694,3.377614", \
                "2.821141,3.032707,3.182020,3.338567,3.444608,3.488752,3.508229", \
                "3.129641,3.235525,3.357993,3.567372,3.743682,3.792092,3.808289", \
                "3.724304,3.738737,3.808381,3.980825,4.147999,4.278043,4.311323", \
                "4.526175,4.492292,4.510220,4.634217,4.814899,4.934862,5.047389");
    }
    rise_power(Power_7_7) {
        index_1 ("0.00117378,0.00472397,0.0171859,0.0409838,0.0780596,0.130081,0.198535");
        index_2 ("0.365616,1.893040,3.786090,7.572170,15.144300,30.288700,60.577400");
        values ("1.823439,1.926997,1.963153,2.028865,1.957837,2.123314,2.075262", \
                "1.796317,1.896145,1.960625,2.014112,2.050786,2.046472,1.972327", \
                "1.811604,1.886741,1.955658,1.978263,1.965671,1.963736,2.071227", \
                "1.997387,2.045930,2.092357,2.063643,2.099127,1.932089,2.131341", \
                "2.367285,2.439718,2.440043,2.403446,2.305848,2.351146,2.195145", \
                "2.916140,2.994325,3.044451,2.962881,2.836259,2.781564,2.633645", \
                "3.687718,3.756085,3.789394,3.792984,3.773583,3.593022,3.405552");
    }
}
```

可以看到，这也是一个查找表，也是按照输出的 rise/fall 有不同的功耗。巧合的是，功耗的查找表的 index_1/index_2 和上面的时序查找表是一样的。除了 internal power，还有 leakage power，定义如下：

```liberty
leakage_power_unit : "1nW";
/* ... */
cell_leakage_power 	: 50.353160;

leakage_power () {
    when           : "!A1 & !A2";
    value          : 40.690980;
}
leakage_power () {
    when           : "!A1 & A2";
    value          : 62.007550;
}
leakage_power () {
    when           : "A1 & !A2";
    value          : 41.294331;
}
leakage_power () {
    when           : "A1 & A2";
    value          : 57.419780;
}
```

可以看到，它的 leakage power 取决于输入的状态，单位是 1nW。

再来看 Flip Flop 的定义：

```liberty
cell (DFFRS_X1) {
    ff ("IQ" , "IQN") {
		next_state         	: "D";
		clocked_on         	: "CK";
		preset             	: "!SN";
		clear              	: "!RN";
		clear_preset_var1  	: L;
		clear_preset_var2  	: L;
	}
    pin (D) {
		direction		: input;
		capacitance		: 1.148034;
		fall_capacitance	: 1.081549;
		rise_capacitance	: 1.148034;

		timing () {

			related_pin	   : "CK";
			timing_type	   : hold_rising;
			when	           : "RN & SN";
			sdf_cond	   : "RN_AND_SN === 1'b1";
			fall_constraint(Hold_3_3) {
				index_1 ("0.00117378,0.0449324,0.198535");
				index_2 ("0.00117378,0.0449324,0.198535");
				values ("0.002921,0.012421,0.011913", \
				        "0.002707,0.008886,0.005388", \
				        "0.139993,0.148595,0.137370");
			}
			rise_constraint(Hold_3_3) {
				index_1 ("0.00117378,0.0449324,0.198535");
				index_2 ("0.00117378,0.0449324,0.198535");
				values ("0.004193,0.015978,0.019836", \
				        "0.020266,0.031864,0.035343", \
				        "0.099118,0.113075,0.120979");
			}
		}
    }
}
```

可以看到，这里的属性变成了 setup/hold 时间。

SRAM 也有类似的定义，通常是写在单独的 lib 文件中，根据 width 和 depth 生成，比如 [fakeram45_32x64.lib](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/blob/master/flow/platforms/nangate45/lib/fakeram45_32x64.lib)：

```liberty
cell(fakeram45_32x64) {
    area : 1754.536;
    interface_timing : true;
    memory() {
        type : ram;
        address_width : 5;
        word_width : 64;
    }
    pin(clk)   {
        direction : input;
        min_period : 0.174 ;
        internal_power(){
            rise_power(scalar) {
                values ("1498.650")
            }
            fall_power(scalar) {
                values ("1498.650")
            }
        }
    }
    bus(wd_in)   {
        bus_type : fakeram45_32x64_DATA;
        direction : input;
        timing() {
            related_pin     : clk;
            timing_type     : setup_rising ;
            rise_constraint(scalar) {
                values ("0.050");
            }
            fall_constraint(scalar) {
                values ("0.050");
            }
        } 
        internal_power(){
            when : "(we_in)";
            rise_power(scalar) {
                values ("14.987");
            }
            fall_power(scalar) {
                values ("14.987");
            }
        }
    }
}
```

也可以类似地看到，它的输入 setup/hold，功耗，面积等等信息。

### DB 格式

在给 Design Compiler 配置工艺库前，需要用 Library Compiler 先把 lib 格式转换为更紧凑的二进制 db 格式：

```tcl
read_lib xxx.lib
write_lib -format db xxx
```

实测部分 Liberty 文件会报错，不知道有没有修复的办法。另外，不同版本的 Library Compiler 生成的格式也不大一样，但都是兼容的。

在 Design Compiler 中，设置当前工艺库命令：

```tcl
set_app_var target_library xxx.db
set_link_var target_library xxx.db
# or
set_app_var target_library {xxx.db yyy.db}
set_link_var target_library {xxx.db yyy.db}
```

## 综合脚本

准备好工艺库以后，就可以开始编写综合脚本了，通常有这么些步骤：

```tcl
# step 1: read source code & set top level module name
read_file -format verilog xxx.v
read_file -format vhdl yyy.vhdl
current_design xxx

# step 2: setup timing constraints
create_clock clock -period 1.0000 # 1GHz for example
# other timing constraints:
# e.g. set_input_delay/set_output_delay

# step 3: synthesis
link
uniquify
# use this if you want to ungroup all hierarchy
# ungroup -flatten -all
# use this to retime design
# set_optimize_registers
compile_ultra

# step 4: check & report
check_timing
check_design
report_design
report_area -hierarchy
report_power -hierarchy
report_cell
report_timing -delay_type max
report_timing -delay_type min
report_constraint -all_violators
report_qor

# step 5: export
write -format ddc -hierarchy -output xxx.ddc
write_sdc -version 1.0 xxx.sdf
write -format verilog -hierarchy -output xxx.syn.v
write_sdc xxx.sdc
```

根据需求，进行自定义的修改。综合完成后，可以看到生成的 `xxx.syn.v` 文件里都是一个个的 cell，比如：

```verilog
AND2X2 U3912 ( .A(n4416), .B(n2168), .Y(n3469) );
OAI21X1 U3913 ( .A(n2872), .B(n4589), .C(n2461), .Y(n3471) );
DFFPOSX1 clock_r_REG147_S1 ( .D(n7634), .CLK(clock), .Q(n7773) );
```

还有一些比较特殊的 cell，比如 TIEHI/TIELO 就是恒定输出 1/0，用于门控时钟的 CLKGATE/ICG 等，还有一些综合阶段不会出现的 cell，在后续阶段会使用。

## 参考文档

- [Liberty format: an introduction](https://vlsiuniverse.blogspot.com/2016/12/liberty-format-introduction.html)
- [Digital VLSI Design Lecture 4: Standard Cell Libraries](https://www.eng.biu.ac.il/temanad/files/2017/02/Lecture-4-Standard-Cell-Libraries.pdf)