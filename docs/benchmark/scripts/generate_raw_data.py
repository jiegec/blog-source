#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate raw data markdown content for SPEC CPU 2017 Rate-1 (both INT and FP)"""

import os
import glob
from pathlib import Path

# Parent directory of script (docs/benchmark)
BASE_DIR = Path(__file__).parent.parent.absolute()

# Define platform categories
PLATFORMS = {
    'desktop': [
        'AMD Ryzen',
        'Apple M1',
        'Intel Core',
        'Intel Xeon w9-3595X',  # Workstation CPU
        'Qualcomm 8cx Gen3',
        'Qualcomm X1E80100',
        'Qualcomm X Elite',
        'Huawei Kirin X90',
        'Loongson 3A',
    ],
    'server': [
        'AMD EPYC',
        'AWS Graviton',
        'Ampere Altra',
        'Hygon C86',
        'IBM POWER',
        'Intel Xeon',
        'Kunpeng',
        'T-Head Yitian',
        'Loongson 3C',
        'Google Axion',
    ],
}

# Define compilation option groups
# IMPORTANT: Order matters! More specific groups must come before general ones
# For example, 'O3 -flto -ljemalloc' must come before 'O3 -flto'
OPT_FLAGS_GROUPS = {
    'O3 -flto -ljemalloc': ['-flto', '-ljemalloc'],
    'O3 -flto': ['-flto'],
    'O3 -march=native': ['-march=native'],
    'O3': ['-O3'],
}

