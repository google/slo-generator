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
import warnings

from datadog.api import Metric, ServiceLevelObjective
from elasticsearch import Elasticsearch
from google.auth._default import _CLOUD_SDK_CREDENTIALS_WARNING
from mock import MagicMock, patch
from prometheus_http_client import Prometheus
from splunklib import client as Splunk
from splunklib.client import Jobs

from slo_generator.backends.dynatrace import DynatraceClient
from slo_generator.compute import compute, export
from slo_generator.exporters.base import MetricsExporter
from slo_generator.exporters.bigquery import BigQueryError

from .test_stubs import (
    CTX,
    load_fixture,
    load_sample,
    load_slo_samples,
    mock_dd_metric_query,
    mock_dd_metric_send,
    mock_dd_slo_get,
    mock_dd_slo_history,
    mock_dt,
    mock_dt_errors,
    mock_es,
    mock_prom,
    mock_sd,
    mock_splunk_oneshot,
    mock_ssm_client,
)

warnings.filterwarnings("ignore", message=_CLOUD_SDK_CREDENTIALS_WARNING)

CONFIG = load_sample("config.yaml", CTX)
STEPS = len(CONFIG["error_budget_policies"]["default"]["steps"])
SLO_CONFIGS_SD = load_slo_samples("cloud_monitoring", CTX)
SLO_CONFIGS_SDSM = load_slo_samples("cloud_service_monitoring", CTX)
SLO_CONFIGS_PROM = load_slo_samples("prometheus", CTX)
SLO_CONFIGS_ES = load_slo_samples("elasticsearch", CTX)
SLO_CONFIGS_DD = load_slo_samples("datadog", CTX)
SLO_CONFIGS_DT = load_slo_samples("dynatrace", CTX)
SLO_CONFIGS_SPLUNK = load_slo_samples("splunk", CTX)
SLO_REPORT = load_fixture("slo_report_v2.json")
SLO_REPORT_V1 = load_fixture("slo_report_v1.json")
EXPORTERS = load_fixture("exporters.yaml", CTX)
BQ_ERROR = load_fixture("bq_error.json")

# Pub/Sub methods to patch
PUBSUB_MOCKS = [
    "google.cloud.pubsub_v1.gapic.publisher_client.PublisherClient.publish",
    "google.cloud.pubsub_v1.publisher.futures.Future.result",
    "google.api_core.grpc_helpers.create_channel",
]

# Service Monitoring method to patch
SSM_MOCKS = [
    "slo_generator.backends.cloud_service_monitoring.ServiceMonitoringServiceClient",
    "slo_generator.backends.cloud_service_monitoring.SSM.to_json",
]


