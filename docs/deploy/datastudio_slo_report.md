# Build an SLO achievements report using BigQuery and DataStudio.

## Setup the BigQuery exporter
In order to setup a DataStudio report, make sure `slo-generator` is configured
to export to a BigQuery dataset (see [instructions here](../providers/bigquery.md)).

## Create a BigQuery view
Replace the variables `PROJECT_ID`, `DATASET_ID` and `TABLE_ID` in the
content below by the values configured in your BigQuery exporter, and put it
into a file `create_view.sql`:

```sql
CREATE VIEW <PROJECT_ID>.<DATASET_ID>.last_report AS
SELECT
   r2.*
FROM
   (
      SELECT
         r.service_name,
         r.feature_name,
         r.slo_name,
         r.window,
         MAX(r.timestamp_human) AS timestamp_human
      FROM
         <PROJECT_ID>.<DATASET_ID>.<TABLE_ID> AS r
      GROUP BY
         r.service_name,
         r.feature_name,
         r.slo_name,
         r.window
      ORDER BY
         r.window
   )
   AS latest_report
   INNER JOIN
      <PROJECT_ID>.<DATASET_ID>.<TABLE_ID> AS r2
      ON r2.service_name = latest_report.service_name
      AND r2.feature_name = latest_report.feature_name
      AND r2.slo_name = latest_report.slo_name
      AND r2.window = latest_report.window
      AND r2.timestamp_human = latest_report.timestamp_human
ORDER BY
   r2.service_name,
   r2.feature_name,
   r2.slo_name,
   r2.error_budget_policy_step_name
```

Run it with the BigQuery CLI using:

    bq query `cat create_view.sql`

Alternatively, you can create the view above with Terraform.

### Setup DataStudio SLO achievements report

Duplicate the [SLO achievements report template (public)](https://datastudio.google.com/reporting/964e185c-6ca0-4ed8-809d-425e22568aa0)  following instructions on the report page named README.

This template provides a basic dashboard with 3 views:

* `Morning snapshot`: last error budget and SLI achievement, support decisions agreed in the Error Budget Policy.

* `Trends`: SLI vs SLO by service/feature over a period of time.

* `Alerting on burnrate`: visualize when alerting engage and fade off by sliding window sizes
