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
"""
`compute.py`
Compute utilities.
"""

import logging
import pprint
import time

from slo_generator import utils
from slo_generator.report import SLOReport
from slo_generator.migrations.migrator import report_v2tov1

LOGGER = logging.getLogger(__name__)


def compute(slo_config,
            config,
            timestamp=None,
            client=None,
            do_export=False,
            delete=False):
    """Run pipeline to compute SLO, Error Budget and Burn Rate, and export the
    results (if exporters are specified in the SLO config).

    Args:
        slo_config (dict): SLO configuration.
        config (dict): SLO Generator configuration.
        timestamp (float, optional): UNIX timestamp. Defaults to now.
        client (obj, optional): Existing metrics backend client.
        do_export (bool, optional): Enable / Disable export. Default: False.
        delete (bool, optional): Enable / Disable delete mode. Default: False.
    """
    start = time.time()
    if timestamp is None:
        timestamp = time.time()

    if slo_config is None:
        LOGGER.error('SLO configuration is empty')
        return []

    # Get exporters, backend and error budget policy
    spec = slo_config['spec']
    exporters = utils.get_exporters(config, spec)
    error_budget_policy = utils.get_error_budget_policy(config, spec)
    backend = utils.get_backend(config, spec)
    reports = []
    for step in error_budget_policy['steps']:
        report = SLOReport(config=slo_config,
                           backend=backend,
                           step=step,
                           timestamp=timestamp,
                           client=client,
                           delete=delete)

        if not report.valid:
            continue

        if delete:  # delete mode is enabled
            continue

        LOGGER.info(report)
        json_report = report.to_json()

        if exporters is not None and do_export is True:
            responses = export(json_report, exporters)
            json_report['exporters'] = responses
        reports.append(json_report)
    end = time.time()
    run_duration = round(end - start, 1)
    LOGGER.debug(pprint.pformat(reports))
    LOGGER.info(f'Run finished successfully in {run_duration}s.')
    return reports


def export(data, exporters, raise_on_error=False):
    """Export data using selected exporters.

    Args:
        data (dict): Data to export.
        exporters (list): List of exporter configurations.

    Returns:
        obj: Return values from exporters output.
    """
    LOGGER.debug(f'Exporters: {pprint.pformat(exporters)}')
    LOGGER.debug(f'Data: {pprint.pformat(data)}')
    responses = []

    # Convert data to export from v1 to v2 for backwards-compatible exports
    data = report_v2tov1(data)

    # Passing one exporter as a dict will work for convenience
    if isinstance(exporters, dict):
        exporters = [exporters]

    for config in exporters:
        try:
            exporter_class = config.get('class')
            instance = utils.get_exporter_cls(exporter_class)
            if not instance:
                continue
            LOGGER.info(
                f'Exporting SLO report using {exporter_class}Exporter ...')
            LOGGER.debug(f'Exporter config: {pprint.pformat(config)}')
            response = instance().export(data, **config)
            if isinstance(response, list):
                for elem in response:
                    elem['exporter'] = exporter_class
            responses.append(response)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.critical(exc, exc_info=True)
            LOGGER.error(f'{exporter_class}Exporter failed. Passing.')
            if raise_on_error:
                raise exc
            responses.append(exc)
    return responses
