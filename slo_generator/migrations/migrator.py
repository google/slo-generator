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
# pylint: disable=line-too-long, too-many-statements, too-many-ancestors, too-many-locals, too-many-nested-blocks, unused-argument
# flake8: noqa
# pytype: skip-file
import copy
import itertools
import pprint
import random
import string
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Optional

import click
from ruamel import yaml

from slo_generator import utils
from slo_generator.constants import (
    BOLD,
    CONFIG_SCHEMA,
    ENDC,
    FAIL,
    GREEN,
    METRIC_LABELS_COMPAT,
    METRIC_METADATA_LABELS_TOP_COMPAT,
    PROVIDERS_COMPAT,
    RED,
    RIGHT_ARROW,
    SLO_CONFIG_SCHEMA,
    SUCCESS,
    WARNING,
)

yaml.explicit_start = True  # type: ignore[attr-defined]
yaml.default_flow_style = None  # type: ignore[attr-defined]
yaml.preserve_quotes = True  # type: ignore[attr-defined]


# pylint: disable=too-many-arguments
def do_migrate(
    source,
    target,
    error_budget_policy_path: list,
    exporters_path: list,
    version: str,
    quiet: bool = False,
    verbose: int = 0,
):
    """Process all SLO configs in folder and generate new SLO configurations.

    Args:
        source (str): Source SLO configs folder.
        target (str): Target SLO configs folder.
        error_budget_policy_path (list): Error budget policy paths.
        exporters_path (list): Exporters paths.
        glob (str): Glob expression to add to source path.
        version (str): slo-generator major version string (e.g: v1, v2, ...)
        quiet (bool, optional): If true, do not prompt for user input.
        verbose (int, optional): Verbose level.
    """
    curver: str = "v1"
    shared_config = CONFIG_SCHEMA
    cwd = Path.cwd()
    source = Path(source).resolve()
    target = Path(target).resolve()
    source_str = source.relative_to(cwd)  # human-readable path
    target_str = target.relative_to(cwd)  # human-readable path
    ebp_paths = [Path(ebp) for ebp in error_budget_policy_path]
    exporters_paths = [Path(exp) for exp in exporters_path]

    # Create target folder if it doesn't exist
    target.mkdir(parents=True, exist_ok=True)

    # Translate error budget policy to v2 and put into shared config
    if ebp_paths:
        ebp_func = getattr(sys.modules[__name__], f"ebp_{curver}to{version}")
        ebp_func(
            ebp_paths,
            shared_config=shared_config,
            quiet=quiet,
        )

    # Translate exporters to v2 and put into shared config
    if exporters_paths:
        exporters_func = getattr(
            sys.modules[__name__], f"exporters_{curver}to{version}"
        )
        exp_keys = exporters_func(
            exporters_paths,
            shared_config=shared_config,
            quiet=quiet,
        )

    # Process SLO configs
    click.secho("=" * 50)
    click.secho(
        f"Migrating slo-generator configs to {version} ...", fg="cyan", bold=True
    )
    paths = utils.get_files(source)
    if not paths:
        click.secho(f"{FAIL} No SLO configs found in {source}", fg="red", bold=True)
        sys.exit(1)

    curver = ""
    for source_path in paths:
        if source_path in ebp_paths + exporters_paths:
            continue
        source_path_str = source_path.relative_to(cwd)
        target_path = utils.get_target_path(
            source,
            target,
            source_path,
            mkdir=True,
        )
        target_path_str = target_path.resolve().relative_to(cwd)
        slo_config_str = source_path.open().read()
        slo_config, ind, blc = yaml.util.load_yaml_guess_indent(slo_config_str)
        curver = detect_config_version(slo_config)
        if not curver:
            continue

        # Source path info
        click.secho("-" * 50)
        click.secho(f"{WARNING}{source_path_str}{ENDC} [{curver}] ")

        # If config version is same as target version, continue
        if curver == version:
            click.secho(
                f"{FAIL} {source_path_str} is already in {version} format",
                fg="red",
                bold=True,
            )
            continue

        # Create target dirs if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Run vx to vy migrator method
        slo_func = getattr(sys.modules[__name__], f"slo_config_{curver}to{version}")
        slo_config_v2 = slo_func(
            slo_config,
            shared_config=shared_config,
            shared_exporters=exp_keys if exporters_paths else [],
            quiet=quiet,
        )
        if not slo_config_v2:
            continue

        # Write resulting config to target path
        extra = "(replaced)" if target_path_str == source_path_str else ""
        click.secho(f"{RIGHT_ARROW} {GREEN}{target_path_str}{ENDC} [{version}] {extra}")
        with target_path.open("w", encoding="utf8") as conf:
            yaml.round_trip_dump(
                slo_config_v2,
                conf,
                indent=ind,
                block_seq_indent=blc,
                default_flow_style=None,
            )
        click.secho(f"{SUCCESS} Success !", fg="green", bold=True)

    # Write shared config to file
    click.secho("=" * 50)
    shared_config_path = target / "config.yaml"
    shared_config_path_str = shared_config_path.relative_to(cwd)
    with shared_config_path.open("w", encoding="utf8") as conf:
        click.secho(
            f"Writing slo-generator config to {shared_config_path_str} ...",
            fg="cyan",
            bold=True,
        )
        yaml.round_trip_dump(
            shared_config,
            conf,
            Dumper=CustomDumper,
            indent=2,
            block_seq_indent=0,
            explicit_start=True,
        )
        click.secho(f"{SUCCESS} Success !", fg="green", bold=True)

    # Remove error budget policy file
    # click.secho('=' * 50)
    # click.secho(f'Removing {error_budget_policy_path} ...',
    #             fg='cyan',
    #             bold=True)
    # error_budget_policy_path.unlink()
    # click.secho(f'{SUCCESS} Success !', fg='green', bold=True)

    # Print next steps
    relative_ebp_path = ebp_paths[0].relative_to(cwd)
    click.secho("=" * 50)
    click.secho(
        f"\n{SUCCESS} Migration of `slo-generator` configs to v2 completed successfully ! Configs path: {target_str}/.\n",
        fg="green",
        bold=True,
    )
    click.secho("=" * 50)
    click.secho(
        f"{BOLD}PLEASE FOLLOW THE MANUAL STEPS BELOW TO FINISH YOUR MIGRATION:",
        fg="red",
        bold=True,
    )
    click.secho(
        f"""
    1 - Commit the updated SLO configs and your shared SLO config to version control.
    2 - [local/k8s/cloudbuild] Update your slo-generator command:
    {RED}  [-] slo-generator -f {source_str} -b {relative_ebp_path}{ENDC}
    {GREEN}  [+] slo-generator -f {target_str} -c {target_str}/config.yaml{ENDC}
    """
    )
    # 3 - [terraform] Upgrade your `terraform-google-slo` modules:
    # 3.1 - Upgrade the module `version` to 2.0.0.
    # 3.2 - Replace `error_budget_policy` field in your `slo` and `slo-pipeline` modules by `shared_config`
    # 3.3 - Replace `error_budget_policy.yaml` local variable to `config.yaml`