# CPU info mapping table (frequency, microarchitecture)
# IMPORTANT: Order matters! More specific keys must come before general ones
# For example, 'AWS Graviton 3E' must come before 'AWS Graviton 3'
# Format: cpu_base_name -> {opt_flags -> info}
# If opt_flags is None, it represents default value
CPU_INFO = [
    # Desktop - AMD
    ('AMD Ryzen 5 7500F', {None: '@ 5.0 GHz Zen 4'}),
    ('AMD Ryzen 7 5700X', {None: '@ 4.65 GHz Zen 3'}),
    ('AMD Ryzen 9 9950X', {None: '@ 5.7 GHz Zen 5'}),
    # Desktop - Apple
    ('Apple M1 E-Core', {None: '@ 2.1 GHz Icestorm'}),
    ('Apple M1 P-Core', {None: '@ 3.2 GHz Firestorm'}),
    # Desktop - Intel
    ('Intel Core i9-10980XE', {
        'O3-march=native': '@ 4.7 GHz (AVX-512 @ 4.0 GHz) Cascade Lake',
        None: '@ 4.7 GHz Cascade Lake',
    }),
    ('Intel Core i9-12900KS P-Core', {None: '@ 5.5 GHz Golden Cove'}),
    ('Intel Core i9-12900KS E-Core', {None: '@ 4.1 GHz Gracemont'}),
    ('Intel Core i9-14900K P-Core', {None: '@ 6.0 GHz Raptor Cove'}),
    ('Intel Core i9-14900K E-Core', {None: '@ 4.4 GHz Gracemont'}),
    ('Intel Xeon w9-3595X', {None: '@ 4.5 GHz Golden Cove'}),
    # Desktop - Qualcomm
    ('Qualcomm 8cx Gen3 E-Core', {None: '@ 2.4 GHz Cortex-A78C'}),
    ('Qualcomm 8cx Gen3 P-Core', {None: '@ 3.0 GHz Cortex-X1C'}),
    ('Qualcomm X Elite', {None: '@ 4.0 GHz X Elite'}),
    ('Qualcomm X1E80100', {None: '@ 4.0 GHz X Elite'}),  # Keep original name
    # Server - AMD EPYC
    ('AMD EPYC 7551', {None: '@ 2.5 GHz Zen 1'}),
    ('AMD EPYC 7742', {None: '@ 3.4 GHz Zen 2'}),
    ('AMD EPYC 7H12', {None: '@ 3.3 GHz Zen 2'}),
    ('AMD EPYC 7K83', {None: 'Zen 3'}),
    ('AMD EPYC 9754', {None: '@ 3.1 GHz Zen 4c'}),
    ('AMD EPYC 9755', {None: '@ 4.1 GHz Zen 5'}),
    ('AMD EPYC 9K65', {None: '@ 3.7 GHz Zen 5c'}),
    ('AMD EPYC 9K85', {None: '@ 4.1 GHz Zen 5'}),
    ('AMD EPYC 9R14', {None: '@ 3.7 GHz Zen 4'}),
    ('AMD EPYC 9R45', {None: '@ 4.5 GHz Zen 5'}),
    ('AMD EPYC 9T24', {None: '@ 3.7 GHz Zen 4'}),
    ('AMD EPYC 9T95', {None: '@ 3.7 GHz Zen 5c'}),
    # Server - AWS
    ('AWS Graviton 3E', {None: '@ 2.6 GHz Neoverse V1'}),  # Must come before AWS Graviton 3
    ('AWS Graviton 3', {None: '@ 2.6 GHz Neoverse V1'}),
    ('AWS Graviton 4', {None: '@ 2.8 GHz Neoverse V2'}),
    # Server - Others
    ('Ampere Altra', {None: '@ 3.0 GHz Neoverse N1'}),
    ('Hygon C86 7390', {None: ''}),
    ('IBM POWER8NVL', {None: '@ 4.0 GHz POWER8'}),
    ('Google Axion N4A', {None: '@ Neoverse N3'}),
    ('Kunpeng 920 HuaweiCloud kc2', {None: '@ 2.9 GHz'}),  # Must come before Kunpeng 920
    ('Kunpeng 920', {None: '@ 2.6 GHz TaiShan V110'}),
    ('T-Head Yitian 710', {None: '@ 3.0 GHz Neoverse N2'}),
    # Server - Intel Xeon
    ('Intel Xeon 6981E', {None: 'Crestmont'}),
    ('Intel Xeon 6982P-C', {None: '@ 3.6 GHz Redwood Cove'}),
    ('Intel Xeon 6975P-C', {None: '@ 3.9 GHz Redwood Cove'}),
    ('Intel Xeon D-2146NT', {None: '@ 2.9 GHz Skylake'}),
    ('Intel Xeon E5-2603 v4', {None: '@ 1.7 GHz Broadwell'}),
    ('Intel Xeon E5-2680 v3', {None: '@ 3.3 GHz Haswell'}),
    ('Intel Xeon E5-2680 v4', {None: '@ 3.3 GHz Broadwell'}),
    ('Intel Xeon E5-4610 v2', {None: '@ 2.7 GHz Ivy Bridge EP'}),
    ('Intel Xeon Gold 6430', {None: '@ 2.6 GHz Golden Cove'}),
    ('Intel Xeon Platinum 8358P', {None: '@ 3.4 GHz Sunny Cove'}),
    ('Intel Xeon Platinum 8581C', {None: '@ 3.4 GHz Raptor Cove'}),
    ('Intel Xeon Platinum 8576C', {None: 'Raptor Cove'}),
    # Server - Loongson
    ('Loongson 3A6000', {None: '@ 2.5 GHz LA664'}),
    ('Loongson 3C5000', {None: '@ 2.2 GHz LA464'}),
    ('Loongson 3C6000', {None: '@ 2.2 GHz LA664'}),
    # Mobile - Huawei Kirin
    ('Huawei Kirin X90 E-Core', {None: '@ 2.0 GHz'}),
    ('Huawei Kirin X90 P-Core', {None: '@ 2.3 GHz'}),
    ('Huawei Kirin X90 VM P-Core', {None: '@ 2.3 GHz'}),
    ('Huawei Kirin 9010 E-Core Full', {None: '@ 2.2 GHz'}),
    ('Huawei Kirin 9010 P-Core Best', {None: '@ 2.3 GHz'}),
    ('Huawei Kirin 9010 P-Core Full', {None: '@ 2.3 GHz'}),
]


