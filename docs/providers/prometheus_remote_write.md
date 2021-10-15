# Prometheus Remote Write

## Exporter

The `prometheus_remote_write` exporter allows to export SLO metrics to any of the compatible [Remote Write](https://prometheus.io/docs/operating/integrations/#remote-endpoints-and-storage) endpoints.

```yaml
exporters:
  prometheus_remote_write:
    url: https://your-cortex-endpoint/api/v1/push
    username: foo
    password: bar
    tls_config:
      ca_file: path/to/certchain.pem
      ca_cert: path/to/cert.crt
      ca_key: path/to/cert.key
      insecure_skip_verify: True|False
```

Required fields:
  * `url`: Fully-qualified remote write endpoint, including the API path. E.g. `api/v1/push` for Cortex or `api/v1/receive` for Thanos etc.

Optional fields:
  * `metrics`: List of metrics to export ([see docs](../shared/metrics.md))
  * `username`: Username for Basic Auth.
  * `password`: Password for Basic Auth.
  * `job`: Name of `RemoteWrite` job. Defaults to `slo-generator`.
  * `tls_config`: Dict holding the custom TLS configuration.
    * `ca_file`: File path to a certificate authority used to validate the authenticity of a server certificate.
    * `cert_file`: File path to a certificate used with the private key. Requires also `key_file` to be provided.
    * `key_file`: File path to a private key used with the certificate. Requires also `cert_file` to be provided.
    * `insecure_skip_verify`: Boolean to skip TLS chain and host verification.
