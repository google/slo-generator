# OpenTelemetry

## Exporter

The `opentelemetry` exporter allows to export SLO metrics via [OTLP gRPC](https://opentelemetry.io/docs/specs/otlp/) to any OpenTelemetry-compatible backend (e.g., Grafana Mimir, Datadog, New Relic, Jaeger, etc.).

**Installation:**

```sh
pip install slo-generator[opentelemetry]
```

**Config example:**

```yaml
exporters:
  opentelemetry:
    endpoint: ${OTLP_ENDPOINT}
    headers:
      Authorization: Bearer ${OTLP_TOKEN}
    insecure: false
```

**Required fields:**

* `endpoint`: OTLP gRPC endpoint (e.g., `localhost:4317`).

**Optional fields:**

* `headers`: `dict` - Headers to send with each request (e.g., for authentication).
* `insecure`: `bool` - Use insecure (non-TLS) connection. Defaults to `false`.
* `metrics`: `list` - List of metrics to export ([see docs](../shared/metrics.md)).

All SLO metrics are exported as gauges with the `slo_` prefix (e.g., `slo_error_budget_burn_rate`). SLO report labels are mapped directly to OpenTelemetry metric attributes.
