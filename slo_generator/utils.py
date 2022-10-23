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
`utils.py`
Utility functions.
"""
import argparse
import errno
import importlib
import logging
import os
import pprint
import re
import sys
import warnings
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from dateutil import tz

from slo_generator.constants import DEBUG

try:
    # pytype: disable=import-error
    from google.cloud import storage  # type: ignore[attr-defined]

    GCS_ENABLED = True
except ImportError:
    GCS_ENABLED = False

LOGGER = logging.getLogger(__name__)


# pylint: disable=dangerous-default-value
def load_configs(
    path: str, ctx: os._Environ = os.environ, kind: Optional[str] = None
) -> list:
    """Load multiple slo-generator configs from a folder path.

    Args:
        path (str): Folder path.
        ctx (dict): Context for variable replacement.
        kind (str): Config kind filter.

    Returns:
        list: List of configs downloaded and parsed.
    """
    configs = [
        load_config(str(p), ctx=ctx, kind=kind)
        for p in sorted(Path(path).glob("*.yaml"))
    ]
    return [cfg for cfg in configs if cfg]


# pylint: disable=dangerous-default-value
def load_config(
    path: str, ctx: os._Environ = os.environ, kind: Optional[str] = None
) -> Optional[dict]:
    """Load any slo-generator config, from a local path, a GCS URL, or directly
    from a string content.

    Args:
        path (str): GCS URL, file path, or data as string.
        ctx (dict): Context for variable replacement.
        kind (str): Config kind filter.

    Returns:
        dict: Config downloaded and parsed.
    """
    abspath = Path(path)
    try:
        if path.startswith("gs://"):
            if not GCS_ENABLED:
                warnings.warn(
                    "To load a file from GCS, you need `google-cloud-storage` "
                    "installed. Please install it using pip by running "
                    "`pip install google-cloud-storage`",
                    ImportWarning,
                )
                sys.exit(1)
            config = parse_config(content=download_gcs_file(str(path)), ctx=ctx)
        elif abspath.is_file():
            config = parse_config(path=str(abspath.resolve()), ctx=ctx)
        else:
            LOGGER.debug(f"Path {path} not found. Trying to load from string")
            config = parse_config(content=str(path), ctx=ctx)

        # Filter on 'kind'
        if kind and (not isinstance(config, dict) or kind != config.get("kind", "")):
            config = None
        return config

    except OSError as exc:
        if exc.errno == errno.ENAMETOOLONG:
            return parse_config(content=str(path), ctx=ctx)
        raise


# pylint: disable=dangerous-default-value
def parse_config(
    path: Optional[str] = None, content=None, ctx: os._Environ = os.environ
):
    """Load a yaml configuration file and resolve environment variables in it.

    Args:
        path (str): the path to the yaml file.
        content (str): the config content as a dict string.
        ctx (dict): Context to replace env variables from (defaults to
            `os.environ`).

    Returns:
        dict: Parsed YAML dictionary.
    """
    pattern = re.compile(r".*?\${(\w+)}.*?")

    def replace_env_vars(content, ctx) -> str:
        """Replace env variables in content from context.

        Args:
            content (str): String to parse.
            ctx (dict): Context to replace vars from.

        Returns:
            str: the parsed string with the env var replaced.
        """
        match = pattern.findall(content)
        if match:
            full_value = content
            for var in match:
                try:
                    full_value = full_value.replace(f"${{{var}}}", ctx[var])
                except KeyError as exception:
                    LOGGER.error(
                        f'Environment variable "{var}" should be set.', exc_info=True
                    )
                    raise exception
            content = full_value
        return content

    if path:
        with Path(path).open(encoding="utf8") as config:
            content = config.read()
    if ctx:
        content = replace_env_vars(content, ctx)
    data = yaml.safe_load(content)
    if isinstance(data, str):
        error = (
            "Error serializing config into dict. This might be due to a syntax "
            "error in the YAML / JSON config file."
        )
        LOGGER.error(error)

    LOGGER.debug(pprint.pformat(data))
    return data


def setup_logging():
    """Setup logging for the CLI."""
    if DEBUG == 1:
        print(f"DEBUG mode is enabled. DEBUG={DEBUG}")
        level = logging.DEBUG
        format_str = "%(name)s - %(levelname)s - %(message)s"
    else:
        level = logging.INFO
        format_str = "%(levelname)s - %(message)s"
    logging.basicConfig(
        stream=sys.stdout, level=level, format=format_str, datefmt="%m/%d/%Y %I:%M:%S"
    )
    logging.getLogger("googleapiclient").setLevel(logging.ERROR)

    # Ignore Cloud SDK warning when using a user instead of service account
    try:
        # pylint: disable=import-outside-toplevel
        from google.auth._default import _CLOUD_SDK_CREDENTIALS_WARNING

        warnings.filterwarnings("ignore", message=_CLOUD_SDK_CREDENTIALS_WARNING)
    except ImportError:
        pass


def get_human_time(timestamp: int, timezone: Optional[str] = None) -> str:
    """Get human-readable timestamp from UNIX UTC timestamp.

    Args:
        timestamp (int): UNIX UTC timestamp.
        timezone (optional): Explicit timezone (e.g: "America/Chicago").

    Returns:
        str: Formatted human-readable date in ISO format (UTC), with
             time zone added.

    Example:
        >>> get_human_time(1565092435, timezone='Europe/Paris')
        >>> 2019-08-06T11:53:55.000000+02:00
        which corresponds to the UTC time appended the timezone format
        to help with display and retrieval of the date localized.
    """
    if timezone is not None:  # get timezone from arg
        to_zone = tz.gettz(timezone)
    else:  # auto-detect locale
        to_zone = tz.tzlocal()
    dt_utc = datetime.utcfromtimestamp(timestamp)
    dt_tz = dt_utc.replace(tzinfo=to_zone)
    timeformat = "%Y-%m-%dT%H:%M:%S.%f%z"
    date_str = datetime.strftime(dt_tz, timeformat)
    core_str = date_str[:-2]
    tz_str = date_str[-2:]
    date_str = f"{core_str}:{tz_str}"
    return date_str


def get_exporters(config: dict, spec: dict) -> list:
    """Get SLO exporters configs from spec and global config.

    Args:
        config (dict): Global config.
        spec (dict): SLO config.

    Returns:
        list: List of dict containing exporters configurations.
    """
    all_exporters = config.get("exporters", {})
    spec_exporters = spec.get("exporters", [])
    exporters = []
    for exporter in spec_exporters:
        if exporter not in all_exporters.keys():
            LOGGER.error(f'Exporter "{exporter}" not found in config.')
            continue
        exporter_data = all_exporters[exporter]
        exporter_data["name"] = exporter
        if "." in exporter:  # support custom exporter
            exporter_data["class"] = exporter
        else:  # core exporter
            exporter_data["class"] = capitalize(snake_to_caml(exporter.split("/")[0]))
        exporters.append(exporter_data)
    return exporters


def get_backend(config: dict, spec: dict):
    """Get SLO backend config from spec and global config.

    Args:
        config (dict): Global config.
        spec (dict): SLO config.

    Returns:
        list: List of dict containing exporters configurations.
    """
    all_backends = config.get("backends", {})
    spec_backend = spec["backend"]
    backend_data = {}
    if spec_backend not in all_backends.keys():
        LOGGER.error(f'Backend "{spec_backend}" not found in config. Exiting.')
        sys.exit(0)
    backend_data = all_backends[spec_backend]
    backend_data["name"] = spec_backend
    if "." in spec_backend:  # custom backend
        backend_data["class"] = spec_backend
    else:  # built-in backend
        backend_data["class"] = capitalize(snake_to_caml(spec_backend.split("/")[0]))
    return backend_data


def get_error_budget_policy(config: dict, spec: dict):
    """Get error budget policy from spec and global config.

    Args:
        config (dict): Global config.
        spec (dict): SLO config.

    Returns:
        list: List of dict containing exporters configurations.
    """
    all_ebp = config.get("error_budget_policies", {})
    spec_ebp = spec.get("error_budget_policy", "default")
    if spec_ebp not in all_ebp.keys():
        LOGGER.error(f'Error budget policy "{spec_ebp}" not found in config. Exiting.')
        sys.exit(0)
    return all_ebp[spec_ebp]


def get_backend_cls(backend: str):
    """Get backend class.

    Args:
        backend (str): Exporter type.

    Returns:
        class: Backend class.
    """
    expected_type = "Backend"
    return import_cls(backend, expected_type)


def get_exporter_cls(exporter: str):
    """Get exporter class.

    Args:
        exporter (str): Backend type.

    Returns:
        class: Exporter class.
    """
    expected_type = "Exporter"
    return import_cls(exporter, expected_type)


def import_cls(cls_name, expected_type):
    """Import class or method dynamically from full name.
    If `cls_name` is not part of the core, try import from local path (plugins).

    Args:
        cls_name: Class name to import.
        expected_type: Type of class expected.

    Returns:
        obj: Imported class or method object.
    """
    # plugin class
    if "." in cls_name:
        package, name = cls_name.rsplit(".", maxsplit=1)
        return import_dynamic(package, name, prefix=expected_type)

    # slo-generator core class
    modules_name = f"{expected_type.lower()}s"
    full_cls_name = f"{cls_name}{expected_type}"
    filename = re.sub(r"(?<!^)(?=[A-Z])", "_", cls_name).lower()
    return import_dynamic(
        f"slo_generator.{modules_name}.{filename}", full_cls_name, prefix=expected_type
    )


def import_dynamic(package: str, name: str, prefix: str = "class"):
    """Import class or method dynamically from package and name.

    Args:
        package: Where the method or class is located in the import path.
        name: Name of method or class.

    Returns:
        obj: Imported class or method object.
    """
    try:
        return getattr(importlib.import_module(package), name)
    except Exception as exception:  # pylint: disable=W0703
        dep = package.split(".")[-1]
        warnings.warn(
            f'{prefix} "{package}.{name}" not found.\nPlease ensure that:\n'
            f"1. Package and class name are valid.\n"
            f"2. Extra dependency {dep} is installed. If not, install it "
            f'locally with "pip install slo-generator[{dep}]" or remotely '
            f'by adding "slo-generator[{dep}]" to your requirements.txt.',
            ImportWarning,
        )
        if DEBUG:
            LOGGER.debug(exception, exc_info=True)
        return None


def capitalize(word: str) -> str:
    """Only capitalize the first letter of a word, even when written in
    CamlCase.

    Args:
        word (str): Input string.

    Returns:
        str: Input string with first letter capitalized.
    """
    return re.sub("([a-zA-Z])", lambda x: x.groups()[0].upper(), word, 1)


def snake_to_caml(word: str) -> str:
    """Convert a string written in snake_case to a string in CamlCase.

    Args:
        word (str): Input string.

    Returns:
        str: Output string.
    """
    return re.sub("_.", lambda x: x.group()[1].upper(), word)


def caml_to_snake(word: str) -> str:
    """Convert a string written in CamlCase to a string written in snake_case.

    Args:
        word (str): Input string.

    Returns:
        str: Output string.
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "_", word).lower()


