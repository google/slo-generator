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

import importlib
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.environment = patch.dict(
            os.environ,
            {
                "CONFIG_PATH": "/tmp/slo-generator-test-config.yaml",
                "GOOGLE_FUNCTION_SIGNATURE_TYPE": "http",
            },
        )
        cls.environment.start()
        cls.main = importlib.import_module("slo_generator.api.main")

    @classmethod
    def tearDownClass(cls):
        cls.environment.stop()

    def test_compute_request_does_not_expand_service_environment(self):
        remote_config = "metadata:\n  marker: ${SERVER_SECRET}\n"
        request = MagicMock()
        request.args.get.return_value = False

        with (
            patch.dict(os.environ, {"SERVER_SECRET": "service-secret"}),
            tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as config_file,
        ):
            config_file.write("marker: ${SERVER_SECRET}\n")
            config_file.flush()
            with (
                patch.object(self.main, "CONFIG_PATH", config_file.name),
                patch.object(self.main, "process_req", return_value=remote_config),
                patch.object(self.main, "compute", return_value=[]) as compute,
                patch.object(self.main, "jsonify", side_effect=lambda value: value),
            ):
                self.main.run_compute(request)

        slo_config, shared_config = compute.call_args.args[:2]
        self.assertEqual(slo_config["metadata"]["marker"], "${SERVER_SECRET}")
        self.assertEqual(shared_config["marker"], "service-secret")

    def test_export_request_does_not_expand_service_environment(self):
        remote_report = "metadata:\n  marker: ${SERVER_SECRET}\n"
        request = MagicMock()

        with (
            patch.dict(os.environ, {"SERVER_SECRET": "service-secret"}),
            tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as config_file,
        ):
            config_file.write("default_exporters: [dummy]\n")
            config_file.flush()
            with (
                patch.object(self.main, "CONFIG_PATH", config_file.name),
                patch.object(self.main, "process_req", return_value=remote_report),
                patch.object(self.main, "get_exporters", return_value=[]),
                patch.object(self.main, "export", return_value=[]) as export,
                patch.object(self.main, "jsonify", side_effect=lambda value: value),
            ):
                self.main.run_export(request)

        slo_report = export.call_args.args[0]
        self.assertEqual(slo_report["metadata"]["marker"], "${SERVER_SECRET}")


if __name__ == "__main__":
    unittest.main()
