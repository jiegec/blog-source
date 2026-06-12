#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate raw data markdown content for SPEC CPU 2017/2026 Rate-1 (both INT and FP)"""

from pathlib import Path

# Parent directory of script (docs/benchmark)
BASE_DIR = Path(__file__).parent.parent.absolute()

BENCHMARKS_INT_2017_RATE = [
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

BENCHMARKS_FP_2017_RATE = [
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

BENCHMARKS_INT_2026_RATE = [
    "706.stockfish_r",
    "707.ntest_r",
    "708.sqlite_r",
    "710.omnetpp_r",
    "714.cpython_r",
    "721.gcc_r",
    "723.llvm_r",
    "727.cppcheck_r",
    "729.abc_r",
    "734.vpr_r",
    "735.gem5_r",
    "750.sealcrypto_r",
    "753.ns3_r",
    "777.zstd_r",
]

BENCHMARKS_FP_2026_RATE = [
    "709.cactus_r",
    "722.palm_r",
    "731.astcenc_r",
    "736.ocio_r",
    "737.gmsh_r",
    "748.flightdm_r",
    "749.fotonik3d_r",
    "765.roms_r",
    "766.femflow_r",
    "767.nest_r",
    "772.marian_r",
    "782.lbm_r",
]

# Define platform categories
PLATFORMS = {
    "desktop": [
        "AMD Ryzen",
        "Apple M1",
        "Apple M2",
        "Intel Core",
        "Intel Xeon w9-3595X",  # Workstation CPU
        "Qualcomm 8cx Gen3",
        "Qualcomm X1E80100",
        "Qualcomm X Elite",
        "Huawei Kirin X90",
        "Loongson 3A",
    ],
    "server": [
        "AMD EPYC",
        "AWS Graviton",
        "Ampere Altra",
        "Hygon C86",
        "IBM POWER",
        "Intel Xeon",
        "Kunpeng",
        "T-Head Yitian",
        "Loongson 3C",
        "Google Axion",
    ],
}

# Define compilation option groups
# IMPORTANT: Order matters! More specific groups must come before general ones
# For example, 'O3 -flto -ljemalloc' must come before 'O3 -flto'
OPT_FLAGS_GROUPS = {
    "O3 -march=native -flto -ljemalloc": ["-march=native", "-flto", "-ljemalloc"],
    "O3 -flto -ljemalloc": ["-flto", "-ljemalloc"],
    "O3 -flto": ["-flto"],
    "O3 -march=native": ["-march=native"],
    "O3": ["-O3"],
}

# CPU info mapping table (frequency, microarchitecture)
# IMPORTANT: Order matters! More specific keys must come before general ones
# For example, 'AWS Graviton 3E' must come before 'AWS Graviton 3'
# Format: cpu_base_name -> {opt_flags -> info}
# If opt_flags is None, it represents default value
CPU_INFO = [
    # Desktop - AMD
    ("AMD Ryzen 5 7500F", {None: "@ 5.0 GHz Zen 4"}),
    ("AMD Ryzen 7 5700X", {None: "@ 4.65 GHz Zen 3"}),
    ("AMD Ryzen 9 9950X", {None: "@ 5.7 GHz Zen 5"}),
    # Desktop - Apple
    ("Apple M1 E-Core", {None: "@ 2.1 GHz Icestorm"}),
    ("Apple M1 P-Core", {None: "@ 3.2 GHz Firestorm"}),
    ("Apple M2 E-Core", {None: "@ 2.4 GHz Blizzard"}),
    ("Apple M2 P-Core", {None: "@ 3.5 GHz Avalanche"}),
    # Desktop - Intel
    (
        "Intel Core i9-10980XE",
        {
            "O3-march=native": "@ 4.7 GHz (AVX-512 @ 4.0 GHz) Cascade Lake",
            None: "@ 4.7 GHz Cascade Lake",
        },
    ),
    ("Intel Core i9-12900KS P-Core", {None: "@ 5.5 GHz Golden Cove"}),
    ("Intel Core i9-12900KS E-Core", {None: "@ 4.1 GHz Gracemont"}),
    ("Intel Core i7-13700K P-Core", {None: "@ 5.4 GHz Raptor Cove"}),
    ("Intel Core i7-13700K E-Core", {None: "@ 4.2 GHz Gracemont"}),
    ("Intel Core i9-14900K P-Core", {None: "@ 6.0 GHz Raptor Cove"}),
    ("Intel Core i9-14900K E-Core", {None: "@ 4.4 GHz Gracemont"}),
    ("Intel Core i5-1135G7", {None: "@ 4.2 GHz Willow Cove"}),
    ("Intel Xeon w9-3595X", {None: "@ 4.5 GHz Golden Cove"}),
    # Desktop - Qualcomm
    ("Qualcomm 8cx Gen3 E-Core", {None: "@ 2.4 GHz Cortex-A78C"}),
    ("Qualcomm 8cx Gen3 P-Core", {None: "@ 3.0 GHz Cortex-X1C"}),
    ("Qualcomm X Elite", {None: "@ 4.0 GHz X Elite"}),
    ("Qualcomm X1E80100", {None: "@ 4.0 GHz X Elite"}),  # Keep original name
    # Server - AMD EPYC
    ("AMD EPYC 7551", {None: "@ 2.5 GHz Zen 1"}),
    ("AMD EPYC 7742", {None: "@ 3.4 GHz Zen 2"}),
    ("AMD EPYC 7H12", {None: "@ 3.3 GHz Zen 2"}),
    ("AMD EPYC 7K83", {None: "Zen 3"}),
    ("AMD EPYC 9754", {None: "@ 3.1 GHz Zen 4c"}),
    ("AMD EPYC 9755", {None: "@ 4.1 GHz Zen 5"}),
    ("AMD EPYC 9K65", {None: "@ 3.7 GHz Zen 5c"}),
    ("AMD EPYC 9K85", {None: "@ 4.1 GHz Zen 5"}),
    ("AMD EPYC 9R14", {None: "@ 3.7 GHz Zen 4"}),
    ("AMD EPYC 9R45", {None: "@ 4.5 GHz Zen 5"}),
    ("AMD EPYC 9T24", {None: "@ 3.7 GHz Zen 4"}),
    ("AMD EPYC 9T95", {None: "@ 3.7 GHz Zen 5c"}),
    # Server - AWS
    (
        "AWS Graviton 3E",
        {None: "@ 2.6 GHz Neoverse V1"},
    ),  # Must come before AWS Graviton 3
    ("AWS Graviton 3", {None: "@ 2.6 GHz Neoverse V1"}),
    ("AWS Graviton 4", {None: "@ 2.8 GHz Neoverse V2"}),
    ("AWS Graviton 5", {None: "@ 3.3 GHz Neoverse V3"}),
    # Server - Others
    ("Ampere Altra", {None: "@ 3.0 GHz Neoverse N1"}),
    ("Hygon C86 7390", {None: ""}),
    ("IBM POWER8NVL", {None: "@ 4.0 GHz POWER8"}),
    ("IBM POWER8", {None: "@ 3.2 GHz POWER8"}),
    ("IBM POWER9 3.2 GHz", {None: "@ 3.2 GHz POWER9"}),
    ("IBM POWER9 3.8 GHz", {None: "@ 3.8 GHz POWER9"}),
    ("Google Axion C4A", {None: "@ Neoverse V2"}),
    ("Google Axion N4A", {None: "@ Neoverse N3"}),
    (
        "Kunpeng 920 HuaweiCloud kc2",
        {None: "@ 2.9 GHz"},
    ),  # Must come before Kunpeng 920
    ("Kunpeng 920", {None: "@ 2.6 GHz TaiShan V110"}),
    ("T-Head Yitian 710", {None: "@ 3.0 GHz Neoverse N2"}),
    # Server - Intel Xeon
    ("Intel Xeon 6981E", {None: "Crestmont"}),
    ("Intel Xeon 6982P-C", {None: "@ 3.6 GHz Redwood Cove"}),
    ("Intel Xeon 6975P-C", {None: "@ 3.9 GHz Redwood Cove"}),
    ("Intel Xeon D-2146NT", {None: "@ 2.9 GHz Skylake"}),
    ("Intel Xeon E5-2603 v4", {None: "@ 1.7 GHz Broadwell"}),
    ("Intel Xeon E5-2680 v3", {None: "@ 3.3 GHz Haswell"}),
    ("Intel Xeon E5-2680 v4", {None: "@ 3.3 GHz Broadwell"}),
    ("Intel Xeon E5-4610 v2", {None: "@ 2.7 GHz Ivy Bridge EP"}),
    ("Intel Xeon Gold 6430", {None: "@ 2.6 GHz Golden Cove"}),
    ("Intel Xeon Platinum 8358P", {None: "@ 3.4 GHz Sunny Cove"}),
    ("Intel Xeon Platinum 8581C", {None: "@ 3.4 GHz Raptor Cove"}),
    ("Intel Xeon Platinum 8576C", {None: "Raptor Cove"}),
    # Server - Loongson
    ("Loongson 3A6000", {None: "@ 2.5 GHz LA664"}),
    ("Loongson 3C5000", {None: "@ 2.2 GHz LA464"}),
    ("Loongson 3C6000D", {None: "@ 2.1 GHz LA664"}),
    ("Loongson 3C6000S", {None: "@ 2.2 GHz LA664"}),
    # Mobile - Huawei Kirin
    ("Huawei Kirin X90 E-Core", {None: "@ 2.0 GHz"}),
    ("Huawei Kirin X90 P-Core", {None: "@ 2.3 GHz"}),
    ("Huawei Kirin X90 VM P-Core", {None: "@ 2.3 GHz"}),
    ("Huawei Kirin 9010 E-Core Full", {None: "@ 2.2 GHz"}),
    ("Huawei Kirin 9010 P-Core Best", {None: "@ 2.3 GHz"}),
    ("Huawei Kirin 9010 P-Core Full", {None: "@ 2.3 GHz"}),
]


def parse_cpu_name(filename):
    """Parse CPU name and compilation flags from filename"""
    # Remove .txt suffix
    name = filename.replace(".txt", "")

    # Split out final number (001, 002, etc.)
    parts = name.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        name = parts[0]

    # Split out compilation flags
    # Look for compilation flags from right to left
    # Possible formats: O3, O3-flto, O3-march=native, etc.
    cpu_parts = name.rsplit("_O", 1)
    if len(cpu_parts) == 2:
        cpu_name = cpu_parts[0]
        # Restore -O before compilation flags
        opt_flags = "-O" + cpu_parts[1]
    else:
        # May not have compilation flag marker
        cpu_name = name
        opt_flags = None

    # Process special CPU names - handle underscores first
    cpu_display = cpu_name.replace("_", " ")

    # Don't replace Qualcomm X1E80100 with Qualcomm X Elite - keep original name

    # Find and add CPU info - use ordered list for proper matching
    # More specific keys (like AWS Graviton 3E) must come before general ones (AWS Graviton 3)
    for cpu_key, info_dict in CPU_INFO:
        # Use exact match for the CPU name part (before @ or space)
        # This ensures AWS Graviton 3E doesn't match AWS Graviton 3
        cpu_display_parts = cpu_display.split("@")[0].strip()
        if cpu_display_parts == cpu_key or cpu_display_parts.startswith(cpu_key + " "):
            # Try to find info matching compilation flags
            # Strip leading '-' from opt_flags for matching (e.g., '-O3' -> 'O3')
            opt_flags_key = opt_flags.lstrip("-") if opt_flags else None

            if opt_flags_key in info_dict:
                info = info_dict[opt_flags_key]
            elif None in info_dict:
                info = info_dict[None]
            else:
                info = ""

            if info:  # If there is info, add it
                cpu_display = f"{cpu_key} {info}"
            break

    return cpu_display, opt_flags


def format_score(score):
    """Format score, determine decimal places based on size"""
    if score >= 100:
        # Scores >= 100 keep 1 decimal place
        return f"{score:.1f}"
    else:
        # Scores < 100 keep 2-3 significant figures
        if score >= 10:
            # 10-99 keep 1 decimal place
            return f"{score:.1f}"
        else:
            # Less than 10 keep 2 decimal places
            return f"{score:.2f}"


def parse_score_from_file(filepath, test_type="fp2017"):
    """Extract score from SPEC result file

    Args:
        filepath: Path to the result file
        test_type: 'int2017', 'fp2017', 'int2026', or 'fp2026'
    """
    # Determine the score pattern based on test type
    if test_type == "int2017":
        score_pattern = "SPECrate(R)2017_int_base"
        est_pattern = "Est. SPECrate(R)2017_int_base"
    elif test_type == "fp2017":
        score_pattern = "SPECrate(R)2017_fp_base"
        est_pattern = "Est. SPECrate(R)2017_fp_base"
    elif test_type == "int2026":
        score_pattern = "SPECrate(R)2026_int_base"
        est_pattern = "Est. SPECrate(R)2026_int_base"
    else:  # fp2026
        score_pattern = "SPECrate(R)2026_fp_base"
        est_pattern = "Est. SPECrate(R)2026_fp_base"

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            # Look for score line
            if score_pattern in line:
                # Format: SPECrate(R)2017_fp_base                 11.6
                parts = line.strip().split()
                if len(parts) >= 2:
                    try:
                        return float(parts[-1])
                    except ValueError:
                        pass
            elif est_pattern in line:
                # Format: Est. SPECrate(R)2017_fp_base            9.91
                parts = line.strip().split()
                if len(parts) >= 2:
                    try:
                        return float(parts[-1])
                    except ValueError:
                        pass
    return None


def get_platform_type(cpu_name):
    """Determine platform type based on CPU name"""
    # Check desktop platform first, ensure specific server CPUs (like w9-3595X) are correctly classified
    for keyword in PLATFORMS["desktop"]:
        if keyword in cpu_name:
            return "desktop"

    # Then check server platform
    for keyword in PLATFORMS["server"]:
        # Skip those already matched in desktop platform
        if keyword in cpu_name:
            # Intel Xeon w9-3595X is special, not classified as server
            if "w9-3595X" in cpu_name:
                continue
            return "server"

    # Default to server platform
    return "server"


def group_by_opt_flags(data):
    """Group by compilation flags

    IMPORTANT: Order matters! More specific groups (with more flags) must come first.
    This is handled by the order in OPT_FLAGS_GROUPS.
    """
    groups = {}

    for group_name, group_flags in OPT_FLAGS_GROUPS.items():
        groups[group_name] = []

    for item in data:
        cpu_name = item["cpu_name"]
        opt_flags = item.get("opt_flags", "")

        # Determine which group it belongs to
        # Try to match the most specific group first (by order in OPT_FLAGS_GROUPS)
        matched = False
        for group_name, group_flags in OPT_FLAGS_GROUPS.items():
            # Check if opt_flags contains all flags in this group
            if all(flag in opt_flags for flag in group_flags):
                # Also make sure we don't match a less specific group when a more specific one exists
                # For example, -O3-flto-ljemalloc should match 'O3 -flto -ljemalloc', not 'O3 -flto' or 'O3'
                groups[group_name].append(item)
                matched = True
                break

        if not matched and opt_flags:
            # Unmatched options
            groups.setdefault(opt_flags, []).append(item)

    return groups


def format_opt_flags_for_display(opt_flags):
    """Format optimization flags for display with proper spacing"""
    if not opt_flags:
        return opt_flags

    result = opt_flags

    # Format flags
    # -O3-flto-ljemalloc -> -O3 -flto -ljemalloc
    # -O3-march=native -> -O3 -march=native
    # -O3-flto -> -O3 -flto
    assert result[0] == "-"
    result = "-" + result[1:].replace("-", " -")

    return result


def merge_duplicate_cpus(items):
    """Merge items with the same CPU name, combining multiple scores on one line"""
    from collections import defaultdict
    import re

    cpu_dict = defaultdict(list)
    for item in items:
        # Use cpu_name + opt_flags as key
        key = (item["cpu_name"], item["opt_flags"])
        cpu_dict[key].append(item)

    merged = []
    for (cpu_name, opt_flags), entries in cpu_dict.items():
        if len(entries) == 1:
            merged.append(entries[0])
        else:
            # Sort by filename number (001, 002, etc.) instead of score
            def extract_file_number(item):
                match = re.search(r"_(\d+)\.txt$", item["filename"])
                if match:
                    return int(match.group(1))
                return 0

            entries_sorted = sorted(entries, key=extract_file_number)
            main_entry = entries_sorted[0].copy()
            # Create score links for all entries
            score_links = []
            for e in entries_sorted:
                score_str = format_score(e["score"])
                score_links.append(f"[{score_str}]({e['rel_path']})")
            main_entry["all_links"] = " ".join(score_links)
            merged.append(main_entry)
    return merged


def generate_section_markdown(data_dir, section_name, test_type="fp2017"):
    """Generate markdown content for a data directory (e.g., data-bookworm, data-trixie, data-forky, data-harmonyos)

    Args:
        data_dir: Path to data directory
        section_name: Name of the section for the header
        test_type: 'int2017' or 'fp2017'
    """
    # Determine the subdirectory name based on test type
    if test_type == "int2017":
        test_dir = data_dir / "int2017_rate1"
    elif test_type == "fp2017":
        test_dir = data_dir / "fp2017_rate1"
    elif test_type == "int2026":
        test_dir = data_dir / "int2026_rate1"
    else:  # fp2026
        test_dir = data_dir / "fp2026_rate1"

    if not test_dir.exists():
        return ""

    # Scan all files
    files = list(test_dir.glob("*.txt"))

    if not files:
        return ""

    # Determine the relative path prefix
    rel_path_prefix = f"./{data_dir.name}/{test_dir.name}"

    # Parse all data
    data = []
    for f in files:
        score = parse_score_from_file(f, test_type)
        if score is not None:
            cpu_display, opt_flags = parse_cpu_name(f.name)
            platform_type = get_platform_type(cpu_display)
            data.append(
                {
                    "cpu_name": cpu_display,
                    "opt_flags": opt_flags,
                    "score": score,
                    "platform_type": platform_type,
                    "filename": f.name,
                    "rel_path": f"{rel_path_prefix}/{f.name}",
                }
            )

    # Group by compilation flags first
    opt_groups = group_by_opt_flags(data)

    # Define compilation option group order based on test type
    # FP 2017 has -march=native data, order: -march=native -> O3 -> LTO -> LTO+Jemalloc
    # INT 2017 has no -march=native data, order: LTO+Jemalloc -> LTO -> O3
    if "HarmonyOS" in section_name:
        # For HarmonyOS, use different grouping
        opt_group_order = [
            ("O3 -flto", "-flto"),
        ]
    elif (test_type == "int2017" or test_type == "int2026"):
        # INT 2017: -march=native+LTO+Jemalloc -> LTO+Jemalloc -> LTO -> O3
        opt_group_order = [
            ("O3 -march=native -flto -ljemalloc", "-march=native -flto -ljemalloc"),
            ("O3 -flto -ljemalloc", "-flto -ljemalloc"),
            ("O3 -flto", "-flto"),
            ("O3", "-O3"),
        ]
    else:
        # FP 2017: -march=native -> O3 -> LTO -> LTO+Jemalloc
        opt_group_order = [
            ("O3 -march=native", "-march=native"),
            ("O3", "-O3"),
            ("O3 -flto", "-flto"),
            ("O3 -flto -ljemalloc", "-flto -ljemalloc"),
        ]

    # Generate markdown
    md_lines = [f"#### {section_name}\n\n"]

    # For HarmonyOS, group by platform type first (desktop/mobile), then by opt flags
    if "HarmonyOS" in section_name:
        # Split into desktop and mobile platforms
        desktop_data = [x for x in data if "X90" in x["cpu_name"]]
        mobile_data = [x for x in data if "9010" in x["cpu_name"]]

        if desktop_data:
            md_lines.append("桌面平台（LTO）：\n\n")
            desktop_items = merge_duplicate_cpus(desktop_data)
            for item in sorted(desktop_items, key=lambda x: x["cpu_name"]):
                opt_flags_display = format_opt_flags_for_display(item["opt_flags"])
                if "all_links" in item:
                    md_lines.append(
                        f"- {item['cpu_name']}（`{opt_flags_display}`）: {item['all_links']}\n"
                    )
                else:
                    score_str = format_score(item["score"])
                    md_lines.append(
                        f"- {item['cpu_name']}（`{opt_flags_display}`）: [{score_str}]({item['rel_path']})\n"
                    )

        if mobile_data:
            if md_lines and md_lines[-1].startswith("- "):
                md_lines.append("\n")
            md_lines.append("手机平台（LTO）：\n\n")
            mobile_items = merge_duplicate_cpus(mobile_data)
            for item in sorted(mobile_items, key=lambda x: x["cpu_name"]):
                opt_flags_display = format_opt_flags_for_display(item["opt_flags"])
                if "all_links" in item:
                    md_lines.append(
                        f"- {item['cpu_name']}（`{opt_flags_display}`）: {item['all_links']}\n"
                    )
                else:
                    score_str = format_score(item["score"])
                    md_lines.append(
                        f"- {item['cpu_name']}（`{opt_flags_display}`）: [{score_str}]({item['rel_path']})\n"
                    )
    else:
        # For Debian Bookworm/Trixie/Forky, group by platform type first (desktop/server), then by opt flags
        for platform_type, platform_title in [("desktop", "桌面"), ("server", "服务器")]:
            platform_items = [x for x in data if x["platform_type"] == platform_type]
            if not platform_items:
                continue

            # Process platform in opt flag order
            for opt_group_keys, header_flags in opt_group_order:
                matched_group = opt_groups.get(opt_group_keys, [])
                if not matched_group:
                    continue

                items = [x for x in matched_group if get_platform_type(x["cpu_name"]) == platform_type]
                if not items:
                    continue

                items = merge_duplicate_cpus(items)

                # Add blank line if previous section had entries
                if md_lines and md_lines[-1].startswith("- "):
                    md_lines.append("\n")

                parts = []
                if "-march=native" in header_flags:
                    parts.append("`-march=native`")
                if "-flto" in header_flags:
                    parts.append("LTO")
                if "-ljemalloc" in header_flags:
                    parts.append("Jemalloc")

                if len(parts) > 0:
                    md_lines.append(f"{platform_title}平台（{' + '.join(parts)}）：\n\n")
                else:
                    md_lines.append(f"{platform_title}平台：\n\n")

                for item in sorted(items, key=lambda x: x["cpu_name"]):
                    opt_flags_display = format_opt_flags_for_display(item["opt_flags"])
                    if "all_links" in item:
                        md_lines.append(
                            f"- {item['cpu_name']}（`{opt_flags_display}`）: {item['all_links']}\n"
                        )
                    else:
                        score_str = format_score(item["score"])
                        md_lines.append(
                            f"- {item['cpu_name']}（`{opt_flags_display}`）: [{score_str}]({item['rel_path']})\n"
                        )

    return "".join(md_lines)


def update_index_md(test_type="fp2017", output_md="spec-cpu-2017-rate.md"):
    """Update a spec-cpu-XXXX-rate.md file

    Args:
        test_type: 'int2017', 'fp2017', 'int2026', or 'fp2026'
        output_md: output markdown filename (default: spec-cpu-2017-rate.md)
    """
    # Determine display name
    year = "2026" if "2026" in test_type else "2017"
    type_label = "INT" if "int" in test_type else "FP"
    test_display = f"SPEC {type_label} {year}"

    # Generate new raw data content
    data_dirs = [
        (BASE_DIR / "data-forky", "Debian Forky"),
        (BASE_DIR / "data-trixie", "Debian Trixie"),
        (BASE_DIR / "data-bookworm", "Debian Bookworm"),
        (BASE_DIR / "data-harmonyos", "HarmonyOS"),
    ]

    md_content = []
    for data_dir, section_name in data_dirs:
        section_md = generate_section_markdown(data_dir, section_name, test_type)
        if section_md:
            md_content.append(section_md)

    # Join sections with blank lines between them
    new_content = "\n".join(md_content)

    # Read the target markdown file
    index_md_path = BASE_DIR / output_md
    with open(index_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the correct section based on test_type
    # First occurrence is for INT, second is for FP
    lines = content.split("\n")
    start_idx = -1
    end_idx = -1
    raw_data_count = 0

    # Determine which occurrence we need (1 for INT, 2 for FP)
    target_occurrence = 1 if "int" in test_type else 2

    for i, line in enumerate(lines):
        if line == "### 原始数据":
            raw_data_count += 1
            if raw_data_count == target_occurrence:
                start_idx = i
                break

    if start_idx == -1:
        print(f"Could not find {test_display} Rate-1 raw data section start")
        print("\nGenerated raw data content:")
        print(new_content)
        return

    # Find the end marker after start_idx
    for i in range(start_idx + 1, len(lines)):
        if lines[i] == "#### 备注":
            end_idx = i
            break

    if end_idx == -1:
        print(f"Could not find {test_display} Rate-1 raw data section end")
        print("\nGenerated raw data content:")
        print(new_content)
        return

    # Reconstruct the file:
    # Lines before start_idx (including "### 原始数据")
    # + blank line + new_content (which already has trailing newlines)
    # + blank line + lines from end_idx onwards
    before = "\n".join(lines[: start_idx + 1])
    after = "\n".join(lines[end_idx:])

    # Construct new content - new_content already has proper newlines
    # Add blank line after "### 原始数据" and before "#### 备注"
    new_index_md = before + "\n\n" + new_content + "\n" + after

    # Write back to file
    with open(index_md_path, "w", encoding="utf-8") as f:
        f.write(new_index_md)

    print(f"Updated {index_md_path}")
    print(f"Replaced {test_display} Rate-1 raw data section")


# ──────────────────────────────────────────────
# Metadata helpers for JSON export
# ──────────────────────────────────────────────

VENDOR_MAP = [
    ("AMD", "AMD"),
    ("Intel", "Intel"),
    ("Apple", "Apple"),
    ("Qualcomm", "Qualcomm"),
    ("AWS", "AWS"),
    ("Ampere", "Ampere"),
    ("Hygon", "Hygon"),
    ("IBM", "IBM"),
    ("Kunpeng", "Huawei"),
    ("T-Head", "T-Head"),
    ("Loongson", "Loongson"),
    ("Google", "Google"),
    ("Huawei", "Huawei"),
]


def detect_vendor(cpu_name):
    for pattern, vendor in VENDOR_MAP:
        if pattern in cpu_name:
            return vendor
    assert False, cpu_name


UARCH_VENDOR_MAP = [
    ("AMD", "AMD"),
    ("Intel", "Intel"),
    ("Apple", "Apple"),
    ("AWS Graviton", "ARM"),
    ("Google Axion", "ARM"),
    ("Ampere Altra", "ARM"),
    ("T-Head Yitian", "ARM"),
    ("Qualcomm X", "Qualcomm"),
    ("Qualcomm 8cx", "ARM"),
    ("Loongson", "Loongson"),
    ("IBM POWER", "IBM"),
    ("Hygon", "Hygon"),
    ("Kunpeng", "Huawei"),
    ("Huawei", "Huawei"),
]


def detect_uarch_vendor(cpu_name):
    for pattern, uarch_vendor in UARCH_VENDOR_MAP:
        if pattern in cpu_name:
            return uarch_vendor
    assert False, cpu_name


def detect_launch_date(cpu_name):
    """Launch year based on CPU name."""
    mapping = [
        ("AMD EPYC 7551", "2017"),
        ("AMD EPYC 7742", "2019"),
        ("AMD EPYC 7H12", "2019"),
        ("AMD EPYC 7K83", "2021"),
        ("AMD EPYC 9754", "2023"),
        ("AMD EPYC 9755", "2024"),
        ("AMD EPYC 9K65", "2024"),
        ("AMD EPYC 9K85", "2024"),
        ("AMD EPYC 9R14", "2023"),
        ("AMD EPYC 9R45", "2024"),
        ("AMD EPYC 9T24", "2023"),
        ("AMD EPYC 9T95", "2024"),
        ("AMD Ryzen 5 7500F", "2023"),
        ("AMD Ryzen 7 5700X", "2022"),
        ("AMD Ryzen 9 9950X", "2024"),
        ("AWS Graviton 3", "2022"),
        ("AWS Graviton 3E", "2022"),
        ("AWS Graviton 4", "2023"),
        ("AWS Graviton 5", "2026"),
        ("Ampere Altra", "2021"),
        ("Apple M1", "2020"),
        ("Apple M2", "2022"),
        ("Google Axion C4A", "2024"),
        ("Google Axion N4A", "2026"),
        ("Huawei Kirin 9010", "2024"),
        ("Huawei Kirin X90", "2025"),
        ("Hygon C86 7390", "2023"),
        ("IBM POWER8", "2014"),
        ("IBM POWER8NVL", "2016"),
        ("IBM POWER9", "2018"),
        ("Intel Core i5-1135G7", "2020"),
        ("Intel Core i7-13700K", "2022"),
        ("Intel Core i9-10980XE", "2019"),
        ("Intel Core i9-12900KS", "2022"),
        ("Intel Core i9-14900K", "2023"),
        ("Intel Xeon 6975P-C", "2024"),
        ("Intel Xeon 6981E", "2024"),
        ("Intel Xeon 6982P-C", "2024"),
        ("Intel Xeon D-2146NT", "2018"),
        ("Intel Xeon E5-2603 v4", "2016"),
        ("Intel Xeon E5-2680 v3", "2014"),
        ("Intel Xeon E5-2680 v4", "2016"),
        ("Intel Xeon E5-4610 v2", "2014"),
        ("Intel Xeon Gold 6430", "2023"),
        ("Intel Xeon Platinum 8358P", "2021"),
        ("Intel Xeon Platinum 8576C", "2023"),
        ("Intel Xeon Platinum 8581C", "2023"),
        ("Intel Xeon w9-3595X", "2024"),
        ("Kunpeng 920", "2019"),
        ("Loongson 3A6000", "2023"),
        ("Loongson 3C5000", "2022"),
        ("Loongson 3C6000", "2024"),
        ("Qualcomm 8cx Gen3", "2022"),
        ("Qualcomm X Elite", "2023"),
        ("Qualcomm X1E80100", "2024"),
        ("T-Head Yitian 710", "2022"),
    ]
    for pattern, year in mapping:
        if pattern in cpu_name:
            return year
    assert False, cpu_name


def detect_sector(cpu_name):
    """Determine sector from CPU name."""
    mobile_keywords = ["Kirin"]
    for kw in mobile_keywords:
        if kw in cpu_name:
            return "mobile"
    return get_platform_type(cpu_name)


def detect_isa(cpu_name):
    if "Intel" in cpu_name or "AMD" in cpu_name or "Hygon" in cpu_name:
        return "amd64"
    candidates = [
        "Graviton",
        "Huawei",
        "Kunpeng",
        "Qualcomm",
        "Apple",
        "Ampere",
        "Yitian",
        "Axion",
    ]
    if any(c in cpu_name for c in candidates):
        return "arm64"
    if "Loongson" in cpu_name:
        return "loong64"
    if "POWER" in cpu_name:
        return "ppc64el"
    assert False, cpu_name


# ──────────────────────────────────────────────
# JSON export
# ──────────────────────────────────────────────


def check_frequency_deviation(cpu_display, all_data, filepath, threshold_mhz=150):
    """Report if aggregate clock frequency deviates from named frequency by more than threshold."""
    import re

    m = re.search(r"@\s*([\d.]+)\s*GHz", cpu_display)
    if not m:
        return

    if "clock" not in all_data:
        return

    named_freq_mhz = float(m.group(1)) * 1000
    measured_freq_mhz = all_data["clock"]
    deviation = abs(measured_freq_mhz - named_freq_mhz)
    if deviation > threshold_mhz:
        print(
            f"WARNING: {filepath}: measured clock {measured_freq_mhz:.0f} MHz "
            f"deviates from named {named_freq_mhz:.0f} MHz by {deviation:.0f} MHz "
            f"({cpu_display})"
        )


def parse_per_benchmark_data(filepath, test_type="fp2017"):
    """Parse per-benchmark scores and perf data from a SPEC result file.

    Returns (per_benchmark, all_data) where all_data contains aggregate metrics.
    """
    if test_type == "int2017":
        benchmark_names = set(BENCHMARKS_INT_2017_RATE)
        score_marker = "SPECrate(R)2017_int_base"
    elif test_type == "fp2017":
        benchmark_names = set(BENCHMARKS_FP_2017_RATE)
        score_marker = "SPECrate(R)2017_fp_base"
    elif test_type == "int2026":
        benchmark_names = set(BENCHMARKS_INT_2026_RATE)
        score_marker = "SPECrate(R)2026_int_base"
    else:  # fp2026
        benchmark_names = set(BENCHMARKS_FP_2026_RATE)
        score_marker = "SPECrate(R)2026_fp_base"

    per_benchmark = {}
    all_data = {}
    found_delim = False
    passed_score = False

    key_map = {
        "time": "time",
        "clock freq": "clock",
        "instructions": "instructions",
        "branch instructions": "branch_instructions",
        "ipc": "ipc",
        "misprediction rate": "misprediction_rate",
        "mpki": "mpki",
    }

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("===="):
                found_delim = True
                continue

            parts = line.strip().split()
            parts = [p for p in parts if len(p) > 0]

            if line.strip() == "System Info:":
                break

            if found_delim:
                if "*" in line and len(parts) >= 4:
                    bm = parts[0]
                    if bm in benchmark_names:
                        try:
                            ratio = float(parts[3])
                        except ValueError:
                            continue
                        per_benchmark.setdefault(bm, {})["ratio"] = ratio

                if score_marker in line:
                    passed_score = True

                if passed_score and ":" in line and not line.startswith(" "):
                    colon = line.split(":", 1)
                    if len(colon) != 2:
                        continue
                    bm = colon[0].strip()
                    if bm == "all":
                        target = all_data
                    elif bm in benchmark_names:
                        target = per_benchmark.setdefault(bm, {})
                    else:
                        continue
                    rest = colon[1].strip()
                    if " = " not in rest:
                        continue
                    kv = rest.split(" = ", 1)
                    key_raw = kv[0].strip()
                    try:
                        value = float(kv[1].strip())
                    except ValueError:
                        continue
                    # strip units in parentheses
                    key_clean = key_raw.split(" (")[0].strip()
                    norm_key = key_map.get(key_clean, key_clean.replace(" ", "_"))
                    target[norm_key] = value
    return per_benchmark, all_data


def parse_compiler_from_file(filepath):
    """Parse compiler info from the first line of a SPEC result file.
    Format: 'Built with GCC 14.2.0 from Debian Trixie with -O3'
    """
    with open(filepath, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()
    if first_line.startswith("Built with "):
        parts = first_line.split()
        if len(parts) >= 4:
            return f"{parts[2]} {parts[3]}"
    return None


def parse_memory_from_file(filepath):
    """Parse memory info from a SPEC result file.
    Format: 'Memory: 4x Crucial Technology CT32G48C40U5.M16A1 32 GB 2 rank 4400'
    """
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("Memory:"):
                return simplify_memory(line[len("Memory:") :].strip())
    return None


def simplify_memory(mem_str):
    """Simplify memory string e.g. '4x 32 GB @ 4400'"""
    parts = mem_str.split()
    if not parts:
        return mem_str
    count = parts[0]
    size = ""
    for i, p in enumerate(parts):
        if p in ("GB", "MB") and i > 0:
            size = parts[i - 1] + " " + p
            break
    speed = parts[-1]
    result = count
    if size:
        result += " " + size
    if speed.isdigit():
        result += " @" + speed
    return result


def generate_json_data():
    """Generate a JSON-serialisable data structure with full metadata."""
    import json

    data_dirs = [
        (BASE_DIR / "data-forky", "forky"),
        (BASE_DIR / "data-trixie", "trixie"),
        (BASE_DIR / "data-bookworm", "bookworm"),
        (BASE_DIR / "data-harmonyos", "harmonyos"),
    ]
    test_types = ["int2017", "fp2017", "int2026", "fp2026"]

    result = {"version": 5, "data": {}}

    for data_dir, os_name in data_dirs:
        os_entry = {}
        for test_type in test_types:
            if test_type == "int2017":
                test_dir = data_dir / "int2017_rate1"
                suite_key = "int2017_rate1"
            elif test_type == "fp2017":
                test_dir = data_dir / "fp2017_rate1"
                suite_key = "fp2017_rate1"
            elif test_type == "int2026":
                test_dir = data_dir / "int2026_rate1"
                suite_key = "int2026_rate1"
            else:  # fp2026
                test_dir = data_dir / "fp2026_rate1"
                suite_key = "fp2026_rate1"

            if not test_dir.exists():
                continue

            files = list(test_dir.glob("*.txt"))
            if not files:
                continue

            entries = []
            for f in files:
                score = parse_score_from_file(f, test_type)
                if score is None:
                    continue
                cpu_display, opt_flags = parse_cpu_name(f.name)
                cpu_raw = cpu_display.split("@")[0].strip()
                opt_flags_display = (
                    format_opt_flags_for_display(opt_flags) if opt_flags else "-O3"
                )
                per_bm, all_data = parse_per_benchmark_data(f, test_type)
                if all_data:
                    check_frequency_deviation(cpu_display, all_data, str(f))
                entry = {
                    "cpu_name": cpu_display,
                    "cpu_raw": cpu_raw,
                    "opt_flags": opt_flags_display,
                    "score": score,
                    "vendor": detect_vendor(cpu_raw),
                    "uarch_vendor": detect_uarch_vendor(cpu_raw),
                    "launch_date": detect_launch_date(cpu_raw),
                    "sector": detect_sector(cpu_raw),
                    "isa": detect_isa(cpu_raw),
                    "os": os_name,
                    "test_type": suite_key,
                    "filename": f.name,
                    "rel_path": f"./{data_dir.name}/{test_dir.name}/{f.name}",
                    "compiler": parse_compiler_from_file(f),
                    "memory": parse_memory_from_file(f),
                }
                if per_bm:
                    entry["benchmarks"] = {}
                    for bm, bm_data in per_bm.items():
                        entry["benchmarks"][bm] = {}
                        if "ratio" in bm_data:
                            entry["benchmarks"][bm]["ratio"] = bm_data["ratio"]
                        for k in (
                            "time",
                            "clock",
                            "instructions",
                            "branch_instructions",
                            "ipc",
                            "misprediction_rate",
                            "mpki",
                        ):
                            if k in bm_data:
                                entry["benchmarks"][bm][k] = bm_data[k]
                entries.append(entry)
            if entries:
                os_entry[suite_key] = entries
        if os_entry:
            result["data"][os_name] = os_entry

    return result


def write_json(output_path=None):
    """Write benchmark data as JSON."""
    import json

    data = generate_json_data()
    if output_path is None:
        output_path = BASE_DIR / "benchmark_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Wrote {output_path}")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate raw data markdown for SPEC CPU 2017/2026",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate INT 2017 data and print to stdout
  %(prog)s --type int2017

  # Generate FP 2026 data and print to stdout
  %(prog)s --type fp2026

  # Generate INT 2026 data and update spec-cpu-2026-rate.md
  %(prog)s --type int2026 --update

  # Generate all data and update both markdown files
  %(prog)s --type all --update

  # Generate JSON for the web viewer
  %(prog)s --json
        """,
    )
    parser.add_argument(
        "--type",
        choices=["int2017", "fp2017", "int2026", "fp2026", "all"],
        default="all",
        help="Type of SPEC test to generate (default: all)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update markdown file(s) instead of printing to stdout",
    )
    parser.add_argument(
        "--json",
        nargs="?",
        const="default",
        metavar="OUTPUT_PATH",
        help="Generate JSON data file for the web viewer (default: ../benchmark_data.json)",
    )

    args = parser.parse_args()

    if args.json is not None:
        output_path = None if args.json == "default" else args.json
        write_json(output_path)
        return

    # Determine which test types to process
    type_map = {
        "int2017": ["int2017"],
        "fp2017": ["fp2017"],
        "int2026": ["int2026"],
        "fp2026": ["fp2026"],
        "all": ["int2017", "fp2017", "int2026", "fp2026"],
    }
    test_types = type_map[args.type]

    if args.update:
        # Update the appropriate markdown file(s)
        for test_type in test_types:
            if "2026" in test_type:
                update_index_md(test_type, output_md="spec-cpu-2026-rate.md")
            else:
                update_index_md(test_type, output_md="spec-cpu-2017-rate.md")
    else:
        # Only print generated markdown content
        data_dirs = [
            (BASE_DIR / "data-forky", "Debian forky"),
            (BASE_DIR / "data-trixie", "Debian Trixie"),
            (BASE_DIR / "data-bookworm", "Debian Bookworm"),
            (BASE_DIR / "data-harmonyos", "HarmonyOS"),
        ]

        for test_type in test_types:
            if len(test_types) > 1:
                # Print separator if processing both types
                print("=" * 80)
                print(f"# {test_type.upper()}")
                print("=" * 80)
                print()

            md_content = []
            for data_dir, section_name in data_dirs:
                section_md = generate_section_markdown(
                    data_dir, section_name, test_type
                )
                if section_md:
                    md_content.append(section_md)

            # Print generated markdown content
            print("".join(md_content))


if __name__ == "__main__":
    main()