def dict_snake_to_caml(data: dict) -> dict:
    """Convert dictionary with keys written in snake_case to another one with
    keys written in CamlCase.

    Args:
        data (dict): Input dictionary.

    Returns:
        dict: Output dictionary.
    """
    return apply_func_dict(data, snake_to_caml)


def apply_func_dict(data: dict, func) -> dict:
    """Apply function on a dictionary keys.

    Args:
        data (dict): Input dictionary.

    Returns:
        dict: Output dictionary.
    """
    if isinstance(data, Mapping):
        return {func(k): apply_func_dict(v, func) for k, v in data.items()}
    return data


def str2bool(string: str) -> bool:
    """Convert a string to a boolean.

    Args:
        string (str): String to convert

    Returns:
        bool: Boolean value.

    Raises:
        `argparse.ArgumentTypeError`: IF no acceptable boolean string is found.
    """
    if isinstance(string, bool):
        return string
    if string.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if string.lower() in ("no", "false", "f", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


def download_gcs_file(url: str) -> dict:
    """Download config from GCS.

    Args:
        url: Config URL.

    Returns:
        dict: Loaded configuration.
    """
    client = storage.Client()
    bucket, filepath = decode_gcs_url(url)
    bucket = client.get_bucket(bucket)
    blob = bucket.blob(filepath)
    return blob.download_as_string(client=None).decode("utf-8")


def decode_gcs_url(url: str) -> tuple:
    """Decode GCS URL.

    Args:
        url (str): GCS URL.

    Returns:
        tuple: (bucket_name, file_path)
    """
    split_url = url.split("/")
    bucket_name = split_url[2]
    file_path = "/".join(split_url[3:])
    return (bucket_name, file_path)


# pylint: disable=dangerous-default-value
def get_files(source, extensions=["yaml", "yml", "json"]) -> list:
    """Get all files matching extensions.

    Args:
        extensions (list): List of extensions to match.

    Returns:
        list: List of all files matching extensions relative to source folder.
    """
    all_files: list = []
    for ext in extensions:
        all_files.extend(Path(source).rglob(f"*.{ext}"))
    return all_files


def get_target_path(source_dir, target_dir, relative_path, mkdir: bool = True):
    """Get target file path from a source directory, a target directory and a
    path relative to the source directory.

    Args:
        source_dir (Path): path to source directory.
        target_dir (pathlib.Path): path to target directory.
        relative_path (pathlib.Path): path relative to source directory.
        mkdir (bool): Create directory structure for target path.

    Returns:
        pathlib.Path: path to target file.
    """
    source_dir = source_dir.resolve()
    target_dir = target_dir.resolve()
    relative_path = relative_path.relative_to(source_dir)
    common_path = os.path.commonpath([source_dir, target_dir])
    target_path = common_path / target_dir.relative_to(common_path) / relative_path
    if mkdir:
        target_path.parent.mkdir(parents=True, exist_ok=True)
    return target_path


def fmt_traceback(exc) -> str:
    """Format exception to be human-friendly.

    Args:
        exc (Exception): Exception to format.

    Returns:
        str: Formatted exception.
    """
    return exc.__class__.__name__ + ": " + str(exc).replace("\n", " ")