def parse_cpu_name(filename):
    """Parse CPU name and compilation flags from filename"""
    # Remove .txt suffix
    name = filename.replace('.txt', '')

    # Split out final number (001, 002, etc.)
    parts = name.rsplit('_', 1)
    if len(parts) == 2 and parts[1].isdigit():
        name = parts[0]

    # Split out compilation flags
    # Look for compilation flags from right to left
    # Possible formats: O3, O3-flto, O3-march=native, etc.
    cpu_parts = name.rsplit('_O', 1)
    if len(cpu_parts) == 2:
        cpu_name = cpu_parts[0]
        # Restore -O before compilation flags
        opt_flags = '-O' + cpu_parts[1]
    else:
        # May not have compilation flag marker
        cpu_name = name
        opt_flags = None

    # Process special CPU names - handle underscores first
    cpu_display = cpu_name.replace('_', ' ')

    # Don't replace Qualcomm X1E80100 with Qualcomm X Elite - keep original name

    # Find and add CPU info - use ordered list for proper matching
    # More specific keys (like AWS Graviton 3E) must come before general ones (AWS Graviton 3)
    for cpu_key, info_dict in CPU_INFO:
        # Use exact match for the CPU name part (before @ or space)
        # This ensures AWS Graviton 3E doesn't match AWS Graviton 3
        cpu_display_parts = cpu_display.split('@')[0].strip()
        if cpu_display_parts == cpu_key or cpu_display_parts.startswith(cpu_key + ' '):
            # Try to find info matching compilation flags
            # Strip leading '-' from opt_flags for matching (e.g., '-O3' -> 'O3')
            opt_flags_key = opt_flags.lstrip('-') if opt_flags else None

            if opt_flags_key in info_dict:
                info = info_dict[opt_flags_key]
            elif None in info_dict:
                info = info_dict[None]
            else:
                info = ''

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


def parse_score_from_file(filepath, test_type='fp2017'):
    """Extract score from SPEC result file

    Args:
        filepath: Path to the result file
        test_type: 'int2017' or 'fp2017'
    """
    # Determine the score pattern based on test type
    if test_type == 'int2017':
        score_pattern = 'SPECrate(R)2017_int_base'
        est_pattern = 'Est. SPECrate(R)2017_int_base'
    else:  # fp2017
        score_pattern = 'SPECrate(R)2017_fp_base'
        est_pattern = 'Est. SPECrate(R)2017_fp_base'

    with open(filepath, 'r', encoding='utf-8') as f:
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
    for keyword in PLATFORMS['desktop']:
        if keyword in cpu_name:
            return 'desktop'

    # Then check server platform
    for keyword in PLATFORMS['server']:
        # Skip those already matched in desktop platform
        if keyword in cpu_name:
            # Intel Xeon w9-3595X is special, not classified as server
            if 'w9-3595X' in cpu_name:
                continue
            return 'server'

    # Default to server platform
    return 'server'


def group_by_opt_flags(data):
    """Group by compilation flags

    IMPORTANT: Order matters! More specific groups (with more flags) must come first.
    This is handled by the order in OPT_FLAGS_GROUPS.
    """
    groups = {}

    for group_name, group_flags in OPT_FLAGS_GROUPS.items():
        groups[group_name] = []

    for item in data:
        cpu_name = item['cpu_name']
        opt_flags = item.get('opt_flags', '')

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

    # Handle specific patterns in order (most specific first)
    # -O3-flto-ljemalloc -> -O3 -flto -ljemalloc
    if '-O3-flto-ljemalloc' in result:
        result = result.replace('-O3-flto-ljemalloc', '-O3 -flto -ljemalloc')
    # -O3-march=native -> -O3 -march=native
    elif '-O3-march=native' in result:
        result = result.replace('-O3-march=native', '-O3 -march=native')
    # -O3-flto -> -O3 -flto
    elif '-O3-flto' in result:
        result = result.replace('-O3-flto', '-O3 -flto')

    return result


def merge_duplicate_cpus(items):
    """Merge items with the same CPU name, combining multiple scores on one line"""
    from collections import defaultdict
    import re

    cpu_dict = defaultdict(list)
    for item in items:
        # Use cpu_name + opt_flags as key
        key = (item['cpu_name'], item['opt_flags'])
        cpu_dict[key].append(item)

    merged = []
    for (cpu_name, opt_flags), entries in cpu_dict.items():
        if len(entries) == 1:
            merged.append(entries[0])
        else:
            # Sort by filename number (001, 002, etc.) instead of score
            def extract_file_number(item):
                match = re.search(r'_(\d+)\.txt$', item['filename'])
                if match:
                    return int(match.group(1))
                return 0

            entries_sorted = sorted(entries, key=extract_file_number)
            main_entry = entries_sorted[0].copy()
            # Create score links for all entries
            score_links = []
            for e in entries_sorted:
                score_str = format_score(e['score'])
                score_links.append(f"[{score_str}]({e['rel_path']})")
            main_entry['all_links'] = ' '.join(score_links)
            merged.append(main_entry)
    return merged


