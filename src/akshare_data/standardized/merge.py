"""Merge / Upsert logic for Standardized (L1) layer.

Handles late-arriving data, duplicate data, and incremental coverage
with clear rules for version-based conflict resolution.

Spec: docs/design/40-standardized-storage-spec.md §6
"""

from __future__ import annotations

import logging
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MergeEngine:
    """Merges new normalized data into existing Standardized data.

    Merge rules:
    1. Late-arriving data: compare normalize_version and ingest_time
    2. Duplicate data: deduplicate by primary key within the same batch
    3. Incremental coverage: upsert by primary key across batches

    Usage::

        engine = MergeEngine(primary_key=["security_id", "trade_date", "adjust_type"])

        merged = engine.merge(
            existing=existing_df,
            incoming=new_df,
            strategy="upsert",
        )
    """

    def __init__(self, primary_key: List[str]) -> None:
        self._primary_key = primary_key

    def merge(
        self,
        existing: pd.DataFrame,
        incoming: pd.DataFrame,
        *,
        strategy: str = "upsert",
    ) -> pd.DataFrame:
        """Merge incoming data into existing data.

        Args:
            existing: Current data in the partition.
            incoming: New data to merge.
            strategy: One of "upsert", "append", "replace".
                - "upsert": incoming overwrites existing rows with same PK
                - "append": simply concatenate (no dedup)
                - "replace": return only incoming data

        Returns:
            Merged DataFrame.
        """
        if existing.empty:
            return incoming.copy()
        if incoming.empty:
            return existing.copy()

        if strategy == "replace":
            return incoming.copy()

        if strategy == "append":
            return pd.concat([existing, incoming], ignore_index=True)

        return self._upsert(existing, incoming)

    def _upsert(
        self,
        existing: pd.DataFrame,
        incoming: pd.DataFrame,
    ) -> pd.DataFrame:
        """Upsert incoming data over existing data by primary key.

        For rows with matching primary keys:
        - If incoming normalize_version > existing version: use incoming
        - If versions are equal but incoming ingest_time > existing: use incoming
        - Otherwise: keep existing

        For rows with no match: include as-is.
        """
        pk_cols = [
            c
            for c in self._primary_key
            if c in existing.columns and c in incoming.columns
        ]
        if not pk_cols:
            logger.warning(
                "No common primary key columns found, falling back to append"
            )
            return pd.concat([existing, incoming], ignore_index=True)

        existing_keys = _make_key(existing, pk_cols)
        incoming_keys = _make_key(incoming, pk_cols)

        existing_key_set = set(existing_keys)
        incoming_key_set = set(incoming_keys)

        overlapping_keys = existing_key_set & incoming_key_set

        if not overlapping_keys:
            return pd.concat([existing, incoming], ignore_index=True)

        existing_mask = existing_keys.isin(overlapping_keys)
        incoming_mask = incoming_keys.isin(overlapping_keys)

        existing_overlap = existing[existing_mask].copy()
        incoming_overlap = incoming[incoming_mask].copy()

        existing_overlap["_merge_key"] = existing_keys[existing_mask].values
        incoming_overlap["_merge_key"] = incoming_keys[incoming_mask].values

        resolved = self._resolve_conflicts(existing_overlap, incoming_overlap)

        existing_non_overlap = existing[~existing_mask].copy()
        incoming_non_overlap = incoming[~incoming_mask].copy()

        result = pd.concat(
            [existing_non_overlap, incoming_non_overlap, resolved],
            ignore_index=True,
        )

        if "_merge_key" in result.columns:
            result = result.drop(columns=["_merge_key"])

        return result

    def _resolve_conflicts(
        self,
        existing: pd.DataFrame,
        incoming: pd.DataFrame,
    ) -> pd.DataFrame:
        """Resolve conflicts for overlapping primary keys using vectorized operations.

        Priority:
        1. Higher normalize_version wins
        2. If versions equal, later ingest_time wins
        3. If both equal, incoming wins
        """
        merged = existing.merge(
            incoming,
            on="_merge_key",
            how="outer",
            suffixes=("_existing", "_incoming"),
            indicator=True,
        )

        norm_exist_col = "normalize_version_existing"
        norm_income_col = "normalize_version_incoming"
        ingest_exist_col = "ingest_time_existing"
        ingest_income_col = "ingest_time_incoming"

        if norm_exist_col not in merged.columns or norm_income_col not in merged.columns:
            return pd.DataFrame()

        norm_exist = merged[norm_exist_col].astype(str)
        norm_income = merged[norm_income_col].astype(str)
        ingest_exist = pd.to_datetime(merged[ingest_exist_col], errors="coerce")
        ingest_income = pd.to_datetime(merged[ingest_income_col], errors="coerce")

        incoming_version_lower = norm_income.str.lt(norm_exist) & norm_exist.notna() & norm_income.notna()
        version_equal = norm_income == norm_exist
        incoming_time_le = version_equal & ingest_income.notna() & ingest_exist.notna() & ingest_income.le(ingest_exist)
        use_existing = incoming_version_lower | incoming_time_le

        base_cols = [c for c in merged.columns if not c.endswith(("_existing", "_incoming", "_merge_key", "_merge"))]
        result_parts = []

        for col in base_cols:
            existing_col = f"{col}_existing"
            incoming_col = f"{col}_incoming"
            if existing_col in merged.columns and incoming_col in merged.columns:
                result_parts.append(
                    pd.Series(
                        np.where(use_existing, merged[existing_col], merged[incoming_col]),
                        index=merged.index,
                        name=col,
                    )
                )
            elif existing_col in merged.columns:
                result_parts.append(merged[existing_col].rename(col))
            elif incoming_col in merged.columns:
                result_parts.append(merged[incoming_col].rename(col))

        if not result_parts:
            return pd.DataFrame()

        return pd.concat(result_parts, axis=1)

    def merge_late_arriving(
        self,
        existing: pd.DataFrame,
        late_data: pd.DataFrame,
    ) -> pd.DataFrame:
        """Merge late-arriving data with version-aware conflict resolution.

        Late-arriving data is data that arrives after its business time
        partition has already been written.

        Args:
            existing: Current partition data.
            late_data: Late-arriving data.

        Returns:
            Merged DataFrame with late data properly integrated.
        """
        return self._upsert(existing, late_data)

    def merge_incremental(
        self,
        existing: pd.DataFrame,
        incremental: pd.DataFrame,
    ) -> pd.DataFrame:
        """Merge incremental data (new rows + updates).

        Same as upsert but optimized for the case where most incoming
        rows are new (not overlapping with existing).

        Args:
            existing: Current data.
            incremental: New incremental data.

        Returns:
            Merged DataFrame.
        """
        return self._upsert(existing, incremental)


