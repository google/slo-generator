# Copyright 2021 Google Inc.
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
`v1tov2.py`
Migrate utilities for migrating slo-generator configs from v1 to v2.
"""
# pylint: disable=line-too-long, too-many-statements, too-many-ancestors
# flake8: noqa
import copy
import click
import itertools
import pprint
import random
import string
import sys
from collections import OrderedDict
from pathlib import Path

import ruamel.yaml as yaml

from slo_generator import utils
from slo_generator.constants import (METRIC_LABELS_COMPAT,
                                     METRIC_LABELS_TOP_COMPAT, PROVIDERS_COMPAT,
                                     CONFIG_SCHEMA, SLO_CONFIG_SCHEMA, GREEN,
                                     RED, BOLD, WARNING, ENDC, SUCCESS, FAIL,
                                     RIGHT_ARROW)

yaml.explicit_start = True
yaml.default_flow_style = None
yaml.preserve_quotes = True


def do_migrate(source,
               target,
               error_budget_policy_path,
               glob,
               version,
               quiet=False,
               verbose=0):
    """Process all SLO configs in folder and generate new SLO configurations.

    Args:
        source (str): Source SLO configs folder.
        target (str): Target SLO configs folder.
        error_budget_policy_path (str): Error budget policy path.
        glob (str): Glob expression to add to source path.
        version (str): slo-generator major version string (e.g: v1, v2, ...)
        quiet (bool, optional): If true, do not prompt for user input.
        verbose (int, optional): Verbose level.
    """
    shared_config = CONFIG_SCHEMA
    cwd = Path.cwd()
    source = Path(source).resolve()
    target = Path(target).resolve()
    source_str = source.relative_to(cwd)  # human-readable path
    target_str = target.relative_to(cwd)  # human-readable path
    error_budget_policy_path = Path(error_budget_policy_path)

    # Create target folder if it doesn't exist
    target.mkdir(parents=True, exist_ok=True)

    # Process SLO configs
    click.secho('=' * 50)
    click.secho(f"Migrating slo-generator configs to {version} ...",
                fg='cyan',
                bold=True)

    paths = Path(source).glob(glob)

    if not peek(paths):
        click.secho(f"{FAIL} No SLO configs found in {source}",
                    fg='red',
                    bold=True)
        sys.exit(1)

    for source_path in paths:
        source_path_str = source_path.relative_to(cwd)
        if source == target == cwd:
            target_path = target.joinpath(*source_path.relative_to(cwd).parts)
        else:
            target_path = target.joinpath(
                *source_path.relative_to(cwd).parts[1:])
        target_path_str = target_path.relative_to(cwd)
        slo_config_str = source_path.open().read()
        slo_config, ind, blc = yaml.util.load_yaml_guess_indent(slo_config_str)
        curver = get_config_version(slo_config)

        # Source path info
        click.secho("-" * 50)
        click.secho(f"{WARNING}{source_path_str}{ENDC} [{curver}] ")

        # If config version is same as target version, continue
        if curver == version:
            click.secho(
                f'{FAIL} {source_path_str} is already in {version} format',
                fg='red',
                bold=True)
            continue

        # Create target dirs if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Run vx to vy migrator method
        func = getattr(sys.modules[__name__], f"slo_config_{curver}to{version}")
        slo_config_v2 = func(slo_config, shared_config, quiet=quiet)

        # Write resulting config to target path
        extra = '(replaced)' if target_path_str == source_path_str else ''
        click.secho(
            f"{RIGHT_ARROW} {GREEN}{target_path_str}{ENDC} [{version}] {extra}")
        with target_path.open('w') as conf:
            yaml.round_trip_dump(
                slo_config_v2,
                conf,
                indent=ind,
                block_seq_indent=blc,
                default_flow_style=None,
            )
        click.secho(f'{SUCCESS} Success !', fg='green', bold=True)

    # Translate error budget policy to v2 and put into shared config
    error_budget_policy = yaml.load(open(error_budget_policy_path),
                                    Loader=yaml.Loader)
    for step in error_budget_policy:
        step['name'] = step.pop('error_budget_policy_step_name')
        step['burn_rate_threshold'] = step.pop('alerting_burn_rate_threshold')
        step['alert'] = step.pop('urgent_notification')
        step['message_alert'] = step.pop('overburned_consequence_message')
        step['message_standard'] = step.pop('achieved_consequence_message')

    ebp = {'steps': error_budget_policy}
    if error_budget_policy_path.name == 'error_budget_policy.yaml':
        ebp_key = 'default'
    else:
        ebp_key = error_budget_policy_path.name
    shared_config['error_budget_policies'][ebp_key] = ebp
    shared_config_path = target / 'config.yaml'
    shared_config_path_str = shared_config_path.relative_to(cwd)

    # Write shared config to file
    click.secho('=' * 50)
    with shared_config_path.open('w') as conf:
        click.secho(
            f'Writing slo-generator config to {shared_config_path_str} ...',
            fg='cyan',
            bold=True)
        yaml.round_trip_dump(
            shared_config,
            conf,
            Dumper=CustomDumper,
            indent=2,
            block_seq_indent=0,
            explicit_start=True,
        )
        click.secho(f'{SUCCESS} Success !', fg='green', bold=True)

    # Remove error budget policy file
    click.secho('=' * 50)
    click.secho(f'Removing {error_budget_policy_path} ...',
                fg='cyan',
                bold=True)
    error_budget_policy_path.unlink()
    click.secho(f'{SUCCESS} Success !', fg='green', bold=True)

    # Print next steps
    click.secho('=' * 50)
    click.secho(
        f'\n{SUCCESS} Migration of `slo-generator` configs to v2 completed successfully ! Configs path: {target_str}/.\n',
        fg='green',
        bold=True)
    click.secho('=' * 50)
    click.secho(
        f'{BOLD}PLEASE FOLLOW THE MANUAL STEPS BELOW TO FINISH YOUR MIGRATION:',
        fg='red',
        bold=True)
    click.secho(f"""
    1 - Commit the updated SLO configs and your shared SLO config to version control.
    2 - [local/k8s/cloudbuild] Update your slo-generator command:
    {RED}  [-] slo-generator -f {source_str} -b {error_budget_policy_path}{ENDC}
    {GREEN}  [+] slo-generator -f {target_str} -c {target_str}/config.yaml{ENDC}
    3 - [terraform] Upgrade your `terraform-google-slo` modules:
    3.1 - Upgrade the module `version` to 2.0.0.
    3.2 - Replace `error_budget_policy` field in your `slo` and `slo-pipeline` modules by `shared_config`
    3.3 - Replace `error_budget_policy.yaml` local variable to `config.yaml`
    """)


def slo_config_v1tov2(slo_config, shared_config={}, quiet=False, verbose=0):
    """Process old SLO config v1 and generate SLO config v2.

    Args:
        slo_config (dict): SLO Config v1.
        shared_config (dict): SLO Generator config.
        quiet (bool): If true, do not ask for user input.
        verbose (int): Verbose level.

    Returns:
        dict: SLO Config v2.
    """
    # SLO config v2 skeleton
    slo_config_v2 = OrderedDict(copy.deepcopy(SLO_CONFIG_SCHEMA))
    slo_config_v2['apiVersion'] = 'sre.google.com/v2'
    slo_config_v2['kind'] = 'ServiceLevelObjective'

    # Get fields from old config
    slo_metadata_name = '{service_name}-{feature_name}-{slo_name}'.format(
        **slo_config)
    slo_description = slo_config.pop('slo_description')
    service_level_indicator = slo_config['backend'].pop('measurement', {})
    backend = slo_config['backend']
    method = backend.pop('method')
    exporters = slo_config.get('exporters', [])

    # Process backend
    backend = OrderedDict(backend)
    backend_key = add_to_shared_config(backend,
                                       shared_config,
                                       'backends',
                                       quiet=quiet)
    slo_config_v2['spec']['backend'] = backend_key

    # If exporter not in general config, add it and add an alias for the
    # exporter. Refer to the alias in the SLO config file.
    for exporter in exporters:
        exporter = OrderedDict(exporter)
        exp_key = add_to_shared_config(exporter,
                                       shared_config,
                                       'exporters',
                                       quiet=quiet)
        slo_config_v2['spec']['exporters'].append(exp_key)

    # Fill spec.serviceLevelIndicator and spec.backend/method
    slo_config_v2['spec']['description'] = slo_description
    slo_config_v2['spec']['method'] = method
    slo_config_v2['spec']['service_level_indicator'] = service_level_indicator

    # Fill metadata.name
    slo_config_v2['metadata']['name'] = slo_metadata_name

    # Fill metadata labels
    slo_config_v2['metadata']['labels'] = {
        'service': slo_config['service_name'],
        'feature': slo_config['feature_name'],
        'slo_name': slo_config['slo_name'],
    }
    if verbose > 0:
        pprint.pprint(dict(slo_config_v2))
    return dict(slo_config_v2)


def report_v2tov1(report):
    """Convert SLO report from v2 to v1 format, for exporters to be
    backward-compatible with v1 data format.

    Args:
        report (dict): SLO report.

    Returns:
        dict: Converted SLO report.
    """
    mapped_report = {}
    for key, value in report.items():

        # If a metadata label is passed, use the metadata label mapping
        if key == 'metadata':
            mapped_report['metadata'] = {}
            for subkey, subvalue in value['labels'].items():
                if subkey in METRIC_LABELS_TOP_COMPAT:
                    mapped_report[subkey] = subvalue
                else:
                    mapped_report['metadata'][subkey] = subvalue

        # If a key in the default label mapping is passed, use the default
        # label mapping
        elif key in METRIC_LABELS_COMPAT.keys():
            mapped_report.update({METRIC_LABELS_COMPAT[key]: value})

        # Otherwise, write the label as is
        else:
            mapped_report.update({key: value})
    return mapped_report


def get_random_suffix():
    """Get random suffix for our backends / exporters when configs clash."""
    return ''.join(random.choices(string.digits, k=4))


def add_to_shared_config(new_obj, shared_config, section, quiet=False):
    """Add an object to the shared_config.

    If the object with the same config already exists in the shared config,
    simply return its key.

    If the object does not exist in the shared config:
    * If the default key is already taken, add a random suffix to it.
    * If the default key is not taken, add the new object to the config.

    Args:
        new_obj (OrderedDict): Object to add to shared_config.
        shared_config (dict): Shared config to add object to.
        section (str): Section name in shared config to add the object under.
        quiet (bool): If True, do not ask for user input.

    Returns:
        str: Object key in the shared config.
    """
    shared_obj = shared_config[section]
    key = new_obj.pop('class')
    if '.' not in key:
        key = utils.caml_to_snake(PROVIDERS_COMPAT.get(key, key))

    existing_obj = {
        k: v
        for k, v in shared_obj.items()
        if k.startswith(key.split('/')[0]) and str(v) == str(dict(new_obj))
    }
    if existing_obj:
        key = next(iter(existing_obj))
        # click.secho(f'Found existing {section} {key}')
    else:
        if key in shared_obj.keys():  # key conflicts
            if quiet:
                key += '/' + get_random_suffix()
            else:
                name = section.rstrip('s')
                cfg = pprint.pformat(dict(new_obj))
                valid = False
                while not valid:
                    click.secho(
                        f'\nNew {name} found with the following config:\n{cfg}',
                        fg='cyan',
                        blink=True)
                    user_input = click.prompt(
                        f'\n{RED}{BOLD}Please give this {name} a name:{ENDC}',
                        type=str)
                    key += '/' + user_input.lower()
                    if key in shared_obj.keys():
                        click.secho(
                            f'{name.capitalize()} "{key}" already exists in shared config',
                            fg='red',
                            bold=True)
                    else:
                        valid = True
                click.secho(f'Backend {key} was added to shared config.',
                            fg='green',
                            bold=True)

        # click.secho(f"Adding new {section} {key}")
        shared_obj[key] = dict(new_obj)
        shared_config[section] = dict(sorted(shared_obj.items()))
    return key


def get_config_version(config):
    """Return version of an slo-generator config based on the format.

    Args:
        config (dict): slo-generator configuration.

    Returns:
        str: SLO config version.
    """
    api_version = config.get('apiVersion', '')
    kind = config.get('kind', '')
    if not kind:  # old v1 format
        return 'v1'
    return api_version.split('/')[-1]


def peek(iterable):
    """Check if iterable is empty.

    Args:
        iterable (collections.Iterable): an iterable

    Returns:
        iterable (collections.Iterable): the same iterable, or None if empty.
    """
    try:
        first = next(iterable)
    except StopIteration:
        return None
    return first, itertools.chain([first], iterable)


class CustomDumper(yaml.RoundTripDumper):
    """Dedicated YAML dumper to insert lines between top-level objects.

    Args:
        data (str): Line data.
    """

    # HACK: insert blank lines between top-level objects
    # inspired by https://stackoverflow.com/a/44284819/3786245
    def write_line_break(self, data=None):
        super().write_line_break(data)

        if len(self.indents) == 1:
            super().write_line_break()
