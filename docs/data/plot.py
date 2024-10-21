from matplotlib import pyplot as plt
import glob
from collections import defaultdict
from statistics import mean
import numpy as np

# name -> key -> list[float]
data = defaultdict(lambda: defaultdict(list))

benchmarks = [
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


def parse_data():
    for f in glob.glob("int2017_rate1/*.txt"):
        name = f.split("/")[-1].split(".")[0]
        parts = name.split("_")
        core = " ".join(parts[:-2])
        flag = parts[-2]
        index = parts[-1]
        name = f"{core} ({flag})"

        # parse
        found_delim = False
        for line in open(f, "r", encoding="utf-8"):
            if line.startswith("===="):
                found_delim = True
            parts = line.strip().split(" ")
            parts = list(filter(lambda s: len(s) > 0, parts))

            # ratio
            if found_delim and "*" in line:
                benchmark = parts[0]
                ratio = float(parts[3])
                data[name][benchmark].append(ratio)
            if found_delim and "SPECrate(R)2017_int_base" in line:
                ratio = float(parts[-1])
                data[name]["all"].append(ratio)

            # perf
            if found_delim and ":" in line:
                benchmark = parts[0][:-1]
                key = parts[1]
                value = float(parts[-1])
                data[name][f"{benchmark}/{key}"].append(value)


def plot_score():
    # plot score data
    x_data = sorted(data.keys(), key=lambda x: mean(data[x]["all"]))
    y_data = []
    for x in x_data:
        y_data.append(mean(data[x]["all"]))

    plt.cla()
    _, ax = plt.subplots()

    for x, y in enumerate(y_data):
        ax.text(y, x, f"{y:.2f}")

    ax.set_xlim(0, 15)
    ax.barh(x_data, y_data)
    ax.set_title("SPEC INT 2017 Rate-1 Estimated Score")
    plt.savefig("int2017_rate1_score.png", bbox_inches="tight")


def plot_perf(file_name, key, display):
    # plot perf data
    plt.cla()
    fig, ax = plt.subplots(figsize=(5, 15))

    names = []
    for name in data:
        if f"{benchmarks[0]}/{key}" in data[name]:
            names.append(name)

    names = sorted(names)
    width = 1 / (len(names) + 1)
    max_value = 0
    for i, name in enumerate(names):
        x_data = np.arange(len(benchmarks)) + width * (len(names) - i - 1)
        y_data = []
        for bench in reversed(benchmarks):
            y_data.append(mean(data[name][f"{bench}/{key}"]))
        rects = ax.barh(x_data, y_data, width, label=name)
        ax.bar_label(rects, padding=3)
        max_value = max(max_value, max(y_data))

    ax.set_xlim(0, max_value * 1.5)
    ax.set_yticks(np.arange(len(benchmarks)) + width * (len(names) - 1) / 2, reversed(benchmarks))
    ax.legend()
    ax.set_title(f"SPEC INT 2017 Rate-1 Estimated {display}")
    plt.savefig(f"int2017_rate1_{file_name}.png", bbox_inches="tight")


parse_data()
plot_score()
plot_perf("mpki", "mpki", "MPKI")
plot_perf("ipc", "ipc", "IPC")
plot_perf("mispred", "misprediction", "Branch Misprediction Rate (%)")
