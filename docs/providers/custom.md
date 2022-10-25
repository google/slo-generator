# Custom

`slo-generator` allows you to load custom backends / exporters dynamically.

This enables you to:

* Support other backends or exporters that are not part of `slo-generator` core.
* Query or export from / to internal custom APIs.
* Create SLOs based on more complicated logic (e.g: fetch a Datastore record or run a BQ query).

## Backend

To create a custom backend, simply create a new file and add the backend code within it.

For this example, we will assume the backend code below was added to `custom/custom_backend.py`.

A sample custom backend will have the following look:

```py
class CustomBackend:
    def __init__(self, client=None, **kwargs):
        # create a client for your backend using **kwargs, use existing one, or
        # just ignore the init.
        # **kwargs are the fields specified in the backend section of your
        # SLO Config YAML file.
        pass

    def good_bad_ratio(self, timestamp, window, slo_config):
        # compute your good bad ratio in this method.
        # you can do anything here (query your internal API, correlate with
        # other data, etc...)
        # return a tuple (number_good_events, number_bad_events)
        return (100000, 100)

    def query_sli(self, timestamp, window, slo_config):
        # compute your SLI value directly.
        # return a float or integer.
        return 0.999
```

In order to call the `good_bad_ratio` method in the custom backend above, the `backends` block would look like this:

```yaml
backends:
  custom.custom_backend.CustomBackend: # relative Python path to the backend. Make sure  __init__.py is created in subdirectories for this to work.
    arg_1:  test_arg_1     # passed to kwargs in __init__
    arg_2:  test_arg_2     # passed to kwargs in __init__
```

The `spec` section in the SLO config would look like:

```yaml
backend: custom.custom_backend.CustomBackend
method: good_bad_ratio # name of the method to run
service_level_indicator: {}
```

**&rightarrow; [Full SLO config](../../samples/custom/slo_custom_app_availability_ratio.yaml)**

## Exporter

To create a custom exporter, simply create a new file and add the exporter code within it.

For the examples below, we will assume the exporter code below was added to `custom/custom_exporter.py`.

### Standard

A standard exporter:

* must implement the `export` method.

A sample exporter looks like:

```py
class CustomExporter:
    """Custom exporter."""

    def export(self, data, **config):
        """Export data.

        Args:
            data (dict): Data to send.
            config (dict): Exporter config.

        Returns:
            object: Custom exporter response.
        """
        # export your `data` (SLO report) using `config` to setup export
        # parameters that need to be configurable.
        return {
            'status': 'ok',
            'code': 200,
            'arg_1': config['arg_1']
        }
```

and the corresponding `exporters` section in your SLO config:

The `exporters` block in the shared config would look like this:

```yaml
exporters:
  custom.custom_exporter.CustomExporter: # relative Python path to the backend. Make sure  __init__.py is created in subdirectories for this to work.
    arg_1:  test_arg_1     # passed to kwargs in __init__
```

The `spec` section in the SLO config would look like:

```yaml
exporters: [custom.custom_exporter.CustomExporter]
```

### Metrics

A metrics exporter:

* must inherit from `slo_generator.exporters.base.MetricsExporter`.
* must implement the `export_metric` method which exports **one** metric. The `export_metric` function takes a metric dict as input, such as:

    ```py
    {
        "name": <METRIC_NAME>,
        "alias": <METRIC_NAME_RELABELED>,
        "additional_labels": [
            <METRIC_LABEL_1>,
            <METRIC_LABEL_2>
        ],
        "value": <METRIC_VALUE>,
        "timestamp": <METRIC_TIMESTAMP>,
        "description": <METRIC_DESCRIPTION>
    }
    ```

A sample metrics exporter will look like:

```py
from slo_generator.exporters.base import MetricsExporter

class CustomExporter(MetricsExporter): # derive from base class
    """Custom exporter."""

    def export_metric(self, data):
        """Export data to Custom Monitoring API.

        Args:
            data (dict): Metric data.

        Returns:
            object: Custom Monitoring API result.
        """
        # implement how to export 1 metric here...
        return {
            'status': 'ok',
            'code': 200,
        }
```

The `exporters` block in the shared config would look like this:

```yaml
exporters:
  custom.custom_exporter.CustomExporter: # relative Python path to the backend. Make sure  __init__.py is created in subdirectories for this to work.
    arg_1:  test_arg_1     # passed to kwargs in __init__
```

**Note:**

The `MetricsExporter` base class has the following behavior:

* The `metrics` block in the SLO config is passed to the base class `MetricsExporter`
* The base class `MetricsExporter` runs the `export` method which iterates through each metric and add information to it, such as the current value and timestamp.
* The base class `MetricsExporter` calls the derived class `export_metric` for each metric and pass it the metric data to export.
* The derived class for each metric to export. See [metrics](../shared/metrics.md) for more details on the `metrics` block.
