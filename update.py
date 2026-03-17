#!/usr/bin/env python3
"""Fetch iCloud Private Relay egress IPs and collapse into minimal CIDR sets."""

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


def collapse(networks):
    return list(ipaddress.collapse_addresses(sorted(networks)))


def write_file(path, networks):
    with open(path, "w") as f:
        for net in networks:
            f.write(f"{net}\n")


def count_addresses(networks):
    return sum(net.num_addresses for net in networks)


def main():
    print(f"Fetching {SOURCE_URL} ...")
    csv_text = fetch_csv(SOURCE_URL)
    raw_lines = [l for l in csv_text.strip().splitlines() if l.strip()]
    print(f"  raw lines: {len(raw_lines)}")

    ipv4_raw, ipv6_raw = parse_cidrs(csv_text)
    print(f"\nParsed CIDRs:")
    print(f"  IPv4: {len(ipv4_raw)}")
    print(f"  IPv6: {len(ipv6_raw)}")
    print(f"  total: {len(ipv4_raw) + len(ipv6_raw)}")

    ipv4 = collapse(ipv4_raw)
    ipv6 = collapse(ipv6_raw)
    all_nets = ipv4 + ipv6

    print(f"\nCollapsed CIDRs:")
    print(f"  IPv4: {len(ipv4_raw)} -> {len(ipv4)} ({100 - len(ipv4) * 100 / max(len(ipv4_raw), 1):.1f}% reduction)")
    print(f"  IPv6: {len(ipv6_raw)} -> {len(ipv6)} ({100 - len(ipv6) * 100 / max(len(ipv6_raw), 1):.1f}% reduction)")
    print(f"  total: {len(ipv4_raw) + len(ipv6_raw)} -> {len(all_nets)} ({100 - len(all_nets) * 100 / max(len(ipv4_raw) + len(ipv6_raw), 1):.1f}% reduction)")

    print(f"\nAddress coverage:")
    print(f"  IPv4: {count_addresses(ipv4):,} addresses")
    print(f"  IPv6: {count_addresses(ipv6):,} addresses")

    write_file(os.path.join(OUTPUT_DIR, "ipv4.txt"), ipv4)
    write_file(os.path.join(OUTPUT_DIR, "ipv6.txt"), ipv6)
    write_file(os.path.join(OUTPUT_DIR, "all.txt"), all_nets)

    print(f"\nWritten:")
    print(f"  ipv4.txt ({len(ipv4)} entries)")
    print(f"  ipv6.txt ({len(ipv6)} entries)")
    print(f"  all.txt  ({len(all_nets)} entries)")


if __name__ == "__main__":
    main()
