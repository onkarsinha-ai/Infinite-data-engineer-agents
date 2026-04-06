"""Schema extraction and normalization."""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from src.core.data_types import TypeConverter, TypeInfo
from src.core.document_parser import DocumentParser, ParsedContent
from src.utils.logger import get_logger
from src.utils.helpers import generate_id

logger = get_logger(__name__)


@dataclass
class Field:
    """Represents a database field/column."""

    name: str
    type_info: TypeInfo
    table_name: str
    is_primary_key: bool = False
    is_unique: bool = False
    nullable: bool = True
    has_default: bool = False
    description: str = ""
    source_file: str = ""
    raw_definition: str = ""
    field_id: str = field(default_factory=lambda: generate_id("field"))

    def __str__(self) -> str:
        return f"{self.table_name}.{self.name} ({self.type_info})"

    def __hash__(self):
        return hash(f"{self.table_name}.{self.name}")

    def __eq__(self, other):
        if not isinstance(other, Field):
            return False
        return self.table_name == other.table_name and self.name == other.name


@dataclass
class Schema:
    """Represents a database schema."""

    name: str
    tables: Dict[str, List[Field]] = field(default_factory=dict)
    source_file: str = ""
    source_type: str = ""  # 'ddl', 'excel', 'word', 'html', 'pdf'
    metadata: Dict[str, Any] = field(default_factory=dict)
    schema_id: str = field(default_factory=lambda: generate_id("schema"))

    def add_table(self, table_name: str, fields: List[Field]) -> None:
        """Add table to schema."""
        self.tables[table_name] = fields
        logger.debug(f"Added table {table_name} with {len(fields)} fields to schema {self.name}")

    def get_table(self, table_name: str) -> Optional[List[Field]]:
        """Get fields for a table."""
        return self.tables.get(table_name)

    def get_all_fields(self) -> List[Field]:
        """Get all fields from all tables."""
        fields = []
        for table_fields in self.tables.values():
            fields.extend(table_fields)
        return fields

    def get_field(self, table_name: str, field_name: str) -> Optional[Field]:
        """Get specific field."""
        table_fields = self.get_table(table_name)
        if table_fields:
            for field in table_fields:
                if field.name == field_name:
                    return field
        return None

    def __str__(self) -> str:
        table_info = ", ".join(
            f"{name}({len(fields)} cols)" for name, fields in self.tables.items()
        )
        return f"Schema({self.name}): [{table_info}]"


class SchemaExtractor:
    """Extract and normalize schemas from various sources."""

    def __init__(self):
        """Initialize extractor."""
        self.document_parser = DocumentParser()
        self.type_converter = TypeConverter()

    def extract_from_file(self, file_path: str, schema_name: Optional[str] = None) -> Schema:
        """Extract schema from a single file."""
        logger.info(f"Extracting schema from: {file_path}")

        parsed_content = self.document_parser.parse(file_path)
        schema_name = schema_name or parsed_content.metadata.get("file", "unknown")

        return self._create_schema(parsed_content, schema_name, file_path)

    def extract_from_multiple_files(
        self, file_paths: List[str], schema_names: Optional[List[str]] = None
    ) -> Dict[str, Schema]:
        """Extract schemas from multiple files."""
        schemas = {}

        for idx, file_path in enumerate(file_paths):
            schema_name = (schema_names[idx] if schema_names else None) or f"schema_{idx}"
            schema = self.extract_from_file(file_path, schema_name)
            schemas[schema_name] = schema
            logger.info(f"Extracted schema: {schema}")

        return schemas

    def _create_schema(
        self, parsed_content: ParsedContent, schema_name: str, source_file: str
    ) -> Schema:
        """Create Schema object from parsed content."""
        schema = Schema(
            name=schema_name,
            source_file=source_file,
            source_type=parsed_content.source_type,
            metadata=parsed_content.metadata,
        )

        # Convert parsed tables to Field objects
        for table_name, columns in parsed_content.tables.items():
            fields = self._create_fields(table_name, columns, source_file)
            schema.add_table(table_name, fields)

        return schema

    def _create_fields(self, table_name: str, columns: List[Dict], source_file: str) -> List[Field]:
        """Create Field objects from column definitions."""
        fields = []

        for col in columns:
            type_info = self.type_converter.parse_type_string(col.get("type", "VARCHAR"))

            field = Field(
                name=col.get("name", "unknown"),
                type_info=type_info,
                table_name=table_name,
                is_primary_key=col.get("primary_key", False),
                is_unique=col.get("unique", False),
                nullable=col.get("nullable", True),
                has_default=col.get("has_default", False),
                source_file=source_file,
                raw_definition=col.get("raw", ""),
            )
            fields.append(field)

        return fields

    def normalize_schema(self, schema: Schema) -> Schema:
        """Normalize schema (standardize names, types, etc.)."""
        logger.info(f"Normalizing schema: {schema.name}")

        normalized_tables = {}

        for table_name, fields in schema.tables.items():
            normalized_fields = []

            for field in fields:
                # Normalize field name
                normalized_name = field.name.lower().replace(" ", "_")

                # Already has normalized TypeInfo
                normalized_field = Field(
                    name=normalized_name,
                    type_info=field.type_info,
                    table_name=table_name.lower().replace(" ", "_"),
                    is_primary_key=field.is_primary_key,
                    is_unique=field.is_unique,
                    nullable=field.nullable,
                    has_default=field.has_default,
                    source_file=field.source_file,
                    raw_definition=field.raw_definition,
                )
                normalized_fields.append(normalized_field)

            normalized_tables[table_name.lower().replace(" ", "_")] = normalized_fields

        schema.tables = normalized_tables
        return schema

    def get_schema_statistics(self, schema: Schema) -> Dict[str, Any]:
        """Get statistics about schema."""
        all_fields = schema.get_all_fields()

        type_distribution = {}
        for field in all_fields:
            type_name = field.type_info.base_type.value
            type_distribution[type_name] = type_distribution.get(type_name, 0) + 1

        return {
            "name": schema.name,
            "table_count": len(schema.tables),
            "total_fields": len(all_fields),
            "primary_keys": sum(1 for f in all_fields if f.is_primary_key),
            "nullable_fields": sum(1 for f in all_fields if f.nullable),
            "unique_fields": sum(1 for f in all_fields if f.is_unique),
            "type_distribution": type_distribution,
        }
