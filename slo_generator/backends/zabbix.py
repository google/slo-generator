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
`zabbix.py`
Zabbix backend implementation.
"""

from pyzabbix import ZabbixAPI
import logging

LOGGER = logging.getLogger(__name__)


class ZabbixBackend:
    """Backend for querying metrics from Zabbix.
    Args:
        client (obj, optional): Existing `requests.Session` to pass.
        api_url (str): PRTG API URL.
        api_passhash (str): PRTG passhash.
    """
    def __init__(self, client=None, user=None, password=None, api_url=None):
        self.client = client
        if not self.client:
            self.client = ZabbixAPI(api_url, use_authenticate=False)
            self.client.session.verify = False
            self.client.login(user, password)

    def query_sli(self, timestamp, window, slo_config):
        """Query SLI value from a given PromQL expression.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            float: SLI value.
        """
        measurement = slo_config['spec']['service_level_indicator']
        service_id = measurement['service_id'] #serive_id "Firewall Cluster (Availability)"

        response = self.client.service.getsla(serviceids=service_id, intervals=[  {
                "from": timestamp - window,
                "to": timestamp
            }])
        sli_value = response[service_id]["sla"][0]["sla"]
        LOGGER.debug(f"SLI value: {sli_value}")
        return sli_value
