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
from typing import Optional

from slo_generator import constants, utils
from slo_generator.migrations.migrator import report_v2tov1
from slo_generator.report import SLOReport

LOGGER = logging.getLogger(__name__)


# pylint: disable=too-many-arguments,too-many-locals
def compute(
    slo_config: dict,
    config: dict,
    timestamp: Optional[float] = None,
    client=None,
    do_export: bool = False,
    delete: bool = False,
):
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
        LOGGER.error("SLO configuration is empty")
        return []

    # Get exporters, backend and error budget policy
    spec = slo_config["spec"]
    exporters = utils.get_exporters(config, spec)
    default_exporters_spec = {"exporters": config.get("default_exporters", [])}
    default_exporters = utils.get_exporters(config, default_exporters_spec)
    exporters.extend(x for x in default_exporters if x not in exporters)
    error_budget_policy = utils.get_error_budget_policy(config, spec)
    backend = utils.get_backend(config, spec)
    reports = []
    for step in error_budget_policy["steps"]:
        report = SLOReport(
            config=slo_config,
            backend=backend,
            step=step,
            timestamp=timestamp,
            client=client,
            delete=delete,
        )
        json_report = report.to_json()

        if not report.valid:
            LOGGER.error(report)
            reports.append(json_report)
            continue

        if delete:  # delete mode is enabled
            continue

        LOGGER.info(report)
        if exporters is not None and do_export is True:
            errors = export(json_report, exporters)
            json_report["errors"].extend(errors)
        reports.append(json_report)
    end = time.time()
    run_duration = round(end - start, 1)
    LOGGER.debug(pprint.pformat(reports))
    LOGGER.info(f"Run finished successfully in {run_duration}s.")
    return reports


def export(data: dict, exporters: list, raise_on_error: bool = False) -> list:
    """Export data using selected exporters.

    Args:
        data (dict): Data to export.
        exporters (list): List of exporter configurations.

    Returns:
        list: List of export errors.
    """
    LOGGER.debug(f"Exporters: {pprint.pformat(exporters)}")
    LOGGER.debug(f"Data: {pprint.pformat(data)}")
    name = data["metadata"]["name"]
    ebp_step = data["error_budget_policy_step_name"]
    info = f"{name :<32} | {ebp_step :<8}"
    errors = []

    # Passing one exporter as a dict will work for convenience
    if isinstance(exporters, dict):
        exporters = [exporters]
    if not exporters:
        error = "No exporters were found."
        LOGGER.error(f"{info} | {error}")
        errors.append(error)

    for exporter in exporters:
        try:
            cls = exporter.get("class")
            name = exporter.get("name")
            instance = utils.get_exporter_cls(cls)
            if not instance:
                raise ImportError("Exporter not found in shared config.")
            LOGGER.debug(f"Exporter config: {pprint.pformat(exporter)}")

            # Convert data to export from v1 to v2 for backwards-compatible
            # exporters such as BigQuery.
            json_data = data
            if cls not in constants.V2_EXPORTERS:
                LOGGER.debug(f"{info} | Converting SLO report to v1.")
                json_data = report_v2tov1(data)
            LOGGER.debug(f"{info} | SLO report: {json_data}")
            response = instance().export(json_data, **exporter)
            LOGGER.info(f'{info} | SLO report sent to "{name}" exporter successfully.')
            LOGGER.debug(f"{info} | {response}")
        except Exception as exc:  # pylint: disable=broad-except
            if raise_on_error:
                raise exc
            tbk = utils.fmt_traceback(exc)
            error = f'{cls}Exporter "{name}" failed. | {tbk}'
            LOGGER.error(f"{info} | {error}")
            LOGGER.exception(exc)
            errors.append(error)
    return errors
