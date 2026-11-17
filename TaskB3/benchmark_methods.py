import csv
import io
import random
import sqlite3
import time
from datetime import datetime, timedelta
from collections import defaultdict


def generate_csv(stations, hours=8760, seed=7):
    rng = random.Random(seed)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["station", "date", "pm25"])
    start = datetime(2026, 1, 1)
    for s in range(stations):
        name = f"Station_{s:03d}"
        for hour in range(hours):
            stamp = start + timedelta(hours=hour)
            writer.writerow([name, stamp.strftime("%Y-%m-%d %H:%M:%S"),
                             round(rng.uniform(5, 180), 2)])
    return output.getvalue()


def method_loops(rows):
    totals, counts = defaultdict(float), defaultdict(int)
    for station, day, value in rows:
        totals[station] += value
        counts[station] += 1
    return {name: totals[name] / counts[name] for name in totals}


def method_csv(csv_text):
    totals, counts = defaultdict(float), defaultdict(int)
    for row in csv.DictReader(io.StringIO(csv_text)):
        value = float(row["pm25"])
        totals[row["station"]] += value
        counts[row["station"]] += 1
    return {name: totals[name] / counts[name] for name in totals}


def method_pandas(csv_text):
    import pandas as pd
    frame = pd.read_csv(io.StringIO(csv_text))
    return frame.groupby("station")["pm25"].mean().to_dict()


def method_sql(rows):
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE readings(station TEXT, day TEXT, pm25 REAL)")
    con.executemany("INSERT INTO readings VALUES (?, ?, ?)", rows)
    result = dict(con.execute(
        "SELECT station, AVG(pm25) FROM readings GROUP BY station"
    ).fetchall())
    con.close()
    return result


def benchmark(stations):
    text = generate_csv(stations)
    raw_rows = list(csv.DictReader(io.StringIO(text)))
    rows = [(r["station"], r["date"], float(r["pm25"])) for r in raw_rows]
    methods = [("Python loops", lambda: method_loops(rows)),
               ("CSV DictReader", lambda: method_csv(text)),
               ("SQLite GROUP BY", lambda: method_sql(rows))]
    try:
        import pandas  # noqa: F401
        methods.insert(2, ("pandas groupby", lambda: method_pandas(text)))
    except ImportError:
        pass

    results = {}
    for name, fn in methods:
        start = time.perf_counter()
        answer = fn()
        elapsed = time.perf_counter() - start
        results[name] = (elapsed, answer)

    base = results["Python loops"][1]
    for name, (_, answer) in results.items():
        assert base.keys() == answer.keys()
        assert all(abs(base[k] - answer[k]) < 1e-8 for k in base)
    return len(rows), {name: value[0] for name, value in results.items()}


if __name__ == "__main__":
    for count in (1, 12, 120):
        n, timings = benchmark(count)
        print(f"{count} stations / {n:,} hourly readings")
        for method, seconds in timings.items():
            print(f"  {method}: {seconds:.6f} seconds")
