# Prometheus

## Backend

Using the `Prometheus` backend class, you can query any metrics available in
Prometheus to create an SLO.

The following methods are available to compute SLOs with the `Prometheus`
backend:

* `good_bad_ratio` for computing good / bad metrics ratios.
* `query_sli` for computing SLIs directly with Prometheus.

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
backend:
  class: Prometheus
  method: good_bad_ratio
  url: http://localhost:9090
  # headers:
  #   Content-Type: application/json
  #   Authorization: Basic b2s6cGFzcW==
  measurement:
    filter_good: http_requests_total{handler="/metrics", code=~"2.."}[window]
    filter_valid: http_requests_total{handler="/metrics"}[window]
    # operators: ['sum', 'rate']
```
* The `window` placeholder is needed in the query and will be replaced by the
corresponding `window` field set in each step of the Error Budget Policy.

* The `headers` section (commented) allows to specify Basic Authentication
credentials if needed.

* The `operators` section defines which PromQL functions to apply on the
timeseries. The default is to compute `sum(increase([METRIC_NAME][window]))` to
get an accurate count of good and bad events. Be aware that changing will likely
result in good / bad counts that do not accurately reflect actual load.

**&rightarrow; [Full SLO config](../../samples/prometheus/slo_prom_metrics_availability_ratio.yaml)**


### Query SLI

The `query_sli` method is used to directly query the needed SLI with Prometheus:
indeed, Prometheus' `PromQL` language is powerful enough that it can do ratios
natively.

This method makes it more flexible to input any `PromQL` SLI computation and
eventually reduces the number of queries made to Prometheus.

See Bitnami's [article](https://engineering.bitnami.com/articles/implementing-slos-using-prometheus.html)
on engineering SLOs with Prometheus.

```yaml
backend:
  class:         Prometheus
  method:        query_sli
  url:           ${PROMETHEUS_URL}
  # headers:
  #   Content-Type: application/json
  #   Authorization: Basic b2s6cGFzcW==
  measurement:
    expression:  >
      sum(rate(http_requests_total{handler="/metrics", code=~"2.."}[window]))
      /
      sum(rate(http_requests_total{handler="/metrics"}[window]))
```
* The `window` placeholder is needed in the query and will be replaced by the
corresponding `window` field set in each step of the Error Budget Policy.

* The `headers` section (commented) allows to specify Basic Authentication
credentials if needed.

**&rightarrow; [Full SLO config (availability)](../../samples/prometheus/slo_prom_metrics_availability_query_sli.yaml)**

**&rightarrow; [Full SLO config (latency)](../../samples/prometheus/slo_prom_metrics_latency_query_sli.yaml)**

### Distribution cut

The `distribution_cut` method is used for Prometheus distribution-type metrics (histograms), which are usually used for latency metrics.

A distribution metric records the **statistical distribution of the extracted
values** in **histogram buckets**. The extracted values are not recorded
individually, but their distribution across the configured buckets are recorded.
Prometheus creates 3 separate metrics `<metric>_count`, `<metric>_bucket`,
and `<metric>_sum` metrics.

When computing SLOs on histograms, we're usually interested in
taking the ratio of the number of events that are located in particular buckets
(considered 'good', e.g: all requests in the `le=0.25` bucket) over the total
count of valid events.

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
additionally gathering exact good / bad counts - and proposes a simpler way of
expressing it, as shown in the config example below.

**Config example:**
```yaml
backend:
  class: Prometheus
  project_id: ${STACKDRIVER_HOST_PROJECT_ID}
  method: distribution_cut
  measurement:
    expression: http_requests_duration_bucket{path='/', code=~"2.."}
    threshold_bucket: 0.25 # corresponds to 'le' attribute in Prometheus histograms
```
**&rightarrow; [Full SLO config](../../samples/prometheus/slo_prom_metrics_latency_distribution_cut.yaml)**

The `threshold_bucket` allowed  will depend on how the buckets boundaries are
set for your metric. Learn more in the [Prometheus docs](https://prometheus.io/docs/concepts/metric_types/#histogram).


## Exporter

The `Prometheus` exporter allows to export the error budget burn rate metric as
a **Prometheus metric** that can be used for alerting:

 * The **metric name** is `error_budget_burn_rate` by default, but can be
 modified using the `metric_type` field in the exporter YAML.

 * The **metric descriptor** has labels describing our SLO, amongst which the
 `service_name`, `feature_name`, and `error_budget_policy_step_name` labels.

The exporter pushes the metric to the `Prometheus`
[Pushgateway](https://prometheus.io/docs/practices/pushing/) which needs to be
running.

`Prometheus` needs to be setup to **scrape metrics from `Pushgateway`** (see
  [documentation](https://github.com/prometheus/pushgateway) for more details).

**Example config:**

```yaml
exporters:
 - class: Prometheus
   url: ${PUSHGATEWAY_URL}
```

Optional fields:
  * `metric_type`: Metric type / name. Defaults to `error_budget_burn_rate`.
  * `metric_description`: Metric description.
  * `username`: Username for Basic Auth.
  * `password`: Password for Basic Auth.
  * `job`: Name of `Pushgateway` job. Defaults to `slo-generator`.

**&rightarrow; [Full SLO config](../../samples/prometheus/slo_prom_metrics_availability_query_sli.yaml)**


### Examples

Complete SLO samples using `Prometheus` are available in
[samples/prometheus](../../samples/prometheus). Check them out !
