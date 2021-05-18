from slo_generator.exporters.base import MetricsExporter


class FailExporter(MetricsExporter):

    def export_metric(self, data):
        raise ValueError("Oops !")
