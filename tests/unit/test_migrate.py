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

from slo_generator.migrations.migrator import slo_config_v1tov2

from .test_stubs import load_fixture


class TestMigrator(unittest.TestCase):
    def setUp(self):
        self.slo_config_v1 = load_fixture("slo_config_v1.yaml")
        self.slo_config_v2 = load_fixture("slo_config_v2.yaml")
        self.shared_config = {
            "backends": {},
            "exporters": {},
            "error_budget_policies": {},
        }

    def test_migrate_v1_to_v2(self):
        slo_config_migrated = slo_config_v1tov2(
            self.slo_config_v1, self.shared_config, quiet=True
        )
        self.assertDictEqual(slo_config_migrated, self.slo_config_v2)
