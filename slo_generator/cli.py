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
`cli.py`
Command-Line interface of `slo-generator`.
"""

import logging
import os
import sys
import time
from pathlib import Path

import click
from pkg_resources import get_distribution

from slo_generator import utils
from slo_generator.compute import compute as _compute
from slo_generator.constants import LATEST_MAJOR_VERSION
from slo_generator.migrations import migrator

sys.path.append(os.getcwd())  # dynamic backend loading

LOGGER = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option(
    "--version",
    "-v",
    is_flag=True,
    help="Show slo-generator version.",
)
@click.pass_context
def main(ctx, version):
    """CLI entrypoint."""
    utils.setup_logging()
    if ctx.invoked_subcommand is None or version:
        ver = get_distribution("slo-generator").version
        print(f"slo-generator v{ver}")
        sys.exit(0)


@main.command()
@click.option(
    "--slo-config",
    "-f",
    type=click.Path(),
    required=True,
    help="SLO config path",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    default="config.yaml",
    show_default=True,
    help="slo-generator config path",
)
@click.option(
    "--export",
    "-e",
    is_flag=True,
    help="Export SLO report to exporters",
)
@click.option(
    "--delete",
    "-d",
    is_flag=True,
    help="Delete mode (used for backends with SLO APIs)",
)
@click.option(
    "--timestamp",
    "-t",
    type=float,
    default=time.time(),
    help="End timestamp for query.",
)
def compute(slo_config, config, export, delete, timestamp):
    """Compute SLO report."""
    start = time.time()

    # Load slo-generator config
    LOGGER.debug(f"Loading slo-generator config from {config}")
    config_dict = utils.load_config(config)

    # Load SLO config(s)
    if Path(slo_config).is_dir():
        slo_configs = utils.load_configs(slo_config, kind="ServiceLevelObjective")
    else:
        slo_configs = [utils.load_config(slo_config, kind="ServiceLevelObjective")]

    if not slo_configs:
        LOGGER.error(f"No SLO configs found in {slo_config}.")
        sys.exit(1)

    # Load SLO configs and compute SLO reports
    all_reports = {}
    for slo_config_dict in slo_configs:
        reports = _compute(
            slo_config_dict,
            config_dict,
            timestamp=timestamp,
            do_export=export,
            delete=delete,
        )
        if reports:
            name = slo_config_dict["metadata"]["name"]
            all_reports[name] = reports
    end = time.time()
    duration = round(end - start, 1)
    LOGGER.info(
        f"Run summary | SLO Configs: {len(slo_configs)} | " f"Duration: {duration}s"
    )
    LOGGER.debug(all_reports)
    return all_reports


# pylint: disable=import-error,import-outside-toplevel
@main.command()
@click.pass_context
@click.option(
    "--config",
    "-c",
    envvar="CONFIG_PATH",
    required=True,
    help="slo-generator configuration file path.",
)
@click.option(
    "--exporters",
    "-e",
    envvar="EXPORTERS",
    required=False,
    default="",
    help="List of exporters to send data to",
)
@click.option(
    "--signature-type",
    envvar="GOOGLE_FUNCTION_SIGNATURE_TYPE",
    default="http",
    type=click.Choice(["http", "cloudevent"]),
    help="Signature type",
)
@click.option(
    "--target",
    envvar="GOOGLE_FUNCTION_TARGET",
    default="run_compute",
    help="Target function name",
)
@click.option(
    "--port",
    "-p",
    default=8080,
    help="HTTP port",
)
# pylint: disable=too-many-arguments
def api(ctx, config, exporters, signature_type, target, port):
    """Run an API that can receive requests (supports both 'http' and
    'cloudevents' signature types)."""
    from functions_framework._cli import _cli

    os.environ["EXPORTERS"] = exporters
    os.environ["CONFIG_PATH"] = config
    os.environ["GOOGLE_FUNCTION_SIGNATURE_TYPE"] = signature_type
    os.environ["GOOGLE_FUNCTION_TARGET"] = target
    ctx.invoke(
        _cli,
        target=target,
        source=Path(__file__).parent / "api" / "main.py",
        signature_type=signature_type,
        port=port,
    )


@main.command()
@click.option(
    "--source",
    "-s",
    type=click.Path(exists=True, resolve_path=True, readable=True),
    required=True,
    default=Path.cwd(),
    help="Source SLO configs folder",
)
@click.option(
    "--target",
    "-t",
    type=click.Path(resolve_path=True),
    default=Path.cwd(),
    required=True,
    help="Target SLO configs folder",
)
@click.option(
    "--error-budget-policy-path",
    "-b",
    type=click.Path(exists=True, resolve_path=True, readable=True),
    required=False,
    multiple=True,
    default=["error_budget_policy.yaml"],
    help="Error budget policy path",
)
@click.option(
    "--exporters-path",
    "-e",
    type=click.Path(exists=True, resolve_path=True, readable=True),
    required=False,
    multiple=True,
    help="Exporters path",
)
@click.option(
    "--version",
    type=str,
    required=False,
    default=LATEST_MAJOR_VERSION,
    show_default=True,
    help="SLO generate major version to migrate towards",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Do not ask for user input and auto-generate config keys",
)
def migrate(**kwargs):
    """Migrate SLO configs from v1 to v2."""
    migrator.do_migrate(**kwargs)
