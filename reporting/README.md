You will need to fill in `reporting_period_start` (e.g. `2025-01-01 00:00:00+01`), `reporting_period_end` (e.g. `2025-02-01 00:00:00+01`) and `metric` (e.g `median-transcription-turnaround-time`)

```sql
PGPASSWORD=insecure psql \
  -h localhost \
  -p 5432 \
  -U postgres \
  -d minute_db \
  -v ON_ERROR_STOP=1 \
  -v reporting_period_start="'<reporting_period_start>'" \
  -v reporting_period_end="'<reporting_period_end>'" \
  -f reporting/<metric>.sql
```
