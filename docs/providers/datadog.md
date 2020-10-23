# Datadog

## Backend

Using the `Datadog` backend class, you can query any metrics available in
Datadog to create an SLO.

The following methods are available to compute SLOs with the `Datadog`
backend:

* `good_bad_ratio` for computing good / bad metrics ratios.
* `query_sli` for computing SLIs directly with Datadog.
* `query_slo` for getting SLO value from Datadog SLO endpoint.

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
  class:   Datadog
  method:  good_bad_ratio
  api_key: ${DATADOG_API_KEY}
  app_key: ${DATADOG_APP_KEY}
  measurement:
    filter_good: app.requests.count{http.path:/, http.status_code_class:2xx}
    filter_valid: app.requests.count{http.path:/}
```
**&rightarrow; [Full SLO config](../../samples/datadog/slo_dd_app_availability_ratio.yaml)**

Optional arguments to configure Datadog are documented in the Datadog
`initialize` method [here](https://github.com/DataDog/datadogpy/blob/058114cc3d65483466684c96a5c23e36c3aa052e/datadog/__init__.py#L33).
You can pass them in the `backend` section, such as specifying
`api_host: api.datadoghq.eu` in order to use the EU site.

### Query SLI

The `query_sli` method is used to directly query the needed SLI with Datadog:
Datadog's query language is powerful enough that it can do ratios natively.

This method makes it more flexible to input any `Datadog` SLI computation and
eventually reduces the number of queries made to Datadog.

```yaml
backend:
  class:   Datadog
  method:  query_sli
  api_key: ${DATADOG_API_KEY}
  app_key: ${DATADOG_APP_KEY}
  measurement:
    expression: sum:app.requests.count{http.path:/, http.status_code_class:2xx} / sum:app.requests.count{http.path:/}
```

Optional arguments to configure Datadog are documented in the Datadog
`initialize` method [here](https://github.com/DataDog/datadogpy/blob/058114cc3d65483466684c96a5c23e36c3aa052e/datadog/__init__.py#L33).
You can pass them in the `backend` section, such as specifying
`api_host: api.datadoghq.eu` in order to use the EU site.

**&rightarrow; [Full SLO config](../../samples/datadog/slo_dd_app_availability_query_sli.yaml)**

### Query SLO

The `query_slo` method is used to directly query the needed SLO with Datadog:
indeed, Datadog has SLO objects that you can directly refer to in your config by inputing their `slo_id`.

This method makes it more flexible to input any `Datadog` SLI computation and
eventually reduces the number of queries made to Datadog.

To query the value from Datadog SLO, simply add a `slo_id` field in the
`measurement` section:

```yaml
...
backend:
  class:   Datadog
  method:  query_slo
  api_key: ${DATADOG_API_KEY}
  app_key: ${DATADOG_APP_KEY}
  measurement:
    slo_id:  ${DATADOG_SLO_ID}
```

**&rightarrow; [Full SLO config](../../samples/datadog/slo_dd_app_availability_query_slo.yaml)**

### Examples

Complete SLO samples using `Datadog` are available in
[samples/datadog](../../samples/datadog). Check them out!

## Exporter

The `Datadog` exporter allows to export SLO metrics to the Datadog API.

**Example config:**

```yaml
exporters:
 - class: Datadog
   api_key: ${DATADOG_API_KEY}
   app_key: ${DATADOG_APP_KEY}
```

Optional fields:
  * `metrics`: List of metrics to export ([see docs](../shared/metrics.md)). Defaults to [`custom:error_budget_burn_rate`, `custom:sli_measurement`].


**&rightarrow; [Full SLO config](../../samples/datadog/slo_dd_app_availability_ratio.yaml)**


## Datadog API considerations

The `distribution_cut` method is not currently implemented for Datadog.

The reason for this is that Datadog distributions (or histograms) do not conform
to what histograms should be (see [old issue](https://github.com/DataDog/dd-agent/issues/349)),
i.e a set of configurable bins, each providing the number of events falling into
each bin.

Standard histograms representations (see [wikipedia](https://en.wikipedia.org/wiki/Histogram))
already implement this, but the approach Datadog took is to pre-compute
(client-side) or post-compute (server-side) percentiles, resulting in a
different metric for each percentile representing the percentile value instead
of the number of events in the percentile.

This implementation has a couple of advantages, like making it easy to query and
graph the value of the 99th, 95p, or 50p percentiles; but it makes it
effectively very hard to compute a standard SLI for it, since it's not possible
to see how many requests fall in each bin; hence there is no way to know how
many good and bad events there are.

Three options can be considered to implement this:

* Add support for `gostatsd`'s [Timer histograms implementation](https://github.com/atlassian/gostatsd#timer-histograms-experimental-feature)
in `datadog-agent`.

**OR**

* Implement support for standard histograms where bucketization is configurable
and where it's possible to query the number of events falling into each bucket.

**OR**

* Design an implementation that tries to reconstitute the original distribution
by assimilating it to a Gaussian distribution and estimating its parameters.
This is a complex and time-consuming approach that will give approximate results
and is not a straightforward problem (see [StackExchange thread](https://stats.stackexchange.com/questions/6022/estimating-a-distribution-based-on-three-percentiles))
