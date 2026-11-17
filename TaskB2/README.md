# B2 – Engineer adversarial data
Run `python adversarial_sql.py`. It tests missing columns, wrong delimiters,
valid UTF-8 CSV and empty data, and uses SQLite parameter placeholders to prevent
SQL injection. A quote in a station name is treated as data, not executable SQL.
