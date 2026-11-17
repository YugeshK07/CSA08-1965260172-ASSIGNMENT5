import csv
import io
import sqlite3
import tempfile
from pathlib import Path


def load_rows(csv_text):
    accepted, errors = [], []
    try:
        reader = csv.DictReader(io.StringIO(csv_text))
        if not reader.fieldnames or not {"station", "date", "pm25"}.issubset(reader.fieldnames):
            raise ValueError("missing required CSV columns")
        for line_no, row in enumerate(reader, start=2):
            try:
                station = (row["station"] or "").strip()
                day = (row["date"] or "").strip()
                value = float(row["pm25"])
                if not station or not day or value < 0 or value > 999:
                    raise ValueError("invalid station/date/value")
                accepted.append((station, day, value))
            except (ValueError, TypeError, KeyError) as exc:
                errors.append((line_no, str(exc)))
    except (csv.Error, ValueError) as exc:
        errors.append((0, str(exc)))
    return accepted, errors


def inspect_file(path):
    try:
        with open(path, "r", encoding="utf-8", newline="") as file:
            return load_rows(file.read())
    except UnicodeDecodeError as exc:
        return [], [(0, f"UnicodeDecodeError: {exc}")]
    except OSError as exc:
        return [], [(0, f"{type(exc).__name__}: {exc}")]


def run_database_demo():
    readings = [
        ("Adyar", "2026-10-01", 48.0),
        ("Guindy", "2026-10-01", 95.0),
        ("Guindy", "2026-10-03", 121.0),
        ("Adyar", "2026-10-04", 60.0),
    ]
    con = sqlite3.connect(":memory:")
    con.execute("""CREATE TABLE air_quality (
        station TEXT NOT NULL, day TEXT NOT NULL, pm25 REAL NOT NULL,
        PRIMARY KEY(station, day))""")
    con.executemany(
        "INSERT OR REPLACE INTO air_quality(station, day, pm25) VALUES (?, ?, ?)",
        readings
    )
    con.commit()

    def station_average(name):
        row = con.execute(
            "SELECT AVG(pm25) FROM air_quality WHERE station = ?", (name,)
        ).fetchone()
        return round(row[0], 1) if row[0] is not None else None

    print("Adyar average:", station_average("Adyar"))
    print("Guindy average:", station_average("Guindy"))
    print("Injection attempt:", station_average("Adyar' OR '1'='1"))
    con.close()


def sentiment_score(text):
    positive = {"good", "clean", "fast", "helpful", "improved"}
    negative = {"bad", "dirty", "slow", "rude", "smoke", "broken"}
    negators = {"not", "never", "no"}
    words = text.lower().replace(",", "").replace(".", "").split()
    total = 0
    negate = False
    for word in words:
        if word in negators:
            negate = True
            continue
        value = 1 if word in positive else -1 if word in negative else 0
        if value:
            total += -value if negate else value
            negate = False
    return total


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        cases = {
            "valid.csv": "station,date,pm25\nAdyar,2026-10-01,48\n",
            "missing_column.csv": "station,date\nAdyar,2026-10-01\n",
            "wrong_delimiter.csv": "station;date;pm25\nAdyar;2026-10-01;48\n",
            "empty.csv": "",
        }
        for filename, content in cases.items():
            (directory / filename).write_text(content, encoding="utf-8")
        # Write a byte sequence that is invalid UTF-8 to test decoding failure.
        (directory / "bad_encoding.csv").write_bytes(b"station,date,pm25\nAdyar,\x96,48\n")
        for path in sorted(directory.iterdir()):
            accepted, errors = inspect_file(path)
            print(f"{path.name}: accepted={len(accepted)}, errors={errors}")

    run_database_demo()
    stress = [
        "Great, another smoky day. (sarcasm)",
        "The service is not bad.",
        "The air is clean but the response was slow.",
        "The staff were not helpful.",
        "The report is never good.",
    ]
    print("Sentiment stress tests:")
    for sentence in stress:
        print(sentiment_score(sentence), "|", sentence)
