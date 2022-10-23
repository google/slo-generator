# SLO Generator

![test](https://github.com/google/slo-generator/workflows/test/badge.svg)
![build](https://github.com/google/slo-generator/workflows/build/badge.svg)
![deploy](https://github.com/google/slo-generator/workflows/deploy/badge.svg)
[![PyPI version](https://badge.fury.io/py/slo-generator.svg)](https://badge.fury.io/py/slo-generator)
[![Downloads](https://static.pepy.tech/personalized-badge/slo-generator?period=total&units=international_system&left_color=grey&right_color=orange&left_text=pypi%20downloads)](https://pepy.tech/project/slo-generator)

`slo-generator` is a tool to compute and export **Service Level Objectives** ([SLOs](https://landing.google.com/sre/sre-book/chapters/service-level-objectives/)), **Error Budgets** and **Burn Rates**, using configurations written in YAML (or JSON) format.

***IMPORTANT NOTE: the following content is the `slo-generator` v2 documentation. The v1 documentation is available [here](https://github.com/google/slo-generator/tree/v1.5.1), and instructions to migrate to v2 are available [here](https://github.com/google/slo-generator/blob/master/docs/shared/migration.md).***

## Table of contents

- [Description](#description)
- [Local usage](#local-usage)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [CLI usage](#cli-usage)
  - [API usage](#api-usage)
- [Configuration](#configuration)
  - [SLO configuration](#slo-configuration)
  - [Shared configuration](#shared-configuration)
- [More documentation](#more-documentation)
  - [Build an SLO achievements report with BigQuery and DataStudio](#build-an-slo-achievements-report-with-bigquery-and-datastudio)
  - [Deploy the SLO Generator in Cloud Run](#deploy-the-slo-generator-in-cloud-run)
  - [Deploy the SLO Generator in Kubernetes (Alpha)](#deploy-the-slo-generator-in-kubernetes-alpha)
  - [Deploy the SLO Generator in a CloudBuild pipeline](#deploy-the-slo-generator-in-a-cloudbuild-pipeline)
  - [DEPRECATED: Deploy the SLO Generator on Google Cloud Functions (Terraform)](#deprecated-deploy-the-slo-generator-on-google-cloud-functions-terraform)
  - [Contribute to the SLO Generator](#contribute-to-the-slo-generator)

## Description

The `slo-generator` runs backend queries computing **Service Level Indicators**, compares them with the **Service Level Objectives** defined and generates a report by computing important metrics:

- **Service Level Indicator** (SLI) defined as **SLI = N<sub>good_events</sub> &#47; N<sub>valid_events</sub>**
- **Error Budget** (EB) defined as **EB = 1 - SLI**
- **Error Budget Burn Rate** (EBBR) defined as **EBBR = EB / EB<sub>target</sub>**
- **... and more**, see the [example SLO report](./test/unit/../../tests/unit/fixtures/slo_report_v2.json).

The **Error Budget Burn Rate** is often used for [**alerting on SLOs**](https://sre.google/workbook/alerting-on-slos/), as it demonstrates in practice to be more **reliable** and **stable** than alerting directly on metrics or on **SLI > SLO** thresholds.

## Local usage

### Requirements

- `python3.7` and above
- `pip3`

### Installation

`slo-generator` is a Python library published on [PyPI](https://pypi.org). To install it, run:

```sh
pip3 install slo-generator
```

***Notes:***

- To install **[providers](./docs/providers)**, use `pip3 install slo-generator[<PROVIDER_1>, <PROVIDER_2>, ... <PROVIDER_n]`. For instance:
  - `pip3 install slo-generator[cloud_monitoring]` installs the Cloud Monitoring backend / exporter.
  - `pip3 install slo-generator[prometheus, datadog, dynatrace]` install the Prometheus, Datadog and Dynatrace, backends / exporters.
- To install the **slo-generator API**, run `pip3 install slo-generator[api]`.
- To enable **debug logs**, set the environment variable `DEBUG` to `1`.
- To enable **colorized output** (local usage), set the environment variable `COLORED_OUTPUT` to `1`.

### CLI usage

To compute an SLO report using the CLI, run:

```sh
slo-generator compute -f <SLO_CONFIG_PATH> -c <SHARED_CONFIG_PATH> --export
```

where:

- `<SLO_CONFIG_PATH>` is the [SLO configuration](#slo-configuration) file or folder path.
- `<SHARED_CONFIG_PATH>` is the [Shared configuration](#shared-configuration) file path.
- `--export` | `-e` enables exporting data using the `exporters` specified in the SLO
  configuration file.

Use `slo-generator compute --help` to list all available arguments.

### API usage

On top of the CLI, the `slo-generator` can also be run as an API using the Cloud Functions Framework SDK (Flask) using the `api` subcommand:

```sh
slo-generator api --config <SHARED_CONFIG_PATH>
```

where:

- `<SHARED_CONFIG_PATH>` is the [Shared configuration](#shared-configuration) file path or GCS URL.

Once the API is up-and-running, you can make HTTP POST requests with your SLO configurations (YAML or JSON) in the request body:

```sh
curl -X POST -H "Content-Type: text/x-yaml" --data-binary @slo.yaml localhost:8080 # yaml SLO config
curl -X POST -H "Content-Type: application/json" -d @slo.json localhost:8080 # json SLO config
```

To read more about the API and advanced usage, see [docs/shared/api.md](./docs/shared/api.md).

## Configuration

The `slo-generator` requires two configuration files to run, an **SLO configuration** file, describing your SLO, and the **Shared configuration** file (common configuration for all SLOs).

### SLO configuration

The **SLO configuration** (JSON or YAML) is following the Kubernetes format and is composed of the following fields:

- `api`: `sre.google.com/v2`
- `kind`: `ServiceLevelObjective`
- `metadata`:
  - `name`: [**required**] *string* - Full SLO name (**MUST** be unique).
  - `labels`: [*optional*] *map* - Metadata labels, **for example**:
    - `slo_name`: SLO name (e.g `availability`, `latency128ms`, ...).
    - `service_name`: Monitored service (to group SLOs by service).
    - `feature_name`: Monitored feature (to group SLOs by feature).

- `spec`:
  - `description`: [**required**] *string* - Description of this SLO.
  - `goal`: [**required**] *string* - SLO goal (or target) (**MUST** be between 0 and 1).
  - `backend`: [**required**] *string* - Backend name (**MUST** exist in SLO Generator Configuration).
  - `method`: [**required**] *string* - Backend method to use (**MUST** exist in backend class definition).
  - `service_level_indicator`: [**required**] *map* - SLI configuration. The content of this section is
  specific to each provider, see [`docs/providers`](./docs/providers).
  - `error_budget_policy`: [*optional*] *string* - Error budget policy name
  (**MUST** exist in SLO Generator Configuration). If not specified, defaults to `default`.
  - `exporters`: [*optional*] *string* - List of exporter names (**MUST** exist in SLO Generator Configuration).

***Note:*** *you can use environment variables in your SLO configs by using `${MY_ENV_VAR}` syntax to avoid having sensitive data in version control. Environment variables will be replaced automatically at run time.*

**&rarr; See [example SLO configuration](samples/cloud_monitoring/slo_gae_app_availability.yaml).**

### Shared configuration

The shared configuration (JSON or YAML) configures the `slo-generator` and acts as a shared config for all SLO configs. It is composed of the following fields:

- `backends`: [**required**] *map* - Data backends configurations. Each backend alias is defined as a key `<backend_name>/<suffix>`, and a configuration map.

  ```yaml
  backends:
    cloud_monitoring/dev:
      project_id: proj-cm-dev-a4b7
    datadog/test:
      app_key: ${APP_SECRET_KEY}
      api_key: ${API_SECRET_KEY}
  ```

  See specific providers documentation for detailed configuration:
  - [`cloud_monitoring`](docs/providers/cloud_monitoring.md#backend)
  - [`cloud_service_monitoring`](docs/providers/cloud_service_monitoring.md#backend)
  - [`prometheus`](docs/providers/prometheus.md#backend)
  - [`elasticsearch`](docs/providers/elasticsearch.md#backend)
  - [`datadog`](docs/providers/datadog.md#backend)
  - [`dynatrace`](docs/providers/dynatrace.md#backend)
  - [`<custom>`](docs/providers/custom.md#backend)

- `exporters`: A map of exporters to export results to. Each exporter is defined as a key formatted as `<exporter_name>/<optional_suffix>`, and a map value detailing the exporter configuration.

  ```yaml
  exporters:
    bigquery/dev:
      project_id: proj-bq-dev-a4b7
      dataset_id: my-test-dataset
      table_id: my-test-table
    prometheus:
      url: ${PROMETHEUS_URL}
  ```

  See specific providers documentation for detailed configuration:
  - [`bigquery`](docs/providers/bigquery.md#exporter) to export SLO reports to BigQuery for historical analysis and DataStudio reporting.
  - [`cloudevent`](docs/providers/cloudevent.md#exporter) to stream SLO reports to Cloudevent receivers.
  - [`pubsub`](docs/providers/pubsub.md#exporter) to stream SLO reports to Pubsub.
  - [`cloud_monitoring`](docs/providers/cloud_monitoring.md#exporter) to export metrics to Cloud Monitoring.
  - [`prometheus`](docs/providers/prometheus.md#exporter) to export metrics to Prometheus.
  - [`datadog`](docs/providers/datadog.md#exporter) to export metrics to Datadog.
  - [`dynatrace`](docs/providers/dynatrace.md#exporter) to export metrics to Dynatrace.
  - [`<custom>`](docs/providers/custom.md#exporter) to export SLO data or metrics to a custom destination.

- `error_budget_policies`: [**required**] A map of various error budget policies.
  - `<ebp_name>`: Name of the error budget policy.
    - `steps`: List of error budget policy steps, each containing the following fields:
      - `window`: Rolling time window for this error budget.
      - `alerting_burn_rate_threshold`: Target burnrate threshold over which alerting is needed.
      - `urgent_notification`: boolean whether violating this error budget should trigger a page.
      - `overburned_consequence_message`: message to show when the error budget is above the target.
      - `achieved_consequence_message`: message to show when the error budget is within the target.

  ```yaml
  error_budget_policies:
    default:
      steps:
      - name: 1 hour
        burn_rate_threshold: 9
        alert: true
        message_alert: Page to defend the SLO
        message_ok: Last hour on track
        window: 3600
      - name: 12 hours
        burn_rate_threshold: 3
        alert: true
        message_alert: Page to defend the SLO
        message_ok: Last 12 hours on track
        window: 43200
  ```

**&rarr; See [example Shared configuration](samples/config.yaml).**

## More documentation

To go further with the SLO Generator, you can read:

### [Build an SLO achievements report with BigQuery and DataStudio](docs/deploy/datastudio_slo_report.md)

### [Deploy the SLO Generator in Cloud Run](docs/deploy/cloudrun.md)

### [Deploy the SLO Generator in Kubernetes (Alpha)](docs/deploy/kubernetes.md)

### [Deploy the SLO Generator in a CloudBuild pipeline](docs/deploy/cloudbuild.md)

### [DEPRECATED: Deploy the SLO Generator on Google Cloud Functions (Terraform)](docs/deploy/cloudfunctions.md)

### [Contribute to the SLO Generator](CONTRIBUTING.md)
