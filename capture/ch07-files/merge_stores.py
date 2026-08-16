#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge all store CSV files in 门店销售/ into one summary CSV,
add a store-name column, drop fully duplicate rows, and report
total amount per store sorted descending."""
import csv
import glob
import os

SRC_DIR = "门店销售"
OUT_FILE = "汇总.csv"

# 1) Read every store file
rows = []
for path in sorted(glob.glob(os.path.join(SRC_DIR, "*.csv"))):
    store = os.path.basename(path).rsplit(".", 1)[0]  # e.g. "01-朝阳店"
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            continue
        # Add the store-name column to each row
        for row in reader:
            if not row or all(c.strip() == "" for c in row):
                continue  # skip blank lines
            rows.append(row + [store])

# 2) Drop fully duplicate rows (keep first occurrence)
seen = set()
unique_rows = []
for row in rows:
    key = tuple(row)
    if key not in seen:
        seen.add(key)
        unique_rows.append(row)

# 3) Write the summary CSV
out_header = header + ["门店"]
with open(OUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(out_header)
    writer.writerows(unique_rows)

# 4) Total amount per store, descending
totals = {}
for row in unique_rows:
    store = row[-1]
    try:
        amount = float(row[3])
    except (ValueError, IndexError):
        continue
    totals[store] = totals.get(store, 0.0) + amount

print(f"输入文件数: {len(glob.glob(os.path.join(SRC_DIR, '*.csv')))}")
print(f"合并后原始行数: {len(rows)}")
print(f"去重后行数: {len(unique_rows)} (删除 {len(rows) - len(unique_rows)} 行)")
print(f"已写入: {OUT_FILE}")
print("\n各门店总金额(从高到低):")
for store, total in sorted(totals.items(), key=lambda kv: kv[1], reverse=True):
    print(f"{store}: {total:,.0f}")
