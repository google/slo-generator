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
        tz_UTC = "UTC"
        tz_Paris = "Europe/Paris"
        tz_Chicago = "America/Chicago"

        # Timestamp 1
        timestamp_20230615T16 = 1686845838
        utc_time_20230615T16 = "2023-06-15T16:17:18+00:00"
        paris_time_20230615T16 = "2023-06-15T18:17:18+02:00"
        chicago_time_20230615T16 = "2023-06-15T11:17:18-05:00"
        human_utc_20230615T16 = get_human_time(timestamp_20230615T16, timezone=tz_UTC)
        human_paris_20230615T16 = get_human_time(
            timestamp_20230615T16, timezone=tz_Paris
        )
        human_chicago_20230615T16 = get_human_time(
            timestamp_20230615T16, timezone=tz_Chicago
        )

        # Timestamp 2
        timestamp_20231215T16 = 1702660513.987654
        utc_time_20231215T16 = "2023-12-15T17:15:13.987654+00:00"
        paris_time_20231215T16 = "2023-12-15T18:15:13.987654+01:00"
        chicago_time_20231215T16 = "2023-12-15T11:15:13.987654-06:00"
        human_utc_20231215T16 = get_human_time(timestamp_20231215T16, timezone=tz_UTC)
        human_paris_20231215T16 = get_human_time(
            timestamp_20231215T16, timezone=tz_Paris
        )
        human_chicago_20231215T16 = get_human_time(
            timestamp_20231215T16, timezone=tz_Chicago
        )

        self.assertEqual(utc_time_20230615T16, human_utc_20230615T16)
        self.assertEqual(paris_time_20230615T16, human_paris_20230615T16)
        self.assertEqual(chicago_time_20230615T16, human_chicago_20230615T16)

        self.assertEqual(utc_time_20231215T16, human_utc_20231215T16)
        self.assertEqual(paris_time_20231215T16, human_paris_20231215T16)
        self.assertEqual(chicago_time_20231215T16, human_chicago_20231215T16)

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
