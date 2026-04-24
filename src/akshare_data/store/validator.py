import pandas as pd
import pandas.api.types as pdt
import pyarrow as pa


class SchemaValidationError(Exception):
    def __init__(self, table: str, errors: list[str]):
        self.table = table
        self.errors = errors
        super().__init__(f"Schema validation failed for '{table}': {'; '.join(errors)}")


PYARROW_TYPE_MAP = {
    "string": pa.string(),
    "int64": pa.int64(),
    "int32": pa.int32(),
    "float64": pa.float64(),
    "float32": pa.float32(),
    "bool": pa.bool_(),
    "date": pa.date32(),
    "date64": pa.date64(),
    "timestamp": pa.timestamp("ms"),
    "datetime": pa.timestamp("ms"),
}


_NUMERIC_KINDS = {"int64", "int32", "int16", "int8", "float64", "float32", "float16"}
_DATE_KINDS = {"date", "date64", "timestamp", "datetime"}


def _dtype_kind(dtype_or_name) -> str:
    """Normalize a pandas/numpy dtype (or its string form) into a canonical kind.

    The validator's schema vocabulary uses simple names like 'string', 'int64',
    'float64', 'bool', 'date', 'datetime'. Pandas 2.x / 3.x now emit nullable
    extension dtypes such as ``StringDtype()``, ``Int64Dtype()``, ``BooleanDtype()``
    whose ``str()`` representation is ``'str'`` / ``'Int64'`` / ``'boolean'`` and
    therefore does not match the legacy vocabulary. We canonicalize via
    ``pandas.api.types`` so both legacy and nullable dtypes map onto the same
    keyword.
    """

    # Accept either a real dtype object or its string alias.
    if isinstance(dtype_or_name, str):
        raw = dtype_or_name.lower()
        if raw in _NUMERIC_KINDS or raw == "bool" or raw in _DATE_KINDS:
            return raw
        if raw in ("string", "str", "object"):
            return "string" if raw != "object" else "object"
        if raw.startswith("datetime64"):
            return "datetime"
        if raw.startswith("int"):
            return "int64"
        if raw.startswith("float"):
            return "float64"
        return raw

    dtype = dtype_or_name
    try:
        if pdt.is_bool_dtype(dtype):
            return "bool"
        if pdt.is_integer_dtype(dtype):
            return "int64"
        if pdt.is_float_dtype(dtype):
            return "float64"
        if pdt.is_datetime64_any_dtype(dtype):
            return "datetime"
        if pdt.is_string_dtype(dtype):
            # Treat numpy object columns as object so the "object -> anything"
            # fallbacks still apply; only truly string-typed extension arrays
            # report as 'string'.
            if getattr(dtype, "name", None) == "object":
                return "object"
            return "string"
    except (TypeError, ValueError):
        pass

    return str(dtype).lower()


class SchemaValidator:
    def __init__(self, table: str, schema: dict[str, str]):
        self.table = table
        self.schema = schema

    def validate(self, df: pd.DataFrame) -> list[str]:
        errors = []
        for col, expected_type in self.schema.items():
            if col not in df.columns:
                errors.append(f"Missing column: '{col}'")
                continue
            actual_dtype = str(df[col].dtype)
            if not SchemaValidator.is_compatible(df[col].dtype, expected_type):
                errors.append(
                    f"Column '{col}' has incompatible type: expected '{expected_type}', got '{actual_dtype}'"
                )
        return errors

    def validate_and_cast(
        self, df: pd.DataFrame, primary_key: list[str] | None = None
    ) -> pd.DataFrame:
        errors = self.validate(df)
        if errors:
            raise SchemaValidationError(self.table, errors)

        result = df.copy()
        for col, target_type in self.schema.items():
            if col not in result.columns:
                continue
            # Skip when the column already represents the requested kind; this
            # preserves nullable extension dtypes (``string``, ``Int64``...)
            # instead of downcasting them to the legacy numpy equivalents.
            if _dtype_kind(result[col].dtype) == _dtype_kind(target_type):
                continue
            result[col] = self._cast_column(result[col], target_type)

        if primary_key is not None:
            for pk_col in primary_key:
                if pk_col in result.columns and result[pk_col].isna().any():
                    raise SchemaValidationError(
                        self.table,
                        [f"Primary key column '{pk_col}' contains null values"],
                    )

        return result

    def _cast_column(self, series: pd.Series, target_type: str) -> pd.Series:
        if target_type in ("string",):
            # Cast to a raw object/str column (not a nullable StringDtype) so
            # downstream consumers (duckdb, pyarrow, legacy tests) see dtype
            # ``object`` consistently across pandas versions.
            return series.astype(str).astype(object)
        if target_type in ("int64", "int32"):
            return pd.to_numeric(series, errors="coerce").astype(
                "Int64" if target_type == "int64" else "Int32"
            )
        if target_type in ("float64", "float32"):
            return pd.to_numeric(series, errors="coerce").astype(
                "float64" if target_type == "float64" else "float32"
            )
        if target_type in ("date", "date64"):
            return pd.to_datetime(series).dt.date
        if target_type in ("timestamp", "datetime"):
            return pd.to_datetime(series)
        if target_type == "bool":
            return series.astype(bool)
        return series

    @staticmethod
    def is_compatible(from_type, to_type: str) -> bool:
        """Return True when ``from_type`` is acceptable for ``to_type``.

        ``from_type`` may be a raw pandas/numpy dtype instance or the legacy
        lower-case string alias. The comparison normalizes both sides through
        :func:`_dtype_kind` so pandas nullable extension dtypes (``Int64``,
        ``string``, ``boolean``, ``Float64``) and legacy numpy dtypes
        (``int64``, ``object``, ``datetime64[ns]``) are treated uniformly.
        """

        from_kind = _dtype_kind(from_type)
        to_kind = _dtype_kind(to_type)

        if from_kind == to_kind:
            return True
        if from_kind in _NUMERIC_KINDS and to_kind in _NUMERIC_KINDS:
            return True
        if from_kind in _DATE_KINDS and to_kind in _DATE_KINDS:
            return True
        if from_kind in ("object", "string") and to_kind in _DATE_KINDS:
            return True
        if from_kind in ("object", "string") and to_kind in _NUMERIC_KINDS:
            return True
        if from_kind in _NUMERIC_KINDS and to_kind == "string":
            return True
        if from_kind == "object" and to_kind == "string":
            return True
        if from_kind == "string" and to_kind == "object":
            return True
        if from_kind == "bool" and to_kind in ("string", "int64", "int32"):
            return True
        return False


def infer_schema(df: pd.DataFrame) -> dict[str, str]:
    schema = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        if dtype.startswith("float"):
            schema[col] = "float64"
        elif dtype.startswith("int"):
            schema[col] = "int64"
        elif dtype == "bool":
            schema[col] = "bool"
        elif dtype == "object":
            schema[col] = "string"
        elif "datetime" in dtype:
            schema[col] = "datetime"
        else:
            schema[col] = "string"
    return schema


def normalize_date_columns(
    df: pd.DataFrame, columns: list[str] | None = None
) -> pd.DataFrame:
    result = df.copy()
    cols = columns if columns is not None else result.columns.tolist()
    for col in cols:
        if col in result.columns:
            result[col] = pd.to_datetime(result[col]).dt.date
    return result


def deduplicate_by_key(df: pd.DataFrame, primary_key: list[str]) -> pd.DataFrame:
    return df.drop_duplicates(subset=primary_key, keep="last")
