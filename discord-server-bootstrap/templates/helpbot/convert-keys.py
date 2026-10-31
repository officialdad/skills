#!/usr/bin/env python3
"""Converts the organizers' keys txt (name line, then `email:` and `key:` lines) to secrets/keys.csv."""
import csv
import re
import sys

source, target = sys.argv[1], sys.argv[2]
with open(source, encoding="utf-8-sig") as file:
    blocks = [block for block in re.split(r"\n\s*\n", file.read().strip()) if block.strip()]

rows = []
for block in blocks:
    name = re.sub(r"^\s*\d+\.\s*", "", block.splitlines()[0]).strip()
    emails = re.findall(r"email:\s*(\S+)", block)
    keys = re.findall(r"key:\s*(sk-\S+)", block)
    if len(emails) != 1 or len(keys) != 1:
        sys.exit(f"block for '{name}' needs exactly one email and one key")
    rows.append((emails[0].lower(), keys[0], name))

if len({row[0] for row in rows}) != len(rows):
    sys.exit("duplicate email in the source")

with open(target, "w", encoding="utf-8", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(("email", "key", "name"))
    writer.writerows(rows)
print(f"wrote {len(rows)} rows to {target}", file=sys.stderr)
