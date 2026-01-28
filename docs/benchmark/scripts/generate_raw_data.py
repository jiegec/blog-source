#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate raw data markdown content for SPEC FP 2017 Rate-1"""

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
OPT_FLAGS_GROUPS = {
    'O3 -march=native': ['-march=native'],
    'O3': ['-O3'],
    'O3 -flto': ['-flto'],
    'O3 -flto -ljemalloc': ['-flto', '-ljemalloc'],
}

# CPU info mapping table (frequency, microarchitecture)
# IMPORTANT: Order matters! More specific keys must come before general ones
# For example, 'AWS Graviton 3E' must come before 'AWS Graviton 3'
# Format: cpu_base_name -> {opt_flags -> info}
# If opt_flags is None, it represents default value
CPU_INFO = [
    # Desktop - AMD
    ('AMD Ryzen 5 7500F', {None: 'Zen 4'}),  # No frequency in original
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


def parse_score_from_file(filepath):
    """Extract score from SPEC result file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            # Look for score line
            if 'SPECrate(R)2017_fp_base' in line:
                # Format: SPECrate(R)2017_fp_base                 11.6
                parts = line.strip().split()
                if len(parts) >= 2:
                    try:
                        return float(parts[-1])
                    except ValueError:
                        pass
            elif 'Est. SPECrate(R)2017_fp_base' in line:
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
    """Group by compilation flags"""
    groups = {}

    for group_name, group_flags in OPT_FLAGS_GROUPS.items():
        groups[group_name] = []

    for item in data:
        cpu_name = item['cpu_name']
        opt_flags = item.get('opt_flags', '')

        # Determine which group it belongs to
        matched = False
        for group_name, group_flags in OPT_FLAGS_GROUPS.items():
            # Check if it contains all required flags
            if all(flag in opt_flags for flag in group_flags):
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
    # Add space between -O3 and other flags
    # -O3-march=native -> -O3 -march=native
    # -O3-flto -> -O3 -flto
    # -O3-flto-ljemalloc -> -O3 -flto -ljemalloc
    result = opt_flags
    if result.startswith('-O3'):
        result = result.replace('-O3-flto', '-O3 -flto')
        result = result.replace('-O3-march=native', '-O3 -march=native')
        # Handle -O3-flto-ljemalloc -> -O3 -flto -ljemalloc
        if '-ljemalloc' in result and '-flto' in result:
            result = result.replace('-O3 -flto', '-O3 -flto -ljemalloc').replace('-ljemalloc', '-ljemalloc').replace('-O3 -flto -ljemalloc -ljemalloc', '-O3 -flto -ljemalloc')
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


def generate_section_markdown(data_dir, section_name):
    """Generate markdown content for a data directory (e.g., data, data-trixie, data-harmonyos)"""
    fp2017_dir = data_dir / 'fp2017_rate1'

    if not fp2017_dir.exists():
        return ""

    # Scan all files
    files = list(fp2017_dir.glob('*.txt'))

    if not files:
        return ""

    # Parse all data
    data = []
    for f in files:
        score = parse_score_from_file(f)
        if score is not None:
            cpu_display, opt_flags = parse_cpu_name(f.name)
            platform_type = get_platform_type(cpu_display)
            data.append({
                'cpu_name': cpu_display,
                'opt_flags': opt_flags,
                'score': score,
                'platform_type': platform_type,
                'filename': f.name,
                'rel_path': f'./{data_dir.name}/fp2017_rate1/{f.name}',
            })

    # Group by compilation flags first
    opt_groups = group_by_opt_flags(data)

    # Define compilation option group order
    # For Debian Bookworm/Trixie
    opt_group_order = [
        ('O3 -march=native', '-march=native'),
        ('O3', '-O3'),
        ('O3 -flto', '-flto'),
        ('O3 -flto -ljemalloc', '-flto -ljemalloc'),
    ]

    # For HarmonyOS, use different grouping
    if 'HarmonyOS' in section_name:
        opt_group_order = [
            ('O3 -flto', '-flto'),
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
            # Find the group that matches this combination
            matched_group = None
            for group_name in opt_groups.keys():
                if group_name == 'O3 -march=native' and header_flags == '-march=native':
                    matched_group = opt_groups[group_name]
                    break
                elif group_name == 'O3' and header_flags == '-O3':
                    matched_group = opt_groups[group_name]
                    break
                elif group_name == 'O3 -flto' and header_flags == '-flto':
                    matched_group = opt_groups[group_name]
                    break
                elif group_name == 'O3 -flto -ljemalloc' and header_flags == '-flto -ljemalloc':
                    matched_group = opt_groups[group_name]
                    break
                elif header_flags in group_name:
                    matched_group = opt_groups[group_name]
                    break

            if not matched_group or not matched_group:
                continue

            # Filter to desktop items only
            desktop_items = [x for x in matched_group if get_platform_type(x['cpu_name']) == 'desktop']

            if not desktop_items:
                continue

            # Merge duplicate CPUs
            desktop_items = merge_duplicate_cpus(desktop_items)

            # Add header
            # Add blank line before `-O3` group (transition from -march=native)
            if header_flags == '-O3' and md_lines and not md_lines[-1].endswith('\n\n'):
                md_lines.append('\n')

            if '-march=native' in header_flags:
                md_lines.append("桌面平台（`-march=native`）：\n\n")
            elif '-flto' in header_flags:
                if '-ljemalloc' in header_flags:
                    md_lines.append("桌面平台（LTO + Jemalloc）：\n\n")
                else:
                    md_lines.append("桌面平台（LTO）：\n\n")
            elif header_flags == '-O3':
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
            # Find the group that matches this combination
            matched_group = None
            for group_name in opt_groups.keys():
                if group_name == 'O3 -march=native' and header_flags == '-march=native':
                    matched_group = opt_groups[group_name]
                    break
                elif group_name == 'O3' and header_flags == '-O3':
                    matched_group = opt_groups[group_name]
                    break
                elif group_name == 'O3 -flto' and header_flags == '-flto':
                    matched_group = opt_groups[group_name]
                    break
                elif group_name == 'O3 -flto -ljemalloc' and header_flags == '-flto -ljemalloc':
                    matched_group = opt_groups[group_name]
                    break
                elif header_flags in group_name:
                    matched_group = opt_groups[group_name]
                    break

            if not matched_group or not matched_group:
                continue

            # Filter to server items only
            server_items = [x for x in matched_group if get_platform_type(x['cpu_name']) == 'server']

            if not server_items:
                continue

            # Merge duplicate CPUs
            server_items = merge_duplicate_cpus(server_items)

            # Add header
            # Add blank line before `-O3` group (transition from -march=native)
            if header_flags == '-O3' and md_lines and not md_lines[-1].endswith('\n\n'):
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


def update_index_md():
    """Update index.md file"""
    # Generate new raw data content
    data_dirs = [
        (BASE_DIR / 'data', 'Debian Bookworm'),
        (BASE_DIR / 'data-trixie', 'Debian Trixie'),
        (BASE_DIR / 'data-harmonyos', 'HarmonyOS'),
    ]

    md_content = []
    for data_dir, section_name in data_dirs:
        section_md = generate_section_markdown(data_dir, section_name)
        if section_md:
            md_content.append(section_md)

    # Join sections with blank lines between them
    new_content = '\n'.join(md_content)

    # Read index.md
    index_md_path = BASE_DIR / 'index.md'
    with open(index_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the fp2017 section (the second "### 原始数据" in the file)
    # First occurrence is for int2017, second is for fp2017
    lines = content.split('\n')
    start_idx = -1
    end_idx = -1
    raw_data_count = 0

    for i, line in enumerate(lines):
        if line == "### 原始数据":
            raw_data_count += 1
            if raw_data_count == 2:  # Second occurrence is fp2017
                start_idx = i
                break

    if start_idx == -1:
        print("Could not find SPEC FP 2017 Rate-1 raw data section start")
        print("\nGenerated raw data content:")
        print(new_content)
        return

    # Find the end marker after start_idx
    for i in range(start_idx + 1, len(lines)):
        if lines[i] == "#### 备注":
            end_idx = i
            break

    if end_idx == -1:
        print("Could not find SPEC FP 2017 Rate-1 raw data section end")
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

    print(f"Updated {index_md_path}")
    print(f"Replaced SPEC FP 2017 Rate-1 raw data section")


def main():
    """Main function"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--update':
        # Update index.md
        update_index_md()
    else:
        # Only print generated markdown content
        data_dirs = [
            (BASE_DIR / 'data', 'Debian Bookworm'),
            (BASE_DIR / 'data-trixie', 'Debian Trixie'),
            (BASE_DIR / 'data-harmonyos', 'HarmonyOS'),
        ]

        md_content = []
        for data_dir, section_name in data_dirs:
            section_md = generate_section_markdown(data_dir, section_name)
            if section_md:
                md_content.append(section_md)

        # Print generated markdown content
        print(''.join(md_content))


if __name__ == '__main__':
    main()
