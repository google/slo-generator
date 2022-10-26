# Prometheus

## Backend

Using the `prometheus` backend class, you can query any metrics available in Prometheus to create an SLO.

```yaml
backends:
  prometheus:
    url: http://localhost:9090
    # headers:
    #   Content-Type: application/json
    #   Authorization: Basic b2s6cGFzcW==
```

Optional fields:

* `headers` allows to specify Basic Authentication credentials if needed.

The following methods are available to compute SLOs with the `prometheus`
backend:

* `good_bad_ratio` for computing good / bad metrics ratios.
* `query_sli` for computing SLIs directly with Prometheus.

### Good / bad ratio

The `good_bad_ratio` method is used to compute the ratio between two metrics:

* **Good events**, i.e events we consider as 'good' from the user perspective.
* **Bad or valid events**, i.e events we consider either as 'bad' from the user perspective, or all events we consider as 'valid' for the computation of the SLO.

This method is often used for availability SLOs, but can be used for other purposes as well (see examples).

**Config example:**

```yaml
backend: prometheus
method: good_bad_ratio
service_level_indicator:
  filter_good: http_requests_total{handler="/metrics", code=~"2.."}[window]
  filter_valid: http_requests_total{handler="/metrics"}[window]
  # operators: ['sum', 'rate']
```

* The `window` placeholder is needed in the query and will be replaced by the corresponding `window` field set in each step of the Error Budget Policy.

* The `operators` section defines which PromQL functions to apply on the timeseries. The default is to compute `sum(increase([METRIC_NAME][window]))` to get an accurate count of good and bad events. Be aware that changing will likely result in good / bad counts that do not accurately reflect actual load.

**&rightarrow; [Full SLO config](../../samples/prometheus/slo_prom_metrics_availability_ratio.yaml)**

### Query SLI

The `query_sli` method is used to directly query the needed SLI with Prometheus: indeed, Prometheus' `PromQL` language is powerful enough that it can do ratios natively.

This method makes it more flexible to input any `PromQL` SLI computation and eventually reduces the number of queries made to Prometheus.

See Bitnami's [article](https://engineering.bitnami.com/articles/implementing-slos-using-prometheus.html) on engineering SLOs with Prometheus.

**Config example:**

```yaml
backend: prometheus
method: query_sli
service_level_indicator:
  expression:  >
    sum(rate(http_requests_total{handler="/metrics", code=~"2.."}[window]))
    /
    sum(rate(http_requests_total{handler="/metrics"}[window]))
```

* The `window` placeholder is needed in the query and will be replaced by the corresponding `window` field set in each step of the Error Budget Policy.

**&rightarrow; [Full SLO config (availability)](../../samples/prometheus/slo_prom_metrics_availability_query_sli.yaml)**

**&rightarrow; [Full SLO config (latency)](../../samples/prometheus/slo_prom_metrics_latency_query_sli.yaml)**

### Distribution cut

The `distribution_cut` method is used for Prometheus distribution-type metrics (histograms), which are usually used for latency metrics.

A distribution metric records the **statistical distribution of the extracted values** in **histogram buckets**. The extracted values are not recorded individually, but their distribution across the configured buckets are recorded. Prometheus creates 3 separate metrics `<metric>_count`, `<metric>_bucket`, and `<metric>_sum` metrics.

When computing SLOs on histograms, we're usually interested in taking the ratio of the number of events that are located in particular buckets (considered 'good', e.g: all requests in the `le=0.25` bucket) over the total count of valid events.

The resulting PromQL expression would be similar to:

```
increase(
  <metric>_bucket{le="0.25"}[window]
)
 / ignoring (le)
increase(
  <metric>_count[window]
)
```

which you can very well use directly with the method `query_sli`.

The `distribution_cut` method does this calculus under the hood - while
additionally gathering exact good / bad counts - and proposes a simpler way of expressing it, as shown in the config example below.

**Config example:**

```yaml
backend: prometheus
method: distribution_cut
service_level_indicator:
  expression: http_requests_duration_bucket{path='/', code=~"2.."}
  threshold_bucket: 0.25 # corresponds to 'le' attribute in Prometheus histograms
```

**&rightarrow; [Full SLO config](../../samples/prometheus/slo_prom_metrics_latency_distribution_cut.yaml)**

The `threshold_bucket` allowed  will depend on how the buckets boundaries are set for your metric. Learn more in the [Prometheus docs](https://prometheus.io/docs/concepts/metric_types/#histogram).

## Exporter

The `prometheus` exporter allows to export SLO metrics to the [Prometheus Pushgateway](https://prometheus.io/docs/practices/pushing/) which needs to be running.

```yaml
exporters:
  prometheus:
    url: ${PUSHGATEWAY_URL}
```

Optional fields:

* `metrics`: List of metrics to export ([see docs](../shared/metrics.md)). Defaults to [`error_budget_burn_rate`, `sli_service_level_indicator`].
* `username`: Username for Basic Auth.
* `password`: Password for Basic Auth.
* `job`: Name of `Pushgateway` job. Defaults to `slo-generator`.

***Note:*** `prometheus` needs to be setup to **scrape metrics from `Pushgateway`** (see [documentation](https://github.com/prometheus/pushgateway) for more details).

**&rightarrow; [Full SLO config](../../samples/prometheus/slo_prom_metrics_availability_query_sli.yaml)**

## Self Exporter (API mode)

When running slo-generator as an API, you can enable `prometheus_self` exporter, which will expose all metrics on a standard `/metrics` endpoint, instead of pushing them to a gateway.

```yaml
exporters:
  prometheus_self: { }
```

***Note:*** The metrics endpoint will be available after a first successful SLO request. Before that, it's going to act as if it was endpoint of the generator API.

### Examples

Complete SLO samples using `prometheus` are available in
[samples/prometheus](../../samples/prometheus). Check them out!
