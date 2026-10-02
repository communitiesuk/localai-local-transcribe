# First party reporting

We collect first party analytic events. These scripts summarise those events into various metrics.

## Parameters

Before running a report, create local parameter files from the example files in `reporting/params/`.

```bash
cp reporting/params/params.sql.example reporting/params/params.sql
cp reporting/params/ready-dates.json.example reporting/params/ready-dates.json
cp reporting/params/monthly-lt-costs.json.example reporting/params/monthly-lt-costs.json
```

Fill in these values for the period of data you are interested in. Not all metrics require all params.

## Connecting to database

Connect to the AWS database:

```bash
aws sso login --profile <your-profile>
export AWS_PROFILE=<your-profile>
bash connect-to-aws-db.sh
```

Or locally:

```bash
PGPASSWORD=insecure psql \
  -h localhost \
  -p 5432 \
  -U postgres \
  -d minute_db
```

## Running metrics

Load the params:

```bash
\i reporting/params/params.sql
```

Run the sql script for the metric of interest:

```
\i reporting/<metric>.sql
```
