# Cloud Monitoring

## Backends

Using the `cloud_monitoring` and `cloud_monitoring_mql` backend classes, you can query any metrics available in `Cloud Monitoring` to create an SLO.

- To query data with Monitoring Query Filters (MQF), use the `cloud_monitoring` backend:

  ```yaml
  backends:
    cloud_monitoring:
      project_id: "${WORKSPACE_PROJECT_ID}"
  ```

  In this case, the syntax of the filters for SLI definition follows [Cloud Monitoring v3 APIs' definitions](https://cloud.google.com/monitoring/api/v3/filters).

- To query data with Monitoring Query Language (MQL), use the `cloud_monitoring_mql` backend:

  ```yaml
  backends:
    cloud_monitoring_mql:
      project_id: "${WORKSPACE_PROJECT_ID}"
  ```

  In this case, SLI definitions use the MQL language. Refer to the [MQL Reference](https://cloud.google.com/monitoring/mql/reference) and [MQL Examples](https://cloud.google.com/monitoring/mql/examples) pages for more details.

The following methods are available to compute SLOs with the `cloud_monitoring` and `cloud_monitoring_mql` backends:

| `method` | `cloud_monitoring` | `cloud_monitoring_mql` | For metrics of type: |
| --- | --- | --- | --- |
| `good_bad_ratio` | ✅ | ✅ |`DELTA`, `GAUGE`, or `CUMULATIVE` |
| `distribution_cut` | ✅ | ✅ | `DELTA` and unit `DISTRIBUTION` |
| `query_sli` | ❌ | ✅ | any |

### Good / bad ratio

The `good_bad_ratio` method is used to compute the ratio between two metrics:

- **Good events**, i.e events we consider as 'good' from the user perspective.
- **Bad or valid events**, i.e events we consider either as 'bad' from the user perspective, or all events we consider as 'valid' for the computation of the SLO.

This method is often used for availability SLOs, but can be used for other purposes as well (see examples).

**SLO config blob:**

- For queries defined using Monitoring Query Filters (MQF):

  ```yaml
  backend: cloud_monitoring
  method: good_bad_ratio
  service_level_indicator:
    filter_good: >
      project="${GAE_PROJECT_ID}"
      metric.type="appengine.googleapis.com/http/server/response_count"
      metric.labels.response_code >= 200
      metric.labels.response_code < 500
    filter_valid: >
      project="${GAE_PROJECT_ID}"
      metric.type="appengine.googleapis.com/http/server/response_count"
  ```

  You can also use the `filter_bad` field which identifies bad events instead of the `filter_valid` field which identifies all valid events.

  **&rightarrow; [Full SLO config](../../samples/cloud_monitoring/slo_gae_app_availability.yaml)**

- For queries defined using Monitoring Query Language (MQL) :

  ```yaml
  backend: cloud_monitoring_mql
  method: good_bad_ratio
  service_level_indicator:
    filter_good: >
      fetch gae_app
      | metric 'appengine.googleapis.com/http/server/response_count'
      | filter resource.project_id == '${GAE_PROJECT_ID}'
      | filter
          metric.response_code == 429
          || metric.response_code == 200
    filter_valid: >
      fetch gae_app
      | metric 'appengine.googleapis.com/http/server/response_count'
      | filter resource.project_id == '${GAE_PROJECT_ID}'
  ```

  You can also use the `filter_bad` field which identifies bad events instead of the `filter_valid` field which identifies all valid events.

  **&rightarrow; [Full SLO config](../../samples/cloud_monitoring_mql/slo_gae_app_availability.yaml)**

### Distribution cut

The `distribution_cut` method is used for Cloud Monitoring distribution-type metrics, which are usually used for latency metrics.

A distribution metric records the **statistical distribution of the extracted values** in **histogram buckets**. The extracted values are not recorded individually, but their distribution across the configured buckets are recorded, along with the `count`, `mean`, and `sum` of squared deviation of the values.

In Cloud Monitoring, there are three different ways to specify bucket boundaries:

- **Linear:** Every bucket has the same width.
- **Exponential:** Bucket widths increases for higher values, using an exponential growth factor.
- **Explicit:** Bucket boundaries are set for each bucket using a bounds array.

**SLO config blob:**

- For queries defined using Monitoring Query Filters (MQF):

  ```yaml
  backend: cloud_monitoring
  method: exponential_distribution_cut
  service_level_indicator:
    filter_valid: >
      project=${GAE_PROJECT_ID} AND
      metric.type=appengine.googleapis.com/http/server/response_latencies AND
      metric.labels.response_code >= 200 AND
      metric.labels.response_code < 500
    good_below_threshold: true
    threshold_bucket: 19
  ```

  **&rightarrow; [Full SLO config](../../samples/cloud_monitoring/slo_gae_app_latency.yaml)**

- For queries defined using Monitoring Query Language (MQL) :

  ```yaml
  backend: cloud_monitoring_mql
  method: distribution_cut
  exporters:
  - cloud_monitoring
  service_level_indicator:
    filter_valid: >
      fetch https_lb_rule
      | metric 'loadbalancing.googleapis.com/https/total_latencies'
      | filter resource.project_id == '${LB_PROJECT_ID}'
      | filter metric.label.response_code_class = "200"
          || metric.response_code_class = "300"
          || metric.response_code_class = "400"
    good_below_threshold: true
    threshold_bucket: 19
  ```

  **&rightarrow; [Full SLO config](../../samples/cloud_monitoring_mql/slo_gae_app_latency.yaml)**

The `threshold_bucket` number to reach our 724ms target latency will depend on how the buckets boundaries are set. Learn how to [inspect your distribution metrics](https://cloud.google.com/logging/docs/logs-based-metrics/distribution-metrics#inspecting_distribution_metrics) to figure out the bucketization.

### Query SLI

As MQL is a much richer language than MQF, the `cloud_monitoring_mql` backend has an extra `query_sli` method that can be used to retrieve the value of a given SLI with a single API call.

For example, the `ratio` keyword lets us compute a ratio of good and valid events directly. Here is an example for availability:

```yaml
  backend: cloud_monitoring_mql
  method: query_sli
  exporters:
  - cloud_monitoring
  service_level_indicator:
    query: >
      fetch gae_app
      | metric 'appengine.googleapis.com/http/server/response_count'
      | filter resource.project_id == '${GAE_PROJECT_ID}'
      | { filter
            metric.response_code == 429
            || metric.response_code == 200
            || metric.response_code == 201
            || metric.response_code == 202
            || metric.response_code == 203
            || metric.response_code == 204
            || metric.response_code == 205
            || metric.response_code == 206
            || metric.response_code == 207
            || metric.response_code == 208
            || metric.response_code == 226
            || metric.response_code == 304
        ; ident }
      | sum
      | ratio
```

Refer to the [MQL Examples](https://cloud.google.com/monitoring/mql/examples) page for more details and more interesting keywords/functions.

**&rightarrow; [Full SLO config](../../samples/cloud_monitoring_mql/slo_gae_app_availability_ratio.yaml)**

Generally speaking, any query that returns a single value after being aggregated (within a given time series) and reduced (across all time series) with a sum can be retrieved directly with `query_sli`.

## Exporter

The `cloud_monitoring` exporter allows to export SLO metrics to Cloud Monitoring API.

```yaml
exporter:
  cloud_monitoring:
    project_id: "${WORKSPACE_PROJECT_ID}"
```

Optional fields:

- `metrics`: [*optional*] `list` - List of metrics to export ([see docs](../shared/metrics.md)).

**&rightarrow; [Full SLO config](../../samples/cloud_monitoring/slo_lb_request_availability.yaml)**

## Alerting

Alerting is essential in any SRE approach. Having all the right metrics without being able to alert on them is simply useless.

**Too many alerts** can be daunting, and page your SRE engineers for no valid reasons.

**Too little alerts** can mean that your applications are not monitored at all (no application have 100% reliability).

**Alerting on high error budget burn rates** for some hand-picked SLOs can help reduce the noise and page only when it's needed.

**Example:**

We will define a `Cloud Monitoring` alert that we will **filter out on the corresponding error budget step**.

Consider the following error budget policy step config:

```yaml
- name: 1 hour
  window: 3600
  burn_rate_threshold: 9
  alert: true
  message_alert: Page the SRE team to defend the SLO
  message_ok: Last hour on track
```

Using Cloud Monitoring UI, let's set up an alert when our error budget burn rate is burning **9X faster** than it should in the last hour:

1. Open `Cloud Monitoring` and click `Alerting > Create Policy`.
1. Fill the alert name and click `Add Condition`.
1. Search for `custom/error_budget_burn_rate` and click the metric.
1. Filter on `error_budget_policy_step_name` label with value `1 hour`.
1. Set the `Condition` field to `is above`.
1. Set the `Threshold` field to `9`.
1. Set the `For` field to `most_recent_value`.
1. Click `Add`
1. Fill the notification options for your alert.
1. Click `Save`.

Repeat the above steps for every item in your error budget policy.

Alerts can be filtered out more (e.g: `service_name`, `feature_name`), but you can keep global ones filtered only on `error_budget_policy_step_name` if you want your SREs to have visibility on all the incidents. Labels will be used to differentiate the alert messages.

## Examples

Complete SLO samples using Cloud Monitoring are available in [samples/cloud_monitoring](../../samples/cloud_monitoring). Check them out!
