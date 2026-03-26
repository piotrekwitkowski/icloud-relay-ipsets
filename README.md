# iCloud Private Relay Egress IP Sets

Apple publishes ~287K individual CIDRs for iCloud Private Relay egress IPs. This repo collapses them into minimal IP sets by merging adjacent and overlapping ranges, updated daily via GitHub Actions.

Source: https://mask-api.icloud.com/egress-ip-ranges.csv

## Files

| File | Raw CIDRs | Collapsed CIDRs | Reduction |
|---|---|---|---|
| [all.txt](all.txt) | 286,877 | 13,356 | 95.3% |
| [ipv4.txt](ipv4.txt) | 41,701 | 3,265 | 92.2% |
| [ipv6.txt](ipv6.txt) | 245,176 | 10,091 | 95.9% |

## Reducing CIDR count

By default the script collapses adjacent/overlapping CIDRs. If the collapsed list is still too large, you can cap prefix lengths to shrink it further. Blocks smaller than the cap are promoted to their containing supernet, trading a small number of false positives for fewer entries.

```bash
# Cap IPv4 to /30, IPv6 to /60
python update.py --ipv4-cap 30 --ipv6-cap 60
```

| Flag | Effect | Example reduction |
|------|--------|-------------------|
| `--ipv4-cap 30` | Promotes /31, /32 → containing /30 | ~3,265 → ~1,662 entries |
| `--ipv6-cap 60` | Promotes /61–/64 → containing /60 | ~10,091 → ~6,955 entries |
