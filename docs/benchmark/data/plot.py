import matplotlib as mpl
from matplotlib import pyplot as plt
import glob
from collections import defaultdict
from statistics import mean, geometric_mean
import numpy as np
import os

# reproducibility
# https://github.com/matplotlib/matplotlib/issues/27831
mpl.rcParams["svg.hashsalt"] = "fixed-salt"
os.environ["SOURCE_DATE_EPOCH"] = "0"

# name -> key -> list[float]
data = defaultdict(lambda: defaultdict(list))
benchmarks = []

benchmarks_int_rate = [
    "500.perlbench_r",
    "502.gcc_r",
    "505.mcf_r",
    "520.omnetpp_r",
    "523.xalancbmk_r",
    "525.x264_r",
    "531.deepsjeng_r",
    "541.leela_r",
    "548.exchange2_r",
    "557.xz_r",
]

benchmarks_fp_rate = [
    "503.bwaves_r",
    "507.cactuBSSN_r",
    "508.namd_r",
    "510.parest_r",
    "511.povray_r",
    "519.lbm_r",
    "521.wrf_r",
    "526.blender_r",
    "527.cam4_r",
    "538.imagick_r",
    "544.nab_r",
    "549.fotonik3d_r",
    "554.roms_r",
]

opt_flags = [
    "O3",
    "O3 -flto",
    "O3 -flto -ljemalloc",
    "O3 -march=native",
    "O3 -march=native -flto -ljemalloc",
]


def parse_data(flavor):
    for f in glob.glob(f"{flavor}2017_rate1/*.txt"):
        print(f"Processing {f}")
        name = f.split("/")[-1].split(".")[0]
        parts = name.split("_")
        core = " ".join(parts[:-2])
        flag = parts[-2]
        flag = flag.replace("-", " -")
        # index = parts[-1]
        name = f"{core} ({flag})"

        # parse
        found_delim = False
        for line in open(f, "r", encoding="utf-8"):
            if line.startswith("===="):
                found_delim = True
            parts = line.strip().split(" ")
            parts = list(filter(lambda s: len(s) > 0, parts))

            # end
            if line.strip() == "System Info:":
                break

            # ratio
            if found_delim and "*" in line:
                benchmark = parts[0]
                ratio = float(parts[3])
                data[name][f"{benchmark}/ratio"].append(ratio)
            if found_delim and f"SPECrate(R)2017_{flavor}_base" in line:
                ratio = float(parts[-1])
                data[name]["all"].append(ratio)

            # perf
            if found_delim and ":" in line:
                benchmark = parts[0][:-1]
                if benchmark == "all":
                    continue
                key = parts[1]
                value = float(parts[-1])
                data[name][f"{benchmark}/{key}"].append(value)


def get_opt_flags(name):
    return name.split("(")[1].removesuffix(")")


def get_isa(name):
    if "Intel" in name or "AMD" in name or "Hygon" in name:
        return "amd64"
    elif (
        "Graviton" in name
        or "Huawei" in name
        or "Kunpeng" in name
        or "Qualcomm" in name
        or "Apple" in name
        or "Ampere" in name
        or "Yitian" in name
    ):
        return "arm64"
    elif "Loongson" in name:
        return "loong64"
    elif "POWER" in name:
        return "ppc64el"
    assert False, f"Unknown ISA for CPU {name}"


def compute_key(x):
    # sort by opt flags first, then score
    opt_flags = get_opt_flags(x)
    score = mean(data[x]["all"])
    return opt_flags, score


def plot_score(flavor):
    # plot score data
    x_data = sorted(data.keys(), key=compute_key)
    y_data = []
    for x in x_data:
        y_data.append(mean(data[x]["all"]))

    plt.cla()
    _, ax = plt.subplots(figsize=(6, len(y_data) * 0.3))

    for x, y in enumerate(y_data):
        ax.text(y, x, f"{y:.2f}", verticalalignment="center")

    ax.set_xlim(0, max(y_data) * 1.5)
    ax.barh(x_data, y_data)
    ax.set_title(f"SPEC {flavor.upper()} 2017 Rate-1 Estimated Score")

    # add horizontal lines for each opt flag
    for opt_flag in opt_flags:
        for i, x in enumerate(x_data):
            if get_opt_flags(x) == opt_flag:
                # found delimiter
                ax.axhline(i - 0.5)
                break
    ax.axhline(len(x_data) - 0.5)
    plt.savefig(f"{flavor}2017_rate1_score.svg", bbox_inches="tight")


def plot_score_per_ghz(flavor):
    # plot score per ghz data
    names = []
    for name in data:
        if f"{benchmarks[0]}/clock" in data[name]:
            names.append(name)

    x_data = names
    y_data = []
    for x in x_data:
        freq = []
        for bench in benchmarks:
            freq.append(mean(data[x][f"{bench}/clock"]) / 1000)
        y_data.append(mean(data[x]["all"]) / mean(freq))

    # sort by opt flags first, then y: https://stackoverflow.com/a/9764364/2148614
    y_data, x_data = (
        list(t)
        for t in zip(
            *sorted(
                zip(y_data, x_data),
                key=lambda arg: (get_opt_flags(arg[1]), arg[0]),
            )
        )
    )

    plt.cla()
    _, ax = plt.subplots(figsize=(6, len(y_data) * 0.3))

    for x, y in enumerate(y_data):
        ax.text(y, x, f"{y:.2f}", verticalalignment="center")

    ax.set_xlim(0, max(y_data) * 1.5)
    ax.barh(x_data, y_data)
    ax.set_title(f"SPEC {flavor.upper()} 2017 Rate-1 Estimated Score/GHz")

    # add horizontal lines for each opt flag
    for opt_flag in opt_flags:
        for i, x in enumerate(x_data):
            if get_opt_flags(x) == opt_flag:
                # found delimiter
                ax.axhline(i - 0.5)
                break
    ax.axhline(len(x_data) - 0.5)

    plt.savefig(f"{flavor}2017_rate1_score_per_ghz.svg", bbox_inches="tight")


