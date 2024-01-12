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
`bigquery.py`
BigQuery exporter class.
"""
import io
import json
import logging
import pprint

import google.api_core
from google.cloud import bigquery  # type: ignore[attr-defined]

from slo_generator import constants

LOGGER = logging.getLogger(__name__)


class BigqueryExporter:
    """BigQuery exporter class."""

    def __init__(self):
        self.client = bigquery.Client(project="unset")

    def export(self, data, **config):
        """Export results to BigQuery.

        Args:
            data (dict): Data to export.
                service_name (str): Service name.
                feature_name (str): Feature name.
                slo_name (str): SLO name.
                timestamp_human (str): Timestamp in human-readable format.
                measurement_window_seconds (int): Measurement window (in s).

            config (dict): Exporter config.
                project_id (str): BigQuery dataset project id.
                dataset_id (str): BigQuery dataset id.
                table_id (str): BigQuery table id.

        Raises:
            BigQueryError (object): BigQuery exception object.
        """
        project_id = config["project_id"]
        dataset_id = config["dataset_id"]
        table_id = config["table_id"]
        self.client.project = project_id
        table_ref = self.client.dataset(dataset_id).table(table_id)
        schema_fields = [element["name"] for element in TABLE_SCHEMA]
        keep_fields = config.get("keep_fields", [])
        try:
            table = self.client.get_table(table_ref)
            table = self.update_schema(table_ref, keep=keep_fields)
        except google.api_core.exceptions.NotFound:
            table = self.create_table(
                project_id,
                dataset_id,
                table_id,
                schema=TABLE_SCHEMA,
            )

        # Format user metadata if needed
        json_data = {k: v for k, v in data.items() if k in schema_fields}
        metadata = json_data.get("metadata", {})
        if isinstance(metadata, dict):
            metadata_fields = [
                {
                    "key": key,
                    "value": value,
                }
                for key, value in metadata.items()
            ]
            json_data["metadata"] = metadata_fields

        # Write results to BQ table
        if constants.DRY_RUN:
            LOGGER.info(f"[DRY RUN] Writing data to BigQuery: \n{json_data}")
            return []
        LOGGER.debug(f"Writing data to BigQuery:\n{json_data}")
        results = self.client.insert_rows_json(
            table,
            json_rows=[json_data],
            retry=google.api_core.retry.Retry(deadline=30),
        )
        if results:
            raise BigQueryError(results)
        return results

    @staticmethod
    def build_schema(schema):
        """Takes a schema defined as JSON (see TABLE_SCHEMA definition below)
        and convert it to a BigQuery schema.

        Args:
            schema (list): JSON Schema.

        Returns:
            list: BigQuery schema.
        """
        final_schema = []
        for row in schema:
            subschema = []
            if "fields" in row:
                subschema = [
                    bigquery.SchemaField(
                        subrow["name"],
                        subrow["type"],
                        mode=subrow["mode"],
                    )
                    for subrow in row["fields"]
                ]
            field = bigquery.SchemaField(
                row["name"],
                row["type"],
                mode=row["mode"],
                fields=subschema,
            )
            final_schema.append(field)
        return final_schema

    def create_table(self, project_id, dataset_id, table_id, schema=None):
        """Creates a BigQuery table from a schema.

        Args:
            project_id (str): Project id.
            dataset_id (str): Dataset id.
            table_id (str): Table id to create.
            schema (dict): BigQuery table schema in JSON format.

        Returns:
            obj: BigQuery table object.
        """
        if schema is not None:
            schema = TABLE_SCHEMA
        pyschema = BigqueryExporter.build_schema(schema)
        table_name = f"{project_id}.{dataset_id}.{table_id}"
        LOGGER.info(f"Creating table {table_name}")
        LOGGER.debug(f"Table schema: {pyschema}")
        table = bigquery.Table(table_name, schema=pyschema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
        )
        return self.client.create_table(table)

    # pylint: disable=dangerous-default-value
    def update_schema(self, table_ref, keep=[]):
        """Updates a BigQuery table schema if needed.

        Args:
            table_ref (str): BigQuery table reference.
            keep (list): List of fields to remote schema fields to keep.

        Returns:
            obj: BigQuery table object.
        """
        table = self.client.get_table(table=table_ref)
        iostream = io.StringIO("")
        self.client.schema_to_json(table.schema, iostream)
        existing_schema = json.loads(iostream.getvalue())
        existing_fields = [field["name"] for field in existing_schema]
        LOGGER.debug(f"Existing fields: {existing_fields}")

        # Fields in TABLE_SCHEMA to add / remove
        updated_fields = [
            field["name"] for field in TABLE_SCHEMA if field not in existing_schema
        ]
        extra_remote_fields = [
            field
            for field in existing_schema
            if field not in TABLE_SCHEMA and field["name"] in keep
        ]

        # If extra remote fields are detected in existing schema, update our
        # TABLE_SCHEMA with those
        if extra_remote_fields:
            LOGGER.info(f"Extra remote BigQuery fields: {extra_remote_fields}")
            TABLE_SCHEMA.extend(extra_remote_fields)

        # If new fields are detected in TABLE_SCHEMA, update BigQuery schema
        if updated_fields:
            LOGGER.info(f"Updated BigQuery fields: {updated_fields}")
            table.schema = BigqueryExporter.build_schema(TABLE_SCHEMA)
            if constants.DRY_RUN:
                LOGGER.info("[DRY RUN] Updating BigQuery schema.")
            else:
                LOGGER.info("Updating BigQuery schema.")
                LOGGER.debug(f"New schema: {pprint.pformat(table.schema)}")
                self.client.update_table(table, ["schema"])
        return table


class BigQueryError(Exception):
    """Exception raised whenever a BigQuery error happened.

    Args:
        errors (list): List of errors.
    """

    def __init__(self, errors):
        super().__init__(BigQueryError._format(errors))
        self.errors = errors

    @staticmethod
    def _format(errors):
        err = []
        for error in errors:
            err.extend(error["errors"])
        return json.dumps(err)


TABLE_SCHEMA = [
    {
        "name": "service_name",
        "type": "STRING",
        "mode": "REQUIRED",
    },
    {
        "name": "feature_name",
        "type": "STRING",
        "mode": "REQUIRED",
    },
    {
        "name": "slo_name",
        "type": "STRING",
        "mode": "REQUIRED",
    },
    {
        "name": "slo_target",
        "type": "FLOAT",
        "mode": "NULLABLE",
    },
    {
        "name": "slo_description",
        "type": "STRING",
        "mode": "REQUIRED",
    },
    {
        "name": "error_budget_policy_step_name",
        "type": "STRING",
        "mode": "NULLABLE",
    },
    {
        "name": "error_budget_remaining_minutes",
        "type": "FLOAT",
        "mode": "NULLABLE",
    },
    {
        "name": "consequence_message",
        "type": "STRING",
        "mode": "NULLABLE",
    },
    {
        "name": "error_budget_minutes",
        "type": "FLOAT",
        "mode": "NULLABLE",
    },
    {
        "name": "error_minutes",
        "type": "FLOAT",
        "mode": "NULLABLE",
    },
    {
        "name": "error_budget_target",
        "type": "FLOAT",
        "mode": "NULLABLE",
    },
    {
        "name": "timestamp_human",
        "type": "TIMESTAMP",
        "mode": "REQUIRED",
    },
    {
        "name": "timestamp",
        "type": "FLOAT",
        "mode": "NULLABLE",
    },
    {
        "name": "cadence",
        "type": "STRING",
        "mode": "NULLABLE",
    },
    {
        "name": "window",
        "type": "INTEGER",
        "mode": "REQUIRED",
    },
    {
        "name": "bad_events_count",
        "type": "INTEGER",
        "mode": "NULLABLE",
    },
    {
        "name": "good_events_count",
        "type": "INTEGER",
        "mode": "NULLABLE",
    },
    {
        "name": "sli_measurement",
        "type": "FLOAT",
        "mode": "NULLABLE",
    },
    {
        "name": "gap",
        "type": "FLOAT",
        "mode": "NULLABLE",
    },
    {
        "name": "error_budget_measurement",
        "type": "FLOAT",
        "mode": "NULLABLE",
    },
    {
        "name": "error_budget_burn_rate",
        "type": "FLOAT",
        "mode": "NULLABLE",
    },
    {
        "name": "alerting_burn_rate_threshold",
        "type": "FLOAT",
        "mode": "NULLABLE",
    },
    {
        "name": "alert",
        "type": "BOOLEAN",
        "mode": "NULLABLE",
    },
    {
        "name": "metadata",
        "type": "RECORD",
        "mode": "REPEATED",
        "fields": [
            {
                "name": "key",
                "type": "STRING",
                "mode": "NULLABLE",
            },
            {
                "name": "value",
                "type": "STRING",
                "mode": "NULLABLE",
            },
        ],
    },
]
