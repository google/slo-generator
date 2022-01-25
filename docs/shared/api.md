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

* In the `http` mode, it can receive HTTP requests containing SLO configs YAMLs 
such as:

```
{
    "data": <BASE64ENCODED_CONTENT>
}
```


### Export-only API

By default, the API computes and export SLO reports using the `exporters:` 
block in the Shared Config to get their configs, and the `exporters: []` list in the SLO config.

Some use cases require to have a distinct service for the compute part, and 
another service for the export part.

It is possible to run the `slo-generator` API in `export` mode only:

```
slo-generator api --config /path/to/config.yaml --target export
```

The exporters are configured using a simple `exporters.yaml` 
