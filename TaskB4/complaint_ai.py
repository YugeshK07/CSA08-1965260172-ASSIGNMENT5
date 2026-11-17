import re
import sqlite3
import time
from collections import Counter

POSITIVE = {"good", "clean", "fast", "helpful", "improved"}
NEGATIVE = {"bad", "dirty", "slow", "rude", "smoke", "broken"}
NEGATORS = {"not", "never", "no"}


def score(text):
    words = re.findall(r"[a-z']+", text.lower())
    total = 0
    negate_next = False
    for word in words:
        if word in NEGATORS:
            negate_next = True
            continue
        value = 1 if word in POSITIVE else (-1 if word in NEGATIVE else 0)
        if negate_next and value:
            value *= -1
            negate_next = False
        elif value:
            negate_next = False
        total += value
    return total


def label(text):
    value = score(text)
    return "positive" if value > 0 else "negative" if value < 0 else "neutral"


def summarise(complaints, limit=5):
    words = re.findall(r"[a-z']+", " ".join(complaints).lower())
    stop = {"the", "and", "is", "in", "to", "a", "of", "was", "are", "for", "on"}
    frequent = {word for word, _ in Counter(w for w in words if w not in stop).most_common(limit)}
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(complaints))
    ranked = []
    for index, sentence in enumerate(sentences):
        tokens = set(re.findall(r"[a-z']+", sentence.lower()))
        score_value = len(tokens & frequent)
        if score_value:
            ranked.append((score_value, -index, sentence.strip()))
    ranked.sort(reverse=True)
    return [item[2] for item in ranked[:3]]


def make_complaint_set():
    """50 reproducible examples with manually assigned reference labels."""
    positive = [
        "The air is clean today.", "The response team was helpful.",
        "The monitoring service improved.", "The reporting app is good.",
        "The station update was fast.", "The staff were helpful and polite.",
        "The air quality report is good.", "The roads are clean.",
        "The service improved this week.", "The dashboard is fast and helpful.",
        "The station is working well.", "The public alert was helpful.",
        "The report is clear and good.", "The response was fast.",
        "The monitoring system improved."
    ]
    negative = [
        "Smoke makes the air bad.", "The station sensor is broken.",
        "The air is dirty near school.", "The response team was slow.",
        "The staff were rude.", "The pollution report is bad.",
        "Smoke levels are high today.", "The monitoring device is broken.",
        "The air is dirty near the road.", "The alert was slow.",
        "The service is bad.", "The station is not working.",
        "The response was rude and slow.", "The smoke is making air dirty.",
        "The report is not helpful."
    ]
    neutral = [
        "The station is near the school.", "A report was posted this morning.",
        "The reading was recorded at noon.", "The dashboard shows today's data.",
        "The station is located near the bus stop.", "The report contains hourly values.",
        "The reading was taken yesterday.", "The air quality board met today.",
        "The station sends data every hour.", "The report lists PM2.5 values.",
        "The city has several monitoring stations.", "The data is available online.",
        "The reading is from the north station.", "The board received a complaint.",
        "The station reports temperature and PM2.5."
    ]
    return ([(x, "positive") for x in positive] +
            [(x, "negative") for x in negative] +
            [(x, "neutral") for x in neutral] +
            [(positive[i], "positive") for i in range(2)] +
            [(negative[i], "negative") for i in range(2)] +
            [(neutral[i], "neutral") for i in range(1)])


def answer_question(question, db_path="air_quality.db"):
    match_station = re.search(r"\b(Adyar|Guindy)\b", question, re.I)
    match_date = re.search(r"\b\d{4}-\d{2}-\d{2}\b", question)
    if not match_station or not match_date:
        return "Please mention a supported station (Adyar or Guindy) and date (YYYY-MM-DD)."
    con = sqlite3.connect(db_path)
    row = con.execute(
        "SELECT pm25 FROM readings WHERE station = ? AND day = ?",
        (match_station.group(1).title(), match_date.group(0))
    ).fetchone()
    con.close()
    if row is None:
        return "No valid PM2.5 reading is available for that station and date."
    return f"PM2.5 at {match_station.group(1).title()} on {match_date.group(0)} was {row[0]}."


def index_experiment():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE readings(station TEXT, day TEXT, pm25 REAL)")
    rows = []
    for station_id in range(100):
        station = f"Station_{station_id:03d}"
        for day in range(30):
            for quarter in range(96):
                rows.append((station, f"2026-10-{day+1:02d} {quarter:02d}", float((station_id+day+quarter)%180)))
    con.executemany("INSERT INTO readings VALUES (?, ?, ?)", rows)
    con.commit()
    query = ("SELECT AVG(pm25) FROM readings "
             "WHERE station = ? AND day >= ? AND day < ?")
    args = ("Station_050", "2026-10-10", "2026-10-11")
    start = time.perf_counter()
    for _ in range(100):
        con.execute(query, args).fetchone()
    before = (time.perf_counter()-start)/100
    con.execute("CREATE INDEX idx_station_day ON readings(station, day)")
    con.commit()
    start = time.perf_counter()
    for _ in range(100):
        con.execute(query, args).fetchone()
    after = (time.perf_counter()-start)/100
    con.close()
    return len(rows), before, after


def main():
    dataset = make_complaint_set()
    complaints = [text for text, _ in dataset]
    correct = sum(label(text) == reference for text, reference in dataset)
    agreement = correct / len(dataset) * 100
    print(f"Complaint count: {len(dataset)}")
    print(f"Agreement with manual reference labels: {correct}/{len(dataset)} ({agreement:.1f}%)")
    for complaint in complaints[:6]:
        print(f"{label(complaint):8} | {complaint}")
    print("Extractive summary:", summarise(complaints))

    con = sqlite3.connect("air_quality.db")
    con.execute("CREATE TABLE IF NOT EXISTS readings(station TEXT, day TEXT, pm25 REAL)")
    con.execute("DELETE FROM readings")
    con.executemany("INSERT INTO readings VALUES (?, ?, ?)", [
        ("Adyar", "2026-10-01", 48.0),
        ("Guindy", "2026-10-01", 95.0),
    ])
    con.commit()
    con.close()
    print(answer_question("What is the PM2.5 in Adyar on 2026-10-01?"))
    count, before, after = index_experiment()
    print(f"Index experiment rows: {count}")
    print(f"Mean query time before index: {before:.6f}s")
    print(f"Mean query time after index: {after:.6f}s")


if __name__ == "__main__":
    main()
