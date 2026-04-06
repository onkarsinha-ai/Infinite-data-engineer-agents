"""Transformation and validation logic for mappings."""
from typing import List, Optional, Dict, Any
from src.mapping.mapping_lineage import FieldMapping, MappingType, MappingLineage
from src.core.data_types import TypeConverter, TypeInfo
from src.core.schema_extractor import Field
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TransformationEngine:
    """Generate and manage transformation rules."""

    def __init__(self):
        """Initialize transformation engine."""
        self.type_converter = TypeConverter()

    def generate_transformation_code(self, field_mapping: FieldMapping) -> str:
        """Generate Python transformation code."""
        if not field_mapping.source_field or not field_mapping.dest_field:
            return ""

        source_type = field_mapping.source_field.type_info
        dest_type = field_mapping.dest_field.type_info

        code_lines = []
        code_lines.append(f"# Transform {field_mapping.source_field.name} to {field_mapping.dest_field.name}")

        if source_type == dest_type:
            code_lines.append(f"{field_mapping.dest_field.name} = {field_mapping.source_field.name}")
        else:
            code_lines.append(self._generate_type_conversion(field_mapping.source_field, field_mapping.dest_field))

        return "\n".join(code_lines)

    def _generate_type_conversion(self, source_field: Field, dest_field: Field) -> str:
        """Generate type conversion code."""
        source_type = source_field.type_info.base_type
        dest_type = dest_field.type_info.base_type

        src_name = source_field.name
        dest_name = dest_field.name

        # String to Integer
        if source_type.value in ["VARCHAR", "TEXT", "CHAR"] and dest_type.value in [
            "INTEGER",
            "BIGINT",
        ]:
            return f"{dest_name} = int({src_name}) if {src_name} else None"

        # String to Float
        elif source_type.value in ["VARCHAR", "TEXT", "CHAR"] and dest_type.value in [
            "FLOAT",
            "DOUBLE",
            "DECIMAL",
        ]:
            return f"{dest_name} = float({src_name}) if {src_name} else None"

        # Integer to String
        elif source_type.value in ["INTEGER", "BIGINT"] and dest_type.value in [
            "VARCHAR",
            "TEXT",
            "CHAR",
        ]:
            return f"{dest_name} = str({src_name}) if {src_name} is not None else None"

        # Date/Datetime conversions
        elif "DATE" in source_type.value or "TIME" in source_type.value:
            if dest_type.value in ["VARCHAR", "TEXT", "CHAR"]:
                return f"{dest_name} = {src_name}.isoformat() if {src_name} else None"
            elif "DATE" in dest_type.value or "TIME" in dest_type.value:
                return f"{dest_name} = {src_name}  # Date/time compatible"

        # JSON conversions
        elif source_type.value in ["JSON", "JSONB"]:
            if dest_type.value in ["VARCHAR", "TEXT"]:
                return f"import json\n{dest_name} = json.dumps({src_name}) if {src_name} else None"

        # Default: Direct cast
        else:
            return f"{dest_name} = {dest_type.value}({src_name}) if {src_name} is not None else None"

    def build_transformation_pipeline(
        self, lineage: MappingLineage
    ) -> List[FieldMapping]:
        """Build complete transformation pipeline for a lineage."""
        pipeline = []

        if lineage.mapping_type == MappingType.ONE_TO_ONE:
            if lineage.source_fields and lineage.destination_field:
                mapping = FieldMapping(
                    source_field=lineage.source_fields[0],
                    dest_field=lineage.destination_field,
                    mapping_type=MappingType.ONE_TO_ONE,
                    requires_conversion=self.type_converter.requires_conversion(
                        lineage.source_fields[0].type_info,
                        lineage.destination_field.type_info,
                    ),
                    transformation_rule=lineage.aggregation_rule.aggregation_expression
                    if lineage.aggregation_rule
                    else "",
                    transformation_code=self.generate_transformation_code(
                        FieldMapping(
                            source_field=lineage.source_fields[0],
                            dest_field=lineage.destination_field,
                            mapping_type=MappingType.ONE_TO_ONE,
                        )
                    ),
                )
                pipeline.append(mapping)

        elif lineage.mapping_type == MappingType.MANY_TO_ONE:
            if lineage.aggregation_rule:
                mapping = FieldMapping(
                    source_field=None,
                    dest_field=lineage.destination_field,
                    mapping_type=MappingType.MANY_TO_ONE,
                    transformation_rule=lineage.aggregation_rule.aggregation_expression,
                    transformation_code=lineage.aggregation_rule.aggregation_code,
                )
                pipeline.append(mapping)

        elif lineage.mapping_type == MappingType.ONE_TO_MANY:
            if lineage.decomposition_rule:
                mapping = FieldMapping(
                    source_field=lineage.source_fields[0] if lineage.source_fields else None,
                    dest_field=None,
                    mapping_type=MappingType.ONE_TO_MANY,
                    transformation_rule=lineage.decomposition_rule.decomposition_expression,
                    transformation_code=lineage.decomposition_rule.decomposition_code,
                )
                pipeline.append(mapping)

        lineage.transformation_pipeline = pipeline
        return pipeline


