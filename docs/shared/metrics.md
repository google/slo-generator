# Metrics block

## Configuration
The `metrics` block can be added to the configuration of any exporter derived 
from [`MetricsExporter`](../../slo_generator/exporters/base.py#L41). It is used 
to specify which metrics should be exported to the destination.

### Simple config
The simple version of the `metrics` block is:
```yaml
metrics:
- error_budget_burn_rate
- sli_measurement
- slo_target
```

### Advanced config
The advanced format of the `metrics` block is:
```yaml
metrics:
- name: error_budget_burn_rate
  description: Error Budget burn rate.
  alias: ebbr
  additional_labels:
  - good_events_count
  - bad_events_count
  
- name: sli_measurement
  description: Error Budget burn rate.
  alias: sli
  additional_labels:
  - slo_target
```

where:
* `name`: name of the [SLO Report](../../tests/unit/fixtures/slo_report.json) 
field to export as a metric.
* `description`: description of the metric (if the metrics exporter supports it)
* `alias` (optional): rename the metric before writing to the monitoring 
backend.
* `additional_labels` (optional) allow you to specify other labels to the 
timeseries written. Each label name must correspond to a field of the SLO 
report.

### Default (no config)
If the `metrics` block is not present in the metrics exporter configuration, 
the default behaviour is to export the following metrics:
- `error_budget_burn_rate`: used for alerting.
- `sli_measurement`: used for visualizing the SLI over time.

The default set of labels added by default to each metric is:
- `error_budget_policy_step_name`
- `window`
- `service_name`
- `slo_name`
- `alerting_burn_rate_threshold`

## Metric prefix
Some metrics exporters have a specific `prefix` that is pre-prepended to the 
metric name:
* `StackdriverExporter` prefix: `custom.googleapis.com/`
* `DatadogExporter` prefix: `custom:`

Those are standards and cannot be modified.

## MetricsExporter

The `MetricsExporter` base class that other exporters can inherit from has the 
following behavior:
