# B1 – Implement and validate the cleaning pipeline
Run `python cleaning_pipeline.py`. The program reads CSV text with csv.DictReader,
rejects blank/NA, non-numeric, negative and above-999 PM2.5 readings, and removes
duplicate station/date rows. It then demonstrates min–max scaling.
