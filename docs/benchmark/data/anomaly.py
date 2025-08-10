import glob

for flavor in ["int", "fp"]:
    for f in glob.glob(f"{flavor}2017_rate1/*.txt"):
        # parse
        found_delim = False
        times = []
        for line in open(f, "r", encoding="utf-8"):
            line = line.strip()
            if line.startswith("---------------"):
                found_delim = True
            if line.startswith("==============="):
                break
            parts = line.strip().split(" ")
            parts = list(filter(lambda s: len(s) > 0, parts))
            if found_delim and parts[1] == '1':
                times.append(float(parts[2]))

                if len(times) == 3:
                    times = sorted(times)
                    if times[1] / times[0] > 1.1:
                        print(f"Anomaly found in {f}: {times} {line}")
                    times = []
                
                ratio = float(parts[3])
                if ratio < 1.0:
                    print(f"Anomaly found in {f}: {ratio} {line}")

