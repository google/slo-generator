"""
`v1tov2.py`
Migrate utilities for migrating slo-generator configs from v1 to v2.
"""
# pylint: disable=line-too-long, too-many-statements, too-many-ancestors
# flake8: noqa

import itertools
import os
import sys
from collections import OrderedDict
from pathlib import Path

import ruamel.yaml as yaml

from slo_generator import utils
from slo_generator.constants import (METRIC_LABELS_COMPAT,
                                     METRIC_LABELS_TOP_COMPAT, PROVIDERS_COMPAT,
                                     CONFIG_SCHEMA, SLO_CONFIG_SCHEMA, GREEN,
                                     RED, BOLD, WARNING, ENDC, SUCCESS, FAIL)

yaml.explicit_start = True
yaml.default_flow_style = None
yaml.preserve_quotes = True


def do_migrate(source, target, error_budget_policy_path, glob, version):
    """Process all SLO configs in folder and generate new SLO configurations.

    Args:
        source (str): Source SLO configs folder.
        target (str): Target SLO configs folder.
        error_budget_policy_path (str): Error budget policy path.
        glob (str): Glob expression to add to source path.
        version (str): slo-generator major version string (e.g: v1, v2, ...)
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
    print(
        f'{BOLD}{WARNING}Migrating slo-generator configs to {version} ...{ENDC}'
    )
    paths = Path(source).glob(glob)

    if not peek(paths):
        print(f'{FAIL} {RED}No SLO configs found in {source}')
        sys.exit(1)

    for source_path in paths:
        source_path_str = source_path.relative_to(cwd)
        if source == target == cwd:
            target_path = target.joinpath(*source_path.relative_to(cwd).parts)
        else:
            target_path = target.joinpath(
                *source_path.relative_to(cwd).parts[-1])
        target_path_str = target_path.relative_to(cwd)
        slo_config_str = source_path.open().read()
        slo_config, ind, blc = yaml.util.load_yaml_guess_indent(slo_config_str)
        curver = get_config_version(slo_config)

        # Source path info
        print('-' * 50)
        print(f'{WARNING}{source_path_str}{ENDC} [{curver}]', end='')

        # If config version is same as target version, continue
        if curver == version:
            print(
                f'\n{FAIL} {BOLD}{RED}{source_path_str} is already in {version} format{ENDC}'
            )
            continue

        # Create target dirs if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Run vx to vy migrator method
        func = getattr(sys.modules[__name__], f'slo_config_{curver}to{version}')
        slo_config_v2 = func(slo_config, shared_config)
        slo_config_v2 = utils.dict_snake_to_caml(slo_config_v2)

        # Write resulting config to target path
        print(f' \u2192 {GREEN}{target_path_str}{ENDC} [{version}]', end='')
        with target_path.open('w') as conf:
            yaml.round_trip_dump(slo_config_v2,
                                 conf,
                                 indent=ind,
                                 block_seq_indent=blc,
                                 default_flow_style=None)
        print(f'\n{SUCCESS} {BOLD}{WARNING}Success !{ENDC}')

    # Translate error budget policy to v2 and put into shared config
    error_budget_policy = yaml.load(open(error_budget_policy_path),
                                    Loader=yaml.Loader)
    for step in error_budget_policy:
        step['name'] = step.pop('error_budget_policy_step_name')
        step['burn_rate_threshold'] = step.pop('alerting_burn_rate_threshold')
        step['alert'] = step.pop('urgent_notification')
        step['message_alert'] = step.pop('overburned_consequence_message')
        step['message_standard'] = step.pop('achieved_consequence_message')

    ebp = {'name': 'default', 'steps': error_budget_policy}
    shared_config['error_budget_policies'].append(ebp)
    shared_config = utils.dict_snake_to_caml(shared_config)
    shared_config_path = target / 'config.yaml'
    shared_config_path_str = shared_config_path.relative_to(cwd)
    with shared_config_path.open('w') as conf:
        print("-" * 50)
        print(
            f"{BOLD}{GREEN}Writing slo-generator config to {shared_config_path_str} ...{ENDC}"
        )
        yaml.round_trip_dump(shared_config,
                             conf,
                             Dumper=CustomDumper,
                             indent=2,
                             block_seq_indent=0,
                             explicit_start=True)
        print(f'{SUCCESS} {GREEN}{BOLD}Success !{ENDC}')

    print("-" * 50)
    print(
        f'{SUCCESS} {GREEN}{BOLD}Migration of `slo-generator` configs to v2 completed successfully ! Configs path: {target_str}/.{ENDC}'
    )
    print("-" * 50)
    print(
        f'{BOLD}{RED}Please follow the manual steps below to finish your migration.{ENDC}'
    )
    print("-" * 50)
    print(f'{BOLD}{WARNING}MANUAL STEPS:{ENDC}')

    # Step 1
    print()
    print(
        f'{BOLD}{WARNING}1 - Commit the updated SLO configs and your shared SLO config to version control.{ENDC}'
    )

    # Step 2
    print()
    print(
        f'{BOLD}{WARNING}2 - [local/k8s/cloudbuild] Update your slo-generator command:{ENDC}'
    )
    print(
        f'{RED}  [-] slo-generator -f {source_str} -b {error_budget_policy_path}{ENDC}'
    )
    print(
        f'{GREEN}  [+] slo-generator -f {target_str} -c {target_str}/config.yaml{ENDC}'
    )

    # Step 3
    print()
    print(
        f'{BOLD}{WARNING}3 - [terraform] Upgrade your `terraform-google-slo` modules:{ENDC}'
    )
    print(
        f'  {BOLD}{WARNING}3.1 - Upgrade the module `version` to 2.0.0.{ENDC}')
    print(
        f'  {BOLD}{WARNING}3.2 - Replace `error_budget_policy` field in your `slo` and `slo-pipeline` modules by `shared_config`{ENDC}'
    )
    print(
        f'  {BOLD}{WARNING}3.3 - Replace `error_budget_policy.yaml` local variable to `config.yaml`{ENDC}'
    )


def slo_config_v1tov2(slo_config, shared_config={}):
    """Process old SLO config v1 and generate SLO config v2.

    Args:
        slo_config (dict): SLO Config v1.
        shared_config (dict): SLO Generator config.

    Returns:
        dict: SLO Config v2.
    """
    # SLO config v2 skeleton
    slo_config_v2 = OrderedDict(SLO_CONFIG_SCHEMA)
    slo_config_v2['apiVersion'] = 'sre.google.com/v2'
    slo_config_v2['kind'] = 'ServiceLevelObjective'

    # Get fields from old config
    slo_metadata_name = '{service_name}-{feature_name}-{slo_name}'.format(
        **slo_config)
    slo_description = slo_config.pop('slo_description')
    service_level_indicator = slo_config['backend'].pop('measurement', None)
    backend = slo_config['backend']
    method = backend.pop('method')
    exporters = slo_config.get('exporters', [])

    # If backend not in general config, add it and add an alias for the backend
    # Refer to the alias in the SLO config file.
    backend = OrderedDict(backend)
    backend_name = utils.dict_snake_to_caml(backend['class']).replace(
        '_', '-').lower()
    backend_name = PROVIDERS_COMPAT.get(backend_name, backend_name)
    backend['name'] = backend_name
    backend.move_to_end('name', last=False)
    backend = dict(backend)
    slo_config_v2['spec']['backend'] = backend_name
    backends = shared_config['backends']
    if not any(str(b) == str(backend) for b in backends):
        backends.append(backend)
        shared_config['backends'] = backends

    # If exporter not in general config, add it and add an alias for the
    # exporter. Refer to the alias in the SLO config file.
    for exporter in exporters:
        exporter = OrderedDict(exporter)
        exporter_name = utils.dict_snake_to_caml(exporter['class']).replace(
            '_', '-').lower()
        exporter_name = PROVIDERS_COMPAT.get(exporter_name, exporter_name)
        exporter['name'] = exporter_name
        exporter.move_to_end('name', last=False)
        exporter = dict(exporter)
        if exporter_name not in slo_config_v2['spec']['exporters']:
            slo_config_v2['spec']['exporters'].append(exporter_name)
        exporters = shared_config['exporters']
        if not any(str(d) == str(exporter) for d in exporters):
            exporters.append(exporter)
            shared_config['exporters'] = exporters

    # Fill spec.serviceLevelIndicator and spec.backend/method
    slo_config_v2['spec']['description'] = slo_description
    slo_config_v2['spec']['method'] = method
    if service_level_indicator:
        slo_config_v2['spec']['serviceLevelIndicator'] = service_level_indicator

    # Fill metadata.name
    slo_config_v2['metadata']['name'] = slo_metadata_name

    # Fill labels
    slo_config_v2['metadata']['labels'] = {
        'service': slo_config['service_name'],
        'feature': slo_config['feature_name'],
        'slo_name': slo_config['slo_name']
    }
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


if __name__ == "__main__":
    main()
