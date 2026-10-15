# Copyright 2022 Google Inc.
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

# flake8: noqa

import unittest
from types import SimpleNamespace

from slo_generator.backends.cloud_monitoring import infer_threshold_bucket
from slo_generator.backends.cloud_monitoring_mql import CloudMonitoringMqlBackend


class TestCloudMonitoringMqlBackend(unittest.TestCase):
    def test_enrich_query_with_time_horizon_and_period(self):
        timestamp: float = 1666995015.5144777  # = 2022/10/28 22:10:15.5144777
        window: int = 3600  # in seconds
        query: str = """fetch gae_app
| metric 'appengine.googleapis.com/http/server/response_count'
| filter resource.project_id == 'slo-generator-demo'
| filter
    metric.response_code == 429
    || metric.response_code == 200
"""

        enriched_query = """fetch gae_app
| metric 'appengine.googleapis.com/http/server/response_count'
| filter resource.project_id == 'slo-generator-demo'
| filter
    metric.response_code == 429
    || metric.response_code == 200
| group_by [] | within 3600s, d'2022/10/28 22:10:15' | every 3600s"""

        assert (
            CloudMonitoringMqlBackend.enrich_query_with_time_horizon_and_period(
                timestamp, window, query
            )
            == enriched_query
        )

    def test_infer_threshold_bucket_from_value(self):
        exp_opts = SimpleNamespace(
            exponential_buckets=SimpleNamespace(
                growth_factor=1.4142135623730951,
                num_finite_buckets=64,
                scale=1.0,
            ),
            linear_buckets=None,
            explicit_buckets=None,
        )
        self.assertEqual(infer_threshold_bucket(exp_opts, 8.0), 6)
        self.assertEqual(infer_threshold_bucket(exp_opts, 9.0), 7)
        self.assertEqual(infer_threshold_bucket(exp_opts, 128.0), 14)
        self.assertEqual(infer_threshold_bucket(exp_opts, 724.0), 19)
        self.assertEqual(infer_threshold_bucket(exp_opts, 1e12), 65)

        lin_opts = SimpleNamespace(
            exponential_buckets=None,
            linear_buckets=SimpleNamespace(
                offset=0.0, width=10.0, num_finite_buckets=20
            ),
            explicit_buckets=None,
        )
        self.assertEqual(infer_threshold_bucket(lin_opts, 44.0), 5)
        self.assertEqual(infer_threshold_bucket(lin_opts, 50.0), 5)
        self.assertEqual(infer_threshold_bucket(lin_opts, 500.0), 21)

        explicit_opts = SimpleNamespace(
            exponential_buckets=None,
            linear_buckets=None,
            explicit_buckets=SimpleNamespace(bounds=[10.0, 25.0, 100.0, 500.0]),
        )
        self.assertEqual(infer_threshold_bucket(explicit_opts, 25.0), 1)
        self.assertEqual(infer_threshold_bucket(explicit_opts, 30.0), 2)
