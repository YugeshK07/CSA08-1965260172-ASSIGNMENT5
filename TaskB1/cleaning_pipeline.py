import csv
import io
import math
from statistics import mean, median

RAW = """station,date,pm25
Adyar,2026-10-01,48
Adyar,2026-10-02,NA
Adyar,2026-10-03,
Guindy,2026-10-01,95
Guindy,2026-10-02,-5
Guindy,2026-10-03,121
Guindy,2026-10-04,1005
"""


def load_clean(text):
    """Return valid (station, date, pm25) rows; skip missing, negative and >999 values."""
    rows = []
    reader = csv.DictReader(io.StringIO(text))
    required = {"station", "date", "pm25"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise ValueError("CSV must contain station,date,pm25 columns")

    seen = set()
    for row in reader:
        station = (row.get("station") or "").strip()
        day = (row.get("date") or "").strip()
        raw_value = (row.get("pm25") or "").strip()
        if not station or not day or raw_value.upper() in {"", "NA", "N/A", "NULL"}:
            continue
        try:
            value = float(raw_value)
        except ValueError:
            continue
        if not math.isfinite(value) or value < 0 or value > 999:
            continue
        key = (station.casefold(), day)
        if key in seen:
            continue
        seen.add(key)
        rows.append((station, day, value))
    return rows


def min_max(values):
    if not values:
        return []
    low, high = min(values), max(values)
    if high == low:
        return [0.0 for _ in values]
    return [round((value-low)/(high-low), 3) for value in values]


def main():
    clean = load_clean(RAW)
    print("Cleaned rows:", clean)
    values = [row[2] for row in clean]
    print("Min-max:", min_max(values))
    print("Rejected or duplicate rows:", 7 - len(clean))
    return clean


if __name__ == "__main__":
    main()
