"""
`v1tov2.py`
Migrate utilities for migrating slo-generator configs from v1 to v2.
"""
import sys
import os
from collections import OrderedDict

import ruamel.yaml as yaml

from slo_generator import utils

DEFAULT_SHARED_CONFIG = {
    'backends': [],
    'exporters': [],
    'error_budget_policies': [],
}

GREEN = utils.Colors.OKGREEN
RED = utils.Colors.FAIL
ENDC = utils.Colors.ENDC
BOLD = utils.Colors.BOLD
WARNING = utils.Colors.WARNING

# Fields that have changed name with v2 YAML config format. This mapping helps
# migrate them back to their former name, so that exporters are backward-
# compatible with v1.
LABELS_MAPPING = {
    'goal': 'slo_target',
    'description': 'slo_description',
    'burn_rate_threshold': 'alerting_burn_rate_threshold'
}

# Fields that used to be specified in top-level of YAML config are now specified
# in metadata fields. This mapping helps migrate them back to the top level when
# exporting reports, so that so that exporters are backward-compatible with v1.
METADATA_LABELS_TOP_LEVEL = ['service_name', 'feature_name', 'slo_name']


def migrate_slo_report_v1_to_v2(report):
    """Convert SLO report to v1 format, for exporters to be backward-compatible
    with v1 data format.

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
                if subkey in METADATA_LABELS_TOP_LEVEL:
                    mapped_report[subkey] = subvalue
                else:
                    mapped_report['metadata'][subkey] = subvalue

        # If a key in the default label mapping is passed, use the default
        # label mapping
        elif key in LABELS_MAPPING.keys():
            mapped_report.update({LABELS_MAPPING[key]: value})

        # Otherwise, write the label as is
        else:
            mapped_report.update({key: value})
    return mapped_report


def migrate_slo_config_v1_to_v2(slo_config, shared_config={}):
    """Process old SLO config v1 and generate SLO config v2.

    Args:
        slo_config (dict): SLO Config v1.
        shared_config (dict): SLO Generator config.

    Returns:
        dict: SLO Config v2.
    """
    # New slo config skeleton
    slo_config_v2 = OrderedDict({
        'apiVersion': 'cloud.google.com/v1',
        'kind': 'ServiceLevelObjectives',
        'metadata': {},
        'spec': {
            'backend': '',
            'method': '',
            'exporters': [],
            'serviceLevelIndicator': {}
        }
    })

    # print("OLD CONFIG")
    # pprint.pprint(slo_config)
    # print("-" * 50)

    # Get fields from old config
    slo_metadata_name = '{service_name}-{feature_name}-{slo_name}'.format(
        **slo_config)
    slo_description = slo_config.pop('slo_description')
    service_level_indicator = slo_config['backend'].pop('measurement')
    backend = slo_config['backend']
    method = backend.pop('method')
    exporters = slo_config.get('exporters', [])

    # If backend not in general config, add it and add an alias for the backend
    # Refer to the alias in the SLO config file.
    backend = OrderedDict(backend)
    backend_name = utils.dict_snake_to_caml(backend['class']).replace(
        '_', '-').lower()
    backend['name'] = backend_name
    backend.move_to_end('name', last=False)
    backend = dict(backend)
    slo_config_v2['spec']['backend'] = backend_name
    backends = shared_config['backends']
    if not any([str(b) == str(backend) for b in backends]):
        backends.append(backend)
        shared_config['backends'] = backends

    # If exporter not in general config, add it and add an alias for the
    # exporter. Refer to the alias in the SLO config file.
    for exporter in exporters:
        exporter = OrderedDict(exporter)
        exporter_name = utils.dict_snake_to_caml(exporter['class']).replace(
            '_', '-').lower()
        exporter['name'] = exporter_name
        exporter.move_to_end('name', last=False)
        exporter = dict(exporter)
        if exporter_name not in slo_config_v2['spec']['exporters']:
            slo_config_v2['spec']['exporters'].append(exporter_name)
        exporters = shared_config['exporters']
        if not any([str(d) == str(exporter) for d in exporters]):
            exporters.append(exporter)
            shared_config['exporters'] = exporters

    # Fill spec.serviceLevelIndicator and spec.backend/method
    slo_config_v2['spec']['description'] = slo_description
    slo_config_v2['spec']['method'] = method
    slo_config_v2['spec']['serviceLevelIndicator'] = service_level_indicator

    # Fill metadata.name
    slo_config_v2['metadata']['name'] = slo_metadata_name

    # Fill labels
    slo_config_v2['metadata']['labels'] = {
        'service': slo_config['service_name'],
        'feature': slo_config['feature_name'],
        'slo_name': slo_config['slo_name']
    }

    # print("NEW CONFIG")
    # pprint.pprint(slo_config_v2)
    # print("-" * 50)
    return dict(slo_config_v2)


def process_all():
    shared_config = DEFAULT_SHARED_CONFIG

    if len(sys.argv) < 2:
        print(
            "Usage: python v1tov2.py <SLO_FOLDER_PATH> <ERROR_BUDGET_POLICY_PATH> (<TARGET_FOLDER>)"
        )
        sys.exit(1)

    source_folder = sys.argv[1]

    if len(sys.argv) < 3:
        error_budget_policy_path = 'error_budget_policy.yaml'
    else:
        error_budget_policy_path = sys.argv[2]

    if len(sys.argv) < 4:
        target_folder = 'v2'
    else:
        target_folder = sys.argv[3]

    # Create target folder if it doesn't exist
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    # Process SLO configs
    print(f'{BOLD}{WARNING}slo-generator migration to v2 started ...{ENDC}')
    paths = utils.list_slo_configs(source_folder)
    target_dir = os.path.abspath(target_folder)
    # print(f"Source SLO configs directory: {os.path.abspath(source_folder)}")
    # print(f"Target SLO configs directory: {target_dir}")
    yaml.explicit_start = True
    yaml.default_flow_style = None
    for path in paths:
        print("-" * 50)
        print(f"{RED}{os.path.relpath(path, source_folder)}{ENDC} [v1]", end='')
        source_dir = os.path.dirname(path)
        target_path = path.replace(source_dir, target_dir)
        slo_config_str = open(path).read()
        slo_config, indent, block_seq_indent = yaml.util.load_yaml_guess_indent(
            slo_config_str, preserve_quotes=False)
        slo_config_v2 = migrate_slo_config_v1_to_v2(slo_config, shared_config)
        slo_config_v2 = utils.dict_snake_to_caml(slo_config_v2)
        print(" \u2192 ", end='')
        print(f"{GREEN}{os.path.relpath(target_path, source_dir)}{ENDC} [v2]",
              end='')
        with open(target_path, 'w') as f:
            yaml.round_trip_dump(slo_config_v2,
                                 f,
                                 indent=2,
                                 block_seq_indent=2,
                                 default_flow_style=None)
        print(f'\n{GREEN}{BOLD}Success !{ENDC}')

    # Process error budget policy
    # Add it to shared SLO generator config
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
    target_path = f'{target_dir}/config.yaml'
    target_path_human = os.path.relpath(target_path, source_dir)
    source_path_slo_human = os.path.relpath(source_dir, source_dir)
    target_path_slo_human = os.path.relpath(target_dir, source_dir)
    with open(target_path, 'w') as f:
        print("-" * 50)
        print(f"{BOLD}Writing shared config v2 to {target_path_human}{ENDC}")
        yaml.round_trip_dump(shared_config,
                             f,
                             Dumper=MyDumper,
                             indent=2,
                             block_seq_indent=0,
                             explicit_start=True)
        print(f'{GREEN}{BOLD}Success !{ENDC}')

    print("-" * 50)
    print(
        f'{GREEN}{BOLD}Migration of `slo-generator` configs to v2 completed successfully ! Configs path: {target_path_slo_human}/.{ENDC}'
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
        f'{RED}  [-] slo-generator -f {source_path_slo_human} -b {error_budget_policy_path}{ENDC}'
    )
    print(
        f'{GREEN}  [+] slo-generator -f {target_path_slo_human} -c {target_path_slo_human}/config.yaml{ENDC}'
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


class MyDumper(yaml.RoundTripDumper):
    # HACK: insert blank lines between top-level objects
    # inspired by https://stackoverflow.com/a/44284819/3786245
    def write_line_break(self, data=None):
        super().write_line_break(data)

        if len(self.indents) == 1:
            super().write_line_break()


if __name__ == "__main__":
    process_all()
