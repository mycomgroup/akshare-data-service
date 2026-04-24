"""Custom exceptions for akshare_data service layer."""


class DataServiceError(Exception):
    """Base exception for all data service errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class InvalidTableError(DataServiceError):
    """Raised when the requested table does not exist in the schema registry."""

    def __init__(self, table: str, available: list[str]):
        self.table = table
        self.available = available
        msg = f"Table '{table}' not found. Available tables: {sorted(available)}"
        super().__init__(msg)


class InvalidPartitionError(DataServiceError):
    """Raised when partition_by does not match the table's schema partition key."""

    def __init__(self, table: str, partition_by: str | None, expected: str | None):
        self.table = table
        self.partition_by = partition_by
        self.expected = expected
        msg = (
            f"Table '{table}' partition_by mismatch: got {partition_by!r}, "
            f"expected {expected!r}"
        )
        super().__init__(msg)


class InvalidColumnError(DataServiceError):
    """Raised when where/columns/order_by contains columns not in the table schema."""

    def __init__(
        self, table: str, invalid_columns: list[str], valid_columns: list[str]
    ):
        self.table = table
        self.invalid_columns = invalid_columns
        self.valid_columns = valid_columns
        msg = (
            f"Table '{table}' has invalid columns: {sorted(invalid_columns)}. "
            f"Valid columns: {sorted(valid_columns)}"
        )
        super().__init__(msg)