# pylint: disable=dangerous-default-value
def exporters_v1tov2(
    exporters_paths: list, shared_config: dict = {}, quiet: bool = False
) -> list:
    """Translate exporters to v2 and put into shared config.

    Args:
        exporters_path (list): List of exporters file paths.
        shared_config (dict): Shared config to add exporters to.
        quiet (bool): Quiet mode.

    Returns:
        list: List of exporters keys added to shared config.
    """
    exp_keys = []
    for exp_path in exporters_paths:
        with open(exp_path, encoding="utf-8") as conf:
            content = yaml.load(conf, Loader=yaml.SafeLoader)
        exporters = content

        # If exporters file has sections, concatenate all of them
        if isinstance(content, dict):
            exporters = []
            for _, value in content.items():
                exporters.extend(value)

        # If exporter not in general config, add it and add an alias for the
        # exporter. Refer to the alias in the SLO config file.
        for exporter in exporters:
            exporter = OrderedDict(exporter)
            exp_key = add_to_shared_config(
                exporter, shared_config, "exporters", quiet=quiet
            )
            exp_keys.append(exp_key)
    return exp_keys


# pylint: disable=dangerous-default-value
def ebp_v1tov2(ebp_paths: list, shared_config: dict = {}, quiet: bool = False) -> list:
    """Translate error budget policies to v2 and put into shared config

    Args:
        ebp_paths (list): List of error budget policies file paths.
        shared_config (dict): Shared config to add exporters to.
        quiet (bool): Quiet mode.

    Returns:
        list: List of error budget policies keys added to shared config.
    """
    ebp_keys = []
    for ebp_path in ebp_paths:
        with open(ebp_path, encoding="utf-8") as conf:
            error_budget_policy = yaml.load(conf, Loader=yaml.SafeLoader)
        for step in error_budget_policy:
            step["name"] = step.pop("error_budget_policy_step_name")
            step["burn_rate_threshold"] = step.pop("alerting_burn_rate_threshold")
            step["alert"] = step.pop("urgent_notification")
            step["message_alert"] = step.pop("overburned_consequence_message")
            step["message_ok"] = step.pop("achieved_consequence_message")
            step["window"] = step.pop("measurement_window_seconds")

        ebp = {"steps": error_budget_policy}
        if ebp_path.name == "error_budget_policy.yaml":
            ebp_key = "default"
        else:
            ebp_key = ebp_path.stem.replace("error_budget_policy_", "")
        ebp_key = add_to_shared_config(
            ebp,
            shared_config,
            "error_budget_policies",
            ebp_key,
            quiet=quiet,
        )
        ebp_keys.append(ebp_key)
    return ebp_keys


