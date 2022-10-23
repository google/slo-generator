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

import os
import unittest

from click.testing import CliRunner
from mock import patch

from slo_generator.cli import main
from slo_generator.utils import load_config

from .test_stubs import CTX, mock_sd

cwd = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(cwd))


class TestCLI(unittest.TestCase):
    def setUp(self):
        for key, value in CTX.items():
            os.environ[key] = value
        slo_config = f"{root}/samples/cloud_monitoring/slo_gae_app_availability.yaml"  # noqa: E501
        config = f"{root}/samples/config.yaml"
        self.slo_config = slo_config
        self.slo_metadata_name = load_config(slo_config, ctx=CTX)["metadata"]["name"]
        self.config = config
        self.cli = CliRunner()

    @patch("google.api_core.grpc_helpers.create_channel", return_value=mock_sd(8))
    def test_cli_compute(self, mock):
        args = ["compute", "-f", self.slo_config, "-c", self.config]
        result = self.cli.invoke(main, args)
        self.assertEqual(result.exit_code, 0)

    @patch("google.api_core.grpc_helpers.create_channel", return_value=mock_sd(40))
    def test_cli_compute_folder(self, mock):
        args = ["compute", "-f", f"{root}/samples/cloud_monitoring", "-c", self.config]
        result = self.cli.invoke(main, args)
        self.assertEqual(result.exit_code, 0)

    def test_cli_compute_no_config(self):
        args = ["compute", "-f", f"{root}/samples", "-c", f"{root}/samples/config.yaml"]
        result = self.cli.invoke(main, args)
        self.assertEqual(result.exit_code, 1)

    def test_cli_api(self):
        # TODO: Write test
        pass

    def test_cli_migrate(self):
        # TODO: Write test
        pass


if __name__ == "__main__":
    unittest.main()
