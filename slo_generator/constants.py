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
"""
`constants.py`
Constants and environment variables used in `slo-generator`.
"""
import os

NO_DATA = -1
MIN_VALID_EVENTS = int(os.environ.get("MIN_VALID_EVENTS", "1"))
COLORED_OUTPUT = int(os.environ.get("COLORED_OUTPUT", "0"))
DRY_RUN = bool(int(os.environ.get("DRY_RUN", "0")))
