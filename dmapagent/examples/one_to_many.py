"""Example: One-to-Many Decomposition Mapping"""
from src.core.schema_extractor import Field, Schema
from src.core.data_types import TypeConverter
from src.mapping.mapping_lineage import (
    MappingLineage,
    MappingType,
    MappingContext,
    DecompositionRule,
    DecompositionStrategy,
)
from src.mapping.decomposition_engine import DecompositionEngine
from src.exporters.excel_exporter import ExcelExporter


def example_one_to_many_mapping():
    """Demonstrate 1:N decomposition mapping."""
    print("=" * 60)
    print("Example 3: One-to-Many Decomposition")
    print("=" * 60)

    type_converter = TypeConverter()

    # Source schema
    source_schema = Schema(name="SourceDB")
    source_fields = [
        Field(
            name="full_name",
            type_info=type_converter.parse_type_string("VARCHAR(100)"),
            table_name="contact",
        ),
        Field(
            name="address_data",
            type_info=type_converter.parse_type_string("VARCHAR(500)"),
            table_name="contact",
        ),
    ]
    source_schema.add_table("contact", source_fields)

    # Destination schema
    dest_schema = Schema(name="DestDB")
    dest_fields = [
        Field(
            name="first_name",
            type_info=type_converter.parse_type_string("VARCHAR(50)"),
            table_name="person",
        ),
        Field(
            name="last_name",
            type_info=type_converter.parse_type_string("VARCHAR(50)"),
            table_name="person",
        ),
        Field(
            name="street",
            type_info=type_converter.parse_type_string("VARCHAR(100)"),
            table_name="person",
        ),
        Field(
            name="city",
            type_info=type_converter.parse_type_string("VARCHAR(50)"),
            table_name="person",
        ),
    ]
    dest_schema.add_table("person", dest_fields)

    # Create mapping context
    context = MappingContext()
    context.source_schemas = {"SourceDB": source_schema}
    context.destination_schemas = {"DestDB": dest_schema}

    # Use decomposition engine
    decomp_engine = DecompositionEngine()

    # 1:N Mapping 1: Split full name
    decomp_rule1 = decomp_engine.analyze_decomposition(
        source_fields[0], [dest_fields[0], dest_fields[1]]
    )

    mapping1 = MappingLineage(
        mapping_type=MappingType.ONE_TO_MANY,
        source_fields=[source_fields[0]],
        destination_fields=[dest_fields[0], dest_fields[1]],
        decomposition_rule=decomp_rule1,
        confidence=0.9,
        notes="Split full_name by space into first and last",
        is_destructive=True,
        destruction_type="DECOMPOSITION_LOSS",
        destruction_details="Names with multiple spaces may be split incorrectly",
    )

    # 1:N Mapping 2: Parse address
    decomp_rule2 = decomp_engine.analyze_decomposition(
        source_fields[1], [dest_fields[2], dest_fields[3]]
    )

    mapping2 = MappingLineage(
        mapping_type=MappingType.ONE_TO_MANY,
        source_fields=[source_fields[1]],
        destination_fields=[dest_fields[2], dest_fields[3]],
        decomposition_rule=decomp_rule2,
        confidence=0.75,
        notes="Parse address_data to extract street and city",
        is_destructive=True,
        destruction_type="DECOMPOSITION_LOSS",
        destruction_details="Some address fields may be lost if format varies",
    )

    # Add mappings to context
    context.add_lineage(mapping1)
    context.add_lineage(mapping2)

    # Set execution order
    context.execution_order = [mapping1.mapping_id, mapping2.mapping_id]

    # Export to Excel
    exporter = ExcelExporter("examples/output/one_to_many_decomposition.xlsx")
    exporter.export(context)

    print(f"\n✓ Created {len([mapping1, mapping2])} 1:N decomposition mappings:")
    print(f"  - full_name → (first_name + last_name) via SPLIT")
    print(f"  - address_data → (street + city) via PARSE_STRUCT")
    print(f"\n⚠ Both mappings are DESTRUCTIVE (potential data loss)")
    print(f"\n✓ Exported to: examples/output/one_to_many_decomposition.xlsx")


if __name__ == "__main__":
    example_one_to_many_mapping()
