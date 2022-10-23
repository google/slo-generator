# Dynatrace

## Backend

Using the `dynatrace` backend class, you can query any metrics available in
Dynatrace to create an SLO.

```yaml
backends:
  dynatrace:
    api_token: ${DYNATRACE_API_TOKEN}
    api_url:   ${DYNATRACE_API_URL}
```

The following methods are available to compute SLOs with the `dynatrace`
backend:

* `good_bad_ratio` for computing good / bad metrics ratios.

### Good / bad ratio

The `good_bad_ratio` method is used to compute the ratio between two metrics:

- **Good events**, i.e events we consider as 'good' from the user perspective.
- **Bad or valid events**, i.e events we consider either as 'bad' from the user
perspective, or all events we consider as 'valid' for the computation of the
SLO.

This method is often used for availability SLOs, but can be used for other
purposes as well (see examples).

**Config example:**

```yaml
backend: dynatrace
method: good_bad_ratio
service_level_indicator:
  query_good:
    metric_selector: ext:app.request_count:filter(and(eq(app,test_app),eq(env,prod),eq(status_code_class,2xx)))
    entity_selector: type(HOST)
  query_valid:
      metric_selector: ext:app.request_count:filter(and(eq(app,test_app),eq(env,prod)))
      entity_selector: type(HOST)
```
**&rightarrow; [Full SLO config](../../samples/dynatrace/slo_dt_app_availability_ratio.yaml)**


### Threshold

The `threshold` method is used to split a series of values into two buckets
using a threshold as delimiter: one bucket which will represent the good events,
the other will represent the bad events.

This method can be used for latency SLOs, by defining a latency threshold.

**Config example:**

```yaml
backend: dynatrace
method: threshold
service_level_indicator:
  query_valid:
    metric_selector: ext:app.request_latency:filter(and(eq(app,test_app),eq(env,prod),eq(status_code_class,2xx)))
    entity_selector: type(HOST)
  threshold: 40000 # us
```
**&rightarrow; [Full SLO config](../../samples/dynatrace/slo_dt_app_latency_threshold.yaml)**

Optional fields:
  * `good_below_threshold`: Boolean, specify if good events are above or below threshold. Default: `true`.


### Examples

Complete SLO samples using `dynatrace` are available in
[samples/dynatrace](../../samples/dynatrace). Check them out!

## Exporter

The `dynatrace` exporter allows to export SLO metrics to Dynatrace API.

```yaml
exporters:
  dynatrace:
    api_token: ${DYNATRACE_API_TOKEN}
    api_url: ${DYNATRACE_API_URL}
```

Optional fields:
  * `metrics`: List of metrics to export ([see docs](../shared/metrics.md)). Defaults to [`custom:error_budget_burn_rate`, `custom:sli_service_level_indicator`].

**&rightarrow; [Full SLO config](../../samples/dynatrace/slo_dt_app_availability_ratio.yaml)**


## Dynatrace API considerations

The `distribution_cut` method is not currently implemented for Dynatrace, since
there are no metric type corresponding to a distribution in the API.
