"""Data types and type conversion support."""
from enum import Enum
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from config import get_settings

settings = get_settings()


class SQLDataType(str, Enum):
    """Supported SQL data types."""

    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    SMALLINT = "SMALLINT"
    DECIMAL = "DECIMAL"
    NUMERIC = "NUMERIC"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"
    VARCHAR = "VARCHAR"
    CHAR = "CHAR"
    TEXT = "TEXT"
    DATE = "DATE"
    DATETIME = "DATETIME"
    TIMESTAMP = "TIMESTAMP"
    TIME = "TIME"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
    JSONB = "JSONB"
    UUID = "UUID"
    BLOB = "BLOB"
    CLOB = "CLOB"
    ARRAY = "ARRAY"
    UNKNOWN = "UNKNOWN"


@dataclass
class TypeInfo:
    """Information about a data type."""

    base_type: SQLDataType
    precision: Optional[int] = None  # For DECIMAL, VARCHAR
    scale: Optional[int] = None  # For DECIMAL
    nullable: bool = True
    is_array: bool = False

    def __str__(self) -> str:
        """String representation."""
        type_str = self.base_type.value
        if self.precision:
            if self.scale:
                type_str += f"({self.precision},{self.scale})"
            else:
                type_str += f"({self.precision})"
        nullable_str = "" if self.nullable else " NOT NULL"
        return type_str + nullable_str


class TypeConverter:
    """Convert between different type representations."""

    def __init__(self):
        """Initialize converter."""
        self.type_mappings = settings.DEFAULT_TYPE_MAPPINGS

    def parse_type_string(self, type_string: str) -> TypeInfo:
        """Parse type string into TypeInfo.
        
        Examples:
            "INTEGER" -> TypeInfo(SQLDataType.INTEGER)
            "VARCHAR(100)" -> TypeInfo(SQLDataType.VARCHAR, precision=100)
            "DECIMAL(10,2)" -> TypeInfo(SQLDataType.DECIMAL, precision=10, scale=2)
        """
        type_string = type_string.strip().upper()
        nullable = "NOT NULL" not in type_string

        # Remove NOT NULL clause
        type_string = type_string.replace("NOT NULL", "").strip()

        # Extract base type and parameters
        if "(" in type_string:
            base, params = type_string.split("(", 1)
            base = base.strip()
            params = params.rstrip(")")

            precision, scale = self._parse_params(params)
        else:
            base = type_string
            precision = None
            scale = None

        # Normalize base type
        base_type = self._normalize_base_type(base)

        return TypeInfo(
            base_type=base_type,
            precision=precision,
            scale=scale,
            nullable=nullable,
        )

    def _parse_params(self, params: str) -> Tuple[Optional[int], Optional[int]]:
        """Parse type parameters."""
        parts = params.split(",")
        precision = None
        scale = None

        if len(parts) > 0:
            try:
                precision = int(parts[0].strip())
            except ValueError:
                pass

        if len(parts) > 1:
            try:
                scale = int(parts[1].strip())
            except ValueError:
                pass

        return precision, scale

    def _normalize_base_type(self, type_name: str) -> SQLDataType:
        """Normalize type name."""
        type_name = type_name.lower().strip()

        # Check direct mapping
        if type_name in self.type_mappings:
            mapped = self.type_mappings[type_name]
            try:
                return SQLDataType[mapped]
            except KeyError:
                pass

        # Try exact match
        try:
            return SQLDataType[type_name.upper()]
        except KeyError:
            return SQLDataType.UNKNOWN

    def is_type_narrowing(
        self, source_type: TypeInfo, dest_type: TypeInfo
    ) -> bool:
        """Check if conversion is narrowing (potential data loss)."""
        # VARCHAR narrowing
        if (
            source_type.base_type == SQLDataType.VARCHAR
            and dest_type.base_type == SQLDataType.VARCHAR
        ):
            if (
                source_type.precision
                and dest_type.precision
                and source_type.precision > dest_type.precision
            ):
                return True

        # DECIMAL narrowing (precision or scale loss)
        if (
            source_type.base_type == SQLDataType.DECIMAL
            and dest_type.base_type == SQLDataType.DECIMAL
        ):
            if source_type.precision and dest_type.precision:
                if source_type.precision > dest_type.precision:
                    return True
                if source_type.scale and dest_type.scale:
                    if source_type.scale > dest_type.scale:
                        return True

        # Numeric to integer (potential precision loss)
        if source_type.base_type in [
            SQLDataType.DECIMAL,
            SQLDataType.NUMERIC,
            SQLDataType.FLOAT,
            SQLDataType.DOUBLE,
        ] and dest_type.base_type in [SQLDataType.INTEGER, SQLDataType.BIGINT]:
            return True

        # Any type to CHAR/VARCHAR of smaller size
        if dest_type.base_type in [
            SQLDataType.VARCHAR,
            SQLDataType.CHAR,
        ] and source_type.base_type not in [
            SQLDataType.VARCHAR,
            SQLDataType.CHAR,
            SQLDataType.TEXT,
        ]:
            if dest_type.precision and dest_type.precision < 50:
                return True

        return False

    def is_type_widening(
        self, source_type: TypeInfo, dest_type: TypeInfo
    ) -> bool:
        """Check if conversion is widening (safe type expansion)."""
        # Integer to Bigint
        if (
            source_type.base_type == SQLDataType.INTEGER
            and dest_type.base_type == SQLDataType.BIGINT
        ):
            return True

        # Numeric widening
        if source_type.base_type in [
            SQLDataType.INTEGER,
            SQLDataType.BIGINT,
        ] and dest_type.base_type in [
            SQLDataType.DECIMAL,
            SQLDataType.NUMERIC,
            SQLDataType.FLOAT,
            SQLDataType.DOUBLE,
        ]:
            return True

        # VARCHAR widening
        if (
            source_type.base_type == SQLDataType.VARCHAR
            and dest_type.base_type == SQLDataType.VARCHAR
        ):
            if (
                source_type.precision
                and dest_type.precision
                and source_type.precision < dest_type.precision
            ):
                return True

        # Any to TEXT
        if dest_type.base_type == SQLDataType.TEXT:
            return True

        return False

    def requires_conversion(
        self, source_type: TypeInfo, dest_type: TypeInfo
    ) -> bool:
        """Check if type conversion is needed."""
        return source_type.base_type != dest_type.base_type

    def get_conversion_risk(
        self, source_type: TypeInfo, dest_type: TypeInfo
    ) -> str:
        """Get risk level for type conversion.
        
        Returns:
            "NONE" - No risk
            "LOW" - Minimal risk
            "MEDIUM" - Moderate risk
            "HIGH" - High risk of data loss
            "CRITICAL" - Guaranteed data loss
        """
        if not self.requires_conversion(source_type, dest_type):
            return "NONE"

        if self.is_type_widening(source_type, dest_type):
            return "LOW"

        if self.is_type_narrowing(source_type, dest_type):
            return "CRITICAL"

        # Check for incompatible conversions
        if source_type.base_type == SQLDataType.JSON and dest_type.base_type in [
            SQLDataType.VARCHAR,
            SQLDataType.CHAR,
        ]:
            return "HIGH"

        if source_type.base_type in [
            SQLDataType.DATETIME,
            SQLDataType.TIMESTAMP,
        ] and dest_type.base_type == SQLDataType.VARCHAR:
            return "MEDIUM"

        return "MEDIUM"
