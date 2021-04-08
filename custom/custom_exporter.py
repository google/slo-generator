import pprint
import logging

from prometheus_client import Gauge
from slo_generator.exporters.base import MetricsExporter

gauge_map = {}

class PrometheusExporter(MetricsExporter):
    def export_metric(self, data):
        """Export data.

        Args:
            data (dict): Data to send.
            config (dict): Exporter config.

        Returns:
            object: Custom exporter response.
        """
        # export your `data` (SLO report) using `config` to setup export
        # parameters that need to be configurable.
        name = data['name']
        description = data['description']
        value = data['value']

        # Write timeseries w/ metric labels.
        labels = data['labels']
        if name in gauge_map:
            gauge = gauge_map[name]
        else:
            gauge = Gauge(name,
                          description,
                          labelnames=labels.keys())
            gauge_map[name] = gauge
        gauge.labels(*labels.values()).set(value)
        return {
            'status': 'ok',
            'code': 200,
        }