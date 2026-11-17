# B3 – Loops vs libraries vs SQL
Run `python benchmark_methods.py`. It generates 8,760 hourly readings per station
for 1, 12 and 120 stations, compares Python dictionary aggregation, CSV ingestion
with Python aggregation and SQLite GROUP BY, checks that the answers agree, and
prints measured times. Timing values depend on the computer.
