"""dummy_exporter.py

Dummy exporter implementation for testing.
"""
# pylint: disable=missing-class-docstring

from slo_generator.exporters.base import MetricsExporter


class FailExporter(MetricsExporter):

    def export_metric(self, data):
        raise ValueError("Oops !")
