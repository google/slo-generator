# Copyright 2019 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from slo_generator.utils import (
    get_backend_cls,
    get_exporter_cls,
    get_human_time,
    import_dynamic,
)


class TestUtils(unittest.TestCase):
    def test_get_human_time(self):
        # Timezones
        tz_1 = "Europe/Paris"
        tz_2 = "America/Chicago"

        # Timestamp 1
        timestamp = 1565092435
        utc_time = "2019-08-06T11:53:55.000000"
        human_paris_1 = get_human_time(timestamp, timezone=tz_1)
        human_chicago_1 = get_human_time(timestamp, timezone=tz_2)

        # Timestamp 2
        timestamp_2 = 1565095633.9568892
        utc_time_2 = "2019-08-06T12:47:13.956889"
        human_paris_2 = get_human_time(timestamp_2, timezone=tz_1)
        human_chicago_2 = get_human_time(timestamp_2, timezone=tz_2)

        self.assertEqual(human_paris_1, utc_time + "+02:00")
        self.assertEqual(human_chicago_1, utc_time + "-05:00")
        self.assertEqual(human_paris_2, utc_time_2 + "+02:00")
        self.assertEqual(human_chicago_2, utc_time_2 + "-05:00")

    def test_get_backend_cls(self):
        res1 = get_backend_cls("CloudMonitoring")
        res2 = get_backend_cls("Prometheus")
        self.assertEqual(res1.__name__, "CloudMonitoringBackend")
        self.assertEqual(res1.__module__, "slo_generator.backends.cloud_monitoring")
        self.assertEqual(res2.__name__, "PrometheusBackend")
        self.assertEqual(res2.__module__, "slo_generator.backends.prometheus")
        with self.assertWarns(ImportWarning):
            get_backend_cls("UndefinedBackend")

    def test_get_backend_dynamic_cls(self):
        res1 = get_backend_cls("pathlib.Path")
        self.assertEqual(res1.__name__, "Path")
        self.assertEqual(res1.__module__, "pathlib")
        with self.assertWarns(ImportWarning):
            get_exporter_cls("foo.bar.DoesNotExist")

    def test_get_exporter_cls(self):
        res1 = get_exporter_cls("CloudMonitoring")
        res2 = get_exporter_cls("Pubsub")
        res3 = get_exporter_cls("Bigquery")
        self.assertEqual(res1.__name__, "CloudMonitoringExporter")
        self.assertEqual(res1.__module__, "slo_generator.exporters.cloud_monitoring")
        self.assertEqual(res2.__name__, "PubsubExporter")
        self.assertEqual(res2.__module__, "slo_generator.exporters.pubsub")
        self.assertEqual(res3.__name__, "BigqueryExporter")
        self.assertEqual(res3.__module__, "slo_generator.exporters.bigquery")
        with self.assertWarns(ImportWarning):
            get_exporter_cls("UndefinedExporter")

    def test_get_exporter_dynamic_cls(self):
        res1 = get_exporter_cls("pathlib.Path")
        self.assertEqual(res1.__name__, "Path")
        self.assertEqual(res1.__module__, "pathlib")
        with self.assertWarns(ImportWarning):
            get_exporter_cls("foo.bar.DoesNotExist")

    def test_import_dynamic(self):
        res1 = import_dynamic(
            "slo_generator.backends.cloud_monitoring",
            "CloudMonitoringBackend",
            prefix="backend",
        )
        res2 = import_dynamic(
            "slo_generator.exporters.cloud_monitoring",
            "CloudMonitoringExporter",
            prefix="exporter",
        )
        self.assertEqual(res1.__name__, "CloudMonitoringBackend")
        self.assertEqual(res2.__name__, "CloudMonitoringExporter")
        with self.assertWarns(ImportWarning):
            import_dynamic(
                "slo_generator.backends.unknown",
                "CloudMonitoringUnknown",
                prefix="unknown",
            )


if __name__ == "__main__":
    unittest.main()
