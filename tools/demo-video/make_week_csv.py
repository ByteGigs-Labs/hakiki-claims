import csv
import os
import tempfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "claims.csv"
OUTPUT = Path(os.environ.get("DEMO_CSV", Path(tempfile.gettempdir()) / "hk-demo-week.csv"))
PICK = [1, 2, 3, 5, 6, *range(13, 32)]

rows = list(csv.reader(SOURCE.open()))
header, body = rows[0], rows[1:]
week = [header]
for number, index in enumerate(PICK, start=1):
    row = list(body[index - 1])
    row[0] = f"wk-{number:03d}"
    row[1] = row[1].replace("SYN-P", "SYN-W")
    week.append(row)
csv.writer(OUTPUT.open("w", newline="")).writerows(week)
print(f"{len(week) - 1} claims written to {OUTPUT}")
