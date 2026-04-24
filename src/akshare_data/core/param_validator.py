"""Parameter validation for query operations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from akshare_data.core.exceptions import (
    InvalidColumnError,
    InvalidPartitionError,
    InvalidTableError,
)
from akshare_data.core.schema import CacheTable, get_table_schema, list_tables

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def validate_query(
    table: str,
    partition_by: str | None,
    partition_value: str | None,
    where: dict[str, Any] | None,
    columns: list[str] | None,
    order_by: list[str] | None,
) -> CacheTable:
    """Validate query parameters against table schema.

    Args:
        table: Table name to query.
        partition_by: Partition key used for routing.
        partition_value: Partition value for the query.
        where: Column filters to apply.
        columns: Subset of columns to return.
        order_by: Columns to order results by.

    Returns:
        CacheTable schema for the validated table.

    Raises:
        InvalidTableError: If table does not exist in registry.
        InvalidPartitionError: If partition_by does not match schema.
        InvalidColumnError: If any where/columns/order_by columns are not in schema.
    """
    schema = get_table_schema(table)
    if schema is None:
        raise InvalidTableError(table, list_tables())

    if partition_by is not None and schema.partition_by is not None:
        if partition_by != schema.partition_by:
            raise InvalidPartitionError(table, partition_by, schema.partition_by)

    if where:
        unknown = set(where.keys()) - set(schema.schema.keys())
        if unknown:
            raise InvalidColumnError(table, list(unknown), list(schema.schema.keys()))

    if columns:
        unknown = set(columns) - set(schema.schema.keys())
        if unknown:
            raise InvalidColumnError(table, list(unknown), list(schema.schema.keys()))

    if order_by:
        order_cols = [c.split()[0] for c in order_by]
        unknown = set(order_cols) - set(schema.schema.keys())
        if unknown:
            raise InvalidColumnError(table, list(unknown), list(schema.schema.keys()))

    return schema


def validate_partition_params(
    table: str,
    partition_by: str | None,
    partition_value: str | None,
) -> CacheTable:
    """Validate partition-related parameters.

    Args:
        table: Table name.
        partition_by: Partition key.
        partition_value: Partition value.

    Returns:
        CacheTable schema for the validated table.

    Raises:
        InvalidTableError: If table does not exist.
        InvalidPartitionError: If partition mismatch.
    """
    schema = get_table_schema(table)
    if schema is None:
        raise InvalidTableError(table, list_tables())

    if partition_by is not None and schema.partition_by is not None:
        if partition_by != schema.partition_by:
            raise InvalidPartitionError(table, partition_by, schema.partition_by)

    return schema