# pylint: disable=dangerous-default-value
def slo_config_v1tov2(
    slo_config: dict,
    shared_config: dict = {},
    shared_exporters: list = [],
    quiet: bool = False,
    verbose: int = 0,
):
    """Process old SLO config v1 and generate SLO config v2.

    Args:
        slo_config (dict): SLO Config v1.
        shared_config (dict): SLO Generator config.
        shared_exporters (list): Shared exporters keys to add to SLO configs.
        quiet (bool): If true, do not ask for user input.
        verbose (int): Verbose level.

    Returns:
        dict: SLO Config v2.
    """
    # SLO config v2 skeleton
    slo_config_v2 = OrderedDict(copy.deepcopy(SLO_CONFIG_SCHEMA))
    slo_config_v2["apiVersion"] = "sre.google.com/v2"
    slo_config_v2["kind"] = "ServiceLevelObjective"
    missing_keys = [
        key
        for key in ["service_name", "feature_name", "slo_name", "backend"]
        if key not in slo_config
    ]
    if missing_keys:
        click.secho(
            f"Invalid SLO configuration: missing key(s) {missing_keys}.", fg="red"
        )
        return None

    # Get fields from old config
    slo_metadata_name_fmt = "{service_name}-{feature_name}-{slo_name}"
    slo_metadata_name = slo_metadata_name_fmt.format(**slo_config)
    slo_description = slo_config.pop("slo_description")
    slo_target = slo_config.pop("slo_target")
    service_level_indicator = slo_config["backend"].pop("measurement", {})
    backend = slo_config["backend"]
    method = backend.pop("method")
    exporters = slo_config.get("exporters", [])
    if isinstance(exporters, dict):  # single exporter, deprecated
        exporters = [exporters]

    # Fill spec
    slo_config_v2["metadata"]["name"] = slo_metadata_name
    slo_config_v2["metadata"]["labels"] = {
        "service_name": slo_config["service_name"],
        "feature_name": slo_config["feature_name"],
        "slo_name": slo_config["slo_name"],
    }
    other_labels = {
        k: v
        for k, v in slo_config.items()
        if k not in ["service_name", "feature_name", "slo_name", "backend", "exporters"]
    }
    slo_config_v2["metadata"]["labels"].update(other_labels)
    slo_config_v2["spec"]["description"] = slo_description
    slo_config_v2["spec"]["goal"] = slo_target

    # Process backend
    backend = OrderedDict(backend)
    backend_key = add_to_shared_config(
        backend,
        shared_config,
        "backends",
        quiet=quiet,
    )
    slo_config_v2["spec"]["backend"] = backend_key
    slo_config_v2["spec"]["method"] = method

    # If exporter not in general config, add it and add an alias for the
    # exporter. Refer to the alias in the SLO config file.
    for exporter in exporters:
        exporter = OrderedDict(exporter)
        exp_key = add_to_shared_config(
            exporter, shared_config, "exporters", quiet=quiet
        )
        slo_config_v2["spec"]["exporters"].append(exp_key)

    # Add shared exporters to slo config
    for exp_key in shared_exporters:
        slo_config_v2["spec"]["exporters"].append(exp_key)

    # Fill spec
    slo_config_v2["spec"]["service_level_indicator"] = service_level_indicator

    if verbose > 0:
        pprint.pprint(dict(slo_config_v2))
    return dict(slo_config_v2)


