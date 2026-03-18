#!/usr/bin/env python3
"""Fetch iCloud Private Relay egress IPs and collapse into minimal CIDR sets."""

import argparse
import ipaddress
import os
import sys
import urllib.request

SOURCE_URL = "https://mask-api.icloud.com/egress-ip-ranges.csv"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def fetch_csv(url):
    req = urllib.request.Request(url, headers={"User-Agent": "icloud-relay-ipsets/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def parse_cidrs(csv_text):
    ipv4, ipv6 = [], []
    for line in csv_text.strip().splitlines():
        cidr = line.split(",", 1)[0].strip()
        if not cidr:
            continue
        try:
            net = ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            print(f"  skipping invalid CIDR: {cidr}", file=sys.stderr)
            continue
        if net.version == 4:
            ipv4.append(net)
        else:
            ipv6.append(net)
    return ipv4, ipv6


def cap_prefixes(networks, max_prefix):
    capped = []
    for net in networks:
        if net.prefixlen > max_prefix:
            capped.append(net.supernet(new_prefix=max_prefix))
        else:
            capped.append(net)
    return list(set(capped))


def collapse(networks):
    return list(ipaddress.collapse_addresses(sorted(networks)))


def update_readme(output_dir, ipv4_raw_count, ipv6_raw_count, ipv4_count, ipv6_count):
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "r") as f:
        content = f.read()

    stats = (
        "## Files\n"
        "\n"
        "| File | Raw CIDRs | Collapsed CIDRs | Reduction |\n"
        "|---|---|---|---|\n"
        f"| [ipv4.txt](ipv4.txt) | {ipv4_raw_count:,} | {ipv4_count:,} | {100 - ipv4_count * 100 / max(ipv4_raw_count, 1):.1f}% |\n"
        f"| [ipv6.txt](ipv6.txt) | {ipv6_raw_count:,} | {ipv6_count:,} | {100 - ipv6_count * 100 / max(ipv6_raw_count, 1):.1f}% |\n"
        f"| [all.txt](all.txt) | {ipv4_raw_count + ipv6_raw_count:,} | {ipv4_count + ipv6_count:,} | {100 - (ipv4_count + ipv6_count) * 100 / max(ipv4_raw_count + ipv6_raw_count, 1):.1f}% |\n"
    )

    import re
    stats_pattern = r"## Files\n\n\| File[^#]*?\n(?=\n##|\Z)"
    if re.search(stats_pattern, content):
        content = re.sub(stats_pattern, stats, content)
    else:
        content = content.replace("## Reducing", stats + "\n## Reducing")

    with open(readme_path, "w") as f:
        f.write(content)


def write_file(path, networks):
    with open(path, "w") as f:
        for net in networks:
            f.write(f"{net}\n")


def count_addresses(networks):
    return sum(net.num_addresses for net in networks)


def main():
    parser = argparse.ArgumentParser(description="Fetch and collapse iCloud Private Relay egress IPs.")
    parser.add_argument("--ipv4-cap", type=int, default=None, metavar="N",
                        help="Cap IPv4 prefix length to /N (e.g. 30). Smaller blocks are promoted to their containing /N supernet.")
    parser.add_argument("--ipv6-cap", type=int, default=None, metavar="N",
                        help="Cap IPv6 prefix length to /N (e.g. 60). Smaller blocks are promoted to their containing /N supernet.")
    args = parser.parse_args()

    print(f"Fetching {SOURCE_URL} ...")
    csv_text = fetch_csv(SOURCE_URL)
    raw_lines = [l for l in csv_text.strip().splitlines() if l.strip()]
    print(f"  raw lines: {len(raw_lines)}")

    ipv4_raw, ipv6_raw = parse_cidrs(csv_text)
    ipv4_raw_count, ipv6_raw_count = len(ipv4_raw), len(ipv6_raw)
    print(f"\nParsed CIDRs:")
    print(f"  IPv4: {len(ipv4_raw)}")
    print(f"  IPv6: {len(ipv6_raw)}")
    print(f"  total: {len(ipv4_raw) + len(ipv6_raw)}")

    if args.ipv4_cap:
        print(f"\nCapping IPv4 to /{args.ipv4_cap}")
        ipv4_raw = cap_prefixes(ipv4_raw, args.ipv4_cap)
    if args.ipv6_cap:
        print(f"Capping IPv6 to /{args.ipv6_cap}")
        ipv6_raw = cap_prefixes(ipv6_raw, args.ipv6_cap)

    ipv4 = collapse(ipv4_raw)
    ipv6 = collapse(ipv6_raw)
    all_nets = ipv4 + ipv6

    print(f"\nCollapsed CIDRs:")
    print(f"  IPv4: {len(ipv4)} entries")
    print(f"  IPv6: {len(ipv6)} entries")
    print(f"  total: {len(all_nets)} entries")

    print(f"\nAddress coverage:")
    print(f"  IPv4: {count_addresses(ipv4):,} addresses")
    print(f"  IPv6: {count_addresses(ipv6):,} addresses")

    write_file(os.path.join(OUTPUT_DIR, "ipv4.txt"), ipv4)
    write_file(os.path.join(OUTPUT_DIR, "ipv6.txt"), ipv6)
    write_file(os.path.join(OUTPUT_DIR, "all.txt"), all_nets)
    update_readme(OUTPUT_DIR, ipv4_raw_count, ipv6_raw_count, len(ipv4), len(ipv6))

    print(f"\nWritten:")
    print(f"  ipv4.txt ({len(ipv4)} entries)")
    print(f"  ipv6.txt ({len(ipv6)} entries)")
    print(f"  all.txt  ({len(all_nets)} entries)")


if __name__ == "__main__":
    main()
