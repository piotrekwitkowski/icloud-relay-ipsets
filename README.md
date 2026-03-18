# iCloud Private Relay Egress IP Sets

Collapsed CIDR sets from Apple's [iCloud Private Relay egress IP ranges](https://mask-api.icloud.com/egress-ip-ranges.csv).

Updated daily via GitHub Actions.

## Files

- `ipv4.txt` — collapsed IPv4 CIDRs
- `ipv6.txt` — collapsed IPv6 CIDRs
- `all.txt` — both combined

## Reducing CIDR count

By default the script collapses adjacent/overlapping CIDRs. For further reduction (e.g. to fit within AWS WAF IP set limits of 10,000), you can cap prefix lengths. Blocks smaller than the cap are promoted to their containing supernet, trading a small number of false positives for fewer entries.

```bash
# Cap IPv4 to /30, IPv6 to /60
python update.py --ipv4-cap 30 --ipv6-cap 60
```

| Flag | Effect | Example reduction |
|------|--------|-------------------|
| `--ipv4-cap 30` | Promotes /31, /32 → containing /30 | ~3,265 → ~1,662 entries |
| `--ipv6-cap 60` | Promotes /61–/64 → containing /60 | ~10,091 → ~6,955 entries |
