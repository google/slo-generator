# SLO Generator API

## Description

The **SLO Generator API** is based on the [Functions Framework](https://cloud.google.com/functions/docs/functions-framework) 
allowing deployments to hosted services easier, such as 
[Kubernetes](./../../../deploy/kubernetes.md), [CloudRun](./../deploy/cloudrun.md) 
or [Cloud Functions](./../deploy/cloudfunctions.md).

## Run

To run the `slo-generator` API:

```
slo-generator api -c <CONFIG_PATH>
```
where:
  * `CONFIG_PATH` is the [Shared configuration](../../README.md#shared-configuration) file path or GCS URL.

## Modes of functioning

The API has two modes of functioning that can be controlled using the 
`--signature-type` CLI argument:

* In the `http` mode, it can receive HTTP requests containing SLO configs.

* In the `cloudevent` mode, it can receive HTTP POST requests containing SLO 
configs enclosed in the CloudEvent message, under the `data` key.


### Export-only API

By default, the API computes and export SLO reports using the `exporters:` 
config block in the Shared Config to get their configs, and the `exporters:` 
list in the SLO config.

Some use cases require to have a distinct service for the compute part, and 
another service for the export part.

It is possible to run the `slo-generator` API in `export` mode only:

```
slo-generator api --config /path/to/config.yaml --target export --signature-type=cloudevent
```

In this mode, the API accepts an 
[SLO report](../../tests/unit/fixtures/slo_report_v2.json) as a POST request, 
and exports that data to the required exporters, converting the data if need be 
such as for metrics exporters.

The exporters which are used for the export are configured using the 
`default_exporters` property in the `slo-generator` configuration.

For instance of an `export_config.yaml` for the export-only API:

```
default_exporters:
- bigquery
- bigquery/test

exporters:
  bigquery:
    project_id: test-project-id
    dataset_id: slo
    table_name: reports
  bigquery/test:
    project_id: test-project-id2
    dataset_id: slo
    table_name: reports
```

This API can be called like:

```
curl -X POST -H "Content-Type: application/json" -d @tests/fixtures/slo_report_v2.json
```

#### Using PubsubExporter for CloudEvents API

You can use the PubsubExporter to send data from one `slo-generator` service 
configured in compute mode to one configured in export mode:

* Compute + export to Pubsub service config [example](../../samples/config.yaml)
* Export-only service config [example](../../samples/config_export.yaml) with 
Bigquery configured.
