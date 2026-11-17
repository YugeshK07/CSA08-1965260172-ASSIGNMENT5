import csv
import io
from pathlib import Path
from cleaning_pipeline import RAW, load_clean

def main():
    rows = load_clean(RAW)
    out = Path(__file__).with_name("cleaned_readings.csv")
    with out.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["station", "date", "pm25"])
        writer.writerows(rows)
    try:
        import matplotlib.pyplot as plt
        stations = sorted({row[0] for row in rows})
        for station in stations:
            subset = [(day, value) for name, day, value in rows if name == station]
            plt.plot([x[0] for x in subset], [x[1] for x in subset], marker="o", label=station)
        plt.title("PM2.5 readings by station")
        plt.xlabel("Date")
        plt.ylabel("PM2.5 (µg/m³)")
        plt.legend()
        plt.xticks(rotation=30)
        plt.tight_layout()
        plt.savefig(Path(__file__).with_name("pm25_trend.png"), dpi=150)
        plt.close()
        print("Chart saved as pm25_trend.png")
    except ImportError:
        print("matplotlib is not installed; CSV was still generated.")
    print("Cleaned CSV saved:", out)

if __name__ == "__main__":
    main()
