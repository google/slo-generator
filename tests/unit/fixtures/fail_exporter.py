"""dummy_exporter.py

Dummy exporter implementation for testing.
"""

from slo_generator.exporters.base import MetricsExporter


# pylint: disable=missing-class-docstring
class FailExporter(MetricsExporter):
    def export_metric(self, data):
        raise ValueError("Oops !")
