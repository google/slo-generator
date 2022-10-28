# SLO Library

This folder is an SLO library to facilitate writing new SLOs by starting from already written SLO configurations.

All samples are classified within folders named after their respective backend or exporter class.

Each sample references environment variables that must be set prior to running it.

## Environment variables

The following is listing all environment variables found in the SLO configs, per backend:

You can either set those variables for the backends you want to try, or set all of those in an `.env` file and then `source` it. Note that the actual GCP resources you're pointing to need to exist.

### `cloud_monitoring`

| Environment variable | Description |
| --- | --- |
| `WORKSPACE_PROJECT_ID` | Cloud Monitoring host project ID |
| `LOG_METRIC_NAME` | Cloud Logging log-based metric name |
| `GAE_PROJECT_ID` | Google App Engine application project ID |
| `GAE_MODULE_ID` | Google App Engine application module ID |
| `PUBSUB_PROJECT_ID` | Pub/Sub project ID |
| `PUBSUB_TOPIC_NAME` | Pub/Sub topic name |

### `cloud_monitoring_mql`

| Environment variable | Description |
| --- | --- |
| `WORKSPACE_PROJECT_ID` | Cloud Monitoring host project ID |
| `LOG_METRIC_NAME` | Cloud Logging log-based metric name |
| `GAE_PROJECT_ID` | Google App Engine application project ID |
| `GAE_MODULE_ID` | Google App Engine application module ID |
| `PUBSUB_PROJECT_ID` | Pub/Sub project ID |
| `PUBSUB_TOPIC_NAME` | Pub/Sub topic name |

### `cloud_service_monitoring`

| Environment variable | Description |
| --- | --- |
| `WORKSPACE_PROJECT_ID` | Cloud Monitoring host project ID |
| `LOG_METRIC_NAME` | Cloud Logging log-based metric name |
| `GAE_PROJECT_ID` | Google App Engine application project ID |
| `GAE_MODULE_ID` | Google App Engine application module ID |
| `PUBSUB_PROJECT_ID` | Pub/Sub project ID |
| `PUBSUB_TOPIC_NAME` | Pub/Sub topic name |
| `GKE_PROJECT_ID` | GKE project ID |
| `GKE_LOCATION` | GKE location |
| `GKE_CLUSTER_NAME` | GKE cluster name |
| `GKE_SERVICE_NAMESPACE` | GKE service namespace |
| `GKE_SERVICE_NAME` | GKE service name |

### `datadog`

| Environment variable | Description |
| --- | --- |
| `DATADOG_API_KEY` | Datadog API key |
| `DATADOG_APP_KEY` | Datadog APP key |

### `dynatrace`

| Environment variable | Description |
| --- | --- |
| `DYNATRACE_API_URL` | Dynatrace API URL |
| `DYNATRACE_API_TOKEN` | Dynatrace API token |

### `elasticsearch`

| Environment variable | Description |
| --- | --- |
| `ELASTICSEARCH_URL` | ElasticSearch instance URL |

### `prometheus`

| Environment variable | Description |
| --- | --- |
| `PROMETHEUS_URL` | Prometheus instance URL |
| `PROMETHEUS_PUSHGATEWAY_URL` | Prometheus Pushgateway instance URL |

## Running the samples

To run one sample:

```sh
slo-generator -f samples/cloud_monitoring/<filename>.yaml
```

To run all the samples for a backend:

```sh
slo-generator -f samples/<backend> -b samples/<error_budget_policy>
```

*where:*

- `<backend>` is the backend name (lowercase)
- `<error_budget_policy>` is the path to the error budget policy YAML file.

***Note:*** *if you want to enable the exporters as well, you can add the `--export` flag.*

### Examples

#### Cloud Monitoring (MQF)

```sh
slo-generator -f samples/cloud_monitoring -b error_budget_policy.yaml
```

#### Cloud Monitoring (MQL)

```sh
slo-generator -f samples/cloud_monitoring_mql -b error_budget_policy.yaml
```

#### Cloud Service Monitoring

```sh
slo-generator -f samples/cloud_service_monitoring -b error_budget_policy_ssm.yaml
```

***Note:*** *the Error Budget Policy is different for this backend, because it only supports steps where `window` is a multiple of 24 hours.*

#### Datadog

```sh
slo-generator -f samples/datadog -b error_budget_policy.yaml
```

#### Dynatrace

```sh
slo-generator -f samples/dynatrace -b error_budget_policy.yaml
```

#### Elasticsearch

```sh
slo-generator -f samples/elasticsearch -b error_budget_policy.yaml
```

#### Prometheus

```sh
slo-generator -f samples/prometheus -b error_budget_policy.yaml
```

#### Custom Class

```sh
cd samples/
slo-generator -f custom -b error_budget_policy.yaml -e
```