def generate_section_markdown(data_dir, section_name, test_type='fp2017'):
    """Generate markdown content for a data directory (e.g., data, data-trixie, data-harmonyos)

    Args:
        data_dir: Path to data directory
        section_name: Name of the section for the header
        test_type: 'int2017' or 'fp2017'
    """
    # Determine the subdirectory name based on test type
    if test_type == 'int2017':
        test_dir = data_dir / 'int2017_rate1'
    else:  # fp2017
        test_dir = data_dir / 'fp2017_rate1'

    if not test_dir.exists():
        return ""

    # Scan all files
    files = list(test_dir.glob('*.txt'))

    if not files:
        return ""

    # Determine the relative path prefix
    rel_path_prefix = f'./{data_dir.name}/{test_dir.name}'

    # Parse all data
    data = []
    for f in files:
        score = parse_score_from_file(f, test_type)
        if score is not None:
            cpu_display, opt_flags = parse_cpu_name(f.name)
            platform_type = get_platform_type(cpu_display)
            data.append({
                'cpu_name': cpu_display,
                'opt_flags': opt_flags,
                'score': score,
                'platform_type': platform_type,
                'filename': f.name,
                'rel_path': f'{rel_path_prefix}/{f.name}',
            })

    # Group by compilation flags first
    opt_groups = group_by_opt_flags(data)

    # Define compilation option group order based on test type
    # FP 2017 has -march=native data, order: -march=native -> O3 -> LTO -> LTO+Jemalloc
    # INT 2017 has no -march=native data, order: LTO+Jemalloc -> LTO -> O3
    if 'HarmonyOS' in section_name:
        # For HarmonyOS, use different grouping
        opt_group_order = [
            ('O3 -flto', '-flto'),
        ]
    elif test_type == 'int2017':
        # INT 2017: LTO+Jemalloc -> LTO -> O3
        opt_group_order = [
            ('O3 -flto -ljemalloc', '-flto -ljemalloc'),
            ('O3 -flto', '-flto'),
            ('O3', '-O3'),
        ]
    else:
        # FP 2017: -march=native -> O3 -> LTO -> LTO+Jemalloc
        opt_group_order = [
            ('O3 -march=native', '-march=native'),
            ('O3', '-O3'),
            ('O3 -flto', '-flto'),
            ('O3 -flto -ljemalloc', '-flto -ljemalloc'),
        ]

    # Generate markdown
    md_lines = [f"#### {section_name}\n\n"]

    # For HarmonyOS, group by platform type first (desktop/mobile), then by opt flags
    if 'HarmonyOS' in section_name:
        # Split into desktop and mobile platforms
        desktop_data = [x for x in data if 'X90' in x['cpu_name']]
        mobile_data = [x for x in data if '9010' in x['cpu_name']]

        if desktop_data:
            md_lines.append("桌面平台（LTO）：\n\n")
            desktop_items = merge_duplicate_cpus(desktop_data)
            for item in sorted(desktop_items, key=lambda x: x['cpu_name']):
                opt_flags_display = format_opt_flags_for_display(item['opt_flags'])
                if 'all_links' in item:
                    md_lines.append(f"- {item['cpu_name']}（`{opt_flags_display}`）: {item['all_links']}\n")
                else:
                    score_str = format_score(item['score'])
                    md_lines.append(f"- {item['cpu_name']}（`{opt_flags_display}`）: [{score_str}]({item['rel_path']})\n")

        if mobile_data:
            # Add blank line before mobile platforms section
            if md_lines and not md_lines[-1].endswith('\n\n'):
                md_lines.append('\n')
            md_lines.append("手机平台（LTO）：\n\n")
            mobile_items = merge_duplicate_cpus(mobile_data)
            for item in sorted(mobile_items, key=lambda x: x['cpu_name']):
                opt_flags_display = format_opt_flags_for_display(item['opt_flags'])
                if 'all_links' in item:
                    md_lines.append(f"- {item['cpu_name']}（`{opt_flags_display}`）: {item['all_links']}\n")
                else:
                    score_str = format_score(item['score'])
                    md_lines.append(f"- {item['cpu_name']}（`{opt_flags_display}`）: [{score_str}]({item['rel_path']})\n")
    else:
        # For Debian Bookworm/Trixie, group by platform type first (desktop/server), then by opt flags
        # Desktop platforms
        desktop_data = [x for x in data if x['platform_type'] == 'desktop']

        # Process desktop platforms in opt flag order
        for opt_group_keys, header_flags in opt_group_order:
            # Get the group directly using opt_group_keys (which is the key in opt_groups)
            matched_group = opt_groups.get(opt_group_keys, [])

            if not matched_group:
                continue

            # Filter to desktop items only
            desktop_items = [x for x in matched_group if get_platform_type(x['cpu_name']) == 'desktop']

            if not desktop_items:
                continue

            # Merge duplicate CPUs
            desktop_items = merge_duplicate_cpus(desktop_items)

            # Add blank line before certain sections
            # For FP 2017: add before `-O3` (transition from -march=native)
            # For INT 2017: add before `-O3` (transition from LTO) and before `LTO` (transition from LTO+Jemalloc)
            if md_lines and not md_lines[-1].endswith('\n\n'):
                if header_flags == '-O3':
                    md_lines.append('\n')
                elif header_flags == '-flto' and test_type == 'int2017':
                    md_lines.append('\n')

            # Generate title based on header_flags
            if '-march=native' in header_flags:
                md_lines.append("桌面平台（`-march=native`）：\n\n")
            elif '-flto' in header_flags:
                if '-ljemalloc' in header_flags:
                    md_lines.append("桌面平台（LTO + Jemalloc）：\n\n")
                else:
                    md_lines.append("桌面平台（LTO）：\n\n")
            else:  # -O3 only
                md_lines.append("桌面平台：\n\n")

            for item in sorted(desktop_items, key=lambda x: x['cpu_name']):
                opt_flags_display = format_opt_flags_for_display(item['opt_flags'])
                if 'all_links' in item:
                    md_lines.append(f"- {item['cpu_name']}（`{opt_flags_display}`）: {item['all_links']}\n")
                else:
                    score_str = format_score(item['score'])
                    md_lines.append(f"- {item['cpu_name']}（`{opt_flags_display}`）: [{score_str}]({item['rel_path']})\n")

        # Server platforms
        server_data = [x for x in data if x['platform_type'] == 'server']

        # Add blank line before server platforms section
        if md_lines and not md_lines[-1].endswith('\n\n'):
            md_lines.append('\n')

        # Process server platforms in opt flag order
        for opt_group_keys, header_flags in opt_group_order:
            # Get the group directly using opt_group_keys (which is the key in opt_groups)
            matched_group = opt_groups.get(opt_group_keys, [])

            if not matched_group:
                continue

            # Filter to server items only
            server_items = [x for x in matched_group if get_platform_type(x['cpu_name']) == 'server']

            if not server_items:
                continue

            # Merge duplicate CPUs
            server_items = merge_duplicate_cpus(server_items)

            # Add blank line before certain sections
            # For FP 2017: add before `-O3` (transition from -march=native)
            # For INT 2017: add before `-O3` (transition from LTO) and before `LTO` (transition from LTO+Jemalloc)
            if md_lines and not md_lines[-1].endswith('\n\n'):
                if header_flags == '-O3':
                    md_lines.append('\n')
                elif header_flags == '-flto' and test_type == 'int2017':
                    md_lines.append('\n')

            if '-march=native' in header_flags:
                md_lines.append("服务器平台（`-march=native`）：\n\n")
            elif '-flto' in header_flags:
                if '-ljemalloc' in header_flags:
                    md_lines.append("服务器平台（LTO + Jemalloc）：\n\n")
                else:
                    md_lines.append("服务器平台（LTO）：\n\n")
            elif header_flags == '-O3':
                md_lines.append("服务器平台：\n\n")

            for item in sorted(server_items, key=lambda x: x['cpu_name']):
                opt_flags_display = format_opt_flags_for_display(item['opt_flags'])
                if 'all_links' in item:
                    md_lines.append(f"- {item['cpu_name']}（`{opt_flags_display}`）: {item['all_links']}\n")
                else:
                    score_str = format_score(item['score'])
                    md_lines.append(f"- {item['cpu_name']}（`{opt_flags_display}`）: [{score_str}]({item['rel_path']})\n")

    return ''.join(md_lines)