class ValidationEngine:
    """Validate mappings and detect issues."""

    def __init__(self):
        """Initialize validation engine."""
        self.type_converter = TypeConverter()

    def validate_field_mapping(self, mapping: FieldMapping) -> Dict[str, Any]:
        """Validate a field mapping."""
        issues = []
        warnings = []

        if not mapping.source_field and mapping.mapping_type == MappingType.ONE_TO_ONE:
            issues.append("ONE_TO_ONE mapping requires source field")

        if not mapping.dest_field and mapping.mapping_type == MappingType.ONE_TO_ONE:
            issues.append("ONE_TO_ONE mapping requires destination field")

        # Check type compatibility
        if mapping.source_field and mapping.dest_field:
            risk = self.type_converter.get_conversion_risk(
                mapping.source_field.type_info, mapping.dest_field.type_info
            )
            if risk in ["HIGH", "CRITICAL"]:
                mapping.is_destructive = True
                mapping.destruction_risk = risk
                issues.append(f"High risk type conversion: {risk}")

        # Check nullability
        if mapping.source_field and mapping.dest_field:
            if mapping.source_field.nullable and not mapping.dest_field.nullable:
                warnings.append("Source is nullable but destination is NOT NULL")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "destructive": mapping.is_destructive,
        }

    def validate_lineage(self, lineage: MappingLineage) -> Dict[str, Any]:
        """Validate a mapping lineage."""
        issues = []
        warnings = []

        if lineage.mapping_type == MappingType.ONE_TO_ONE:
            if not lineage.source_fields or len(lineage.source_fields) != 1:
                issues.append("ONE_TO_ONE mapping must have exactly 1 source field")
            if not lineage.destination_field:
                issues.append("ONE_TO_ONE mapping must have 1 destination field")

        elif lineage.mapping_type == MappingType.MANY_TO_ONE:
            if len(lineage.source_fields) < 2:
                issues.append("MANY_TO_ONE mapping must have at least 2 source fields")
            if not lineage.destination_field:
                issues.append("MANY_TO_ONE mapping must have 1 destination field")
            if not lineage.aggregation_rule:
                issues.append("MANY_TO_ONE mapping must have aggregation rule")

        elif lineage.mapping_type == MappingType.ONE_TO_MANY:
            if not lineage.source_fields or len(lineage.source_fields) != 1:
                issues.append("ONE_TO_MANY mapping must have exactly 1 source field")
            if len(lineage.destination_fields) < 2:
                issues.append("ONE_TO_MANY mapping must have at least 2 destination fields")
            if not lineage.decomposition_rule:
                issues.append("ONE_TO_MANY mapping must have decomposition rule")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "destructive": lineage.is_destructive,
        }
