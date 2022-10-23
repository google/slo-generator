# Metrics block

## Configuration
The `metrics` block can be added to the configuration of any exporter derived
from [`MetricsExporter`](../../slo_generator/exporters/base.py#L41). It is used
to specify which metrics should be exported to the destination.

**Metrics** exported by default:
- `error_budget_burn_rate`: used for alerting.
- `alerting_burn_rate_threshold`: used for defining the alerting threshold.
- `sli_measurement`: used for visualizing the SLI over time.
- `slo_target`: used for drawing target over SLI measurement.
- `events_count`: used to split good / bad events in dashboards. Has two
additional labels: `good_events_count` and `bad_events_count`.

**Metric labels** exported by default:
- `service_name`
- `feature_name`
- `slo_name`
- `error_budget_policy_step_name`
- `metadata` labels, flattened, coming from the SLO configuration.
  For instance, if the SLO config contains the following metadata:
  ```yaml
  metadata:
    labels:
      env: dev
      team: devrel
      site: us
  ```
  The `env`, `team`, and `site` label will be available in the exported metric
  automatically.

### Override config (simple)
If you want to discard some default metrics, but keep the overall defaults, you
can use the simple override of the `metrics` block:
```yaml
metrics:
- error_budget_burn_rate
- sli_measurement
- slo_target
```

### Override config (advanced)
If you want to discard some default metrics while having additional settings,
you can use the advanced override of the `metrics` block:
```yaml
metrics:
- name: error_budget_burn_rate
  description: Error Budget burn rate.
  alias: ebbr

- name: events_count
  description: Events count.
  alias: events
  additional_labels:
  - good_events_count
  - bad_events_count

- name: sli_measurement
  description: SLI measurement.
  alias: sli
  additional_labels:
  - slo_target
```

where:
* `name`: name of the [SLO Report](../../tests/unit/fixtures/slo_report_v2.json)
field to export as a metric. The field MUST exist in the SLO report.
* `description`: description of the metric (if the metrics exporter supports it)
* `alias` (optional): rename the metric before writing to the monitoring
backend.
* `additional_labels` (optional) allow you to specify other labels to the
timeseries written. Each label name must correspond to a field of the
[SLO Report](../../tests/unit/fixtures/slo_report_v2.json).

## Metric exporters
Some metrics exporters have a specific `prefix` that is pre-prepended to the
metric name:
* `cloud_monitoring` exporter prefix: `custom.googleapis.com/`
* `datadog` prefix: `custom:`

Some metrics exporters have a limit of `labels` that can be written to their
metrics timeseries:
* `cloud_monitoring` labels limit: `10`.

Those are standards and cannot be modified.