def plot_perf(flavor, file_name, key, display):
    # plot perf data
    names = []
    for name in data:
        if f"{benchmarks[0]}/{key}" in data[name]:
            names.append(name)

    plt.cla()
    _, ax = plt.subplots(figsize=(6, len(names) * 3))

    names = sorted(names)
    width = 1 / (len(names) + 1)
    max_value = 0
    for i, name in enumerate(names):
        x_data = np.arange(len(benchmarks) + 2) + width * (len(names) - i - 1)
        y_data = []
        for bench in reversed(benchmarks):
            y_data.append(mean(data[name][f"{bench}/{key}"]))
        # geomean
        y_geomean = geometric_mean(y_data)
        y_mean = mean(y_data)
        y_data.insert(0, round(y_geomean, 2))
        # average
        y_data.insert(0, round(y_mean, 2))
        rects = ax.barh(x_data, y_data, width, label=name)
        ax.bar_label(rects, labels=[f"{y:.3g} {name}" for y in y_data], padding=3)
        max_value = max(max_value, *y_data)

    ax.set_xlim(0, max_value * 2.0)
    ax.set_yticks(
        np.arange(len(benchmarks) + 2) + width * (len(names) - 1) / 2,
        ["average", "geomean"] + list(reversed(benchmarks)),
    )
    ax.set_title(f"SPEC {flavor.upper()} 2017 Rate-1 Estimated {display}")
    plt.savefig(f"{flavor}2017_rate1_{file_name}.svg", bbox_inches="tight")


def plot_table(flavor):
    # plot score data
    x_data = sorted(data.keys(), key=compute_key)
    table = []
    columns = [
        "CPU",
        "ISA",
        "Flags",
        "MPKI",
        "Misp (%)",
        "Clock",
        "Score/GHz",
        "Score",
        *benchmarks,
    ]

    last_x = None
    for x in x_data:
        if last_x is not None and get_opt_flags(x) != get_opt_flags(last_x):
            # add delimiter
            table.append(columns)

        cpu = x.split(" (")[0]
        row = [cpu, get_isa(cpu), get_opt_flags(x)]

        if f"{benchmarks[0]}/mpki" in data[x]:
            mpkis = [mean(data[x][benchmark + "/mpki"]) for benchmark in benchmarks]
            mean_mpki = mean(mpkis)
            row.append(f"{mean_mpki:.2f}")
        else:
            row.append("N/A")

        if f"{benchmarks[0]}/misprediction" in data[x]:
            mispreds = [
                mean(data[x][benchmark + "/misprediction"]) for benchmark in benchmarks
            ]
            mean_mispred = mean(mispreds)
            row.append(f"{mean_mispred:.2f}")
        else:
            row.append("N/A")

        if f"{benchmarks[0]}/clock" in data[x]:
            clocks = [
                mean(data[x][benchmark + "/clock"]) / 1000 for benchmark in benchmarks
            ]
            mean_clock = mean(clocks)
            row.append(f"{mean_clock:.2f} GHz")
            score_per_ghz = mean(data[x]["all"]) / mean_clock
            row.append(f"{score_per_ghz:.2f}")
        else:
            row.append("N/A")
            row.append("N/A")

        row.append(f"{mean(data[x]["all"]):.2f}")
        row += [
            f"{mean(data[x][benchmark + '/ratio']):.2f}" for benchmark in benchmarks
        ]

        table.append(row)
        last_x = x

    plt.cla()
    fig, ax = plt.subplots()

    # hide axes
    ax.axis("off")
    ax.axis("tight")
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

    table = ax.table(cellText=table, colLabels=columns, loc="center", colLoc="right")
    table.auto_set_font_size(False)
    table.set_fontsize(16)
    table.scale(1, 2)
    table.auto_set_column_width(col=list(range(len(columns))))
    plt.savefig(f"{flavor}2017_rate1_table.svg", bbox_inches="tight")


for flavor in ["int", "fp"]:
    data.clear()
    if flavor == "int":
        benchmarks = benchmarks_int_rate
    else:
        benchmarks = benchmarks_fp_rate
    parse_data(flavor)
    plot_table(flavor)
    plot_score(flavor)
    plot_score_per_ghz(flavor)
    plot_perf(flavor, "mpki", "mpki", "MPKI")
    plot_perf(flavor, "ipc", "ipc", "IPC")
    plot_perf(flavor, "mispred", "misprediction", "Branch Misprediction Rate (%)")
    plot_perf(flavor, "freq", "clock", "Clock Freq (MHz)")
    plot_perf(flavor, "inst", "instructions", "Instructions")
    plot_perf(flavor, "brinst", "branch", "Branch Instructions")
    plot_perf(flavor, "ratio", "ratio", "Ratio")
