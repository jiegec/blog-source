from matplotlib import pyplot as plt
import glob
from collections import defaultdict
from statistics import mean, geometric_mean
import numpy as np

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
                key = parts[1]
                value = float(parts[-1])
                data[name][f"{benchmark}/{key}"].append(value)


def plot_score(flavor):
    # plot score data
    x_data = sorted(data.keys(), key=lambda x: mean(data[x]["all"]))
    y_data = []
    for x in x_data:
        y_data.append(mean(data[x]["all"]))

    plt.cla()
    _, ax = plt.subplots(figsize=(6, len(y_data) * 0.3))

    for x, y in enumerate(y_data):
        ax.text(y, x, f"{y:.2f}")

    ax.set_xlim(0, max(y_data) * 1.5)
    ax.barh(x_data, y_data)
    ax.set_title(f"SPEC {flavor.upper()} 2017 Rate-1 Estimated Score")
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

    # sort by y: https://stackoverflow.com/a/9764364/2148614
    y_data, x_data = (list (t) for t in zip(*sorted(zip(y_data, x_data))))

    plt.cla()
    _, ax = plt.subplots(figsize=(6, len(y_data) * 0.3))

    for x, y in enumerate(y_data):
        ax.text(y, x, f"{y:.2f}")

    ax.set_xlim(0, max(y_data) * 1.5)
    ax.barh(x_data, y_data)
    ax.set_title(f"SPEC {flavor.upper()} 2017 Rate-1 Estimated Score/GHz")
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
        y_data.insert(0, round(geometric_mean(y_data), 2))
        # average
        y_data.insert(0, round(mean(y_data), 2))
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


for flavor in ["int", "fp"]:
    data.clear()
    if flavor == "int":
        benchmarks = benchmarks_int_rate
    else:
        benchmarks = benchmarks_fp_rate
    parse_data(flavor)
    plot_score(flavor)
    plot_score_per_ghz(flavor)
    plot_perf(flavor, "mpki", "mpki", "MPKI")
    plot_perf(flavor, "ipc", "ipc", "IPC")
    plot_perf(flavor, "mispred", "misprediction", "Branch Misprediction Rate (%)")
    plot_perf(flavor, "freq", "clock", "Clock Freq (MHz)")
    plot_perf(flavor, "inst", "instructions", "Instructions")
    plot_perf(flavor, "ratio", "ratio", "Ratio")
