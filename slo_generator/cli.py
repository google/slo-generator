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
import pprint
import time
from pathlib import Path

import click
from slo_generator import utils
from slo_generator.compute import compute

sys.path.append(os.getcwd())  # dynamic backend loading

LOGGER = logging.getLogger(__name__)


@click.command()
@click.option('--slo-config',
              '-f',
              type=click.Path(),
              required=True,
              help='SLO config path')
@click.option('--config',
              '-c',
              type=click.Path(exists=True),
              default='config.yaml',
              show_default=True,
              help='slo-generator config path')
@click.option('--export',
              '-e',
              is_flag=True,
              help='Export SLO reports to exporters defined in SLO config')
@click.option('--delete',
              '-d',
              is_flag=True,
              help='Delete SLO (used for backends with SLO APIs)')
@click.option('--timestamp',
              '-t',
              type=int,
              default=None,
              help='End timestamp for query.')
def main(**kwargs):
    """slo-generator CLI entrypoint.

    Args:
        kwargs (Namespace): Click CLI options.

    Returns:
        dict: Dict of all reports indexed by config file path.
    """
    utils.setup_logging()
    LOGGER.debug(f'CLI Options: {pprint.pformat(kwargs)}')
    export = kwargs['export']
    delete = kwargs['delete']
    timestamp = kwargs['timestamp']
    slo_path = kwargs['slo_config']
    config_path = kwargs['config']
    start = time.time()

    # Load slo-generator config
    LOGGER.debug(f"Loading slo-generator config from {config_path}")
    config = utils.load_config(config_path)

    # Load SLO config(s)
    if Path(slo_path).is_dir():
        slo_configs = utils.load_configs(slo_path)
    else:
        slo_configs = [utils.load_config(slo_path)]

    if not slo_configs:
        LOGGER.error(f'No SLO configs found in {slo_path}.')
        sys.exit(1)

    # Load SLO configs and compute SLO reports
    all_reports = {}
    for slo_config in slo_configs:
        name = slo_config['metadata']['name']
        reports = compute(slo_config,
                          config,
                          timestamp=timestamp,
                          do_export=export,
                          delete=delete)
        all_reports[name] = reports
    end = time.time()
    duration = round(end - start, 1)
    LOGGER.info(f'Run summary | SLO Configs: {len(slo_configs)} | '
                f'Duration: {duration}s')
    return all_reports


# pylint: disable=import-error,import-outside-toplevel
@click.command()
@click.pass_context
@click.option('--config', envvar='CONFIG_PATH')
def api(ctx, config):
    """Run functions framework programmatically to provide the slo-generator-api
    endpoint."""
    from functions_framework._cli import _cli
    os.environ['CONFIG_PATH'] = config
    ctx.invoke(_cli,
               target='run_compute',
               source=Path(__file__).parent / 'api' / 'main.py',
               signature_type='cloudevent')


if __name__ == '__main__':
    main()
