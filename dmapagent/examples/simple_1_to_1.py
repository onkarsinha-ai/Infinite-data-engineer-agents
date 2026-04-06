"""Example: Simple 1:1 Mapping"""
from src.core.schema_extractor import SchemaExtractor, Field, Schema
from src.core.data_types import TypeInfo, SQLDataType, TypeConverter
from src.mapping.mapping_lineage import MappingLineage, MappingType, MappingContext
from src.mapping.transformation import TransformationEngine
from src.exporters.excel_exporter import ExcelExporter


def example_1_to_1_mapping():
    """Demonstrate simple 1:1 field mapping."""
    print("=" * 60)
    print("Example 1: Simple 1:1 Mapping")
    print("=" * 60)

    # Create sample schemas
    type_converter = TypeConverter()

    # Source schema
    source_schema = Schema(name="SourceDB")
    source_fields = [
        Field(
            name="employee_id",
            type_info=type_converter.parse_type_string("INTEGER"),
            table_name="employees",
            is_primary_key=True,
        ),
        Field(
            name="first_name",
            type_info=type_converter.parse_type_string("VARCHAR(50)"),
            table_name="employees",
        ),
        Field(
            name="last_name",
            type_info=type_converter.parse_type_string("VARCHAR(50)"),
            table_name="employees",
        ),
    ]
    source_schema.add_table("employees", source_fields)

    # Destination schema
    dest_schema = Schema(name="ReportDB")
    dest_fields = [
        Field(
            name="emp_id",
            type_info=type_converter.parse_type_string("VARCHAR(20)"),
            table_name="employee_report",
        ),
        Field(
            name="fname",
            type_info=type_converter.parse_type_string("VARCHAR(100)"),
            table_name="employee_report",
        ),
        Field(
            name="lname",
            type_info=type_converter.parse_type_string("VARCHAR(100)"),
            table_name="employee_report",
        ),
    ]
    dest_schema.add_table("employee_report", dest_fields)

    # Create mapping context
    context = MappingContext()
    context.source_schemas = {"SourceDB": source_schema}
    context.destination_schemas = {"ReportDB": dest_schema}

    # Create 1:1 mappings
    mappings = [
        MappingLineage(
            mapping_type=MappingType.ONE_TO_ONE,
            source_fields=[source_fields[0]],
            destination_field=dest_fields[0],
            confidence=0.95,
            notes="INTEGER to VARCHAR conversion",
        ),
        MappingLineage(
            mapping_type=MappingType.ONE_TO_ONE,
            source_fields=[source_fields[1]],
            destination_field=dest_fields[1],
            confidence=1.0,
            notes="Direct VARCHAR mapping, wider dest field",
        ),
        MappingLineage(
            mapping_type=MappingType.ONE_TO_ONE,
            source_fields=[source_fields[2]],
            destination_field=dest_fields[2],
            confidence=1.0,
            notes="Direct VARCHAR mapping, wider dest field",
        ),
    ]

    for mapping in mappings:
        context.add_lineage(mapping)

    # Generate transformation code
    trans_engine = TransformationEngine()
    for mapping in mappings:
        trans_engine.build_transformation_pipeline(mapping)

    # Export to Excel
    exporter = ExcelExporter("examples/output/simple_1_to_1_mapping.xlsx")
    exporter.export(context)

    print(f"\n[OK] Created {len(mappings)} 1:1 mappings")
    print(f"  - employee_id -> emp_id")
    print(f"  - first_name -> fname")
    print(f"  - last_name -> lname")
    print(f"\n[OK] Exported to: examples/output/simple_1_to_1_mapping.xlsx")


if __name__ == "__main__":
    example_1_to_1_mapping()
