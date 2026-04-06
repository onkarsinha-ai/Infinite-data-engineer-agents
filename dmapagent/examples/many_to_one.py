"""Example: Many-to-One Aggregation Mapping"""
from src.core.schema_extractor import SchemaExtractor, Field, Schema
from src.core.data_types import TypeInfo, SQLDataType, TypeConverter
from src.mapping.mapping_lineage import (
    MappingLineage,
    MappingType,
    MappingContext,
    AggregationRule,
    AggregationStrategy,
)
from src.mapping.aggregation_engine import AggregationEngine
from src.exporters.excel_exporter import ExcelExporter


def example_many_to_one_mapping():
    """Demonstrate N:1 aggregation mapping."""
    print("=" * 60)
    print("Example 2: Many-to-One Aggregation")
    print("=" * 60)

    type_converter = TypeConverter()

    # Source schema
    source_schema = Schema(name="EmployeeDB")
    source_fields = [
        Field(
            name="first_name",
            type_info=type_converter.parse_type_string("VARCHAR(50)"),
            table_name="employee",
        ),
        Field(
            name="last_name",
            type_info=type_converter.parse_type_string("VARCHAR(50)"),
            table_name="employee",
        ),
        Field(
            name="salary",
            type_info=type_converter.parse_type_string("DECIMAL(10,2)"),
            table_name="employee",
        ),
        Field(
            name="bonus",
            type_info=type_converter.parse_type_string("DECIMAL(10,2)"),
            table_name="employee",
        ),
    ]
    source_schema.add_table("employee", source_fields)

    # Destination schema
    dest_schema = Schema(name="ReportDB")
    dest_fields = [
        Field(
            name="full_name",
            type_info=type_converter.parse_type_string("VARCHAR(200)"),
            table_name="report",
        ),
        Field(
            name="total_compensation",
            type_info=type_converter.parse_type_string("DECIMAL(15,2)"),
            table_name="report",
        ),
    ]
    dest_schema.add_table("report", dest_fields)

    # Create mapping context
    context = MappingContext()
    context.source_schemas = {"EmployeeDB": source_schema}
    context.destination_schemas = {"ReportDB": dest_schema}

    # Use aggregation engine
    agg_engine = AggregationEngine()

    # N:1 Mapping 1: Concatenate names
    agg_rule1 = agg_engine.analyze_aggregation(
        [source_fields[0], source_fields[1]], dest_fields[0]
    )

    mapping1 = MappingLineage(
        mapping_type=MappingType.MANY_TO_ONE,
        source_fields=[source_fields[0], source_fields[1]],
        destination_field=dest_fields[0],
        aggregation_rule=agg_rule1,
        confidence=0.95,
        notes="Concatenate first and last names",
    )

    # N:1 Mapping 2: Sum compensation
    agg_rule2 = agg_engine.analyze_aggregation(
        [source_fields[2], source_fields[3]], dest_fields[1]
    )

    mapping2 = MappingLineage(
        mapping_type=MappingType.MANY_TO_ONE,
        source_fields=[source_fields[2], source_fields[3]],
        destination_field=dest_fields[1],
        aggregation_rule=agg_rule2,
        confidence=1.0,
        notes="Sum salary and bonus for total compensation",
    )

    # Add mappings to context
    context.add_lineage(mapping1)
    context.add_lineage(mapping2)

    # Set execution order (no dependencies)
    context.execution_order = [mapping1.mapping_id, mapping2.mapping_id]

    # Export to Excel
    exporter = ExcelExporter("examples/output/many_to_one_aggregation.xlsx")
    exporter.export(context)

    print(f"\n[OK] Created {len([mapping1, mapping2])} N:1 aggregation mappings:")
    print(f"  - (first_name + last_name) -> full_name via CONCAT")
    print(f"  - (salary + bonus) -> total_compensation via SUM")
    print(f"\n[OK] Exported to: examples/output/many_to_one_aggregation.xlsx")


if __name__ == "__main__":
    example_many_to_one_mapping()
