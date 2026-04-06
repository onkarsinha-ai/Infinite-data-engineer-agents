"""Aggregation engine for N:1 mappings."""
from typing import List, Optional, Dict, Any
from src.mapping.mapping_lineage import (
    AggregationRule,
    AggregationStrategy,
    FieldMapping,
    MappingType,
)
from src.core.schema_extractor import Field
from src.core.data_types import TypeInfo, SQLDataType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AggregationEngine:
    """Engine for handling aggregation of multiple sources to one destination."""

    def __init__(self):
        """Initialize aggregation engine."""
        self.strategy_templates = self._init_strategy_templates()

    def _init_strategy_templates(self) -> Dict[str, str]:
        """Initialize strategy code templates."""
        return {
            AggregationStrategy.CONCAT: "result = '{sep}'.join([str({fields})])",
            AggregationStrategy.SUM: "result = sum([{fields}])",
            AggregationStrategy.AVG: "result = sum([{fields}]) / len([{fields}])",
            AggregationStrategy.MAX: "result = max([{fields}])",
            AggregationStrategy.MIN: "result = min([{fields}])",
            AggregationStrategy.FIRST: "result = [{fields}][0]",
            AggregationStrategy.LAST: "result = [{fields}][-1]",
            AggregationStrategy.GROUP_ARRAY: "result = [{fields}]",
            AggregationStrategy.MERGE: "result = {{**{fields}}}.copy()",
            AggregationStrategy.MERGE_JSON: "import json; result = json.dumps({{{', '.join([f'{f.name}: {f.name}' for f in source_fields])}}})",
        }

    def analyze_aggregation(
        self,
        source_fields: List[Field],
        destination_field: Field,
    ) -> Optional[AggregationRule]:
        """Analyze if aggregation is possible and suggest strategy."""
        if not source_fields:
            logger.warning("No source fields provided for aggregation analysis")
            return None

        logger.info(
            f"Analyzing aggregation: {[f.name for f in source_fields]} -> {destination_field.name}"
        )

        # Determine best strategy based on types
        strategy = self._determine_strategy(source_fields, destination_field)

        if not strategy:
            logger.warning("Could not determine aggregation strategy")
            return None

        # Generate aggregation expression and code
        expression = self._generate_expression(strategy, source_fields, destination_field)
        code = self._generate_aggregation_code(strategy, source_fields, destination_field)

        # Check for data loss
        is_destructive, data_loss_desc = self._detect_data_loss(
            source_fields, destination_field, strategy
        )

        rule = AggregationRule(
            strategy=strategy,
            source_fields=source_fields,
            destination_field=destination_field,
            aggregation_expression=expression,
            aggregation_code=code,
            is_destructive=is_destructive,
            data_loss_description=data_loss_desc,
        )

        logger.debug(f"Created aggregation rule: {rule}")
        return rule

    def _determine_strategy(
        self, source_fields: List[Field], destination_field: Field
    ) -> Optional[AggregationStrategy]:
        """Determine best aggregation strategy."""
        # If destination is VARCHAR/TEXT and sources are strings -> CONCAT
        if destination_field.type_info.base_type in [
            SQLDataType.VARCHAR,
            SQLDataType.TEXT,
            SQLDataType.CHAR,
        ]:
            if all(
                f.type_info.base_type
                in [SQLDataType.VARCHAR, SQLDataType.TEXT, SQLDataType.CHAR]
                for f in source_fields
            ):
                return AggregationStrategy.CONCAT

        # If destination is numeric and sources are numeric -> SUM or AVG
        if destination_field.type_info.base_type in [
            SQLDataType.INTEGER,
            SQLDataType.BIGINT,
            SQLDataType.DECIMAL,
            SQLDataType.FLOAT,
            SQLDataType.DOUBLE,
        ]:
            if all(
                f.type_info.base_type
                in [
                    SQLDataType.INTEGER,
                    SQLDataType.BIGINT,
                    SQLDataType.DECIMAL,
                    SQLDataType.FLOAT,
                    SQLDataType.DOUBLE,
                ]
                for f in source_fields
            ):
                return AggregationStrategy.SUM

        # If destination is JSON -> MERGE_JSON
        if destination_field.type_info.base_type in [SQLDataType.JSON, SQLDataType.JSONB]:
            return AggregationStrategy.MERGE_JSON

        # Default: GROUP_ARRAY
        return AggregationStrategy.GROUP_ARRAY

    def _generate_expression(
        self,
        strategy: AggregationStrategy,
        source_fields: List[Field],
        destination_field: Field,
    ) -> str:
        """Generate aggregation expression."""
        field_names = ", ".join(f'"{f.name}"' for f in source_fields)

        if strategy == AggregationStrategy.CONCAT:
            return f"CONCAT({', '.join(f.name for f in source_fields)})"
        elif strategy == AggregationStrategy.SUM:
            return f"SUM({field_names})"
        elif strategy == AggregationStrategy.AVG:
            return f"AVG({field_names})"
        elif strategy == AggregationStrategy.MAX:
            return f"MAX({field_names})"
        elif strategy == AggregationStrategy.MIN:
            return f"MIN({field_names})"
        elif strategy == AggregationStrategy.FIRST:
            return f"FIRST({field_names})"
        elif strategy == AggregationStrategy.LAST:
            return f"LAST({field_names})"
        elif strategy == AggregationStrategy.GROUP_ARRAY:
            return f"ARRAY({field_names})"
        elif strategy == AggregationStrategy.MERGE_JSON:
            return f"JSON_MERGE({field_names})"
        else:
            return f"{strategy.value}({field_names})"

    def _generate_aggregation_code(
        self,
        strategy: AggregationStrategy,
        source_fields: List[Field],
        destination_field: Field,
    ) -> str:
        """Generate Python code for aggregation."""
        field_names = ", ".join(f"{f.name}" for f in source_fields)

        if strategy == AggregationStrategy.CONCAT:
            sep = " "
            return f"result = '{sep}'.join(str(v) for v in [{field_names}] if v)"

        elif strategy == AggregationStrategy.SUM:
            return f"result = sum(v for v in [{field_names}] if v is not None)"

        elif strategy == AggregationStrategy.AVG:
            return f"values = [v for v in [{field_names}] if v is not None]\nresult = sum(values) / len(values) if values else None"

        elif strategy == AggregationStrategy.MAX:
            return f"values = [v for v in [{field_names}] if v is not None]\nresult = max(values) if values else None"

        elif strategy == AggregationStrategy.MIN:
            return f"values = [v for v in [{field_names}] if v is not None]\nresult = min(values) if values else None"

        elif strategy == AggregationStrategy.FIRST:
            return f"result = next((v for v in [{field_names}] if v is not None), None)"

        elif strategy == AggregationStrategy.LAST:
            return f"result = next((v for v in reversed([{field_names}]) if v is not None), None)"

        elif strategy == AggregationStrategy.GROUP_ARRAY:
            return f"result = [v for v in [{field_names}] if v is not None]"

        elif strategy == AggregationStrategy.MERGE_JSON:
            return f"import json\nresult = {{**{{{', '.join(f'{f.name}: {f.name}' for f in source_fields)}}}}}"

        else:
            return f"# Custom aggregation for {strategy.value}"

    def _detect_data_loss(
        self, source_fields: List[Field], destination_field: Field, strategy: AggregationStrategy
    ) -> tuple[bool, str]:
        """Detect potential data loss in aggregation."""
        is_destructive = False
        details = []

        # Aggregation always loses detailed information
        if strategy in [
            AggregationStrategy.SUM,
            AggregationStrategy.AVG,
            AggregationStrategy.MAX,
            AggregationStrategy.MIN,
            AggregationStrategy.FIRST,
            AggregationStrategy.LAST,
        ]:
            is_destructive = True
            details.append(
                f"{strategy.value} aggregation loses individual field values from sources"
            )

        # Type mismatches
        for source_field in source_fields:
            if source_field.type_info.base_type != destination_field.type_info.base_type:
                details.append(
                    f"Type conversion {source_field.type_info.base_type} -> {destination_field.type_info.base_type}"
                )

        # NULL handling
        null_source_count = sum(1 for f in source_fields if f.nullable)
        if null_source_count > 0 and not destination_field.nullable:
            is_destructive = True
            details.append("Source fields can be NULL but destination is NOT NULL")

        data_loss_desc = "; ".join(details) if details else "No known data loss"
        return is_destructive, data_loss_desc

    def validate_aggregation(self, rule: AggregationRule) -> bool:
        """Validate aggregation rule."""
        if not rule.source_fields:
            logger.warning("Aggregation rule has no source fields")
            return False

        if not rule.destination_field:
            logger.warning("Aggregation rule has no destination field")
            return False

        return True