class TestCompute(unittest.TestCase):
    maxDiff = None

    @patch.object(Jobs, "oneshot", side_effect=mock_splunk_oneshot)
    @patch.object(Splunk, "connect", return_value=None)
    def test_splunk_search(self, *mocks):
        for config in SLO_CONFIGS_SPLUNK:
            with self.subTest(config=config):
                compute(config, CONFIG)

    @patch(
        "google.api_core.grpc_helpers.create_channel",
        return_value=mock_sd(2 * STEPS * len(SLO_CONFIGS_SD)),
    )
    def test_compute_stackdriver(self, mock):
        for config in SLO_CONFIGS_SD:
            with self.subTest(config=config):
                compute(config, CONFIG)

    @patch(SSM_MOCKS[0], return_value=mock_ssm_client())
    @patch(SSM_MOCKS[1], return_value=MagicMock(side_effect=mock_ssm_client.to_json))
    @patch(
        "google.api_core.grpc_helpers.create_channel",
        return_value=mock_sd(2 * STEPS * len(SLO_CONFIGS_SDSM)),
    )
    def test_compute_ssm(self, *mocks):
        for config in SLO_CONFIGS_SDSM:
            with self.subTest(config=config):
                compute(config, CONFIG)

    @patch(SSM_MOCKS[0], return_value=mock_ssm_client())
    @patch(SSM_MOCKS[1], return_value=MagicMock(side_effect=mock_ssm_client.to_json))
    @patch(
        "google.api_core.grpc_helpers.create_channel",
        return_value=mock_sd(2 * STEPS * len(SLO_CONFIGS_SDSM)),
    )
    @patch(PUBSUB_MOCKS[0])
    @patch(PUBSUB_MOCKS[1])
    def test_compute_ssm_delete_export(self, *mocks):
        for config in SLO_CONFIGS_SDSM:
            with self.subTest(config=config):
                compute(config, CONFIG, delete=True, do_export=True)

    @patch.object(Prometheus, "query", mock_prom)
    def test_compute_prometheus(self):
        for config in SLO_CONFIGS_PROM:
            with self.subTest(config=config):
                compute(config, CONFIG)

    @patch.object(Elasticsearch, "search", mock_es)
    def test_compute_elasticsearch(self):
        for config in SLO_CONFIGS_ES:
            with self.subTest(config=config):
                compute(config, CONFIG)

    @patch.object(Metric, "query", mock_dd_metric_query)
    @patch.object(ServiceLevelObjective, "history", mock_dd_slo_history)
    @patch.object(ServiceLevelObjective, "get", mock_dd_slo_get)
    def test_compute_datadog(self):
        for config in SLO_CONFIGS_DD:
            with self.subTest(config=config):
                compute(config, CONFIG)

    @patch.object(DynatraceClient, "request", side_effect=mock_dt)
    def test_compute_dynatrace(self, mock):
        for config in SLO_CONFIGS_DT:
            with self.subTest(config=config):
                compute(config, CONFIG)

    @patch(PUBSUB_MOCKS[0])
    @patch(PUBSUB_MOCKS[1])
    @patch(PUBSUB_MOCKS[2])
    def test_export_pubsub(self, *mocks):
        export(SLO_REPORT, EXPORTERS[0])

    @patch("google.api_core.grpc_helpers.create_channel", return_value=mock_sd(STEPS))
    def test_export_stackdriver(self, mock):
        export(SLO_REPORT, EXPORTERS[1])

    @patch("google.cloud.bigquery.Client.get_table")
    @patch("google.cloud.bigquery.Client.create_table")
    @patch("google.cloud.bigquery.Client.update_table")
    @patch("google.cloud.bigquery.Client.insert_rows_json", return_value=[])
    def test_export_bigquery(self, *mocks):
        export(SLO_REPORT, EXPORTERS[2])

    @patch("google.cloud.bigquery.Client.get_table")
    @patch("google.cloud.bigquery.Client.create_table")
    @patch("google.cloud.bigquery.Client.update_table")
    @patch("google.cloud.bigquery.Client.insert_rows_json", return_value=BQ_ERROR)
    def test_export_bigquery_error(self, *mocks):
        with self.assertRaises(BigQueryError):
            export(SLO_REPORT, EXPORTERS[2], raise_on_error=True)

    @patch("prometheus_client.push_to_gateway")
    def test_export_prometheus(self, mock):
        export(SLO_REPORT, EXPORTERS[3])

    def test_export_prometheus_self(self):
        export(SLO_REPORT, EXPORTERS[7])

    @patch.object(Metric, "send", mock_dd_metric_send)
    def test_export_datadog(self):
        export(SLO_REPORT, EXPORTERS[4])

    @patch.object(DynatraceClient, "request", side_effect=mock_dt)
    def test_export_dynatrace(self, mock):
        export(SLO_REPORT, EXPORTERS[5])

    @patch.object(DynatraceClient, "request", side_effect=mock_dt_errors)
    def test_export_dynatrace_error(self, mock):
        responses = export(SLO_REPORT, EXPORTERS[5])
        codes = [r[0]["response"]["error"]["code"] for r in responses]
        self.assertTrue(all(code == 429 for code in codes))

    def test_metrics_exporter_build_data_labels(self):
        exporter = MetricsExporter()
        data = SLO_REPORT_V1
        labels = ["service_name", "slo_name", "metadata"]
        result = exporter.build_data_labels(data, labels)
        expected = {
            "service_name": SLO_REPORT_V1["service_name"],
            "slo_name": SLO_REPORT_V1["slo_name"],
            "env": SLO_REPORT_V1["metadata"]["env"],
            "team": SLO_REPORT_V1["metadata"]["team"],
        }
        self.assertEqual(result, expected)

    @patch("google.api_core.grpc_helpers.create_channel", return_value=mock_sd(STEPS))
    @patch("google.cloud.bigquery.Client.get_table")
    @patch("google.cloud.bigquery.Client.create_table")
    @patch("google.cloud.bigquery.Client.update_table")
    @patch("google.cloud.bigquery.Client.insert_rows_json", return_value=BQ_ERROR)
    def test_export_multiple_error(self, *mocks):
        exporters = [EXPORTERS[1], EXPORTERS[2]]
        errors = export(SLO_REPORT, exporters)
        self.assertEqual(len(errors), 1)
        self.assertIn("BigQueryError", errors[0])

    @patch("google.api_core.grpc_helpers.create_channel", return_value=mock_sd(STEPS))
    @patch("google.cloud.bigquery.Client.get_table")
    @patch("google.cloud.bigquery.Client.create_table")
    @patch("google.cloud.bigquery.Client.update_table")
    @patch("google.cloud.bigquery.Client.insert_rows_json", return_value=BQ_ERROR)
    def test_export_multiple_error_raise(self, *mocks):
        exporters = [EXPORTERS[1], EXPORTERS[2]]
        with self.assertRaises(BigQueryError):
            export(SLO_REPORT, exporters, raise_on_error=True)

    def test_export_wrong_class(self):
        exporters = [{"class": "Unknown"}]
        with self.assertRaises(ImportError):
            export(SLO_REPORT, exporters, raise_on_error=True)


if __name__ == "__main__":
    unittest.main()