def _make_key(df: pd.DataFrame, pk_cols: List[str]) -> pd.Series:
    """Create a composite key string from primary key columns."""
    if len(pk_cols) == 1:
        return df[pk_cols[0]].astype(str)
    return df[pk_cols].astype(str).agg("|".join, axis=1)


def _compare_version(v1: str, v2: str) -> int:
    """Compare version strings like 'v1', 'v2', 'v10'.

    Returns:
        -1 if v1 < v2, 0 if equal, 1 if v1 > v2.
    """
    n1 = _parse_version_num(v1)
    n2 = _parse_version_num(v2)
    if n1 < n2:
        return -1
    if n1 > n2:
        return 1
    return 0


def _parse_version_num(version: str) -> int:
    """Extract numeric part from version string like 'v1' -> 1."""
    s = version.lstrip("vV")
    try:
        return int(s)
    except ValueError:
        return 0


def _pick_row(
    merged_row: pd.Series,
    source: str,
) -> dict:
    """Pick columns from the specified source in a merged row."""
    result = {}
    for col in merged_row.index:
        if col in (
            "_merge_key",
            "_merge_key_existing",
            "_merge_key_incoming",
            "_merge",
        ):
            continue
        if col.endswith("_existing"):
            base = col[: -len("_existing")]
            if source == "existing":
                result[base] = merged_row[col]
        elif col.endswith("_incoming"):
            base = col[: -len("_incoming")]
            if source == "incoming":
                result[base] = merged_row[col]
        else:
            if col not in result:
                result[col] = merged_row[col]
    return result
