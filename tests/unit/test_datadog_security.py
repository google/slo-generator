# Copyright 2026 Google Inc.
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
from unittest.mock import patch

from slo_generator.backends.datadog import DatadogBackend
from slo_generator.datadog_utils import validate_api_host
from slo_generator.exporters.datadog import DatadogExporter


class TestDatadogSecurity(unittest.TestCase):
    def test_accepts_official_https_api_hosts(self):
        self.assertEqual(
            validate_api_host("https://api.datadoghq.eu/"),
            "https://api.datadoghq.eu",
        )
        self.assertEqual(
            validate_api_host("https://api.us2.ddog-gov.com:443"),
            "https://api.us2.ddog-gov.com",
        )

    def test_rejects_credential_redirects(self):
        invalid_hosts = [
            "http://attacker.example",
            "https://attacker.example",
            "https://api.datadoghq.com.attacker.example",
            "https://api.datadoghq.com@attacker.example",
            "https://api.datadoghq.com/redirect",
        ]
        for api_host in invalid_hosts:
            with self.subTest(api_host=api_host), self.assertRaises(ValueError):
                validate_api_host(api_host)

    @patch("slo_generator.backends.datadog.datadog.initialize")
    def test_backend_passes_only_explicit_validated_options(self, initialize):
        DatadogBackend(
            api_key="api-key",
            app_key="app-key",
            api_host="https://api.us3.datadoghq.com",
        )

        initialize.assert_called_once_with(
            api_key="api-key",
            app_key="app-key",
            api_host="https://api.us3.datadoghq.com",
        )
        with self.assertRaises(TypeError):
            DatadogBackend(proxies={"https": "https://attacker.example"})

    @patch("slo_generator.exporters.datadog.datadog.initialize")
    def test_exporter_rejects_redirect_before_initialization(self, initialize):
        data = {
            "api_key": "api-key",
            "app_key": "app-key",
            "api_host": "https://attacker.example",
        }

        with self.assertRaises(ValueError):
            DatadogExporter().export_metric(data)
        initialize.assert_not_called()


if __name__ == "__main__":
    unittest.main()