def report_v2tov1(report: dict) -> dict:
    """Convert SLO report from v2 to v1 format, for exporters to be
    backward-compatible with v1 data format.

    Args:
        report (dict): SLO report.

    Returns:
        dict: Converted SLO report.
    """
    mapped_report: dict = {}
    for key, value in report.items():
        # If a metadata label is passed, use the metadata label mapping
        if key == "metadata":
            mapped_report["metadata"] = {}
            for subkey, subvalue in value.items():
                # v2 `metadata.labels` attributes map to `metadata` attributes
                # in v1
                if subkey == "labels":
                    labels = subvalue
                    for labelkey, labelval in labels.items():
                        # Top-level labels like 'service_name', 'feature_name',
                        # and 'slo_name'.
                        if labelkey in METRIC_METADATA_LABELS_TOP_COMPAT:
                            mapped_report[labelkey] = labelval

                        # Other labels that are mapped to 'metadata' in the v1
                        # report
                        else:
                            mapped_report["metadata"][labelkey] = labelval

                # ignore the name attribute which is just a concatenation of
                # service_name, feature_name and slo_name
                elif subkey == "name":
                    continue

                # other metadata labels are still mapped to the v1 `metadata`
                # attributes
                else:
                    mapped_report["metadata"][subkey] = subvalue

        # If a key in the default label mapping is passed, use the default
        # label mapping
        elif key in METRIC_LABELS_COMPAT:
            mapped_report[METRIC_LABELS_COMPAT[key]] = value
        else:
            mapped_report[key] = value
    return mapped_report


def get_random_suffix() -> str:
    """Get random suffix for our backends / exporters when configs clash."""
    return "".join(random.choices(string.digits, k=4))  # nosec B311


def add_to_shared_config(
    new_obj: dict, shared_config: dict, section: str, key=None, quiet: bool = False
):
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
        key (str): Key if cannot be infered.
        quiet (bool): If True, do not ask for user input.

    Returns:
        str: Object key in the shared config.
    """
    shared_obj = shared_config[section]
    key = key or new_obj.pop("class", None)
    if not key:
        raise ValueError("Object key is undefined.")
    if "." not in key:
        key = utils.caml_to_snake(PROVIDERS_COMPAT.get(key, key))

    existing_obj = {
        k: v
        for k, v in shared_obj.items()
        if k.startswith(key.split("/")[0]) and str(v) == str(dict(new_obj))
    }
    if existing_obj:
        key = next(iter(existing_obj))
        # click.secho(f'Found existing {section} {key}')
    else:
        if key in shared_obj.keys():  # key conflicts
            if quiet:
                key += "/" + get_random_suffix()
            else:
                name = section.rstrip("s")
                cfg = pprint.pformat({key: dict(new_obj)})
                valid = False
                while not valid:
                    click.secho(
                        f"\nNew {name} found with the following config:\n{cfg}",
                        fg="cyan",
                        blink=True,
                    )
                    user_input = click.prompt(
                        f"\n{RED}{BOLD}Please give this {name} a name{ENDC}", type=str
                    )
                    former_key = key
                    key += "/" + user_input.lower()
                    if key in shared_obj.keys():
                        click.secho(
                            f'{name.capitalize()} "{key}" already exists in shared config',
                            fg="red",
                            bold=True,
                        )
                        key = former_key
                    else:
                        valid = True
                click.secho(
                    f"Backend {key} was added to shared config.", fg="green", bold=True
                )

        # click.secho(f"Adding new {section} {key}")
        shared_obj[key] = dict(new_obj)
        shared_config[section] = dict(sorted(shared_obj.items()))
    return key


def detect_config_version(config: dict) -> str:
    """Return version of an slo-generator config based on the format.

    Args:
        config (dict): slo-generator configuration.

    Returns:
        str: SLO config version.
    """
    if not isinstance(config, dict):
        click.secho(
            "Config does not correspond to any known SLO config versions.", fg="red"
        )
        return None
    api_version: str = config.get("apiVersion", "")
    kind = config.get("kind", "")
    if not kind:  # old v1 format
        return "v1"
    return api_version.split("/")[-1]


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


# pylint: disable=too-few-public-methods
class CustomDumper(yaml.RoundTripDumper):
    """Dedicated YAML dumper to insert lines between top-level objects.

    Args:
        data (str): Line data.
    """

    # HACK: insert blank lines between top-level objects
    # inspired by https://stackoverflow.com/a/44284819/3786245
    # pylint: disable=missing-function-docstring
    def write_line_break(self, data: Optional[str] = None):
        super().write_line_break(data)

        if len(self.indents) == 1:
            super().write_line_break()
