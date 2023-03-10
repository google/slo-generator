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
`report.py`
Report utilities.
"""

import logging
from dataclasses import asdict, dataclass, field, fields
from typing import List

from slo_generator import utils
from slo_generator.constants import COLORED_OUTPUT, MIN_VALID_EVENTS, NO_DATA, Colors

LOGGER = logging.getLogger(__name__)


@dataclass(init=False)
class SLOReport:
    """SLO report dataclass. Compute an SLO report out of an SLO config and an
    Error Budget Policy step.

    Args:
        config (dict): SLO configuration.
        backend (dict): Backend configuration.
        step (dict): Error budget policy step configuration.
        timestamp (int): Timestamp.
        client (obj): Existing backend client.
        delete (bool): Backend delete action.
    """

    # pylint: disable=too-many-instance-attributes

    # SLO
    name: str
    description: str
    goal: str
    backend: str

    # SLI
    gap: float

    # Error budget
    error_budget_policy_step_name: str
    error_budget_target: float
    error_budget_measurement: float
    error_budget_burn_rate: float
    error_budget_burn_rate_threshold: float
    error_budget_minutes: float
    error_budget_remaining_minutes: float
    error_minutes: float

    # Data validation
    valid: bool

    # Global (from error budget policy)
    timestamp: int
    timestamp_human: str
    window: int
    alert: bool

    consequence_message: str

    # SLO
    exporters: list = field(default_factory=list)
    error_budget_policy: str = "default"

    # SLI
    sli_measurement: float = 0
    events_count: int = 0
    bad_events_count: int = 0
    good_events_count: int = 0

    # Metadata
    metadata: dict = field(default_factory=dict)

    # Data validation
    errors: List[str] = field(default_factory=list)

    # pylint: disable=too-many-arguments
    def __init__(self, config, backend, step, timestamp, client=None, delete=False):
        # Init dataclass fields from SLO config and Error Budget Policy
        spec = config["spec"]
        self.exporters = []
        self.__set_fields(
            **spec,
            **step,
            lambdas={
                "goal": float,
                "step": int,
                "error_budget_burn_rate_threshold": float,
            },
        )
        # Set other fields
        self.metadata = config["metadata"]
        self.timestamp = int(timestamp)
        self.name = self.metadata["name"]
        self.error_budget_policy_step_name = step["name"]
        self.error_budget_burn_rate_threshold = float(step["burn_rate_threshold"])
        self.timestamp_human = utils.get_human_time(timestamp)
        self.valid = True
        self.errors = []

        # Get backend results
        data = self.run_backend(config, backend, client=client, delete=delete)
        if not self._validate(data):
            self.valid = False
            return

        # Build SLO report
        self.build(step, data)

        # Post validation
        if not self._post_validate():
            self.valid = False

    def build(self, step, data):
        """Compute all data necessary to build the SLO report.

        Args:
            step (dict): Error Budget Policy step configuration.
            data (obj): Backend data.

        See https://landing.google.com/sre/workbook/chapters/implementing-slos/
        for details on the calculations.
        """
        LOGGER.debug(f"{self.info} | SLO report starting ...")

        # SLI, Good count, Bad count, Gap from backend results
        sli, good_count, bad_count = self.get_sli(data)
        gap = sli - self.goal

        # Error Budget calculations
        eb_target = 1 - self.goal
        eb_value = 1 - sli
        eb_remaining_minutes = self.window * gap / 60
        eb_target_minutes = self.window * eb_target / 60
        eb_minutes = self.window * eb_value / 60
        if eb_target == 0:
            eb_burn_rate = 0
        else:
            eb_burn_rate = round(eb_value / eb_target, 1)

        # Alert boolean on burn rate excessive speed.
        alert = eb_burn_rate > self.error_budget_burn_rate_threshold

        # Manage alerting message.
        if alert:
            consequence_message = step["message_alert"]
        elif eb_burn_rate <= 1:
            consequence_message = step["message_ok"]
        else:
            consequence_message = (
                "Missed for this measurement window, but not enough to alert"
            )

        # Set fields in dataclass.
        self.__set_fields(
            sli_measurement=sli,
            good_events_count=int(good_count),
            bad_events_count=int(bad_count),
            events_count=int(good_count + bad_count),
            gap=gap,
            error_budget_target=eb_target,
            error_budget_measurement=eb_value,
            error_budget_burn_rate=eb_burn_rate,
            error_budget_remaining_minutes=eb_remaining_minutes,
            error_budget_minutes=eb_target_minutes,
            error_minutes=eb_minutes,
            alert=alert,
            consequence_message=consequence_message,
        )

    def run_backend(self, config, backend, client=None, delete=False):
        """Get appropriate backend method from SLO configuration and run it on
        current SLO config and Error Budget Policy step.

        Args:
            config (dict): SLO configuration.
            backend (dict): Backend configuration.
            client (obj, optional): Backend client initiated beforehand.
            delete (bool, optional): Set to True if we're running a delete
                action.

        Returns:
            obj: Backend data.
        """
        # Grab backend class and method dynamically.
        cls_name = backend.get("class")
        method = config["spec"]["method"]
        excluded_keys = ["class", "service_level_indicator", "name"]
        backend_cfg = {k: v for k, v in backend.items() if k not in excluded_keys}
        cls = utils.get_backend_cls(cls_name)
        if not cls:
            LOGGER.warning(f"{self.info} | Backend {cls_name} not loaded.")
            self.valid = False
            return None
        instance = cls(client=client, **backend_cfg)
        method = getattr(instance, method)
        LOGGER.debug(
            f"{self.info} | "
            f"Using backend {cls_name}.{method.__name__} (from "
            f"SLO config file)."
        )

        # Delete mode activation.
        if delete and hasattr(instance, "delete"):
            method = instance.delete
            LOGGER.info(f"{self.info} | Delete mode enabled.")

        # Run backend method and return results.
        try:
            data = method(self.timestamp, self.window, config)
            LOGGER.debug(f"{self.info} | Backend response: {data}")
        except Exception as exc:  # pylint:disable=broad-except
            self.errors.append(utils.fmt_traceback(exc))
            return None
        return data

    def get_sli(self, data):
        """Compute SLI value and good / bad counts from the backend result.

        Some backends (e.g: Prometheus) are computing and returning the SLI
        value directly, others are sending a tuple (good_count, bad_count) and
        SLI value is computed from there.

        Args:
            data (obj): Backend data.

        Returns:
            tuple: A tuple of 3 values to unpack (float, int, int).
                float: SLI value.
                int: Good events count.
                int: Bad events count.

        Raises:
            Exception: When the backend does not return a proper result.
        """
        if isinstance(data, tuple):  # good, bad count
            good_count, bad_count = data
            if good_count == NO_DATA:
                good_count = 0
            if bad_count == NO_DATA:
                bad_count = 0
            LOGGER.debug(f"{self.info} | Good: {good_count} | Bad: {bad_count}")
            sli_measurement = round(good_count / (good_count + bad_count), 6)
        else:  # sli value
            sli_measurement = round(data, 6)
            good_count, bad_count = NO_DATA, NO_DATA
        return sli_measurement, good_count, bad_count

    def to_json(self) -> dict:
        """Serialize dataclass to JSON."""
        if not self.valid:
            ebp_name = self.error_budget_policy_step_name
            return {
                "metadata": self.metadata,
                "errors": self.errors,
                "error_budget_policy_step_name": ebp_name,
                "valid": self.valid,
            }
        return asdict(self)

    # pylint: disable=too-many-return-statements
    def _validate(self, data) -> bool:
        """Validate backend results. Invalid data will result in SLO report not
        being built.

        Args:
            data (obj): Backend result (expecting tuple, float, or int).

        Returns:
            bool: True if data is valid, False
        """
        # Backend not found
        if data is None:
            return False

        # Backend result is the wrong type
        if not isinstance(data, (tuple, float, int)):
            error = (
                f"Backend method returned an object of type "
                f"{type(data).__name__}. It should instead return a tuple "
                "(good_count, bad_count) or a numeric SLI value (float / int)."
            )
            self.errors.append(error)
            return False

        # Good / Bad tuple
        if isinstance(data, tuple):
            # Tuple length should be 2
            if len(data) != 2:
                error = (
                    f"Backend method returned a tuple with {len(data)} items."
                    f"Expected 2 items."
                )
                self.errors.append(error)
                return False
            good, bad = data

            # Tuple should contain only elements of type int or float
            if not all(isinstance(n, (float, int)) for n in data):
                error = (
                    "Backend method returned a tuple with some elements having"
                    " a type different than float or int"
                )
                self.errors.append(error)
                return False

            # Tuple should not contain any element with value None.
            if good is None or bad is None:
                error = (
                    f"Backend method returned a valid tuple {data} but one of "
                    "the values is None."
                )
                self.errors.append(error)
                return False

            # Tuple should not have NO_DATA everywhere
            if (good, bad) == (NO_DATA, NO_DATA):
                error = (
                    f"Backend method returned a valid tuple {data} but the "
                    "good and bad count is NO_DATA (-1)."
                )
                self.errors.append(error)
                return False

            # Tuple should not have elements where the sum is inferior to our
            # minimum valid events threshold
            if (good + bad) < MIN_VALID_EVENTS:
                error = (
                    f"Not enough valid events ({good + bad}) found. Minimum "
                    f"valid events: {MIN_VALID_EVENTS}."
                )
                self.errors.append(error)
                return False

        # Check backend float / int value
        if isinstance(data, (float, int)) and data == NO_DATA:
            error = "Backend returned NO_DATA (-1)."
            self.errors.append(error)
            return False

        # Check backend None
        if data is None:
            error = "Backend returned None."
            self.errors.append(error)
            return False

        return True

    def _post_validate(self) -> bool:
        """Validate report after build."""

        # SLI measurement should be 0 <= x <= 1
        if not 0 <= self.sli_measurement <= 1:
            error = f"SLI is not between 0 and 1 (value = {self.sli_measurement})"
            self.errors.append(error)
            return False

        return True

    # pylint: disable=dangerous-default-value
    def __set_fields(self, lambdas={}, **kwargs):
        """Set all fields in dataclasses from configs passed and apply function
        on values whose key match one in the dictionaries.

        Args:
            lambdas (dict): Dict {key: function} to apply a function on certain
            kwargs (dict): Dict of key / values to set in dataclass.
        """
        names = set(f.name for f in fields(self))
        for name in names:
            if name not in kwargs:
                continue
            value = kwargs[name]
            if name in lambdas:
                value = lambdas[name](value)
            setattr(self, name, value)

    @property
    def info(self) -> str:
        """Step information."""
        return f"{self.name :<32} | {self.error_budget_policy_step_name :<8}"

    def __str__(self) -> str:
        report = self.to_json()
        if not self.valid:
            errors_str = " | ".join(self.errors)
            return f"{self.info} | {errors_str}"
        goal_per = self.goal * 100
        sli_per = round(self.sli_measurement * 100, 6)
        gap = round(self.gap * 100, 2)
        gap_str = str(gap)
        if gap >= 0:
            gap_str = f"+{gap}"

        sli_str = f"SLI: {sli_per:<7} % | SLO: {goal_per} % | " f"Gap: {gap_str:<6}%"
        result_str = (
            "BR: {error_budget_burn_rate:<2} / "
            "{error_budget_burn_rate_threshold} | "
            "Alert: {alert:<1} | Good: {good_events_count:<8} | "
            "Bad: {bad_events_count:<8}"
        ).format_map(report)
        full_str = f"{self.info} | {sli_str} | {result_str}"
        if COLORED_OUTPUT == 1:
            if self.alert:
                full_str = Colors.FAIL + full_str + Colors.ENDC
            else:
                full_str = Colors.OKGREEN + full_str + Colors.ENDC
        return full_str