def update_index_md(test_type='fp2017'):
    """Update index.md file

    Args:
        test_type: 'int2017' or 'fp2017'
    """
    # Generate new raw data content
    data_dirs = [
        (BASE_DIR / 'data', 'Debian Bookworm'),
        (BASE_DIR / 'data-trixie', 'Debian Trixie'),
        (BASE_DIR / 'data-harmonyos', 'HarmonyOS'),
    ]

    md_content = []
    for data_dir, section_name in data_dirs:
        section_md = generate_section_markdown(data_dir, section_name, test_type)
        if section_md:
            md_content.append(section_md)

    # Join sections with blank lines between them
    new_content = '\n'.join(md_content)

    # Read index.md
    index_md_path = BASE_DIR / 'index.md'
    with open(index_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the correct section based on test_type
    # First occurrence is for int2017, second is for fp2017
    lines = content.split('\n')
    start_idx = -1
    end_idx = -1
    raw_data_count = 0

    # Determine which occurrence we need (1 for int2017, 2 for fp2017)
    target_occurrence = 1 if test_type == 'int2017' else 2

    for i, line in enumerate(lines):
        if line == "### 原始数据":
            raw_data_count += 1
            if raw_data_count == target_occurrence:
                start_idx = i
                break

    if start_idx == -1:
        test_name = "SPEC INT 2017" if test_type == 'int2017' else "SPEC FP 2017"
        print(f"Could not find {test_name} Rate-1 raw data section start")
        print("\nGenerated raw data content:")
        print(new_content)
        return

    # Find the end marker after start_idx
    for i in range(start_idx + 1, len(lines)):
        if lines[i] == "#### 备注":
            end_idx = i
            break

    if end_idx == -1:
        test_name = "SPEC INT 2017" if test_type == 'int2017' else "SPEC FP 2017"
        print(f"Could not find {test_name} Rate-1 raw data section end")
        print("\nGenerated raw data content:")
        print(new_content)
        return

    # Reconstruct the file:
    # Lines before start_idx (including "### 原始数据")
    # + blank line + new_content (which already has trailing newlines)
    # + blank line + lines from end_idx onwards
    before = '\n'.join(lines[:start_idx + 1])
    after = '\n'.join(lines[end_idx:])

    # Construct new content - new_content already has proper newlines
    # Add blank line after "### 原始数据" and before "#### 备注"
    new_index_md = before + '\n\n' + new_content + '\n' + after

    # Write back to file
    with open(index_md_path, 'w', encoding='utf-8') as f:
        f.write(new_index_md)

    test_name = "SPEC INT 2017" if test_type == 'int2017' else "SPEC FP 2017"
    print(f"Updated {index_md_path}")
    print(f"Replaced {test_name} Rate-1 raw data section")


def main():
    """Main function"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate raw data markdown for SPEC CPU 2017',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate INT 2017 data and print to stdout
  %(prog)s --type int2017

  # Generate FP 2017 data and print to stdout
  %(prog)s --type fp2017

  # Generate both and update index.md
  %(prog)s --type both --update

  # Generate INT 2017 data and update index.md
  %(prog)s --type int2017 --update
        '''
    )
    parser.add_argument(
        '--type',
        choices=['int2017', 'fp2017', 'both'],
        default='both',
        help='Type of SPEC test to generate (default: fp2017)'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update index.md file instead of printing to stdout'
    )

    args = parser.parse_args()

    # Determine which test types to process
    if args.type == 'both':
        test_types = ['int2017', 'fp2017']
    else:
        test_types = [args.type]

    if args.update:
        # Update index.md
        for test_type in test_types:
            update_index_md(test_type)
    else:
        # Only print generated markdown content
        data_dirs = [
            (BASE_DIR / 'data', 'Debian Bookworm'),
            (BASE_DIR / 'data-trixie', 'Debian Trixie'),
            (BASE_DIR / 'data-harmonyos', 'HarmonyOS'),
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
                section_md = generate_section_markdown(data_dir, section_name, test_type)
                if section_md:
                    md_content.append(section_md)

            # Print generated markdown content
            print(''.join(md_content))


if __name__ == '__main__':
    main()
