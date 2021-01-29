# SLO Generator

![build](https://github.com/google/slo-generator/workflows/build/badge.svg)
![cloudbuild](https://github.com/google/slo-generator/workflows/cloudbuild/badge.svg)
[![PyPI version](https://badge.fury.io/py/slo-generator.svg)](https://badge.fury.io/py/slo-generator)

`slo-generator` is a tool to compute and export **Service Level Objectives** ([SLOs](https://landing.google.com/sre/sre-book/chapters/service-level-objectives/)),
**Error Budgets** and **Burn Rates**, using policies written in JSON or YAML format.

## Description
`slo-generator` will query metrics backend and compute the following metrics:

* **Service Level Objective** defined as `SLO (%) = GOOD_EVENTS / VALID_EVENTS`
* **Error Budget** defined as `ERROR_BUDGET = 100 - SLO (%)`
* **Burn Rate** defined as `BURN_RATE = ERROR_BUDGET / ERROR_BUDGET_TARGET`

## Local usage

**Requirements**

* Python 3

**Installation**

`slo-generator` is published on PyPI. To install it, run:

```sh
pip3 install slo-generator
```

**Run the `slo-generator`**

```
slo-generator -f <SLO_CONFIG_PATH> -b <ERROR_BUDGET_POLICY> --export
```
  * `<SLO_CONFIG_PATH>` is the [SLO config](#slo-configuration) file or folder.
    If a folder path is passed, the SLO configs filenames should match the pattern `slo_*.yaml` to be loaded.

  * `<ERROR_BUDGET_POLICY>` is the [Error Budget Policy](#error-budget-policy) file.

  * `--export` enables exporting data using the `exporters` defined in the SLO
  configuration file.

Use `slo-generator --help` to list all available arguments.

***Notes:***
* To enable **debug logs**, set the environment variable `DEBUG` to `1`.
* To enable **colorized output** (local usage), set the environment variable `COLORED_OUTPUT` to `1`.

## Configuration

The `slo-generator` requires two configuration files to run, the **SLO configuration** file and the **Error budget policy** file.

#### SLO configuration

The **SLO configuration** (JSON or YAML) is composed of the following fields:

* **SLO metadata**:
  * `slo_name`: Name of this SLO.
  * `slo_description`: Description of this SLO.
  * `slo_target`: SLO target (between 0 and 1).
  * `service_name`: Name of the monitored service.
  * `feature_name`: Name of the monitored subsystem.
  * `metadata`: Dict of user metadata.


* **SLI configuration**:
  * `backend`: Specific documentation and examples are available for each supported backends:
    * [Stackdriver Monitoring](docs/providers/stackdriver.md#backend)
    * [Stackdriver Service Monitoring](docs/providers/stackdriver_service_monitoring.md#backend)
    * [Prometheus](docs/providers/prometheus.md#backend)
    * [ElasticSearch](docs/providers/elasticsearch.md#backend)
    * [Datadog](docs/providers/datadog.md#backend)
    * [Dynatrace](docs/providers/dynatrace.md#backend)
    * [Custom](docs/providers/custom.md#backend)

- **Exporter configuration**:
  * `exporters`: A list of exporters to export results to. Specific documentation is available for each supported exporters:
      * [Cloud Pub/Sub](docs/providers/pubsub.md#exporter) to stream SLO reports.
      * [BigQuery](docs/providers/bigquery.md#exporter) to export SLO reports to BigQuery for historical analysis and DataStudio reporting.
      * [Stackdriver Monitoring](docs/providers/stackdriver.md#exporter) to export metrics to Stackdriver Monitoring.
      * [Prometheus](docs/providers/prometheus.md#exporter) to export metrics to Prometheus.
      * [Datadog](docs/providers/datadog.md#exporter) to export metrics to Datadog.
      * [Dynatrace](docs/providers/dynatrace.md#exporter) to export metrics to Dynatrace.
      * [Custom](docs/providers/custom.md#exporter) to export SLO data or metrics to a custom destination.

***Note:*** *you can use environment variables in your SLO configs by using `${MY_ENV_VAR}` syntax to avoid having sensitive data in version control. Environment variables will be replaced at run time.*

==> An example SLO configuration file is available [here](samples/stackdriver/slo_gae_app_availability.yaml).

#### Error Budget policy

The **Error Budget policy** (JSON or YAML) is a list of multiple error budgets, each one composed of the following fields:

* `window`: Rolling time window for this error budget.
* `alerting_burn_rate_threshold`: Target burnrate threshold over which alerting is needed.
* `urgent_notification`: boolean whether violating this error budget should trigger a page.
* `overburned_consequence_message`: message to show when the error budget is above the target.
* `achieved_consequence_message`: message to show when the error budget is within the target.

==> An example Error Budget policy is available [here](samples/error_budget_policy.yaml).

## More documentation

To go further with the SLO Generator, you can read:

* [Build an SLO achievements report with BigQuery and DataStudio](docs/deploy/datastudio_slo_report.md)

* [Deploy the SLO Generator on Google Cloud Functions (Terraform)](docs/deploy/cloudfunctions.md)

* [Deploy the SLO Generator on Kubernetes (Alpha)](docs/deploy/kubernetes.md)

* [Deploy the SLO Generator in a CloudBuild pipeline](docs/deploy/cloudbuild.md)

* [Contribute to the SLO Generator](CONTRIBUTING.md)
