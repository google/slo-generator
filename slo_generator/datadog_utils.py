# Copyright 2026 Google Inc.
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
"""Shared security helpers for Datadog providers."""

from urllib.parse import urlsplit

DEFAULT_API_HOST = "https://api.datadoghq.com"

# Datadog API hosts documented at https://docs.datadoghq.com/api/latest/.
DATADOG_API_HOSTS = frozenset(
    {
        "api.ap1.datadoghq.com",
        "api.ap2.datadoghq.com",
        "api.datadoghq.com",
        "api.datadoghq.eu",
        "api.ddog-gov.com",
        "api.uk1.datadoghq.com",
        "api.us2.ddog-gov.com",
        "api.us3.datadoghq.com",
        "api.us5.datadoghq.com",
    }
)


def validate_api_host(api_host: str) -> str:
    """Validate and normalize a Datadog API endpoint.

    API and application keys are sent to this endpoint, so accepting an
    arbitrary URL would allow configuration writers to redirect credentials.

    Args:
        api_host: Datadog API endpoint.

    Returns:
        str: Normalized HTTPS Datadog API endpoint.

    Raises:
        ValueError: The endpoint is not an official Datadog API host.
    """
    if not isinstance(api_host, str):
        raise ValueError("Datadog api_host must be a string.")

    endpoint = urlsplit(api_host)
    try:
        port = endpoint.port
    except ValueError as exception:
        raise ValueError("Datadog api_host has an invalid port.") from exception

    if (
        endpoint.scheme.lower() != "https"
        or endpoint.hostname not in DATADOG_API_HOSTS
        or endpoint.username is not None
        or endpoint.password is not None
        or port not in (None, 443)
        or endpoint.path not in ("", "/")
        or endpoint.query
        or endpoint.fragment
    ):
        raise ValueError(
            "Datadog api_host must be an official HTTPS Datadog API endpoint."
        )

    return f"https://{endpoint.hostname}"
