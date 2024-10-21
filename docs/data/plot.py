from matplotlib import pyplot as plt
import glob
from collections import defaultdict
from statistics import mean

# name -> key -> list[float]
data = defaultdict(lambda: defaultdict(list))

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

# plot overall data
x_data = sorted(data.keys(), key=lambda x: mean(data[x]["all"]))
y_data = []
for x in x_data:
    y_data.append(mean(data[x]["all"]))

plt.cla()
fig, ax = plt.subplots()

for x, y in enumerate(y_data):
    ax.text(y, x, f"{y:.2f}")

ax.set_xlim(0, 15)
ax.barh(x_data, y_data)
ax.set_title("SPEC INT 2017 Rate-1 Estimated Score")
plt.savefig("int2017_rate1_score.png", bbox_inches="tight")
