# Copyright 2020 Google Inc.
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

from slo_generator.report import SLOReport

from .test_stubs import mock_slo_report


class TestReport(unittest.TestCase):
    def test_report_enough_events(self):
        report_cfg = mock_slo_report("enough_events")
        report = SLOReport(**report_cfg)
        self.assertTrue(report.valid)
        self.assertEqual(report.sli_measurement, 0.5)
        self.assertEqual(report.alert, True)

    def test_report_no_good_events(self):
        report_cfg = mock_slo_report("no_good_events")
        report = SLOReport(**report_cfg)
        self.assertTrue(report.valid)
        self.assertEqual(report.sli_measurement, 0)

    def test_report_no_bad_events(self):
        report_cfg = mock_slo_report("no_bad_events")
        report = SLOReport(**report_cfg)
        self.assertTrue(report.valid)
        self.assertEqual(report.sli_measurement, 1)

    def test_report_valid_sli_value(self):
        report_cfg = mock_slo_report("valid_sli_value")
        report = SLOReport(**report_cfg)
        self.assertTrue(report.valid)
        self.assertEqual(report.sli_measurement, report_cfg["backend"]["sli"])
        self.assertEqual(report.alert, False)

    def test_report_no_events(self):
        report_cfg = mock_slo_report("no_events")
        report = SLOReport(**report_cfg)
        self.assertFalse(report.valid)

    def test_report_no_good_bad_events(self):
        report_cfg = mock_slo_report("no_good_bad_events")
        report = SLOReport(**report_cfg)
        self.assertFalse(report.valid)

    def test_report_not_enough_events(self):
        report_cfg = mock_slo_report("not_enough_events")
        report = SLOReport(**report_cfg)
        self.assertFalse(report.valid)

    def test_report_no_sli_value(self):
        report_cfg = mock_slo_report("no_sli_value")
        report = SLOReport(**report_cfg)
        self.assertFalse(report.valid)

    def test_report_no_backend_response_sli(self):
        report_cfg = mock_slo_report("no_backend_response_sli")
        report = SLOReport(**report_cfg)
        self.assertFalse(report.valid)

    def test_report_no_backend_response_ratio(self):
        report_cfg = mock_slo_report("no_backend_response_ratio")
        report = SLOReport(**report_cfg)
        self.assertFalse(report.valid)

    def test_report_invalid_backend_response_type(self):
        report_cfg = mock_slo_report("invalid_backend_response_type")
        report = SLOReport(**report_cfg)
        self.assertFalse(report.valid)
